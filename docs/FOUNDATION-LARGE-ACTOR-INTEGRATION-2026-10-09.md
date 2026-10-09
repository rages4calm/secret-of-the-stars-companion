# Private B0 callback and PPU integration — October 9, 2026

This adds an isolated integration proof after installed native 0.1.8. **B0 is
still excluded from the player.** Qualified authored/live sources, installation
receipts, original ROM and owner saves/profile remain unchanged. The earlier
`FOUNDATION-LARGE-ACTOR-CONTRACT-2026-10-09.md` and its canary helpers remain
byte-identical for the historical 0.1.8 source package.

## Private implementation

`local/evidence/large-actor-integration-20261009/src/` contains exact copied
0.1.8 field/header sources and a modified actor source. It reuses the frozen
ROM-free B0 canary, rather than introducing another descriptor or coordinate
interpretation. The copy starts from actor C
`57456b84c79601f1ce3756b3caea6eb18923f777e0502e70fdef886866ae2d88`
and field C
`b58b866ebb82161a7ea6ecb3af0eb4402f69f8b910c420feb4dbfda2ee59d4ae`.
The private modified actor C is frozen at
`272452548f83cfb1de68fd3c50d37fb9e66314f6e42b0cdaa0c97f351baf3b77`.
The actor header and field sources are unchanged copies.

The private actor module registers the original seven ordinary producer seams
plus party `01:D989` and regular `01:DB68`. B0 records join the shared expected
and seen masks, while their metadata owns only fixed OAM slots 0/1. Ordinary
append/reserved objects retain their existing slots and cursor checks. Both
families must finish, the original complete staging packet must match, and the
same queued → START → COMPLETE → displayed packet carries the B0 state. The
actual field-resource eligibility checker and full 48-byte presentation resource
key remain required, in addition to the B0 helper's narrower key.

The original parked low-slot XY is checked at the party producer start. A
complete later B0 writer replaces earlier metadata; a partially culled same-slot
overwrite refuses the derived packet. It never appends duplicate fixed ranks.
The transfer guard retains all 544 bytes and the original channel/bank/address,
BBUS address, size, mode, direction and increment settings. Reset clears the
derived producer/queued/transfer/displayed states. A subsequent complete checked
producer and transfer can recover the metadata.

`FoundationWideActorsPrepareLine` supplies checked 16×16 objects to the existing
public `PpuSetExtraObjects` path. It uses current rendering VRAM and CGRAM,
original tile/palette/flip words, fixed virtual slots 0/1 and actual raster scroll
deltas. Ordinary 8×8 objects share that same private array with disjoint slots.
No guest OAM, actor activation, ROM, camera, collision or CPU budget is changed.

## Exact headless evidence

Final report:
`local/evidence/large-actor-integration-20261009/authored-checker-proof/report.json`
SHA-256:
`98e795882bd0c7a5db9c00dfcb6e10eb3adc5993a63b728e0dbe029ef7e32259`.
All eleven aggregate checks pass, covering **56 synthetic cases** and
**1,806,336 independently predicted margin pixels** with zero differences.

The harness captures the callbacks installed by the actual private module and
dispatches through those registered functions; it does not call internal
observer functions directly. It checks nine unique registrations and snapshots
WRAM, CPU, PPU and DMA inputs around callback calls to verify read-only behavior.
The bridge registration and DMA notifications are finite host adapters. This is
not guest opcode execution or actual DMA-engine transfer qualification.

For composition, it executes the real public `ppu_runLine` renderer. An
independent Python byte-plane oracle predicts the complete left/right margins
using original descriptor words and captured tile/palette inputs. Positive
cases cover party packed and regular world-camera coordinates, objects culled
from the original viewport, per-component boundary clipping, a complete
party-to-regular last writer, regular B0 record 18, ordinary-object coexistence,
current palette changes, horizontal/vertical raster deltas and reset recovery.

Brightness, a full OBJ window, disabled OBJ output and fixed add/subtract color
math produce independently checked pixel changes. The positive color-math
cases use an original descriptor with the palette classification bit set; cases
where that bit is clear explicitly show no effect from enabling OBJ math.
The whole margin is compared against isolated OBJ over the captured backdrop.
Background occlusion, overlapping OBJ priority, subscreen/half-color combinations
and arbitrary raster windows remain outside this finite oracle.

The authentic 256-wide source PPU renders separately. The harness stitches that
exact source center into its 400-wide result, as the qualified presentation
contract does. Every stitched center line matches. This does not assert that
the private margin PPU independently renders an unchanged center after its
native OAM is cleared.

Thirty requested refusals cover CPU bank/width/pointer/mask/descriptor and
duplicate capture, staging words/high bits/cursor, every START transfer setting,
missing START, complete-packet differences, altered COMPLETE settings, resource
changes, reset, feature disable and invalid displayed OAM/OBJ size. Public
line 0/225, null input/output and source/output alias calls also refuse. No
margin metadata appears before a completed checked transfer.

Five genuine existing ordinary-actor packet pairs (`start`, `edge`, `entered`,
`further`, `return`) are separately replayed against compiled exact 0.1.8 and
private sources. Their entire 400×224 outputs match in all five comparisons;
these prove preservation of ordinary host composition, not natural B0 behavior.
Both their observer contexts and transfer notifications are still host-replayed.
All protected original inputs, authored/live sources and owner profile/save
files have matching before/after hashes.

Earlier `proof-1`, `proof-2` and `proof-3` reports remain separate development
checkpoints. The final authored checker result above supersedes their counts.
Compilation emits existing warnings in the unchanged PPU runtime; no new
private actor/helper/driver diagnostics appear.

## Reusable authored checker and next qualification

New ROM-free files:

- `tools/check_foundation_large_actor_integration.c`:
  `9f4959c6f68bd8d43318ee10f29e7d632761a9594e44d45b16645383716a90f5`.
- `tools/check_foundation_large_actor_integration.py`:
  `5a4e1c3857ac72e278c9d11d084d123f0754a1db363d0dce4ba20e7d3a98121e`.

These contain test logic and source addresses, without original opcode bodies,
ROM descriptors, pixels, saves or art arrays. Derived fixtures/output remain
under ignored `local/`. The checker requires an existing private source set and
its copy manifest; it refuses a changed baseline source. A fresh output directory
is required:

```powershell
python tools/check_foundation_large_actor_integration.py --out local/evidence/large-actor-integration-20261009/fresh-proof
```

The parent's read-only fixture inventory is recorded separately in
`local/evidence/large-actor-natural-candidates-20261009.json`: 9,866 complete
WRAM files, 586 unique hashes and zero active-looking raw B0 party/regular
records. That describes only available fixtures. It does not establish that
the game has no B0 actors, or that every original scene was observed.

No natural B0 fixture is claimed or manufactured. Before player integration,
the private module still needs actual interpreter-hook and DMA-engine execution,
guest-state/center parity in an isolated game candidate, combined terrain/OBJ
composition checks and a genuinely reached original B0 producer. Audio, GPU
pacing and controller coverage would belong to that candidate's own receipt.
The installed 0.1.8 behavior and frozen package remain intact.
