/* Opt-in local fixture telemetry. Never writes guest memory or supplies input. */
#include "foundation_diagnostics.h"
#include "common_rtl.h"
#include "beam_frame_driver.h"
#include "cpu_state.h"
#include "snes/interp_bridge.h"
#include "snes/interp816.h"
#include "snes/apu.h"
#include "snes/dsp.h"
#include "snes/spc.h"
#include "snes/ppu.h"
#include <stdio.h>
#include <stdlib.h>
extern Snes *g_snes;

/* This observer grants no CPU work and does not consume scheduler flags.
 * The CPU half is bounded by BeginFrame/Frame; raster DMA outside that half
 * is not mislabeled as interpreted instruction time. Exact interpreted
 * master-clock totals are not exposed, so only the total master delta is used. */
static FILE *cpu_trace;
static int cpu_initialized, cpu_began;
static uint64_t cpu_before, master_before, insns_before, interp_before, resume_before;
static uint64_t wait_iterations, wait_first_master, wait_first_cpu;
static int wait_hook;

static void ObserveNmiWait(CpuState *cpu, uint32_t pc) {
    (void)pc;
    /* Clean-USA 008414 is LDA $0000 / BPL back. The original NMI sets bit
     * seven; only a clear flag under the original scheduler register context
     * is an actual wait. Direct WRAM observation has no bus side effect. */
    if (!cpu_began || !cpu->m_flag || cpu->DB || cpu->D || (g_ram[0] & 0x80)) return;
    if (!wait_iterations) {
        wait_first_master = cpu->master_cycles - master_before;
        wait_first_cpu = cpu->cycles - cpu_before;
    }
    ++wait_iterations;
}

void FoundationDiagnosticsBeginFrame(void) {
    if (!cpu_initialized) {
        const char *path = getenv("SNESRECOMP_FOUNDATION_CPU_TRACE");
        cpu_initialized = 1;
        if (path && *path) cpu_trace = fopen(path, "w");
        if (path && *path && !cpu_trace)
            fprintf(stderr, "[foundation_cpu] cannot open diagnostic trace\n");
        if (cpu_trace) {
            wait_hook = interp_bridge_add_pre_opcode_hook(0x008414, ObserveNmiWait);
            fprintf(stderr, "[foundation_cpu] read-only NMI wait observer %s\n", wait_hook ? "registered" : "FAILED");
        }
        if (cpu_trace) fprintf(cpu_trace,
            "frame,valid,input,mode,bg1_scroll_x,bg1_scroll_y,resume_pc,wai,"
            "cpu_cycles,master_cycles,interp_cpu_cycles,interp_insns,"
            "resume_events,resume_evicted,deadline_events,deadline_unwind_events,"
            "quiescent_events,stable_poll_events,wai_events,irq_events,step_cap_events,"
            "other_events,last_deadline_pc,last_step_cap_pc,"
            "nmi_wait_hook,nmi_wait_iterations,pre_wait_master_cycles,pre_wait_cpu_cycles\n");
    }
    if (!cpu_trace) return;
    cpu_before = g_cpu.cycles;
    master_before = g_cpu.master_cycles;
    insns_before = interp816_insns_total();
    interp_before = interp816_cycles_total();
    resume_before = interp_bridge_resume_total();
    wait_iterations = wait_first_master = wait_first_cpu = 0;
    cpu_began = 1;
}

