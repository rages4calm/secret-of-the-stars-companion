# Original sprite offsets in widescreen — native 0.4.5

Compatible ordinary party, NPC and bounded variable-effect margins now support
the original signed sprite offsets0471/0473. Companion remains0.3.6. The42-page
guide, town tracking, map, controls, optional Original View and QoL remain.

## Coordinate ownership

Original D906/D912 applies offsets to party screen coordinates; DA9F/DAAD
applies them before ordinary camera subtraction. DC64/DC6C applies them to
effect anchors before original descriptor resolution. Capture follows these
operations. Original camera updater B071 also consumes the offsets.

Signed offsets belong to immutable producer epochs copied through queued,
full544-byte DMA and displayed packets. They remain stable during capture,
effect/ordinary join and seal. A displayed predecessor keeps its own offsets
while the guest produces its successor. Offsets are separate from loaded
resource identity. Ordinary margin positions add displayed offsets once before
raster subtraction; captured party/effect positions receive no second addition.
Terrain and periodic camera authentication retain their original transforms.

The original center, collision, activation, descriptors, clocks and pace remain.
Nonzero large/travel families, ambiguous anchors and incompatible layouts retain
fallback. Existing caps and packet/resource/raster refusals remain.

## Focused evidence and limits

New offset-only actual-C/PPU controls pass29 cases/406,474 checks in optimized
and UBSan builds, with322,560 independent margin comparisons per run. These
synthetic producer inputs are separate from original-engine evidence.

A strictly staged coherent original-loader checkpoint executes original DC15,
DCF7, ordinary producers and DMA. Two finite ten-frame actors-off/on runs have
equal original centers and final guest/PPU/clock dumps. Frames3/6 each show146
independently decoded effect pixels with zero mismatches. Persistent staged
offsets advance the original camera: frames9/10 trigger1/4 center tile-word
refusals and retain the original guarded picture. This diagnostic geometry is
not natural effect acquisition or a campaign/art-role claim.

Actual keyboard and explicitly indexed virtual-controller journal openers,
Guide navigation and closure pass. Scripted guest button navigation is separate
from SDL opener delivery; no new physical-controller certification is inferred.
A separate300-frame D3D11/VSync/audio route measures59.95FPS with zero steady
underflow, missing-frame or audible-overflow deltas. Startup2drops remain scoped.

Native SHA-256: `f31a0cacfcda4bc53119526a6c79a5203533c6d045a801472bf70806cab30b4d`.
Immutable compiled_unqualified receipt: `43d2a857d789a3f16719dd41bf8d7b3ea817e9d2b0b69f7893320fda57cdea4e`.
62authored native inputs;13runtime patches and declared execution ABI unchanged.
Qualification is a separate report. Full native/AOT execution remains unfinished.
Campaign verdict belongs to the owner/play testers; exhaustive replay is not a
release gate. ROM-free downloads include launcher/source/credits; owned ROM and
development tools are required to build the native game. Discord: chrono.trigger.
