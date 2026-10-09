# Combined presentation integration experiment

Historical experiment snapshot: the guarded combined policy is now integrated
into native 0.2.1. Read [current release](../../docs/FOUNDATION-INTEGRATED-RELEASE-2026-10-09.md) for new exact-build checks and world-edge fallback evidence.
The experimental build receipts described below remain excluded from normal Setup.

This isolated candidate combines the exact qualified actor experiment sources:

- `../b0-travel/foundation_wide_actors.c`: SHA256 `eed0b34c27987999afd42e98e662887fb4d69015028bfa181dad6bd2bc1aee5f`.
- `../wrapping/foundation_wide_actors.c`: SHA256 `8f42a5caad4f01c40be1ada05d8f5c6c39865178238ce82081b5c0e041d16867`.

The merged actor module SHA256 is
`69348ed2de92fe69fc3b4cb73e6cf84c504979b2cde8d0df729840ec4476eb7a`.
The separate inputs are unchanged. This module is excluded from the canonical48
inputs and is not installed. Companion Setup must refuse the experimental receipt.

## Contracts retained

Nonwrapping ordinary actors retain their original constructor, clipping, resource
and complete544-byte OAM packet checks. The B0 contract remains nonwrapping only;
its original body slots0/1 and exact mode82 center-only A8 proxy slots124–127,
cursor save/restore, packet words and size bits remain those of the travel module.
The proxy contributes to original packet identity and never receives side drawing.

The separate wrapping path accepts only the selected scene0/stage17/grid252
resource and its two original0598 ship records. It retains exact original wrapping
gates, raw emitted coordinates, complete-DMA promotion, displayed descriptor/phase
binding, actual OBJ VRAM/CGRAM and exact original-center preservation. It refuses
active HDMA, other wrapping allocations, wrapping B0/A8, high/composite poses,
changed resources, rotated OAM and unqualified packet/raster discontinuities.

`LargeBegin` intentionally refuses wrapping states. The combined observer skips it
for the strict ordinary wrapping family and explicitly refuses wrapping large
captures; the B0 contract itself is not relaxed. Actual3584→0 edge timing remains
unqualified, and stale camera/packet jumps beyond±8 are refused. See the separate
[wrapping contract](../wrapping/README.md) and
[travel contract](../b0-travel/README.md) for their bounded provenance.

The trace retains the original columns and appends packet camera, two regular
descriptors/phases and a SHA256 of the immutable displayed544-byte packet. Current
queued WRAM staging may describe the next packet during movement. Qualification
uses the packet actually completed into PPU OAM, rather than substituting the
current guest animation phase.

## Build

Create a matching canonical source build following [BUILDING](../../BUILDING.md),
then run from the repository directory:

```powershell
python tools/build_experimental_b0.py --experiment combined `
  --base-receipt local/source-builds/YOUR-BUILD/source-build-receipt.json `
  --rom C:/private/clean-usa.sfc
```

The helper freezes the authored components, copies matching generated source into
a fresh ignored build, includes the existing large-actor canary source/header and
the declared combined journal modules, and preserves canonical source/runtime and
owner profiles. Generated code, ROM, states and extracted graphics are not public.

## Qualification status

The exact combined binary is
`23e3fdb43ab277b18d7c91004f4e07e7e9a8fe6a06a4e67ba283a02a036cc38b`.
Its focused wrapping integration repeats all 12 checks on 17 silent replays:
224 exact guest comparisons, 32 exact composed centers, 27 bound complete-packet
samples, five correctly refused startup samples, 28 reconstructed original emitted
pieces and 3791 independently decoded changed margin pixels. Actual original
walking crosses the horizontal actor gate both directions on the second staged
approach; that ship is visible only on bottom raster row223. The first approach
stops at original mountain collision. Cold rebuilding and an actual pad-save/
pad-load restore retain the original state and rebuild packet-derived metadata.

Positive private report:
`local/evidence/combined-staged-20261009/final-assessment-report.json`, SHA256
`03aafa694c98e9c0172369ecefa7cd4332eb5055e2654e484388743b503cecc0`.
Separate negatives add eight silent replays, 84 exact guest comparisons, 60
auxiliary diagnostic comparisons and 12 exact centers. Original stage0 wrapping,
wrapping partyB0 and wrapping partyA8 produce no qualified actor packet or margin
pixels. The retained postloader-camera mismatch can form a real packet but the
compositor refuses its tilemap mismatch and adds no actor pixels. Negative report
SHA256 is `906c9ff35e6cb2b023f1afb1e539fd803ad9009f0f82a637c283bc362736b17d`.

The same exact binary also passes the separate existing 78 ordinary actor gates
and four finite Direct3D/audio routes: parked B0 margin, wrapping ships, Algos
travel, and the staged journal. Those routes run at about60.03 presentations/second
with zero measured steady underflows, missing samples or audible-buffer overflow.
They are recorded separately under `local/evidence/combined-staged-20261009/`;
they are not additional silent fixture counts or physical listening certification.
The separate staged journal integration on this binary passes 101 checks plus
199 inline-predicate checks. It examines all64 inventory slots, both inventory
groups, current STARCREST presence/absence, removal/compaction, missing lead and
different stage, keyboard and an SDL virtual controller, cold/in-process restore
and reset. It retains guest parity and the existing host card bounds. This is
current mutable possession, not an observed acquisition event, permanent quest
completion or a historical journal. The private report is
`local/evidence/combined-staged-20261009/journal-final/report.json`.
The complete travel-body/proxy proof is reported separately in the continuation
receipt. Results from standalone binaries do not certify this combination.

Developer fixtures use owner-authorized disposable progression and saved entry
camera staging **before the original loader**. They retain original actor records,
graphics, collision and constructor/DMA code. A postloader live-camera jump is a
preserved negative case because its tilemaps do not match the new camera. Staged
proofs do not establish natural chapter progression, acquisition, actual world-edge
timing, all actor/resource families, the full campaign or physical-controller use.
