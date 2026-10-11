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
static int GeneratedClearSupports(uint32_t pc) { (void)pc; return 0; }
static unsigned GeneratedClearStep(CpuState *cpu, uint32_t pc,
                                   unsigned *cycles, uint32_t *next) {
    (void)cpu; (void)pc; (void)cycles; (void)next; abort();
}
#endif
extern Snes *g_snes;
static int enabled, installed, identity;
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
    if ((!enabled && !generated_enabled) || !g_snes || !g_snes->cart || !g_rom) return;
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
    fprintf(stderr, "[foundation_clear] native_instructions=%llu\n", completed_instructions);
    fprintf(stderr, "[foundation_generated_clear] generated_instructions=%llu sta=%llu dey=%llu bne=%llu\n",
        generated_steps[0]+generated_steps[1]+generated_steps[2], generated_steps[0], generated_steps[1], generated_steps[2]);
    enabled = reduced_cost = fast_cost = generated_enabled = 0; FoundationClearReset();
}
