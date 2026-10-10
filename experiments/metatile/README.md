# Original-cost queued metatile-index experiment

This excluded source-only prototype replaces eleven straight-line arithmetic
opcodes in the original queued scrolling-map builder. It is **experimental,
default off and not installed**. It preserves the original guest cost; it is
**not a slower-guest fix or a measured host-performance improvement**.

The [public build instructions](../../BUILDING.md) remain authoritative
for tooling and an owned clean USA ROM. No original game data is included here.

## Build from a frozen public build

First use `tools/build_public_foundation.py` to create a fresh source build from
your own ROM. Keep that build's project, CMake cache and source receipt intact.
Then, from this repository root:

```powershell
python experiments/metatile/build.py --base-build local/source-builds/<your-build>
```

The helper copies the receipt-verified project and its runtime into a new ignored
`local/experimental-metatile/<timestamp>` directory, adds this module to only that
copy, and compiles using the baseline CMake toolchain/SDL configuration. It does
not install, mutate the baseline, copy an owner profile or touch game data.
The output receipt explicitly says `experimental_compiled_unqualified`.
New baselines require their own gameplay checks.

Only a copied/disposable launch may opt in:

```powershell
$env:SNESRECOMP_EXPERIMENT_QUEUE_INDEX = 'original'
# Launch your copied experimental EXE with your owned ROM and copied state.
```

Unset the variable for the original interpreter path. There is no GUI setting,
production config key, automatic adoption or altered-cost policy.

## Exact seam and guard

The clean-USA interval is `01:B408..B419`, continuing at `01:B41B`. It loads
`0520`, masks the metatile to eight bits, shifts it by three, combines it with
twice the original direct-page quadrant word, and stores the index at `D+1B`.
The original attribute helper, tile read/queue store, queue cursor, column loops,
cooperative waits, DMA, collision and activation all remain in original code.
This interval contains no branch.

Every native opcode requires the whole original ROM SHA-256 and exact interval
bytes, native mode, 16-bit accumulator/index, decimal off, `PB=DB=01`,
`D=0B00`, original mode byte `0020=01`, visible PPU and scene `040E=0000` or
`0005`. Unsupported contexts return to the interpreter without a native bus
access or write. All input word bits use the original 16-bit wrap/flag semantics;
there is no arbitrary metatile/quadrant clamp.

Each opcode fetches its original bytes through the existing paced read API,
performs ordered original memory accesses, mirrors the flags, and commits once
with the original instruction cost. The complete interval costs **34 CPU cycles
and 262 opcode master clocks** in the checked SlowROM/WRAM context; these are
different units. Refresh and work outside the interval are not included in 262.
The bridge checks IRQ/deadline edges between every native instruction. No
instruction batching, uncharged ROM fetch, CPU budget increase or direct RAM
write is used. Reset invalidates the ROM binding; no new serialized progress or
cache is introduced.

## Bounded local evidence (2026-10-09)

The independent pinned interpreter oracle checks all **16,777,216** combinations
of eight-bit metatile and full sixteen-bit quadrant. The underlying loaded
metatile word also exercises every upper-byte value. It compares every opcode's
registers, flags, index writes, ordered byte bus reads/writes and cycles:
**184,549,376** per-op checks. Fourteen unsupported/begin-failure contexts refuse
without changing CPU, index memory or bus state.

A private candidate built from frozen native 0.2.1 replaces 2,112 opcodes in a
92-field world-edge route, 2,464 in a 184-field parked-vehicle walking route and
22,880 in a 310-field four-direction travel route. The 113-field world-loader
route remains original and performs zero replacements. Disabled-vs-baseline and
native-enabled-vs-disabled checks preserve seven captured guest surfaces
(WRAM/VRAM/SRAM/OAM/CGRAM/registers/framebuffer), field traces, total CPU/master
clocks, camera, deadline position and NMI wait timings exactly. Interpreted
instruction/cycle counters decrease by the replaced amount, as expected.
Copied save, cold resume and same-process restore also preserve those surfaces
and timings, with positive native execution after restore.

All visible fields in these finite original-path routes reach the game's NMI
wait; no productive visible CPU-budget miss is established. The world loader
has blank-screen map/DMA work and separate APU readiness/byte-acknowledgement
polls. A non-NMI deadline does not itself prove CPU overload. No campaign,
physical-controller, audible-audio, generic AOT or speedup qualification is
claimed. Private reports, original code dumps, game states and executable stay
outside this public directory.

## Host measurement: negative result (2026-10-10)

The frozen private candidate `1a7f5fe883e1a417778164c8c5165e5e99efab00321c883c43ac8aab81f912c3`
was measured with the native policy enabled versus absent, using the **same
binary** and copied profiles/checkpoints. Six alternating-order unpaced travel
pairs showed a median **2.48% higher guest-stage wall cost** with native hooks
(range 2.19–3.19%, about 0.048 ms extra per field). Four short world-loader pairs
with **zero native replacements** also showed a median 2.88% higher guest-stage
cost. Three paced Direct3D/audio pairs showed 2.56% higher guest-stage cost;
both policies held 60.010–60.014 fps with zero steady audio underflow, missing
frame and audible-overflow counter deltas in each seven-second steady window.
The capped frame rate does not establish a CPU improvement or waveform quality.

