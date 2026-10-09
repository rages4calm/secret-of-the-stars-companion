/* Title-owned, optional presentation. No ROM, WRAM, SRAM or timing writes. */
#include "foundation_presentation.h"
#include "common_rtl.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include "snes_overlay_draw.h"
#include "foundation_scale2x.h"
#include "foundation_journal.h"
#include "foundation_wide.h"
#include "foundation_wide_actors.h"
#include "foundation_hd_ui.h"
#include "desktop/sdl_compat.h"
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Snes *g_snes;
extern Ppu *g_ppu;
static int battle_info, experimental_wide, enhanced_pixels, hidden;
static uint32_t previous_input;
static unsigned frame_number;
static atomic_uint hotkey_requests;
static int input_watch;
static SDL_Joystick *test_pad;
static int input_test;

/* Host hotkeys remain available when the player's gameplay source is a pad.
 * Watches may run off the main thread: queue requests, never touch guest state. */
#if SNESRECOMP_SDL3
static bool PresentationInput(void *unused, SDL_Event *event) {
#else
static int PresentationInput(void *unused, SDL_Event *event) {
#endif
    (void)unused;
    if (event->type == SDL_KEYDOWN && SNESRECOMP_SDL_EVENT_KEY(*event) == SDLK_h &&
        !SNESRECOMP_SDL_EVENT_REPEAT(*event) &&
        !(SNESRECOMP_SDL_EVENT_MOD(*event) & (KMOD_CTRL | KMOD_ALT | KMOD_GUI)))
        atomic_fetch_or(&hotkey_requests, 1);
    if (event->type == SDL_CONTROLLERBUTTONDOWN &&
        SNESRECOMP_SDL_EVENT_BUTTON(*event) == SDL_CONTROLLER_BUTTON_RIGHTSTICK)
        atomic_fetch_or(&hotkey_requests, 2);
    return true;
}

void FoundationPresentationReset(void) {
    /* Also called after a modal rewind/browser closes. Discard events queued
     * while gameplay was frozen, including the Select+R3 rewind gesture. */
    atomic_store(&hotkey_requests, 0);
    previous_input = 0;
    FoundationWideReset();
}

void FoundationPresentationShutdown(void) {
    if (input_watch) SDL_DelEventWatch(PresentationInput, NULL);
    input_watch = 0;
    if (test_pad) { SDL_JoystickClose(test_pad); test_pad = NULL; }
}

void FoundationPresentationBeforeFrame(void) {
    if (!input_watch) {
        SDL_AddEventWatch(PresentationInput, NULL);
        input_watch = 1;
        const char *test = getenv("SNESRECOMP_FOUNDATION_HUD_INPUT_TEST");
        input_test = test && !strcmp(test, "keyboard") ? 1 : test && !strcmp(test, "pad") ? 2 : 0;
        if (input_test == 2) {
#if SNESRECOMP_SDL3
            SDL_VirtualJoystickDesc desc;
            SDL_INIT_INTERFACE(&desc);
            desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
            desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
            desc.nbuttons = 15;
            desc.name = "foundation HUD test controller";
            SDL_JoystickID id = SDL_AttachVirtualJoystick(&desc);
            test_pad = id ? SDL_OpenJoystick(id) : NULL;
#else
            int id = SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,
                                              SDL_CONTROLLER_AXIS_MAX, 15, 0);
            test_pad = id >= 0 ? SDL_JoystickOpen(id) : NULL;
#endif
            fprintf(stderr, "[foundation_hud_input] virtual pad %s\n", test_pad ? "attached" : "FAILED");
        }
    }
    /* Finite opt-in input fixtures, removed from ordinary player launches.
     * They use SDL events/devices rather than poking guest input or HUD state. */
    if (input_test == 1 && (frame_number == 30 || frame_number == 60 ||
                           frame_number == 90 || (frame_number > 30 && frame_number < 60))) {
        SDL_Event event = {0};
        event.type = frame_number == 60 ? SDL_KEYUP : SDL_KEYDOWN;
#if SNESRECOMP_SDL3
        event.key.key = SDLK_h;
        event.key.repeat = frame_number > 30 && frame_number < 60;
#else
        event.key.keysym.sym = SDLK_h;
        event.key.repeat = frame_number > 30 && frame_number < 60;
#endif
        SDL_PushEvent(&event);
    }
    if (test_pad && (frame_number == 30 || frame_number == 60 || frame_number == 90 || frame_number == 120)) {
        bool down = frame_number == 30 || frame_number == 90;
#if SNESRECOMP_SDL3
        SDL_SetJoystickVirtualButton(test_pad, SDL_GAMEPAD_BUTTON_RIGHT_STICK, down);
#else
        SDL_JoystickSetVirtualButton(test_pad, SDL_CONTROLLER_BUTTON_RIGHTSTICK, down);
#endif
        SDL_JoystickUpdate();
    }
}

