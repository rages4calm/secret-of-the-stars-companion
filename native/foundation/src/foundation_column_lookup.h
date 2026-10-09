#pragma once
/* Default-off, bounded Likado loading lookup. Original-cost execution and the
 * separate diagnostic fast-fetch policy retain each instruction boundary. */
void FoundationColumnLookupInit(void);
void FoundationColumnLookupBeforeFrame(void);
void FoundationColumnLookupReset(void);
void FoundationColumnLookupShutdown(void);
