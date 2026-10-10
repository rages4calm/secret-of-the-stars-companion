/* Current chapter advice, derived only from original guest state.
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
    if (trace) fprintf(trace, "frame,mode,stage,flags,enabled,visible,has_lead,inventory_groups,lead_kind\n");
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
        fprintf(trace, "%u,%u,%u,%u,%d,%d,%d,%u,%u\n", frame_number, g_ram[0x20],
                g_ram[0x5372], g_ram[0x5360], enabled, visible, has_lead,
                JournalPossessionGroups(g_ram, 0x20000),
                FoundationJournalLead(g_ram[0x5372], g_ram[0x5360]));
        fflush(trace);
    }
}

/* Eight-pixel font, at most 28 characters per row inside the 240px panel.
 * All text is current original advice: no inferred destinations in later stages. */
void FoundationJournalDraw(uint8_t *dst, size_t pitch, int w, int h) {
    if (!enabled || !visible || g_ram[0x20] != 1 || w < 256 || h < 212) return;
    /* A restore can precede the next guest update. Always derive here too. */
    unsigned lead = FoundationJournalLead(g_ram[0x5372], g_ram[0x5360]);
    unsigned groups = possession_enabled ? JournalPossessionGroups(g_ram, 0x20000) : 0;
    unsigned used[2] = {0, 0};
    for (unsigned pack = 0; pack < 2; ++pack)
        for (unsigned slot = 0; slot < 32; ++slot)
            used[pack] += g_ram[0x5373 + pack * 32 + slot] != 0xff;
    const char *objective[2], *route[2], *progress;
    if (lead == 3) {
        objective[0] = "Defeat Homncruse's follower";
        objective[1] = "in Jeep Volcano.";
        route[0] = "Enter the nearby mountain.";
        route[1] = "Kustera can fight for you.";
        progress = "Aris advice: Pennon";
    } else if (lead == 2) {
        objective[0] = "Find Aqutallion allies.";
        objective[1] = "Find Kustera; build a town.";
        route[0] = "Bosen asks you to find";
        route[1] = "allies for the new town.";
        progress = "Bosen's current advice";
        if (FoundationJournalHasLikadoClue(g_ram[0x5372], g_ram[0x5360])) {
            route[0] = "Uncle Save: Likado is empty.";
            route[1] = "Gather allies for the town.";
        }
    } else if (lead == 1) {
        objective[0] = "Seek the Crest of Stars.";
        objective[1] = "Follow David's lead.";
        route[0] = "David: somewhere in";
        route[1] = "the mountain.";
        progress = "David's current advice";
    } else {
        objective[0] = "No current lead recorded.";
        objective[1] = "Talk to people for clues.";
        route[0] = "No route recorded for";
        route[1] = "the current chapter.";
        progress = "Current party packs";
    }
    uint32_t *pixels = (uint32_t *)dst;
    int stride = (int)(pitch / 4), x = (w - 240) / 2, y = (h - 196) / 2;
    const uint32_t body = 0xff080e1c, border = 0xff809bc8;
    const uint32_t gold = 0xffffdf78, ink = 0xfff0f3fa, muted = 0xffa7b9d8;
    snes_ovl_fill_rect(pixels, stride, h, x, y, 240, 196, body);
    snes_ovl_stroke_rect(pixels, stride, h, x, y, 240, 196, border);
    snes_ovl_stroke_rect(pixels, stride, h, x + 2, y + 2, 236, 192, 0xff293a57);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 8, "QUEST JOURNAL", gold, 1);
    for (int row = 22; row <= 122; row += 50)
        snes_ovl_fill_rect(pixels, stride, h, x + 8, y + row, 224, 1, 0xff293a57);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 28, "CURRENT OBJECTIVE", gold, 1);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 42, objective[0], ink, 1);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 54, objective[1], ink, 1);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 78, "ROUTE AND ADVICE", gold, 1);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 92, route[0], ink, 1);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 104, route[1], ink, 1);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 128, "CURRENT PROGRESS", gold, 1);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 142, progress, ink, 1);
    char packs[32];
    snprintf(packs, sizeof(packs), "PACKS: %u/32 AND %u/32", used[0], used[1]);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 154, packs, muted, 1);
    const char *crest = !possession_enabled ? "PACK ITEM SUMMARY OFF" :
                        groups == 3 ? "STARCREST: BOTH PACKS" :
                        groups ? "STARCREST: ONE PACK" : "STARCREST: NOT HELD NOW";
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 166, crest, muted, 1);
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 184,
                       "HOTKEY: CLOSE - GAME RUNNING", gold, 1);
}

void FoundationJournalShutdown(void) {
    watch_installed = 0;
    if (test_pad) { SDL_JoystickClose(test_pad); test_pad = NULL; }
    if (trace) { fclose(trace); trace = NULL; }
}