A separate unpaced diagnostic pair matched the travel measurement's **90,464
replaced opcodes / 8,224 complete indices** across 1,060 fields. Interpreted CPU
cycles decreased by exactly 279,616 while total guest CPU/master clocks,
camera/wait/deadline telemetry and seven before/after guest surfaces stayed exact.
The 113-field loader control replaced zero opcodes and retained the same parity.
Synchronous guest traces/dumps were excluded from the paced measurements.

The existing bridge linearly scans its registered pre-op hooks on every guest
opcode. Enabling this prototype adds eleven entries even on a zero-call route;
each native hit also synchronizes CPU state and restarts decoding. The measured
result supports testing dispatch lookup overhead first, while preserving the
ordered callback loop and every guest opcode boundary. Whole-process CPU
measurements include all threads and have coarse timing granularity; they are
corroboration, not a seam-local benefit measurement. These finite staged routes
do not cover the campaign or arbitrary host load. **Do not promote this current
prototype as a performance enhancement. Original guest budgets remain intact.**

## Separate experimental hook lookup filter

`dispatch-index.patch` is a host-only experiment against the exact retained
runtime bridge base SHA-256
`5c1308342c57f84e68e12160e8dc274ed4dbbf9b7e15e505aa71e7a0b11ac1de`.
It is excluded from the canonical runtime patch and installed binaries. Build a
fresh disposable copy with:

```powershell
python experiments/metatile/build.py --base-build local/source-builds/<your-build> --indexed-dispatch
```

The helper refuses a different bridge base, applies the patch only to its new
runtime copy, and records the before/after bridge and patch hashes. It retains
the ordinary source receipt and pin rather than declaring this experiment
compatible with a production profile update. A changed runtime patch changes
the declared execution-state ABI; existing update refusals remain authoritative.

The filter uses **1,048,576 bytes** of exact normalized-key presence plus a
**4,096-byte** page bitmap. Existing registration and lookup both normalize with
`pc24 & 0x7FFFFF`; the original high-bank alias is preserved. Empty pages and
absent keys skip the original linear scan. Present keys still use that same
ordered loop, including CPU synchronization, callback mutations, redirects and
per-op interrupt/deadline boundaries. Same-PC replacement, duplicate callback
handling and table-capacity behavior stay in the original registration code;
successful appends mark presence and clear-all clears both bitmaps. No guest
data, clock budget, opcode cost or serialized state is changed.

The lookup filter defaults on **inside this experimental copied build**. Set
`SNESRECOMP_EXPERIMENT_PREOP_INDEX=0` before launch to select the original scan
for paired diagnostics; `1` selects the filter. The metatile module's separate
`SNESRECOMP_EXPERIMENT_QUEUE_INDEX=original` opt-in is unchanged. This separation
lets the filter be tested with the original interpreter path and zero metatile
replacements. The current title-specific C/H and arithmetic oracle are unchanged.
The private filter candidate
`fe49401b01f80a64f76911549b6779f33a19de19540324dbc71917922cec5673`
passes 98 real-runtime guest/restore checks in 22 finite runs against the frozen
0.2.1 baseline. Four scene routes retain the seven guest surfaces and original
CPU/master/camera/wait/deadline telemetry. Saved checkpoints, cold resume and
same-process rollback remain exact, including positive native execution after
restore. Separate tests extract the actual registry and dispatch loop: both
filter policies pass 14 registration/order/alias/reentrant/redirect/capacity
controls and 8,388,608 normalized-key membership comparisons each. That isolated
test stubs CPU synchronization; the real-runtime checks cover it separately.

In 44 quiet-window timing runs using the same candidate and independent flags,
six unpaced index-only travel pairs reduced guest-stage wall cost by a median
**1.15%**, or about **0.022 ms per field** (all six favorable, range 0.84–1.72%).
Four pairs with the eleven metatile hooks present reduced that stage by 2.83%;
four zero-replacement loader pairs reduced it by 2.69%. Whole-process CPU is
corroboration rather than seam-local timing. With indexing already enabled,
adding the native arithmetic gave **no useful gain** (+0.35% median guest-stage
cost, mixed signs); the arithmetic prototype remains excluded.

Two paced index-only pairs had mixed guest-stage signs and a 1.34% higher median
whole-process CPU cost. They do **not** establish improved paced performance.
All eight paced runs held about 60.01 fps with zero steady audio-loss counters
in seven-second windows. These small host measurements do not change guest
timing, establish a scrolling fix, or justify an installed runtime/ABI update.
The original timing report retains 12 failed substring-based anchor checks from
truncated long-path breadcrumbs; a separate source-backed verifier confirms the
untruncated launcher's exact copied-directory success line in all 44 runs.
Other runtime gates and protected owner/input hashes pass. No results were
discarded or owner installation changed.

## Upstream credit

The native transaction and interpreter APIs come from the pinned
[SNESRecomp runtime](https://github.com/RetroPortingToolKit/snesrecomp) revision
`7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`, with this project's retained runtime
patch. Its `interp816` core derives from
[LakeSnes](https://github.com/angelo-wf/lakesnes), copyright 2021–2023 angelo_wf
and contributors, MIT. Existing repository and upstream notices remain in force.
This directory adds title-specific authored source and build integration;
it does not redistribute original ROM-derived generated code or assets.
