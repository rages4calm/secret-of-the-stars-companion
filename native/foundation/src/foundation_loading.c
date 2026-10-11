/* Read-only loading seam proof. Every row describes state BEFORE the original
 * opcode. A store row observes the two bytes the original 16-bit STA will write;
 * it does not perform the write. Entry is the observer's first seen store, which
 * can be a partial loop after a copied restore; it is not the routine's prologue.
 * Private CSV contains ROM-derived context and must remain under local/. */
#include "foundation_loading.h"
#include "constructor.h"
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

enum { kImageSize = 1572864, kFirstWord = 0x4800,
       kEndWord = 0x6000, kClearWords = 0x1800 };
static const uint8_t clean_identity[32] = {
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00
};
static FILE *trace;
static FILE *columns;
static int column_hooks_installed, column_active, column_pending, column_sequence;
static unsigned column_pass, column_count, column_entry_s, column_caller;
static unsigned column_last_pointer, column_last_word, column_write_count;
static unsigned column_attribute_input, column_attribute_seen;
static uint64_t column_cpu, column_master;
static const uint8_t *bound_rom;
static size_t bound_size;
static int initialized, hooks_installed, identity_ok, active, continuity_ok, prologue;
static unsigned epoch, pass, count, first_word, last_word, entry_remaining;
static unsigned previous_y, next_pointer, entry_s, entry_db;
static uint64_t entry_cpu, entry_master;

static unsigned Ram16(unsigned at) {
    return g_ram[at] | (unsigned)g_ram[at + 1] << 8;
}

static unsigned Ram24(unsigned at) {
    return Ram16(at) | (unsigned)g_ram[at + 2] << 16;
}

static void DiscardPass(void) {
    active = continuity_ok = prologue = 0;
    count = first_word = last_word = entry_remaining = 0;
    previous_y = next_pointer = entry_s = entry_db = 0;
    entry_cpu = entry_master = 0;
}

static void DiscardColumn(void) {
    column_active = column_pending = column_sequence = 0;
    column_count = column_entry_s = column_caller = 0;
    column_last_pointer = column_last_word = column_write_count = 0;
    column_attribute_input = column_attribute_seen = 0;
    column_cpu = column_master = 0;
}

/* These image buffers are immutable between reset/content binds. Never read
 * ROM through cpu_read*: even an observation must not update the data bus. */
static int BindRom(void) {
    if ((!trace && !columns) || !g_snes || !g_snes->cart || !g_rom) return 0;
    size_t size = g_snes->cart->romImageSize;
    if (bound_rom == g_rom && bound_size == size) return identity_ok;
    bound_rom = g_rom;
    bound_size = size;
    identity_ok = 0;
    DiscardPass();
    DiscardColumn();
    if (size == kImageSize) {
        uint8_t hash[32];
        sha256_compute(g_rom, size, hash);
        identity_ok = !memcmp(hash, clean_identity, sizeof(hash));
        /* Exact LoROM offsets, after the whole-image identity gate. */
        identity_ok = identity_ok && g_rom[0xcb2e] == 0x8d &&
            g_rom[0xcb2f] == 0x18 && g_rom[0xcb30] == 0x21 &&
            g_rom[0xcb34] == 0x60 && g_rom[0xb4b8] == 0xe2 &&
            g_rom[0xb50c] == 0x8f && g_rom[0xb50d] == 0x18 &&
            g_rom[0xb50e] == 0x21 && g_rom[0xb50f] == 0 &&
            g_rom[0xb59b] == 0x60;
    }
    fprintf(stderr, "[foundation_loading] read-only rom_identity=%d image_size=%zu\n",
            identity_ok, size);
    return identity_ok;
}

static int PortBank(unsigned db) {
    return (db & 0x7f) < 0x40;
}

static int Context(const CpuState *cpu, const Ppu *ppu, int exit) {
    if (!cpu || !ppu || cpu->emulation || cpu->m_flag || cpu->x_flag ||
        cpu->A || !PortBank(cpu->DB) || (cpu->PB & 0x7f) != 1 ||
        !PPU_forcedBlank(ppu) || ppu->vramRemapMode ||
        ppu->vramIncrement != 1 || !ppu->vramIncrementOnHigh) return 0;
    if (exit) return cpu->Y == 0 && ppu->vramPointer == kEndWord &&
                     cpu->_flag_Z && !cpu->_flag_N;
    return cpu->Y && cpu->Y <= kClearWords &&
           ppu->vramPointer == kEndWord - cpu->Y;
}

