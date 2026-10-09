/* First-stage current lead, derived only from original guest state.
 * No ROM/guest writes, completion guesses or external seen-event history. */
#include "foundation_journal.h"
#include "foundation_hotkeys.h"
#include "common_rtl.h"
#include "snes/snes.h"
#include "snes_overlay_draw.h"
#include "desktop/sdl_compat.h"
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Snes *g_snes;
static int enabled, visible, has_lead, watch_installed, input_test;
static unsigned frame_number;
static int possession_enabled;
static SDL_Joystick *test_pad;
static FILE *trace;

void FoundationJournalReset(void) {
    visible = has_lead = 0;
}

void FoundationJournalInit(void) {
    possession_enabled = 1;
    char line[128], key[64]; int value;
    FILE *file = fopen("foundation.ini", "r");
    if (file) {
        while (fgets(line, sizeof(line), file)) {
            if (sscanf(line, " %63[^=]=%d", key, &value) != 2) continue;
            size_t len = strlen(key);
            while (len && (key[len-1] == ' ' || key[len-1] == '\t')) key[--len] = 0;
            if (!strcmp(key, "Journal")) enabled = value == 1;
            if (!strcmp(key, "JournalPossession")) possession_enabled = value == 1;
        }
        fclose(file);
    }
    const char *env = getenv("SNESRECOMP_FOUNDATION_JOURNAL");
    if (env) enabled = !strcmp(env, "1");
    env = getenv("SNESRECOMP_FOUNDATION_JOURNAL_INPUT_TEST");
    input_test = env && !strcmp(env, "keyboard") ? 1 : env && !strcmp(env, "pad") ? 2 : 0;
    env = getenv("SNESRECOMP_FOUNDATION_JOURNAL_TRACE");
    if (env && *env) trace = fopen(env, "w");
    env = getenv("SNESRECOMP_FOUNDATION_JOURNAL_POSSESSION");
    if (env) possession_enabled = !strcmp(env, "1");
    if (trace) fprintf(trace, "frame,mode,stage,flags,enabled,visible,has_lead,inventory_groups\n");
    fprintf(stderr, "[foundation] journal enabled=%d; configurable Journal hotkey\n", enabled);
    FoundationJournalReset();
}

void FoundationJournalBeforeFrame(void) {
    if (!watch_installed && (enabled || input_test)) {
        watch_installed = 1;
        if (input_test == 2) {
#if SNESRECOMP_SDL3
            SDL_VirtualJoystickDesc desc;
            SDL_INIT_INTERFACE(&desc);
            desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
            desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
            desc.nbuttons = 15;
            desc.name = "foundation journal test controller";
            SDL_JoystickID id = SDL_AttachVirtualJoystick(&desc);
            test_pad = id ? SDL_OpenJoystick(id) : NULL;
#else
            int id = SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,
                                              SDL_CONTROLLER_AXIS_MAX, 15, 0);
            test_pad = id >= 0 ? SDL_JoystickOpen(id) : NULL;
#endif
            fprintf(stderr, "[foundation_journal_input] virtual pad %s\n", test_pad ? "attached" : "FAILED");
        }
    }
    /* Finite opt-in fixtures inject real SDL input, never quest state. */
    if (input_test == 1 && (frame_number == 30 || frame_number == 60 ||
                           frame_number == 90 || (frame_number > 30 && frame_number < 60))) {
        SDL_Event event = {0};
        event.type = frame_number == 60 ? SDL_KEYUP : SDL_KEYDOWN;
#if SNESRECOMP_SDL3
        event.key.key = SDLK_j;
        event.key.repeat = frame_number > 30 && frame_number < 60;
#else
        event.key.keysym.sym = SDLK_j;
        event.key.repeat = frame_number > 30 && frame_number < 60;
#endif
        SDL_PushEvent(&event);
    }
    if (test_pad && (frame_number == 30 || frame_number == 60 ||
                     frame_number == 90 || frame_number == 120)) {
        bool down = frame_number == 30 || frame_number == 90;
#if SNESRECOMP_SDL3
        SDL_SetJoystickVirtualButton(test_pad, SDL_GAMEPAD_BUTTON_LEFT_STICK, down);
#else
        SDL_JoystickSetVirtualButton(test_pad, SDL_CONTROLLER_BUTTON_LEFTSTICK, down);
#endif
        SDL_JoystickUpdate();
    }
}

