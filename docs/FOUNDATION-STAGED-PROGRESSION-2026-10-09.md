# Focused staged progression — 2026-10-09

The owner authorized advancing gameplay and setting disposable test flags to
accelerate foundation work. Earlier instructions to wait for natural later-game
checkpoints no longer limit development. Staged states remain a distinct evidence
category: they establish execution of the original loaders and constructors,
not natural campaign progression or a verified quest award.

The normal installed foundation remains 0.2.0 and Companion remains 0.3.0.
These separate experimental builds do not change the owner installation.
Original ROMs, saves and settings remain protected. The canonical 48-input native
manifest, guest cycle accounting and runtime patch remain unchanged.

## Disposable checkpoint tooling

`tools/stage_foundation_checkpoint.py` creates a fresh checkpoint and an explicit
receipt under a caller-specified private evidence root. Every edit supplies a
hexadecimal WRAM offset, expected bytes and replacement bytes. It validates the
foundation envelope, CRC, pinned RTLS v10 serialization layout and foundation
execution extension v2/v3. Only requested WRAM bytes and the envelope CRC change.
It refuses overwrites, overlapping/out-of-range edits, unexpected old bytes,
invalid layouts and output escaping the evidence root. It never rewrites input.

For example, with an existing compatible **copied** developer checkpoint:

```powershell
python tools/stage_foundation_checkpoint.py "D:\Private tests\source.sav" `
  --evidence-root "D:\Private tests\evidence" `
  --output-dir "D:\Private tests\evidence\world-stage17" `
  --edit 5372=00:11 --edit 5361=00:00 `
  --reason "Later world-map loader test; staged progression"
```

This example requires stage zero and a clear second flag byte already present;
other source bytes require different explicit expectations. Stage 17 is byte
`11` in hexadecimal. A valid envelope does not establish coherent gameplay.
Older extension-v1 snapshots must be restored and resaved through the game in
an isolated profile first. No private checkpoint is included in this repository.
Fourteen existing layouts were assessed; refusal controls and v2/v3 positive
edit controls pass 17 focused checks.

## Parked Algos / regular B0

The exact separate B0 candidate is
`98fdf7fa43207feed5af791def8ee510ac3f36f0a46be9df32ead3019c3af021`.
A copied interior checkpoint was resaved through the game. Its saved vehicle
scene and position were staged before the original door/field loader. Original
allocation activated the parked record and original `01:DB68` executed; its
graphics came from the game, not a substituted asset or fabricated OAM packet.

The regular parked sprite's two 16×16 components contain 390 nontransparent
pixels. An independent decoder matches all 390 in center, left-edge and
right-edge cases, including 76 or 314 visible margin pixels in the respective
placements. Five paired cases preserve all 175 captured guest/register/center
dumps and fifteen original-center host surfaces. A saved-scene mismatch refuses
the constructor. Cold restore and rollback clear derived packets until a new
matching complete 544-byte original OAM transfer arrives.

Fifteen focused parked-B0 checks pass. Its paced Direct3D test holds about
60.04 presentations/second, with 0.635 ms mean composition and no measured
steady audio underflows, missing frames or audible overflow. These are finite
local hardware checks, separate from listening and physical-controller testing.
The earlier three ordinary paced routes also pass on this exact candidate.

An Algos UFO deliberately placed in Likado is an actor-rendering fixture. It
does not represent natural story placement or modify the owner save. Travel
and world-edge crossings have separate evidence requirements.

## Algos travel and its reserved shadow packet

The separate travel candidate is
`9f9fa0d988dff7d55ca548ed9aac7fb222ee5882ab75656b2740e6afb2021372`.
Staging the travel mode before the original party loader reaches original
`01:D989` for the B0 body and the A8 proxy constructor. The proxy temporarily
uses reserved OAM slots 124–127 without advancing the ordinary append cursor.
The experiment verifies their exact words and high bits in the completed
544-byte original packet; it does not draw the proxy into the margins.

Sixteen focused checks pass: 372 original body and 372 proxy captures, all four
direction poses, both proxy phases, 91 guest comparisons, seven same-field
rollback comparisons and thirteen exact original-center captures. Independently
decoded body art matches all 386–390 original opaque pixels. Cold restoration
and rollback reset derived packets; an unsupported proxy coordinate refuses
the extension. The exact candidate also passes 78 ordinary actor gates.
Its finite paced four-direction route also passes eleven Windows GPU/audio
gates: about 60.03 presentations/second, 0.657 ms mean composition and no
measured steady audio underflows, missing frames or audible overflow.
The original travel body stays centered, so this establishes travel packet
support rather than body-margin coverage or natural vehicle acquisition.