static void Row(const char *event, CpuState *cpu, uint32_t pc, int context,
                int sequence, int store, int completed, int full_range) {
    const Ppu *ppu = g_snes->ppu;
    const unsigned pointer = ppu->vramPointer;
    const unsigned stack_valid = cpu->S <= 0x1ffc;
    const unsigned caller_return = stack_valid ? Ram16(cpu->S + 1) : 0;
    const unsigned caller_next = stack_valid ? (unsigned)cpu->PB << 16 |
                                             ((caller_return + 1) & 0xffff) : 0;
    const unsigned task = Ram16(1);
    const unsigned task_valid = task <= 0x1fec;
    const int clocks_valid = active && cpu->cycles >= entry_cpu &&
                             cpu->master_cycles >= entry_master;
    /* ROM/context guards make the raw pointer the exact unremapped write
     * destination. Invalid rows retain context but claim no actual bytes. */
    const int bytes_valid = store && context;
    fprintf(trace, "%u,%u,%s,%d,%u,%d,%d,%d,%d,",
            epoch, pass, event, snes_frame_counter, pc, identity_ok, context, sequence, prologue);
    fprintf(trace, "%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,",
            cpu->A, cpu->X, cpu->Y, cpu->P, cpu->m_flag, cpu->x_flag,
            cpu->emulation, cpu->D, cpu->DB, cpu->PB, cpu->S);
    fprintf(trace, "%u,%u,%u,%u,%u,%u,%u,%llu,%llu,%llu,%u,%u,",
            cpu->_flag_N, cpu->_flag_V, cpu->_flag_Z, cpu->_flag_C,
            cpu->_flag_I, cpu->_flag_D, cpu->open_bus,
            (unsigned long long)cpu->cycles, (unsigned long long)cpu->master_cycles,
            (unsigned long long)g_snes->beamMasterLast, g_snes->hPos, g_snes->vPos);
    fprintf(trace, "%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,",
            !!PPU_forcedBlank(ppu), g_ram[0x20], ppu->bgmode,
            g_snes->input1_currentState, task, task_valid,
            task_valid ? g_ram[task + 0x10] : 0,
            task_valid ? g_ram[task + 0x11] : 0,
            task_valid ? Ram16(task + 0x12) : 0,
            stack_valid, caller_return, caller_next);
    fprintf(trace, "%u,%u,%u,%u,%u,%d,%u,%u,%u,%u,%u,",
            pointer, ppu->vramIncrement, ppu->vramIncrementOnHigh,
            ppu->vramRemapMode, ppu->vramReadBuffer, bytes_valid,
            bytes_valid ? pointer : 0, bytes_valid ? pointer * 2 : 0,
            bytes_valid ? cpu->A & 255 : 0, bytes_valid ? cpu->A >> 8 : 0,
            bytes_valid ? ppu->vram[pointer & 0x7fff] : 0);
    fprintf(trace, "%u,%u,%u,%u,%u,%d,%d,%d,%llu,%llu,",
            first_word, last_word, count, entry_remaining, next_pointer,
            completed, full_range, clocks_valid,
            (unsigned long long)(clocks_valid ? cpu->cycles - entry_cpu : 0),
            (unsigned long long)(clocks_valid ? cpu->master_cycles - entry_master : 0));
    const int last_valid = active && count && last_word >= kFirstWord && last_word < kEndWord;
    fprintf(trace, "%d,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,",
            last_valid, last_valid ? last_word : 0,
            last_valid ? ppu->vram[last_word] : 0,
            Ram16(0x040e), g_ram[0x0531], g_ram[0x0408],
            Ram16(0x02ad), Ram16(0x02af), Ram16(0x02b1), Ram16(0x02b3),
            Ram24(0x0513), Ram24(0x0516), Ram24(0x0506), Ram24(0x0509),
            Ram24(0x0500), Ram24(0x0503), Ram24(0x0537), Ram24(0x055c),
            g_ram[0x0970], g_ram[0x0971]);
    /* Label direct-page bytes as valid only in the low-WRAM mirror. No MMIO
     * peek is used for an unfamiliar D. Original camera words above are raw
     * uint16; the checker must interpret them as signed where appropriate. */
    const unsigned dp_valid = cpu->D <= 0x1fc6;
    const unsigned dp = dp_valid ? cpu->D : 0;
    fprintf(trace, "%u,%u,%u,%u,%u,%u,%u,%u\n", dp_valid,
            dp_valid ? g_ram[dp] : 0, dp_valid ? g_ram[dp + 1] : 0,
            dp_valid ? g_ram[dp + 2] : 0, dp_valid ? g_ram[dp + 3] : 0,
            dp_valid ? Ram16(dp + 0x0d) : 0, dp_valid ? Ram16(dp + 0x0f) : 0,
            dp_valid ? Ram16(dp + 0x15) : 0);
}

