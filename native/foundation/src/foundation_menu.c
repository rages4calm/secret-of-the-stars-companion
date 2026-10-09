/* Native field-menu batching. Preserve normal guest frames and audio; finish
 * validated BG3 row uploads and window slide loops within the current frame.
 * Unsupported records/contexts retain the original coroutine wait. */
#include "foundation_menu.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "snes/interp_bridge.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Snes *g_snes;
static int enabled, trace;
static unsigned budget;

void FoundationMenuBeginFrame(void) { budget = 256; }

static int IsFieldMenuStack(CpuState *cpu, int slide) {
    if (!g_snes || g_ram[0x20] != 1 ||
        cpu->D != 0x0a00 || cpu->DB != 1 || !cpu->m_flag ||
        cpu->S < 0x1b00 || cpu->S >= 0x1e00) return 0;
    /* The field dispatcher tail-enters the menu from its interaction call.
     * Only scan active stack bytes; stale popped return addresses do not count.
     * Re-derived from guest state, so checkpoint/rewind needs no native latch. */
    int dispatcher = 0, menu_phase = 0;
    for (unsigned i = cpu->S + 1; i + 2 < 0x1e00 && i < cpu->S + 96; ++i) {
        unsigned ret = g_ram[i] | g_ram[i+1] << 8;
        unsigned bank = g_ram[i+2] & 0x7f;
        /* The interactive 02C000 call (return 029152) owns asynchronous
         * submenu/cursor producers. Do not batch those shared queues: doing
         * so can consume a submenu row before its original frame handoff.
         * Interactive slide waits can still be completed, but row producers
         * must retain their original frame handoff. */
        unsigned target = ret == 0x9136 ? 0x02910f : ret == 0x913f ? 0x00ff3b :
                          ret == 0x9162 ? 0x00ff23 : (slide && ret == 0x9152) ? 0x02c000 : 0;
        if (bank == 2 && target && cpu_read8(cpu, 2, ret-3) == 0x22 &&
            cpu_read8(cpu, 2, ret-2) == (target & 255) &&
            cpu_read8(cpu, 2, ret-1) == ((target >> 8) & 255) &&
            cpu_read8(cpu, 2, ret) == (target >> 16)) menu_phase = 1;
        if (bank != 1 || (ret != 0x88a4 && ret != 0x88be)) continue;
        unsigned call = ret - 3;
        if (cpu_read8(cpu, 1, call) == 0x22 &&
            cpu_read8(cpu, 1, call+1) == 0x00 &&
            cpu_read8(cpu, 1, call+2) == 0x8c &&
            cpu_read8(cpu, 1, call+3) == 0x01) dispatcher = 1;
    }
    return dispatcher && menu_phase;
}

static int DrainRowQueue(CpuState *cpu, unsigned *tile_count) {
    /* Original 008118 consumer: [count, VRAM word address, tile words],
     * zero terminated. Restrict this native path to the four BG3 transfer forms.
     * Validate the entire queue before changing PPU or guest memory. */
    unsigned flags = g_ram[0x02a0];
    if (flags != 0x81 && flags != 0x83 && flags != 0xc1 && flags != 0xc3) return 0;
    unsigned stride = flags & 2 ? 32 : 1;
    unsigned base = (g_snes->ppu->bgXsc[2] & 0xfc) << 8;
    if (base != 0x5000 || PPU_mode(g_snes->ppu) != 1) return 0;
    unsigned shape = g_snes->ppu->bgXsc[2] & 3;
    unsigned capacity = shape == 3 ? 0x1000 : shape ? 0x800 : 0x400;
    unsigned index = 0, records = 0, total = 0;
    for (;;) {
        if (index >= 0x1a0) return 0;
        unsigned count = g_ram[0x100 + index];
        if (!count) break;
        if (count > 32 || ++records > 16 || index + 3 + count * 2 >= 0x1a0) return 0;
        unsigned addr = g_ram[0x101+index] | g_ram[0x102+index] << 8;
        if (addr < base || addr + (count - 1) * stride >= base + capacity) return 0;
        total += count;
        index += 3 + count * 2;
    }
    if (!records) return 0;
    cpu_write8(cpu, 0, 0x2115, 0x80 | ((flags & 2) >> 1));
    for (index = 0; g_ram[0x100+index]; ) {
        unsigned count = g_ram[0x100+index];
        unsigned addr = g_ram[0x101+index] | g_ram[0x102+index] << 8;
        cpu_write16(cpu, 0, 0x2116, (uint16_t)addr);
        for (unsigned i = 0; i < count; ++i) {
            unsigned at = 0x103 + index + i * 2;
            if (flags & 0x40) cpu_write8(cpu, 0, 0x2119, g_ram[at+1]);
            else cpu_write16(cpu, 0, 0x2118, g_ram[at] | g_ram[at+1] << 8);
        }
        index += 3 + count * 2;
    }
    cpu_write8(cpu, 0, 0x02a0, 0);
    *tile_count = total;
    return 1;
}

