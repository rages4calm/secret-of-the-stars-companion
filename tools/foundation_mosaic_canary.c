#include FOUNDATION_PPU_SOURCE
#include <assert.h>
Snes *g_snes;
unsigned char g_snesrecomp_last_hdmaen;
int snes_frame_counter;
void ppu_draw_whole_line_legacy(Ppu *ppu, int y) { (void)ppu; (void)y; abort(); }
void WsShadowOnVramWrite(uint16_t addr, uint16_t value) { (void)addr; (void)value; abort(); }

bool WsShadowLayerActive(int layer) { (void)layer; return false; }
uint16_t WsShadowTile(int layer, int sx, uint32_t y, uint16_t hs, uint16_t addr, uint16_t tile) {
  (void)layer; (void)sx; (void)y; (void)hs; (void)addr; return tile;
}
#include "mosaic-reference.inc"

typedef struct Guarded {
  uint64_t before[16];
  PpuPixelPrioBufs buf;
  uint64_t after[16];
} Guarded;
static Ppu p;
static unsigned cases, words, phase_checks, parity_cases, parity_words, empty_cases;
static void guards(Guarded *g) {
  for (int i=0;i<16;i++) assert(g->before[i]==0xCAFE123456789ABCULL && g->after[i]==0xCAFE123456789ABCULL);
}
static void init(Guarded *g, int mode, int size, int oldsize, int wide, int window) {
  memset(&p,0,sizeof(p)); memset(g,0,sizeof(*g));
  for(int i=0;i<16;i++) g->before[i]=g->after[i]=0xCAFE123456789ABCULL;
  p.screenEnabled[0]=1; p.bgTileAdr=1; p.bgXsc[0]=0;
  p.extraLeftCur=p.extraRightCur=wide; p.extraLeftRight=wide;
  p.mosaic=((oldsize-1)<<4)|1; PpuRefreshMosaicModulo(&p);
  p.mosaic=((size-1)<<4)|1;
  if(window) {
    p.screenWindowed[0]=1; p.windowsel=kWindow1Enabled|kWindow1Inversed;
    p.window1left=13; p.window1right=241;
  }
  if(mode==7) {
    p.m7matrix[0]=p.m7matrix[3]=256;
    for(int i=0;i<0x8000;i++) p.vram[i]=(uint16_t)(0x0100 | 1);
  } else {
    for(int i=0;i<1024;i++) p.vram[i]=0;
    for(int i=0;i<16;i++) p.vram[0x1000+i]=0xffff;
  }
}
static void draw(Guarded *g,int mode,int y) {
  if(mode==4) PpuDrawBackground_4bpp_mosaic(&p,&g->buf,y,false,0,0x2000,0x1000);
  else if(mode==2) PpuDrawBackground_2bpp_mosaic(&p,&g->buf,y,false,0,0x2000,0x1000);
  else PpuDrawBackground_mode7(&p,&g->buf,y,false,0x1000);
}
int main(void) {
  Guarded g, reference;
  for(int size=1;size<=16;size++) {
    p.mosaic=(size-1)<<4; p.lastMosaicModulo=0; PpuRefreshMosaicModulo(&p);
    for(int x=-272;x<528;x++) {
      int phase=x%size; if(phase<0)phase+=size;
      assert(PpuMosaicAt(&p,x)==x-phase);
      assert(size-(x-PpuMosaicAt(&p,x))>0); phase_checks++;
    }
    for(int mode=2;mode<=7;mode+=(mode==2?2:3))
      for(int window=0;window<2;window++) for(int wide=0;wide<=272;wide+=272) {
        init(&g,mode,size,16,wide,window);
        PpuRefreshMosaicModulo(&p); draw(&g,mode,13); guards(&g);
        int lo=window?13:-wide, hi=window?242:256+wide;
        unsigned expected=mode==7?0x1001:(mode==4?0x100f:0x1003);
        for(int x=-272;x<528;x++) {
          assert(g.buf.data[x+272]==(x>=lo&&x<hi?expected:0)); words++;
        }
        cases++;
      }
  }
  /* Exact crashing transition: old size 16 maps x=13 to zero, while
     current MOSAIC 0x83 needs a size-nine block starting at nine. */
  init(&g,4,9,16,0,1);
  assert(p.mosaicModulo[13]==0);
  assert(PPU_mosaicSize((&p))-(13-p.mosaicModulo[13])==-4);
  PpuRefreshMosaicModulo(&p); assert(p.mosaicModulo[13]==9);
  draw(&g,4,13); guards(&g);
  /* Size one: unchanged original center, with all effects still enabled. */
  init(&g,4,1,1,0,0); draw(&g,4,13); guards(&g);
  for(int x=0;x<256;x++) assert(g.buf.data[x+272]==0x100f);
  for(int size=1;size<=16;size++) for(int mode=2;mode<=7;mode+=(mode==2?2:3))
    for(int window=0;window<2;window++) for(int variant=0;variant<8;variant++) {
      init(&g,mode,size,size,0,window);
      p.hScroll[0]=variant*37; p.vScroll[0]=variant*19;
      unsigned seed=1234+variant;
      for(int i=0;i<0x8000;i++) {
        seed=seed*1664525u+1013904223u;
        p.vram[i]=seed>>16;
      }
      if(mode!=7) for(int i=0;i<1024;i++) p.vram[i]&=0xffff;
      reference=g;
      int y=variant*31;
      draw(&g,mode,y);
      if(mode==4) Legacy_PpuDrawBackground_4bpp_mosaic(&p,&reference.buf,y,false,0,0x2000,0x1000);
      else if(mode==2) Legacy_PpuDrawBackground_2bpp_mosaic(&p,&reference.buf,y,false,0,0x2000,0x1000);
      else Legacy_PpuDrawBackground_mode7(&p,&reference.buf,y,false,0x1000);
      guards(&g); guards(&reference);
      for(int x=0;x<800;x++) { assert(g.buf.data[x]==reference.buf.data[x]); parity_words++; }
      parity_cases++;
    }
  /* Host-only injected empty spans exercise the new defensive seam. They
     are derived from the actual function bodies, substituting window setup;
     no claim that a guest-generated window emitted this interval. */
  for(int mode=2;mode<=7;mode+=(mode==2?2:3)) {
    init(&g,mode,9,9,0,0);
    if(mode==4) Empty_PpuDrawBackground_4bpp_mosaic(&p,&g.buf,13,false,0,0x2000,0x1000);
    else if(mode==2) Empty_PpuDrawBackground_2bpp_mosaic(&p,&g.buf,13,false,0,0x2000,0x1000);
    else Empty_PpuDrawBackground_mode7(&p,&g.buf,13,false,0x1000);
    guards(&g); for(int x=0;x<800;x++) assert(g.buf.data[x]==0); empty_cases++;
  }
  printf("{\"pass\":true,\"render_cases\":%u,\"checked_words\":%u,\"phase_checks\":%u,\"exact_crash_transition\":true,\"legacy_center_cases\":%u,\"legacy_center_words\":%u,\"host_injected_empty_span_cases\":%u}\n",cases,words,phase_checks,parity_cases,parity_words,empty_cases);
  return 0;
}
