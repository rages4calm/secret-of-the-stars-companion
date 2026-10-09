# Likado actor visibility foundation — October 9, 2026

The initial read-only actor proof below now has a default-off diagnostic actor
side-pass implementation, qualified in a copied candidate at the end of this
document. The owner installation remains the qualified 0.1.5 build. No owner
ROM, save or settings were changed. Terrain reconstruction is already covered by
`FOUNDATION-FIELD-STREAMING-2026-10-09.md` and the Likado preview documents.

## Qualified copied proof

The authored inspector is `tools/inspect_foundation_actors.py`. It accepts
copied dump prefixes or an explicitly supplied diagnostic executable, guards
the exact clean USA ROM and nonwrapping scene-5 resource/layout contract, and
writes fresh private reports under `local/`. It never changes guest records.

Final report: `local/evidence/wide-actors-20261009-131537/report.json`.

- Executable SHA-256:
  `987554031d343fbc54e89b4fbc54e40058147aa6f26e75ee486391b4ff00c00e`.
- Copied east-town fixture SHA-256:
  `aabd365c8b4a64dd17cfec34476c8864c9a538a73e44b97c19aeab4bd9c0fa51`.
- Clean USA ROM SHA-256:
  `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.
- Inspector SHA-256:
  `221de666aa3d6b82d55b725cc29030bc362055daadb5136f897342acb2363772`.
- Script SHA-256:
  `08e48f3bdf60d9a571b312bc1b088d94070fc489e42afd3f9a5ed77c24aaff06`.

Three cases use the same frozen binary, copied fixture and bounded right/left
movement: no write observer, OAM-staging writes `2200..241F`, and actor-record
writes `4100..42DA`. All exit normally. Gamepads are explicitly disabled for
deterministic scripted input. Native loading, fast menus, battle HUD, journal,
enhanced pixels, frame art and wide rendering are off in these diagnostic copies.

Both observers preserve all ten WRAM/VRAM/SRAM/OAM/CGRAM/register/pixel snapshots,
the complete CPU scheduler trace and the field trace exactly. The scoped logs
contain 37,646 OAM writes and 1,662 actor writes; these are observation counts,
not counts of actors or new content. Source inputs retain their hashes.

The inspector reconstructs **144 regular actor pieces**, all exactly matching
current WRAM OAM staging. Five adjacent snapshot pairs link those descriptors to
the next field's actual PPU OAM: **72 of 72 pieces match**. This phase difference
is essential: current WRAM staging is not the current displayed OAM. Reading
current WRAM at host composition time without that lineage would introduce a
one-field pose/position error.

## Exact regular-actor route

Party and world actors have different contracts. `01:D8B1..D988` consumes five
18-byte party records starting at `7E:4000`, with screen coordinates. It does
not subtract the town camera. Do not apply town-coordinate rules to that list.

`01:DA56..DB2C` consumes **19 world draw records**, each 25 bytes, starting at
`7E:4100`. The first 17 use the regular four-piece constructor; the last two
have a separate output path. The checked fixture has eight active regular
records, inactive remaining records, one regular party member and no variable
sprite records. Special sprite index `00B0`, wrapping maps, effects and other
constructor families remain excluded.

| Regular record field | Meaning established here |
| --- | --- |
| byte `+00` | `FF` skips the record; captured active values `00..03` select pose/direction |
| LE word `+01` | World X in pixels |
| LE word `+03` | World Y in pixels |
| LE word `+05` | Base sprite descriptor index |
| byte `+08`, `+09` | Signed X/Y increments used by `01:C1C7..C213` |
| byte `+0F` | Observed task counter; still updates outside the draw rectangle |

The renderer adds signed offsets `0471/0473` and subtracts camera words
`02AD/02AF` at `01:DA9C..DAB4`. Both offsets are zero in the qualified captures;
`0407` is zero, so the map-wrap branches are not used. Intermediate coordinates
are 16-bit values, with signed interpretation for host placement.

The original vertical test `01:DAB8..DACD` accepts unsigned `FFF1..FFFF`
(-15..-1), or `0000..00EE` (0..238). Horizontal `01:DAD1..DAE6` accepts the same
negative interval, or `0000..00FE` (0..254). The comparisons run with **M=0,
X=1** on this regular route. The `BCS` rejection follows `CMP #00FF` at `DAE3`.
These are draw limits, not proven collision, spawning or task-activation limits.

After the gates, `01:DAF2..DB0D` selects the original graphics descriptor:

```
index = base + ((flags << 1) & 255) + (WRAM[0475] >> 7)
descriptor = ROM[0E:9800 + index * 8 .. +7]
```

`01:DB17` calls `01:DE2A`. That routine emits four 8×8 pieces at offsets
`(0,0), (8,0), (0,8), (8,8)`, with displayed Y equal to anchor Y minus one.
It ANDs tilewords with renderer scratch `DP+10` (`EFFF` in these captures),
preserving tile, palette and flip fields as the original path does. The XY word
store is `01:DE5D`; the tile/attribute word store is `01:DE65`. OAM staging starts
at `7E:2200`, and channel 7 transfers 544 bytes to OAM. Low X/Y and the packed
high X bits must remain distinct from signed host coordinates.

