#!/usr/bin/env python3
"""Read an Android boot header and SHA256; never execute or write to a device."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def inspect(path):
    data = path.read_bytes()
    if len(data) < 48 or data[:8] != b'ANDROID!':
        raise ValueError('Not a complete Android boot image header')
    u32 = lambda offset: struct.unpack_from('<I', data, offset)[0]
    version = u32(40)
    if version > 4:
        raise ValueError(f'Unsupported boot header version {version}')
    if version >= 3:
        page = 4096
        minimum = 1584 if version == 4 else 1580
        kernel_size, ramdisk_size, header_size = u32(8), u32(12), u32(20)
        if header_size != minimum:
            raise ValueError('Unexpected v3/v4 header size')
        addresses = {}
    else:
        page = u32(36)
        minimum = (1632, 1648, 1660)[version]
        kernel_size, ramdisk_size = u32(8), u32(16)
        addresses = {'kernel_address_header': u32(12), 'ramdisk_address_header': u32(20),
                     'tags_address_header': u32(32)}
        if page not in (2048, 4096, 8192, 16384, 32768, 65536):
            raise ValueError('Invalid legacy page size')
        if version and len(data) >= minimum and u32(1644) != minimum:
            raise ValueError('Unexpected v1/v2 header size')
    if len(data) < minimum or minimum > page:
        raise ValueError('Truncated or oversized Android boot header')
    if not kernel_size:
        raise ValueError('Boot image has no kernel')
    align = lambda value: (value + page - 1) // page * page
    kernel_start = page
    ramdisk_start = kernel_start + align(kernel_size)
    if kernel_start + kernel_size > len(data) or ramdisk_start + ramdisk_size > len(data):
        raise ValueError('Kernel/ramdisk extends beyond the image')
    return {'file': path.name, 'sha256': hashlib.sha256(data).hexdigest(),
            'image_bytes': len(data), 'header_version': version, 'page_bytes': page,
            'kernel_bytes': kernel_size, 'kernel_file_offset': kernel_start,
            'ramdisk_bytes': ramdisk_size, 'ramdisk_file_offset': ramdisk_start,
            **addresses, 'note': 'Header addresses are not observed bootloader load addresses.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = json.dumps(inspect(args.image), indent=2) + '\n'
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f'boot image: {error}\n')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding='utf-8')
    print(result, end='')
