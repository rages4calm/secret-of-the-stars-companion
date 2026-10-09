# Shared field actor coverage — October 9, 2026

The actor cache now follows the original regular actor constructor instead of
assuming one party member and a fixed OAM start at slot 16. This is authored
candidate work. Installation and cross-scene qualification belong to the next
frozen executable receipt; the installed 0.1.6 proof remains historical evidence
for Likado only.

## Original constructor contract

Read-only decoding of the exact clean USA ROM establishes this sequence:

- `01:D80F..D829` sets original allocation byte cursor `046B` to `0030`, reserving
  twelve OAM slots. Draw flag `0401` selects the variable, party and world calls.
- With flag `0401=12`, `01:D862` calls the party list and `01:D86C` calls the
  regular world list. The variable constructor is not selected. Inactive or
  leftover `4300` effect records therefore do not determine this draw contract.
- `01:DE2A` reads allocation cursor `046B`, rejects allocation at `01F0` or
  above, emits four eight-pixel pieces, then advances the cursor by sixteen
  bytes. The world list begins at the cursor left by the party constructor.
- `01:D837..D847` sets the original descriptor mask to `EFFF` when `0400` is
  nonzero and `FFFF` otherwise. The candidate observes that original scratch
  value and applies the same mask; it does not change priority bits in guest OAM.

The source remains the first seventeen regular 25-byte records at `7E:4100`.
Inactive records, the two composite records, `00B0` descriptors, unexpected pose
flags or CPU context still reject the sequence. Every regular piece that passes
the original viewport gate must match the actual staging packet at its observed
allocation slot. Capacity exhaustion rejects the cache; it does not increase
guest OAM limits.

## Derived identity and rendering changes

Each candidate packet captures loaded tile/cell-definition pointers, both
segment-grid pointers, both attribute pointers, dimensions, actual scene
selector, wrap policy, renderer mask/route, and PPU object/background layout.
Mutable camera, task and animation fields are excluded from this resource key.
The key is checked through capture, completed DMA activation and actual raster
composition. A change between two eligible scenes clears pending and displayed
metadata; the cache must wait for a fresh matching completed packet. This is
important when the shared terrain eligibility admits maps beyond scene 5.

Rendering still delegates to `FoundationFieldSceneEligible`; the actor module
does not invent its own list of supported maps. Wrapping and nonzero sprite
offsets remain excluded. OAM priority rotation is also excluded. In the private
margin PPU, bounded virtual slots preserve regular constructor record/piece
order even when an earlier record was culled by the original viewport. The
actual observed slots govern staging validation; they are not repurposed as
world coordinates or written back into guest OAM.

The CSV retains its existing fields and adds `scene`, `start_slot`, `mask` and
`rotation`. Existing producer/DMA epoch identity, per-line original VRAM/CGRAM,
center preservation and restore reset remain required. No actor is spawned or
teleported, and no movement/task/collision/CPU timing is changed.

## Remaining coverage and next fixtures

This constructor-based generalization allows regular world actors to remain
available when original party rendering consumes a different number of slots.
It does not reconstruct party members themselves, special/composite actors,
effects or variable constructors. Party records use screen-space coordinates
and a separate phase/direction formula; applying the world camera to them would
be incorrect. Their own margin support requires an observed pre-cull producer
and completed packet lineage, including the alternate `00A8` and `00B0` paths.

Existing copied fixtures include `world-cave-a`, `cave-route-d`,
`cave-interact`, `likado-inside-a`, and the natural house-exit route. Cross-scene
qualification should pair actor-off/on on each eligible map, require actual
successful packets and positive rendered margin pieces where an actor exists,
and compare original center, WRAM, VRAM, OAM, CGRAM, SRAM and execution traces.
A transition between distinct eligible resource keys and cold/rollback restore
must prove stale metadata never becomes active. The prior Likado sweep remains
a required exact regression, including descriptor phase and X=254 entry.

Authored and live mirror C SHA-256:
`a3c87b76d9fb075c9cea31432af05499527ea4494ba6fcfafb4a63d00faee6a8`.
Header SHA-256:
`9cef473607a2ffbf9534d33d841eb041c1ae41a069a30f7f0833e54b6daed763`.
Standalone Clang syntax checking is recorded locally. Runtime coverage must be
attached to the frozen new candidate rather than inferred from this source check.
