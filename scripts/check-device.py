#!/usr/bin/env python3
"""Verify source pins, profile resolution and the real FDT-to-ADT handoff."""
import argparse
from contextlib import nullcontext
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def check(source, dtc=False):
    board = tomllib.loads((ROOT / 'board.toml').read_text(encoding='utf-8'))
    pins = tomllib.loads((ROOT / 'sources.lock.toml').read_text(encoding='utf-8'))
    for item in pins['source']:
        assert re.fullmatch('[0-9a-f]{40}', item['commit']), item['name']
        assert item['repository'].startswith('https://github.com/'), item['name']
    assert pins['source'][0]['commit'] == (ROOT / 'upstream.rev').read_text().strip()
    assert board['board']['soc'] == 'SM7250'
    assert board['board']['name'] == 'picasso'
    sys.path.insert(0, str(source / 'scripts'))
    from unixnu import cli, components, config, devicetree, feeds, kernel, patches
    check_output = ROOT / 'out/host-check'
    check_output.mkdir(parents=True, exist_ok=True)
    with nullcontext(str(check_output)) as temporary:
        args = cli.parser().parse_args(['defconfig', 'picasso_defconfig', '-D', str(ROOT), '--out', temporary])
        ctx = config.Context(args)
        cli.cmd_defconfig(ctx)
        selected = {item['id'] for item in components.selected(ctx)}
        assert selected == set(board['components']['include'])
        assert ctx.board['board']['soc_source'] == 'sm7250'
        assert ctx.board['soc']['name'] == 'SM7250'
        assert ctx.board['os']['name'] == board['board']['os_profile']
        assert ctx.config_path.is_file()
        ctx.config = config.parse_config(ctx.config_path.read_text())
        modules = feeds.resolve(ctx)
        kernel.archive_plan(ctx)
        patches.plan(ctx, modules)
        if dtc:
            dtb = Path(temporary) / 'picasso.dtb'
            subprocess.run(['dtc', '-I', 'dts', '-O', 'dtb', '-i', str(ROOT / 'socs/sm7250/dts'),
                            '-o', str(dtb), str(ROOT / 'dts/picasso.dts')], check=True)
            root = devicetree.read_fdt(dtb.read_bytes())
            entries = list(root.walk())
            timer = next(e for e in entries if e.name == 'timer')
            assert timer.cells('interrupts')[6:9] == [1, 3, 0xff08]
            intc = next(e for e in entries if e.name.startswith('interrupt-controller@'))
            assert devicetree.registers(intc) == [(0x17a00000, 0x10000), (0x17a60000, 0x100000)]
            assert intc.cells('redistributor-stride') == [0, 0x20000]
            cpus = next(e for e in entries if e.name == 'cpus')
            assert len([e for e in cpus.children if e.enabled()]) == 1
            handles = {e.scalar('phandle'): e for e in entries if 'phandle' in e.properties}
            properties = dict(devicetree.hardware_properties(timer, handles))
            import struct
            assert struct.unpack('<12I', properties['interrupts'])[8] == 0xff08
            assert struct.unpack('<12I', properties['interrupts'])[7] + 16 == 19
            # A missing measured RAM map must fail rather than inventing 128 GB DRAM.
            try:
                devicetree.generate(dtb, ctx.board, unique_chip_id='1')
            except Exception as error:
                assert 'DRAM range' in str(error), str(error)
            else:
                raise AssertionError('Unqualified tree unexpectedly generated a payload ADT')
    spec = importlib.util.spec_from_file_location('device_launcher', ROOT / 'scripts/unixnu.py')
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    for command in (['bootimg'], ['build', 'payload'], ['build', 'userdata'], ['build', 'firmware']):
        try:
            launcher.image_gate(command)
        except ValueError as error:
            assert 'measured board inputs' in str(error)
        else:
            raise AssertionError('Unqualified image build was not stopped')
    launcher.image_gate(['build', 'kernel'])
    print(json.dumps({'board': 'picasso', 'soc': 'SM7250', 'virtual_timer_intid': 19,
                      'dtc_checked': dtc, 'hardware_boot_verified': False}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--dtc', action='store_true')
    args = parser.parse_args()
    check(args.upstream.resolve(), args.dtc)
