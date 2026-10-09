/* Authored equivalents of the captured straight-line metatile-index/word-load
 * instructions. The original attribute helper, map setup, column port store,
 * splits and cooperative waits still execute. No native progress is retained. */
#include "foundation_column_lookup.h"
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
static const uint8_t clean_hash[32] = {
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00
};
static int enabled, fast_cost, installed, identity;
static const uint8_t *bound_rom;
static size_t bound_size;
static uint64_t native_instructions;

static unsigned Ram16(unsigned at) {
    return g_ram[at] | (unsigned)g_ram[at + 1] << 8;
}

static unsigned Ram24(unsigned at) {
    return Ram16(at) | (unsigned)g_ram[at + 2] << 16;
}

void FoundationColumnLookupReset(void) {
    bound_rom = NULL; bound_size = 0; identity = 0;
}

void FoundationColumnLookupBeforeFrame(void) {
    if (!enabled || !g_snes || !g_snes->cart || !g_rom) return;
    size_t size = g_snes->cart->romImageSize;
    if (bound_rom == g_rom && bound_size == size) return;
    FoundationColumnLookupReset(); bound_rom = g_rom; bound_size = size;
    if (size != 1572864) return;
    uint8_t hash[32]; sha256_compute(g_rom, size, hash);
    static const uint8_t instructions[] = {
        0xad,0x20,0x05,0x29,0xff,0x00,0x0a,0x0a,0x0a,0x85,0x1b,
        0xa5,0x35,0x0a,0x18,0x65,0x1b,0x85,0x1b,0xc2,0x20,
        0xa4,0x1b,0xb7,0x29
    };
    identity = !memcmp(hash, clean_hash, 32) &&
        !memcmp(g_rom + 0xb4f3, instructions, sizeof(instructions));
}

static int Context(const CpuState *cpu) {
    if (!enabled || !identity || !cpu || !g_snes || !g_snes->ppu ||
        cpu->emulation || cpu->m_flag || cpu->x_flag || cpu->_flag_D ||
        cpu->PB != 1 || cpu->DB != 1 || cpu->D != 0x0b00 || cpu->S != 0x1c28 ||
        Ram16(cpu->S + 1) != 0xb25b || Ram16(1) != 8 || g_ram[0x20] != 1 ||
        Ram16(0x040e) != 5 || g_ram[0x0531] != 0x80 ||
        g_ram[0x0408] != 0x81 || g_ram[0x0407] ||
        Ram24(0x0b26) != 0x0a8818 || Ram24(0x0b29) != 0x038f58 ||
        Ram24(0x0b2c) != 0x098210 || Ram24(0x0b2f) ||
        Ram24(0x0b32) != 0x08f620 || g_ram[0x0b35] > 3 ||
        g_ram[0x0b36] || g_ram[0x0b37] > 3 || g_ram[0x0b38]) return 0;
    const Ppu *ppu = g_snes->ppu;
    if (!PPU_forcedBlank(ppu) || ppu->vramRemapMode ||
        !ppu->vramIncrementOnHigh || ppu->vramIncrement != 32) return 0;
    unsigned layer = g_ram[0x0b00];
    if (layer == 0) {
        if (g_ram[0x0b01] || g_ram[0x0b02] || Ram24(0x0b20) != 0x0996a2 ||
            g_ram[0x0b13] != 2 || g_ram[0x0b14] != 2 ||
            ppu->vramPointer < 0x4800 || ppu->vramPointer >= 0x5000) return 0;
    } else if (layer == 2) {
        if (g_ram[0x0b01] != 4 || g_ram[0x0b02] != 3 || Ram24(0x0b20) != 0x099700 ||
            g_ram[0x0b13] != 4 || g_ram[0x0b14] != 4 ||
            ppu->vramPointer < 0x5800 || ppu->vramPointer >= 0x6000) return 0;
    } else return 0;
    return 1;
}

static uint8_t Fetch(CpuState *cpu, uint32_t address) {
    return fast_cost ? interp_bridge_native_rom_fetch8(cpu, address) :
        interp_bridge_native_read8(cpu, address);
}

static uint16_t ReadWord(CpuState *cpu, uint32_t address) {
    uint8_t low = interp_bridge_native_read8(cpu, address);
    uint8_t high = interp_bridge_native_read8(cpu, (address + 1) & 0xffffff);
    return low | (uint16_t)high << 8;
}

static void SetZN(CpuState *cpu, uint16_t value) {
    cpu->_flag_Z = value == 0;
    cpu->_flag_N = (value & 0x8000) != 0;
}