## Later wrapping world-map actors

Staging only the relevant story stage/selector before the original world entry
selects the actual later stream and grid, then original `01:CD61` allocates
the two `0598` records from `0A:F992`. Captured original VRAM gives positive
artwork in both animation phases. Selected-source observers leave the guest
captures unchanged.

Camera tests exposed an important state-coherence requirement. Changing the
live camera after loading left the original tilemap out of sync and produced
the yellow/cyan repeated tiles seen during the test. That failed state is retained
as a negative control. Staging the entry camera **before the original loader**
lets the game rebuild the map and graphics normally; the corrected picture has
normal terrain and both ship actors in the right margin. Original camera and
collision behavior are preserved by the presentation module.

The wrapping experiment admits only the checked scene-zero, stage-17 resource
tuple and two exact ordinary records. Unsupported allocations, large sprites,
active HDMA and unsupported raster/scroll states refuse the extension. It is
an interior view on a wrapping map, not a complete world-edge qualification.
The frozen candidate is
`6592943bd6a84e43a3a27c534d9563c7159c20da82e0573933330df7d9187444`.
Seventeen silent routes pass 224 guest comparisons, 32 composed-center checks,
27 complete displayed-packet samples and five startup refusals. An independent
packet-phase-aware decoder explains all 3,791 changed margin pixels. Left/right
views, real walking, collision refusal, cold load and actual in-process restore
are checked separately. These counts are finite checks, not campaign totals.

The exact final artifact also passes the existing 78 ordinary actor gates and
a paced Direct3D margin route at about 60.03 presentations/second, 0.782 ms mean
composition, with no measured steady audio underflow/missing-frame/overflow.
Raw large camera/packet discontinuities refuse until new lineage is established;
an actual crossing of the 3,584-pixel world boundary remains unqualified.
Original directional input also crosses the horizontal original sprite gate in
both directions. At that test position only the first ship's bottom raster row
is visible; this is a bounded gate crossing, not whole-ship/campaign coverage.

## Journal possession experiment

The separate journal experiment reads original item `40` (STARCREST) from both
32-byte inventory groups. Original lookup scans all slots; the reader does not
invent a completion event or retain a historical latch. The opt-in card describes
current possession and the inventory group, while absence retains the existing
stage-scoped David lead or no-lead card. Draw and frame updates derive the state
again, so restoration/removal cannot retain a future possession claim.

This remains separate from proving the original title-specific Crest award,
durable quest completion or a complete journal. Neither David's introduction
bit nor generic item insertion establishes those events.

The polished isolated candidate is
`97f86cde5c0391f22467256a62ff6f76576e69a4e8d1c180de995d1b02abe113`.
It passes 101 integration checks across 33 native processes and 199 tests of
the same inline predicate. Positive first/second/both-inventory cards, explicit
removal/compaction fixtures, cold load, a real in-process checkpoint restore,
restart and keyboard/indexed-SDL-virtual-controller toggles pass. Captured guest
state remains exact. Positive cards fit their heading and say "In your pack now";
outside their box the picture matches the original guest framebuffer. The
disabled/no-possession variants preserve canonical presentation. A finite
Direct3D/audio route also opens and closes the positive card through real SDL
keyboard events, holds about 60.03 presentations/second and passes thirteen
gates with no measured steady audio underflow/missing-frame/overflow. These
local measurements do not replace listening or physical-controller tests.
The original award and physical controller remain separate coverage.

## Build and evidence boundaries

After a matching canonical source build, the isolated helper also supports:

```powershell
python tools/build_experimental_b0.py --experiment wrapping --base-receipt "<source-build>/source-build-receipt.json" --rom "D:\My Games\Secret of the Stars (USA).sfc"
python tools/build_experimental_b0.py --experiment b0-travel --base-receipt "<source-build>/source-build-receipt.json" --rom "D:\My Games\Secret of the Stars (USA).sfc"
python tools/build_experimental_b0.py --experiment journal --base-receipt "<source-build>/source-build-receipt.json" --rom "D:\My Games\Secret of the Stars (USA).sfc"
```

The default remains the B0 experiment. Each variant freezes its authored input
hashes, copies into a new ignored build folder, preserves the baseline/runtime
and emits `compiled_unqualified_experimental`, `public_build: false`. Normal
Companion Setup refuses these receipts. Source compilation, staged execution,
original progression and installed release qualification remain separate claims.

Private checkpoints, dumps, captured art, audio and executable builds stay local.
This public repository includes authored source/tools and scope documentation.
