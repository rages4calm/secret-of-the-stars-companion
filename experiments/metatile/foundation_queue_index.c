/* Private original-cost prototype. No production configuration or installation. */
#include "foundation_queue_index.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "sha256.h"
#include "snes/cart.h"
#include "snes/interp_bridge.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern Snes *g_snes;
static const uint8_t image_sha[32]={0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00};
static int enabled,installed,identity;
static const uint8_t *bound_rom;static size_t bound_size;
static uint64_t instructions,completed,refused;
static unsigned Ram16(unsigned at){return g_ram[at]|(unsigned)g_ram[at+1]<<8;}
void FoundationQueueIndexReset(void){bound_rom=NULL;bound_size=0;identity=0;}
void FoundationQueueIndexBeforeFrame(void){
 if(!enabled||!g_snes||!g_snes->cart||!g_rom)return;
 size_t size=g_snes->cart->romImageSize;
 if(bound_rom==g_rom&&bound_size==size)return;
 FoundationQueueIndexReset();bound_rom=g_rom;bound_size=size;
 if(size!=1572864)return;
 uint8_t hash[32];sha256_compute(g_rom,size,hash);
 static const uint8_t bytes[]={0xad,0x20,0x05,0x29,0xff,0x00,0x0a,0x0a,0x0a,0x85,0x1b,0xa5,0x35,0x0a,0x18,0x65,0x1b,0x85,0x1b};
 identity=!memcmp(hash,image_sha,32)&&!memcmp(g_rom+0xb408,bytes,sizeof(bytes));
}
static int Context(const CpuState *cpu){
 return enabled&&identity&&cpu&&g_snes&&g_snes->ppu&&!cpu->emulation&&!cpu->m_flag&&!cpu->x_flag&&!cpu->_flag_D&&cpu->PB==1&&cpu->DB==1&&cpu->D==0x0b00&&g_ram[0x20]==1&&!PPU_forcedBlank(g_snes->ppu)&&(Ram16(0x40e)==0||Ram16(0x40e)==5);
}
static unsigned ReadWord(CpuState *cpu,unsigned adr){unsigned low=interp_bridge_native_read8(cpu,adr);return low|((unsigned)interp_bridge_native_read8(cpu,(adr&0xff0000)|((adr+1)&65535))<<8);}
static void ZN(CpuState *cpu){cpu->_flag_Z=cpu->A==0;cpu->_flag_N=!!(cpu->A&0x8000);}
static void Native(CpuState *cpu,uint32_t pc){
 if(!Context(cpu)){++refused;return;}
 unsigned bytes,cycles;
 switch(pc){
 case 0x1b408:bytes=3;cycles=5;break;
 case 0x1b40b:bytes=3;cycles=3;break;
 case 0x1b40e:case 0x1b40f:case 0x1b410:case 0x1b415:case 0x1b416:bytes=1;cycles=2;break;
 case 0x1b411:case 0x1b413:case 0x1b417:case 0x1b419:bytes=2;cycles=4;break;
 default:return;
 }
 /* One opcode at a time retains every IRQ/deadline edge. No uncharged fetch,
  * direct guest write, collapsed clock/device update or future cached state. */
 if(!interp_bridge_native_begin(cpu))return;
 interp_bridge_native_read8(cpu,pc);unsigned operand=0;
 if(bytes>1)operand=interp_bridge_native_read8(cpu,pc+1);
 if(bytes>2)operand|=(unsigned)interp_bridge_native_read8(cpu,pc+2)<<8;
 switch(pc){
 case 0x1b408:cpu->A=ReadWord(cpu,(unsigned)cpu->DB<<16|operand);ZN(cpu);break;
 case 0x1b40b:cpu->A&=operand;ZN(cpu);break;
 case 0x1b40e:case 0x1b40f:case 0x1b410:case 0x1b415:
  cpu->_flag_C=!!(cpu->A&0x8000);cpu->A=(uint16_t)(cpu->A<<1);ZN(cpu);break;
 case 0x1b411:case 0x1b419:interp_bridge_native_write16(cpu,cpu->D+operand,cpu->A);break;
 case 0x1b413:cpu->A=ReadWord(cpu,cpu->D+operand);ZN(cpu);break;
 case 0x1b416:cpu->_flag_C=0;break;
 case 0x1b417:{unsigned value=ReadWord(cpu,cpu->D+operand);unsigned result=(unsigned)cpu->A+value+cpu->_flag_C;
  cpu->_flag_V=!!((~(cpu->A^value)&(cpu->A^result))&0x8000);cpu->_flag_C=result>65535;cpu->A=(uint16_t)result;ZN(cpu);break;}
 }
 cpu_mirrors_to_p(cpu);++instructions;if(pc==0x1b419)++completed;
 interp_bridge_native_commit(cpu,cycles,pc+bytes);
}
void FoundationQueueIndexInit(void){
 const char *env=getenv("SNESRECOMP_EXPERIMENT_QUEUE_INDEX");enabled=env&&!strcmp(env,"original");
 if(enabled&&!installed){static const uint32_t sites[]={0x1b408,0x1b40b,0x1b40e,0x1b40f,0x1b410,0x1b411,0x1b413,0x1b415,0x1b416,0x1b417,0x1b419};installed=1;
  for(unsigned i=0;i<sizeof(sites)/sizeof(sites[0]);++i)installed&=interp_bridge_add_pre_opcode_hook(sites[i],Native);
  if(!installed)enabled=0;
 }
 fprintf(stderr,"[queue_index] private_original_cost=%d\n",enabled);
}
void FoundationQueueIndexShutdown(void){if(enabled)fprintf(stderr,"[queue_index] native_instructions=%llu completed=%llu refused=%llu original_cost=1\n",(unsigned long long)instructions,(unsigned long long)completed,(unsigned long long)refused);enabled=0;FoundationQueueIndexReset();}
