# Scene 0 wrapping actor contract — October 9, 2026

This is a focused read-only assessment of the installed 0.1.8 authored actor/map sources and exact original instructions. It changes no native/runtime module, installed artifact, save or earlier receipt. Continue from `FOUNDATION-ACTOR-RESOURCE-RELEASE-2026-10-09.md`. The installed actor observer still explicitly refuses any nonzero `0407`; wrapping terrain support does not imply wrapping actor support.

Private evidence is `local/evidence/wrapping-actor-contract-20261009/`. The independent `inspect_wrapping.py` reads exactly six current release namespaces: `world-off`, `world-on`, `world-enhanced-off`, `world-enhanced-on`, `warm-entry-off`, `warm-entry-on`, all under `local/runs/actor-resource-wide-20261009-final`, plus one historical `presentation-20261009-125502/field-wide/dump/end` effect capture. It checks original record/descriptor/OAM arithmetic and input hashes; it does not execute guest routines or compose actor pixels.

## Exact ordinary constructor behavior

Scene 0 has primary dimensions14×14 and periods `Px=3584`, `Py=3584` pixels in all 23 inspected dumps. Loader `01:C5A8..C5AD` shifts the original primary stream's flag high byte and stores its former top bit into `0407`. Any nonzero byte enables the regular constructor's wrapping gates. Secondary dimensions4×4 do not set regular actor periods: `DA56..DA64` loads `046D/046E` into direct-page `30/32` as `width<<8`, `height<<8`.

The producer setup `D80F..D84E` establishes ordinary cursor `046B=0030`, reserved cursor `34=0010`, high-OAM cursors and the original `EFFF/FFFF` descriptor mask, then reads actual constructor bits from `0401`. `D862→D803→D8B1` calls the party constructor when bit04 is set; `D86C→D806→DA56` calls regular records when bit08 is set. A retained scene selector 0 alone is insufficient when those bits or the active field presentation are absent.

Party records remain five 18-byte records at `4000+18*i`. Their packed screen coordinates are:

```text
partyX = byte(+1) | ((byte(+5)&1)<<8)
partyY = byte(+2) | ((byte(+5)&2)<<7)
DP16 = U16(partyX + 0471)
DP18 = U16(partyY - 1 + 0473)
```

`D917` is after these calculations and before clipping. Party gates accept `v>=01F9` or `v<00FF` for X / `v<00EF` for Y. They do not read `0407`, map dimensions or primary camera words. The low pose/own-record phase descriptor contract and party-A8/B0 distinctions remain those in the separate party/large-actor documents. Applying the 3584-pixel world period to party screen positions would invent extra party copies.

Regular records remain nineteen 25-byte records at `4100+25*i`. The existing `DAB6` preclip seam sees:

```text
DP16 = U16(record.worldX + 0471 - camera02AD)
DP18 = U16(record.worldY + 0473 - camera02AF)
```

The exact unsigned original regular gate, independently on each axis, is:

```text
Gate(raw,stop,period,wrap):
    if raw >= FFF1: accept
    a = raw
    if wrap != 0 and raw >= 8000: a = U16(raw + period)
    accept only if a < stop
X: stop=00FF, period=width<<8
Y: stop=00EF, period=height<<8
```

Y uses `DAB8..DACD`; X uses `DAD1..DAE6`. This is one conditional addition, not general Euclidean modulo. Small negatives−15..−1 pass before any addition; a positive raw value beyond the original viewport is not corrected. Most critically, the added period remains **only in accumulatorA for the gate**. Neither path stores it back into `16/18`. `DAE8` reloads raw `18`, subtracts1 and stores it before constructing the ordinary descriptor. Thus physical emitted coordinates are raw X, raw Y−1, not the corrected gate accumulator.

`DE2A/DE82` emit four8×8 pieces using `DED3` offsets `(0,0),(8,0),(0,8),(8,8)`. They write X modulo 512, Y modulo 256, descriptor/mask words, and original X-high/size 0 bits. They emit one four-piece instance per accepted record; no world-seam OAM duplication occurs here. Ordinary records 0..16 consume `046B`; indices 17/18 compact into reserved slots 4..11 via `34/38`, independently of `046B`. BaseB0 branches before this index distinction; its separate large-actor work is outside this assessment.

For scene 0,3584 is divisible by 512 and256. Example rawX=−3580: the gate tests4 and the emitter's raw X also stores X9=4. This congruence is not universal. For an odd width 1, period 256 and rawX=−252: the gate tests4 but the raw emitter stores X9=260. Replacing raw coordinates with gate accumulators would change original OAM in that case. A first wrapping proof should qualify scene 0's exact14×14 resource rather than relax every wrapping map simultaneously.

## Camera and actual raster lineage

Original primary camera update is `01:B071..B0E2`. It accumulates the guest velocity/offset and fractional carry into `02AD/02AF`. With wrapping enabled it tests the updated high byte against `046D/046E`. An out-of-range high byte is replaced by0 for a nonnegative step, or dimension−1 for a negative step; the low byte remains unchanged. This follows the original bounded step, not a general arbitrary-value modulo operation. Secondary camera/parallax calculations remain separate and must not supply regular actor positions.

The current observer captures producer camera at `D8B1` and promotes immutable metadata only through the complete staging packet and the actual started/completed544-byte OAM transfer. Presentation also requires the actual PPU OAM packet, resource identity and restore generation. These contracts must carry forward unchanged.

Current nonwrapping presentation chooses the nearest10-bit primary scroll image relative to the displayed packet's camera. That alone is unsafe across a scene 0 world seam because3584 is **not** divisible by 1024. Host arithmetic example: producer camera3560 followed by wrapped camera0 and scroll latch0 makes the existing nearest-latch formula choose3072, although the actual wrapped camera is0. There is no natural seam capture for this example.

