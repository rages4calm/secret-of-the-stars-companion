/* Renderer-owned side columns for original standard field resources.
 * The beam driver remains the sole raster/HDMA owner. Its observer receives
 * each already drawn original line; only a private PPU copy is drawn again. */
#include "foundation_wide.h"
#include "foundation_field.h"
#include "foundation_hd_ui.h"
#include "foundation_wide_actors.h"
#include "foundation_battle_wide.h"
#include "common_rtl.h"
#include "beam_frame_driver.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include "snes/cart.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Ppu *g_ppu;
extern Snes *g_snes;
static int active;
static Ppu picture;
static uint16_t shadow[0x8000];
static uint32_t scratch[400 * 224];
static uint32_t actor_baseline[144];
static unsigned accepted, rejected, tile_mismatches, pixel_mismatches;
static unsigned stale_margin_words;
static unsigned title_lines, battle_lines, title_scroll_min, title_scroll_max;
static FILE *trace;
static int trace_checked;

static int signed_word(unsigned offset) {
    return (int16_t)(g_ram[offset] | g_ram[offset + 1] << 8);
}
static int floor8(int x) { return x >= 0 ? x / 8 : -((-x + 7) / 8); }
static unsigned slot(int x, int y, unsigned base) {
    unsigned tx = (unsigned)floor8(x) & 63, ty = (unsigned)floor8(y) & 31;
    return base + (tx & 31) + ty * 32 + (tx >= 32 ? 1024 : 0);
}

void FoundationWideReset(void) {
    active = 0;
    FoundationFieldReset();
    FoundationWideActorsReset();
    FoundationBattleWideReset();
}

int FoundationWideWidth(int requested) {
    /* Keep one canvas through fades, menus and transitions. A resource that
     * cannot expand still receives authentic centered scanout and blank sides. */
    active = requested && g_ppu;
    return active ? 400 : 256;
}

static int title_eligible(const Ppu *ppu) {
    return ppu && g_snes && g_snes->cart &&
        FoundationFieldBind(g_rom, g_snes->cart->romImageSize) &&
        g_ram[0x20] == 0 && (g_ram[0x40e] | g_ram[0x40f] << 8) == 13 && !g_ram[0x105c] &&
        ppu->inidisp == 15 && ppu->bgmode == 1 && !ppu->mosaic && !ppu->setini &&
        ppu->bgXsc[0] == 0x49 && ppu->bgXsc[1] == 0x59 && ppu->bgXsc[2] == 0x51 &&
        ppu->bgTileAdr == 0x0466 && ppu->screenEnabled[0] == 0x13 && !ppu->screenEnabled[1] &&
        !ppu->windowsel && !ppu->cgadsub && !ppu->cgwsel &&
        ppu->hScroll[0] == 256 && !ppu->vScroll[0] && !ppu->vScroll[1];
}

static void clone_line(const Ppu *ppu, unsigned mask) {
    memcpy(&picture, ppu, sizeof(picture));
    if (!(picture.mosaic & 0xf0)) picture.mosaic = 0;
    picture.renderBuffer = (uint8_t *)scratch;
    picture.renderPitch = 400 * 4;
    picture.renderVram = shadow;
    memset(picture.overlayRenderBuffer, 0, sizeof(picture.overlayRenderBuffer));
    picture.mode7Hd.pixels = NULL;
    picture.extraObjects = NULL; picture.extraObjectCount = 0;
    picture.widescreenLineEnhancer = NULL;
    PpuSetExtraSideSpace(&picture, 72, 72, 0);
    PpuSetWidescreenLayerMask(&picture, mask);
    uint8_t no_hints[16] = {0};
    PpuWsSetOamLeftHints(&picture, no_hints);
    PpuWsSetOamRightHints(&picture, no_hints);
    picture.wsOamMotionGraceOn = 0;
}

static int accept_line(const Ppu *ppu, unsigned line) {
    ppu_runLine(&picture, (int)line);
    const uint8_t *row = ppu->renderBuffer + (line - 1) * ppu->renderPitch;
    const uint8_t *candidate = (uint8_t *)&scratch[(line - 1) * 400];
    if (memcmp(candidate + 72 * 4, row + 72 * 4, 256 * 4)) {
        ++pixel_mismatches; ++rejected; return 0;
    }
    return 1;
}

