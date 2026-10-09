# Native Likado margin actors — October 9, 2026

The first native actor side pass qualifies in a copied 0.1.6 candidate. It draws
existing regular Likado actors beyond the original viewport, using their
original graphics and an observed, completed OAM packet. It preserves the
original 256-pixel center and guest execution exactly in this bounded proof.
This document records candidate evidence; it does not certify installation,
full-campaign widescreen, new actor simulation, or a performance improvement.

The source contract and earlier read-only producer assessment are in
[FOUNDATION-WIDE-ACTORS-2026-10-09.md](FOUNDATION-WIDE-ACTORS-2026-10-09.md).
Terrain coverage remains governed by the existing Likado terrain documents.

## Frozen inputs and result

- Candidate: `local/evidence/actor-wide-candidate-20261009-133803/candidate.exe`.
- Candidate SHA-256:
  `b88a6966bfe6c2a2df7a5a07e291c24f0db76366f712e793d7485c3477e96d8b`.
- Copied east-town fixture: `local/runs/likado-east-a/saves/save0.sav`.
- Fixture SHA-256:
  `aabd365c8b4a64dd17cfec34476c8864c9a538a73e44b97c19aeab4bd9c0fa51`.
- Clean USA ROM SHA-256:
  `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.
- Final independent report:
  `local/runs/actor-wide-20261009-134507/report.json` — **78 of 78 gates pass**.
- Authored checker: `tools/check_foundation_wide_actors.py`.

The checker freezes the executable, copies every checkpoint into a fresh private
profile, and checks source hashes afterward. It launches thirteen headless
processes: six actor-off/on pairs plus a copied checkpoint producer. The off
route disables the actor observer as well as drawing, providing a true original
execution control. Deterministic scripts disable gamepads and audio. These
private runs do not use, save into, or modify the owner profile.

## Checked behavior

The paired cases are the original-pixel right/left sweep, the same sweep with
enhanced pixels, a field menu open/close, cold restoration of a generated copied
checkpoint, an actual within-process checkpoint load, and the original-width
fallback. They compare 43 paired snapshot tags across WRAM, VRAM, SRAM, PPU OAM,
CGRAM, registers and original framebuffer bytes. All 301 corresponding files
match exactly. Complete CPU scheduler, state and field traces also match in
every pair.

All 667 paired composed captures retain an identical original 256-pixel center
(512 physical pixels when enhanced scaling is enabled). Differences are confined
to the two margins. Enabling actors without the wide surface changes no composed
pixels and leaves width 256. The original constructor still produces exactly
the same guest OAM: the independent adjacent-field oracle matches **72 of 72
original pieces** against the next actual PPU packet.

The observed target is scene-scoped record `7E:414B`, regular list index 3, base
descriptor index `0268`. This proof establishes a runtime record, not a story
name or permanent character identity. Natural movement brings it from outside
the original draw rectangle into the center, and its original task changes pose
flags from 1 to 3. A displayed X=254 edge sample has positive actual margin
pixels while the original center remains exact. The route moves the camera both
right and left; it does not separately qualify a left-edge actor family.

The first displayed packet uses original descriptor `0E:AB58`, phase 1,
producer field 17525, anchor (289,96). Independently decoding its original
4bpp tiles with captured VRAM/CGRAM explains **all 127 changed margin pixels**,
with exact original colors and no unexplained changed pixel. Current WRAM at the
post-draw snapshot instead has phase 0, descriptor `0E:AB50`, and anchor
(288,96). The checker deliberately uses the displayed packet's identity, avoiding
a pose error from consulting current WRAM. The original-pixel start and X=254
composed screenshots were visually inspected.

The main sweep has 115 frame observations, 114 active matched packets, 192
rendered side pieces and 5,630 actual changed margin pixels. These are counts
over one short replay, not counts of campaign actors or added content.

## Packet identity and restoration

Actual constructor observations confirm D=`0E00`, DB=`01`, M=0 and X=1. Actor
records use a `7E` long pointer; that does not imply CPU DB=`7E`. Every active
frame's actor metadata matches an observed producer record and a preceding,
successful completed DMA with the same generation, epoch and producer field.
The source staging packet and actual PPU OAM match all 544 bytes. No fixed
one-field delay is assumed.

Cold restore begins with a cleared cache and reactivates only after a new
matched packet. The actual load at script step 96 moves the guest field counter
backward, clears the native cache, and increments its generation. All reset rows
have no valid packet and zero cached actors. Across the rollback replay, 112
frames have matched packets and three correctly have no active packet. No
pre-restore pose is promoted into a post-restore generation. The cache is derived
host state; it is not written into guest RAM or serialized into a save schema.

The trace's `capture` rows count constructor observations across all regular
actors. Its target metadata columns consistently describe `414B`; the report's
`target_captures` count of 920 is therefore eight capture rows per field, not
920 unique observations of that one record.

## Scope and reproducibility

`ExperimentalFieldActors=1` / `SNESRECOMP_FOUNDATION_WIDE_ACTORS=1` remains
optional and requires the guarded Likado wide terrain surface. The runtime uses
original descriptor artwork and current per-line PPU state in a private margin
pass. It does not insert additional guest OAM entries or change guest sprite
limits, CPU budgets, tasks, collision or spawning. Original scene logic and the
center renderer continue to run.

Party/composite/variable/effect actors, special `00B0` records, wrapping maps,
other scenes, multiple party members, changed descriptor/resource contracts,
and wider campaign progression are outside this qualification. Interactive
rewind selection and physical controller behavior are not newly certified.
This actor proof contains original pixels; it is distinct from enhanced scaling
and replacement HD artwork.

Paced GPU/audio is separately qualified on this executable in
`local/runs/frame-audio-20261009-134054/report.json`: current menu, original-width
and actor-wide routes hold about 59.9 fps with zero steady underflows, missing
or dropped audible samples. Positive actor counts verify the wide route draws
margin actors. Headless exact parity alone does not establish performance.
All raw snapshots, ROM-derived pixels and captures remain local.

The exact candidate is installed as native **0.1.6**. Companion **0.1.1** offers
a default-off paired expanded-Likado setting and isolated preview. Read
[the installation continuation](FOUNDATION-COMPANION-FIX-2026-10-09.md) for
launcher repair, hashes, protected saves and final launch-route evidence.

```powershell
python tools/check_foundation_wide_actors.py --exe local/evidence/actor-wide-candidate-20261009-133803/candidate.exe
```

Every invocation requires a fresh output directory under `local/`. A later
binary requires a new frozen candidate and receipt; these results apply only to
the hash above.
