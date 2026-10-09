# Native loading proof and checkpoint cursor repair

October 9, 2026. Version 0.1.3 continues the approved Likado terrain preview.
The release receipt records installed status and all report paths. Executable
SHA-256: `6a25f32924e6511a0a0c732135fa8e6ce06b46c41876aa77d2f70d047cfc255a`.

## What changed

`foundation_clear.c` provides native equivalents of three instructions at
`01CB2E`, `01CB31` and `01CB32` in the original loading clear. A natural house
exit performs 6,144 zero-word writes to VRAM `4800..5FFF`, replacing 18,432
interpreted instructions. Original setup and RTS still execute. This is direct
clearing, not decompression or a replacement of the map loader.

Each native instruction fetches through the original bus, writes through the
original PPU ports and commits its original cost. It returns to the scheduler
after every instruction, preserving deadlines, interrupt checks, DRAM refresh,
device advancement, audio-flush progress checkpoints and open bus. There is no
raw VRAM fill, batched world update or unsaved native cursor. The small shared
runtime transaction API centralizes existing accounting; it is qualified for
this title's bounded clear, not arbitrary native opcodes.

Guards require exact clean USA ROM/opcode identity, native 16-bit CPU widths,
A=0, DP `0900`, bank 1, the observed task/caller stack, scene 5, forced blank
and matching VRAM pointer/increment/remap. Unsupported context executes original
instructions. Progress derives from restored guest Y and PPU port state.

`NativeClear=1` in `foundation.ini` opts into this original-cost proof. Absence
or 0 keeps the original route; new player profiles default to 0. Existing owner
preferences are preserved. Original View disables it for that launch. The
diagnostic equivalent is `SNESRECOMP_FOUNDATION_NATIVE_CLEAR=original`; normal
launch strips diagnostic environment variables.

## A restore defect exposed by the proof

The first cold mid-clear comparison appeared identical, but its replacement
count was zero. Generic PPU snapshots omit VRAM access latches, and the runtime
execution residue preserves OAM latches without the VRAM cursor. A cold load
therefore restarted the clear with pointer zero; in-session rollback could
inherit a later pointer. Native guards correctly refused this inconsistent
state. Matching two fallback runs was insufficient certification.

Title checkpoint schema v3 now stores eight explicit bytes for VRAM pointer,
read buffer, increment, remap and high-byte increment selection, alongside the
existing audio clock and CPU/beam state. These restore directly as serialized
hardware state without causing PPU writes. Invalid port encodings reject in
preflight before applying a snapshot.

Guarded v1/v2 checkpoints remain accepted and are never rewritten on load.
Their missing VRAM cursor is not generally reconstructible; the old mid-clear
fixture remains compatibility/fallback evidence, not faithful continuation.
New v3 partial clears actually resume natively. Old binaries reject the new
schema, so previous executable and save copies remain in installation backups.

## Evidence

`local/runs/loading-20261009-120404/report.json` qualifies the final artifact in
seventeen copied cases:

- Clock helper refactoring and the read-only observer preserve original guest
  snapshots, field traces and complete CPU traces against version 0.1.2.
- Native execution preserves every 93-column seam row, seven guest snapshot
  payloads and CPU/scheduler timing; exactly 18,432 interpreted instructions move
  to the native route.
- A v3 partial clear restores Y=1,830 and VRAM pointer `58DA`. Cold continuation
  replaces 5,490 instructions and matches the uninterrupted original run at the
  later guest field.
- Same-process save/rollback replaces 23,922 instructions, reenters the partial
  clear and matches uninterrupted continuation from that saved state. Overlay
  closure resets observer epochs without guest changes.
- Copied valid increment-32/remap-1 states execute zero native instructions and
  match the original path exactly. An actual v2 partial checkpoint retains its
  old route and matches the older executable.

Costs remain STA 5 CPU/36 master clocks, DEY 2/14, taken BNE 3/22 and final BNE
2/16, plus existing 40-clock refresh where due. The loop retains 61,439 CPU
cycles and the original field budget. Instruction counts and individual
concurrent headless durations do not establish a host speedup or saved fields.

`local/runs/loading-desktop-20261009-120530/report.json` pairs natural exit and
v3 partial continuation off/on with copied owner settings. All four Windows
runs initialize actual Direct3D 11 VSync, capture identical enhanced 512x448
pixels/guest snapshots and produce nonzero SDL callback PCM by 0.272 seconds.
This is not physical controller, listening or monitor scanout certification.

The same artifact passes existing virtual-controller/overlay, menu-clipping,
fast-menu dialogue/battle, HUD, journal rollback, terrain-wide, presentation,
CPU observer, audio and checkpoint gates. Rejection tests now include a
checksum-valid invalid VRAM-port encoding. Launcher/desktop, settings migration,
isolated Likado preview and protected installation reports are recorded in
`local/evidence/build-receipt.json`.

## What remains

Normal launch retains original CPU timing and default-off native clearing.
This fixes new checkpoint continuation and establishes an exact execution seam;
it does not shorten loading or close scrolling lag. Most execution remains
interpreted. Prior AOT WRAM and reference timing/NPC differences remain open.

Next is a separate reduced-computation-cost clear policy, retaining port/DMA/
device timing and measuring saved loading fields. Do not silently change the
global CPU budget. The larger subsequent target is direct tilemap construction:
two observed constructor calls use transient layer resources, so ready-Likado
identity alone cannot qualify their lookup. Capture conditional attributes and
original 30-word column writes first. Do not broadly remove cooperative waits.

The approved terrain preview stays separate and limited to Likado BG1/BG2.
Actor visibility outside the old viewport, other maps, replacement HD art,
further verified journal events and a compatible MSU-1 driver remain future
work. Preserve ROM/save/settings hashes and use copied fixtures.
