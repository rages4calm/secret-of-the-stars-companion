#pragma once
#include "host_main.h"
#include <stddef.h>
#include <stdint.h>

/* Bitmask of mutable current inventory evidence, not completed quests.
 * The original item lookup uses these two 32-byte blocks. */
static inline unsigned JournalItemGroups(const uint8_t *ram, size_t size, unsigned item) {
    unsigned groups = 0;
    if (!ram || size < 0x53b3) return 0;
    for (unsigned group = 0; group < 2; ++group)
        for (unsigned slot = 0; slot < 32; ++slot)
            if (ram[0x5373 + group * 32 + slot] == item)
                groups |= 1u << group;
    return groups;
}

static inline unsigned JournalPossessionGroups(const uint8_t *ram, size_t size) {
    /* Original inventory names use 04:C080: item00 is STARCREST.
     * The different 04:C000 table gives a misleading index40; inventory40
     * is LIFEVEST. This is current possession, never award history. */
    return JournalItemGroups(ram, size, 0x00);
}

/* Bounded interpretation of original state, never persistent native history.
 * This exact predicate is also available to a pure synthetic stage unit check. */
/* Current original chapter only. Stage one was observed after Bosen's
 * original rescue dialogue; this is advice, not a quest-completion claim. */
static inline unsigned FoundationJournalLead(unsigned stage, unsigned flags) {
    /* Original Aris message 0304/03AB sets stage-zero bit 02.
     * Pennon advice has priority; David bit 40 is not a prerequisite. */
    if (stage == 0 && (flags & 0x02) != 0) return 3;
    if (stage == 0 && (flags & 0x40) != 0) return 1;
    if (stage == 1) return 2;
    if (stage == 2) return 5;
    if (stage == 3) return 4;
    if (stage == 4) return 6;
    if (stage == 5) return 7;
    /* Original0346 FA7F advances to chapter6 and resets both flag bytes.
     * Actual0323 describes farming the town; later father0326 is not covered. */
    if (stage == 6 && flags == 0) return 8;
    return 0;
}

/* Current Decatas ballot/mayor advice, not election history. Original0807
 * supplies/consumes6F; original0809 tests global5365bit10 first, then current
 * chapter6 flags and the signed04B6 party before offering71. Admit only the
 * actually replayed exact current flag states; unknown/later states refuse.
 * 9: Aqutallion ballot; 10: Aqutallion mayor; 11: Aqutallion circus advice;
 * 12: Kustera mayor refusal. Possession remains independently mutable. */
static inline unsigned FoundationJournalDecatasRoute(unsigned stage, unsigned flags,
                                                      unsigned global_flags, unsigned party,
                                                      unsigned mode) {
    if (stage != 6 || flags > 255 || global_flags > 255 || party > 255 ||
        mode != 1 || (global_flags & 0x10)) return 0;
    if (flags == 0x80) return (party & 0x80) ? 0 : 9;
    if (flags != 0xc0 && flags != 0xe0) return 0;
    if (party & 0x80) return 12;
    return flags == 0xc0 ? 10 : 11;
}

/* Narrow current priest clue from original0150/032F, after0332 FA7F.
 * Actual01D35E/364/368 reset the current chapter flags;01D335 writes5365bit10.
 * Exact observed state only, not permanent circus/victory/recruitment history.
 * Other-party access and later/nonzero current flags remain unqualified.
 * Mutable ticket/Starcrest/roster possession does not establish this clue. */
static inline unsigned FoundationJournalPriestRoute(unsigned stage, unsigned flags,
                                                    unsigned secondary_flags,
                                                    unsigned global_flags,
                                                    unsigned party, unsigned mode) {
    return stage == 7 && flags == 0 && secondary_flags == 0 &&
        global_flags == 0x10 && party == 0 && mode == 1 ? 13 : 0;
}

/* Original077C FA00 supplies current chapter7 bit80. Original0762
 * selects the key offer at that bit, then FA02 supplies bit20 before
 * original00873F inserts item01 WIN-KEY. Flags are current advice only;
 * possession remains independently mutable. This exact observed Aqutallion
 * context does not certify bridge operation or permanent quest history. */
static inline unsigned FoundationJournalBridgeRoute(unsigned stage, unsigned flags,
                                                     unsigned secondary_flags,
                                                     unsigned global_flags,
                                                     unsigned party, unsigned mode) {
    if (stage != 7 || secondary_flags != 0 || global_flags != 0x10 ||
        party != 0 || mode != 1) return 0;
    return flags == 0x80 ? 14 : flags == 0xa0 ? 15 : 0;
}

/* Original0128 FA7F advances to current chapter8 before item01 removal.
 * Original0151 then settles, and the still-loaded0719 selects289329:
 * "THE BRIDGE MOVED". Original077C names Bonzley and south of Winds.
 * This is the narrow observed current route, never durable completion.
 * Do not derive the route from keyabsence. Wait for idle original field
 * dialogue/event state; a scene reload may retire the shrine NPC. */
