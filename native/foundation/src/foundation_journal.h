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

void FoundationJournalInit(void);
void FoundationJournalBeforeFrame(void);
void FoundationJournalReset(void);
void FoundationJournalHide(void);
void FoundationJournalAfterFrame(const SnesDesktopHostFrameStats *stats);
void FoundationJournalDraw(uint8_t *dst, size_t pitch, int w, int h);
void FoundationJournalShutdown(void);
