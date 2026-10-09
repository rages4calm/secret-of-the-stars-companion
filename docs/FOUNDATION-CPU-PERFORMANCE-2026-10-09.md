# CPU budget and gameplay slowdown assessment

October 9, 2026. The owner reported visible tearing and motion lag during the
downward leg of our Windows walk and asked for original SNES hardware slowdown
to be addressed, using Star Fox Enhanced as a reference. That observation remains
valid. A steady host frame rate alone cannot establish smooth motion or rule out
missed game updates. This assessment is read-only; it does not add an overclock,
change game speed, or claim that CPU slowdown has been eliminated.

Read this alongside the newest UI/presentation continuation. The launcher and
installed-build status belong to that continuation. The original CPU/reference
fidelity limits from the handoff remain open.

## The current execution budget

The title calls `snes_beam_frame_driver_run_frame()` from
`native/foundation/src/game_rtl.c`. The live pinned implementation is under
`local/native-proof/SecretOfTheStarsSNESRecomp/snesrecomp/runner/src`:

| Source | Concrete behavior |
| --- | --- |
| `beam_frame_driver.c:29` | Defines one nominal NTSC field as 357,368 master clocks: 262 lines at 1,364 clocks per line. |
| `beam_frame_driver.c:130` | Derives the next frame boundary from the beam's V=225 position, rather than a PC wall-clock duration. |
| `beam_frame_driver.c:150` | Delivers enabled NMI, then runs guest instructions against that field's master-clock deadline. |
| `beam_frame_driver.c:185` | A deadline ends this field's CPU work even if the guest is still doing productive work. |
| `beam_frame_driver.c:199` | Parked CPU time still advances the beam, APU and cartridge devices; parking does not grant extra execution. |
| `snes/interp_bridge.c:168` | Charges actual instruction/data/stack bus transfers at the shared address-dependent speed, plus six master clocks for each internal cycle. |
| `snes/interp_bridge.c:1662` | Interpreted whole-program execution yields at the first instruction boundary reaching the master deadline. |
| `snes/interp_bridge.c:2472` | Adds the instruction's CPU and master-cycle costs, charges refresh and synchronizes hardware clocks. |
| `cpu_state.c:354` | Shared CPU bus pricing uses six, eight or twelve master clocks per access. This clean game is SlowROM; the low-bank ROM accesses remain eight clocks. |
| `common_cpu_infra.c:890` | Models the DRAM refresh cost. DMA and hardware synchronization have additional costs, so CPU instruction counts alone are not the whole field budget. |

This preserves an original hardware-sized execution budget. Faster host execution
or promotion into generated C can reduce PC processing time while leaving that
guest budget intact. Consequently, original CPU-bound missed updates can survive
in this foundation. There is no verified title-specific overclock option in the
inspected execution path.

The driver also has a 1,024-slice safety bound, and the interpreter has a separate
step-cap bail. These are containment mechanisms, not desired gameplay slowdown.
A cap or an incorrect cooperative-wait detection would be a runtime correctness
problem and must be distinguished from faithfully reproduced SNES slowdown.

## What the watched fixture does establish

The existing copied-town walk is
`local/runs/scroll-pacing-20261009-102819/walk-enhanced/foundation.csv`.
It records the guest's BG1 scroll position after each simulated field. Inspection
of its continuous input segments gives:

| Input leg | Held fields | Successive camera deltas inside that leg |
| --- | --- | --- |
| Left | 90 | 89 of 89 are exactly (-1, 0) |
| Right | 160 | 159 of 159 are exactly (1, 0) |
| Down, the watched leg | 60 | 59 of 59 are exactly (0, 1) |

All three segments stay in field mode 1. This narrow downward leg therefore does
not contain a skipped **camera-coordinate** update between consecutive held-input
fields. This is a specific measurement, not a dismissal of the owner's visible
lag. It does not measure the time between physical input and display, establish
actor/world streaming synchronization, characterize other maps, or certify every
gameplay task's update rate. GPU presentation qualification is recorded separately;
it does not close the CPU budget question.

The earlier menu trace at `local/runs/menu-wait-trace/entry.log` demonstrates
several cooperative field tasks reaching the original `00FF03` wait entry each
field. Observed callers include `00A0D6`, `018099`, `0188A0`, `01B01C`,
`01C010`, `01D87B` and `01840D`. These addresses are useful task observation
points, not established semantic names. Their waits may be intentional pacing.
Do not bypass them globally: the prior submenu regression already demonstrates
that removing original waits can disrupt asynchronous producers/consumers.

## Star Fox's relevant lesson

