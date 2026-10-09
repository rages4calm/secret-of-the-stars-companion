"""ROM-free exact-function host buffer and allocation-fault probes. No game launch or source edits."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'local/evidence' / ('host-buffer-check-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
RUNTIME = ROOT / 'local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src'
FILES = {
    'presentation': ROOT / 'native/foundation/src/foundation_presentation.c',
    'scale': ROOT / 'native/foundation/src/foundation_scale2x.c',
    'hd': ROOT / 'native/foundation/src/foundation_hd_ui.c',
    'wide': ROOT / 'native/foundation/src/foundation_wide.c',
    'state': ROOT / 'native/foundation/src/foundation_state.c',
    'host': RUNTIME / 'desktop/host_main.c',
    'gl': RUNTIME / 'desktop/opengl.c',
    'dsp': RUNTIME / 'snes/dsp.c',
    'dsp_header': RUNTIME / 'snes/dsp.h',
    'rtl': RUNTIME / 'common_rtl.c',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def function(text, signature):
    start = text.index(signature)
    opening = text.index('{', start)
    while ';' in text[start:opening]:
        start = text.index(signature, start + len(signature))
        opening = text.index('{', start)
    depth = 1
    for end in range(opening + 1, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if not depth: return text[start:end + 1]
    raise AssertionError(signature)

def main():
    global OUT
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate-dir',type=Path,help='Read-only directory containing host_main.c and opengl.c overrides; baseline controls are also supported.')
    parser.add_argument('--output',type=Path,help='Private evidence directory; default is a fresh ignored local/evidence directory.')
    args=parser.parse_args()
    if args.output:
        OUT=args.output.resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.candidate_dir:
        FILES['host']=args.candidate_dir.resolve()/'host_main.c'
        FILES['gl']=args.candidate_dir.resolve()/'opengl.c'
    hashes = {str(p): sha(p) for p in FILES.values()}
    sources = {k:p.read_text(encoding='utf-8') for k,p in FILES.items()}
    repaired = 'static bool AllocateAudioBuffer(' in sources['host']
    draw = function(sources['presentation'], 'int FoundationPresentationDraw(')
    hd = function(sources['hd'], 'void FoundationHdUiDraw(')
    blend = function(sources['hd'], 'static uint32_t blend(')
    scale = sources['scale'].replace('#include "foundation_scale2x.h"', '')
    presentation = r'''
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
static int enhanced_pixels,battle_info,hidden,hd_enabled;
#define enabled hd_enabled
static unsigned frame_number,snes_frame_counter;
static uint8_t g_ram[131072];
typedef struct Binding { uint32_t rgb; uint8_t tile,u,v,valid; } Binding;
static Binding bindings[224][256];
static uint32_t palettes[224][4];
static uint8_t atlas[8][32][32][3];
static unsigned replaced;
static void snes_ovl_fill_rect(uint32_t*p,int s,int h,int x,int y,int w,int z,uint32_t c){(void)p;(void)s;(void)h;(void)x;(void)y;(void)w;(void)z;(void)c;}
static void snes_ovl_stroke_rect(uint32_t*p,int s,int h,int x,int y,int w,int z,uint32_t c){(void)p;(void)s;(void)h;(void)x;(void)y;(void)w;(void)z;(void)c;}
static void snes_ovl_draw_text(uint32_t*p,int s,int h,int x,int y,const char*t,uint32_t c,int n){(void)p;(void)s;(void)h;(void)x;(void)y;(void)t;(void)c;(void)n;}
static void FoundationJournalDraw(uint8_t*d,size_t p,int w,int h){(void)d;(void)p;(void)w;(void)h;}
int FoundationHdUiEnabled(void){return hd_enabled;}
int FoundationPresentationScale(void){return hd_enabled?4:enhanced_pixels?2:1;}
''' + scale + '\n' + blend + '\n' + hd + '\n' + draw + r'''
static uint8_t *guarded(size_t bytes,void **base){
 size_t pages=(bytes+4095)&~(size_t)4095;
 *base=VirtualAlloc(NULL,pages+8192,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
 assert(*base); DWORD old;
 assert(VirtualProtect(*base,4096,PAGE_NOACCESS,&old));
 assert(VirtualProtect((uint8_t*)*base+4096+pages,4096,PAGE_NOACCESS,&old));
 /* End-align exact caller capacity against trailing no-access page. */
 return (uint8_t*)*base+4096+pages-bytes;
}
int main(void){
 SetErrorMode(3); unsigned cases=0; uint64_t pixels=0,hd_pixels=0;
 int widths[]={400,256,400,256},padding[]={0,16,64};
 for(unsigned step=0;step<4;step++) for(int ep=0;ep<2;ep++) for(int hdmode=0;hdmode<2;hdmode++) for(int pad=0;pad<3;pad++){
  int w=widths[step],h=224; enhanced_pixels=ep;hd_enabled=hdmode;
  int factor=FoundationPresentationScale(),ow=w*factor,oh=h*factor;
  size_t pitch=(size_t)ow*4+padding[pad],bytes=pitch*oh;
  void *srcbase,*dstbase; uint32_t *src=(uint32_t*)guarded((size_t)w*h*4,&srcbase);
  uint8_t *dst=guarded(bytes,&dstbase); memset(dst,0xa5,bytes);
  for(int i=0;i<w*h;i++)src[i]=0xff112233;
  memset(bindings,0,sizeof(bindings));
  assert(FoundationPresentationDraw(dst,pitch,(uint8_t*)src,w,h,0.5)==1);
  for(int y=0;y<oh;y++){
   uint32_t *row=(uint32_t*)(dst+y*pitch);
   for(int x=0;x<ow;x++){assert(row[x]==0xff112233);pixels++;}
   for(size_t b=(size_t)ow*4;b<pitch;b++)assert(dst[y*pitch+b]==0xa5);
  }
  if(hdmode){
   for(int y=0;y<224;y++)for(int x=0;x<256;x++){
    bindings[y][x]=(Binding){0x112233,(uint8_t)((x&7)|((x&8)?0x40:0)|((y&8)?0x80:0)),(uint8_t)(x&7),(uint8_t)(y&7),1};
   }
   for(int y=0;y<224;y++)palettes[y][1]=0x445566;
   for(int t=0;t<8;t++)for(int v=0;v<32;v++)for(int u=0;u<32;u++)atlas[t][v][u][0]=255;
   replaced=0;
   assert(FoundationPresentationDraw(dst,pitch,(uint8_t*)src,w,h,1)==1);
   assert(replaced==224*256);hd_pixels+=(uint64_t)replaced*16;
   int left=(w-256)/2*4;
   for(int y=0;y<oh;y++)for(int x=0;x<ow;x++){
    uint32_t expected=x>=left&&x<left+1024?0xff445566:0xff112233;
    assert(((uint32_t*)(dst+y*pitch))[x]==expected);
   }
   for(int y=0;y<oh;y++)for(size_t b=(size_t)ow*4;b<pitch;b++)assert(dst[y*pitch+b]==0xa5);
  }
  VirtualFree(srcbase,0,MEM_RELEASE);VirtualFree(dstbase,0,MEM_RELEASE);cases++;
 }
 printf("{\"cases\":%u,\"flat_pixels_checked\":%llu,\"hd_binding_pixels_checked\":%llu}\n",cases,(unsigned long long)pixels,(unsigned long long)hd_pixels);return 0;
}
'''
    fill = function(sources['host'], 'static void FillAudioBuffer(')
    callback = function(sources['host'], 'static void SDLCALL AudioStreamCallback(')
    gl = function(sources['gl'], 'static void OpenGLRenderer_BeginDraw(')
    gl_end = function(sources['gl'], 'static void OpenGLRenderer_EndDraw(')
    gl_destroy = function(sources['gl'], 'static void OpenGLRenderer_Destroy(')
    audio_alloc_function=''
    if repaired:
        audio_alloc_function=function(sources['host'],'static bool AllocateAudioBuffer(')
        audio_alloc='    assert(AllocateAudioBuffer(have.freq,have.channels) == !fail);'
    else:
        audio_alloc = sources['host'][sources['host'].index('    g_frames_per_block = (534 * have.freq'):]
        audio_alloc = audio_alloc[:audio_alloc.index('\n    host_report_breadcrumb')]
    faults = r'''
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <assert.h>
#include <limits.h>
#define SNESRECOMP_SDL3 1
#define SDLCALL
#define SDL_AUDIO_S16 0
#define SNESRECOMP_SDL_MIX_MAXVOLUME 128
#define HOST_AUDIO_PREFILL 2136u
#define IntMin(a,b) ((a)<(b)?(a):(b))
typedef uint8_t uint8,Uint8;typedef int16_t int16;typedef int SDL_atomic_t,SDL_AudioStream;
static uint8 *g_audiobuffer,*g_audiobuffer_cur,*g_audiobuffer_end,*g_audio_stream_buffer;
static size_t g_audio_stream_buffer_size;
static int g_frames_per_block,g_audio_channels=2,g_audio_mutex,g_sdl_audio_mixer_volume=128;
static uint64_t g_audio_callback_count;static bool g_audio_primed;static FILE*g_audio_capture;
static struct{struct{void*dsp;}*apu;} machine;static void *apu_storage;static typeof(machine)*g_snes=&machine;
static int SDL_AtomicCAS(int*p,int a,int b){if(*p!=a)return 0;*p=b;return 1;}
#define host_report_breadcrumb(...) ((void)0)
#define Die(...) abort()
static int snesrecomp_sdl_lock_mutex(int m){(void)m;return 1;}
static void SDL_UnlockMutex(int m){(void)m;}
static uint32_t dsp_available(void*d){(void)d;return 0;}
static void audio_trace_on_output_underflow(uint32_t a,int f){(void)a;(void)f;}
static void RtlRenderAudio(int16*p,int n,int c){memset(p,0,(size_t)n*c*2);}
#define SDL_memset memset
static void SDL_MixAudio(void*a,void*b,int f,int n,float v){(void)a;(void)b;(void)f;(void)n;(void)v;}
static unsigned puts_count,alloc_calls;static int fail_alloc;
static void*task_malloc(size_t s){alloc_calls++;return fail_alloc?NULL:malloc(s);}
static void*task_realloc(void*p,size_t s){alloc_calls++;return fail_alloc?NULL:realloc(p,s);}
static void*task_calloc(size_t n,size_t s){alloc_calls++;return fail_alloc?NULL:calloc(n,s);}
static void SDL_PutAudioStreamData(SDL_AudioStream*s,void*p,int n){(void)s;(void)p;(void)n;puts_count++;}
static uint8 *g_screen_buffer;static size_t g_screen_buffer_size;static int g_draw_width,g_draw_height;
/* Renderer services are spies: an invalid-draw guard must reach NONE. */
static unsigned gl_calls,swaps,null_uploads;
typedef struct{int x,y,width,height;}SnesDisplayViewport;
static int g_window,g_program,g_VAO,g_want_screenshot;static double g_screenshot_flash_start_time=-1;
static void*g_glsl_shader;static struct{int width,height,gl_texture;}g_texture;
static struct{int display_aspect,ignore_aspect_ratio,linear_filtering;}g_config;
static void(*g_compute_viewport)(int,int,int,int,SnesDisplayViewport*);
static void snesrecomp_sdl_get_drawable_size(int w,int*x,int*y){(void)w;*x=1920;*y=1080;}
static int SnesDisplayAspect_Clamp(int a){return a;}
static void SnesDisplayAspect_ComputeViewport(int a,int b,int c,int d,int e,int f,int g,SnesDisplayViewport*v){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;*v=(SnesDisplayViewport){0,0,1920,1080};}
#define GL_TEXTURE_2D 1
#define GL_BGRA 2
#define GL_UNSIGNED_INT_8_8_8_8_REV 3
#define GL_RGBA 4
#define GL_COLOR_BUFFER_BIT 5
#define GL_LINEAR 6
#define GL_NEAREST 7
#define GL_TEXTURE_MIN_FILTER 8
#define GL_TEXTURE_MAG_FILTER 9
#define GL_TRIANGLE_STRIP 10
#define glBindTexture(...) (++gl_calls)
#define glClearColor(...) (++gl_calls)
#define glClear(...) (++gl_calls)
#define glViewport(...) (++gl_calls)
#define glUseProgram(...) (++gl_calls)
#define glBindVertexArray(...) (++gl_calls)
#define glDrawArrays(...) (++gl_calls)
static void glTexParameteri(int a,int b,int c){(void)a;(void)b;(void)c;gl_calls++;}
static void glTexSubImage2D(int a,int b,int c,int d,int e,int f,int g,int h,void*p){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;(void)h;gl_calls++;null_uploads+=!p;}
static void glTexImage2D(int a,int b,int c,int d,int e,int f,int g,int h,void*p){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;(void)h;gl_calls++;null_uploads+=!p;}
static void GlslShader_Render(void*s,void*t,int a,int b,int c,int d){(void)s;(void)t;(void)a;(void)b;(void)c;(void)d;gl_calls++;}
static void SaveScreenshotBmp(int a,int b){(void)a;(void)b;}
static double MonotonicSeconds(void){return 0;}
static int DrawScreenshotFlash(double t){(void)t;return 0;}
static void SDL_GL_SwapWindow(int w){(void)w;swaps++;}
''' + fill + '\n#define realloc task_realloc\n' + callback + '\n#undef realloc\n#define malloc task_malloc\n' + gl + '\n#undef malloc\n' + gl_end + '\n' + gl_destroy + '\n#define calloc task_calloc\n' + audio_alloc_function + '\n#undef calloc\n' + r'''
static void init_audio(int fail){struct {int freq,channels;}have={48000,2};fail_alloc=fail;
#define calloc task_calloc
''' + audio_alloc + r'''
#undef calloc
}
int main(int argc,char**argv){
 SetErrorMode(3); struct{void*dsp;} apu={NULL};machine.apu=(void*)&apu;(void)apu_storage;
 if(argc>1&&!strcmp(argv[1],"audio-null")){
  init_audio(1);assert(!g_audiobuffer);uint8_t output[128];FillAudioBuffer(output,sizeof(output));return 99;
 }
 init_audio(0);assert(g_audiobuffer);assert(g_frames_per_block==800);
 uint8 *p=NULL;int pitch=0;
 fail_alloc=0;OpenGLRenderer_BeginDraw(256,224,&p,&pitch);assert(p&&pitch==1024);
 fail_alloc=1;OpenGLRenderer_BeginDraw(1600,896,&p,&pitch);assert(!p&&pitch==6400);
 unsigned after_fail=alloc_calls;
 fail_alloc=0;OpenGLRenderer_BeginDraw(1600,896,&p,&pitch);assert(!p&&alloc_calls==after_fail);
 assert(g_screen_buffer_size==1600u*896u);
 AudioStreamCallback(NULL,NULL,32,32);assert(g_audio_stream_buffer&&g_audio_stream_buffer_size==32&&puts_count==1);
 uint8*old=g_audio_stream_buffer;fail_alloc=1;AudioStreamCallback(NULL,NULL,1024,1024);
 assert(g_audio_stream_buffer==old&&g_audio_stream_buffer_size==32&&puts_count==1);
 fail_alloc=0;AudioStreamCallback(NULL,NULL,1024,1024);
 assert(g_audio_stream_buffer&&g_audio_stream_buffer_size==1024&&puts_count==2);
 free(g_audio_stream_buffer);free(g_audiobuffer);
 puts("{\"gl_failed_allocation_same_size_never_retries\":true,\"audio_stream_realloc_failure_preserves_and_retries\":true}");return 0;
}
'''
    if repaired:
        faults=faults[:faults.index('int main(int argc,char**argv)')] + r'''
int main(int argc,char**argv){
 (void)argc;(void)argv;SetErrorMode(3); struct{void*dsp;} apu={NULL};machine.apu=(void*)&apu;(void)apu_storage;
 fail_alloc=1;assert(!AllocateAudioBuffer(48000,2));
 assert(!g_audiobuffer&&!g_audiobuffer_cur&&!g_audiobuffer_end);
 int badfreq[]={INT_MIN,-1,0},badchannels[]={INT_MIN,-1,0,1,3,INT_MAX};
 for(unsigned i=0;i<3;i++)assert(!AllocateAudioBuffer(badfreq[i],2));
 for(unsigned i=0;i<6;i++)assert(!AllocateAudioBuffer(48000,badchannels[i]));
 unsigned audio_rates=0;int rates[]={8000,11025,22050,32000,32040,44100,48000,96000,192000};
 for(unsigned i=0;i<9;i++){
  fail_alloc=0;assert(AllocateAudioBuffer(rates[i],2));assert(g_audiobuffer&&g_audiobuffer_cur==g_audiobuffer&&g_audiobuffer_end==g_audiobuffer);
  uint8_t output[128];FillAudioBuffer(output,sizeof(output));
  assert(g_audiobuffer_cur>=g_audiobuffer&&g_audiobuffer_end==g_audiobuffer+(size_t)g_frames_per_block*4);
  free(g_audiobuffer);g_audiobuffer=g_audiobuffer_cur=g_audiobuffer_end=NULL;audio_rates++;
 }
 init_audio(0);assert(g_frames_per_block==800);
 uint8*p=NULL;int pitch=0;fail_alloc=0;
 OpenGLRenderer_BeginDraw(256,224,&p,&pitch);assert(p&&pitch==1024);OpenGLRenderer_EndDraw();assert(swaps==1&&!null_uploads);
 uint8*old=p;size_t oldcapacity=g_screen_buffer_size;unsigned rendered=gl_calls;
 fail_alloc=1;OpenGLRenderer_BeginDraw(1600,896,&p,&pitch);
 assert(!p&&pitch==0&&g_screen_buffer==old&&g_screen_buffer_size==oldcapacity&&!g_draw_width&&!g_draw_height);
 OpenGLRenderer_EndDraw();assert(gl_calls==rendered&&swaps==1&&!null_uploads);
 unsigned after_fail=alloc_calls;fail_alloc=0;OpenGLRenderer_BeginDraw(1600,896,&p,&pitch);
 assert(p&&pitch==6400&&alloc_calls==after_fail+1&&g_screen_buffer_size==1600u*896u);
 OpenGLRenderer_EndDraw();assert(swaps==2&&!null_uploads);
 int bad[]={INT_MIN,-1,0,INT_MAX};
 unsigned invalid=0;
 for(unsigned i=0;i<4;i++){
  rendered=gl_calls;OpenGLRenderer_BeginDraw(bad[i],224,&p,&pitch);assert(!p&&!pitch);OpenGLRenderer_EndDraw();assert(gl_calls==rendered);invalid++;
  if(i<3){OpenGLRenderer_BeginDraw(400,bad[i],&p,&pitch);assert(!p&&!pitch);OpenGLRenderer_EndDraw();assert(gl_calls==rendered);invalid++;}
 }
 OpenGLRenderer_BeginDraw(400,224,NULL,&pitch);OpenGLRenderer_EndDraw();
 OpenGLRenderer_BeginDraw(400,224,&p,NULL);OpenGLRenderer_EndDraw();
 OpenGLRenderer_Destroy();assert(!g_screen_buffer&&!g_screen_buffer_size&&!g_draw_width&&!g_draw_height);
 OpenGLRenderer_Destroy();
 fail_alloc=0;OpenGLRenderer_BeginDraw(256,224,&p,&pitch);assert(p&&pitch==1024);OpenGLRenderer_Destroy();
 AudioStreamCallback(NULL,NULL,32,32);assert(g_audio_stream_buffer&&g_audio_stream_buffer_size==32&&puts_count==1);
 old=g_audio_stream_buffer;fail_alloc=1;AudioStreamCallback(NULL,NULL,1024,1024);
 assert(g_audio_stream_buffer==old&&g_audio_stream_buffer_size==32&&puts_count==1);
 fail_alloc=0;AudioStreamCallback(NULL,NULL,1024,1024);
 assert(g_audio_stream_buffer&&g_audio_stream_buffer_size==1024&&puts_count==2);
 free(g_audio_stream_buffer);free(g_audiobuffer);
 printf("{\"checked_audio_rates\":%u,\"rejected_audio_layouts\":9,\"gl_invalid_dimensions\":%u,\"gl_failed_allocation_retry_passed\":true,\"gl_failed_draw_calls\":0,\"gl_null_uploads\":%u,\"gl_destroy_reinitialize_passed\":true,\"audio_stream_realloc_failure_preserves_and_retries\":true}\n",audio_rates,invalid,null_uploads);return 0;
}
'''
    else:
        faults=faults.replace('unsigned after_fail=alloc_calls;','OpenGLRenderer_EndDraw();assert(null_uploads==1&&swaps==1);\n unsigned after_fail=alloc_calls;')
    producer=sources['dsp'][sources['dsp'].index('  uint32_t fill = dsp->sampleWrite - dsp->sampleRead;'):]
    producer=producer[:producer.index('  dsp->evenCycle')]
    ring=r'''
#include <windows.h>
#include <assert.h>
#include <limits.h>
#include "snes/dsp.h"
static unsigned dropped_count;
static void audio_trace_on_sample(int16_t l,int16_t r,int dropped,uint32_t fill){(void)l;(void)r;assert(fill<=8192);dropped_count+=dropped;}
static void audio_trace_on_consume(uint32_t b,uint32_t n,uint32_t a){(void)b;(void)n;assert(a<=8192);}
''' + '\n'.join(function(sources['dsp'],signature) for signature in [
        'uint32_t dsp_available(', 'void dsp_peek(', 'void dsp_advance(',
        'uint32_t dsp_getSamples(', 'void dsp_output_ring_save(', 'void dsp_output_ring_restore(']) + '\nstatic void produce(Dsp*dsp,int totalL,int totalR){\n' + producer + r'''
}
int main(void){
 SetErrorMode(3);size_t bytes=sizeof(Dsp),pages=(bytes+4095)&~(size_t)4095;
 uint8_t*base=VirtualAlloc(NULL,pages+8192,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);assert(base);DWORD old;
 assert(VirtualProtect(base,4096,PAGE_NOACCESS,&old));assert(VirtualProtect(base+4096+pages,4096,PAGE_NOACCESS,&old));
 Dsp*dsp=(Dsp*)(base+4096+pages-bytes);memset(dsp,0,bytes);
 int16_t*output=malloc(DSP_SAMPLE_RING*4);assert(output);unsigned pairs=0;
 uint32_t starts[]={0,UINT32_MAX-4095,UINT32_MAX-1};
 for(unsigned c=0;c<3;c++){
  dsp->sampleRead=dsp->sampleWrite=starts[c];
  for(int i=0;i<8192;i++)produce(dsp,i,-i);
  assert(dsp_available(dsp)==8192);uint32_t write=dsp->sampleWrite;
  produce(dsp,123,456);assert(dsp->sampleWrite==write&&dsp_available(dsp)==8192);
  DspOutputRing saved;dsp_output_ring_save(dsp,&saved);memset(dsp->sampleBuffer,0,sizeof(dsp->sampleBuffer));dsp_output_ring_restore(dsp,&saved);
  assert(dsp_getSamples(dsp,output,-1)==0&&dsp_getSamples(dsp,output,0)==0);
  assert(dsp_getSamples(dsp,output,8192)==8192);
  for(int i=0;i<8192;i++){assert(output[i*2]==i&&output[i*2+1]==-i);pairs++;}
  assert(!dsp_available(dsp));
  for(int i=0;i<64;i++)produce(dsp,i,-i);
  int16_t l,r;dsp_peek(dsp,63,&l,&r);assert(l==63&&r==-63);pairs++;
  dsp_advance(dsp,UINT32_MAX);assert(!dsp_available(dsp));
 }
 assert(dropped_count==3);free(output);VirtualFree(base,0,MEM_RELEASE);
 printf("{\"wraparound_cases\":3,\"stereo_pairs_checked\":%u,\"bounded_full_ring_drops\":%u,\"save_restore_and_clamped_retire_passed\":true}\n",pairs,dropped_count);return 0;
}
'''
    compiler = Path.home()/'.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe'
    results = {}
    for name,source in [('presentation',presentation),('faults',faults),('ring',ring)]:
        path=OUT/(name+'.c');path.write_text(source,encoding='utf-8')
        exe=OUT/(name+'.exe')
        command=[str(compiler),'-std=gnu11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-variable','-Wno-unused-function','-fsanitize=undefined','-fsanitize-trap=all','-I'+str(RUNTIME),str(path),'-o',str(exe)]
        built=subprocess.run(command,capture_output=True,text=True,timeout=30)
        (OUT/(name+'-compile.log')).write_text(built.stdout+built.stderr,encoding='utf-8')
        assert built.returncode==0,built.stderr
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
        (OUT/(name+'-run.log')).write_text(run.stdout+run.stderr,encoding='utf-8')
        assert run.returncode==0,(name,run.returncode,run.stderr)
        results[name]=json.loads(run.stdout)
    if not repaired:
        fault=subprocess.run([str(OUT/'faults.exe'),'audio-null'],capture_output=True,text=True,timeout=10)
        results['audio_null_fault']={'child_exit_code':fault.returncode,'fault_reproduced':fault.returncode not in [0,99]}
    report={'passed':True if repaired else results['audio_null_fault']['fault_reproduced'],'source_override':bool(args.candidate_dir),'allocation_guard_present':repaired,'results':results,'source_hashes':hashes,
            'sources_unchanged':all(sha(Path(p))==v for p,v in hashes.items()),
            'undefined_behavior_traps':True,'ROM_free':True,'checker_sha256':sha(Path(__file__)),
            'limits':'Exact extracted production functions, stubbed external overlays/SDL services. No actual game/GPU/audio-device/campaign run.'}
    report['passed'] &= report['sources_unchanged']
    (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['passed','results','sources_unchanged']},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
