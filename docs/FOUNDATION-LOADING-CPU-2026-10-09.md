# A bounded native loading-work contract

October 9, 2026. Read-only follow-up to the CPU work/wait observation and the
field-streaming contract. This identifies the original routines behind the
natural house-exit loading fields. It changes no executable, ROM, guest state,
checkpoint, profile or timing policy. Installation status remains in the newest
continuation and build receipt.

The concrete opportunity is native tilemap construction and a smaller VRAM-clear
loop. The inspected path does **not** establish a decompression bottleneck. Its
graphics uploader also consumes modeled DMA time, which must be distinguished
from CPU instruction work. CPU slowdown has not been eliminated, and this loading
assessment does not close the owner's visible scrolling report.

## Existing replay evidence

The qualified telemetry replay is `local/runs/cpu-budget-20261009-110303/report.json`.
Its executable SHA-256 is
`8d9a39a8a3ae189f10d9b9f4d3a1d5d3016e12510e9456d9d5ca1983924e4740`.
The paired observer-off/on town, battle and natural house-exit cases cover 2,934
fields. Each pair has identical six guest dumps and existing field traces, with
zero resume-ring evictions and no interpreter step-cap events. This qualifies
the read-only observer, not complete guest timing or physical display fidelity.

The town replay reaches the original `008414/008417` NMI polling loop in all 463
fields. The two-Red-Slime battle does so in all 2,244 fields. Those deadlines are
intentional waiting; this pair of fixtures does not show useful computation
missing the field deadline. Town camera updates remain one pixel per held field
inside its three movement legs. Other scenes and actor/stream synchronization
remain outside that measurement.

The 227-field house exit has 216 NMI-wait fields and the following 11 other
deadlines. They coincide with forced blank and brightness zero. Input is zero
and the sampled camera remains (32,144); mode remains 1. The next field, 18551,
returns to visible rendering, camera (128,320) and the measured NMI wait. Mode 1
alone is therefore not a sufficient field-ready predicate.

| Guest field | Deadline PC | CPU cycles | Master clocks | Inspected operation at that PC |
| --- | --- | ---: | ---: | --- |
| 18540 | `01CB2E` | 46,862 | 357,370 | VRAM clear word store |
| 18541 | `018199` | 25,019 | 357,494 | Graphics DMA loop, immediately after DMA trigger |
| 18542 | `01B714` | 15,212 | 357,232 | Conditional metatile attribute branch |
| 18543 | `01B280` | 44,917 | 357,376 | Streaming dispatcher, second-layer setup |
| 18544 | `01B55E` | 44,915 | 357,390 | Direct column loop, next cell |
| 18545 | `01B4F3` | 44,909 | 357,332 | Metatile-to-tile-word index calculation |
| 18546 | `008632` | 44,913 | 357,384 | Coordinate advance/wrap helper |
| 18547 | `01B50A` | 44,902 | 357,358 | Tile-word lookup before PPU write |
| 18548 | `01B520` | 44,893 | 357,360 | Next quadrant/index calculation |
| 18549 | `01B24F` | 44,901 | 357,380 | Streaming dispatcher, direct/queued path selection |
| 18550 | `008469` | 44,901 | 357,354 | Cooperative task-yield register-save prologue |

The original field budget is 357,368 master clocks. These are per-field totals,
not costs assigned to the sampled routine. The eleven fields occupy about
0.183 seconds at nominal NTSC field cadence; this is not the complete door/fade
duration or a predicted saving. The samples identify real multi-field loading
execution, but the last sample is already inside a cooperative wait. Calling all
eleven fields productive CPU overload would overstate the evidence.

## Exact original routines

Static inspection uses the unchanged clean USA ROM, SHA-256
`7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`, and the
local `snesrecomp/recompiler/snes65816.py` decoder. Bounded private disassembly,
decoder hash, input-report hash and the joined CSV rows are retained in
`local/evidence/loading-cpu-20261009/`. The decode tracks explicit REP/SEP width
changes and stops before identified tables. Inherited register widths and
callee effects still need a dynamic entry/return trace; this is not an exact
instruction cost profile or universal bank analysis.

### VRAM clearing: `01CB19..01CB34`