static void publish_line(const Ppu *ppu, unsigned line) {
    uint8_t *row = ppu->renderBuffer + (line - 1) * ppu->renderPitch;
    const uint8_t *candidate = (uint8_t *)&scratch[(line - 1) * 400];
    memcpy(row, candidate, 72 * 4);
    memcpy(row + 328 * 4, candidate + 328 * 4, 72 * 4);
    ++accepted;
}

static void clear_margins(Ppu *ppu) {
    for (unsigned y = 0; y < 224; ++y) {
        uint8_t *row = ppu->renderBuffer + y * ppu->renderPitch;
        memset(row, 0, 72 * 4);
        memset(row + 328 * 4, 0, 72 * 4);
    }
}

static void draw_line(const Ppu *ppu, unsigned line, void *unused) {
    (void)unused;
    FoundationHdUiObserve(ppu, line, NULL);
    if (PPU_forcedBlank(ppu) ||
        (ppu->mosaic & 0xf0) || ppu->setini || !(ppu->renderFlags & kPpuRenderFlags_NewRenderer)) {
        ++rejected; return;
    }
    memcpy(shadow, ppu->vram, sizeof(shadow));
    if (title_eligible(ppu) || FoundationBattleWideEligible(ppu)) {
        int title = title_eligible(ppu);
        clone_line(ppu, 2);
        if (!title && !FoundationBattleWidePrepareLine(ppu, line, &picture, shadow)) {
            ++rejected; return;
        }
        if (!accept_line(ppu, line)) return;
        /* The title's original 512px panorama and explicitly composed battle
         * scenery extend BG2. Logos, enemies, commands and OBJ remain centered. */
        picture.screenEnabled[0] &= ~16u; picture.screenEnabled[1] &= ~16u;
        ppu_runLine(&picture, (int)line);
        publish_line(ppu, line);
        if (title) {
            ++title_lines;
            if (ppu->hScroll[1] < title_scroll_min) title_scroll_min = ppu->hScroll[1];
            if (ppu->hScroll[1] > title_scroll_max) title_scroll_max = ppu->hScroll[1];
        } else ++battle_lines;
        return;
    }
    if (!FoundationFieldSceneEligible(ppu)) { ++rejected; return; }
    /* Current VRAM supplies every character, including animated tiles. Only
     * private BG1/BG2 tilemap words are reconstructed from the full map. */
    for (int layer = 0; layer < 2; ++layer) {
        if (!FoundationFieldLayerActive(layer)) {
            /* The inactive overworld secondary producer leaves an authentic
             * uniform plane. Retain it; never decode its unused map pointer. */
            unsigned base = layer ? 0x5800 : 0x4800;
            for (unsigned i = 1; i < 2048; ++i)
                if (ppu->vram[base + i] != ppu->vram[base]) { ++rejected; return; }
            continue;
        }
        int cx = signed_word(0x2ad + layer * 4);
        int cy = signed_word(0x2af + layer * 4);
        /* Preparation precedes replay of the field's scroll journal. Unwrap
         * the actual line's ten-bit scroll around the signed world camera,
         * so an in-flight one-pixel move never collapses the viewport. */
        cx += ((ppu->hScroll[layer] - (cx & 1023) + 512) & 1023) - 512;
        cy += ((ppu->vScroll[layer] - (cy & 1023) + 512) & 1023) - 512;
        /* Preserve all word/pixel gates; only the strict completed parked
         * packet may supply its authenticated original full primary raster. */
        if (layer == 0) {
            int full_x,full_y;
            if (FoundationWideActorsPeriodicRaster(ppu,&full_x,&full_y)) {
                cx=full_x; cy=full_y;
            }
        }
        int wy = cy + (int)line;
        unsigned base = layer ? 0x5800 : 0x4800;
        int first = floor8(cx - 72), last = floor8(cx + 327);
        int center_first = floor8(cx), center_last = floor8(cx + 255);
        for (int tx = first; tx <= last; ++tx) {
            uint16_t word;
            if (!FoundationFieldResolve(layer, tx * 8, wy, &word)) { ++rejected; return; }
            unsigned at = slot(tx * 8, wy, base);
            if (tx >= center_first && tx <= center_last) {
                if (word != ppu->vram[at]) { ++tile_mismatches; ++rejected; return; }
            } else if (word != ppu->vram[at]) ++stale_margin_words;
            shadow[at] = word;
        }
    }
    clone_line(ppu, 3);
    if (!accept_line(ppu, line)) return;
    uint8_t *candidate = (uint8_t *)&scratch[(line - 1) * 400];
    /* The terrain-only picture remains the fallback. Only exact packet-bound
     * regular actor metadata can request an additional private line pass. */
    picture.screenEnabled[0] &= ~16u;
    picture.screenEnabled[1] &= ~16u;
    ppu_runLine(&picture, (int)line);
    if (FoundationWideActorsPrepareLine(ppu, line, &picture)) {
        memcpy(actor_baseline, candidate, 72 * 4);
        memcpy(actor_baseline + 72, candidate + 328 * 4, 72 * 4);
        ppu_runLine(&picture, (int)line);
        unsigned changed = 0;
        for (unsigned x = 0; x < 72; ++x) {
            changed += ((uint32_t *)candidate)[x] != actor_baseline[x];
            changed += ((uint32_t *)candidate)[328 + x] != actor_baseline[72 + x];
        }
        FoundationWideActorsDrawResult(changed);
    }
    publish_line(ppu, line);
}

