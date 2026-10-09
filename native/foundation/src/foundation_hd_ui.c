/* Authored 4x menu-frame art, bound to the original BG3 resource per scanline.
 * This is a host-only replacement of eight frame tiles, not a world-art pack.
 * No ROM-derived pixels are stored here; the owner's ROM supplies identity. */
#include "foundation_hd_ui.h"
#include "common_rtl.h"
#include "snes/snes.h"
#include "snes/cart.h"
#include "snes/ppu.h"
#include "sha256.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern Snes *g_snes;
static int enabled, identity;
static const uint8_t *bound_rom;
static size_t bound_size;
static const uint8_t clean_hash[32] = {
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00
};
typedef struct Binding { uint32_t rgb; uint8_t tile, u, v, valid; } Binding;
static Binding bindings[224][256];
static uint32_t palettes[224][4];
/* Weights for original palette 1 (navy), 2 (bevel), 3 (highlight). */
static uint8_t atlas[8][32][32][3];
static unsigned replaced;
static float clamp(float v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
static void make_art(void) {
    for (unsigned t=0; t<8; ++t) for (unsigned v=0; v<32; ++v) for (unsigned u=0; u<32; ++u) {
        float x=(u+.5f)/4, y=(v+.5f)/4, d;
        if (t<4) {
            if (t&1) x=8-x;
            if (t&2) y=8-y;
            float dx=fmaxf(5-x,0), dy=fmaxf(5-y,0);
            d=sqrtf(dx*dx+dy*dy)-4;
        } else {
            if (t==5) y=8-y;
            if (t==7) x=8-x;
            d=1-(t<6 ? y : x);
        }
        /* Quarter-pixel coverage and a thin inner bevel form new authored
         * curved edges. All weights sum to 255; live palette fades stay live. */
        float outer=clamp(.5f-d*4), inner=clamp((-d-2.0f)*4+.5f);
        float bevel=clamp((-d-1.15f)*4+.5f)*(1-inner);
        unsigned g=(unsigned)(255*bevel+.5f), white=(unsigned)(255*(outer-inner-bevel)+.5f);
        if (g+white>255) white=255-g;
        atlas[t][v][u][0]=(uint8_t)(255-g-white);
        atlas[t][v][u][1]=(uint8_t)g;
        atlas[t][v][u][2]=(uint8_t)white;
    }
}
void FoundationHdUiInit(void) {
    FILE *f=fopen("foundation.ini","r"); char line[128],key[64]; int value;
    if (f) { while (fgets(line,sizeof(line),f)) {
        if (sscanf(line," %63[^=]=%d",key,&value)!=2) continue;
        size_t n=strlen(key); while(n&&(key[n-1]==' '||key[n-1]=='\t')) key[--n]=0;
        if (!strcmp(key,"HdMenuFrames")) enabled=value==1;
    } fclose(f); }
    const char *env=getenv("SNESRECOMP_FOUNDATION_HD_MENU_FRAMES");
    if(env) enabled=!strcmp(env,"1");
    make_art();
    fprintf(stderr,"[foundation] hd_menu_frames=%d (host frame art only)\n",enabled);
}
int FoundationHdUiEnabled(void) { return enabled; }
void FoundationHdUiBeginFrame(void) {
    if (!enabled) return;
    memset(bindings,0,sizeof(bindings)); replaced=0;
    if (!g_snes || !g_snes->cart || !g_rom) { identity=0; return; }
    size_t size=g_snes->cart->romImageSize;
    if (bound_rom==g_rom&&bound_size==size) return;
    bound_rom=g_rom; bound_size=size; identity=0;
    if (size!=1572864) return;
    uint8_t hash[32]; sha256_compute(g_rom,size,hash);
    identity=!memcmp(hash,clean_hash,32);
}
static uint32_t rgb15(unsigned c) {
    unsigned r=c&31,g=(c>>5)&31,b=(c>>10)&31;
    return ((r<<3|r>>2)<<16)|((g<<3|g>>2)<<8)|(b<<3|b>>2);
}
void FoundationHdUiObserve(const Ppu *p,unsigned line,void *unused) {
    (void)unused;
    if (!enabled||!identity||!p||line<1||line>224||g_ram[0x20]!=1||
        p->bgmode!=9||PPU_forcedBlank(p)||PPU_brightness(p)!=15||p->mosaic||p->setini||
        !(p->screenEnabled[0]&4)||(p->windowsel&0xf00)||(p->cgadsub&4)||
        PPU_clipMode(p)||PPU_directColor(p)||PPU_bgTileAdr(p,2)!=0x4000||
        p->bgXsc[2]!=0x51||memcmp((const uint8_t *)p->vram+0x8a00,g_rom+0x28a00,128)) return;
    unsigned y=line-1, sy=(line+p->vScroll[2])&255;
    const uint32_t *row=(const uint32_t *)(p->renderBuffer+y*p->renderPitch);
    int left=(int)(p->renderPitch/4-256)/2;
    for (unsigned i=0;i<4;++i) palettes[y][i]=rgb15(p->cgram[i]);
    for(unsigned x=0;x<256;++x) {
        unsigned sx=(x+p->hScroll[2])&511,tx=sx>>3,ty=sy>>3;
        unsigned map=0x5000+(tx&31)+ty*32+(tx>=32?1024:0);
        unsigned word=p->vram[map],tile=word&1023,u=sx&7,v=sy&7;
        if(tile<0xa0||tile>0xa7||(word&0x3c00)!=0x2000) continue;
        if(word&0x4000) u=7-u;
        if(word&0x8000) v=7-v;
        unsigned bits=p->vram[0x4000+tile*8+v],shift=7-u;
        unsigned color=((bits>>shift)&1)|((bits>>(shift+8)&1)<<1);
        if(!color) continue;
        uint32_t expected=palettes[y][color];
        if((row[left+x]&0xffffff)!=expected) continue;
        bindings[y][x]=(Binding){expected,(uint8_t)(tile-0xa0),(uint8_t)u,(uint8_t)v,1};
        /* Encode flips for quarter-pixel ordering, beyond coarse tile index. */
        bindings[y][x].tile|=(word&0x4000?0x40:0)|(word&0x8000?0x80:0);
    }
}
static uint32_t blend(const uint32_t *pal,const uint8_t *weights) {
    uint32_t out=0xff000000;
    for(unsigned shift=0;shift<=16;shift+=8) {
        unsigned c=0;
        for(unsigned i=0;i<3;++i) c+=((pal[i+1]>>shift)&255)*weights[i];
        out|=((c+127)/255)<<shift;
    }
    return out;
}
void FoundationHdUiDraw(uint8_t *dst,size_t pitch,const uint32_t *logical,int w,int h) {
    if(!enabled||h!=224||(w!=256&&w!=400)) return;
    unsigned left=(w-256)/2;
    for(unsigned y=0;y<224;++y) for(unsigned x=0;x<256;++x) {
        const Binding *b=&bindings[y][x];
        if(!b->valid||(logical[y*w+left+x]&0xffffff)!=b->rgb) continue;
        for(unsigned dv=0;dv<4;++dv) for(unsigned du=0;du<4;++du) {
            unsigned u=b->u*4+((b->tile&0x40)?3-du:du),v=b->v*4+((b->tile&0x80)?3-dv:dv);
            uint32_t *row=(uint32_t *)(dst+(y*4+dv)*pitch);
            row[(left+x)*4+du]=blend(palettes[y],atlas[b->tile&7][v][u]);
        }
        ++replaced;
    }
    const char *trace=getenv("SNESRECOMP_FOUNDATION_HD_UI_TRACE");
    if(trace) { FILE *f=fopen(trace,"a"); if(f) { fprintf(f,"%u,%u\n",snes_frame_counter,replaced); fclose(f); } }
}