This small routine sets PPU increment mode `0x80`, writes VRAM word address
`0x4800`, selects 16-bit accumulator/indexes, then repeats a zero word write to
`$2118`, DEY and conditional branch. The count is `0x1800` words: 12,288 bytes
covering word addresses `0x4800..0x5FFF`. This includes the BG1, BG3 and BG2 ring
regions. The loop store is `01CB2E`; the original RTS is `01CB34`.

It is a direct clear, not decompression. At completion A and Y are zero,
accumulator/index widths are 16 bits, and the final DEY sets Z=1/N=0. The rest
of the flags, X, direct page, data bank, stack and exact PPU state must be checked
against a captured entry and return. Under the ordinary increment contract the
final VRAM pointer is `0x6000`.

### Graphics upload: `01813F..0181A3`

This routine disables HDMA and performs twelve DMA-channel-4 transfers, each
4,096 bytes, with mode 1 targeting the two VRAM data ports. Source choices come
from WRAM `0x4412 + block_index`. The twelve destination word starts are
`0000, 0800, 1000, 1800, 2000, 2800, 3000, 3800, 6000, 6800, 7000, 7800`.
Together they upload 49,152 bytes while leaving the tilemap area untouched.

`018199` is the index increment immediately after the `$420B` trigger. The low
CPU-cycle total alongside a full master-clock field is consistent with hardware
DMA time being charged. It does not attribute that entire field to slow CPU
computation, or demonstrate compressed source data. Keep these transfers and
their side effects/timeline in the first CPU proof. A later native resource
upload policy would need its own explicit hardware-timing decision.

### Initial map construction: `01D080..01D106`

The constructor sets `0x0531=0x80`, installs direct page `0x0B00` around the
`01B006` call, and repeatedly walks the selected original camera X by eight
pixels. It makes 34 producer calls, then restores the original camera and clears
`0x0531` and direction state `0x0408`. `01B006` is a trampoline to `01B1D6`.
The producer processes BG1 and BG2, requesting 30 tile words down a new column;
negative `0x0531` selects its direct PPU path `01B4B8`, rather than queue producer
`01B3A8`. The next capture should verify the actual constructor/caller and layer
call counts rather than assume them from deadline PCs alone.

The direct path `01B4B8..01B59B` sets increment mode `0x81` (32 words after each
high-byte write), resolves camera/map/quadrant state, and looks up tile words.
Its writes at `01B50C` go to the original `$002118` ports. Helpers split at the
32-row tilemap wrap and the 256-pixel map-segment boundary. Four of the eight
producer/helper deadline samples lie inside this routine; two are in its
dispatcher, one in attribute resolution and one in coordinate advancement.
This is a more substantial candidate than the small index arithmetic leaf,
although the samples do not yield an exact percentage of loading time.

The lookup hierarchy is the same map-segment/cell/metatile/tile-word hierarchy
already verified in [the field-streaming contract](FOUNDATION-FIELD-STREAMING-2026-10-09.md).
`01B59C` computes camera-edge coordinates and ring address; `01B65E` checks map
bounds, uses the SNES multiplication registers, resolves a segment through
`09B000`, and selects the cell. `01B6D4` splits the output at the ring boundary.
`00FF35` is an exact trampoline to coordinate helper `00861D`; its deadline
`008632` is a normal coordinate load, not evidence of a heavy arithmetic hotspot.

### Conditional terrain and task waits

`01B009` jumps to `01B704`. The attribute helper initially stores the selected
metatile in `0x0520`, then inspects the low nibble of its attribute. Selector
`0x0E` scans four-byte condition records through DP `$2F` and tests progression
bits at WRAM `0x53F9`; selector `0x0F` scans six-byte records through DP `$32`,
calls `01C40C`, and can substitute another metatile. The observed `01B714` is
the branch choosing that second path. Being sampled at its comparison does not
prove a conditional record was taken or a long scan occurred.

The two checked ready-Likado captures have no `0x0E/0x0F` selectors in their
recognized attribute table, so their simple full-map resolver is exact. Do not
silently extend that predicate to the loading constructor or another map:
capture the loading resource records, direct page and attribute identity first.
Preserve map-boundary, signed camera/wrap, progression and quadrant behavior.

`00FF03` jumps to `008461`, the original cooperative task-yield routine. At
`008469` it is restoring its data bank after saving flags/registers; it then
stores wait/task state and stack position before rejoining the scheduler.
This is not a candidate computation to remove globally. Earlier interactive
submenu failures are already evidence against broadly bypassing these waits.

