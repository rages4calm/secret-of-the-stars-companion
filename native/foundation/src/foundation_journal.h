#pragma once
#include "host_main.h"
#include <stddef.h>
#include <stdint.h>

/* Bitmask of mutable current inventory evidence, not completed quests.
 * The original item lookup uses these two 32-byte blocks. */
static inline unsigned JournalPossessionGroups(const uint8_t *ram, size_t size) {
    unsigned groups = 0;
    if (!ram || size < 0x53b3) return 0;
    for (unsigned group = 0; group < 2; ++group)
        for (unsigned slot = 0; slot < 32; ++slot)
            if (ram[0x5373 + group * 32 + slot] == 0x40)
                groups |= 1u << group;
    return groups;
}

/* Bounded interpretation of original state, never persistent native history.
 * This exact predicate is also available to a pure synthetic stage unit check. */
/* Current original chapter only. Stage one was observed after Bosen's
 * original rescue dialogue; this is advice, not a quest-completion claim. */
static inline unsigned FoundationJournalLead(unsigned stage, unsigned flags) {
    if (stage == 0 && (flags & 0x40) != 0) return 1;
    if (stage == 1) return 2;
    return 0;
}

static inline int FoundationJournalHasLead(unsigned stage, unsigned flags) {
    return FoundationJournalLead(stage, flags) != 0;
}

void FoundationJournalInit(void);
void FoundationJournalBeforeFrame(void);
void FoundationJournalReset(void);
void FoundationJournalAfterFrame(const SnesDesktopHostFrameStats *stats);
void FoundationJournalDraw(uint8_t *dst, size_t pitch, int w, int h);
void FoundationJournalShutdown(void);
