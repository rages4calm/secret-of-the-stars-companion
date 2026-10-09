#pragma once
#include <stdint.h>

typedef struct Ppu Ppu;

/* Host-only original-art backdrop extension. Unsupported battles retain their
 * authentic center. No enemy, command, OBJ, input or guest timing relocation. */
int FoundationBattleWideEligible(const Ppu *ppu);
/* Caller supplies a private PPU copy and private complete VRAM shadow. This
 * writes only that copy's side policy and BG2 margin words. Original-center
 * pixel comparison remains the caller's acceptance gate. line is 1..224. */
int FoundationBattleWidePrepareLine(const Ppu *source, unsigned line,
                                   Ppu *picture, uint16_t *shadow);
void FoundationBattleWideReset(void);