static void ObserveClearEntry(CpuState *cpu, uint32_t pc) {
    if (!trace || !BindRom() || !g_snes->ppu) return;
    /* This is the actual prologue; accumulator/index width and contents have
     * not yet been initialized. Record them rather than impose the store guard. */
    DiscardPass();
    ++pass;
    active = prologue = 1;
    continuity_ok = PortBank(cpu->DB) && (cpu->PB & 0x7f) == 1 &&
                    !!PPU_forcedBlank(g_snes->ppu);
    entry_s = cpu->S;
    entry_db = cpu->DB;
    entry_cpu = cpu->cycles;
    entry_master = cpu->master_cycles;
    Row("clear_entry", cpu, pc, continuity_ok, continuity_ok, 0, 0, 0);
}

static void ObserveStore(CpuState *cpu, uint32_t pc) {
    if (!trace || !BindRom() || !g_snes->ppu) return;
    const Ppu *ppu = g_snes->ppu;
    const int context = Context(cpu, ppu, 0);
    if (!active || !count) {
        if (!active) {
            ++pass;
            active = 1;
            prologue = 0;
            continuity_ok = context;
            entry_s = cpu->S;
            entry_db = cpu->DB;
            entry_cpu = cpu->cycles;
            entry_master = cpu->master_cycles;
        } else if (!context || cpu->S != entry_s || cpu->DB != entry_db) {
            continuity_ok = 0;
        }
        first_word = last_word = ppu->vramPointer;
        entry_remaining = cpu->Y;
        previous_y = cpu->Y;
        next_pointer = ppu->vramPointer;
        Row("entry", cpu, pc, context, continuity_ok, 0, 0, 0);
    } else if (!context || cpu->Y + 1 != previous_y ||
               ppu->vramPointer != next_pointer || cpu->S != entry_s ||
               cpu->DB != entry_db || cpu->cycles < entry_cpu ||
               cpu->master_cycles < entry_master) {
        continuity_ok = 0;
    }
    ++count;
    last_word = ppu->vramPointer;
    previous_y = cpu->Y;
    next_pointer = (ppu->vramPointer + 1) & 0xffff;
    Row("store", cpu, pc, context, continuity_ok, 1, 0, 0);
}

static void ObserveLoopPhase(CpuState *cpu, uint32_t pc) {
    if (!trace || !BindRom() || !g_snes->ppu) return;
    const Ppu *ppu = g_snes->ppu;
    const int after_store = (pc & 0x7fffff) == 0x01cb31;
    /* DEY observes the old count, BNE the decremented count. Neither site
     * executes a PPU write; only the preceding original STA did that. */
    int context = !cpu->emulation && !cpu->m_flag && !cpu->x_flag && !cpu->A &&
        PortBank(cpu->DB) && (cpu->PB & 0x7f) == 1 && PPU_forcedBlank(ppu) &&
        !ppu->vramRemapMode && ppu->vramIncrement == 1 && ppu->vramIncrementOnHigh;
    context = context && (after_store ?
        cpu->Y && cpu->Y <= kClearWords && ppu->vramPointer == kEndWord + 1 - cpu->Y :
        cpu->Y < kClearWords && ppu->vramPointer == kEndWord - cpu->Y);
    int sequence = active && count && context && continuity_ok &&
        ppu->vramPointer == next_pointer && cpu->S == entry_s && cpu->DB == entry_db &&
        (after_store ? cpu->Y == previous_y : cpu->Y + 1 == previous_y) &&
        last_word >= kFirstWord && last_word < kEndWord && ppu->vram[last_word] == 0;
    if (!sequence && active) continuity_ok = 0;
    Row(after_store ? "after_store" : "after_dey", cpu, pc, context, sequence, 0, 0, 0);
}

