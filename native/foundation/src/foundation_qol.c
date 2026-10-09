/* Optional native rules at the clean-USA completed-battle reward handoff and
 * ordinary player-walk operands. No global RAM-gain watcher, coordinate jump,
 * scheduler overclock or changed NPC/cutscene/music clock. */
#include "foundation_qol.h"
#include "foundation_hotkeys.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "snes/interp_bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned xp_percent = 100, gold_percent = 100, movement_percent = 200;
static int initialized, trace, movement_ready;

static unsigned Word(unsigned at) {
    return g_ram[at] | (unsigned)g_ram[at + 1] << 8;
}
static int OriginalBytes(unsigned pc, const unsigned char *bytes, size_t count) {
    const unsigned char *rom = RomPtr(pc);
    return rom && !memcmp(rom, bytes, count);
}

uint16_t FoundationQolScaleReward(uint16_t amount, unsigned percent) {
    /* Original per-battle totals are 16-bit; original XP/wallet consumers
     * retain their own 24-bit 9,999,999 cap. Never wrap before that consumer. */
    if (percent < 100 || percent > 1000) percent = 100;
    uint32_t scaled = (uint32_t)amount * percent / 100;
    return scaled > 65535 ? 65535 : (uint16_t)scaled;
}

static void BeforeVictory(CpuState *cpu, uint32_t pc) {
    /* Original enemy reads accumulate first. Scale the completed battle total
     * once at the original handoff to party XP/wallet writers, so e.g. two
     * 2-XP enemies at 125% award floor(4*1.25)=5 instead of floor(2*1.25)*2.
     * The interpreter executes this SEP before any checkpoint can re-enter
     * its preceding policy; no unsaved one-shot/reward latch is required. */
    int qualified = g_ram[0x20] == 5 && cpu->D == 0x0d00 && !cpu->DB &&
        cpu->m_flag && cpu->x_flag && cpu->S >= 0x1d00 && cpu->S < 0x1dba;
    unsigned original_xp = Word(cpu->D+0x21), original_gold = Word(cpu->D+0x1f);
    unsigned scaled_xp = qualified ? FoundationQolScaleReward(original_xp,xp_percent) : original_xp;
    unsigned scaled_gold = qualified ? FoundationQolScaleReward(original_gold,gold_percent) : original_gold;
    if (qualified && xp_percent != 100) cpu_write16(cpu,0,cpu->D+0x21,(uint16_t)scaled_xp);
    if (qualified && gold_percent != 100) cpu_write16(cpu,0,cpu->D+0x1f,(uint16_t)scaled_gold);
    if (trace) fprintf(stderr,
        "[foundation_qol_victory] frame=%d pc=%06X D=%04X DB=%02X M=%u Xf=%u mode=%u original_xp=%u scaled_xp=%u xp_percent=%u original_gold=%u scaled_gold=%u gold_percent=%u qualified=%d S=%04X\n",
        snes_frame_counter,pc,cpu->D,cpu->DB,cpu->m_flag,cpu->x_flag,g_ram[0x20],
        original_xp,scaled_xp,xp_percent,original_gold,scaled_gold,gold_percent,qualified,cpu->S);
}

static void BeforeWalkOperand(CpuState *cpu, uint32_t pc) {
    int secondary = pc == 0x01b139 || pc == 0x01b141;
    int axis_y = pc == 0x01b0af || pc == 0x01b141;
    int held = FoundationHotkeysMovementHeld();
    if (!trace && !secondary && (!held || movement_percent == 100)) return;
    unsigned primary_at = 0x2ad + (axis_y ? 2 : 0);
    unsigned secondary_at = 0x2b1 + (axis_y ? 2 : 0);
    int pending = (int16_t)(Word(primary_at)-Word(secondary_at));
    if (!trace && secondary && pending == (int16_t)cpu->A) return;
    /* Ordinary one-pixel primary motion only. 01:9142 performs the original
     * next-tile collision/event decision; 01:B044 completes a step only at
     * a 16-pixel boundary. Clamp the last increment to that exact boundary.
     * Keep the matched Mode80 secondary camera and refuse currents, special motion,
     * scripted locks and every unsupported movement family. */
    unsigned direction = g_ram[0x408] & 3;
    unsigned vector = axis_y ? 0x45c : 0x459;
    int velocity = (int16_t)Word(vector + 1);
    int qualified = movement_ready && g_ram[0x20] == 1 && cpu->D == 0x0b00 &&
        cpu->DB == 1 && !cpu->m_flag && cpu->x_flag &&
        (g_ram[0x408] & 0xfc) == 0x80 && !g_ram[0x409] &&
        !(g_ram[0x543] & 0x80) && !g_ram[0x527] &&
        g_ram[0x452] == 0x80 && !Word(0x471) && !Word(0x473) &&
        !memcmp(g_ram+0x459,g_ram+0x45f,6) &&
        !g_ram[vector] && (velocity == 1 || velocity == -1) &&
        axis_y == (direction >= 2) &&
        velocity == ((direction & 1) ? -1 : 1) && cpu->A == (uint16_t)velocity &&
        Word(0x2ad+(axis_y ? 0 : 2)) == Word(0x2b1+(axis_y ? 0 : 2));
    unsigned step = 1;
    if (!secondary && pending) qualified = 0;
    if (secondary && (pending * velocity < 1 || pending * velocity > 3)) qualified = 0;
    if (qualified && secondary) {
        /* Mode80 begins both layers at the same camera and has identical
         * vectors. Complete exactly the primary's already recorded advance,
         * even if a deadline/checkpoint falls between the two consumers or
         * the button is released there. This lineage lives entirely in WRAM,
         * not an unsaved held-frame or temporary-vector latch. */
        step = (unsigned)(pending * velocity);
        cpu->A = (uint16_t)pending;
    } else if (qualified && held && movement_percent > 100) {
        /* Restored guest frame counter supplies fractional cadence; there is
         * no unsaved host accumulator which remembers a discarded future. */
        uint64_t frame = (unsigned)snes_frame_counter;
        step = (unsigned)(((frame + 1) * movement_percent / 100) -
                          (frame * movement_percent / 100));
        unsigned position = Word((secondary ? 0x2b1 : 0x2ad)+(axis_y ? 2 : 0)) & 15;
        unsigned remaining = velocity > 0 ? 16 - position : position ? position : 16;
        if (step > remaining) step = remaining;
        cpu->A = (uint16_t)(velocity * (int)step);
    }
    if (trace && (qualified || held)) fprintf(stderr,
        "[foundation_qol_walk] frame=%d pc=%06X held=%d qualified=%d percent=%u step=%u direction=%u xy=%u,%u flags=%02X lock=%02X secondary=%02X D=%04X DB=%02X velocity=%d motion=%02X M=%u Xf=%u secondary_vector=%04X,%04X,%04X fraction=%u pause=%u\n",
        snes_frame_counter, pc, held, qualified, movement_percent, step,
        direction, Word(0x2ad), Word(0x2af), g_ram[0x409], g_ram[0x543],
        g_ram[0x452], cpu->D, cpu->DB, velocity, g_ram[0x408],cpu->m_flag,cpu->x_flag,
        Word(0x45f),Word(0x461),Word(0x463),g_ram[vector],g_ram[0x527]);
}