static inline unsigned FoundationJournalAfterBridgeRoute(const uint8_t *ram, size_t size) {
    if (!ram || size < 0x53b3 || ram[0x5372] != 8 || ram[0x5360] ||
        ram[0x5361] || ram[0x5365] != 0x10 || ram[0x4b6] || ram[0x20] != 1 ||
        ram[0x434] || ram[0x435] || ram[0x532] ||
        ram[0x1410] || ram[0x1411] || ram[0x1415] || ram[0x1416] || ram[0x1417])
        return 0;
    return 16;
}

static inline unsigned FoundationJournalCurrentLead(const uint8_t *ram, size_t size) {
    if (!ram || size < 0x53b3) return 0;
    unsigned after_bridge = FoundationJournalAfterBridgeRoute(ram, size);
    if (after_bridge) return after_bridge;
    unsigned bridge = FoundationJournalBridgeRoute(ram[0x5372], ram[0x5360],
        ram[0x5361], ram[0x5365], ram[0x4b6], ram[0x20]);
    if (bridge) return bridge;
    unsigned priest = FoundationJournalPriestRoute(ram[0x5372], ram[0x5360],
        ram[0x5361], ram[0x5365], ram[0x4b6], ram[0x20]);
    if (priest) return priest;
    unsigned decatas = FoundationJournalDecatasRoute(ram[0x5372], ram[0x5360],
        ram[0x5365], ram[0x4b6], ram[0x20]);
    return decatas ? decatas : FoundationJournalLead(ram[0x5372], ram[0x5360]);
}

/* Original0755: introductory stage1/flag02 (FA02 -> bit20), then type2
 * accepts current chapters <=2. Original01D406 looks for6D in the ACTIVE
 * 32-slot pack only. Chapter2 independently selects the return branch;
 * challenge bit80 is not a victory or award flag. */
static inline unsigned FoundationJournalBadbadRoute(unsigned stage, unsigned flags,
                                                    unsigned dog_groups, unsigned active_pack) {
    if (!(stage == 2 || (stage == 1 && (flags & 0x20)))) return 0;
    if (dog_groups & (1u << (active_pack != 0))) return 2;
    return dog_groups ? 3 : 1;
}

static inline int FoundationJournalHasLead(unsigned stage, unsigned flags) {
    return FoundationJournalLead(stage, flags) != 0;
}

/* Original Uncle Save message0425 reads stage1/flag03, then FA03 sets bit10.
 * This is a current clue about Likado, not a rescued-town completion flag. */
static inline int FoundationJournalHasLikadoClue(unsigned stage, unsigned flags) {
    return stage == 1 && (flags & 0x10) != 0;
}

/* Original0425 FA07: current chapter4 town-building advice. Original0762
 * FA02: current chapter4 Morgan/Dynamite route. Neither is quest history. */
static inline int FoundationJournalHasTownClue(unsigned stage, unsigned flags) {
    return stage == 4 && (flags & 0x01) != 0;
}
static inline int FoundationJournalHasMorganClue(unsigned stage, unsigned flags) {
    return stage == 4 && (flags & 0x20) != 0;
}

/* Original0758 places its other-party branch before chapter4/flag01 care of
 * Bun. The observed original148 branch has currentC0 and global5364bit08;
 * that global bit alone also occurs in earlier dialogue and proves no award.
 * Original0425's ordered chapter5 branch2B95BF says the architect is working,
 * without a current/global flag or party test. Neither clue is completion. */
static inline unsigned FoundationJournalTownBuilderClue(unsigned stage, unsigned flags,
                                                        unsigned global_flags, unsigned party) {
    if (flags > 255 || global_flags > 255 || party > 255) return 0;
    if (stage == 5) return 2;
    if (stage == 4 && (flags & 0xc0) == 0xc0 && (global_flags & 0x08) && !(party & 0x80)) return 1;
    return 0;
}

/* Current available child0421 clue, not an interacted/finished-quest log.
 * Ordered original2B8327/2C/31 clauses select2BA9FE only at chapter6.
 * Original scene321 then selects town118/grid09A0D0; actor listAC selects
 * 0AF01E. Require the observed original six base/message memberships,
 * allowing their normal direction/movement bytes to change. Unknown/stale
 * resources or the other party cannot borrow this scene-specific clue. */
static inline int FoundationJournalTownHouseClue(const uint8_t *ram, size_t size) {
    static const uint16_t bases[6] = {0x0310,0x0320,0x0328,0x0338,0x0348,0x03d8};
    static const uint16_t messages[6] = {0x0420,0x0421,0x0422,0x0423,0x0424,0x041a};
    if (!ram || size < 0x53b3 || ram[0x20] != 1 || ram[0x5372] != 6 ||
        ram[0x5360] || ram[0x5361] || (ram[0x4b6] & 0x80) ||
        ram[0x40e] != 0x41 || ram[0x40f] != 1 ||
        ram[0x46d] != 3 || ram[0x46e] != 4 ||
        ram[0x46f] != 3 || ram[0x470] != 4 ||
        ram[0x513] != 0xd0 || ram[0x514] != 0xa0 || ram[0x515] != 9 ||
        ram[0x516] != 0x90 || ram[0x517] != 0xa1 || ram[0x518] != 9 ||
        ram[0x537] != 0x10 || ram[0x538] != 0x85 || ram[0x539] != 9)
        return 0;
    for (unsigned i = 0; i < 19; ++i) {
        unsigned at = 0x4100 + 25 * i;
        if (i >= 6) {
            if (ram[at] != 0xff) return 0;
        } else if ((ram[at] & 0x7f) > 3 ||
                   (ram[at+5] | ((unsigned)ram[at+6] << 8)) != bases[i] ||
                   (ram[at+12] | ((unsigned)ram[at+13] << 8)) != messages[i])
            return 0;
    }
    return 1;
}