void FoundationPresentationInit(void) {
    FoundationHdUiInit();
    FILE *file = fopen("foundation.ini", "r");
    char line[128], key[64]; int value;
    if (file) {
        while (fgets(line, sizeof(line), file)) {
            if (sscanf(line, " %63[^=]=%d", key, &value) != 2) continue;
            size_t len = strlen(key);
            while (len && (key[len-1] == ' ' || key[len-1] == '\t')) key[--len] = 0;
            if (!strcmp(key, "BattleInfo")) battle_info = value == 1;
            if (!strcmp(key, "EnhancedPixels")) enhanced_pixels = value == 1;
            if (!strcmp(key, "ExperimentalFieldWide")) experimental_wide = value == 1;
            if (!strcmp(key, "ExperimentalFieldActors")) FoundationWideActorsSetEnabled(value == 1);
        }
        fclose(file);
    }
    const char *env = getenv("SNESRECOMP_FOUNDATION_BATTLE_INFO");
    if (env) battle_info = !strcmp(env, "1");
    env = getenv("SNESRECOMP_FOUNDATION_WIDE");
    if (env) experimental_wide = !strcmp(env, "1");
    env = getenv("SNESRECOMP_FOUNDATION_ENHANCED_PIXELS");
    if (env) enhanced_pixels = !strcmp(env, "1");
    fprintf(stderr, "[foundation] presentation: battle_info=%d enhanced_pixels=%d experimental_field_wide=%d\n",
            battle_info, enhanced_pixels, experimental_wide);
}

int FoundationPresentationScale(void) { return FoundationHdUiEnabled() ? 4 : enhanced_pixels ? 2 : 1; }

void FoundationPresentationAfterFrame(const SnesDesktopHostFrameStats *stats) {
    frame_number = stats->frame;
    uint32_t input = g_snes->input1_currentState;
    unsigned request = atomic_exchange(&hotkey_requests, 0);
    int toggle = (request & 1) || ((request & 2) && !(input & SNES_PAD_SELECT)) ||
                 ((input & SNES_PAD_X) && !(previous_input & SNES_PAD_X));
    if (battle_info && g_ram[0x20] == 5 && toggle) {
        hidden = !hidden;
        fprintf(stderr, "[foundation] frame %u battle info %s\n", frame_number, hidden ? "hidden" : "shown");
    }
    previous_input = input;
}

void FoundationPresentationPrepare(int drawable_w, int drawable_h, int *w, int *h) {
    (void)drawable_w; (void)drawable_h;
    *w = FoundationWideWidth(experimental_wide); *h = 224;
    if (g_ppu) PpuSetWidescreenLayerMask(g_ppu, 3);
}