/* A ROM peek is an observation, never a CPU access. Reject non-ROM pointers
 * rather than sampling MMIO/open bus or a mirrored/padded image. */
static const uint8_t *ColumnRom(unsigned address, unsigned length) {
    unsigned bank = address >> 16, low = address & 0xffff;
    if (!identity_ok || address > 0xffffff || low < 0x8000 ||
        length > 0x10000u - low) return NULL;
    size_t offset = (size_t)(bank & 0x7f) * 0x8000u + (low & 0x7fff);
    if (offset > bound_size || length > bound_size - offset) return NULL;
    return bound_rom + offset;
}

static void ColumnNumber(uint64_t value) {
    fprintf(columns, ",%llu", (unsigned long long)value);
}

static void ColumnHex(const uint8_t *bytes, unsigned size) {
    fputc(',', columns);
    for (unsigned n = 0; n < size; ++n) fprintf(columns, "%02x", bytes ? bytes[n] : 0);
}

static void ColumnAttributeHash(unsigned address) {
    const uint8_t *bytes = ColumnRom(address, 256);
    uint8_t hash[32] = {0};
    if (bytes) sha256_compute(bytes, 256, hash);
    ColumnHex(hash, 32);
}

static int ColumnStoreContext(const CpuState *cpu, const Ppu *ppu) {
    return cpu && ppu && !cpu->emulation && !cpu->m_flag && !cpu->x_flag &&
        cpu->D == 0x0b00 && (cpu->PB & 0x7f) == 1 && PPU_forcedBlank(ppu) &&
        !ppu->vramRemapMode && ppu->vramIncrement == 32 &&
        ppu->vramIncrementOnHigh && ppu->vramPointer >= 0x4800 &&
        ppu->vramPointer < 0x6000;
}