static void NativeInstruction(CpuState *cpu, uint32_t pc) {
    if (!Context(cpu)) return;
    unsigned key = pc & 0x7fffff, bytes, cycles;
    switch (key) {
    case 0x01b4f3: bytes = 3; cycles = 5; break;
    case 0x01b4f6: bytes = 3; cycles = 3; break;
    case 0x01b4f9: case 0x01b4fa: case 0x01b4fb:
    case 0x01b500: case 0x01b501: bytes = 1; cycles = 2; break;
    case 0x01b506: bytes = 2; cycles = 3; break;
    case 0x01b50a: bytes = 2; cycles = 7; break;
    case 0x01b4fc: case 0x01b4fe: case 0x01b502:
    case 0x01b504: case 0x01b508: bytes = 2; cycles = 4; break;
    default: return;
    }
    if (!interp_bridge_native_begin(cpu)) return;
    Fetch(cpu, pc);
    uint16_t operand = 0;
    if (bytes > 1) operand = Fetch(cpu, pc + 1);
    if (bytes > 2) operand |= (uint16_t)Fetch(cpu, pc + 2) << 8;
    switch (key) {
    case 0x01b4f3:
        cpu->A = ReadWord(cpu, (uint32_t)cpu->DB << 16 | operand);
        SetZN(cpu, cpu->A); break;
    case 0x01b4f6:
        cpu->A &= operand; SetZN(cpu, cpu->A); break;
    case 0x01b4f9: case 0x01b4fa: case 0x01b4fb: case 0x01b500:
        cpu->_flag_C = (cpu->A & 0x8000) != 0;
        cpu->A = (uint16_t)(cpu->A << 1); SetZN(cpu, cpu->A); break;
    case 0x01b4fc: case 0x01b504:
        interp_bridge_native_write16(cpu, cpu->D + operand, cpu->A); break;
    case 0x01b4fe:
        cpu->A = ReadWord(cpu, cpu->D + operand); SetZN(cpu, cpu->A); break;
    case 0x01b501:
        cpu->_flag_C = 0; break;
    case 0x01b502: {
        uint16_t value = ReadWord(cpu, cpu->D + operand);
        unsigned result = (unsigned)cpu->A + value + cpu->_flag_C;
        cpu->_flag_V = ((~(cpu->A ^ value) & (cpu->A ^ result)) & 0x8000) != 0;
        cpu->_flag_C = result > 0xffff;
        cpu->A = (uint16_t)result; SetZN(cpu, cpu->A); break;
    }
    case 0x01b506:
        /* Captured REP #$20 is idempotent under the guarded M=0 contract. */
        cpu->m_flag = 0; break;
    case 0x01b508:
        cpu->Y = ReadWord(cpu, cpu->D + operand); SetZN(cpu, cpu->Y); break;
    default: {
        unsigned at = cpu->D + operand;
        unsigned pointer = ReadWord(cpu, at);
        pointer |= (unsigned)interp_bridge_native_read8(cpu, at + 2) << 16;
        cpu->A = ReadWord(cpu, (pointer + cpu->Y) & 0xffffff);
        SetZN(cpu, cpu->A); break;
    }
    }
    cpu_mirrors_to_p(cpu);
    if (fast_cost) cycles = cycles > bytes ? cycles - bytes : 1;
    ++native_instructions;
    interp_bridge_native_commit(cpu, cycles, pc + bytes);
}

void FoundationColumnLookupInit(void) {
    /* The player setting offers only the qualified original-cost route.
     * Changed timing remains an explicit diagnostic environment policy. */
    enabled = fast_cost = 0;
    FILE *file = fopen("foundation.ini", "r");
    char line[128], key[64]; int setting;
    if (file) {
        while (fgets(line, sizeof(line), file)) {
            if (sscanf(line, " %63[^=]=%d", key, &setting) != 2) continue;
            size_t length = strlen(key);
            while (length && (key[length - 1] == ' ' || key[length - 1] == '\t'))
                key[--length] = 0;
            if (!strcmp(key, "NativeColumns")) enabled = setting == 1;
        }
        fclose(file);
    }
    const char *value = getenv("SNESRECOMP_FOUNDATION_NATIVE_COLUMNS");
    if (value) {
        enabled = !strcmp(value, "original") || !strcmp(value, "fast");
        fast_cost = enabled && !strcmp(value, "fast");
    }
    if (enabled && !installed) {
        static const uint32_t sites[] = {
            0x01b4f3,0x01b4f6,0x01b4f9,0x01b4fa,0x01b4fb,0x01b4fc,
            0x01b4fe,0x01b500,0x01b501,0x01b502,0x01b504,0x01b506,
            0x01b508,0x01b50a
        };
        installed = 1;
        for (unsigned n = 0; n < sizeof(sites) / sizeof(sites[0]); ++n)
            installed &= interp_bridge_add_pre_opcode_hook(sites[n], NativeInstruction);
        if (!installed) enabled = 0;
    }
    fprintf(stderr, "[foundation] native_column_lookup=%d fast_fetch=%d\n", enabled, fast_cost);
}

void FoundationColumnLookupShutdown(void) {
    if (enabled) fprintf(stderr, "[foundation_column_lookup] native_instructions=%llu original_cost=%d fast_fetch=%d\n",
        (unsigned long long)native_instructions, !fast_cost, fast_cost);
    enabled = fast_cost = 0; FoundationColumnLookupReset();
}