int FoundationPresentationDraw(uint8_t *dst, size_t pitch, const uint8_t *field,
                               int w, int h, double alpha) {
    (void)alpha;
    uint8_t *present_dst = dst;
    size_t present_pitch = pitch;
    static uint32_t logical[800 * 240];
    static uint32_t intermediate[800 * 480];
    int hd = FoundationHdUiEnabled();
    if (enhanced_pixels || hd) { dst = (uint8_t *)logical; pitch = w * 4; }
    for (int y = 0; y < h; ++y)
        memcpy(dst + y * pitch, field + y * w * 4, w * 4);
    if (battle_info && !hidden && g_ram[0x20] == 5) {
        int count = 0;
        for (int i = 0; i < 4; ++i) if (!(g_ram[0x6100 + i * 0x1c] & 0x80)) ++count;
        if (count) {
            uint32_t *pixels = (uint32_t *)dst;
            int stride = (int)(pitch / 4), x = (w - 240) / 2;
            snes_ovl_fill_rect(pixels, stride, h, x, 6, 240, 18 + count * 12, 0xff080e1c);
            snes_ovl_stroke_rect(pixels, stride, h, x, 6, 240, 18 + count * 12, 0xff809bc8);
            snes_ovl_draw_text(pixels, stride, h, x + 6, 10, "ENEMY HP H / CLICK R-STICK: HIDE", 0xffffdf78, 1);
            int row = 0;
            for (int i = 0; i < 4; ++i) {
                unsigned offset = 0x6100 + i * 0x1c, id = g_ram[offset];
                if (id & 0x80) continue;
                unsigned hp = g_ram[offset+1] | g_ram[offset+2] << 8;
                unsigned max = g_ram[offset+3] | g_ram[offset+4] << 8;
                char text[40];
                snprintf(text, sizeof(text), "#%02X  %5u / %-5u", id, hp, max);
                snes_ovl_draw_text(pixels, stride, h, x + 6, 23 + row++ * 12, text, 0xfff0f3fa, 1);
            }
        }
    }
    FoundationJournalDraw(dst, pitch, w, h);
    if (enhanced_pixels) {
        uint8_t *scaled = hd ? (uint8_t *)intermediate : present_dst;
        size_t scaled_pitch = hd ? w * 8 : present_pitch;
        FoundationScale2x(logical, w, h, scaled, scaled_pitch);
        if (w == 400) {
            /* Keep even the edge decisions of the original enhanced viewport
             * identical. New neighbors must not change its first/last column. */
            static uint32_t center[256 * 240];
            for (int y = 0; y < h; ++y)
                memcpy(center + y * 256, logical + y * w + 72, 256 * 4);
            FoundationScale2x(center, 256, h, scaled + 144 * 4, scaled_pitch);
        }
    }
    if (hd) {
        const uint32_t *source = enhanced_pixels ? intermediate : logical;
        int factor = enhanced_pixels ? 2 : 4;
        int source_w = enhanced_pixels ? w * 2 : w;
        int source_h = enhanced_pixels ? h * 2 : h;
        for (int y = 0; y < source_h; ++y) for (int dy = 0; dy < factor; ++dy) {
            uint32_t *row = (uint32_t *)(present_dst + (y * factor + dy) * present_pitch);
            for (int x = 0; x < source_w; ++x) for (int dx = 0; dx < factor; ++dx)
                row[x * factor + dx] = source[y * source_w + x];
        }
        FoundationHdUiDraw(present_dst, present_pitch, logical, w, h);
    }
    dst = present_dst; pitch = present_pitch;
    int output_w = w * FoundationPresentationScale(), output_h = h * FoundationPresentationScale();
    /* Opt-in proof capture of the actual composed host surface. */
    const char *path = getenv("SNESRECOMP_FOUNDATION_PRESENT_CAPTURE");
    const char *at = getenv("SNESRECOMP_FOUNDATION_CAPTURE_AT");
    static unsigned captured;
    if (path && at && frame_number == (unsigned)strtoul(at, NULL, 10) && captured != frame_number) {
        FILE *file = fopen(path, "wb");
        if (file) {
            for (int y = 0; y < output_h; ++y) fwrite(dst + y * pitch, 4, output_w, file);
            fclose(file);
            fprintf(stderr, "[foundation] composed capture %dx%d at %u\n", output_w, output_h, frame_number);
        }
        captured = frame_number;
    }
    /* Finite diagnostic snapshots of the composed surface; state_dump's
     * framebuffer intentionally crops the authentic 256-column center. */
    const char *sequence = getenv("SNESRECOMP_FOUNDATION_CAPTURE_SEQUENCE");
    const char *directory = getenv("SNESRECOMP_FOUNDATION_CAPTURE_DIR");
    static unsigned sequence_captured;
    if (sequence && directory && frame_number != sequence_captured) {
        for (const char *p = sequence; *p;) {
            char *end;
            unsigned wanted = (unsigned)strtoul(p, &end, 10);
            if (end == p) break;
            if (wanted == frame_number) {
                char filename[1024];
                snprintf(filename, sizeof(filename), "%s/frame-%u-%dx%d.bgrx", directory,
                         frame_number, output_w, output_h);
                FILE *file = fopen(filename, "wb");
                if (file) {
                    for (int y = 0; y < output_h; ++y) fwrite(dst + y * pitch, 4, output_w, file);
                    fclose(file);
                }
                sequence_captured = frame_number;
                break;
            }
            p = *end == ',' ? end + 1 : end;
            if (!*p || p == end) break;
        }
    }
    return 1;
}
