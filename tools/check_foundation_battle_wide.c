/* Portable host-only resource fixture. No emulator loop, saves or ROM writes. */
#include "foundation_battle_wide.h"
#include "common_rtl.h"
#include "snes/snes.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
uint8 g_ram[0x20000];const uint8 *g_rom;Snes *g_snes;
unsigned char g_snesrecomp_last_hdmaen;int snes_frame_counter=1;
static void readfile(const char*p,void*v,size_t n){FILE*f=fopen(p,"rb");if(!f||fread(v,1,n,f)!=n)exit(2);fclose(f);}
int main(int argc,char **argv){
 if(argc!=7)return 2;unsigned expected=atoi(argv[6]);unsigned errors=0,margin_pixels=0,selector=0;
 uint8*rom=malloc(1572864);Ppu*s=ppu_init(),*p=calloc(1,sizeof(Ppu)),*before=malloc(sizeof(Ppu));uint16_t*shadow=malloc(65536);uint32_t*original=calloc(256*224,4),*wide=calloc(400*224,4);
 Snes snes={0};Cart cart={0};snes.cart=&cart;snes.ppu=s;cart.romImageSize=1572864;g_snes=&snes;g_rom=rom;
 readfile(argv[1],rom,1572864);readfile(argv[2],g_ram,sizeof(g_ram));readfile(argv[3],s->vram,65536);readfile(argv[4],s->cgram,512);
 selector=g_ram[0x529];s->inidisp=15;s->bgmode=9;s->mosaic=3;s->obsel=3;s->bgTileAdr=0x0400;s->bgXsc[0]=0x49;s->bgXsc[1]=0x59;s->bgXsc[2]=0x51;s->screenEnabled[0]=0x17;s->screenWindowed[0]=0x17;s->windowsel=0x10011;s->window1left=1;s->window1right=0;s->window2left=1;s->window2right=0;
 for(unsigned i=0;i<128;i++)s->oam[i*2]=0xf000;
 PpuBeginDrawing(s,(uint8_t*)original,1024,kPpuRenderFlags_NewRenderer);PpuSetExtraSideSpace(s,0,0,0);ppu_runLine(s,0);
 if(!!FoundationBattleWideEligible(s)!=expected){fprintf(stderr,"Eligibilitydefect\n");return 1;}
 unsigned guard_checks=0;
 if(expected){
  s->vram[0x5800]^=1;if(FoundationBattleWideEligible(s))return 5;s->vram[0x5800]^=1;guard_checks++;
  unsigned used_address=((s->vram[0x5800]&1023)/128)*0x800;
  s->vram[used_address]^=1;if(FoundationBattleWideEligible(s))return 6;s->vram[used_address]^=1;guard_checks++;
  s->hScroll[1]=1;if(FoundationBattleWideEligible(s))return 7;s->hScroll[1]=0;guard_checks++;
  g_ram[0x20]=1;if(FoundationBattleWideEligible(s))return 8;g_ram[0x20]=5;guard_checks++;
  g_ram[0x529]=16;if(FoundationBattleWideEligible(s))return 9;g_ram[0x529]=selector;guard_checks++;
  if(FoundationBattleWidePrepareLine(s,0,p,shadow)||FoundationBattleWidePrepareLine(s,225,p,shadow)||FoundationBattleWidePrepareLine(s,1,s,shadow)||FoundationBattleWidePrepareLine(s,1,p,s->vram))return 10;guard_checks+=4;
 }
 if(!expected){printf("{\"selector\":%u,\"accepted\":false,\"expected_rejected\":true}\n",g_ram[0x529]);return 0;}
 memcpy(shadow,s->vram,65536);
 for(unsigned line=1;line<=224;line++){
  ppu_runLine(s,line);memcpy(before,s,sizeof(Ppu));memcpy(p,s,sizeof(Ppu));PpuBeginDrawing(p,(uint8_t*)wide,1600,kPpuRenderFlags_NewRenderer);PpuSetExtraSpace(p,72);PpuSetExtraSideSpace(p,72,72,0);
  if(!FoundationBattleWidePrepareLine(s,line,p,shadow))return 3;
  if(memcmp(s,before,sizeof(Ppu)))return 4;
  ppu_runLine(p,line);
  errors+=!!memcmp(original+(line-1)*256,wide+(line-1)*400+72,1024);
  for(unsigned x=0;x<72;x++)margin_pixels+=(wide[(line-1)*400+x]&0xffffff)!=0,margin_pixels+=(wide[(line-1)*400+328+x]&0xffffff)!=0;
 }
 char shadow_path[4096];snprintf(shadow_path,sizeof(shadow_path),"%s.shadow",argv[5]);FILE*sf=fopen(shadow_path,"wb");fwrite(shadow,1,65536,sf);fclose(sf);
 FILE*f=fopen(argv[5],"wb");fwrite(wide,4,400*224,f);fclose(f);
 printf("{\"selector\":%u,\"accepted\":true,\"center_line_mismatches\":%u,\"nonblack_side_pixels\":%u,\"source_ppu_unchanged_by_helper\":true,\"rejection_checks\":%u}\n",g_ram[0x529],errors,margin_pixels,guard_checks);
 return errors?1:0;
}
