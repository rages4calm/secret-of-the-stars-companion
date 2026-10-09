/* ROM-free edge/guard probe. Genuine gameplay is checked separately by Python. */
#include "foundation_qol.h"
#include "cpu_state.h"
#include "common_rtl.h"
#include "snes/interp_bridge.h"
#include <stdio.h>
#include <string.h>

uint8 g_ram[0x20000]; int snes_frame_counter;
static int held;
uint8 *RomPtr(uint32_t pc) { (void)pc; return NULL; }
bool interp_bridge_add_pre_opcode_hook(uint32_t pc, InterpPreOpcodeHook hook) {
    (void)pc; (void)hook; return true;
}
int FoundationHotkeysMovementHeld(void) { return held; }
void cpu_write16(CpuState *cpu,uint8 bank,uint16 addr,uint16 value) {
    (void)cpu; (void)bank; g_ram[addr]=(uint8)value;g_ram[addr+1]=(uint8)(value>>8);
}
/* Include the real module so guard and pending-layer cases exercise its
 * callbacks; no copied arithmetic model masquerades as production testing. */
#include "foundation_qol.c"
static unsigned checks;
#define CHECK(x) do {++checks;if(!(x)){fprintf(stderr,"failure line %d\n",__LINE__);return 1;}}while(0)
static void Put(unsigned a,unsigned v) {g_ram[a]=(uint8)v;g_ram[a+1]=(uint8)(v>>8);}
static CpuState Walk(void) {
    memset(g_ram,0,sizeof(g_ram));g_ram[0x20]=1;g_ram[0x408]=0x80;g_ram[0x452]=0x80;
    Put(0x459,0x100);Put(0x45f,0x100);Put(0x2ad,14);Put(0x2b1,14);
    CpuState cpu={0};cpu.A=1;cpu.D=0x0b00;cpu.DB=1;cpu.x_flag=1;
    movement_ready=held=1;movement_percent=300;snes_frame_counter=10;return cpu;
}
int main(void) {
    CHECK(FoundationQolScaleReward(4,125)==5);
    CHECK(FoundationQolScaleReward(0,1000)==0);
    CHECK(FoundationQolScaleReward(65535,100)==65535);
    CHECK(FoundationQolScaleReward(65535,1000)==65535);
    CHECK(FoundationQolScaleReward(6554,1000)==65535);
    CHECK(FoundationQolScaleReward(123,0)==123);
    CHECK(FoundationQolScaleReward(123,1001)==123);
    CpuState cpu=Walk();BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==2);
    /* Mid-instruction-boundary restore/release: only guest camera lineage
     * survives. Secondary finishes the already committed primary advance. */
    Put(0x2ad,16);held=0;cpu.A=1;BeforeWalkOperand(&cpu,0x01b139);CHECK(cpu.A==2);
    cpu=Walk();held=0;BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();g_ram[0x20]=5;BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();g_ram[0x543]=0x80;BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();g_ram[0x408]=0xff;BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();g_ram[0x409]=0x20;BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();Put(0x471,1);BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();g_ram[0x452]=0x81;BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();Put(0x45f,0);BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();Put(0x2b1,13);BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==1);
    cpu=Walk();g_ram[0x408]=0x81;Put(0x459,0xff00);g_ram[0x45b]=0xff;memcpy(g_ram+0x45f,g_ram+0x459,6);Put(0x2ad,1);Put(0x2b1,1);cpu.A=0xffff;
    BeforeWalkOperand(&cpu,0x01b076);CHECK(cpu.A==0xffff);
    memset(g_ram,0,sizeof(g_ram));g_ram[0x20]=5;cpu=(CpuState){0};cpu.D=0x0d00;cpu.S=0x1d5c;cpu.m_flag=cpu.x_flag=1;
    xp_percent=125;gold_percent=1000;Put(0xd21,4);Put(0xd1f,65535);BeforeVictory(&cpu,0x00ae9b);
    CHECK(Word(0xd21)==5&&Word(0xd1f)==65535);
    g_ram[0x20]=1;Put(0xd21,4);BeforeVictory(&cpu,0x00ae9b);CHECK(Word(0xd21)==4);
    printf("{\"passed\":true,\"synthetic_guard_checks\":%u}\n",checks);return 0;
}