static void CpuBudgetFrame(void) {
    if (!cpu_trace || !cpu_began || !g_snes) return;
    const uint64_t insns = interp816_insns_total();
    const uint64_t interpreted = interp816_cycles_total();
    const uint64_t resume_end = interp_bridge_resume_total();
    const uint64_t capacity = (uint64_t)interp_bridge_resume_capacity();
    uint64_t start = resume_before, evicted = 0, observed = 0;
    uint64_t causes[INTERP_RESUME_SITE_COUNT] = {0};
    uint32_t last_deadline = 0, last_step_cap = 0, pc = 0, wai = 0;
    const int valid = g_cpu.cycles >= cpu_before && g_cpu.master_cycles >= master_before &&
                      insns >= insns_before && interpreted >= interp_before &&
                      resume_end >= resume_before;
    if (resume_end > capacity && start < resume_end - capacity) {
        evicted = resume_end - capacity - start;
        start = resume_end - capacity;
    }
    for (uint64_t seq = start; seq < resume_end; ++seq) {
        InterpResumeEvent event;
        if (!interp_bridge_resume_get(seq, &event)) { ++evicted; continue; }
        ++observed;
        if (event.site < INTERP_RESUME_SITE_COUNT) ++causes[event.site];
        if (event.site == INTERP_RESUME_SITE_DEADLINE ||
            event.site == INTERP_RESUME_SITE_DEADLINE_UNWIND ||
            event.site == INTERP_RESUME_SITE_D9_DEADLINE) last_deadline = event.new_pc24;
        if (event.site == INTERP_RESUME_SITE_STEP_CAP) last_step_cap = event.new_pc24;
    }
    const uint64_t deadlines = causes[INTERP_RESUME_SITE_DEADLINE] + causes[INTERP_RESUME_SITE_D9_DEADLINE];
    const uint64_t irq = causes[INTERP_RESUME_SITE_IRQ_PENDING] + causes[INTERP_RESUME_SITE_D9_IRQ];
    const uint64_t classified = deadlines + causes[INTERP_RESUME_SITE_DEADLINE_UNWIND] +
        causes[INTERP_RESUME_SITE_QUIESCENT] + causes[INTERP_RESUME_SITE_STABLE_POLL] +
        causes[INTERP_RESUME_SITE_WAI] + irq + causes[INTERP_RESUME_SITE_STEP_CAP];
    snes_beam_frame_driver_get_position(&pc, &wai);
    fprintf(cpu_trace, "%d,%d,%u,%u,%u,%u,%u,%u,",
        snes_frame_counter, valid, g_snes->input1_currentState, g_ram[0x20],
        g_snes->ppu->hScroll[0], g_snes->ppu->vScroll[0], pc, wai);
    fprintf(cpu_trace, "%llu,%llu,%llu,%llu,%llu,%llu,",
        (unsigned long long)(valid ? g_cpu.cycles - cpu_before : 0),
        (unsigned long long)(valid ? g_cpu.master_cycles - master_before : 0),
        (unsigned long long)(valid ? interpreted - interp_before : 0),
        (unsigned long long)(valid ? insns - insns_before : 0),
        (unsigned long long)observed, (unsigned long long)evicted);
    fprintf(cpu_trace, "%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%u,%u,",
        (unsigned long long)deadlines,
        (unsigned long long)causes[INTERP_RESUME_SITE_DEADLINE_UNWIND],
        (unsigned long long)causes[INTERP_RESUME_SITE_QUIESCENT],
        (unsigned long long)causes[INTERP_RESUME_SITE_STABLE_POLL],
        (unsigned long long)causes[INTERP_RESUME_SITE_WAI],
        (unsigned long long)irq, (unsigned long long)causes[INTERP_RESUME_SITE_STEP_CAP],
        (unsigned long long)(observed - classified), last_deadline, last_step_cap);
    fprintf(cpu_trace, "%d,%llu,%llu,%llu\n", wait_hook,
        (unsigned long long)wait_iterations, (unsigned long long)wait_first_master,
        (unsigned long long)wait_first_cpu);
    fflush(cpu_trace);
    cpu_began = 0;
}

void FoundationDiagnosticsFrame(void) {
    CpuBudgetFrame();
    static int initialized;
    static FILE *trace;
    if (!initialized) {
        const char *path = getenv("SNESRECOMP_FOUNDATION_TRACE");
        initialized = 1;
        if (path && *path) trace = fopen(path, "w");
        if (trace) fprintf(trace, "frame,mode,spc_pc,dsp_flg,mute,reset,volume_l,volume_r,gain0,apu_clock,enemy0,enemy0_hp,enemy0_max,enemy1,enemy1_hp,enemy2,enemy2_hp,enemy3,enemy3_hp,input,brightness,forced_blank,bgmode,ram_02e1,ram_02e3,bg1_scroll_x,bg1_scroll_y\n");
    }
    if (!trace || !g_snes) return;
    RtlApuLock();
    Apu *apu = g_snes->apu;
    Dsp *dsp = apu->dsp;
    fprintf(trace, "%d,%u,%u,%u,%u,%u,%d,%d,%u,%llu,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",
        snes_frame_counter, g_ram[0x20], apu->spc->pc, dsp->ram[0x6c],
        dsp->mute, dsp->reset, dsp->masterVolumeL, dsp->masterVolumeR,
        dsp->channel[0].gain, (unsigned long long)apu->portClock,
        g_ram[0x6100], g_ram[0x6101] | g_ram[0x6102] << 8,
        g_ram[0x6103] | g_ram[0x6104] << 8,
        g_ram[0x611c], g_ram[0x611d] | g_ram[0x611e] << 8,
        g_ram[0x6138], g_ram[0x6139] | g_ram[0x613a] << 8,
        g_ram[0x6154], g_ram[0x6155] | g_ram[0x6156] << 8,
        g_snes->input1_currentState, PPU_brightness(g_snes->ppu),
        !!PPU_forcedBlank(g_snes->ppu), PPU_mode(g_snes->ppu),
        g_ram[0x02e1] | g_ram[0x02e2] << 8, g_ram[0x02e3] | g_ram[0x02e4] << 8,
        g_snes->ppu->hScroll[0], g_snes->ppu->vScroll[0]);
    RtlApuUnlock();
    fflush(trace);
}

/* Finite fixture video tap, before optional host presentation. Disabled in
 * ordinary launch; this file contains private ROM-derived pixels. */
void FoundationDiagnosticsRendered(const uint8_t *field, unsigned frame) {
    (void)frame;
    static int initialized;
    static FILE *video;
    if (!initialized) {
        const char *path = getenv("SNESRECOMP_FOUNDATION_VIDEO_RAW");
        initialized = 1;
        if (path && *path) video = fopen(path, "wb");
    }
    if (!video || !field || !g_snes || g_snes->ppu->renderPitch != 256 * 4) return;
    fwrite(field, 4, 256 * 224, video);
}
