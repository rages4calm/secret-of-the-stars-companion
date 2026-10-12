#ifndef FOUNDATION_WIDE_H
#define FOUNDATION_WIDE_H
/* Selected-resource terrain and packet-bound actors use a private side
 * picture; original guest picture memory and gameplay remain authoritative. */
int FoundationWideWidth(int requested);
void FoundationWideDrawFrame(void);
void FoundationWideReset(void);
#endif