static void ColumnRow(const char *event, CpuState *cpu, uint32_t pc,
                      int context, int sequence, int store, int post, int complete) {
    const Ppu *ppu = g_snes->ppu;
    const unsigned dp_valid = cpu->D <= 0x1f34;
    const unsigned dp = dp_valid ? cpu->D : 0;
    const unsigned stack_valid = cpu->S <= 0x1ffc;
    const unsigned ret = stack_valid ? Ram16(cpu->S + 1) : 0;
    const unsigned task = Ram16(1);
    const unsigned task_valid = task <= 0x1fec;
    const unsigned tile_source = dp_valid ? (Ram24(dp + 0x29) + cpu->Y) & 0xffffff : 0;
    const uint8_t *tile = dp_valid ? ColumnRom(tile_source, 2) : NULL;
    const unsigned attr_id = column_attribute_seen ? column_attribute_input : g_ram[0x0520];
    const unsigned attr_source = dp_valid ? (Ram24(dp + 0x2c) + attr_id) & 0xffffff : 0;
    const uint8_t *attr = dp_valid ? ColumnRom(attr_source, 1) : NULL;
    const int clocks = column_active && cpu->cycles >= column_cpu && cpu->master_cycles >= column_master;
    fputs(event, columns);
#define N(value) ColumnNumber((uint64_t)(value))
    N(epoch); N(column_pass); N(snes_frame_counter); N(pc); N(identity_ok);
    N(context); N(sequence); N(complete); N(column_active); N(column_count);
    N(cpu->A); N(cpu->X); N(cpu->Y); N(cpu->P); N(cpu->m_flag); N(cpu->x_flag);
    N(cpu->emulation); N(cpu->D); N(cpu->DB); N(cpu->PB); N(cpu->S);
    N(cpu->_flag_N); N(cpu->_flag_V); N(cpu->_flag_Z); N(cpu->_flag_C);
    N(cpu->_flag_I); N(cpu->_flag_D); N(cpu->open_bus);
    N(cpu->cycles); N(cpu->master_cycles); N(g_snes->beamMasterLast);
    N(g_snes->hPos); N(g_snes->vPos); N(cpu->coprocessor_master_cycles);
    N(clocks); N(clocks ? cpu->cycles - column_cpu : 0);
    N(clocks ? cpu->master_cycles - column_master : 0);
    N(stack_valid); N(ret); N(stack_valid ? ((unsigned)cpu->PB << 16) | ((ret + 1) & 0xffff) : 0);
    N(column_entry_s); N(column_caller); N(task); N(task_valid);
    N(task_valid ? g_ram[task + 0x10] : 0); N(task_valid ? g_ram[task + 0x11] : 0);
    N(task_valid ? Ram16(task + 0x12) : 0);
    N(PPU_forcedBlank(ppu)); N(g_ram[0x20]); N(ppu->bgmode); N(g_snes->input1_currentState);
    N(Ram16(0x040e)); N(g_ram[0x0531]); N(g_ram[0x0408]); N(g_ram[0x0407]);
    N(Ram16(0x02ad)); N(Ram16(0x02af)); N(Ram16(0x02b1)); N(Ram16(0x02b3));
    N(g_ram[0x046d]); N(g_ram[0x046e]); N(g_ram[0x046f]); N(g_ram[0x0470]);
    N(Ram24(0x0513)); N(Ram24(0x0516)); N(Ram24(0x0506)); N(Ram24(0x0509));
    N(Ram24(0x0500)); N(Ram24(0x0503)); N(Ram24(0x0537)); N(Ram24(0x055c));
    N(Ram24(0x0453)); N(Ram24(0x0456)); N(g_ram[0x0970]); N(g_ram[0x0971]);
    N(g_ram[0x0404]); N(g_ram[0x0405]); N(g_ram[0x0441]); N(g_ram[0x0442]);
    N(g_ram[0x0443]); N(g_ram[0x0444]); N(g_ram[0x0520]);
    N(ppu->vramPointer); N(ppu->vramIncrement); N(ppu->vramIncrementOnHigh);
    N(ppu->vramRemapMode); N(ppu->vramReadBuffer); N(ppu->vramWriteCount);
    N(store && context); N(store && context ? ppu->vramPointer : 0);
    N(store && context ? ppu->vramPointer * 2 : 0); N(store && context ? cpu->A & 255 : 0);
    N(store && context ? cpu->A >> 8 : 0); N(store && context ? ppu->vram[ppu->vramPointer & 0x7fff] : 0);
    N(post && column_pending); N(column_last_pointer); N(column_last_word);
    N(column_pending ? ppu->vram[column_last_pointer & 0x7fff] : 0);
    N(column_pending ? (column_last_pointer + 32) & 0xffff : 0);
    N(dp_valid); N(dp_valid ? g_ram[dp] : 0); N(dp_valid ? g_ram[dp + 1] : 0);
    N(dp_valid ? g_ram[dp + 2] : 0); N(dp_valid ? g_ram[dp + 3] : 0);
    N(dp_valid ? g_ram[dp + 4] : 0); N(dp_valid ? Ram16(dp + 0x0d) : 0);
    N(dp_valid ? Ram16(dp + 0x0f) : 0); N(dp_valid ? Ram16(dp + 0x15) : 0);
    N(dp_valid ? g_ram[dp + 0x1f] : 0); N(dp_valid ? Ram24(dp + 0x20) : 0);
    N(dp_valid ? Ram24(dp + 0x23) : 0); N(dp_valid ? Ram24(dp + 0x26) : 0);
    N(dp_valid ? Ram24(dp + 0x29) : 0); N(dp_valid ? Ram24(dp + 0x2c) : 0);
    N(dp_valid ? Ram24(dp + 0x2f) : 0); N(dp_valid ? Ram24(dp + 0x32) : 0);
    N(dp_valid ? Ram16(dp + 0x19) : 0); N(dp_valid ? Ram16(dp + 0x1b) : 0);
    N(dp_valid ? Ram16(dp + 0x1d) : 0); N(dp_valid ? g_ram[dp + 0x35] : 0);
    N(dp_valid ? g_ram[dp + 0x37] : 0); N(column_attribute_seen); N(column_attribute_input);
    N(attr != NULL); N(attr_source); N(attr ? *attr & 15 : 0);
    N(tile != NULL); N(tile_source); N(tile ? tile[0] | (unsigned)tile[1] << 8 : 0);
#undef N
    ColumnHex(dp_valid ? g_ram + dp : NULL, 0x3d);
    ColumnHex(dp_valid ? g_ram + dp + 0xc9 : NULL, 3);
    /* Selector E indexes this exact 256-byte WRAM range with an 8-bit X.
     * Selector F additionally consults stage/condition records captured above. */
    ColumnHex(g_ram + 0x53f9, 256);
    ColumnAttributeHash(Ram24(0x0537)); ColumnAttributeHash(Ram24(0x055c));
    fputc('\n', columns);
}

