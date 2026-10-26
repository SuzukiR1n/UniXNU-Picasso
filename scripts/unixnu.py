#!/usr/bin/env python3
"""Run the pinned official tools with this device and an explicit image gate."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

DEVICE = Path(__file__).resolve().parents[1]


def prepare(directory=None):
    revision = (DEVICE / 'upstream.rev').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('upstream.rev must contain a full commit ID')
    target = Path(directory or os.environ.get('UNIXNU_SOURCE', DEVICE / '.cache' / 'UniXNU')).resolve()
    if not (target / '.git').exists():
        target.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'init', '-q', str(target)], check=True)
        subprocess.run(['git', '-C', str(target), 'remote', 'add', 'origin',
                        'https://github.com/UniXNU/UniXNU.git'], check=True)
        subprocess.run(['git', '-C', str(target), 'fetch', '--depth=1', 'origin', revision], check=True)
        subprocess.run(['git', '-C', str(target), 'checkout', '--detach', 'FETCH_HEAD'], check=True)
    current = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
    if current != revision:
        raise ValueError(f'UniXNU checkout is {current}; expected {revision}')
    # Format 2 looks up OS profiles inside the official checkout. Add this
    # repository's independently versioned profile without editing its tools.
    for profile in (DEVICE / 'profiles/os').iterdir():
        if profile.is_dir():
            shutil.copytree(profile, target / 'profiles/os' / profile.name, dirs_exist_ok=True)
    return target


def image_gate(arguments):
    board = tomllib.loads((DEVICE / 'board.toml').read_text(encoding='utf-8'))
    profile = tomllib.loads((DEVICE / 'profiles/os' / board['board']['os_profile'] / 'profile.toml').read_text(encoding='utf-8'))
    if any(item in ('kernel', 'prelink', 'all') for item in arguments) and not profile['os']['abi_qualified']:
        raise ValueError('iPhone X iOS 16 kernel ABI is not qualified. The official Darwin 23/iOS 17 '
                         'build recipe must be ported to Darwin 22 before building or prelinking. '
                         'Run scripts/audit-ios16.py for the pinned Apple input report.')
    image = any(item in ('payload', 'bootimg', 'userdata', 'firmware', 'all') for item in arguments)
    if image:
        record = tomllib.loads((DEVICE / 'hardware.toml').read_text(encoding='utf-8'))
        pending = [name for name, ready in record['qualification'].items()
                   if name != 'device_boot' and ready is not True]
        if pending:
            raise ValueError('Image assembly needs measured board inputs: ' + ', '.join(pending)
                             + '. See docs/bring-up.md; kernel/package host builds are available.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    known, arguments = parser.parse_known_args()
    if not known.prepare:
        image_gate(arguments)
    source = prepare()
    if known.prepare:
        print(source)
        return
    if not arguments:
        arguments = ['status', '--json']
    command = [sys.executable, str(source / 'unixnu'), *arguments,
               '-D', str(DEVICE), '--out', str(DEVICE / 'out')]
    raise SystemExit(subprocess.call(command))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
