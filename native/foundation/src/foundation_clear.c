/* Generated faithful instructions in the verified Likado load clear.
 * Each commits through the bridge's faithful bus/clock path and returns to its
 * scheduler boundary. No host cursor, guest wait removal or raw VRAM fill. */
#include "foundation_clear.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "sha256.h"
#include "snes/interp_bridge.h"
#include "snes/snes.h"
#include "snes/cart.h"
#include "snes/ppu.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef SNESRECOMP_HAS_GENERATED_CODE
#include "gen/faithful_clear.generated.h"
#define GENERATED_CLEAR_AVAILABLE 1
#else
/* A ROM-free setup host has no generated guest instructions to execute. */
#define GENERATED_CLEAR_AVAILABLE 0
static const uint32_t GeneratedRoutinePCs[13]={0};
static unsigned GeneratedRoutineStep(CpuState *cpu,uint32_t pc,unsigned *cycles,uint32_t *next) {
    (void)cpu;(void)pc;(void)cycles;(void)next;abort();
}
static int GeneratedClearSupports(uint32_t pc) { (void)pc; return 0; }
static unsigned GeneratedClearStep(CpuState *cpu, uint32_t pc,
                                   unsigned *cycles, uint32_t *next) {
    (void)cpu; (void)pc; (void)cycles; (void)next; abort();
}
#endif
extern Snes *g_snes;
static int enabled, installed, identity;
static int routine_enabled;
static FILE *routine_trace;
static unsigned long long routine_steps[13];


/* NativeClear still controls only the earlier handwritten diagnostic route.
 * Generated original-cost steps default on independently, with exact guards. */
static int generated_enabled;
static unsigned long long generated_steps[3];
/* Diagnostic reduced policy removes only DEY/taken-BNE internal compute
 * cycles. Bus fetches, PPU transfers and every scheduler boundary remain. */
static int reduced_cost;
static int fast_cost;
static const uint8_t *bound_rom;
static size_t bound_size;
static unsigned long long completed_instructions;
static const uint8_t clean_hash[32] = {
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00
};

void FoundationClearReset(void) { bound_rom = NULL; bound_size = 0; identity = 0; }

void FoundationClearBeforeFrame(void) {
    if ((!enabled && !generated_enabled && !routine_enabled && !routine_trace) || !g_snes || !g_snes->cart || !g_rom) return;
    size_t size = g_snes->cart->romImageSize;
    if (bound_rom == g_rom && bound_size == size) return;
    FoundationClearReset(); bound_rom = g_rom; bound_size = size;
    if (size != 1572864) return;
    uint8_t hash[32]; sha256_compute(g_rom, size, hash);
    static const uint8_t instructions[] = {0x8d,0x18,0x21,0x88,0xd0,0xfa,0x60};
    identity = !memcmp(hash, clean_hash, 32) && !memcmp(g_rom + 0xcb2e, instructions, sizeof(instructions));
}

static int Context(const CpuState *cpu, uint32_t pc) {
    if ((!enabled && !generated_enabled) || !identity || !g_snes || !g_snes->ppu || !cpu ||
        cpu->emulation || cpu->m_flag || cpu->x_flag || cpu->A ||
        cpu->DB != 1 || (cpu->PB & 0x7f) != 1 || cpu->D != 0x900 ||
        cpu->S < 0x1b00 || cpu->S + 2 >= 0x1e00 ||
        (g_ram[cpu->S+1] | g_ram[cpu->S+2] << 8) != 0xc460 ||
        (g_ram[1] | g_ram[2] << 8) != 8 || g_ram[0x20] != 1 ||
        (g_ram[0x40e] | g_ram[0x40f] << 8) != 5) return 0;
    const Ppu *ppu = g_snes->ppu;
    if (!PPU_forcedBlank(ppu) || ppu->vramRemapMode ||
        !ppu->vramIncrementOnHigh || ppu->vramIncrement != 1) return 0;
    pc &= 0x7fffff;
    if (pc == 0x01cb2e) return cpu->Y && cpu->Y <= 0x1800 && ppu->vramPointer == 0x6000 - cpu->Y;
    if (pc == 0x01cb31) return cpu->Y && cpu->Y <= 0x1800 && ppu->vramPointer == 0x6001 - cpu->Y && ppu->vram[ppu->vramPointer-1] == 0;
    if (pc == 0x01cb32) return cpu->Y < 0x1800 && ppu->vramPointer == 0x6000 - cpu->Y && ppu->vram[ppu->vramPointer-1] == 0 &&
        cpu->_flag_Z == (cpu->Y == 0) && cpu->_flag_N == ((cpu->Y & 0x8000) != 0);
    return 0;
}

