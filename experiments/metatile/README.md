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

## Upstream credit

The native transaction and interpreter APIs come from the pinned
[SNESRecomp runtime](https://github.com/RetroPortingToolKit/snesrecomp) revision
`7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`, with this project's retained runtime
patch. Its `interp816` core derives from
[LakeSnes](https://github.com/angelo-wf/lakesnes), copyright 2021–2023 angelo_wf
and contributors, MIT. Existing repository and upstream notices remain in force.
This directory adds title-specific authored source and build integration;
it does not redistribute original ROM-derived generated code or assets.
