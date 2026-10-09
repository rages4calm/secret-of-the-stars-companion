"""Reproduce a private Battle Info ROM and regenerate a separate native proof."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PIN = '650721747fd808daeb4e2a9745f16150b2d00c91'
CLEAN_SHA = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(args, cwd, log):
    with log.open('w') as output:
        result = subprocess.run(list(map(str, args)), cwd=cwd, stdout=output, stderr=output)
    if result.returncode:
        raise RuntimeError(log.read_text(errors='replace')[-6000:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compile', action='store_true')
    args = parser.parse_args()
    src = ROOT / 'research/2026-10-08/battle-info'
    out = ROOT / 'local/patch-proof/battle-info-padded'
    out.mkdir(parents=True, exist_ok=True)
    clean = (ROOT / 'local/inputs/clean-usa.sfc').read_bytes()
    if digest(clean) != CLEAN_SHA:
        raise RuntimeError('Clean input identity mismatch')
    image = out / 'battle-info.sfc'
    # The free bank starts at offset 0x190000. Use a declared 2 MiB image,
    # explicit erased-byte fill and Asar's checksum fix, rather than an odd tail.
    image.write_bytes(clean + b'\xff' * (0x200000 - len(clean)))
    asar = ROOT / 'local/tooling/asar-1.91/asar.exe'
    command([asar, '--pause-mode=never', '--symbols=wla',
             '--symbols-path=' + str(out / 'symbols.txt'), src / 'src/main.asm', image], ROOT, out / 'assemble.log')
    data = image.read_bytes()
    checksum, complement = struct.unpack_from('<HH', data, 0x7fdc)[::-1]
    assert len(data) == 0x200000 and checksum ^ complement == 0xffff and sum(data) & 0xffff == checksum
    spans, start = [], None
    for i in range(len(clean)):
        changed = clean[i] != data[i]
        if changed and start is None:
            start = i
        if start is not None and (not changed or i == len(clean) - 1):
            end = i if not changed else i + 1
            spans.append({'offset': hex(start), 'size': end - start})
            start = None
    receipt = {'source_url': 'https://github.com/BlueImp78/Secret-of-The-Stars-Battle-Info-Hack',
        'source_pin': SOURCE_PIN, 'source_files': {str(p.relative_to(src)): digest(p.read_bytes()) for p in sorted((src / 'src').glob('*.asm'))},
        'assembler': 'Asar 1.91', 'assembler_sha256': digest(asar.read_bytes()),
        'clean_input_sha256': CLEAN_SHA, 'output_sha256': digest(data), 'output_size': len(data),
        'padding': {'before_assembly': True, 'byte': 'ff', 'capacity': '0x200000'},
        'checksum': hex(checksum), 'checksum_verified': True, 'changed_original_spans': spans,
        'limits': ['No license file in pinned upstream source; private research only',
                   'Patch assembly is not gameplay or native dispatch qualification']}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if not args.compile:
        print(json.dumps(receipt, indent=2))
        return
    variant = ROOT / 'local/native-proof/SecretOfTheStarsBattleInfo'
    variant.mkdir(exist_ok=True)
    authored = ROOT / 'native/foundation'
    for p in authored.rglob('*'):
        if p.is_file() and p.name != 'authored-files.json':
            target = variant / p.relative_to(authored)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
    state = variant / 'src/foundation_state.c'
    state.write_text(state.read_text().replace('sots-clean-foundation-v1', 'sots-battle-info-v2'))
    (variant / 'mods/preloaded/packages').mkdir(parents=True, exist_ok=True)
    identity = dict(display_name='Secret of the Stars - Battle Info proof', rom_file='battle-info.sfc',
        expected_sha256=digest(data), expected_crc32=f'{zlib.crc32(data) & 0xffffffff:08x}',
        expected_md5=hashlib.md5(data).hexdigest(), expected_sha1=hashlib.sha1(data).hexdigest(),
        rom_size=str(len(data)), mapping='lorom', region='USA', game_id='secretofthestars-battle-info-usa')
    (variant / 'rom_identity.txt').write_text(''.join(f'{key} = {value}\n' for key, value in identity.items()))
    runtime = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp'
    command([sys.executable, runtime / 'snesrecomp_cli.py', 'generate', '--rom', image,
             '--cfg-dir', 'recomp', '--out-dir', 'src/gen', '--funcs-h', 'recomp/funcs.h',
             '--project-root', variant, '--expected-sha256', identity['expected_sha256'],
             '--expected-crc32', identity['expected_crc32']], variant, out / 'generate.log')
    sdl = Path.home() / '.local/share/retcomm/toolchains/cmake-clang-v1/latest/x86_64-w64-mingw32/lib/cmake/SDL3'
    command(['cmake', '-S', variant, '-B', variant / 'build', '-G', 'Ninja',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_C_COMPILER=clang', '-DCMAKE_CXX_COMPILER=clang++',
        '-DSDL3_DIR=' + str(sdl), '-DSNESRECOMP_ROOT=' + str(runtime),
        '-DSNESRECOMP_FRAME_IMPL=LLE', '-DSNESRECOMP_SDL3_FETCH=OFF'], ROOT, out / 'configure.log')
    command(['cmake', '--build', variant / 'build', '-j', '8'], ROOT, out / 'build.log')
    receipt['variant_executable_sha256'] = digest((variant / 'build/SecretOfTheStarsSNESRecomp.exe').read_bytes())
    receipt['variant_snapshot_identity'] = 'sots-battle-info-v2'
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(out / 'receipt.json')


if __name__ == '__main__':
    main()
