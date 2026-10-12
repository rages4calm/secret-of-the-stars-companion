# Native descriptor and VRAM instruction regions — 0.4.9

Existing source-certified stack-neutral instruction bodies now execute inside
the original per-instruction scheduler. The collector reuses faithful typed IR
for known E0 PC/M/X, including direct-page penalties, decimal ALU, width and
flags, byte/word stores, cached RMW and explicit control transitions. Original
opcode/operand data masks, exclusions and forced-original entries remain.
Unknown modes, unresolved or prefix transitions, stack-changing instructions,
calls/returns, interrupts/wait and the existing indirect-Y page-cross residual
retain their original execution. No callable roots or return certificates were
added. Each accepted instruction fetches and commits once; original scheduler
hooks, deadlines, IRQ, producer progress and resume bookkeeping retain ownership.

The sixteenth ordered runtime patch changes three backend files. All previous
fifteen patch hashes are unchanged. Cache format8 / region metadata2 records
5,325 source-generated mode rows; program manifest3 and21 generated outputs
remain. These are generation counts, separate from actual execution. Runner,
serialized state and declared execution ABI are unchanged. Unsupported dispatch
retains the predecessor callback-visible register publication rules.

## Actual finite execution

The original descriptor route enters B81B through the existing B00F graph and
writes word VRAM at B869. Original calls, FF03 guest-stack selection and B8E7
RTL keep their existing ownership. Three exact-artifact runs each finish24,744
equal instruction boundaries: original, native with regions disabled and native
with regions enabled. Registers, open bus, bus counts, clocks, guest/PPU state,
scheduler resume columns and save/load match. The enabled window executes
20,493 native / 4,251 original
instructions. Within B8,10,985 instructions execute generated bodies and the
single RTL stays original. The registered8414 diagnostic callback still keeps
its4,097 reads original. This finite window is not whole-game coverage.

Separate private generated-body/interpreter controls cover42,600 variants with
170,400 checks. Ten original-scheduler descriptor runs use explicitly synthetic
memory/devices, including deadline, registered write callback, unaligned D and
IRQ after a VRAM write. They compare ordered bus/state/clocks/epochs/APU/resume.
They are semantic checks, separate from coherent engine assets and playback.

## Rendering and operation

The exact executable passes60 focused original-loader parked ordinary/B0 actor
controls and21 stationary Current/Guide keyboard/indexed virtual-pad controls.
Independent ROM descriptor/VRAM/CGRAM comparisons match253 ordinary changed
margin colors and478 B0/A8 colors. Original center/guest/PPU equality holds.
Source-defined loader prerequisites and short0471/0473 offsets are staged only
in copied checkpoints. Held-offset frame6 original terrain fallback remains a
negative control; no terrain guard was relaxed. This is staged operation,
not natural acquisition or a campaign verdict. The full42-page Guide,25 Current
chapter cards, finer advice, map/guide-town tracking and configured QoL remain.

One stationary zero-offset300-frame D3D11/VSync/audio route runs at
59.9648FPS with zero steady underflow, missing-frame and audible-drop
deltas. Startup counts remain separate. No full APU/listening or new physical
controller certification is inferred.

Native SHA-256: `454a84292e67c82544a13c1be87f989081ea9d48e9ada27c5a0d7af29c5a9999`.
Immutable compiled_unqualified receipt: `bbdfc75c4b36b00f1c1ddcdf039c35c86780aba7acfc0df06b771255bfb9bebf`.
63 authored native inputs /24 unchanged Companion inputs. Qualification of the
exact executable is separate from the immutable compilation receipt.

Original ROM, center/collision/activation/pace, optional Original View, guarded
fallback, configurable keyboard/controller, XP/gold/encounter modifiers,
movement boost and hold/toggle fast-forward remain. Complete native/AOT remains
unfinished: source/code/data/mode closure, indirect dispatch, coroutine/call/
guest-stack/nonlocal-return/interrupt ownership, callback-owned instructions
and unsupported addressing/modes still require work. Owner/play testers verify
campaign directions. ROM-free authored source/launcher packages retain credits
and truthful WIP scope. Public contact: Discord chrono.trigger.
