"""Bounded actual HD frame-art proof, copied fixtures and private module guards."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import time
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp'
GUEST = ('wram.bin', 'vram.bin', 'sram.bin', 'oam.bin', 'cgram.bin', 'fb.bgrx', 'regs.json')

HARNESS = r'''
#include "foundation_hd_ui.c"
Snes *g_snes;
uint8 g_ram[0x20000];
const uint8 *g_rom;
int snes_frame_counter;
static uint32_t raster[224*256],logical[224*256],output[896*1024];
static void setup(Ppu *p) {
  memset(p,0,sizeof(*p));memset(raster,0,sizeof(raster));memset(logical,0,sizeof(logical));memset(output,0,sizeof(output));
  p->bgmode=9;p->inidisp=15;p->bgTileAdr=0x400;p->bgXsc[2]=0x51;p->screenEnabled[0]=4;
  p->renderBuffer=(uint8_t *)raster;p->renderPitch=256*4;p->cgram[1]=0x0800;p->cgram[2]=0x4210;p->cgram[3]=0x7fff;
  memcpy((uint8_t *)p->vram+0x8a00,g_rom+0x28a00,128);p->vram[0x5000]=0x20a4;
  for(unsigned x=0;x<8;x++) {
    unsigned bits=p->vram[0x4000+0xa4*8+1],shift=7-x;
    unsigned color=((bits>>shift)&1)|((bits>>(shift+8)&1)<<1);
    raster[x]=logical[x]=rgb15(p->cgram[color]);
  }
}
int main(int argc,char **argv) {
  if(argc!=2)return 9;FILE*f=fopen(argv[1],"rb");if(!f)return 8;
  uint8_t *rom=malloc(1572864),*foreign=malloc(1572864);fread(rom,1,1572864,f);fclose(f);
  memcpy(foreign,rom,1572864);foreign[0]^=1;
  Snes snes={0};Cart cart={0};snes.cart=&cart;cart.romImageSize=1572864;g_snes=&snes;g_rom=rom;g_ram[0x20]=1;
  enabled=1;make_art();Ppu *p=calloc(1,sizeof(*p));
  const char *names[]={"valid","resource_changed","mode","charbase","map","hidden_bg3","blank","dim","mosaic","setini","window","color_math","clip","direct_color","title","host_foreground","foreign_rom","out_of_range_line"};
  for(unsigned test=0;test<18;test++) {
    g_rom=rom;g_ram[0x20]=1;setup(p);
    switch(test) {
      case 1:p->vram[0x4500]^=1;break;case 2:p->bgmode=1;break;case 3:p->bgTileAdr=0x300;break;
      case 4:p->bgXsc[2]=0x50;break;case 5:p->screenEnabled[0]=0;break;case 6:p->inidisp=0x8f;break;
      case 7:p->inidisp=14;break;case 8:p->mosaic=1;break;case 9:p->setini=1;break;
      case 10:p->windowsel=0x100;break;case 11:p->cgadsub=4;break;case 12:p->cgwsel=0x40;break;
      case 13:p->cgwsel=1;break;case 14:g_ram[0x20]=0;break;case 15:memset(logical,0,sizeof(logical));break;
      case 16:g_rom=foreign;break;
    }
    FoundationHdUiBeginFrame();FoundationHdUiObserve(p,test==17?225:1,NULL);
    FoundationHdUiDraw((uint8_t *)output,1024*4,logical,256,224);
    printf("%s,%u\n",names[test],replaced);
  }
  free(p);free(rom);free(foreign);return 0;
}
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_reference(base, reference, report):
    """Compare qualified output directly; logs and wall-clock timings excluded."""
    previous=json.loads((reference/'report.json').read_text())
    details={'directory':str(reference.resolve()),'executable_sha256':previous['executable_sha256'],
             'cases':{},'limits':['Host logs, elapsed times, executable bytes and diagnostic source copies are expected to differ']}
    for name in report['cases']:
        current,old=base/name,reference/name
        result={}
        groups={'guest': [p.relative_to(current) for p in (current/'dump').iterdir()
                         if any(p.name.endswith('.'+ext) for ext in GUEST)],
                'composed': [p.relative_to(current) for p in (current/'captures').glob('*.bgrx')],
                'traces': [Path(filename) for filename in ('state.csv','field.csv','cpu.csv','hd.csv') if (current/filename).exists()]}
        for group,paths in groups.items():
            missing=[str(path) for path in paths if not (old/path).exists()]
            changed=[str(path) for path in paths if (old/path).exists() and (current/path).read_bytes()!=(old/path).read_bytes()]
            if group=='guest':
                old_paths={p.relative_to(old) for p in (old/'dump').iterdir() if any(p.name.endswith('.'+ext) for ext in GUEST)}
            elif group=='composed': old_paths={p.relative_to(old) for p in (old/'captures').glob('*.bgrx')}
            else: old_paths={Path(filename) for filename in ('state.csv','field.csv','cpu.csv','hd.csv') if (old/filename).exists()}
            coverage=set(paths)==old_paths
            result[group]={'files':len(paths),'coverage_identical':coverage,'missing':missing,'changed':changed,
                           'identical':bool(paths) and coverage and not missing and not changed}
            report['checks']['reference_'+name+'_'+group+'_byte_identical']=result[group]['identical']
        details['cases'][name]=result
    report['checks']['reference_case_coverage_identical']=set(previous['cases'])==set(report['cases'])
    report['reference_comparison']=details


def image(path):
    _, width, height = map(int, re.search(r'frame-(\d+)-(\d+)x(\d+)', path.name).groups())
    return Image.frombytes('RGB', (width, height), path.read_bytes(), 'raw', 'BGRX')


def surface_metrics(off, on):
    a, b = image(off), image(on)
    nearest = a.resize(b.size, Image.Resampling.NEAREST)
    aa, bb = np.asarray(nearest), np.asarray(b)
    changed = np.any(aa != bb, axis=2)
    blocks = changed.reshape(b.height//4, 4, b.width//4, 4).any(axis=(1, 3))
    # Added detail inside a nearest-expanded 2x source pixel is an actual 4x
    # authored feature; output size alone cannot satisfy this assertion.
    quarters = bb.reshape(b.height//2, 2, b.width//2, 2, 3)
    finer = np.any(quarters != quarters[:, :1, :, :1, :], axis=(1, 3, 4))
    colors = {tuple(v) for _, v in b.getcolors(b.width*b.height)}
    original_colors = {tuple(v) for _, v in nearest.getcolors(b.width*b.height)}
    return {'changed_pixels': int(changed.sum()), 'changed_base_pixels': int(blocks.sum()),
            'finer_than_enhanced2x_blocks': int(finer.sum()),
            'new_colors': len(colors-original_colors), 'width': b.width, 'height': b.height}, blocks


def stable_border_mask(prefix, width):
    """Independent snapshot identity mask, for stable no-HDMA menu captures."""
    regs = json.loads(Path(str(prefix)+'.regs.json').read_text())
    vram = Path(str(prefix)+'.vram.bin').read_bytes()
    mask = np.zeros((224, width), dtype=bool)
    if regs['bgmode'] != 9 or regs['bgsc'][2] != 0x51 or regs['bg_tile_adr'] != 0x400:
        return mask
    for y in range(224):
        sy = (y+1+regs['vscroll'][2]) & 255
        for x in range(256):
            sx = (x+regs['hscroll'][2]) & 511
            offset = 0xa000+(sx//8 & 31)*2+(sy//8)*64+(2048 if sx//8 >= 32 else 0)
            word = struct.unpack_from('<H', vram, offset)[0]
            if 0xa0 <= (word & 1023) <= 0xa7 and word & 0x3c00 == 0x2000:
                u, v = sx & 7, sy & 7
                if word & 0x4000: u = 7-u
                if word & 0x8000: v = 7-v
                bits = struct.unpack_from('<H', vram, 0x8000+(word & 1023)*16+v*2)[0]
                if ((bits >> (7-u)) & 1) | ((bits >> (15-u)) & 1):
                    mask[y, x+(width-256)//2] = True
    return mask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=PROOF/'build-menu/SecretOfTheStarsSNESRecomp.exe')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--reference',type=Path,help='Earlier qualified report directory for exact guest/trace/composed comparison')
    parser.add_argument('--cc', type=Path, default=Path.home()/'.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe')
    args = parser.parse_args()
    base = (args.out or ROOT/'local/runs'/('hd-menu-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    base.mkdir(exist_ok=True)
    frozen = base/'candidate.exe'
    if args.exe.resolve() != frozen.resolve(): shutil.copy2(args.exe, frozen)
    report = {'executable_sha256': digest(frozen), 'cases': {}, 'checks': {}, 'surfaces': {}}
    checks = report['checks']
    fixtures = {'house': ROOT/'local/runs/likado-inside-a/saves/save0.sav',
                'town': ROOT/'local/runs/likado-east-a/saves/save0.sav',
                'battle': ROOT/'local/runs/world-cave-a/saves/save0.sav'}
    source_hashes = {name: digest(path) for name,path in fixtures.items()}
    # Original waits expose the frame slide; FastMenus retains its separately
    # qualified batching. HD is paired against exactly the same path.
    menu = ('wait 30\ndump field\npress b 1\nwait 8\ndump opening\nwait 80\ndump main\n'
            'press down 1\nwait 12\npress down 1\nwait 12\npress down 1\nwait 12\n'
            'press a 1\nwait 90\ndump status\npress down 1\nwait 12\ndump sort\n'
            'press b 1\nwait 40\ndump returned\npress b 1\nwait 8\ndump closing\nwait 90\ndump closed\nquit\n')
    sequence = [10,30,32,35,39,45,48,50,52,54,56,58,60,90,119,160,200,250,262,290,310,312,314,316,318,320,350,390,410,450,480,500,600]

    def run(name, state, script, hd, wide=0, fast=0, enhanced=1, save=None, load=None, journal=0):
        directory = base/name;directory.mkdir();(directory/'dump').mkdir();(directory/'captures').mkdir()
        shutil.copy2(frozen,directory/'game.exe')
        if state: shutil.copy2(state,directory/'resume.state')
        (directory/'input.txt').write_text(script)
        (directory/'config.ini').write_text('[Graphics]\nRenderer=software\nNewRenderer=1\nVSync=0\n'
            '[Sound]\nEnableAudio=0\n[General]\nDisableFrameDelay=1\nAutosave=0\nRunAhead=0\n'
            '[GamepadMap]\nEnableGamepad1=0\nEnableGamepad2=0\n')
        env = {k:v for k,v in os.environ.items() if not k.startswith('SNESRECOMP_')}
        env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SNESRECOMP_DUMP_DIR=str(directory/'dump'),
            SNESRECOMP_STATE_TRACE=str(directory/'state.csv'),SNESRECOMP_FOUNDATION_TRACE=str(directory/'field.csv'),
            SNESRECOMP_FOUNDATION_CPU_TRACE=str(directory/'cpu.csv'),SNESRECOMP_FOUNDATION_BATTLE_INFO='0',
            SNESRECOMP_FOUNDATION_WIDE=str(wide),SNESRECOMP_FOUNDATION_ENHANCED_PIXELS=str(enhanced),
            SNESRECOMP_FOUNDATION_FAST_MENUS=str(fast),SNESRECOMP_FOUNDATION_JOURNAL=str(journal),
            SNESRECOMP_FOUNDATION_HD_MENU_FRAMES=str(hd),SNESRECOMP_FOUNDATION_HD_UI_TRACE=str(directory/'hd.csv'),
            SNESRECOMP_FOUNDATION_CAPTURE_SEQUENCE=','.join(map(str,sequence)),SNESRECOMP_FOUNDATION_CAPTURE_DIR=str(directory/'captures'))
        if save is not None: env.update(SNESRECOMP_OVERLAY_SELFTEST=str(save),SNESRECOMP_OVERLAY_SELFTEST_SAVEONLY='1')
        if load is not None: env.update(SNESRECOMP_OVERLAY_SELFTEST_LOADAT=str(load),SNESRECOMP_RUN_FRAMES=str(load+50))
        if journal: env['SNESRECOMP_FOUNDATION_JOURNAL_INPUT_TEST']='keyboard'
        command = [str(directory/'game.exe'),'--no-launcher','--rom',str(ROOT/'local/inputs/clean-usa.sfc')]
        if state: command += ['--resume-state',str(directory/'resume.state')]
        command += ['--script',str(directory/'input.txt')]
        with (directory/'host.log').open('w') as log:
            result = subprocess.run(command,cwd=directory,env=env,stdout=log,stderr=log,timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        trace = list(csv.reader((directory/'hd.csv').open())) if (directory/'hd.csv').exists() else []
        report['cases'][name] = {'exit': result.returncode,'resume_requested':bool(state),
            'resumed':'resume state loaded:' in (directory/'host.log').read_text(errors='replace'),
            'max_replaced_base_pixels':max((int(row[1]) for row in trace),default=0),
            'replacement_frames':sum(int(row[1])>0 for row in trace), 'trace_rows':len(trace)}
        return directory

    def pair(name, state, script, **kwargs):
        off=run(name+'-off',state,script,0,**kwargs);on=run(name+'-on',state,script,1,**kwargs)
        tags=[p.name[:-9] for p in (off/'dump').glob('*.wram.bin')]
        checks[name+'_all_guest_dumps_identical'] = bool(tags) and all((off/'dump'/f'{tag}.{ext}').read_bytes()==
            (on/'dump'/f'{tag}.{ext}').read_bytes() for tag in tags for ext in GUEST)
        for trace in ('state','field','cpu'):
            checks[name+'_'+trace+'_trace_identical']=(off/(trace+'.csv')).read_bytes()==(on/(trace+'.csv')).read_bytes()
        stats={}
        for p in sorted((on/'captures').glob('*.bgrx')):
            frame=int(p.name.split('-')[1]);original=list((off/'captures').glob(f'frame-{frame}-*.bgrx'))
            if len(original)!=1: raise RuntimeError('Missing paired capture '+str(frame))
            metrics,blocks=surface_metrics(original[0],p);stats[str(frame)]=metrics
            metrics['baseline_height']=image(original[0]).height
            if frame in (30,119,250,350,450): image(p).save(p.with_suffix('.png'))
        report['surfaces'][name]=stats
        checks[name+'_fourfold_output'] = bool(stats) and all(m['height']==896 and m['width'] in (1024,1600) for m in stats.values())
        checks[name+'_baseline_scale_preserved'] = all(m['baseline_height']==(448 if kwargs.get('enhanced',1) else 224) for m in stats.values())
        return off,on

    for name in ('house','town'):
        off,on=pair(name,fixtures[name],menu,wide=int(name=='town'))
        checks[name+'_art_used'] = report['cases'][name+'-on']['max_replaced_base_pixels']>0
        checks[name+'_genuine_finer_geometry_and_colors'] = any(m['finer_than_enhanced2x_blocks']>0 and m['new_colors']>0
            for m in report['surfaces'][name].values())
        # Independently recover stable main/status/sort resource masks. Moving
        # scanlines retain their live observer instead of this snapshot model.
        for frame,tag in ((119,'main'),(250,'status'),(262,'sort')):
            capture=next((on/'captures').glob(f'frame-{frame}-*.bgrx'))
            original=next((off/'captures').glob(f'frame-{frame}-*.bgrx'))
            _,blocks=surface_metrics(original,capture)
            mask=stable_border_mask(on/'dump'/tag,blocks.shape[1])
            checks[name+'_'+tag+'_changes_only_resource_border_pixels'] = bool(blocks.any()) and not bool((blocks & ~mask).any())
    checks['town_expanded400_integration'] = any(m['width']==1600 for m in report['surfaces']['town'].values())
    pair('fast-menu',fixtures['house'],menu,fast=1)
    checks['fast_menu_art_used']=report['cases']['fast-menu-on']['max_replaced_base_pixels']>0
    pair('original-pixels',fixtures['house'],menu,enhanced=0)
    checks['original_pixels_optional_hd_art_used']=report['cases']['original-pixels-on']['max_replaced_base_pixels']>0
    for name,state in [('title',None),('battle',fixtures['battle'])]:
        _,on=pair(name,state,'wait '+('600' if name=='title' else '92')+'\ndump end\nquit\n')
        checks[name+'_exact_nearest_fallback']=all(m['changed_pixels']==0 for m in report['surfaces'][name].values())
        checks[name+'_no_bound_art']=report['cases'][name+'-on']['max_replaced_base_pixels']==0
        if name=='title':
            report['cases']['title-on']['visible_nonblack_surface']=any(image(p).getbbox() is not None for p in (on/'captures').glob('*.bgrx'))
            report['cases']['title-on']['scope']='600-frame cold start; a black surface does not qualify visible title fallback'
    # A fresh copied state is saved mid-menu; cold restores must bind to current
    # raster state rather than retain a previous process's resource cache.
    saved=run('save-menu',fixtures['house'],menu,1,save=160)
    pair('cold-menu',saved/'saves/save0.sav','wait 92\ndump end\nquit\n')
    checks['cold_restored_menu_art_used']=report['cases']['cold-menu-on']['max_replaced_base_pixels']>0
    pair('rollback',fixtures['house'],menu,save=80,load=390)
    checks['rollback_actual_load_issued']='[overlay_selftest] load issued' in (base/'rollback-on/host.log').read_text(errors='replace')
    # Native journal foreground appears over an active opening menu. The same
    # guest path with the same J events is compared; module's second RGB guard
    # must protect host pixels even when BG3 under it contains border tiles.
    pair('journal-over-menu',fixtures['house'],menu,journal=1)
    checks['journal_covered_top_card_unmodified']=all(
        np.array_equal(np.asarray(image(next((base/'journal-over-menu-on/captures').glob(f'frame-{frame}-*.bgrx'))))[24:324,32:992],
            np.asarray(image(next((base/'journal-over-menu-off/captures').glob(f'frame-{frame}-*.bgrx'))).resize((1024,896),Image.Resampling.NEAREST))[24:324,32:992])
        for frame in (35,39,45,60))

    # Compile only an isolated actual-module control. Synthetic PPU memory and
    # a private altered ROM buffer never enter any player process/checkpoint.
    runtime=PROOF/'snesrecomp/runner/src'
    for filename in ('foundation_hd_ui.c','foundation_hd_ui.h'):
        shutil.copy2(ROOT/'native/foundation/src'/filename,base/filename)
    report['hd_source_sha256']=digest(base/'foundation_hd_ui.c')
    (base/'guard-control.c').write_text(HARNESS)
    command=[str(args.cc),'-std=c11','-O2','-I',str(base),'-I',str(runtime),str(base/'guard-control.c'),
             str(runtime/'sha256.c'),'-o',str(base/'guard-control.exe')]
    compiled=subprocess.run(command,capture_output=True,text=True)
    (base/'guard-compile.log').write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode: raise RuntimeError('Private module guard compile failed: '+str(base/'guard-compile.log'))
    guarded=subprocess.run([str(base/'guard-control.exe'),str(ROOT/'local/inputs/clean-usa.sfc')],capture_output=True,text=True,check=True)
    rows=list(csv.reader(guarded.stdout.splitlines()))
    report['private_module_guards']={row[0]:int(row[1]) for row in rows}
    checks['private_guard_positive_control']=int(rows[0][1])>0
    checks['private_invalid_resource_and_mode_guards_refuse']=all(int(row[1])==0 for row in rows[1:])
    checks['fixture_sources_preserved']=all(digest(path)==source_hashes[name] for name,path in fixtures.items())
    checks['all_processes_exited_zero']=all(c['exit']==0 and (not c['resume_requested'] or c['resumed']) for c in report['cases'].values())
    report['limits']=['Eight authored menu frame tiles only; no replacement terrain/font/actors or campaign HD claim',
        'Finite house/Likado main/status/sort slide/close copies and cold-start/battle fallback; no universal UI certification',
        'The title-named cold-start case is black through600; visible title fallback requires a separate fixture or desktop gate',
        'Fine-detail/colors proof compares authored4x surface to nearest-expanded enhanced2x, not output resolution alone',
        'Stable resource mask is an independent snapshot check; moving/HDMA bindings rely on actual per-line observation plus paired traces',
        'Private mutated resource/foreign-ROM guards are synthetic unit controls, never owner or gameplay mutations',
        'Copied cold save and actual host load exercised; interactive rewind timeline and physical-controller/display not newly tested']
    if args.reference: compare_reference(base,args.reference.resolve(strict=True),report)
    report['passed']=all(checks.values())
    (base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(base);print(json.dumps({'passed':report['passed'],'checks':checks,'executable_sha256':report['executable_sha256']},indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