static uint8_t Fetch(CpuState *cpu, uint32_t pc) {
    return fast_cost ? interp_bridge_native_rom_fetch8(cpu, pc) :
        interp_bridge_native_read8(cpu, pc);
}

static void NativeInstruction(CpuState *cpu, uint32_t pc) {
    if (!Context(cpu, pc)) return;
    if (generated_enabled) {
        if (!GeneratedClearSupports(pc) || !interp_bridge_native_begin(cpu)) return;
        unsigned original_cycles; uint32_t next_pc;
        unsigned step = GeneratedClearStep(cpu, pc, &original_cycles, &next_pc);
        ++generated_steps[step];
        interp_bridge_native_commit(cpu, original_cycles, next_pc);
        return;
    }
    if (!interp_bridge_native_begin(cpu)) return;
    /* Real opcode/operand bus fetches preserve open bus and hardware epochs.
     * The whole image was validated before any transaction can begin. */
    Fetch(cpu, pc);
    unsigned cycles; uint32_t next;
    switch (pc & 0x7fffff) {
    case 0x01cb2e:
        Fetch(cpu, pc + 1);
        Fetch(cpu, pc + 2);
        interp_bridge_native_write16(cpu, 0x012118, 0);
        cycles = fast_cost ? 2 : 5; next = pc + 3; break;
    case 0x01cb31:
        cpu->Y = (uint16_t)(cpu->Y - 1);
        cpu->_flag_Z = cpu->Y == 0;
        cpu->_flag_N = (cpu->Y & 0x8000) != 0;
        cpu_mirrors_to_p(cpu);
        cycles = reduced_cost || fast_cost ? 1 : 2; next = pc + 1; break;
    default:
        Fetch(cpu, pc + 1);
        cycles = fast_cost ? 1 : cpu->_flag_Z || reduced_cost ? 2 : 3;
        next = (pc & 0xff0000) | (cpu->_flag_Z ? 0xcb34 : 0xcb2e);
        break;
    }
    ++completed_instructions;
    interp_bridge_native_commit(cpu, cycles, next);
}