/* Private candidate, based on original07BB chapter5 only. FA01 sets bit40
 * before the weapon award, so possession is checked independently. FA03
 * sets bit10 before the original escort event. Neither flag is history.
 * Route1: current weapon plus escort request; route2: current weapon and
 * escort flag; route3: current escort flag, weapon no longer present.
 * Routes4/5: qualified current join flag, weapon held/not held now. */
/* Original0301 FA06 is reached only at the end of Dynamite joining the town.
 * Retain the actual chapter5 offer/escort prerequisites; this current flag
 * is not an enduring escort/Golan completion record. */
static inline int FoundationJournalHasDynamiteJoined(unsigned stage, unsigned flags) {
    return stage == 5 && flags <= 255 && (flags & 0xd2) == 0xd2;
}

static inline unsigned FoundationJournalDynamiteRoute(unsigned stage, unsigned flags,
                                                      unsigned graviton_groups) {
    if (stage != 5 || flags > 255 || graviton_groups > 3 || (flags & 0xc0) != 0xc0) return 0;
    if (FoundationJournalHasDynamiteJoined(stage, flags)) return graviton_groups ? 4 : 5;
    if (flags & 0x10) return graviton_groups ? 2 : 3;
    return graviton_groups ? 1 : 0;
}

/* Read-only navigation hint: exact original destination scene, not a guessed
 * world coordinate. FFFF means no qualified destination. Original0762 paid
 * entry/014A actually loads scene85; no Ringo/Crest completion is inferred. */
static inline unsigned FoundationJournalDestination(unsigned stage, unsigned flags,
                                                     unsigned dog_groups, unsigned active_pack) {
    unsigned town = FoundationJournalBadbadRoute(stage, flags, dog_groups, active_pack);
    if (town) return town >= 2 ? 58 : 67;
    if (stage == 3 && !(flags & 0x80)) return 59;
    /* Original offer/escort flags do not prove a Golan world location.
     * Suppress the old lab marker after the current offer/escort branch;
     * item removal must not restore an outdated destination. */
    /* Original GIANT name04C8F7, entrance08ADF8 destination79 and
     * chapter5 NPC075B large-house clue; no guessed world coordinate. */
    if (FoundationJournalHasDynamiteJoined(stage, flags)) return 79;
    if (stage == 5 && (flags & 0x50)) return 0xffff;
    if (FoundationJournalHasMorganClue(stage, flags) || stage == 5) return 85;
    return 0xffff;
}

/* Keep the prior pure destination API unchanged. Root independently proved
 * the original world destination/name identity separately: Decatas is
 * original world destination85, not an indoor coordinate. The
 * existing parser refuses flags10 interior links120/129. Never invent a
 * circus pin, nor leave a Decatas marker after the current ticket offer. */
static inline unsigned FoundationJournalDestinationState(const uint8_t *ram, size_t size) {
    if (!ram || size < 0x53b3) return 0xffff;
    /* No original Bonzley destination/entrance pin is qualified yet. */
    if (FoundationJournalAfterBridgeRoute(ram, size)) return 0xffff;
    /* Original bridge dialogue names a region, not a verified map entrance. */
    if (FoundationJournalBridgeRoute(ram[0x5372], ram[0x5360],
        ram[0x5361], ram[0x5365], ram[0x4b6], ram[0x20])) return 0xffff;
    /* Original032F names Decatas; the exact chapter7 selector088420 uses
     * town85/088FA1 name03, with original world entrances08AF50/58.
     * This marks the named town, never a guessed temple door coordinate. */
    if (FoundationJournalPriestRoute(ram[0x5372], ram[0x5360],
        ram[0x5361], ram[0x5365], ram[0x4b6], ram[0x20])) return 85;
    unsigned route = FoundationJournalDecatasRoute(ram[0x5372], ram[0x5360],
        ram[0x5365], ram[0x4b6], ram[0x20]);
    if (route == 9 || route == 10) return 85;
    return FoundationJournalDestination(ram[0x5372], ram[0x5360],
        JournalItemGroups(ram, size, 0x6d), (ram[0x4b6] & 0x80) != 0);
}

void FoundationJournalInit(void);
void FoundationJournalBeforeFrame(void);
void FoundationJournalReset(void);
void FoundationJournalHide(void);
void FoundationJournalAfterFrame(const SnesDesktopHostFrameStats *stats);
void FoundationJournalDraw(uint8_t *dst, size_t pitch, int w, int h);
void FoundationJournalShutdown(void);
