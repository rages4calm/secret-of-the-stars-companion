# Opening journal, CPU work observation and field asset identities

This continuation supersedes the UI-repair release for current source/build
status. Read the original handoff and porting references for preserved decisions.
The authoritative executable hash, qualification reports and installation state
are in `local/evidence/build-receipt.json`.

## First playable journal scope

The native journal card has a single verified opening-chapter lead: seek the
Crest of Stars; David places it somewhere in the mountain. Press **J** or click
the **left stick** to open/close it in the field. It starts closed. Select+left
stick retains the existing host launcher chord. The journal is a nonmodal lead
card: viewing it does not pause gameplay or consume the game's menu buttons.

`Journal=1` is the optional player setting in `foundation.ini`; an explicit
existing `Journal=0` remains off. Original View disables it for that launch.
Keyboard hotkeys work with a controller-only gameplay source. SDL watches queue
only atomic requests; guest state changes remain owned by the original game.

Content is derived from original stage byte `0x5372` and the first David
introduction bit `0x5360 & 0x40`, only in stage zero. Before that event, or in an
unsupported chapter, the card says no lead is recorded for this chapter. It does
not reconstruct a historical journal or infer Crest completion. There is no
unseen mountain identity, next destination or fabricated completion milestone.

Checkpoint load and reset close the card and discard queued hotkeys. Drawing
re-derives the lead from current restored guest state, including when no new
guest update has occurred yet. No native seen-event history, external journal
file or checkpoint schema change was added. Later stages need their own verified
events; crest acquisition remains unverified.

The earlier [event assessment](FOUNDATION-JOURNAL-EVENTS-2026-10-09.md) records the
source/capture basis. Its statement that no journal existed describes that earlier
assessment. This continuation adds the bounded card implementation, rather than
claiming campaign-wide quest tracking.

## CPU measurement that does not change timing

`SNESRECOMP_FOUNDATION_CPU_TRACE` enables a private per-field CSV. The title reads
CPU and master-clock counters, interpreter instructions/cycles, resume causes,
evictions, frame-boundary PC/WAI, camera and input. A guarded read-only observer
at the original NMI polling site measures useful execution before the first
poll and counts waiting iterations. No CPU budget, guest data, deadline, MMIO,
audio clock or control flow is changed. Ordinary player launch clears these
diagnostic variables.

Paired copied town, battle and natural house-exit fixtures must produce identical
guest dumps and existing scene traces with observation off/on. The house exit
includes loading-blank fields, so observation covers a real map transition.
Counters distinguish CPU cycles from master clocks; interpreter CPU-cycle totals
are not mislabeled as interpreted master-clock coverage.

The first measurements show town/basic battle deadlines repeatedly inside the
original `008414/008417` NMI-bit polling loop. That is intentional waiting, not
proof that useful work overloaded the SNES CPU. The transition additionally
contains multi-field loading work during forced blank. Those routines are a
more concrete target for a native loading/decompression proof. The original
execution budget remains intact and CPU slowdown has not been eliminated.

The stronger paired observation covers 2,934 fields with exact guest dump/trace
equality, zero event-ring eviction and no interpreter step-cap failures. Town
enters the NMI wait after a median 115,672 master clocks (32.4% of a nominal
field), with a maximum 239,494 (67.0%). Basic battle reaches it after a median
82,472 (23.1%), maximum 251,378 (70.3%). These are elapsed clocks before that
specific wait, not a claim that every preceding instruction is useful work.
All town/battle fields in those fixtures reach that wait. The transition has
216 wait fields and 11 deadline fields coinciding with loading forced blank.

Read [the CPU assessment](FOUNDATION-CPU-PERFORMANCE-2026-10-09.md) for the safe
native-work proof and broader coverage limits. The owner's visible scrolling
report remains valid; current measurements do not certify physical scanout or
rule out guest slowdown in other scenes.

## True widescreen and HD foundation

The field-streaming investigation identifies the scene map, segment, supertile,
metatile and tile-word hierarchy behind the visible town. Exact reconstruction
against captured VRAM establishes source identities and explains why sampling
the old tilemap's outer columns gives empty/stale scenery.

The next rendering proof should build an independent read-only side-column
cache from those records. Increasing the original queue sizes would alter
asynchronous guest rendering behavior and is a separate, riskier step. This
continuation does not enable the existing experimental wide mode. Stable graphics
block identities also support a future live HD asset binding; no replacement
HD artwork is installed by this step.

The [field-streaming contract](FOUNDATION-FIELD-STREAMING-2026-10-09.md) and
`tools/inspect_foundation_field.py` reproduce 3,584 center tile words exactly
across both layers and two camera captures. Full-map word caches agree across
camera positions. The extra right nine columns contain 224 missing/stale words
out of 252 per layer. Seven 4KB graphics blocks retain exact ROM identities; the
last block changes and needs its animation dispatch identified. These are source
identity/cache proofs, not a live widescreen compositor or HD replacement.

## Qualification and preserved limits

Use the latest receipt for results. The journal proof includes original guest
parity, actual composed cards, real SDL keyboard/virtual-controller input,
natural David introduction, unrelated dialogue and copied cold restoration.
Other-stage rejection is a pure predicate unit check, not later-story gameplay.
Physical controller operation is not newly certified by virtual-device tests.

Version **0.1.1** is qualified and installed. Executable SHA-256:
`8d9a39a8a3ae189f10d9b9f4d3a1d5d3016e12510e9456d9d5ca1983924e4740`.
Installation receipt: `local/evidence/player-journal-cpu-release-20261009.json`;
hash-verified backup: `local/owner-backups/journal-cpu-release-20261009-110802`.
Saves, original/working ROMs, graphics/sound settings and bindings were preserved.
Only the missing `Journal=1` enhancement setting was appended. A copied profile
cold-runs installed bytes with Direct3D 11/VSync=1, audio and enhanced journal
pixels. No owner progress was executed or advanced.

The natural introduction, unrelated dialogue, cold restore and actual same-process
save/load rollback pass on the final build. Rollback removes the later lead from
restored earlier progress. Interactive rewind across that story event and a
physical controller test remain outstanding; reset/restore logic is shared,
but that is not a substitute for those tests.

The prior menu repair, original-view route, guarded v1/v2 audio checkpoints and
synchronized GPU presentation remain. All reproduction uses private copied
fixtures. The owner ROM, latest progress and existing bindings are protected.
Most execution remains interpreted; prior experimental AOT WRAM and independent
reference timing/NPC differences remain open. Actual HD art, populated live
widescreen, compatible MSU-1 music and broad campaign coverage remain outstanding.
