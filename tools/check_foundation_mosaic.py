"""ROM-free standalone canaries for the foundation's mosaic rendering seam.

The C harness includes the current runtime PPU source without changing it.
Prior positive-run loop bodies are reconstructed for bounded center parity;
empty spans are explicit host injections, never campaign progression claims.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PPU = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src/snes/ppu.c'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def references(src):
    out = []
    for name in ('PpuDrawBackground_4bpp_mosaic', 'PpuDrawBackground_2bpp_mosaic', 'PpuDrawBackground_mode7'):
        start = src.rindex('static void ' + name + '(')
        brace = src.index('{', start)
        depth, end = 1, brace + 1
        while depth:
            depth += (src[end] == '{') - (src[end] == '}')
            end += 1
        body = src[start:end]
        old = body.replace(name, 'Legacy_' + name, 1)
        old = old.replace('    if (win.edges[windex + 1] <= sx)\n      continue;\n', '')
        old = old.replace('    if (x2 <= x)\n      continue;\n', '')
        old = old.replace('for (int i = 0; i < w; i++) {', 'int i = 0;\n        do {')
        old = old.replace('            dstz[i] = pixel + z;\n        }', '            dstz[i] = pixel + z;\n        } while (++i != w);')
        old = old.replace('for (int i = 0; i < w; i++) dstz[i] = pixel + z;', 'int i = 0; do dstz[i] = pixel + z; while (++i != w);')
        out.append(old.replace('dstz < dstz_end', 'dstz != dstz_end'))
        injected = body.replace(name, 'Empty_' + name, 1)
        setup = '  IS_SCREEN_WINDOWED(ppu, sub, layer) ? PpuWindows_Calc(&win, ppu, layer, y) : PpuWindows_Clear(&win, ppu, layer, y);'
        if setup not in injected:
            raise ValueError('Window setup changed; inspect harness assumptions')
        out.append(injected.replace(setup, '  win.nr = 1; win.bits = 0; win.edges[0] = 13; win.edges[1] = 13;'))
    return '\n\n'.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Fresh private output directory under local/')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / 'local').resolve()) or output.exists():
        raise ValueError('Choose a fresh private directory under local/')
    output.mkdir(parents=True)
    ppu_before = PPU.read_bytes()
    template = ROOT / 'tools/foundation_mosaic_canary.c'
    template_before = template.read_bytes()
    reference = references(ppu_before.decode('utf-8').replace('\r\n', '\n'))
    (output / 'mosaic-reference.inc').write_text(reference, encoding='utf-8')
    compiler_path = Path(r'C:\Users\crono\.local\share\retcomm\toolchains\cmake-clang-v1\latest\bin\clang.exe')
    compiler = str(compiler_path) if compiler_path.exists() else shutil.which('clang')
    if not compiler:
        raise ValueError('Clang required')
    binary = output / 'mosaic-canary.exe'
    command = [compiler, '-O2', '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
               '-DFOUNDATION_PPU_SOURCE="' + PPU.as_posix() + '"', '-I' + str(output), str(template), '-o', str(binary)]
    compile_result = subprocess.run(command, capture_output=True, text=True)
    (output / 'compile.log').write_text(compile_result.stdout + compile_result.stderr, encoding='utf-8')
    if compile_result.returncode:
        raise ValueError('Compile failed: ' + compile_result.stderr)
    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
    (output / 'run.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        raise ValueError('Canary failed: ' + result.stdout + result.stderr)
    report = json.loads(result.stdout)
    report.update({
        'scope': 'ROM-free synthetic renderer inputs; bounded prior-loop center parity; no campaign qualification',
        'source_sha256': {str(PPU.relative_to(ROOT)): sha(ppu_before), str(template.relative_to(ROOT)): sha(template_before)},
        'generated_reference_sha256': sha(reference.encode()),
        'checker_sha256': sha(Path(__file__).read_bytes()),
        'binary_sha256': sha(binary.read_bytes()),
        'source_unchanged': PPU.read_bytes() == ppu_before and template.read_bytes() == template_before,
        'compile_command': command,
    })
    if not report['source_unchanged']:
        raise ValueError('Source changed during qualification')
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