Exact clean-ROM code hashes are recorded in the inspector report:

- `01:DA56..DB2C`: `b994393e35f10f97885a1fa7e578e0b06e88569e81157062696aa42476f7eb8a`.
- `01:DE2A..DED2`: `d1b3bfb85e794507a5ac3454f32951a6e2aba4d67c669531db9ae6bbf3dc94b0`.

The render scratch dump at `0E1C` ends with pointer `7E:42C2`, and its loop
counters match the three draw lists. This supports render DP `0E00`; a future
pre-op observer must confirm CPU D/DB and pointer/register widths directly
before accepting that contract. The current inspector does not claim a full
register capture. Basic write logs report an interpreter resume tag; they are
not instruction PCs. Narrow halted copies provide the exact PCs below.

## Actor just beyond the original edge

Record **`7E:414B`**, list index 3, persists at world **(272, 208)** with base
sprite index **`0268`**. Its identity here is a scene-scoped runtime record;
its story name or permanent character ID has not been established.

| Captured field | Camera | Actor screen anchor | Original draw |
| --- | --- | --- | --- |
| 17527 | (-16, 112) | (288, 96) | Culled; inside the right 72-pixel margin |
| 17561 | (16, 112) | (256, 96) | Culled; inside the right margin |
| 17571 | (25, 112) | (247, 96) | Drawn by the original path |
| 17597 | (51, 112) | (221, 96) | Drawn; original task changes flags `01` to `03` |

Normal movement supplies both sides of the visibility transition. No record
was created, teleported or poked. The actor's counter at `415A` decrements while
the actor is culled, and its pose later changes through the original task.
Thus this particular actor is already present and active outside the original
viewport. Its omission is draw culling. This does not establish spawning rules
for other actors, distant map regions or other scenes.

Additional halted source copies are in
`local/evidence/wide-actors-20261009-131253/halt-evidence.json`:

- World X write to `414C`: `01:C1E0`, field 17525. The source adds sign-extended
  record `+08` to world X; it similarly adds `+09` to Y at `01:C1FD`.
- Counter initialization at `415A`: `01:C100`, field 17526, before this actor
  can pass the original draw gate.
- First matching edge actor XY write at `2250`: **`01:DE5D`, field 17563**,
  value `FE`. The edge ring records caller `01:DB17 -> DE2A`. Actor 3's anchor
  has reached X=254 and passes the original limit.

Those copies deliberately exit 42 before the selected write. They establish
source locations, not completed-state parity. `SNESRECOMP_WLOG_STATE` was not
used: its register formatter performs guest bus reads. The completed cases
above use only basic scoped logging and prove their separate parity.

## Original graphics identities

The actor is reconstructable before it enters the center. Its flag-1 phases
use descriptors **`0E:AB50`** and **`0E:AB58`**; flag-3 phases use `0E:AB70/AB78`.
For the initial phase, the four tile IDs are `C4/C5/D4/D5`, with original
masked attribute `25`. The tiles are already in VRAM and match unique exact
clean-ROM 32-byte original tiles at **`11:9880`, `11:98A0`, `11:9A80`, `11:9AA0`**.

The report stores descriptor hashes and 61 unique original tile-source IDs
observed across the bounded snapshots. IDs are only emitted for a unique exact
ROM match; ambiguous/mutable tiles receive a captured hash without a claimed
stable source. All derived pixels and raw records stay private. This is an
original-asset binding contract, not a replacement art pack.

## One next implementation contract

Implement a **default-off, renderer-owned regular actor descriptor cache** for
this exact Likado contract. A read-only pre-op observer at **`01:DAB6`** is the
smallest useful seam: coordinates are computed and active/special-record checks
have run, but both viewport gates are still ahead. The original instruction
and all subsequent work must execute unchanged. Use direct guarded host RAM/ROM
peeks, no guest bus reads/writes, redirects, spawn changes or CPU-budget changes.

Capture the record pointer/index, raw flag/base, world coordinates, signed
computed coordinates, camera/offsets, mask, animation phase and descriptor
identity. Confirm M=0/X=1, D/DB and the expected `DP+1C/1E` record pointer on
entry; reject any inconsistent context. Initially accept only the checked
first-17 regular records. Leave `FF`, `00B0`, last-two composites, party
screen-coordinate actors and variable/effect records on their original paths.

Queue this metadata with its actual OAM-staging epoch. Activate it only with
the corresponding completed channel-7 OAM packet; the five one-field links
are a test oracle, not permission to hardcode a one-frame delay. On reset,
state restore, scene/resource change or missing/incomplete packet, clear the
cache and wait for a qualified packet. Pending metadata must never leak into
the current displayed field.

