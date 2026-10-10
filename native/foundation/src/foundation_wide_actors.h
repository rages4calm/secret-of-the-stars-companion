#ifndef FOUNDATION_WIDE_ACTORS_H
#define FOUNDATION_WIDE_ACTORS_H
struct Ppu;
/* Derived presentation metadata only; the original actor/opcode/DMA executes. */
void FoundationWideActorsSetEnabled(int value);
int FoundationWideActorsEnabled(void);
void FoundationWideActorsInit(void);
void FoundationWideActorsBeforeFrame(void);
void FoundationWideActorsReset(void);
void FoundationWideActorsShutdown(void);
void FoundationWideActorsBeginDraw(void);
unsigned FoundationWideActorsPrepareLine(const struct Ppu *source, unsigned line,
                                        struct Ppu *picture);
void FoundationWideActorsDrawResult(unsigned changed_margin_pixels);
void FoundationWideActorsEndDraw(void);
int FoundationWideActorsOrdinaryPeriodicRaster(const struct Ppu *source, int *world_x, int *world_y);
#endif