A proposed seam-safe private design must authenticate the actual wrapped camera associated with the current raster, then resolve that line's10-bit latch relative to that wrapped reference. Compute packet-to-line camera displacement separately using the map period. For old3560 and current0, the short periodic displacement is+24. Do not require a continuous image3584 to have the same10-bit latch as wrapped0: their low10 bits differ by 512. Current mutable camera words may help authenticate raster positioning, but must not replace the displayed packet's actor records, pose, phase, mask, activation or transfer identity. Actual latch/camera ordering at a seam and party translation need original positive route evidence before this proposal becomes qualified behavior.

## Proposed bounded private margin policy

Start with exact selected scene 0 resources, dimensions14×14, `0407=1`, route `0401=0C`, zero `0471/0473`, ordinary low-pose records and the existing complete-packet observer. Validate original clipping with the exact accumulator-only equations above while validating staging from raw emitted coordinates. Preserve compact reserved and ordinary append order. Do not change activation, collision, guest budgets, OAM or the original256-pixel picture.

For regular margin geometry only, consider periodic images of immutable world coordinates relative to the authenticated primary line camera:

```text
x(j) = S16(worldX - lineCameraX) + j*3584
y(k) = S16(worldY - lineCameraY) - 1 + k*3584
piece positions add original0/8 offsets
```

Select only images intersecting the private strips `[-72,0)` or `[256,328)` and rows`[0,224)`. The final compositor continues copying the exact original center. This is renderer-owned margin geometry, not a rewrite of the original gate or physical OAM packet. A positive raw seam distance that the original gate rejects must not be repaired in the center. Restrict the first proof to authenticated world coordinates in the selected map's range; do not silently modulo arbitrary16-bit record values.

At this 400-pixel canvas, a 3584-pixel period permits at most one relevant image of an ordinary piece. It needs no extra object capacity or duplicated guest entries. Shorter future map periods could place several images in the canvas and require explicitly bounded instance storage, stable virtual priority ties and duplicate suppression; that is a separate extension. Party positions use their packed 512-pixel screen representation rather than world-map images. Their producer-to-raster correction at an actual world seam remains a proof requirement; use neither the world period to duplicate them nor an inferred world position to replace their original screen bytes.

Keep party derivedA8, either family's B0, unsupported high/composite poses, variable4300 records, rotated OAM, alternate OBJ size/bank/layout states and ambiguous/incomplete transfers refused. Existing field eligibility already excludes effective mosaic sizes above1, unsupported modes/SETINI/main-screen layouts and invalid selected resources. For a first wrapping positivity route additionally require no unqualified HDMA/raster/control changes, zero sprite offsets and unchanged VRAM/CGRAM source lineage. Do not claim every effect is currently rejected by the installed observer merely because the proposed private proof excludes it.

## Read-only positives and next qualification

All23 inspected dumps retain scene selector 0 and primary14×14 dimensions. Only 10 are actual ordinary field samples with `0401=0C` and Mode1 encoding9. Their camera is1728,1760. Each has a genuine centered party 0 at packed128,112 and ordinary regular 0 at world1824,1776, base 04F8, producing screen96,16 before Y−1. All **80 original party/regular piece comparisons** match staging, the complete544 staging bytes match actual PPU scanout, and append end slot 20 matches `046B`. Protected input/source hashes match before and after. Other snapshots retain selector0 during different constructor/presentation states and are not counted as field positives.

None of those 10 samples adds a wrap period in an original gate, crosses a world edge or has a natural actor in a margin. The existing right32 sweep does not change the field camera; its left sweep then leaves the eligible context. It does not prove free traversal or an offscreen actor route. The historical sample carries mosaic byte 03 with size nibble 0 and is excluded here by its constructor context, not by a fictitious effective-size effect.

The known copied `likado-loop-exit-a` world fixture can support a bounded interior positivity attempt: capture adjacent producer/scanout pairs, move in short 8-frame orthogonal steps to avoid the blocked rightward path, and stop on a changed scene, constructor route, battle or effect. Seek regular 0 beyond the original horizontal viewport while still intersecting a private strip. Use dedicated fixture/save directories and hash-protected originals. This route is proposed, not executed; it would qualify ordinary wrapping-enabled interior metadata/pixels, not a global world seam.

For the unobserved edge cases, a host canary should replay the actual registered observer and DMA callbacks using genuine record/descriptor resources with clearly labeled synthetic coordinates. Include rawX/Y−15,−16,−3584+4,255/239, positive3584−4, camera steps3560→0 and0→3582, both map axes, actor-seam image choice, odd-width counterexample refusal, one/both reserved members, packet epochs, restore, offset/control/resource transitions and malformed captures. Compare independent original gate decisions and raw OAM pieces; use synthetic overlap pixels only to qualify ordering. A later original guest seam fixture is still needed for timing/raster and actual center/margin pixels. Existing natural records make that canary grounded, but do not turn its mutated coordinates into campaign evidence.

ROM SHA-256: `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`. Private inspector: `8ed330f210f4c81e9dab8bdfd347f75772d4ca3dde3ba941d5ee7fe7dc8356c5`; report: `9e58f4499136477ddc0c41c98b7fe33b868eef030e9355106b0997faf95a2cad`; bounded original disassembly: `5569e927d9631721aee3a449637b9633ae132574c8a6d30b71ab1c886d483714`. The report contains exact original-span hashes and all read input hashes. No installed wrapping-actor claim follows from this assessment.
