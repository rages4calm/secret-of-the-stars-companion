# Native memory instructions — foundation 0.4.2

Native 0.4.2 adds generated C for memory increment/decrement and all four
shift/rotate families, plus accumulator increment/decrement. Companion 0.3.6
stays unchanged. The full written story guide, map, configurable controller and
keyboard bindings, encounter/reward/travel settings and guarded widescreen
remain available. The owner and play testers verify campaign directions and
full playthrough behavior; developer checks focus on implementation, rendering
and reported failures.

## Implemented instruction group

| Operation | Supported memory forms |
| --- | --- |
| INC / DEC | Direct page, direct page X, absolute, absolute X |
| ASL / LSR | Direct page, direct page X, absolute, absolute X |
| ROL / ROR | Direct page, direct page X, absolute, absolute X |

All 24 exact memory opcodes require native E0 and known M/X modes. Accumulator
INC/DEC additionally require the exact one-byte instruction and matching A
register IR. The emitter checks the decoded instruction and connected memory
IR before admission; malformed or unsupported forms retain original execution.
Existing masks, unknown call/mode yields, callbacks and deadline/interrupt
ownership remain authoritative. Other unsupported operations remain unfinished.

One descriptor caches the original fetched operand, effective address and
width. Sixteen-bit data reads use original low/high order and the existing
claimed MMIO word-read path; result writes use high/low byte order. Direct page
wraps within bank00, while absolute addressing retains linear24 bank carry.
Dynamic penalties and flag updates match the pinned original interp816 core.
This changes native instruction coverage without changing game pace or adding
serialized guest fields.

## Focused implementation and render checks

The generator passes 107 focused cases; 104 compiled generated bodies pass
27,872 arithmetic/flag/order checks using a synthetic helper. The separate
runtime helper harness compares the actual original interp816 core over
43,200 cases, 388,800 checks and ten refusal controls under UBSan. Its data bus
and device callbacks are synthetic. These are instruction checks, not campaign
or complete-device qualification.

Two finite executions use this exact compiled artifact with the same authentic
checkpoint and input: all-original control and normal native emission. All
24,744 completed instruction states and observed clocks match, as do guest
components, original centers and save/load. The new group actually executes
263 native instructions in that window, including the original INC at
01:8199. Total native execution is 4993 versus
19751 interpreted instructions. These are finite-window
counts, not whole-game percentages. The trace records completed registers,
open bus and transfer counts/charges, not transaction addresses and data.

The three parity centers occur during original brightness-zero fade. Separate
visible enhanced-wide guide and combat compositions are inspected after real
checkpoint loads. A finite Direct3D11/VSync route with real SDL audio runs at
59.9769 FPS; steady underflow, missing-frame and audible-overflow
counter deltas are zero. No exhaustive developer campaign replay is required.
Physical controller and full-campaign verification remain with the owner and
play testers.

The first integrated attempt exposed an existing generic JSL return-order bug:
caller PB was restored before checking whether the native callee had yielded.
The shared emitter now restores it only after a normal return; unfinished
calls retain their actual callee bank. The initial failure remains recorded;
345 checks against fresh generated calls cover 48 mode/return/bank cases. The
repaired build passes the finite execution check. No
instruction clocks or guest stack behavior were changed to hide the issue.

## Build and installation identity

- Native EXE SHA-256: `a17c7f04b365b5633d9b1d3cc2d7c0b3b43f36331e1048cb671ab7c1daaf7a88`.
- Immutable compiled_unqualified receipt SHA-256: `b2bf3ec782415a4cc517daad78bd19297e3320060b0819ce26659755bd944001`.
- Generic thirteenth runtime patch SHA-256: `bc942791aabf6920b40bf942d874e0f1d4461eb04867acf3266a285412042b32`.
- 5 exact predecessor/final sources: `patches/runtime-memory-rmw.json`.
- Runtime cache key: `7931b53c4968-a4be41767ed1b650`; thirteen full ordered patch hashes are checked.
- Generated cache format6 / program manifest3 remain unchanged.
- Sixty-two authored native inputs; Companion's 24 inputs and EXE are unchanged.
- Declared041-to042 execution ABI, checkpoint schemas and SRAM identity match.

The thirteenth patch follows the frozen twelfth continuation patch; its earlier
source identities remain separate. New or reused runtime caches must match the
final union of exact source bindings. Changed, missing or old twelve-hash cache
markers refuse reuse. Compilation keeps its genuine compiled_unqualified
status, with focused installation qualification recorded separately.

Both installed native paths and authored mirrors match this build. Owner
preferences, saves and profile selectors are unchanged. New large builds and
captures stay in Temp under the required-only storage policy. Public Setup
uses owned ROM input and authored source, without private test fixtures or
redistributed game data. Full native/AOT execution and broader scene/effect
rendering remain unfinished. See [Roadmap](../ROADMAP.md).
