# Mega Man X timing and sprite reference

The owner supplied [mstan/MegaManXSNESRecomp](https://github.com/mstan/MegaManXSNESRecomp).
The focused source snapshot used here is commit
`fc6f9ad5209307e29528951c09513dea9b149caa`, with source metadata and files under
ignored `research/2026-10-09/megamanx-timing`. Both projects use runtime pin
`7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0` in this comparison.

The relevant entry points are [main.c](https://github.com/mstan/MegaManXSNESRecomp/blob/fc6f9ad5209307e29528951c09513dea9b149caa/src/main.c)
and [mmx_rtl.c](https://github.com/mstan/MegaManXSNESRecomp/blob/fc6f9ad5209307e29528951c09513dea9b149caa/src/mmx_rtl.c).
The source honors the shared NewRenderer and NoSpriteLimits settings. Its
title-specific native passes and synthetic task entry retain clock accounting;
the default task machine and the optional legacy HLE scheduler have distinct
correctness contracts. Compiled execution alone therefore does not demonstrate
that a game receives more useful guest work per display field. Mega Man X actor
bounds and native scheduler substitutions are not appropriate to copy into this
title without identifying the corresponding game state.

This distinction led to three separate Secret of the Stars proofs:

- [Original-cost native column lookup](FOUNDATION-LOADING-COLUMNS-2026-10-09.md):
  original guest state, actual PPU writes and clocks match, with positive native
  replacement counts, including cold continuation and rollback.
- [Reduced loading costs](FOUNDATION-CLEAR-SPEED-2026-10-09.md): actual guest
  clocks are reduced. Combined clear and lookup saves one field in the checked
  house exit; faster scheduling also changes a live NPC direction accumulator.
  It remains diagnostic and is not an invisible fidelity improvement.
- [Sprite limits](FOUNDATION-SPRITE-LIMITS-2026-10-09.md): actual runtime tests
  show the setting removes scanline sprite/sliver limits, but the natural
  sampled town and battle never reach them. This does not explain their scroll
  behavior or expand the game's original 128 OAM slots by itself.

A separate host HLE frame-composition experiment passed the 17 original-cost
loading/checkpoint checks at `local/runs/loading-20261009-122645/report.json`,
artifact SHA `2aa49140f29d1ab47c0942fb34f58caca0788bff8068229a831e7d8087c0dd87`.
That initial experiment was not promoted on its own. Subsequent owner-reported
0.1.4 audio skipping led to a paced GPU/steady-output comparison and the
[qualified cached presentation fix](FOUNDATION-PRESENTATION-AUDIO-2026-10-09.md)
in 0.1.5. Cached host rendering and guest CPU headroom remain separate measurements.

Coverage is a focused reading of timing/scheduler and settings entry points,
not a Mega Man X code audit or a claim about every enhancement in that project.
No Mega Man X ROM, original art or generated game code was imported.
