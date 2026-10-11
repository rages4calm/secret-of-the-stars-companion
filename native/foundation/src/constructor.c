/* Guarded generated original-cost constructor; producers retain original execution. */
#include "constructor.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "snes/interp_bridge.h"
#include "snes/snes.h"
#include "snes/ppu.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#ifdef SNESRECOMP_HAS_GENERATED_CODE
#include "gen/constructor_sites.generated.h"
extern Snes *g_snes;
static FILE *trace;static unsigned epoch;static int initialized;
static unsigned W(unsigned a){return g_ram[a]|g_ram[a+1]<<8;}
static unsigned L(unsigned a){return W(a)|g_ram[a+2]<<16;}
static void CtorExecute(CpuState*c,uint32_t pc);
static void CtorIdentityReset(void);
void ConstructorReset(void){++epoch;CtorIdentityReset();if(trace)fflush(trace);}
static void Observe(CpuState*c,uint32_t pc){
 if(!trace||!g_snes||!g_snes->ppu){CtorExecute(c,pc);return;}
 const Ppu*p=g_snes->ppu;
 fprintf(trace,"%u,%u,%u",epoch,snes_frame_counter,pc);
#define V(v) fprintf(trace,",%llu",(unsigned long long)(v))
 V(c->A);V(c->X);V(c->Y);V(c->S);V(c->D);V(c->DB);V(c->PB);V(c->P);
 V(c->m_flag);V(c->x_flag);V(c->emulation);V(c->_flag_N);V(c->_flag_V);V(c->_flag_Z);V(c->_flag_C);V(c->_flag_I);V(c->_flag_D);V(c->open_bus);
 V(c->host_return_valid);V(c->cycles);V(c->master_cycles);V(c->coprocessor_master_cycles);
 V(g_snes->beamMasterLast);V(g_snes->hPos);V(g_snes->vPos);V(g_snes->inIrq);V(g_snes->inNmi);V(g_snes->rdnmiPending);V(g_snes->dbgIrqLatches);V(g_snes->dbgIrqMissed);
 for(unsigned n=0;n<12;++n)V(g_ram[(c->S+n)&0xffff]);
 V(g_ram[0x4b6]);V(W(0x40e));V(g_ram[0x5372]);V(W(1));V(g_ram[0x20]);V(PPU_forcedBlank(p));V(p->bgmode);
 V(g_ram[0x531]);V(g_ram[0x408]);V(g_ram[0x970]);V(g_ram[0x971]);
 V(W(0x40a));V(W(0x40c));V(W(0x2ad));V(W(0x2af));V(W(0x2b1));V(W(0x2b3));
 V(L(0x513));V(L(0x516));V(L(0x506));V(L(0x509));V(L(0x500));V(L(0x503));V(L(0x537));V(L(0x55c));
 V(p->vramPointer);V(p->vramIncrement);V(p->vramIncrementOnHigh);V(p->vramRemapMode);V(p->vramReadBuffer);V(p->vramWriteCount);
 fputc('\n',trace);
#undef V
 CtorExecute(c,pc);
}

static const uint32_t ConstructorNativePCs[60]={0x1c403,0x1c6fa,0x1c7af,0x1d080,0x1d083,0x1d085,0x1d087,0x1d08a,0x1d08d,0x1d08f,0x1d092,0x1d095,0x1d096,0x1d097,0x1d098,0x1d09a,0x1d09d,0x1d0a0,0x1d0a2,0x1d0a5,0x1d0a8,0x1d0ab,0x1d0ae,0x1d0af,0x1d0b1,0x1d0b4,0x1d0b5,0x1d0b6,0x1d0ba,0x1d0bb,0x1d0bd,0x1d0c0,0x1d0c1,0x1d0c2,0x1d0c5,0x1d0c7,0x1d0c9,0x1d0cc,0x1d0ce,0x1d0d1,0x1d0d4,0x1d0d8,0x1d0db,0x1d0dd,0x1d0e0,0x1d0e2,0x1d0e5,0x1d0e8,0x1d0ea,0x1d0ec,0x1d0ef,0x1d0f0,0x1d0f2,0x1d0f5,0x1d0f8,0x1d0fb,0x1d0fe,0x1d100,0x1d103,0x1d106};

static int ConstructorMode(const CpuState*c,uint32_t pc){switch(pc){
case 0x01c403:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01c6fa:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c32&&c->D==0x0900);
case 0x01c7af:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c32&&c->D==0x0900);
case 0x01d080:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d083:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d085:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d087:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d08a:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d08d:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d08f:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d092:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d095:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d096:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d097:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d098:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d09a:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d09d:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0a0:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0a2:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0a5:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0a8:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0ab:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0ae:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900)||(c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0af:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2d&&c->D==0x0900)||(c->m_flag==1&&c->x_flag==1&&c->S==0x1c2d&&c->D==0x0900);
case 0x01d0b1:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2d&&c->D==0x0900);
case 0x01d0b4:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2d&&c->D==0x0900);
case 0x01d0b5:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2b&&c->D==0x0900);
case 0x01d0b6:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2d&&c->D==0x0b00);
case 0x01d0ba:return (c->m_flag==1&&c->x_flag==0&&c->S==0x1c2d&&c->D==0x0b00);
case 0x01d0bb:return (c->m_flag==1&&c->x_flag==0&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0bd:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0c0:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0c1:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0c2:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0c5:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0c7:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0c9:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0cc:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0ce:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0d1:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0d4:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0d8:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0db:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0dd:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0e0:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0e2:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0e5:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0e8:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0ea:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0ec:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0ef:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0f0:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0f2:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0f5:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0f8:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0fb:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d0fe:return (c->m_flag==0&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d100:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d103:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
case 0x01d106:return (c->m_flag==1&&c->x_flag==1&&c->S==0x1c2f&&c->D==0x0900);
default:return 0;}}
static const uint32_t ConstructorResources0[8]={628386u,631870u,690200u,693968u,233304u,241264u,623120u,624144u};
static const uint32_t ConstructorResources1[8]={628386u,628480u,690200u,690200u,233304u,233304u,623120u,623120u};