static int RoutineContext(const CpuState *cpu, uint32_t raw_pc) {
    uint32_t pc = raw_pc & 0x7fffff;
    if (!identity || !g_snes || !g_snes->ppu || !cpu || cpu->emulation ||
        cpu->DB != 1 || (cpu->PB & 0x7f) != 1 || cpu->D != 0x900 ||
        cpu->S < 0x1b00 || cpu->S + 2 >= 0x1e00 ||
        (g_ram[1] | g_ram[2]<<8) != 8 || g_ram[0x20] != 1 ||
        (g_ram[0x40e] | g_ram[0x40f]<<8) != 5 ||
        !PPU_forcedBlank(g_snes->ppu)) return 0;
    if (pc == 0x01c45e) return cpu->m_flag && cpu->x_flag && cpu->S >= 0x1b02;
    if ((g_ram[cpu->S+1] | g_ram[cpu->S+2]<<8) != 0xc460) return 0;
    if (pc <= 0x01cb20) {
        if (!cpu->m_flag || !cpu->x_flag) return 0;
        return pc == 0x01cb19 || pc == 0x01cb1b ||
               ((pc == 0x01cb1d || pc == 0x01cb20) && (cpu->A & 255) == 128);
    }
    if (cpu->m_flag || cpu->x_flag) return 0;
    const Ppu *ppu=g_snes->ppu;
    if (ppu->vramRemapMode || !ppu->vramIncrementOnHigh || ppu->vramIncrement != 1) return 0;
    if (pc == 0x01cb22) return 1;
    if (pc == 0x01cb25) return cpu->Y == 0x1800;
    if (pc == 0x01cb28) return cpu->Y == 0x1800 && cpu->A == 0x4800;
    if (pc == 0x01cb2b) return cpu->Y == 0x1800 && cpu->A == 0x4800 && ppu->vramPointer == 0x4800;
    if (cpu->A) return 0;
    if (pc == 0x01cb2e) return cpu->Y && cpu->Y <= 0x1800 && ppu->vramPointer == 0x6000-cpu->Y;
    if (pc == 0x01cb31) return cpu->Y && cpu->Y <= 0x1800 && ppu->vramPointer == 0x6001-cpu->Y && ppu->vram[ppu->vramPointer-1] == 0;
    if (pc == 0x01cb32) return cpu->Y < 0x1800 && ppu->vramPointer == 0x6000-cpu->Y && ppu->vram[ppu->vramPointer-1] == 0 && cpu->_flag_Z == (cpu->Y == 0) && cpu->_flag_N == ((cpu->Y&0x8000) != 0);
    if (pc == 0x01cb34) return cpu->Y == 0 && ppu->vramPointer == 0x6000 && cpu->_flag_Z && !cpu->_flag_N;
    return 0;
}
static void RoutineInstruction(CpuState *cpu, uint32_t pc) {
    int valid=RoutineContext(cpu,pc);
    if (routine_trace && g_snes && g_snes->ppu && cpu) {
        const Ppu *p=g_snes->ppu;
        fprintf(routine_trace,"%u,%u,%d,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%llu,%llu,%llu,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",
          snes_frame_counter,pc,valid,cpu->A,cpu->X,cpu->Y,cpu->S,cpu->D,cpu->DB,cpu->PB,cpu->P,cpu->m_flag,cpu->x_flag,cpu->emulation,
          cpu->_flag_N,cpu->_flag_V,cpu->_flag_Z,cpu->_flag_C,cpu->_flag_I,cpu->_flag_D,cpu->open_bus,
          g_ram[cpu->S+1],g_ram[cpu->S+2],(unsigned long long)cpu->cycles,(unsigned long long)cpu->master_cycles,
          (unsigned long long)g_snes->beamMasterLast,g_snes->hPos,g_snes->vPos,p->vramPointer,p->vramIncrement,p->vramIncrementOnHigh,p->vramRemapMode,p->vramReadBuffer,
          g_ram[cpu->S],cpu->S ? g_ram[cpu->S-1] : 0,cpu->host_return_valid);
    }
    if (!routine_enabled || !valid || !interp_bridge_native_begin(cpu)) return;
    unsigned cycles;uint32_t next;unsigned ordinal=GeneratedRoutineStep(cpu,pc,&cycles,&next);
    ++routine_steps[ordinal];interp_bridge_native_commit(cpu,cycles,next);
}