void FoundationWideDrawFrame(void) {
    FoundationHdUiBeginFrame();
    FoundationWideActorsBeginDraw();
    if (!active || !g_ppu || g_ppu->extraLeftRight != 72 || g_ppu->renderPitch != 1600) {
        if (FoundationHdUiEnabled())
            snes_beam_frame_driver_draw_ppu_frame_observed(FoundationHdUiObserve, NULL);
        else snes_beam_frame_driver_draw_ppu_frame();
        FoundationWideActorsEndDraw();
        return;
    }
    accepted = rejected = tile_mismatches = pixel_mismatches = stale_margin_words = 0;
    title_lines = battle_lines = title_scroll_max = 0; title_scroll_min = 1024;
    /* Keep the guest raster's viewport authentic, within the host's centering
     * budget. This also preserves original sprite evaluation/overflow flags. */
    PpuSetExtraSideSpace(g_ppu, 0, 0, 0);
    clear_margins(g_ppu);
    snes_beam_frame_driver_draw_ppu_frame_observed(draw_line, NULL);
    /* Refuse the whole side picture if any line violates the checked contract;
     * never publish a mixture of stale ring columns and reconstructed terrain. */
    if (rejected) clear_margins(g_ppu);
    FoundationWideActorsEndDraw();
    if (!trace_checked) {
        const char *path = getenv("SNESRECOMP_FOUNDATION_FIELD_TRACE");
        if (path) trace = fopen(path, "w");
        if (trace) fputs("frame,accepted_lines,rejected_lines,tile_mismatches,pixel_mismatches,stale_margin_words,camera_x,camera_y,scene,kind,title_lines,battle_lines,title_bg2_min_hscroll,title_bg2_max_hscroll\n", trace);
        trace_checked = 1;
    }
    if (trace) {
        int kind = title_eligible(g_ppu) ? 2 : FoundationBattleWideEligible(g_ppu) ? 3 : FoundationFieldSceneEligible(g_ppu) ? 1 : 0;
        fprintf(trace, "%u,%u,%u,%u,%u,%u,%d,%d,%u,%d,%u,%u,%u,%u\n", snes_frame_counter, accepted,
                rejected, tile_mismatches, pixel_mismatches, stale_margin_words,
                signed_word(0x2ad), signed_word(0x2af), (unsigned)(g_ram[0x40e] | g_ram[0x40f] << 8), kind,
                title_lines, battle_lines, title_scroll_min, title_scroll_max);
        fflush(trace);
    }
}
