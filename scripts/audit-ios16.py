#!/usr/bin/env python3
"""Verify Apple iPhone X inputs; write metadata only, never a bootable image."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import re
import struct
import subprocess
import sys
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def audit(upstream, output, decode=False, local_ipsw=None):
    profile = tomllib.loads((ROOT / 'profiles/os/ios-16.7.16-20H392/profile.toml').read_text(encoding='utf-8'))
    expected, pins = profile['ipsw'], profile['audit']
    sys.path.insert(0, str(upstream / 'scripts'))
    from unixnu.ipsw import RangeFile, im4p_payload
    source = local_ipsw if local_ipsw else RangeFile(expected['url'], block=1 << 20)
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        manifest_bytes = archive.read('BuildManifest.plist')
        manifest = plistlib.loads(manifest_bytes)
        if (manifest['ProductVersion'], manifest['ProductBuildVersion']) != (expected['version'], expected['build']):
            raise ValueError('IPSW version/build differs from the pinned iOS 16 target')
        if expected['product'] not in manifest['SupportedProductTypes']:
            raise ValueError('IPSW does not contain the selected iPhone X product')
        identities = [item for item in manifest['BuildIdentities']
                      if item['Info']['DeviceClass'] == expected['device_class']
                      and item['Info']['RestoreBehavior'] == 'Erase'
                      and int(item['ApChipID'], 16) == expected['chip_id']
                      and int(item['ApBoardID'], 16) == expected['board_id']]
        if len(identities) != 1:
            raise ValueError('Expected exactly one matching iPhone X Erase identity')
        identity = identities[0]
        kernel = identity['Manifest']['KernelCache']
        if kernel['Info']['Path'] != pins['kernel_member']:
            raise ValueError('Kernel member differs from the pinned target')
        im4p = archive.read(pins['kernel_member'])
    digest = hashlib.sha384(im4p).hexdigest()
    if digest != kernel['Digest'].hex() or digest != pins['kernel_im4p_sha384']:
        raise ValueError('Kernel IM4P SHA384 differs from Apple manifest or repository pin')
    if hashlib.sha256(im4p).hexdigest() != pins['kernel_im4p_sha256']:
        raise ValueError('Kernel IM4P SHA256 differs from repository pin')
    report = {'product': expected['product'], 'device_class': expected['device_class'],
              'version': manifest['ProductVersion'], 'build': manifest['ProductBuildVersion'],
              'chip_id': identity['ApChipID'], 'board_id': identity['ApBoardID'],
              'apple_url': expected['url'], 'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
              'kernel_im4p_sha384': digest, 'kernel_im4p_sha256': hashlib.sha256(im4p).hexdigest(),
              'components': {name: value['Info']['Path'] for name, value in identity['Manifest'].items()
                             if name in ('OS', 'SystemOS', 'Cryptex1,SystemOS', 'DeviceTree', 'StaticTrustCache', 'KernelCache')},
              'source_candidate': profile['os']['xnu_revision'], 'abi_qualified': False,
              'device_boot_verified': False}
    if decode:
        if platform.system() != 'Darwin':
            raise ValueError('--decode uses macOS compression_tool; manifest audit works on any host')
        packed, raw = output / 'kernel.lzfse', output / 'kernel.raw'
        packed.write_bytes(im4p_payload(im4p))
        try:
            subprocess.run(['/usr/bin/compression_tool', '-decode', '-a', 'lzfse', '-i', str(packed), '-o', str(raw)], check=True)
            macho = raw.read_bytes()
            if macho[:4] == b'\xca\xfe\xba\xbe':
                count = struct.unpack_from('>I', macho, 4)[0]
                slices = [struct.unpack_from('>5I', macho, 8 + 20 * i) for i in range(count)]
                arm64 = [item for item in slices if item[0] == 0x100000c]
                if len(arm64) != 1:
                    raise ValueError('Expected one arm64 Mach-O slice')
                _, _, offset, size, _ = arm64[0]
                macho = macho[offset:offset + size]
            if macho[:4] != b'\xcf\xfa\xed\xfe' or struct.unpack_from('<I', macho, 4)[0] != 0x100000c:
                raise ValueError('Expected an ARM64 Mach-O kernel')
            if struct.unpack_from('<I', macho, 8)[0] & 0xffffff != 0:
                raise ValueError('Expected arm64, not an unqualified arm64e kernel')
            version = re.search(rb'Darwin Kernel Version [^\x00]{1,400}', macho)
            if not version or not version.group().startswith(b'Darwin Kernel Version 22.'):
                raise ValueError('Expected a Darwin 22 kernel for iOS 16')
            report['darwin_kernel_string'] = version.group().decode('ascii')
            report['kernel_macho_sha256'] = hashlib.sha256(macho).hexdigest()
        finally:
            packed.unlink(missing_ok=True)
            raw.unlink(missing_ok=True)
    (output / 'ios16-input-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'out/ios16-audit')
    parser.add_argument('--decode', action='store_true')
    parser.add_argument('--ipsw', type=Path)
    args = parser.parse_args()
    audit(args.upstream.resolve(), args.output, args.decode, args.ipsw)