Use original descriptor words and current qualified VRAM/CGRAM in a host
side-only PPU pass. Preserve the PPU's OBJ priority, palette, flip,
transparency, window and color-math rules. The existing `PpuExtraObject`
presentation API is a candidate, but its per-line palette/priority behavior
and epoch lifetime need explicit qualification here. Suppress native OAM
objects in that side-only clone rather than promoting parked entries. Assign
side objects monotonically in original record/piece order; do not insert them
into guest OAM or change guest sprite limits/overflow. Preserve the original
256-pixel center exactly, including crossing-edge pieces. Clip the additional
pass to X `[-72,0)` and `[256,328)` with the existing terrain's actual per-line
camera convention. Derive visibility from live records and piece bounds,
never from stale OAM bytes or generic moving-object heuristics.

The next bounded proof should use this same copied sweep plus an exact edge
sample at original X=254: require positive cached/drawn side-piece counts,
source descriptor agreement for `414B`, uninterrupted center pixels, exact
guest/CPU/PPU/OAM parity with the observer off, and smooth entry into the
original path. Add a copied cold/rollback check to prove cache invalidation and
packet reactivation. Start with this right-edge actor; left-edge actors,
composites, other maps and spawning are later separate proofs. No broad
campaign replay or owner playthrough is required for that next step.

Reproduce the read-only completed proof with:

```powershell
python tools/inspect_foundation_actors.py --capture --exe local/evidence/hle-loading-final-inputs-20261009-125100/final.exe
```

## Implemented candidate continuation

`native/foundation/src/foundation_wide_actors.c/.h` implements the guarded
observer/cache/side objects. `foundation_wide.c/.h` integrates it in private
margin pictures and resets the derived cache. Matching authored files are
mirrored into the live generated tree. Module C SHA-256 is
`04138ffed39872e052f3709c4cac5309ec665d1ecb9bbc921c0eaa392c97d729`.
Root-owned main/config/CMake and shared DMA observer changes supply its lifecycle
and completed-transfer notifications; no guest instruction is replaced.

The optional `ExperimentalFieldActors=1` setting and diagnostic
`SNESRECOMP_FOUNDATION_WIDE_ACTORS=1` enable drawing; default remains off. It also
requires the existing qualified Likado wide terrain path. Private CSV is
selected by `SNESRECOMP_FOUNDATION_ACTORS_TRACE`; tracing without drawing may
observe the cache while leaving the output unchanged.

The implementation confirms D=`0E00`, DB/PB=`01`, M=0/X=1, record pointer,
original caller and coordinates directly at `01:DAB6`. Begin/end hooks validate
the 19-record loop, and `01:DE29` checks every regular emitted piece against
the actual completed WRAM staging and allocation cursor. It queues the entire
544-byte packet with its producer metadata. The shared regular-DMA observer
notifies immediately before the first byte and after the last byte/channel
updates. Only channel 7, source `7E:2200`, mode 0, size 544, incrementing nonfixed
A-to-B port 4 is accepted. Source packet and actual PPU low/high OAM must match.
Reset/state application also clears the DMA observer's transient partial-start
state, so a restored partial transfer cannot activate abandoned metadata.

Each accepted line checks that its actual displayed OAM still matches the
activated packet. It unwraps that line's actual scroll around the captured
camera, reads the original four-piece descriptor words and current render VRAM
and CGRAM, and creates only pieces intersecting a margin and the current line.
The side clone parks its native OAM and draws those host objects through the
existing PPU object API, retaining priority, palette class, flips, transparency,
windows and color math. The original center pass is unchanged. A third private
pass is needed only on lines with margin pieces; changed margin pixels are
counted against the immediately preceding terrain-only picture. These pixels
are actual output differences, not merely cached or transparent source pixels.

The first compiled candidate is frozen at
`local/evidence/actor-wide-candidate-20261009-133803/candidate.exe`, SHA-256
`b88a6966bfe6c2a2df7a5a07e291c24f0db76366f712e793d7485c3477e96d8b`.
The independent authored checker `tools/check_foundation_wide_actors.py`
passes **all 75 gates** in
`local/runs/actor-wide-20261009-133859/report.json`:

- Sweeps with original and enhanced pixels preserve all checked guest snapshots,
  CPU/field traces and the composed center exactly; output differences stay
  in the margins. Original-width and copied-menu checks also pass.
- The original right-edge actor's tile/palette pixels match the independent
  art oracle. The checked X=254 crossing and original pose change both have
  positive actual rendered-pixel evidence.
- Producer metadata links to matching completed DMA epochs and displayed-frame
  metadata. CPU D/DB/M/X guards pass on the actual route.
- Copied cold resume and an actual state load at fixture step 96 clear derived
  state and reactivate only through a new matched completed packet. Source
  fixture/ROM/executable hashes remain protected.

The main sweep records 115 constructor sequences, 920 actor captures, 114
matched packet activations, **192 side pieces and 5,630 changed margin pixels**,
with zero rejected contexts. Those totals are for this one copied route, not
campaign actor counts. Startup correctly has an invalid cache until the first
newly produced packet completes. Drawing remains optional and bounded to the
regular actors/resources in this Likado proof; no spawning, collision, task,
CPU-budget, special-actor or campaign expansion is certified. Paced GPU/audio
and release installation remain separate root-owned checks.
