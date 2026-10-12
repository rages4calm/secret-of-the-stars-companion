/* Current chapter advice, derived only from original guest state.
 * No ROM/guest writes, completion guesses or external seen-event history. */
#include "foundation_journal.h"
#include "foundation_hotkeys.h"
#include "foundation_map.h"
#include "foundation_guide_data.h"
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
static int guide_input_test;
static SDL_Joystick *test_pad;
static FILE *trace;
static int guide_visible;
static size_t guide_page;
static int guide_tracking_unavailable;
static uint16_t previous_buttons, blocked_buttons, filtered_buttons;
static uint64_t input_generation;

static size_t GuideCount(void) {
    return sizeof(foundation_guide_pages) / sizeof(foundation_guide_pages[0]);
}

static size_t GuideFirstPage(unsigned part) {
    for (size_t i = 0; i < GuideCount(); ++i)
        if (foundation_guide_pages[i].part == part) return i;
    return 0;
}

static size_t GuideCurrentPage(void) {
    const char *title = NULL;
    switch (g_ram[0x5372]) {
    case 0: title = (g_ram[0x5360] & 2) ? "Jeep Volcano" :
                    (g_ram[0x5360] & 0x40) ? "The first StarCrest" : "Find David"; break;
    case 2: title = "Badbad and the Dog-Pill"; break;
    case 3: title = "Rescue the lab children"; break;
    case 5: title = "Free farmer Baz"; break;
    case 6: if (g_ram[0x5360] & 0x80) title = "A ticket and a lion"; break;
    case 7: title = "Lower Victory Bridge"; break;
    case 8: title = "Kaja's missing mustache"; break;
    case 9: case 10: title = "Bring Cody home"; break;
    case 13: title = "Escape Lagoon's mirage"; break;
    case 14: case 15: title = "Brasca's lava passages"; break;
    case 24: title = "Jeep: Dram and Booth"; break;
    }
    if (title)
        for (size_t i = 0; i < GuideCount(); ++i)
            if (!strcmp(foundation_guide_pages[i].title, title)) return i;
    return GuideFirstPage(FoundationJournalGuidePart(g_ram, 0x20000));
}

static void GuideSection(int direction) {
    unsigned current = foundation_guide_pages[guide_page].part;
    if (direction > 0) {
        for (size_t i = guide_page + 1; i < GuideCount(); ++i)
            if (foundation_guide_pages[i].part != current) { guide_page = i; return; }
    } else {
        size_t first = GuideFirstPage(current);
        if (first) guide_page = GuideFirstPage(foundation_guide_pages[first - 1].part);
    }
}

uint16_t FoundationJournalFilterInput(uint16_t buttons) {
    /* Run-ahead must not repeatedly advance host pages or release masking. */
    if (RtlSpeculativeFrame()) return filtered_buttons;
    buttons &= 0x0fff;
    uint64_t generation = RtlStateGeneration();
    if (generation != input_generation) {
        FoundationJournalHide();
        FoundationMapClearGuideTown();
        if (enabled) blocked_buttons |= buttons;
        previous_buttons = buttons;
        input_generation = generation;
    }
    blocked_buttons &= buttons;
    uint16_t edge = buttons & (uint16_t)~previous_buttons;
    previous_buttons = buttons;
    int toggle = FoundationHotkeysConsumeJournal();
    if (enabled && toggle && (visible || g_ram[0x20] == 1)) {
        visible = !visible;
        guide_visible = 0;
        blocked_buttons |= buttons;
        edge = 0; /* A held opener/chord never selects or moves a page. */
        if (visible) FoundationMapHide();
        fprintf(stderr, "[foundation] frame %u journal %s\n", frame_number + 1,
                visible ? "shown" : "hidden");
    }
    if (enabled && visible && g_ram[0x20] == 1) {
        blocked_buttons |= buttons;
        if (edge & 1u) { /* Configured SNES B: close, then wait for release. */
            FoundationJournalHide();
        } else if (edge & 4u) { /* Configured SNES Select: guide/current view. */
            guide_visible = !guide_visible;
            guide_tracking_unavailable = 0;
            if (guide_visible) guide_page = GuideCurrentPage();
        } else if (guide_visible) {
            size_t old_page = guide_page;
            if ((edge & 0xc0u) == 0x40u && guide_page) --guide_page;
            if ((edge & 0xc0u) == 0x80u && guide_page + 1 < GuideCount()) ++guide_page;
            if ((edge & 0x30u) == 0x10u) GuideSection(-1);
            if ((edge & 0x30u) == 0x20u) GuideSection(1);
            if (guide_page != old_page) guide_tracking_unavailable = 0;
            if (edge & SNES_PAD_X) { /* Configured logical SNES X, not a raw key. */
                int town = FoundationGuideTownName((unsigned)guide_page);
                guide_tracking_unavailable = town < 0 ||
                    !FoundationMapTrackGuideTown((unsigned)town);
            }
        }
        filtered_buttons = 0;
    } else {
        filtered_buttons = buttons & (uint16_t)~blocked_buttons;
    }
    return filtered_buttons;
}

