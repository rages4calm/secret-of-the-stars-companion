/* Current chapter advice, derived only from original guest state.
 * No ROM/guest writes, completion guesses or external seen-event history. */
#include "foundation_journal.h"
#include "foundation_hotkeys.h"
#include "foundation_map.h"
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

void FoundationJournalHide(void) {
    visible = 0;
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
    has_lead = FoundationJournalCurrentLead(g_ram, 0x20000) != 0;
    int toggle = FoundationHotkeysConsumeJournal();
    if (enabled && g_ram[0x20] == 1 && toggle) {
        visible = !visible;
        if (visible) FoundationMapHide();
        fprintf(stderr, "[foundation] frame %u journal %s\n", frame_number, visible ? "shown" : "hidden");
    }
    if (trace) {
        fprintf(trace, "%u,%u,%u,%u,%d,%d,%d,%u,%u\n", frame_number, g_ram[0x20],
                g_ram[0x5372], g_ram[0x5360], enabled, visible, has_lead,
                JournalPossessionGroups(g_ram, 0x20000),
                FoundationJournalCurrentLead(g_ram, 0x20000));
        fflush(trace);
    }
}

/* Eight-pixel font, at most 28 characters per row inside the 240px panel.
 * All text is current original advice: no inferred destinations in later stages. */