## Smallest next implementation proof

Choose the VRAM-clear loop as the first narrow native-cost proof; follow with
the direct tilemap producer once its loading-state contract is captured. The
clear has a small, deterministic write footprint and explicit original return.
It is unlikely to remove all eleven blank fields. Promoting the whole loader
before qualifying its conditional terrain and temporary state would be a much
larger change.

1. Add opt-in read-only entry/return observations at `01CB19`, `01CB34`,
   `01D080`, `01D106`, `01B4B8` and `01B59B`. Record A/X/Y, P and mirrored
   M/X flags, D, DB, S, active return bytes, CPU/master clocks, original field,
   PPU increment/remap/pointer, constructor index, `0x0531`, camera and resource
   pointers. At the stores `01CB2E` and `01B50C`, record or hash the actual
   destination and accumulator word before the original opcode. Read WRAM/PPU
   directly for observation; avoid bus reads that mutate latches. Pair the
   copied house-exit trace off/on with identical dumps again.
2. Implement a game-owned original-cost clear equivalent, guarded by exact ROM
   and opcode identity, actual caller/stack contract, forced blank, A=0,
   16-bit widths and recognized VRAM pointer/increment/remap. Preserve every
   low/high port write in original order, registers, flags, bus/latch effects,
   refresh, device advancement and interrupt/deadline boundaries. Validate
   original-cost parity before reducing any guest CPU cost. Unknown context
   falls through to the interpreted original.
3. Only then add a separate opt-in reduced-computation-cost policy for that
   clear, retaining PPU-port and hardware time. Keep the original field duration,
   NMI/IRQ policy, DMA timeline, audio synchronization and world update pace.
   A continuation must be derived from restored guest Y and PPU pointer, not an
   unsaved native progress latch. Leave the original RTS in charge of returning.
   Do not simply charge the whole loop after it has crossed several fields.
4. Compare off/original-cost/reduced-cost replays. First require exact
   original-cost per-field state and port sequence. With reduced cost, require
   the same completed clear/producer output and matching semantic exit state;
   whole late snapshots may differ legitimately because input/audio/world time
   now align differently. Explain and bound those differences rather than
   treating them as an automatic parity pass. Capture copied mid-clear restore,
   cold restore and rollback; verify that the normal field/battle/menu paths
   retain their pacing. Count saved loading fields and separately test audible
   transition audio before any player default.

Existing title-owned seams avoid a shared runtime patch:
`interp_bridge_add_pre_opcode_hook(pc, callback)` composes callbacks, and
`interp_bridge_pre_opcode_redirect(0x01CB34)` can retain the original RTS once
the loop's exact completed state is established. Those mutation APIs belong
only in the future opt-in implementation, never in the read-only observation.

Use original PPU ports, not `memset(ppu->vram, ...)`. The live
`snes/ppu.c:3520..3550` write handlers update the VRAM pointer and notify text,
shadow and diagnostic consumers. A raw fill omits those effects. The existing
menu `DrainRowQueue` demonstrates port access but uses unpaced transfers for
its distinct menu policy; it is not a complete CPU timing template.
`cpu_state.c:786..812` offers paced write helpers, but they only add bus master
clocks and perform the normal write. They do not themselves charge CPU cycles,
instruction fetch/internal cost, refresh or full device synchronization.
The interpreter's accounting and synchronization at `snes/interp_bridge.c:2472`
and refresh handling at `common_cpu_infra.c:890` remain the reference contract.
Do not assume a paced call alone makes a long native loop interruptible.

The more valuable second proof can reuse the verified resource resolver for
`01B4B8`, but must preserve the original 30-word columns, two layers, temporary
DP state, signed/wrapped coordinates, attribute overrides, page splits and
actual port writes. It should optimize the lookup computation rather than
widening the guest ring or increasing world updates. Renderer-owned margins
remain a separate presentation feature.

## Limits carried forward

This establishes exact routine identities and a targeted implementation
contract from existing finite fixtures. It does not implement faster loading,
grant a global overclock, prove general combat performance, certify native AOT
coverage or remove visible movement lag. The independent-reference timing/NPC
differences and seven experimental AOT WRAM bytes remain unresolved. Star Fox
Enhanced remains a useful reference for separating logic pace from rendering;
its SuperFX-specific solution is not the timing policy of this SlowROM title.
