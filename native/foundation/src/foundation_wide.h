#ifndef FOUNDATION_WIDE_H
#define FOUNDATION_WIDE_H
/* Bounded Likado preview. Optional packet-bound regular actors use only a
 * private side picture; no guest picture-memory writes. */
int FoundationWideWidth(int requested);
void FoundationWideDrawFrame(void);
void FoundationWideReset(void);
#endif
