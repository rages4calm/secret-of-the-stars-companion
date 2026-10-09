# Likado renderer-owned terrain preview

October 9, 2026. Version 0.1.2 supersedes the installed status in
`FOUNDATION-JOURNAL-CPU-2026-10-09.md`. Decisions, controller support, original
view, title-first normal launch, optional journal and the menu-clipping repair
remain. The installation receipt and current executable identity are in
`local/evidence/build-receipt.json`.

The focused live proof is now implemented: Likado scene 5 can show 72 additional
terrain pixels on each side, producing 400×224 native scenery, or 800×448 with
the existing enhanced-pixel filter. The scene's decoded full maps supply tile
words that the original 64×32 scrolling rings leave stale. This is original
terrain, not replacement HD art, stretching, repetition or generated scenery.

## Try the isolated proof

Run `Start Likado Widescreen Preview.cmd`. It creates a fresh timestamped profile
under `local/preview-likado`, copies the owner's current settings/bindings, and
resumes the checked Likado fixture. It does not launch or overwrite owner SRAM
or checkpoints. Each preview's saves/logs remain in its own directory. The
normal foundation launcher still starts at the title and keeps
`ExperimentalFieldWide=0`; existing explicit settings remain editable.

Controller bindings are inherited. Fullscreen remains Alt+Enter/F11/F12;
rewind is F8 and closes with Escape/Z/controller B. Journal is J/left-stick
click; enemy HP is H/right-stick click. Physical controller/display/listening
coverage still rests on the owner's earlier report, not the new automated proof.

## Native implementation

`foundation_field.c` verifies the exact clean USA ROM, Likado pointers,
dimensions, metatile attributes, scene/loading/wrap state and supported PPU
layout before decoding two renderer-owned full maps. It preserves original
tile words, priorities, palettes and flips, with signed negative coordinates and
the original outside-map metatile-zero policy. The portable resolver checker
matches 3,584 captured center words, 40,960 complete-map words and 1,764 boundary
cases. Wrong content/scene/layout and reset controls refuse the cache.

Preparation happens before scroll-journal replay. Its scene guard permits that
specific scroll disagreement; the original strict API still rejects it. Per
raster line, the compositor unwraps actual ten-bit PPU scroll around the signed
WRAM camera. Sampling uses `camera_y + line`, including fractional tile edges.
This fixes the first candidate's viewport narrowing during one-pixel moves.

The original raster draws an authentic 256-column viewport centered inside the
400-column host surface. Original sprite evaluation/overflow and guest VRAM,
OAM, palette and timing remain intact. The beam observer then clones that line's
PPU state after its original draw and before H-blank HDMA. A private VRAM shadow
retains current graphics, including animation, and replaces only BG1/BG2 map
words. It never runs another raster journal or DMA walk.

Every line validates the original center tile words and cloned center pixels.
A second private pass supplies terrain-only margins, excluding OBJ there. Any
line refusal clears both margins for the entire field. BG3 stays centered.
The enhanced filter separately reproduces the original center's edge decisions,
so extra neighbors do not change the established enhanced view. Reset and state
restore discard derived eligibility/cache state; no checkpoint schema change.

## Qualified release evidence

Release SHA-256:
`c6ace23e4cc71436a8b4ad02933ab9200f6e460960b9b8aad5df1dec96b8c288`.
The diagnostic side build had a different PE identity and was qualified
separately; release reports bind to the usual build above.

`local/runs/field-wide-20261009-113109/report.json` passes five off/on pairs:
town movement/menu, natural house exit, battle fallback, cold restore and
enhanced pixels. Twelve guest snapshots match across WRAM, VRAM, SRAM, OAM,
CGRAM and register dumps; their original framebuffer centers match. Seventy-five
composed-surface comparisons also retain the center exactly. All eight camera
pixel phases on both axes and a vertical 256-pixel segment boundary are covered.

The town case verifies 180,544 scanlines with zero tile/pixel mismatches and zero
refused lines. Later ordinary streaming matches 448 previously previewed tile
words, including 392 initially stale ring words. Unsupported house and battle
use 256 columns; natural entry into supported Likado expands to 400.

The final Windows preview report is recorded by `likado_desktop_report` in the
build receipt. It verifies the separate launcher, checked checkpoint consumption,
800×448 composed GPU surface, actual Direct3D 11 VSync, early nonzero callback
PCM and unchanged owner files/ROMs. Normal title/original-view/fullscreen and
settings migration checks pass. Existing virtual controller gameplay/overlay
exit, HP control, journal rollback, menu regression/timing, audio and guarded
checkpoint tests also pass on this release. Headless runtimes are not a benchmark
or proof of physical scanout performance.

## Remaining work and next bounded proof

- The side picture is terrain only. Actors outside the original viewport need
  verified native visibility/spawn/OAM identity work. Other maps, conditional
  terrain, fades, alternate PPU layouts and campaign widescreen remain unqualified.
- Replacement HD graphics and optional compatible MSU-1 track logic/packs are
  not implemented. Current VRAM animation is preserved but its replacement-art
  identity/dispatch is not established.
- The player's observed scrolling/tearing report is not closed by this proof.
  Original CPU budget remains; renderer width does not remove SNES slowdown.
- Read `FOUNDATION-LOADING-CPU-2026-10-09.md` next. The loading deadlines identify
  VRAM clearing, graphics DMA, map lookup/expansion and a cooperative yield;
  decompression or productive overload in all eleven fields is unproven. The
  next timing proof should capture clear-loop entry/return and original writes
  before changing its implementation or modeled costs.
- Journal scope remains David's verified first-stage mountain/Crest lead.
  Crest acquisition/completion and persistent journal history need real events.
- Most CPU execution remains interpreted; reference timing/NPC divergence and
  seven experimental AOT WRAM differences remain unresolved. This is progress
  toward the requested port, not a complete native recompilation or campaign
  compatibility certification.

Author/live sources and additive source-only archive are hash recorded. Owner
installation uses a new hash-verified backup and leaves saves, original ROM,
custom configuration and input bindings unchanged. Its exact receipt is linked
from `installation_report` in the build receipt.
