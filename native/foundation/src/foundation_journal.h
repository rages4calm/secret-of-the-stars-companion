#pragma once
#include "host_main.h"

/* Bounded interpretation of original state, never persistent native history.
 * This exact predicate is also available to a pure synthetic stage unit check. */
static inline int FoundationJournalHasLead(unsigned stage, unsigned flags) {
    return stage == 0 && (flags & 0x40) != 0;
}

void FoundationJournalInit(void);
void FoundationJournalBeforeFrame(void);
void FoundationJournalReset(void);
void FoundationJournalAfterFrame(const SnesDesktopHostFrameStats *stats);
void FoundationJournalDraw(uint8_t *dst, size_t pitch, int w, int h);
void FoundationJournalShutdown(void);