static void ObserveColumn(CpuState *cpu, uint32_t pc) {
    if (!columns || !BindRom() || !g_snes->ppu) return;
    const unsigned key = pc & 0x7fffff;
    const Ppu *ppu = g_snes->ppu;
    if (key == 0x01b4b8) {
        DiscardColumn(); ++column_pass; column_active = column_sequence = 1;
        column_entry_s = cpu->S;
        column_caller = cpu->S <= 0x1ffc ? ((unsigned)cpu->PB << 16) | ((Ram16(cpu->S + 1) + 1) & 0xffff) : 0;
        column_cpu = cpu->cycles; column_master = cpu->master_cycles;
        ColumnRow("column_entry", cpu, pc, cpu->D == 0x0b00, 1, 0, 0, 0);
        return;
    }
    if (!column_active) return;
    if (key == 0x01b50c) {
        int context = ColumnStoreContext(cpu, ppu);
        int sequence = context && column_sequence && !column_pending && cpu->S == column_entry_s;
        if (!sequence) column_sequence = 0;
        ++column_count;
        column_last_pointer = ppu->vramPointer; column_last_word = cpu->A;
        column_write_count = ppu->vramWriteCount;
        ColumnRow("column_store", cpu, pc, context, sequence, 1, 0, 0);
        column_pending = 1;
    } else if (key == 0x01b510) {
        int context = column_pending && !cpu->m_flag && !cpu->x_flag && cpu->D == 0x0b00;
        int sequence = context && column_sequence &&
            ppu->vram[column_last_pointer & 0x7fff] == column_last_word &&
            ppu->vramPointer == ((column_last_pointer + 32) & 0xffff) &&
            ppu->vramWriteCount == column_write_count + 1;
        if (!sequence) column_sequence = 0;
        ColumnRow("column_after_store", cpu, pc, context, sequence, 0, 1, 0);
        column_pending = 0;
    } else if (key == 0x01b59b) {
        int complete = column_sequence && !column_pending && column_count == 30 && cpu->S == column_entry_s;
        ColumnRow("column_exit", cpu, pc, cpu->D == 0x0b00, column_sequence, 0, 0, complete);
        fflush(columns); DiscardColumn();
    } else {
        const char *event = "column_phase";
        if (key == 0x01b59c) event = "edge_entry";
        else if (key == 0x01b4c2) event = "edge_done";
        else if (key == 0x01b4c5) event = "split_done";
        else if (key == 0x01b65e) event = "segment_entry";
        else if (key == 0x01b6b6) event = "segment_exit";
        else if (key == 0x01b4e0) { event = "cell_begin"; column_attribute_seen = 0; }
        else if (key == 0x01b704) {
            event = "attribute_entry"; column_attribute_input = cpu->A & 255; column_attribute_seen = 1;
        } else if (key == 0x01b710) event = "attribute_selector_e";
        else if (key == 0x01b714) event = "attribute_selector_f";
        else if (key == 0x01b723) event = "attribute_e_record";
        else if (key == 0x01b767) event = "attribute_f_record";
        else if (key == 0x01b4f1) event = "attribute_done";
        else if (key == 0x01b4f3) event = "lookup_entry";
        else if (key == 0x01b50a) event = "tile_load";
        ColumnRow(event, cpu, pc, cpu->D == 0x0b00, column_sequence, 0, 0, 0);
    }
}

static void ObserveConstructor(CpuState *cpu, uint32_t pc) {
    if (!BindRom() || !g_snes->ppu) return;
    const char *event = (pc & 0x7fffff) == 0x01d080 ? "constructor_entry" : "constructor_exit";
    if (trace) Row(event, cpu, pc, 0, 0, 0, 0, 0);
    if (columns) ColumnRow(event, cpu, pc, 0, 0, 0, 0, 0);
}