void FoundationJournalAfterFrame(const SnesDesktopHostFrameStats *stats) {
    frame_number = stats->frame;
    has_lead = FoundationJournalHasLead(g_ram[0x5372], g_ram[0x5360]);
    int toggle = FoundationHotkeysConsumeJournal();
    if (enabled && g_ram[0x20] == 1 && toggle) {
        visible = !visible;
        fprintf(stderr, "[foundation] frame %u journal %s\n", frame_number, visible ? "shown" : "hidden");
    }
    if (trace) {
        fprintf(trace, "%u,%u,%u,%u,%d,%d,%d,%u\n", frame_number, g_ram[0x20],
                g_ram[0x5372], g_ram[0x5360], enabled, visible, has_lead,
                JournalPossessionGroups(g_ram, 0x20000));
        fflush(trace);
    }
}

void FoundationJournalDraw(uint8_t *dst, size_t pitch, int w, int h) {
    if (!enabled || !visible || g_ram[0x20] != 1 || w < 240 || h < 88) return;
    /* Re-derive even if presentation follows a load before a guest update. */
    int lead = FoundationJournalHasLead(g_ram[0x5372], g_ram[0x5360]);
    uint32_t *pixels = (uint32_t *)dst;
    int stride = (int)(pitch / 4), x = (w - 240) / 2;
    unsigned groups = possession_enabled ? JournalPossessionGroups(g_ram, 0x20000) : 0;
    snes_ovl_fill_rect(pixels, stride, h, x, 6, 240, 75, 0xff080e1c);
    snes_ovl_stroke_rect(pixels, stride, h, x, 6, 240, 75, 0xff809bc8);
    snes_ovl_draw_text(pixels, stride, h, x + 6, 11,
                       groups ? "JOURNAL - HOTKEY: CLOSE" :
                       "JOURNAL - JOURNAL HOTKEY: CLOSE", 0xffffdf78, 1);
    if (groups) {
        snes_ovl_draw_text(pixels, stride, h, x + 6, 29,
                           "STARCREST: HELD NOW", 0xfff0f3fa, 1);
        snes_ovl_draw_text(pixels, stride, h, x + 6, 45,
                           groups == 3 ? "Both inventory groups" : groups == 2 ?
                           "Second inventory group" : "First inventory group", 0xfff0f3fa, 1);
        snes_ovl_draw_text(pixels, stride, h, x + 6, 57,
                           "In your pack now", 0xfff0f3fa, 1);
    } else if (lead) {
        snes_ovl_draw_text(pixels, stride, h, x + 6, 29,
                           "Seek the Crest of Stars", 0xfff0f3fa, 1);
        snes_ovl_draw_text(pixels, stride, h, x + 6, 45,
                           "David: somewhere in", 0xfff0f3fa, 1);
        snes_ovl_draw_text(pixels, stride, h, x + 6, 57,
                           "the mountain", 0xfff0f3fa, 1);
    } else {
        snes_ovl_draw_text(pixels, stride, h, x + 6, 29,
                           "No lead recorded for", 0xfff0f3fa, 1);
        snes_ovl_draw_text(pixels, stride, h, x + 6, 45,
                           "this chapter.", 0xfff0f3fa, 1);
    }
}

void FoundationJournalShutdown(void) {
    watch_installed = 0;
    if (test_pad) { SDL_JoystickClose(test_pad); test_pad = NULL; }
    if (trace) { fclose(trace); trace = NULL; }
}