#include "sha256.h"
#include "snes/cart.h"
#include "gen/constructor.generated.h"
static int ctor_identity,ctor_identity_ready;
static unsigned long long ctor_count[60];
static void CtorIdentityReset(void){ctor_identity_ready=ctor_identity=0;}
static int ctor_enabled=-1;
static int CtorContext(CpuState*c,uint32_t pc){
 if(!ctor_identity_ready){ctor_identity_ready=1;
  static const uint8_t expected[32]={0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00};
  uint8_t hash[32];if(g_rom&&g_snes&&g_snes->cart&&g_snes->cart->romImageSize==1572864){sha256_compute(g_rom,1572864,hash);ctor_identity=!memcmp(hash,expected,32);}
 }
 if(!ctor_identity||!c||!g_snes||!g_snes->ppu||c->emulation||c->PB!=1||c->DB!=1||
  W(1)!=8||g_ram[0x20]!=1||W(0x40e)!=5||g_ram[0x5372]!=0||g_ram[0x4b6]!=0||
  !PPU_forcedBlank(g_snes->ppu)||!ConstructorMode(c,pc))return 0;
 const Ppu*p=g_snes->ppu;if(p->vramRemapMode||!p->vramIncrementOnHigh||(p->vramIncrement!=1&&p->vramIncrement!=32))return 0;
 unsigned which;
 if(pc==0x1c6fa||pc==0x1c7af){which=pc==0x1c7af;if((c->A&255u)!=(which?4u:0u))return 0;}
 else{unsigned ret=W(0x1c30);if(g_ram[0x1c32]!=1||(ret!=0xc6fd&&ret!=0xc7b2))return 0;which=ret==0xc7b2;}
 const uint32_t*expected=which?ConstructorResources1:ConstructorResources0;
 static const unsigned offsets[8]={0x513,0x516,0x506,0x509,0x500,0x503,0x537,0x55c};
 for(unsigned n=0;n<8;++n)if(L(offsets[n])!=expected[n])return 0;
 return 1;
}
static void CtorExecute(CpuState*c,uint32_t pc){
 if(ctor_enabled<0){const char*v=getenv("SNESRECOMP_FOUNDATION_GENERATED_CONSTRUCTOR");ctor_enabled=!v||!strcmp(v,"1")||!strcmp(v,"original");}
 if(!ctor_enabled||!CtorContext(c,pc)||!interp_bridge_native_begin(c))return;
 unsigned cycles;uint32_t next;unsigned ordinal=GeneratedConstructorStep(c,pc,&cycles,&next);
 ++ctor_count[ordinal];interp_bridge_native_commit(c,cycles,next);
}
static void CtorReport(void){
 fprintf(stderr,"[constructor_generated] steps=");unsigned long long total=0;for(unsigned i=0;i<60;++i)total+=ctor_count[i];fprintf(stderr,"%llu",total);
 for(unsigned i=0;i<60;++i)fprintf(stderr," pc%06x=%llu",ConstructorNativePCs[i],ctor_count[i]);fputc('\n',stderr);
}

void ConstructorInit(void){
 if(initialized)return;initialized=1;
 atexit(CtorReport);
 const char*path=getenv("SNESRECOMP_CONSTRUCTOR_TRACE");
 if(!path||!*path){for(unsigned n=0;n<sizeof(ConstructorSites)/sizeof(ConstructorSites[0]);++n)if(!interp_bridge_add_pre_opcode_hook(ConstructorSites[n],Observe))abort();return;}
 trace=fopen(path,"w");if(!trace)abort();
 fputs("epoch,frame,pc,a,x,y,s,d,db,pb,p,m,xflag,e,n,v,z,c,i,decimal,open_bus,host_return,cycles,master,coprocessor,beam_master,h,vpos,in_irq,in_nmi,rdnmi,irq_latches,irq_missed",trace);
 for(unsigned n=0;n<12;++n)fprintf(trace,",stack%u",n);
 fputs(",active_pack,scene,stage,task,mode,blank,bgmode,loading,direction,selector,iteration,base_x,base_y,camera1_x,camera1_y,camera2_x,camera2_y,map1,map2,cells1,cells2,tiles1,tiles2,attributes1,attributes2,vram,inc,onhigh,remap,readbuf,writes\n",trace);
 for(unsigned n=0;n<sizeof(ConstructorSites)/sizeof(ConstructorSites[0]);++n)
  if(!interp_bridge_add_pre_opcode_hook(ConstructorSites[n],Observe))abort();
}

#else
/* ROM-free Setup has no constructor instructions or hooks. */
void ConstructorInit(void) {}
void ConstructorReset(void) {}
#endif