void FoundationClearInit(void) {
    FILE *file = fopen("foundation.ini", "r"); char line[128], key[64]; int value;
    if (file) {
        while (fgets(line, sizeof(line), file)) {
            if (sscanf(line, " %63[^=]=%d", key, &value) != 2) continue;
            size_t len = strlen(key);
            while (len && (key[len-1] == ' ' || key[len-1] == '\t')) key[--len] = 0;
            if (!strcmp(key, "NativeClear")) enabled = value == 1;
        }
        fclose(file);
    }
    const char *env = getenv("SNESRECOMP_FOUNDATION_NATIVE_CLEAR");
    if (env) {
        reduced_cost = !strcmp(env, "reduced");
        fast_cost = !strcmp(env, "fast");
        enabled = reduced_cost || fast_cost || !strcmp(env, "original");
    }
    const char *generated = getenv("SNESRECOMP_FOUNDATION_GENERATED_CLEAR");
    generated_enabled = GENERATED_CLEAR_AVAILABLE && !reduced_cost && !fast_cost &&
        (!generated || !strcmp(generated, "1") || !strcmp(generated, "original"));
    /* Explicit diagnostics: 0 disables generated execution; combined with
     * NativeClear=0 this leaves the interpreter. This convenience selects
     * only the old handwritten original-cost path, never a faster policy. */
    if (generated && !strcmp(generated, "handwritten-original")) {
        generated_enabled = 0; enabled = 1; reduced_cost = fast_cost = 0;
    }

    const char *whole=getenv("SNESRECOMP_FOUNDATION_GENERATED_ROUTINE");
    /* Preserve explicit NativeClear=1 and its environment override as the
     * existing handwritten diagnostic route; NativeClear=0 leaves it off. */
    int native_diagnostic=enabled;
    if (native_diagnostic) generated_enabled=0;
    routine_enabled=generated_enabled && (!whole || !strcmp(whole,"1") || !strcmp(whole,"original"));
    if (generated && !strcmp(generated,"handwritten-original")) routine_enabled=0;
    const char *trace_path=getenv("SNESRECOMP_FOUNDATION_ROUTINE_TRACE");
    if (trace_path) {
        routine_trace=fopen(trace_path,"w");
        if (routine_trace) fputs("frame,pc,context,a,x,y,s,d,db,pb,p,m,xflag,e,n,v,z,c,i,decimal,open_bus,stack_lo,stack_hi,cycles,master,beam_master,h,vpos,vram,inc,onhigh,remap,readbuf,stack_at_s,stack_below_s,host_return\n",routine_trace);
    }
    if (GENERATED_CLEAR_AVAILABLE && (routine_enabled || routine_trace)) {
        int hooks=1;
        for (unsigned j=0;j<13;++j) hooks &= interp_bridge_add_pre_opcode_hook(GeneratedRoutinePCs[j],RoutineInstruction);
        hooks &= interp_bridge_add_pre_opcode_hook(0x01c461,RoutineInstruction);
        if (!hooks) { routine_enabled=0; if(routine_trace) {fclose(routine_trace);routine_trace=NULL;} }
    }
    if (routine_enabled) enabled=generated_enabled=reduced_cost=fast_cost=0;
    fprintf(stderr,"[foundation_generated_routine] enabled=%d\n",routine_enabled);
    if ((enabled || generated_enabled) && !installed) {
        installed = interp_bridge_add_pre_opcode_hook(0x01cb2e, NativeInstruction) &&
            interp_bridge_add_pre_opcode_hook(0x01cb31, NativeInstruction) &&
            interp_bridge_add_pre_opcode_hook(0x01cb32, NativeInstruction);
        if (!installed) enabled = generated_enabled = 0;
    }
    fprintf(stderr, "[foundation] native_clear_original_cost=%d\n", enabled && !generated_enabled && !reduced_cost && !fast_cost);
    fprintf(stderr, "[foundation_generated_clear] enabled=%d available=%d\n", generated_enabled, GENERATED_CLEAR_AVAILABLE);
    if (reduced_cost) fprintf(stderr, "[foundation] native_clear_reduced_internal_cost=1\n");
    if (fast_cost) fprintf(stderr, "[foundation] native_clear_fast_cost=1\n");
}


void FoundationClearShutdown(void) {
    unsigned long long total=0;
    for(unsigned j=0;j<13;++j) total+=routine_steps[j];
    fprintf(stderr,"[foundation_generated_routine] generated_instructions=%llu",total);
    for(unsigned j=0;j<13;++j) fprintf(stderr," pc%06x=%llu",GeneratedRoutinePCs[j],routine_steps[j]);
    fputc('\n',stderr);
    if(routine_trace) {fclose(routine_trace);routine_trace=NULL;}
    routine_enabled=0;
    fprintf(stderr, "[foundation_clear] native_instructions=%llu\n", completed_instructions);
    fprintf(stderr, "[foundation_generated_clear] generated_instructions=%llu sta=%llu dey=%llu bne=%llu\n",
        generated_steps[0]+generated_steps[1]+generated_steps[2], generated_steps[0], generated_steps[1], generated_steps[2]);
    enabled = reduced_cost = fast_cost = generated_enabled = 0; FoundationClearReset();
}