void FoundationJournalReset(void) {
    visible = has_lead = 0;
    guide_visible = 0;
    guide_page = 0;
    guide_tracking_unavailable = 0;
    FoundationMapClearGuideTown();
    previous_buttons = blocked_buttons = filtered_buttons = 0;
    input_generation = RtlStateGeneration();
}

void FoundationJournalHide(void) {
    visible = 0;
    guide_visible = 0;
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
    guide_input_test = getenv("SNESRECOMP_FOUNDATION_GUIDE_INPUT_TEST") != NULL;
    env = getenv("SNESRECOMP_FOUNDATION_JOURNAL_TRACE");
    if (env && *env) trace = fopen(env, "w");
    env = getenv("SNESRECOMP_FOUNDATION_JOURNAL_POSSESSION");
    if (env) possession_enabled = !strcmp(env, "1");
    if (trace) fprintf(trace, "frame,mode,stage,flags,enabled,visible,has_lead,inventory_groups,lead_kind,guide_visible,guide_page,guide_part,filtered_buttons\n");
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
                           (!guide_input_test && frame_number == 90) || (frame_number > 30 && frame_number < 60))) {
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
                     (!guide_input_test && (frame_number == 90 || frame_number == 120)))) {
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
    has_lead = FoundationJournalCurrentLead(g_ram, 0x20000) != 0 ||
               FoundationJournalGuidePart(g_ram, 0x20000) != 0;
    if (trace) {
        fprintf(trace, "%u,%u,%u,%u,%d,%d,%d,%u,%u,%d,%zu,%u,%u\n", frame_number, g_ram[0x20],
                g_ram[0x5372], g_ram[0x5360], enabled, visible, has_lead,
                JournalPossessionGroups(g_ram, 0x20000),
                FoundationJournalCurrentLead(g_ram, 0x20000), guide_visible, guide_page,
                FoundationJournalGuidePart(g_ram, 0x20000), filtered_buttons);
        fflush(trace);
    }
}

/* Eight-pixel font, at most 28 characters per row inside the 240px panel.
 * All text is current original advice: no inferred destinations in later stages. */