static void ObserveExit(CpuState *cpu, uint32_t pc) {
    if (!trace || !BindRom() || !g_snes->ppu) return;
    const Ppu *ppu = g_snes->ppu;
    const int context = Context(cpu, ppu, 1);
    const int completed = active && context && continuity_ok &&
        previous_y == 1 && count == entry_remaining &&
        ppu->vramPointer == next_pointer && cpu->S == entry_s && cpu->DB == entry_db;
    const int full_range = completed && first_word == kFirstWord &&
        last_word == kEndWord - 1 && count == kClearWords;
    Row("exit", cpu, pc, context, completed, 0, completed, full_range);
    fflush(trace);
    DiscardPass();
}

void FoundationLoadingReset(void) {
    ConstructorReset();
    /* Never serialize the observer's continuity. A restored mid-clear starts
     * a new, explicitly partial observation with its own epoch and pass. */
    ++epoch;
    DiscardPass();
    DiscardColumn();
    bound_rom = NULL;
    bound_size = 0;
    identity_ok = 0;
    if (trace) fflush(trace);
    if (columns) fflush(columns);
}

void FoundationLoadingInit(void) {
    if (initialized) return;
    initialized = 1;
    const char *path = getenv("SNESRECOMP_FOUNDATION_LOADING_TRACE");
    const char *column_path = getenv("SNESRECOMP_FOUNDATION_COLUMNS_TRACE");
    if ((!path || !*path) && (!column_path || !*column_path)) return;
    trace = path && *path ? fopen(path, "w") : NULL;
    columns = column_path && *column_path ? fopen(column_path, "w") : NULL;
    if (!trace && path && *path) {
        fprintf(stderr, "[foundation_loading] cannot open private diagnostic trace\n");
    }
    if (!columns && column_path && *column_path) {
        fprintf(stderr, "[foundation_loading] cannot open private column trace\n");
    }
    if (!trace && !columns) {
        return;
    }
    if (trace) fprintf(trace,
        "epoch,pass,event,frame,pc,rom_ok,context_ok,sequence_ok,prologue_observed,"
        "a,x,y,p,m,x_flag,e,d,db,pb,s,n,v,z,c,i,decimal,open_bus,"
        "cpu_cycles,master_cycles,beam_master_last,beam_h,beam_v,"
        "forced_blank,mode,bgmode,input,task_index,task_valid,task_status,task_wait,task_sp,"
        "caller_valid,caller_return,caller_next,vram_pointer,vram_increment,increment_on_high,"
        "vram_remap,vram_read_buffer,store_bytes_valid,store_word_address,store_byte_address,"
        "store_low,store_high,prior_word,range_first,range_last,observed_stores,entry_remaining,"
        "expected_next_pointer,completed,full_range,clocks_valid,pass_cpu_delta,pass_master_delta,"
        "peek_last_valid,peek_last_address,peek_last_word,scene,loading_flag,direction,"
        "camera1_x,camera1_y,camera2_x,camera2_y,map1,map2,cells1,cells2,tiles1,tiles2,"
        "attributes1,attributes2,constructor_selector,constructor_iteration,"
        "dp_valid,dp_layer,dp_camera_selector,dp_resource_selector,dp_remaining,"
        "dp_edge_x,dp_edge_y,dp_word_pointer\n");
    if (trace && !hooks_installed) {
        int entry_ok = interp_bridge_add_pre_opcode_hook(0x01cb19, ObserveClearEntry);
        int store_ok = interp_bridge_add_pre_opcode_hook(0x01cb2e, ObserveStore);
        int exit_ok = interp_bridge_add_pre_opcode_hook(0x01cb34, ObserveExit);
        int dey_ok = interp_bridge_add_pre_opcode_hook(0x01cb31, ObserveLoopPhase);
        int branch_ok = interp_bridge_add_pre_opcode_hook(0x01cb32, ObserveLoopPhase);
        int constructor_entry_ok = interp_bridge_add_pre_opcode_hook(0x01d080, ObserveConstructor);
        int constructor_exit_ok = interp_bridge_add_pre_opcode_hook(0x01d106, ObserveConstructor);
        hooks_installed = entry_ok && store_ok && exit_ok && dey_ok && branch_ok &&
                          constructor_entry_ok && constructor_exit_ok;
        if (!hooks_installed) {
            fprintf(stderr, "[foundation_loading] observer registration FAILED\n");
            fclose(trace);
            trace = NULL;
        }
    }
    if (columns) {
        fputs("event,epoch,column,frame,pc,rom_ok,context_ok,sequence_ok,completed,active,stores,"
            "a,x,y,p,m,x_flag,e,d,db,pb,s,n,v,z,c,i,decimal,open_bus,"
            "cpu_cycles,master_cycles,beam_master_last,beam_h,beam_v,coprocessor_master,"
            "clocks_valid,column_cpu_delta,column_master_delta,caller_valid,caller_return,caller_next,"
            "column_entry_s,column_caller,task_index,task_valid,task_status,task_wait,task_sp,"
            "forced_blank,mode,bgmode,input,scene,loading_flag,direction,wrap,"
            "camera1_x,camera1_y,camera2_x,camera2_y,width1,height1,width2,height2,"
            "map1,map2,cells1,cells2,tiles1,tiles2,attributes1,attributes2,conditions_e,conditions_f,"
            "constructor_selector,constructor_iteration,cell_x,cell_y,stage_441,stage_442,stage_443,stage_444,metatile,"
            "vram_pointer,vram_increment,increment_on_high,vram_remap,vram_read_buffer,vram_write_count,"
            "store_bytes_valid,store_word_address,store_byte_address,store_low,store_high,prior_word,"
            "post_valid,post_address,post_expected_word,post_actual_word,post_expected_pointer,"
            "dp_valid,dp_layer,dp_camera_selector,dp_resource_selector,dp_remaining,dp_chunk_remaining,"
            "dp_edge_x,dp_edge_y,dp_word_pointer,dp_outside,dp_map,dp_segment,dp_cells,dp_tiles,dp_attributes,"
            "dp_conditions_e,dp_conditions_f,dp_cell_index,dp_tile_index,dp_metatile_index,dp_tile_quadrant,"
            "dp_cell_quadrant,attribute_seen,attribute_input,attribute_rom_valid,attribute_source,attribute_selector,"
            "tile_rom_valid,tile_source,tile_expected,dp_hex,coordinate_hex,progression_hex,"
            "attributes1_sha256,attributes2_sha256\n", columns);
        if (!column_hooks_installed) {
            static const uint32_t sites[] = {
                0x01b4b8, 0x01b50c, 0x01b510, 0x01b59b, 0x01b59c,
                0x01b4c2, 0x01b4c5, 0x01b65e, 0x01b6b6, 0x01b4e0,
                0x01b704, 0x01b710, 0x01b714, 0x01b723, 0x01b767,
                0x01b4f1, 0x01b4f3, 0x01b50a
            };
            column_hooks_installed = 1;
            for (unsigned n = 0; n < sizeof(sites) / sizeof(sites[0]); ++n)
                column_hooks_installed &= interp_bridge_add_pre_opcode_hook(sites[n], ObserveColumn);
            column_hooks_installed &= interp_bridge_add_pre_opcode_hook(0x01d080, ObserveConstructor);
            column_hooks_installed &= interp_bridge_add_pre_opcode_hook(0x01d106, ObserveConstructor);
            if (!column_hooks_installed) {
                fprintf(stderr, "[foundation_loading] column observer registration FAILED\n");
                fclose(columns); columns = NULL;
            }
        }
    }
    FoundationLoadingReset();
    fprintf(stderr, "[foundation_loading] read-only clear_trace=%d column_trace=%d observers registered\n", trace != NULL, columns != NULL);
}

void FoundationLoadingBeforeFrame(void) {
    ConstructorInit();
    if (trace || columns) {
        BindRom();
        if (trace) fflush(trace);
        if (columns) fflush(columns);
    }
}

void FoundationLoadingShutdown(void) {
    if (trace) {
        fclose(trace);
        trace = NULL;
    }
    if (columns) {
        fclose(columns);
        columns = NULL;
    }
    /* Composed observers have no individual removal API. Leave them inert;
     * clearing the shared hook table would remove other game-owned observers. */
    DiscardPass();
    DiscardColumn();
    bound_rom = NULL;
    bound_size = 0;
    identity_ok = 0;
    initialized = 0;
}
