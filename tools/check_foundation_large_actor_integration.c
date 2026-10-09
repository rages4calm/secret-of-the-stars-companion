/* Synthetic host callbacks and actual PPU scanout. No guest is executed. */
#include "foundation_wide_actors.h"
#include "foundation_field.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "snes/ppu.h"
#include "snes/dma.h"
#include "snes/snes.h"
#include "snes/interp_bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
uint8 g_ram[0x20000]; const uint8 *g_rom; Snes *g_snes; Ppu *g_ppu;
int snes_frame_counter = 1; unsigned char g_snesrecomp_last_hdmaen;
static struct {uint32_t pc; InterpPreOpcodeHook fn;} hooks[16];
static unsigned hook_count, readonly_calls, guard; static DmaTransferNotifyHook notify;
bool interp_bridge_add_pre_opcode_hook(uint32_t pc, InterpPreOpcodeHook hook) {
 if(hook_count>=16)return false;hooks[hook_count].pc=pc;hooks[hook_count++].fn=hook;return true;
}
void dma_set_transfer_notify_hook(DmaTransferNotifyHook hook){notify=hook;}
void dma_reset_transfer_notify_state(Dma *dma){(void)dma;}
static void readfile(const char*p,void*v,size_t n){FILE*f=fopen(p,"rb");if(!f||fread(v,1,n,f)!=n||fgetc(f)!=EOF)exit(2);fclose(f);}
static unsigned r16(unsigned at){return g_ram[at]|(unsigned)g_ram[at+1]<<8;}
static void w16(unsigned at,unsigned v){g_ram[at]=v;g_ram[at+1]=v>>8;}
static void w24(unsigned at,unsigned v){w16(at,v);g_ram[at+2]=v>>16;}
static int signed16(unsigned v){return(int16_t)v;}
static int gate(int value,unsigned stop,int party){unsigned v=(uint16_t)value;return v>=(party?0x1f9:0xfff1)||v<stop;}
static void call(CpuState *cpu,unsigned pc){
 uint8_t *ram=malloc(sizeof(g_ram));Ppu *ppu=malloc(sizeof(Ppu));CpuState before=*cpu;
 memcpy(ram,g_ram,sizeof(g_ram));memcpy(ppu,g_ppu,sizeof(Ppu));unsigned found=0;
 for(unsigned i=0;i<hook_count;i++)if(hooks[i].pc==pc){hooks[i].fn(cpu,pc);found++;}
 if(found!=1||memcmp(ram,g_ram,sizeof(g_ram))||memcmp(ppu,g_ppu,sizeof(Ppu))||memcmp(&before,cpu,sizeof(before)))exit(3);
 free(ram);free(ppu);readonly_calls++;
}
static void transfer(Dma*dma,int channel,DmaChannel*start,bool complete){
 uint8_t *ram=malloc(sizeof(g_ram));Ppu *ppu=malloc(sizeof(Ppu));Dma old=*dma;DmaChannel oldstart=*start;
 memcpy(ram,g_ram,sizeof(g_ram));memcpy(ppu,g_ppu,sizeof(Ppu));notify(dma,channel,start,complete);
 if(memcmp(ram,g_ram,sizeof(g_ram))||memcmp(ppu,g_ppu,sizeof(Ppu))||memcmp(dma,&old,sizeof(old))||memcmp(start,&oldstart,sizeof(oldstart)))exit(4);
 free(ram);free(ppu);readonly_calls++;
}
static void producer(CpuState*cpu,const uint8_t final[544]){
 w24(cpu->S+1,0x1d865);cpu->m_flag=cpu->x_flag=1;
 w16(0x46b,0x30);w16(0xe34,0x10);w16(0xe38,0x201);w16(0xe10,g_ram[0x400]?0xefff:0xffff);
 call(cpu,0x1d8b1);unsigned cursor=12;
 for(unsigned family=0;family<2;family++){
  if(family){g_ram[0xe13]=5;cpu->m_flag=cpu->x_flag=1;w16(0x46b,cursor*4);call(cpu,0x1d988);w24(cpu->S+1,0x1d86f);call(cpu,0x1da56);}
  for(unsigned i=0;i<(family?19:5);i++){
   unsigned at=(family?0x4100:0x4000)+i*(family?25:18);if(g_ram[at]==255)continue;
   g_ram[family?0xe14:0xe13]=i;w24(0xe1c,0x7e0000+at);w16(0xe1a,r16(at+(family?5:3)));
   cpu->m_flag=0;cpu->x_flag=1;cpu->Y=family?3:2;
   int x=family?signed16(r16(at+1)-r16(0x2ad)):g_ram[at+1]+((g_ram[at+5]&1)<<8);
   int y=family?signed16(r16(at+3)-r16(0x2af)):(int)(g_ram[at+2]+((g_ram[at+5]&2)<<7))-1;
   if(r16(at+(family?5:3))==0xb0){
    cpu->Y=3;w16(0xe02,x);w16(0xe00,y);w24(0xe1f,0xe9800+0xb0*8+g_ram[at]*4);
    if(guard==1)cpu->DB=0;if(guard==2)w24(0xe1c,0x7e0000+at+1);if(guard==3)cpu->m_flag=1;
    if(guard==4)w16(0xe10,r16(0xe10)^1);if(guard==5)w24(0xe1f,r16(0xe1f)+1+0xe0000);
    unsigned pc=family?0x1db68:0x1d989;call(cpu,pc);if(guard==6)call(cpu,pc);
   }else{
    w16(0xe16,x);w16(0xe18,y);call(cpu,family?0x1dab6:0x1d917);
    if(gate(x,255,!family)&&gate(y,239,!family)&&(!family||i<17))cursor+=4;
   }
  }
 }
 g_ram[0xe14]=19;cpu->m_flag=cpu->x_flag=1;call(cpu,0x1db2c);
 memcpy(g_ram+0x2200,final,544);w16(0x46b,cursor*4);w16(0xe34,0x10);w16(0xe38,0x201);
 if(guard==7)g_ram[0x2202]^=1;if(guard==8)g_ram[0x2400]^=2;if(guard==9)w16(0x46b,cursor*4+4);
 w24(cpu->S+1,0x1d873);call(cpu,0x1de29);
}
static void scanout(Ppu*p,const uint8_t bytes[544]){for(unsigned i=0;i<256;i++)p->oam[i]=bytes[2*i]|(unsigned)bytes[2*i+1]<<8;memcpy(p->highOam,bytes+512,32);}
int main(int argc,char **argv){
 if(argc!=10)return 2;guard=atoi(argv[7]);unsigned expect=atoi(argv[8]),style=atoi(argv[9]);
 uint8_t *rom=malloc(1572864),final[544];Ppu*s=ppu_init(),*p=calloc(1,sizeof(Ppu)),*before=malloc(sizeof(Ppu));
 uint32_t*original=calloc(256*224,4),*wide=calloc(400*224,4);Snes snes={0};Cart cart={0};Dma dma={0};CpuState cpu={0};
 snes.cart=&cart;snes.ppu=s;snes.dma=&dma;cart.romImageSize=1572864;dma.snes=&snes;g_snes=&snes;g_ppu=s;g_rom=rom;
 readfile(argv[1],rom,1572864);readfile(argv[2],g_ram,sizeof(g_ram));readfile(argv[3],s->vram,65536);readfile(argv[4],s->cgram,512);readfile(argv[5],final,544);
 s->inidisp=15;s->bgmode=9;s->obsel=3;s->bgXsc[0]=0x49;s->bgXsc[1]=0x59;s->bgXsc[2]=0x51;s->bgTileAdr=0x400;s->screenEnabled[0]=0x17;
 s->hScroll[0]=r16(0x2ad)&1023;s->vScroll[0]=r16(0x2af)&1023;
 cpu.D=0xe00;cpu.DB=cpu.PB=1;cpu.S=0x1ed0;
 FoundationWideActorsSetEnabled(1);FoundationWideActorsInit();FoundationWideActorsBeforeFrame();
 if((hook_count!=9 && !(guard==31 && hook_count==7))||!notify||!FoundationFieldSceneEligible(s))return 10;
 producer(&cpu,final);
 DmaChannel start={0};start.bAdr=4;start.aBank=0x7e;start.aAdr=0x2200;start.size=544;
 if(guard==10)start.size=543;if(guard==11)start.aAdr++;if(guard==12)start.aBank++;if(guard==13)start.mode=1;
 if(guard==14)start.fromB=1;if(guard==15)start.fixed=1;if(guard==16)start.decrement=1;
 if(guard==17)g_ram[0x2200+543]^=1;
 if(guard!=18)transfer(&dma,guard==19?6:7,&start,false);
 memcpy(p,s,sizeof(Ppu));unsigned beforecomplete=FoundationWideActorsPrepareLine(s,80,p);
 scanout(s,final);if(guard==20)s->highOam[31]^=1;if(guard==21)s->oam[2]^=1;
 if(guard==22)start.size=543;if(guard==23)start.bAdr=5;if(guard==24)start.mode=1;
 transfer(&dma,7,&start,true);
 if(guard==25){g_ram[0x40e]^=1;FoundationWideActorsBeforeFrame();}
 if(guard==26)FoundationWideActorsReset();if(guard==27)FoundationWideActorsSetEnabled(0);
 if(guard==28)s->obsel=0x23;if(guard==29)s->oam[255]^=1;
 if(guard==30){FoundationWideActorsReset();FoundationWideActorsBeforeFrame();}
 if(guard==32){
  FoundationWideActorsReset();FoundationWideActorsBeforeFrame();
  memcpy(p,s,sizeof(Ppu));if(FoundationWideActorsPrepareLine(s,80,p))return 14;
  for(unsigned i=0;i<128;i++)w16(0x2200+i*4,0xf080);
  memset(g_ram+0x2400,85,32);producer(&cpu,final);
  transfer(&dma,7,&start,false);scanout(s,final);transfer(&dma,7,&start,true);
 }
 if(style==6)s->hScroll[0]=(r16(0x2ad)+8)&1023;
 if(style==7)s->vScroll[0]=(r16(0x2af)+3)&1023;
 if(FoundationWideActorsPrepareLine(s,0,p)||FoundationWideActorsPrepareLine(s,225,p)||
    FoundationWideActorsPrepareLine(s,80,s)||FoundationWideActorsPrepareLine(NULL,80,p)||
    FoundationWideActorsPrepareLine(s,80,NULL))return 15;
 unsigned maxpieces=0,pixelopaque=0,centererrors=0;
 PpuBeginDrawing(s,(uint8_t*)original,1024,kPpuRenderFlags_NewRenderer);PpuSetExtraSideSpace(s,0,0,0);ppu_runLine(s,0);
 FoundationWideActorsBeginDraw();
 for(unsigned line=1;line<=224;line++){
  ppu_runLine(s,line);memcpy(before,s,sizeof(Ppu));memcpy(p,s,sizeof(Ppu));
  PpuBeginDrawing(p,(uint8_t*)wide,1600,kPpuRenderFlags_NewRenderer);PpuSetExtraSpace(p,72);PpuSetExtraSideSpace(p,72,72,0);
  unsigned count=FoundationWideActorsPrepareLine(s,line,p);if(count>maxpieces)maxpieces=count;
  if(memcmp(before,s,sizeof(Ppu)))return 11;
  for(unsigned i=0;i<count;i++){const PpuExtraObject*o=&p->extraObjects[i];if(o->oamSlot<2&&(o->width!=16||o->height!=16||o->order!=o->oamSlot+1))return 12;}
  /* Isolated OBJ against backdrop. Source guards and authentic scanout retain BGs. */
  p->screenEnabled[0]=16;p->screenEnabled[1]=0;p->screenWindowed[0]=p->screenWindowed[1]=0;p->windowsel=0;p->cgwsel=0;p->cgadsub=0;
  if(!count){for(unsigned i=0;i<128;i++)p->oam[2*i]=0xf080;memset(p->highOam,0,32);PpuSetExtraObjects(p,NULL,0);}
  if(style==1)p->inidisp=7;
  if(style==2){p->cgadsub=16;p->fixedColor=0x1084;}
  if(style==3){p->cgadsub=0x90;p->fixedColor=0x1084;}
  if(style==4){p->screenWindowed[0]=16;p->windowsel=2u<<16;p->window1left=0;p->window1right=255;}
  if(style==5)p->screenEnabled[0]=0;
  ppu_runLine(p,line);
  memcpy(wide+(line-1)*400+72,original+(line-1)*256,1024);
  centererrors+=!!memcmp(wide+(line-1)*400+72,original+(line-1)*256,1024);
  for(unsigned x=0;x<72;x++)pixelopaque+=!!(wide[(line-1)*400+x]&0xffffff),pixelopaque+=!!(wide[(line-1)*400+328+x]&0xffffff);
 }
 FoundationWideActorsEndDraw();
 if(beforecomplete||(guard!=31 && !!maxpieces!=!!expect))return 13;
 FILE*f=fopen(argv[6],"wb");fwrite(wide,4,400*224,f);fclose(f);
 printf("{\"registered_hooks\":%u,\"readonly_callbacks\":%u,\"before_complete_parts\":%u,\"max_side_parts\":%u,\"center_stitch_line_mismatches\":%u,\"nonblack_margin_pixels\":%u,\"expected_metadata\":%u}\n",hook_count,readonly_calls,beforecomplete,maxpieces,centererrors,pixelopaque,expect);
 return 0;
}
