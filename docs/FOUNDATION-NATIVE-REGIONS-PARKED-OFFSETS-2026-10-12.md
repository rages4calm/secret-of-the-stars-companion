# Scheduler-owned native regions and parked sprite offsets — 0.4.8

Source-derived poll instructions now execute generated C bodies inside the
original per-instruction scheduler. Deadlines, stable-poll observation, IRQ,
callback, producer progress and resume ownership stay original. Unsupported
instructions retain the original route, including callback-visible register
publication. Each accepted body fetches and commits once; the common scheduler
bookkeeping runs once. No serialized state or declared execution ABI changes.

The fifteenth ordered runtime patch adds a source-bound six-file implementation.
Generated cache format7 records per-bank region metadata; program manifest3
stays unchanged. Read/conditional-branch leaves come from already decoded poll
graphs, with original masks, forced-original PCs, hooks and mode guards intact.
They are neither new callable roots nor continuation certificates.

## Exact finite execution

Original, native-with-regions-disabled and native-enabled runs each finish
24,744 equal instruction boundaries. Registers, open bus, bus counts, clocks,
guest/PPU state, original scheduler resume columns and save/load match. Actual
00:8417 accounts for4,097 newly generated instructions. The diagnostic run
registers the original ObserveNmiWait callback at00:8414; those4,097 reads
retain original execution, as required. The enabled window
has 9104 native and 15640
original instructions. These finite counts do not establish complete native/AOT.
Dedicated scheduler controls separately compare ordered bus transactions,
deadlines, IRQ, callbacks, dynamic wake and APU/MMIO poll behavior.

## Original parked sprite rendering

Exact saved A0/A8 rosters now admit nonzero original offsets without adding
coordinate arithmetic. Large B0 rendering snapshots those offsets with the
packet: original party D989 ignores them; regular DB68 adds them once before
component placement. Displayed predecessors retain their captured coordinates
when live offsets change. Art identity, full544-byte packet, fixed-writer order,
DMA and raster ownership remain independent and guarded.

Focused compiled-module checks cover both margins, combined rosters, party
offset suppression, regular offset application, predecessor ownership,
overwrites and refusals. Separate engine checks use the original shrine exit
and allocator for coherent scenery and actors. Source-defined loader
prerequisites are staged in copied checkpoints; only0471/0473 change afterward
for short offset checks. Independent ROM descriptor/VRAM/CGRAM pixel checks
and original center/guest equality qualify that executable. This is staged
operational evidence, not natural acquisition or campaign certification.
Frame3 has253 independently matching changed ordinary margin pixels and478
B0/A8 pixels. At frame6, held staged offsets make the original terrain guard
refuse both fixtures; their margins fall back to black. This negative remains
part of the evidence rather than weakening the original tile guard.

Current/Guide keyboard and indexed virtual-pad checks remain stationary.
The full42-page Guide and25 Current chapter cards are retained. One stationary
zero-offset300-frame D3D11/VSync/audio route runs at 59.9610FPS with
zero steady underflow, missing-frame and audible-drop deltas. Startup counts
remain separately recorded; this is not a listening or full APU equivalence claim.

Native SHA-256: `aa21b6099d281763edbb7fed1ba4cd92042ec94c444cf17e9b4cac2ff8261660`.
Immutable compiled_unqualified receipt: `cd71b5c7622a9c2a6044b3e14c5ae3fc541b4b968d37d9a4cd355776f70486f2`.
63 authored native inputs and24 unchanged Companion inputs. Exact-artifact
qualification is separate from the immutable compilation receipt.

Original ROM, center, collision, activation and pace; Original View; guarded
fallback; map/guide-town tracking; configurable controls; reward/encounter
modifiers; movement boost and hold/toggle fast-forward remain. Full native/AOT,
broader rendering and human campaign verdict are separate unfinished work.
Downloads contain ROM-free authored source/launcher with credits. Discord:
chrono.trigger.
