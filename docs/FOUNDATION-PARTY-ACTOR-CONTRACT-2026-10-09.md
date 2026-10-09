# Party and special field actor contracts — October 9, 2026

This is a read-only next-step assessment. No native actor, runtime, ROM, save or guest-state changes were made. Ordinary party members have a small implementable extension of the existing displayed-packet cache. The special and variable constructors require separate contracts; adding their records to the current 17-entry array would be incorrect.

Private original-source and fixture evidence is under `local/evidence/party-actor-contract-20261009/`. The clean USA ROM hash remains `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.

## Original constructor order

`01:D80F` initializes the producer. `01:D817` sets staging cursor `046B=0030`, so ordinary variable-length output begins at OAM slot 12. The four dispatch bits are consumed from `0401`: bit `04` selects the party call at `01:D862` to `01:D803`, which jumps to `01:D8B1`; bit `08` selects regular records at `01:D86C` to `01:D806/DA56`; bit `02` selects the variable constructor at `01:D858` to `01:D809/DC15`. Variable output precedes party output. `01:D870` calls `01:D80C/DDF8` to complete the packet.

The current `0401=0C` guard admits party then regular output and excludes variable output. The constructor has already drawn the party when the current regular observer begins at `DA56`. This explains the checked regular start cursor `0040` (slot 16): one visible ordinary party member consumed four pieces from slot 12. A party-aware cache must begin before that party call and append regular metadata afterward, rather than resetting away party metadata at `DA56`.

## Ordinary party layout and capture seam

The party loop increments its long WRAM pointer by `0012` at `01:D8C5`, starting at `7E:4000`. `01:D981` terminates after five entries. The CPU data bank remains `01`; the record's long-pointer bank is `7E`.

| Record byte | Original use |
| --- | --- |
| `+00` | Pose/direction selector; `FF` skips the record. |
| `+01` | X low byte. |
| `+02` | Y low byte. |
| `+03..04` | Base sprite descriptor index. |
| `+05` bits 0/1 | Ninth X/Y bits, extracted at `D8ED..D8F4`. |
| `+0A` bit 7 | Animation phase used by `D934..D93B`. |

These are packed screen coordinates, unlike the regular list's 16-bit world coordinates. At `D903..D915`, the constructor adds `0471` to X and adds `0473` to Y after subtracting one. The original unsigned gates accept `value >= 01F9` or `value < 00FF` for X / `< 00EF` for Y. They must not reuse the regular constructor's `FFF1` threshold.

For pose selectors 0–3, the ordinary descriptor is:

```text
0E:9800 + 8 * (base + 2*pose + (record[0A] >> 7))
```

`D93E` retains the carry from the preceding byte rotation, so this formula should stay guarded to the checked low pose range instead of generalizing arbitrary selectors. The descriptor supplies four words. The existing mask remains `EFFF` when `0400` is nonzero and `FFFF` otherwise. `D955` calls the same `DE2A` four-piece emitter as regular actors. Its original offset bytes at `01:DED3` describe `(x,y)` offsets `(0,0),(8,0),(0,8),(8,8)`; the Y subtraction has already occurred.

**The useful observation point is `01:D917`:** it is after both corrected coordinates are complete and before either clipping gate. Expect D=`0E00`, DB/PB=`01`, M=0, X=1, caller return `01:D865`, index byte at direct-page `13`, record pointer at `1C`, base at `1A`, and coordinates at `16/18`. Capturing only `D945` or the emitter misses culled party members. `D988` marks completion of all five entries. Metadata should remain derived host state and become displayed only through the existing exact 544-byte staging/DMA/PPU identity chain.

The original four-piece emitter checks cursor `<01F0` at `DE32`, advances it by 16 bytes, and appends the corresponding high-OAM byte. Validation must account for every visible ordinary party record in order, then confirm the regular constructor starts at that resulting cursor. Party pieces should have a stable order before regular pieces in the private margin pass; assigning both families the current `12 + record_index*4` virtual slots would create duplicate ranks. With only the ordinary families enabled, allocating five party ranks first and then 17 regular ranks fits within the existing 128-slot ordering space.

## Reusing the presentation seam safely

The existing per-line VRAM/CGRAM artwork decode, OBJ priority/windows/color math, completed-DMA promotion, exact packet comparison, resource identity and restore reset can be reused. A first proof can retain `0401=0C`, zero `0471/0473`, the existing nonwrapping actor gate and low pose range, while rejecting every special family below.

Packed X cannot simply be cast to signed nine-bit: X=300 belongs to the right margin, while X=500 represents -12. A 400-pixel viewport fits inside the 512-pixel coordinate period. Choose its representative around the original center (X=128; Y=112), then preserve the producer anchor and adjust only by the actual per-line primary scroll delta. Equivalently, select X in `[-128,383]` from the packed period; the requested `[-72,327]` span fits without ambiguity. This is a bounded presentation mapping, not a newly verified party movement or world-coordinate model. Nonzero offsets, wrapping-map motion, raster shifts and multiple naturally moving party members still need positive packet and pixel evidence before qualification.

## Special families remain separate

- **Party base `00B0`:** `D8DF` branches to `D989`. It uses descriptor `0E:9800 + 8*00B0 + 4*record[00]`, two large OBJ pieces with offsets from `01:DEDB` of `(0,0)` and `(16,0)`, and fixed slots 0/1 (`DA1D..DA28`). It builds high-OAM size bits explicitly and does not use the ordinary cursor. It does not follow the ordinary `0471/0473` coordinate path.
- **Party derived descriptor family `00A8..00AF`:** `D94D..D953` detects this family. It saves the ordinary emitter cursor, sets direct-page `34=01F0` and `38=021F`, calls `DE82`, then restores those cursors. Its four pieces occupy fixed slots 124–127, rather than ordinary append order.
- **Regular indices 17/18:** `DB13` selects `DE82` for these entries. The initial special cursor is direct-page `34=0010` with high-OAM pointer `38=0201`; these are reserved slots 4–11, not extra ordinary records after index 16.
- **Regular base `00B0`:** the comparison at `DA92` and jump at `DA97` select `DB2D`, using the two-large-piece family with actual world-minus-camera and wrapping adjustment paths. Its art/coordinate ordering needs its own proof.
- **Variable constructor:** `DC15` reads eight `7E:4300 + index*21` records, where byte 0 equals zero for inactive. It reads packed coordinate high bits from `+08`, X/Y low bytes from `+03/+05`, and a descriptor selector from `+06..07`. `DC7A` resolves a pointer through `0F:D800 + 2*selector`. The resulting stream has size/control state, row counts, signed offsets, tile words and control opcodes `F0..FF`, including pointer and size changes at `DDBD`. It emits individual pieces and pads the final high-OAM group at `DD84`. A fixed four-word descriptor decoder cannot represent it.

These findings establish constructor interfaces, not campaign identities or special actor names. No positively displayed special/variable fixture was found in the bounded sample.

## Existing natural fixture evidence and limits

The targeted inspector sampled the first and last WRAM capture in opening/journal fixture namespaces: 39 captures. It hashes each input and records the exact paths in `party-fixture-report.json`. No constructor-enabled sample has more than one active party record. The intro snapshot `local/runs/clean-to-outdoors/dump/part0-aftera.wram.bin` contains five identical non-FF records, but `0401=08` disables the party call; it is explicitly separated from a positive multi-party fixture.

Five already existing adjacent Likado producer/scanout pairs under `local/runs/actor-wide-20261009-133859/sweep-on/dump/` independently match all 20 ordinary party pieces at slots 12–15 against the next actual PPU packet. The independent decoder uses the party record's own phase and packed coordinates. This supports one-member original OAM lineage; it does not demonstrate offscreen party margins or multiple moving members.

Source span hashes in the private receipt are `5f86c37d4166cc559688ce331987ed4133118f5f1b60099dc28d58f95ac55c65` for `01:D8B1..DA55`, `f4db63b437669e0cc40ec4d893d7b37b258068d85a0740febc11cc4f716cecfe` for `01:DC15..DDF7`, and `d1b3bfb85e794507a5ac3454f32951a6e2aba4d67c669531db9ae6bbf3dc94b0` for `01:DE2A..DED2`. Linear disassembly is retained privately; branch joins and M/X state were interpreted against the original instruction bytes for the contracts above.

The next implementable proof is an ordinary-party observer joined to the existing packet lifecycle, with original one-member OAM parity and host-synthetic culled/second-member negatives and positives clearly identified as synthetic. A natural second-member fixture is still needed for campaign qualification. There is no need to change guest activation, spawn followers or widen guest OAM to implement this presentation seam.

## Isolated ordinary-party metadata prototype

The next implementation is confined to ignored
`local/evidence/party-actor-prototype-20261009/src/foundation_wide_actors.c` and
its copied header. Authored/live/installed 0.1.7 files remain frozen. Private C
SHA-256 is
`6c30df2bae22d446b727c987b78139f3dcf4a9998dc51a260007223cf49134ed`;
the copied header remains
`9cef473607a2ffbf9534d33d841eb041c1ae41a069a30f7f0833e54b6daed763`.
This is a reviewable prototype, not an installed capability.

The observer begins at D8B1, captures ordinary records before clipping at
D917, and verifies five-record completion and the original emitted cursor at
D988. DA56 retains party metadata and checks the exact party-to-regular cursor.
The cache contains five party ranks followed by 17 regular ranks, giving unique
virtual ordering slots 12..99. Staging validation uses the original party
clipping threshold 01F9 and its already-subtracted Y, then the existing regular
threshold FFF1 and its original Y subtraction. Every actually emitted ordinary
piece must match original staging before the complete 544-byte packet becomes
queued; its actual completed PPU packet still governs displayed metadata.

Party animation phase comes from each record's own +0A byte. The margin mapping
chooses the 512-period representative around original viewport centers X=128 and
Y=112, retains that producer anchor, and adjusts only by actual raster scroll
delta. X=300 remains +300 and X=505 becomes -7. The prototype adds an explicit
nonwrapping actor guard rather than relying on the generalized terrain resource
gate, and rejects an aliased source/private PPU. B0, derived A8..AF, higher pose,
reserved regular records 17/18, variable route, nonzero sprite offsets and unknown
resources remain refused.

`local/evidence/party-actor-prototype-20261009/host-proof-2/report.json` passes
24 bounded host-replay cases. Five existing adjacent natural producer/scanout
pairs accept one ordinary party member plus eight regular records each, with
all original staging bytes equal to the actual next PPU packet. The original
party pieces remain centered in every natural sample: **no natural offscreen
party margin or enabled multiple-member movement is established**.

Two explicitly synthetic positives cover two members at right X=300 and left
X=505, and a per-record phase that differs from the global regular phase. The
two-member case yields three margin pieces on an intersecting raster line;
moving the host scroll by two yields the independently expected X=298/306 and
X=-9/-1 pieces. Seventeen requested refusal cases cover special families,
unsupported pose/route/wrap/offset/PPU layout, invalid CPU context/record pointer,
wrong masks, a visible staging word mismatch, resource transition and incorrect
party/end/regular cursors. Successful cases additionally exercise line bounds,
source alias, stale packet, incomplete DMA and restore invalidation.

The private helper verifies 114 observer calls leave its CPU, WRAM and source
PPU unchanged. All genuine input files, original ROM, prototype proof sources
and authored/live actor files retain their pre-test hashes. The helper compiles
the actual current field-resource checker and PPU sources, but invokes observer
seams and DMA notifications through synthetic host scaffolding. It does not
execute the new hooks in a guest runtime, prove per-pixel composition, grant CPU
cycles, activate followers or alter an owner save. Root's separate isolated
integration build must establish actual guest-hook execution and original/wide
center/state parity before any promotion of this prototype.

## Actual isolated guest-hook qualification

Root copied the frozen private source into the separate
`local/evidence/next-private-integration-20261009/project` build, preserving the
authored/live/installed 0.1.7 sources. Its corrected 0.1.8-prototype executable is
SHA-256
`e156f0d29a1abc477a7c2517d8982e10de14ae6f71149adb422d1d0ead1c7150`.
The earlier initial copy retained an old modification time and was not rebuilt;
its baseline-only result is not party-hook evidence. Root refreshed the isolated
copy timestamp, rebuilt the actor object and froze the corrected executable.

`local/runs/party-live-hooks-20261009-corrected/report.json` passes 78 existing
actor/guest/center gates on the corrected binary. Root's separate authored
`tools/check_foundation_party_lineage.py` adds 21 positive party lineage gates
in `local/evidence/party-live-lineage-20261009-first/report.json`, including
621 actual party captures and 614 displayed party frames across sweep,
enhanced sweep, menu, cold restore and rollback. New party hooks execute at the
documented original seams, with D=0E00, DB=01, M=0, X=1 at capture; party completion
retains the original cursor before regular capture and completed-packet display.

The short additional paired suite at
`local/runs/party-map-transition-20261009-private/report.json` passes 50 gates
and 154 composed capture comparisons on the same corrected executable.
It checks scene 12 house, scene 5 Likado and their natural transition, preserving
all captured guest files, full CPU/state/field traces and the original center.
Positive packet identities occur in both scenes and invalidate during loading.
The private dynamic trace checker records 349 additional actual captures and
346 displayed frames in
`local/evidence/party-actor-prototype-20261009/actual-hooks-house-transition-report.json`.
The private earlier town-only augmentation remains explicitly failed on its
required scene 12 coverage gate; the new house/transition run supplies that
missing positive provenance. No coverage gate was waived.

The read-only feasibility receipt is
`local/evidence/party-actor-prototype-20261009/offscreen-feasibility-report.json`.
All 37 constructor-enabled original snapshots from the previously targeted
sample use packed party coordinates (128,112). Across 970 positive capture
observations in the five root routes and three additional routes, the corrected
producer coordinates remain (128,111). None places an ordinary party piece in a
margin. These observations can duplicate locations and guest frames; they are
not a campaign count or proof that offscreen ordinary party is impossible.

A future natural margin proof needs a genuinely reached scripted or additional
ordinary record with side-overlapping coordinates and the same complete packet
identity. Extra walking by the checked first-stage lead does not provide it in
these routes. No followers are activated, actors spawned, checkpoints edited or
owner campaign requested to manufacture that evidence. The two-member/offscreen
and raster-shift positives remain synthetic, and special/reserved families remain
separate from this frozen prototype.