void FoundationJournalDraw(uint8_t *dst, size_t pitch, int w, int h) {
    if (!enabled || !visible || g_ram[0x20] != 1 || w < 256 || h < 212) return;
    /* A restore can precede the next guest update. Always derive here too. */
    unsigned lead = FoundationJournalCurrentLead(g_ram, 0x20000);
    unsigned groups = possession_enabled ? JournalPossessionGroups(g_ram, 0x20000) : 0;
    unsigned used[2] = {0, 0};
    for (unsigned pack = 0; pack < 2; ++pack)
        for (unsigned slot = 0; slot < 32; ++slot)
            used[pack] += g_ram[0x5373 + pack * 32 + slot] != 0xff;
    const char *objective[2], *route[2], *progress;
    unsigned town_route = FoundationJournalBadbadRoute(g_ram[0x5372], g_ram[0x5360],
        JournalItemGroups(g_ram, 0x20000, 0x6d), g_ram[0x4b6]);
    if (town_route) {
        objective[0] = "Stop Badbad's dog spell.";
        objective[1] = "Recover the Dog Pill.";
        route[0] = "Badbad-House is in";
        route[1] = "the south part of town.";
        progress = "Town's current plea";
        if (town_route >= 2) {
            objective[0] = town_route == 2 ? "Return with the Dog Pill." : "Switch to the Dog Pill pack.";
            objective[1] = "Help the townspeople.";
            route[0] = "Speak to the person who";
            route[1] = "asked you to stop Badbad.";
            progress = town_route == 2 ? "DOG PILL: CURRENT PACK" : "DOG PILL: OTHER PARTY PACK";
        }
    } else if (lead >= 9 && lead <= 12) {
        unsigned item = lead == 9 ? 0x6f : 0x71;
        unsigned item_groups = JournalItemGroups(g_ram, 0x20000, item);
        unsigned current = item_groups & (1u << ((g_ram[0x4b6] & 0x80) != 0));
        if (lead == 9) {
            objective[0] = current ? "Return with the ballot." : "Ask about the Decatas vote.";
            objective[1] = current ? "Talk to the voting clerk." :
                item_groups ? "Ballot is in the other pack." : "Ballot is not held now.";
            route[0] = "Decatas: speak to the clerk.";
            route[1] = "Ask for voting clues.";
            progress = item_groups == 3 ? "BALLOT: BOTH PACKS" : current ? "BALLOT: CURRENT PACK" :
                item_groups ? "BALLOT: OTHER PACK" : "BALLOT: NOT HELD NOW";
        } else {
            objective[0] = "Ask the new mayor for help.";
            objective[1] = "Circus ticket lead: Decatas.";
            route[0] = "Decatas: the mayor's house.";
            route[1] = "Speak with the new mayor.";
            if (lead == 11) {
                objective[0] = current ? "Take the ticket to circus." : "Follow the mayor's advice.";
                objective[1] = current ? "Follow the mayor's advice." :
                    item_groups ? "Ticket is in the other pack." : "Ticket is not held now.";
                route[0] = "Mayor: go to the circus.";
                route[1] = "Ask people for more clues.";
            } else if (lead == 12) {
                objective[0] = "Aqutallion handles this.";
                objective[1] = "No tickets for Kustera.";
                route[0] = "Decatas: the mayor's advice.";
                route[1] = "Use the Aqutallion party.";
            }
            progress = item_groups == 3 ? "TICKET: BOTH PACKS" : current ? "TICKET: CURRENT PACK" :
                item_groups ? "TICKET: OTHER PACK" : "TICKET: NOT HELD NOW";
        }
    } else if (lead == 8) {
        objective[0] = "Help the new town grow.";
        objective[1] = "Find builders and farmers.";
        route[0] = "Baz plans to cut trees";
        route[1] = "and plant crops here.";
        progress = "Current town farming advice";
        if (FoundationJournalTownHouseClue(g_ram, 0x20000))
            progress = "Child: first house is built.";
    } else if (lead == 7) {
        objective[0] = "Seek Dynamite's help.";
        objective[1] = "Find a way to defeat Golan.";
        route[0] = "Dynamite's laboratory is";
        route[1] = "in the town Morgan entered.";
        progress = "The architect is working.";
        unsigned weapon_groups = JournalItemGroups(g_ram, 0x20000, 0x6e);
        unsigned dynamite = FoundationJournalDynamiteRoute(g_ram[0x5372], g_ram[0x5360], weapon_groups);
        if (dynamite == 1) {
            objective[0] = "Take Dynamite to your town.";
            objective[1] = "He asks for a laboratory.";
            route[0] = "Dynamite asks you to";
            route[1] = "take him to the new town.";
        } else if (dynamite >= 2) {
            objective[0] = "Find a way to defeat Golan.";
            objective[1] = dynamite == 2 ? "Use Graviton against Golan." : "Graviton is not held now.";
            route[0] = "Dynamite's weapon advice:";
            route[1] = "use Graviton against Golan.";
        }
        if (dynamite >= 4) {
            objective[0] = "Search GIANT for Golan.";
            objective[1] = dynamite == 4 ? "Use Graviton against Golan." : "Graviton is not held now.";
            route[0] = "GIANT: Golan built a";
            route[1] = "large house in the town.";
        }
        if (dynamite) {
            /* Pack selection uses the original signed004B6 convention.
             * This is mutable possession information, not a usable-item
             * guarantee or a claim that the escort has completed. */
            unsigned pack = (g_ram[0x4b6] & 0x80) != 0;
            progress = weapon_groups == 3 ? "GRAVITON: BOTH PACKS" :
                !weapon_groups ? "GRAVITON: NOT HELD NOW" :
                (weapon_groups & (1u << pack)) ? "GRAVITON: CURRENT PACK" : "GRAVITON: OTHER PACK";
        }
    } else if (lead == 6) {
        objective[0] = "Find builders and farmers.";
        objective[1] = "Help build the new town.";
        route[0] = "Talk to Uncle Save at home.";
        route[1] = "Ask people about town help.";
        progress = "Current town-building lead";
        if (FoundationJournalHasTownClue(g_ram[0x5372], g_ram[0x5360])) {
            route[0] = "Find architects to build";
            route[1] = "and farmers to grow crops.";
            progress = "Uncle Save's current advice";
        }
        if (FoundationJournalTownBuilderClue(g_ram[0x5372], g_ram[0x5360],
                                            g_ram[0x5364], g_ram[0x4b6]) == 1)
            progress = "Master: take care of Bun.";
        if (FoundationJournalHasMorganClue(g_ram[0x5372], g_ram[0x5360])) {
            objective[0] = "Find a way to defeat Golan.";
            objective[1] = "Ask Dynamite for help.";
            route[0] = "Morgan offers town access.";
            route[1] = "Bring 100 gold for entry.";
            progress = "Morgan's current advice";
        }
    } else if (lead == 4) {
        objective[0] = "Rescue the kidnapped kids.";
        objective[1] = "Face the Ringo Brothers.";
        route[0] = "Speak to the town's mayor.";
        route[1] = "Ask about the Ringo Bros.";
        progress = "Town's current chapter";
        if (g_ram[0x5360] & 0x80) {
            route[0] = "Ringo Bros' hide-out lies";
            route[1] = "south of the mayor.";
            progress = "Mayor's current advice";
        }
    } else if (lead == 3) {
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
                       "GAME RUNNING", gold, 1);
}

void FoundationJournalShutdown(void) {
    watch_installed = 0;
    if (test_pad) { SDL_JoystickClose(test_pad); test_pad = NULL; }
    if (trace) { fclose(trace); trace = NULL; }
}
