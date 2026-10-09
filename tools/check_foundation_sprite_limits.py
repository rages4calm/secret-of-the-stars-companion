"""Actual private PPU cap controls and copied title replays; no owner progress."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp'
EXTENSIONS = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx', 'regs.json')

HARNESS = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "snes/ppu.c"
Snes *g_snes;
unsigned char g_snesrecomp_last_hdmaen;
int snes_frame_counter;

static void setup(Ppu *p, unsigned count, int large, unsigned unique_x, unsigned unique_slot) {
  memset(p,0,sizeof(*p));
  for(unsigned i=0;i<128;i++) p->oam[i*2]=0xf000;
  for(unsigned i=0;i<count;i++) {
    p->oam[i*2]=(uint16_t)(i==unique_slot?unique_x:0);
    if(large) p->highOam[i/4]|=(uint8_t)(2u<<((i%4)*2));
  }
  /* Two opaque 4bpp tiles. This is synthetic data, not owner game art. */
  for(unsigned tile=0;tile<2;tile++) for(unsigned y=0;y<8;y++) p->vram[tile*16+y]=0x00ff;
}
static unsigned pixels(Ppu *p) {
  unsigned count=0;
  for(unsigned x=0;x<256;x++) if((p->objBuffer.data[x+kPpuExtraLeftRight]&15)!=0) count++;
  return count;
}
int main(void) {
  Ppu *p=calloc(1,sizeof(*p));
  if(!p) return 10;
  unsigned count[]={33,18,128}, last[]={16,32,64};
  int large[]={0,1,1};
  const char *names[]={"range33","slivers36","oam128"};
  for(unsigned scenario=0;scenario<3;scenario++) for(unsigned renderer=0;renderer<2;renderer++) for(unsigned unlimited=0;unlimited<2;unlimited++) {
    setup(p,count[scenario],large[scenario],last[scenario],scenario==1?0:count[scenario]-1);
    p->renderFlags=(renderer?kPpuRenderFlags_NewRenderer:0)|(unlimited?kPpuRenderFlags_NoSpriteLimits:0);
    ppu_evaluateSprites(p,0);
    printf("%s,%u,%u,%u,%u,%u,%u,%zu,%zu\n",names[scenario],renderer,unlimited,pixels(p),
      p->rangeOver,p->timeOver,ppu_read(p,0x3e),sizeof(p->oam),sizeof(p->highOam));
  }
  free(p); return 0;
}
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def captured_density(prefix):
    regs=json.loads(Path(str(prefix)+'.regs.json').read_text())
    oam=Path(str(prefix)+'.oam.bin').read_bytes()
    sizes=((8,16),(8,32),(8,64),(16,32),(16,64),(32,64),(16,32),(16,32))
    maximum=[0,0]
    for line in range(224):
        sprites=[]
        for slot in range(128):
            high=(oam[512+slot//4]>>((slot%4)*2))&3
            x=oam[slot*4]-(256 if high&1 else 0)
            width=sizes[regs['obsel']>>5][high>>1]
            if ((line-oam[slot*4+1])&255)<width and x+width>0:
                sprites.append((x,width))
        slivers=sum(sum(-8<col+x<256 for col in range(0,width,8)) for x,width in sprites)
        maximum[0]=max(maximum[0],len(sprites));maximum[1]=max(maximum[1],slivers)
    return {'maximum_sprites':maximum[0],'maximum_slivers':maximum[1],
            'below_hardware_caps':maximum[0]<=32 and maximum[1]<=34,
            'limit':'Static captured OAM, not every raster-time write or intervening field'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=PROOF / 'build-menu/SecretOfTheStarsSNESRecomp.exe')
    parser.add_argument('--cc', type=Path, default=Path.home() / '.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe')
    parser.add_argument('--renderer',type=int,choices=(0,1),default=0,help='Original or span renderer for actual title replays')
    args = parser.parse_args()
    args.exe = args.exe.resolve(strict=True)
    base = ROOT / 'local/runs' / ('sprite-limits-' + time.strftime('%Y%m%d-%H%M%S'))
    base.mkdir(exist_ok=False)
    frozen=base / 'candidate.exe';shutil.copy2(args.exe,frozen);args.exe=frozen
    runtime = PROOF / 'snesrecomp/runner/src'
    source = base / 'private-ppu-control.c'; source.write_text(HARNESS)
    executable = base / 'private-ppu-control.exe'
    command = [str(args.cc), '-std=c11', '-O2', '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections', '-Wl,--exclude-all-symbols',
        '-DSNESRECOMP_ENABLE_MODS=0', '-DSNESRECOMP_TRACE=0', '-I', str(runtime), str(source),
        str(runtime / 'snes/ppu_legacy.c'), str(runtime / 'snes/ws_shadow.c'), '-o', str(executable)]
    compiled = subprocess.run(command, capture_output=True, text=True)
    (base / 'compile.log').write_text(compiled.stdout + compiled.stderr)
    if compiled.returncode:
        raise RuntimeError('Private PPU harness compilation failed; see ' + str(base / 'compile.log'))
    synthetic = subprocess.run([str(executable)], capture_output=True, text=True, check=True)
    (base / 'synthetic.csv').write_text('scenario,renderer,unlimited,pixels,range_over,time_over,status77,oam_bytes,high_oam_bytes\n' + synthetic.stdout)
    rows = list(csv.DictReader((base / 'synthetic.csv').open()))
    report = {'executable_sha256': digest(args.exe), 'actual_replay_new_renderer':args.renderer, 'runtime_ppu_sha256': digest(runtime / 'snes/ppu.c'),
        'private_harness_sha256': digest(source), 'checks': {}, 'synthetic': rows, 'cases': {}}
    checks = report['checks']
    expected = {'range33': [(8,1,0,65), (16,0,0,1)],
                'slivers36': [(16,0,1,129), (32,0,0,1)],
                'oam128': [(16,1,1,193), (32,0,0,1)]}
    for scenario in expected:
        for renderer in (0,1):
            pair = [next(r for r in rows if r['scenario']==scenario and int(r['renderer'])==renderer and int(r['unlimited'])==limit)
                    for limit in (0,1)]
            checks[f'{scenario}_renderer{renderer}_pixels_and_status'] = all(
                tuple(int(row[k]) for k in ('pixels','range_over','time_over','status77')) == expected[scenario][limit]
                for limit,row in enumerate(pair))
    checks['original_oam_remains_128_four_byte_slots_plus_high_table'] = all(int(r['oam_bytes'])==512 and int(r['high_oam_bytes'])==32 for r in rows)
    checks['both_renderers_same_sprite_evaluator_result'] = all(
        [(r['pixels'],r['status77']) for r in rows if r['renderer']=='0' and r['scenario']==scenario] ==
        [(r['pixels'],r['status77']) for r in rows if r['renderer']=='1' and r['scenario']==scenario] for scenario in expected)

    cases = [('town', ROOT / 'local/runs/likado-east-a/saves/save0.sav',
              'wait 30\ndump before\npress left 90\nwait 30\npress right 160\nwait 30\npress down 60\nwait 30\ndump after\nquit\n'),
             ('house', ROOT / 'local/runs/likado-inside-a/saves/save0.sav',
              'wait 30\ndump before\npress b 1\nwait 40\ndump menu\npress b 1\nwait 40\ndump after\nquit\n'),
             ('david', ROOT / 'local/runs/david-final-a/saves/save0.sav', (ROOT / 'local/runs/david-dialogue-a/input.txt').read_text()),
             ('battle', ROOT / 'local/runs/world-cave-a/saves/save0.sav', (ROOT / 'local/runs/native-damage-original/input.txt').read_text())]
    report['source_checkpoint_sha256'] = {name: digest(state) for name,state,_ in cases}
    for name,state,script in cases:
        pair = []
        for limit in (0,1):
            run = base / f'{name}-{limit}'; run.mkdir(); (run / 'dump').mkdir()
            shutil.copy2(args.exe,run / 'game.exe'); shutil.copy2(state,run / 'resume.state')
            (run / 'input.txt').write_text(script)
            (run / 'config.ini').write_text(f'[Graphics]\nRenderer=software\nNewRenderer={args.renderer}\nNoSpriteLimits={limit}\nVSync=0\n'
                '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
                '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
            env={k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
            env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SNESRECOMP_DUMP_DIR=str(run / 'dump'),
                SNESRECOMP_STATE_TRACE=str(run / 'state.csv'),SNESRECOMP_FOUNDATION_TRACE=str(run / 'field.csv'),
                SNESRECOMP_FOUNDATION_CPU_TRACE=str(run / 'cpu.csv'),SNESRECOMP_FOUNDATION_FAST_MENUS='0',
                SNESRECOMP_FOUNDATION_BATTLE_INFO='0',SNESRECOMP_FOUNDATION_ENHANCED_PIXELS='0',
                SNESRECOMP_FOUNDATION_WIDE='0',SNESRECOMP_FOUNDATION_JOURNAL='0')
            with (run / 'host.log').open('w') as log:
                result=subprocess.run([str(run / 'game.exe'),'--no-launcher','--rom',str(ROOT / 'local/inputs/clean-usa.sfc'),
                    '--resume-state',str(run / 'resume.state'),'--script',str(run / 'input.txt')],cwd=run,env=env,
                    stdout=log,stderr=log,timeout=50,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            host=(run / 'host.log').read_text(errors='replace')
            report['cases'][f'{name}-{limit}']={'exit':result.returncode,'resumed':'resume state loaded:' in host}
            pair.append(run)
        off,on=pair
        tags=[p.name[:-len('.wram.bin')] for p in (off / 'dump').glob('*.wram.bin')]
        report['cases'][name+'-0']['capture_density']={tag:captured_density(off / 'dump' / tag) for tag in tags}
        checks[name+'_all_guest_captures_identical']=bool(tags) and all(
            (off / 'dump' / f'{tag}.{ext}').read_bytes()==(on / 'dump' / f'{tag}.{ext}').read_bytes()
            for tag in tags for ext in EXTENSIONS)
        checks[name+'_per_frame_state_trace_identical']=(off / 'state.csv').read_bytes()==(on / 'state.csv').read_bytes()
        checks[name+'_field_trace_identical']=(off / 'field.csv').read_bytes()==(on / 'field.csv').read_bytes()
        checks[name+'_cpu_trace_identical']=(off / 'cpu.csv').read_bytes()==(on / 'cpu.csv').read_bytes()
        checks[name+'_source_checkpoint_preserved']=digest(state)==report['source_checkpoint_sha256'][name]
    report['limits']=['Synthetic private PPU proves the scanline setting, not natural title slowdown removal',
        'Original actor allocation/OAM remains128; extra host-object API requires a title producer',
        'Overflow status changes at synthetic thresholds, so universal guest-state invariance is not claimed',
        'Natural coverage is finite town/house/David/two-Red-Slime battle copies; no owner progress run',
        'Headless/audio disabled; no new physical display/controller/audio certification']
    report['passed']=all(checks.values()) and all(c['exit']==0 and c['resumed'] for c in report['cases'].values())
    (base / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base); print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
