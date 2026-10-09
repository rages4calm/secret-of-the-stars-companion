"""Compare isolated foundation captures exactly; do not hide differing bytes."""
from pathlib import Path
import argparse
import csv
import hashlib
import json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline', type=Path)
    p.add_argument('candidate', type=Path)
    p.add_argument('--tags', nargs='+', required=True)
    p.add_argument('--trace-offset', type=int, help='Baseline frames preceding the restored continuation')
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    result = {'baseline': str(args.baseline.resolve()), 'candidate': str(args.candidate.resolve()),
              'captures': {}}
    for tag in args.tags:
        if not tag or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in tag):
            p.error('Tags must be simple lowercase capture names')
        for suffix in ['wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx']:
            name = f'{tag}.{suffix}'
            a = (args.baseline / 'dump' / name).read_bytes()
            b = (args.candidate / 'dump' / name).read_bytes()
            result['captures'][name] = {'identical': a == b, 'baseline_bytes': len(a),
                'candidate_bytes': len(b), 'changed_bytes': sum(x != y for x, y in zip(a, b)) + abs(len(a)-len(b)),
                'candidate_sha256': hashlib.sha256(b).hexdigest()}
    if args.trace_offset is not None:
        if args.trace_offset < 0:
            p.error('Trace offset cannot be negative')
        with (args.baseline / 'state.csv').open() as f:
            a = list(csv.reader(f))[args.trace_offset:]
        with (args.candidate / 'state.csv').open() as f:
            b = list(csv.reader(f))
        result['trace'] = {'identical_except_host_frame_number':
                          [r[1:] for r in a] == [r[1:] for r in b],
                          'baseline_frames': len(a), 'candidate_frames': len(b)}
    result['passed'] = all(x['identical'] for x in result['captures'].values()) and (
        args.trace_offset is None or result['trace']['identical_except_host_frame_number'])
    if args.report:
        report = args.report.resolve()
        if report.suffix != '.json' or report.exists():
            p.error('Use a new .json report path')
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
