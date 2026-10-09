/* A bounded native gameplay-edit proof, never enabled by the player launcher.
 * The source-derived enemy HP consumer is checked against live registers and
 * the clean-USA instruction bytes. Future AOT promotion must call this rule
 * explicitly; this interpreter seam does not cover arbitrary compiled bodies. */
#include "foundation_rules.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "snes/interp_bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int multiplier = 1;
static int trace;

static void TraceFrameWait(CpuState *cpu, uint32_t pc) {
    uint16_t ret = cpu_read16(cpu, 0, (uint16_t)(cpu->S + 1));
    unsigned bank = cpu_read8(cpu, 0, (uint16_t)(cpu->S + 3));
    fprintf(stderr, "[foundation_wait] frame=%d pc=%06X caller=%02X%04X wait=%u D=%04X DB=%02X M=%u mode=%u\n",
            snes_frame_counter, pc, bank, ret, cpu->m_flag ? cpu->A & 255 : cpu->A, cpu->D, cpu->DB,
            cpu->m_flag, g_ram[0x20]);
}

static void BeforeEnemyHpCompare(CpuState *cpu, uint32_t pc) {
    uint16_t dp = (uint16_t)(cpu->D + 0xd3);
    uint32_t ptr = cpu_read8(cpu, 0, dp) | cpu_read8(cpu, 0, (uint16_t)(dp+1)) << 8 |
                   cpu_read8(cpu, 0, (uint16_t)(dp+2)) << 16;
    unsigned damage = cpu_read16(cpu, cpu->DB, 0x0497);
    int slot = ptr >= 0x7e6100 && ptr <= 0x7e6154 && (ptr - 0x7e6100) % 0x1c == 0;
    int qualified = slot && cpu->Y == 1 && !cpu->m_flag && g_ram[0x20] == 5 &&
        cpu_read8(cpu, 0, 0xdc97) == 0xcd && cpu_read8(cpu, 0, 0xdc98) == 0x97 &&
        cpu_read8(cpu, 0, 0xdc99) == 0x04;
    /* Limit the first rule to the observed 11-HP Red Slime record (ID 1). */
    if (qualified) {
        unsigned offset = ptr - 0x7e0000;
        qualified = g_ram[offset] == 1 && (g_ram[offset+3] | g_ram[offset+4] << 8) == 11;
    }
    unsigned result = damage;
    if (qualified && multiplier == 2) {
        result = damage > 32767 ? 65535 : damage * 2;
        cpu_write16(cpu, cpu->DB, 0x0497, (uint16_t)result);
    }
    if (trace || multiplier != 1)
        fprintf(stderr, "[foundation_rule] frame=%d pc=%06X ptr=%06X Y=%u M=%u hp=%u damage=%u result=%u qualified=%d multiplier=%d\n",
                snes_frame_counter, pc, ptr, cpu->Y, cpu->m_flag, cpu->A, damage, result, qualified, multiplier);
}

void FoundationRulesInit(void) {
    static int initialized;
    if (initialized) return;
    initialized = 1;
    if (getenv("SNESRECOMP_FOUNDATION_WAIT_TRACE")) {
        interp_bridge_add_pre_opcode_hook(0x00ff03, TraceFrameWait);
        interp_bridge_add_pre_opcode_hook(0x02911b, TraceFrameWait);
    }
    const char *value = getenv("SNESRECOMP_FOUNDATION_DAMAGE_PROOF");
    multiplier = value && !strcmp(value, "2") ? 2 : 1;
    trace = value && !strcmp(value, "trace");
    if (multiplier != 1 || trace) {
        if (!interp_bridge_add_pre_opcode_hook(0x00dc97, BeforeEnemyHpCompare)) {
            multiplier = 1;
            fprintf(stderr, "[foundation_rule] registration refused; original damage retained\n");
        }
    }
}