static void BeforeFrameWait(CpuState *cpu, uint32_t pc) {
    (void)pc;
    if (!g_snes || !budget || (cpu->A & 255) != 1) return;
    uint16_t ret = cpu_read16(cpu, 0, (uint16_t)(cpu->S+1));
    unsigned bank = cpu_read8(cpu, 0, (uint16_t)(cpu->S+3)) & 0x7f;
    uint32_t caller = bank << 16 | ret;
    int rows = caller == 0x0291cd || caller == 0x029242 || caller == 0x008514;
    int slide = caller == 0x008675 || caller == 0x008692 ||
                caller == 0x0086b4 || caller == 0x0086cf;
    if (!rows && !slide) return;
    if (!IsFieldMenuStack(cpu, slide)) {
        if (trace) fprintf(stderr, "[foundation_menu_skip] frame=%d caller=%06X mode=%u actor=%u D=%04X DB=%02X S=%04X bg3sc=%02X queue=%02X\n",
            snes_frame_counter, caller, g_ram[0x20], g_ram[0x42b], cpu->D, cpu->DB, cpu->S,
            g_snes->ppu->bgXsc[2], g_ram[0x2a0]);
        return;
    }
    if (cpu_read8(cpu, 0, 0x8460) != 0x6b ||
        cpu_read8(cpu, 0, 0xff03) != 0x4c) return;
    unsigned tiles = 0;
    int drained = DrainRowQueue(cpu, &tiles);
    if (g_ram[0x02a0] != 0 || (rows && !drained && caller != 0x029242)) return;
    /* Use the original RTL instruction, keeping call/return bookkeeping.
     * Input polling, mandatory first/last waits and other coroutines still yield. */
    --budget;
    if (trace) fprintf(stderr, "[foundation_menu] frame=%d caller=%06X tiles=%u budget=%u\n",
                       snes_frame_counter, caller, tiles, budget);
    interp_bridge_pre_opcode_redirect(0x008460);
}

void FoundationMenuInit(void) {
    FILE *file = fopen("foundation.ini", "r");
    char line[128], key[64]; int value;
    if (file) {
        while (fgets(line, sizeof(line), file)) {
            if (sscanf(line, " %63[^=]=%d", key, &value) != 2) continue;
            size_t len = strlen(key);
            while (len && (key[len-1] == ' ' || key[len-1] == '\t')) key[--len] = 0;
            if (!strcmp(key, "FastMenus")) enabled = value == 1;
        }
        fclose(file);
    }
    const char *env = getenv("SNESRECOMP_FOUNDATION_FAST_MENUS");
    if (env) enabled = !strcmp(env, "1");
    trace = getenv("SNESRECOMP_FOUNDATION_MENU_TRACE") != NULL;
    if (enabled && !interp_bridge_add_pre_opcode_hook(0x00ff03, BeforeFrameWait)) enabled = 0;
    fprintf(stderr, "[foundation] fast_menus=%d\n", enabled);
}
