# Map resource contracts for broader widescreen

October 9, 2026. Read-only foundation research. The installed 0.1.6 actor and
Companion receipts remain the authority for installed behavior; this document
does not itself install campaign-wide widescreen.

The new `tools/inspect_foundation_maps.py` preserves the historical Likado-only
inspector. It accepts the exact clean USA ROM and copied complete WRAM, VRAM and
register dump prefixes. Reports must go to a fresh ignored `local/` directory.
It never writes guest memory, ROMs, checkpoints, owner profiles or settings.

## Original data structures

The clean ROM SHA-256 is
`7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.
The tables below are ROM structures, not counts of distinct playable maps.

| Structure | Original table | Entries | Evidence for extent |
| --- | --- | ---: | --- |
| Scene selector pointers | `08:8000` | 337 uint16 | First/minimum pointer `82A2`, all records point to selector records through `87E2` |
| Segment-grid pointers | `09:9000` | 328 uint16 | First/minimum pointer `9290`, every record points into `9290..AF3E` |
| 256px segment pointers | `09:B000` | 1280 packed uint24 | First segment starts `09:BF00`, table consumes exactly `0F00` bytes |
| 32px cell-definition pointers | `0A:8000` | 16 uint16 | First record starts `8020` |
| 16px metatile-definition pointers | `03:8000` | 16 uint16 | First record starts `8020` |
| Metatile attribute pointers | `09:8000` | 16 uint16 | First record starts `8020` |

Live resources come from WRAM `0513/0516` (grid), `0506/0509` (cells),
`0500/0503` (metatiles) and `0537/055C` (attributes). The metatile and
attribute pointers must share the same original table index. Cell indices are
independent. Segment IDs must be below 1280, and their source record must have
64 readable LoROM bytes. Grid size must fit the span to the next distinct
original map-table pointer, or `09:B000` for the last grid.

WRAM `046D..0470` contains width/height in 256px segments. Original loaders
`01:C4C8..C4D6` and `C76D..C77B` decode those dimensions from nibbles, so legal
nonempty dimensions are 1..15 per axis, at most 480 by 480 8px tiles. Existing
128 by 128 Likado caches cannot represent the 14 by 14 overworld.

Attribute and definition tables can contain fewer than 256 entries. Validate
the metatiles actually referenced by the authored grid, plus boundary ID zero,
against their resource spans. A blanket scan of 256 attribute entries reads
past some original tables and rejects otherwise unconditional maps.

## Scene identity and transitions

`01:C91D` resolves the scene selector from `08:8000`. Selector records use
three bytes for an unconditional `FF` record, five for conditional selectors
0..6, and four for selector 7. The corresponding conditional dispatcher is at
`01:C969`, with targets `C981..CAA4`; selector 7 consumes one operand byte.

The selected primary stream begins with flags16, definitions8, map ID16 and
dimensions8. Loader `01:C464..C4D6` splits the definitions byte: its high
nibble chooses cells, its low nibble chooses metatiles and matching attributes.
The primary map ID is masked with `3FFF`. The secondary loader uses a separate
optional stream layout and opposite definition-nibble roles; the new inspector
does not claim to parse that complete optional stream syntax.

Compare the live primary resource tuple and dimensions against a possible
variant of the current original scene. An observed transition can already have
scene ID 5 while retaining house pointers, dimensions and a still-valid old
VRAM center. A center-word check alone would accept that stale combination.
Keep display readiness and resource provenance together. The inspector reports
possible resource links; it does not certify dynamic selection of every story
variant.

## Wrapping, parallax and inactive layers

Any nonzero WRAM `0407` enables the original wrap branches for both axes and
both layers. Loader `01:C5A8..C5AD` takes that bit from bit 15 of the primary
stream flags. `01:B071` maintains independent signed 16-bit camera words
`02AD/02AF` and `02B1/02B3`; the secondary velocity/fixed-point state and its
special modes are handled by `B106..B18E` and `C768..C7FB`.

Use each layer's own actual raster scroll, unwrapped relative to that layer's
guest camera. Do not apply the primary camera to a parallax layer. The inspector
uses the final captured PPU scroll latches, not an invented primary-camera
offset. Within-frame scroll journal replay remains a compositor integration
requirement.

Pixel wrap periods are `width * 256` and `height * 256`. Euclidean modulo gives
a bounded extra-margin extension for the inspected grid decoder, but the
original edge producer `01:B59C..B5E6` wraps the coordinate high byte once based
on its selected direction offset. Natural world-edge fixtures are still needed
to qualify those seams beyond the current interior world capture.

WRAM `050C/050D` marks active layer producers. The observed overworld has its
secondary producer inactive: its original tile ring is zero, while blindly
decoding metatile zero would produce `1F80`. Preserve the original ring for an
inactive layer; do not replace it with a reconstructed map or boundary fill.

## Conditional metatiles

Original `01:B704..B7AD` starts with the selected metatile ID in `0520` and
examines the low attribute nibble. Values below `E` preserve that ID.

The location key is `((worldX >> 4) & FF) << 8 | ((worldY >> 4) & FF)`.
For attribute `E`, four-byte records at the live `0453` pointer associate that
key with a 16-bit flag index; the table ends at key `FFFF`. A set bit at
`53F9 + ((index >> 3) & FF)`, using mask `80 >> (index & 7)`, replaces the ID
with 2. Otherwise the original ID stays.

For attribute `F`, five-byte records at the live `0456` pointer contain the
same key, a threshold, a selector and a replacement ID. The original condition
accessor is `01:C40C -> D375`. It reads stage byte `7E:5372` and selector-driven
bits/nibbles from `5360..`. The authored inspector implements those reads
without invoking the guest accessor or writing its scratch bytes `0443/0444`.
Replacement occurs when threshold is below stage, or equal stage with a true
selector value (selector `FF` accepts equality directly). Threshold `FF`
instead uses selector truth alone. Record scans are bounded before their
original 8-bit index wraps.

The implementation is derived from original instructions. The current positive
center capture only exercises an absent `F` record, preserving the base ID.
Matched `E/F` replacement branches and later story conditions need their own
positive native/original fixtures before a release claims them covered.

## Checked snapshot evidence

`local/evidence/map-contract-20261009-authored-proof/report.json` records these
six natural copied captures, with 9,856 active center tile words and no mismatch:

| Observed scene | Copied prefix | Primary grid | Dimensions |
| --- | --- | --- | --- |
| 0, overworld | `local/runs/presentation-20261009-125502/field-wide/dump/end` | `09:9518` | 14 by 14 |
| 5, Likado | `local/runs/sprite-limits-20261009-122344/town-1/dump/before` | `09:96A2` | 2 by 2 |
| 7, David's room | `local/runs/patch-david/dump/david` | `09:A302` | 1 by 1 |
| 12, house | `local/runs/status-original-control/dump/field` | `09:A2D8` | 1 by 1 |
| 38, opening house | `local/runs/sonya-talk/dump/sonya-talk` | `09:A2D8` | 1 by 1 |
| 39, island/outdoors | `local/runs/menu-fast-first/field` | `09:96A0` | 1 by 1 |

All six primary resource tuples match an original scene-stream variant.
All active secondary centers match too; the inactive world secondary is
explicitly skipped. Snapshots include hashes of the ROM, inspector, WRAM,
VRAM, registers and condition state. A prior local inventory scanned 8,056
copied WRAM captures and found twelve distinct raw tuples including title,
battle and transitions; duplicates do not increase the six observed scene IDs.

`local/evidence/map-contract-20261009-unaligned-proof/report.json` adds two
natural Likado actor-sweep captures at camera X 25 and 51. Each layer compares
33 by 28 words rather than omitting the partly visible rightmost tile; all
3,696 words match. The same code accounts for 29 rows when Y is unaligned,
though that Y case has not been positively sampled here.

`local/evidence/map-contract-20261009-transition-reject/report.json` is an
intentional negative proof: the transitional scene-5 `door` capture still
matches all 1,792 old house ring words, but its primary resources do not link
to any scene-5 variant. The inspector returns failure for that provenance
mismatch, demonstrating why exact center words alone are insufficient.

The world capture includes mosaic 3 and secondary-screen OBJ, so it provides
resource decoding evidence rather than qualification for a renderer that
currently excludes those states. The other five captures share the existing
Mode 1 layout: BGxSC `49/59/51`, character bases `0400`, main screen `17`,
secondary screen zero and no mosaic. Existing owner data was not changed.

Next integration gates are original-center pixel equality, guest-state parity,
cache invalidation during transitions/restores, actor packet/producer identity,
independent secondary-layer scroll, positive condition/edge fixtures and paced
GPU/audio checks. No hardware CPU budget, collision or actor activation is
changed by this resource proof.