void FoundationJournalDraw(uint8_t *dst, size_t pitch, int w, int h) {
    if (!enabled || !visible || !dst || g_ram[0x20] != 1 || w < 256 || h < 212 ||
        pitch < (size_t)w * 4 || pitch % 4 || pitch / 4 > INT32_MAX) return;
    if (guide_visible) {
        const FoundationGuidePage *page = &foundation_guide_pages[guide_page];
        uint32_t *pixels = (uint32_t *)dst;
        int stride = (int)(pitch / 4), x = (w - 240) / 2, y = (h - 196) / 2;
        snes_ovl_fill_rect(pixels, stride, h, x, y, 240, 196, 0xff080e1c);
        snes_ovl_stroke_rect(pixels, stride, h, x, y, 240, 196, 0xff809bc8);
        snes_ovl_stroke_rect(pixels, stride, h, x + 2, y + 2, 236, 192, 0xff293a57);
        char heading[32], section[32];
        int town = FoundationGuideTownName((unsigned)guide_page);
        snprintf(heading, sizeof(heading), "STORY GUIDE  %02zu/%02zu", guide_page + 1, GuideCount());
        if (town >= 0) snprintf(section,sizeof(section),"SECTION %u  MAP: %s",page->part,
            FoundationGuideTownLabel((unsigned)guide_page));
        else snprintf(section, sizeof(section), "SECTION %u - CHOOSE A STEP", page->part);
        snes_ovl_draw_text(pixels, stride, h, x + 8, y + 8, heading, 0xffffdf78, 1);
        snes_ovl_fill_rect(pixels, stride, h, x + 8, y + 22, 224, 1, 0xff293a57);
        snes_ovl_draw_text(pixels, stride, h, x + 8, y + 28, page->title, 0xffffdf78, 1);
        for (int i = 0; i < 8; ++i)
            snes_ovl_draw_text(pixels, stride, h, x + 8, y + 44 + i * 12,
                              page->lines[i], 0xfff0f3fa, 1);
        snes_ovl_draw_text(pixels, stride, h, x + 8, y + 148, section, 0xffa7b9d8, 1);
        const char *tracking = town < 0 ? "NO TOWN TO TRACK" :
            guide_tracking_unavailable ? "TRACKING UNAVAILABLE HERE" :
            FoundationMapGuideTown() == town ? "X: CLEAR TRACKED TOWN" : "X: TRACK TOWN";
        snes_ovl_draw_text(pixels, stride, h, x + 8, y + 160, tracking, 0xffa7b9d8, 1);
        snes_ovl_draw_text(pixels, stride, h, x + 8, y + 176, "L/R: PAGE  U/D: SECTION", 0xffffdf78, 1);
        snes_ovl_draw_text(pixels, stride, h, x + 8, y + 186, "SELECT: CURRENT  B: CLOSE", 0xffffdf78, 1);
        return;
    }
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
                /* Original0815 FF3F71 scans the active pack. The gate
                 * accepts held71 even with a full pack and retains the ticket.
                 * Other/missing possession alone cannot promise admission. */
                objective[0] = current ? "Show ticket at circus gate." : "Follow the mayor's advice.";
                objective[1] = current ? "Find the lion in the circus." :
                    item_groups ? "Ticket is in the other pack." : "Ticket is not held now.";
                route[0] = current ? "Gate needs the current pack." : "Mayor: go to the circus.";
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
    } else if (lead == 17 || lead == 18) {
        unsigned moustache_groups = JournalItemGroups(g_ram, 0x20000, 0x70);
        unsigned current = moustache_groups & 1u;
        objective[0] = current ? "Bring MOUSTACHE to Kaja." : "Seek Sidon's moustache.";
        objective[1] = current ? "Help him return to normal." :
            moustache_groups ? "Moustache: in OTHER PACK." : "Kaja asks for MOUSTACHE.";
        route[0] = current ? "Return to Kaja-House." : "Search the southern forest.";
        route[1] = current ? "Talk to Kaja with this pack." : "Kaja names SIDON FOREST.";
        progress = moustache_groups == 3 ? "MOUSTACHE: BOTH PACKS" : current ? "MOUSTACHE: CURRENT PACK" :
            moustache_groups ? "MOUSTACHE: OTHER PACK" : "MOUSTACHE: NOT HELD NOW";
    } else if (lead == 20) {
        unsigned moustache_groups = JournalItemGroups(g_ram, 0x20000, 0x70);
        objective[0] = "Check the party packs.";
        objective[1] = moustache_groups ? "MOUSTACHE: in OTHER PACK." : "MOUSTACHE is not held now.";
        route[0] = "Kaja needs the current pack.";
        route[1] = "Select GUIDE for this route.";
        progress = "Quest items need pack space.";
    } else if (lead == 19) {
        unsigned moustache_groups = JournalItemGroups(g_ram, 0x20000, 0x70);
        objective[0] = "Seek Garados in Bonzley.";
        objective[1] = "Follow Kaja's advice.";
        route[0] = "Go through Kaja's cave.";
        route[1] = "Head south to Bonzley.";
        /* Mutable item summary cannot establish or erase the chapter route. */
        progress = moustache_groups == 3 ? "MOUSTACHE: BOTH PACKS" : (moustache_groups & 1u) ? "MOUSTACHE: CURRENT PACK" :
            moustache_groups ? "MOUSTACHE: OTHER PACK" : "MOUSTACHE: NOT HELD NOW";
    } else if (lead == 16) {
        unsigned key_groups = JournalItemGroups(g_ram, 0x20000, 0x01);
        objective[0] = "Follow the Bonzley lead.";
        objective[1] = "Cross the Victory Bridge.";
        route[0] = "Bridge lies south of Winds.";
        route[1] = "Circus came from Bonzley.";
        /* Current item summary is independent of the original chapter/event.
         * A held/reacquired key never proves or erases permanent history. */
        progress = key_groups == 3 ? "WIN-KEY: BOTH PACKS" : (key_groups & 1u) ? "WIN-KEY: CURRENT PACK" :
            key_groups ? "WIN-KEY: OTHER PACK" : "WIN-KEY: NOT HELD NOW";
    } else if (lead == 14 || lead == 15) {
        unsigned key_groups = JournalItemGroups(g_ram, 0x20000, 0x01);
        unsigned current = key_groups & 1u; /* Exact admitted Aqutallion context. */
        objective[0] = current ? "Lower the bridge to Bonzley." :
            lead == 14 ? "Recover WIN-KEY from Morgan." : "Follow the priest's advice.";
        objective[1] = current ? "Bridge lies south of Winds." :
            key_groups ? "WIN-KEY: in the other pack." : "WIN-KEY is not held now.";
        route[0] = lead == 14 && !key_groups ? "Morgan-House: hidden route." :
            current ? "Use WIN-KEY at the device." : "Bridge lies south of Winds.";
        route[1] = lead == 14 && !key_groups ? "Follow the right-hand wall." :
            current ? "It controls Victory Bridge." : "The bridge leads to Bonzley.";
        progress = key_groups == 3 ? "WIN-KEY: BOTH PACKS" : current ? "WIN-KEY: CURRENT PACK" :
            key_groups ? "WIN-KEY: OTHER PACK" : "WIN-KEY: NOT HELD NOW";
    } else if (lead == 13) {
        objective[0] = "Tell the priest about Cody.";
        objective[1] = "He was turned into a lion.";
        /* Original032F F003 resolves through02AF24/04C200 to DECATAS.
         * No temple door/world coordinate or recruited-party claim follows. */
        route[0] = "Ask at the Decatas temple.";
        route[1] = "Cody asks for the priest.";
        progress = "Current lion's request";
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
    } else if (FoundationJournalGuidePart(g_ram, 0x20000)) {
        const FoundationGuidePage *page = &foundation_guide_pages[GuideCurrentPage()];
        objective[0] = page->title;
        objective[1] = "Guide for this story section.";
        route[0] = page->lines[0];
        route[1] = page->lines[1];
        progress = "Select GUIDE for every step.";
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
    snes_ovl_draw_text(pixels, stride, h, x + 8, y + 28,
                       lead ? "CURRENT OBJECTIVE" : "CURRENT STORY SECTION", gold, 1);
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
                       "SELECT: GUIDE  B: CLOSE", gold, 1);
}

void FoundationJournalShutdown(void) {
    watch_installed = 0;
    if (test_pad) { SDL_JoystickClose(test_pad); test_pad = NULL; }
    if (trace) { fclose(trace); trace = NULL; }
}