The pinned [Star Fox Enhanced architecture](https://github.com/kandowontu2/starfox-enhanced/blob/43bece01fb876d9a5ddb5d2d9efc827ab32d8375/docs/ARCHITECTURE.md)
separates fixed 20 Hz game updates from interpolated presentation and retains
input presses until a game update consumes them. It is a useful model for
understanding game timing and then removing specific limits while preserving
pace. Its particular SuperFX/3D implementation is not a drop-in timing policy for
this SlowROM 2D title. Secret of the Stars still needs its own measured update
boundaries, camera/actor state and expensive routines. Increasing presentation
FPS, increasing game-update frequency and granting more CPU work within one field
are distinct changes.

## Smallest next observation, without a shared-runtime patch

Add an opt-in, game-owned diagnostic to the existing before/after-frame hooks.
It can use these existing read-only observer interfaces:

| Interface | Useful observation |
| --- | --- |
| `snes_beam_frame_driver_get_position(uint32_t *pc, uint32_t *wai)` | The frame-boundary resume PC and WAI state. |
| `interp_bridge_resume_total()`, `interp_bridge_resume_capacity()`, `interp_bridge_resume_get(seq, &event)` | Every recorded resume change, with guest frame, PC, stack pointer and named cause. Consume new records each field and report any eviction; the ring holds 1,024 records. |
| `interp_bridge_resume_site_name(site)` / `interp_bridge_resume_kind_name(kind)` | Distinguish `deadline`/`deadline_unwind` from `quiescent`, `stable_poll`, `wai`, interrupts and `step_cap`. |
| `interp_bridge_edge_total()`, `interp_bridge_edge_get(seq, &edge)` | Recent control transfers and folded repeat counts; useful for locating productive work or a wait. Folded counts are not exact whole-function coverage. |
| `g_cpu.cycles`, `g_cpu.master_cycles`, `interp816_insns_total()`, `interp816_cycles_total()` | Deltas per field, with CPU cycles kept separate from master clocks and parked hardware time. The interpreted counters are declared in `snes/interp816.h`. |
| `interp_bridge_add_pre_opcode_hook(pc, observer)` | Composable, read-only counts of validated task-entry/completion/wait PCs, with live registers and stack context. Already used by the title's diagnostic wait trace. Interpreter-only; future AOT bodies need explicit matching observation. |

`interp_bridge_lle_took_wai()` and `interp_bridge_lle_took_quiescent()` clear
their sticky state when read. A diagnostic must **not** call them and consume
information needed by the scheduler. Use the position and event-ring observers.
Do not set a deadline, redirect the PC or write guest state in this observation.

The existing diagnostic server exposes `resume_ring n=1024`, optional
`site=deadline`, `interp_stats` and `interp_profile` in
`snesrecomp/runner/src/debug_server.c`. Use a diagnostic build where that server
is enabled. These commands can inspect an existing run without changing timing
policy. `interp_stats` computes interpreted share from CPU cycles, not master
clocks; comparing CPU-cycle totals with master-clock totals would give a false
native-coverage claim. Per-field collection in title diagnostics is preferable
to a late ring snapshot for a finite performance proof.

Record field number, input, mode, resume causes/PC, task completion counts,
camera and verified actor position, guest CPU-cycle/master-clock deltas and host
guest/raster/compose/present durations together. Deadline yields alone are not
proof of slowdown: a deliberately busy polling loop can also reach a deadline.
Require evidence that a productive update failed to finish and that an intended
world/camera/actor update was missed or delayed.

Use a copied checkpoint immediately before a map transition/streaming boundary
or the first available dense battle effect, followed by a finite input script.
The existing two-Red-Slime checkpoint can establish a control, but it is not a
verified demanding CPU scene. Capture the genuinely demanding scene through
ordinary gameplay into its own fixture; never manufacture load by editing the
owner's progress. Include the watched town walk as a known camera-cadence control.

## Smallest enhancement proof after that measurement

If the missed update is tied to a costly productive routine, identify its actual
consumer and replace **one** understood computation with an opt-in native path.
First prove the original policy's data/write result and return contract exactly.
Then test a title-specific reduced CPU cost for that computation, leaving the
field duration, original NMI/IRQ and DMA/MMIO timing, audio timeline and intended
update cadence intact. That can grant the guest more useful work per field
without advancing extra world frames. Merely compiling the same charged cycles
faster does not prove removal of original CPU slowdown.

A generic overclock would require coordinated treatment of interpreter and AOT
costs, hardware accesses, interrupts, refresh, DMA and audio; there is no isolated
safe multiplier to turn on from the current source inspection. A bounded native
computation is the smaller first proof. If measurement instead finds intentional
low-rate movement or animation, higher-rate presentation requires a game-owned
camera/actor interpolation policy rather than pretending CPU budget is its cause.

Qualify original/off behavior, repeated on replays, copied cold restore and
rewind, a transition, unchanged movement distance over equal simulated time,
button edges, dialogue/menu pacing and audible audio. Trace the execution route
explicitly through interpreted/AOT/native code. Record which dropped update was
removed and which scenes remain untested before considering a player default.

The unresolved independent-reference timing/NPC differences and seven bytes in
the experimental AOT comparison still apply. This assessment adds a concrete
CPU investigation path; it does not promote that experimental AOT routine or
claim full game timing fidelity.