static unsigned Setting(unsigned value, unsigned minimum, unsigned maximum, unsigned fallback) {
    return value >= minimum && value <= maximum ? value : fallback;
}
static unsigned Environment(const char *name, unsigned value, unsigned maximum) {
    const char *text = getenv(name); char *end;
    if (!text || !*text) return value;
    unsigned long parsed = strtoul(text, &end, 10);
    return *end || parsed > maximum || parsed < 100 ? 100 : (unsigned)parsed;
}

void FoundationQolInit(void) {
    if (initialized) return;
    initialized = 1;
    FILE *file = fopen("foundation.ini", "r");
    char line[160], key[80]; unsigned value;
    if (file) {
        while (fgets(line, sizeof(line), file)) {
            if (sscanf(line, " %79[^=]=%u", key, &value) != 2) continue;
            size_t len = strlen(key);
            while (len && (key[len-1] == ' ' || key[len-1] == '\t')) key[--len] = 0;
            if (!strcmp(key, "XpMultiplierPercent")) xp_percent = Setting(value,100,1000,100);
            if (!strcmp(key, "GoldMultiplierPercent")) gold_percent = Setting(value,100,1000,100);
            if (!strcmp(key, "MovementSpeedPercent")) movement_percent = Setting(value,100,300,200);
        }
        fclose(file);
    }
    xp_percent = Environment("SNESRECOMP_FOUNDATION_XP_PERCENT",xp_percent,1000);
    gold_percent = Environment("SNESRECOMP_FOUNDATION_GOLD_PERCENT",gold_percent,1000);
    movement_percent = Environment("SNESRECOMP_FOUNDATION_MOVEMENT_PERCENT",movement_percent,300);
    trace = getenv("SNESRECOMP_FOUNDATION_QOL_TRACE") != NULL;
    static const unsigned char victory_code[] = {0xe2,0x30,0x64,0x10,0xa5,0x10,0x22,0x32,0xff,0x00};
    static const unsigned char x_code[] = {0xad,0x5a,0x04,0x18,0x6d,0x71,0x04};
    static const unsigned char y_code[] = {0xad,0x5d,0x04,0x18,0x6d,0x73,0x04};
    static const unsigned char secondary_x_code[] = {0xa5,0x01,0x18,0x6d,0x71,0x04};
    static const unsigned char secondary_y_code[] = {0xa5,0x04,0x18,0x6d,0x73,0x04};
    int reward_ready = OriginalBytes(0x00ae9b,victory_code,sizeof(victory_code)) &&
        (xp_percent == 100 && gold_percent == 100 && !trace ? 1 :
         interp_bridge_add_pre_opcode_hook(0x00ae9b,BeforeVictory));
    if (!reward_ready) xp_percent = gold_percent = 100;
    movement_ready = OriginalBytes(0x01b073,x_code,sizeof(x_code)) &&
        OriginalBytes(0x01b0ac,y_code,sizeof(y_code)) &&
        OriginalBytes(0x01b137,secondary_x_code,sizeof(secondary_x_code)) &&
        OriginalBytes(0x01b13f,secondary_y_code,sizeof(secondary_y_code)) &&
        interp_bridge_add_pre_opcode_hook(0x01b076,BeforeWalkOperand) &&
        interp_bridge_add_pre_opcode_hook(0x01b0af,BeforeWalkOperand) &&
        interp_bridge_add_pre_opcode_hook(0x01b139,BeforeWalkOperand) &&
        interp_bridge_add_pre_opcode_hook(0x01b141,BeforeWalkOperand);
    fprintf(stderr,"[foundation_qol] xp_percent=%u gold_percent=%u movement_percent=%u reward_hook=%d movement_hook=%d\n",
        xp_percent,gold_percent,movement_percent,reward_ready,movement_ready);
}
