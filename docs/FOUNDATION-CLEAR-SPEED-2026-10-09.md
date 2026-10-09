# Measured native loading headroom

October 9, 2026. This follows the original-cost native clear and v3 checkpoint
proof. The two new policies are diagnostic opt-ins, with no player default or
global CPU-budget change. The newest installation continuation/receipt remains
authoritative. No owner ROM, checkpoint, profile or other installation was used
as a writable test target.

## Concrete result

Both policies reduce the time charged to the verified loading clear. Neither
reduces the number of loading-blank fields or the first visible/full-bright field
in the copied natural house exit. This creates measured loading headroom; it is
not yet a visible transition speedup, scrolling repair or eliminated slowdown.

| Clear policy | CPU cycles, including original prologue | Elapsed master clocks, including refresh | Raw loop master clocks | Forced-blank fields | First visible guest field | Full-bright guest field |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original native cost | 61,465 | 455,520 | 442,362 | 11 | 18,554 | 18,582 |
| Reduced internal cost | 49,178 | 379,638 | 368,640 | 11 | 18,554 | 18,582 |
| Fast native computation | 24,602 | 151,974 | 147,456 | 11 | 18,554 | 18,582 |

Reduced removes 12,287 CPU cycles and 73,722 raw master clocks; including the
associated refresh difference, the measured clear finishes 75,882 master clocks
sooner. Fast removes 36,863 CPU cycles and 294,906 raw master clocks, finishing
303,546 master clocks sooner including refresh. These are guest clocks, not host
FPS or process-duration measurements.

The fast clear ends in field 18,540 instead of 18,541. Its first constructor
starts 303,546 master clocks earlier. It reaches the original NMI wait in field
18,550, compared with 18,551 for original cost. The visible handoff still occurs
on the same measured fields. Original fade/task pacing and the remaining map
construction therefore need separate investigation before asserting a display
latency benefit. Their exact contribution is not inferred from this result.

First-visible means the first post-loading field with forced blank off,
brightness above zero and field mode 1. Full-ready means the first subsequent
brightness-15 field. The original off-blank field can still have brightness zero;
calling that immediately visible would give the wrong result.

## What changed and what stays charged

All policies use the same exact-ROM, caller, task, direct-page, register-width
and PPU-port guards established by the original-cost proof. They cover only
`01CB2E` STA, `01CB31` DEY and `01CB32` BNE in this recognized loading context.
Unknown contexts retain original execution. The original RTS performs the return.
Each native instruction commits separately through the shared bus/refresh/device
accounting and re-enters the scheduler boundary; there is no multi-field batch
or unsaved native cursor.

| Instruction | Original CPU/master cost | Reduced CPU/master cost | Fast CPU/master cost |
| --- | --- | --- | --- |
| Zero-word STA | 5 / 36 | 5 / 36 | 2 / 12 |
| DEY | 2 / 14 | 1 / 8 | 1 / 6 |
| Taken BNE | 3 / 22 | 2 / 16 | 1 / 6 |
| Final untaken BNE | 2 / 16 | 2 / 16 | 1 / 6 |

The table excludes the existing 40-clock refresh charge at applicable
instruction boundaries. Reduced removes only the DEY and taken-branch internal
six-clock work; original opcode/operand fetches remain charged. Fast treats
verified ROM fetches as native computation: it still obtains the actual values
and preserves open-bus effects, but removes their old ROM-fetch accounting.
The two original PPU byte transfers remain at six master clocks apiece. This
explicit title policy is not a generic overclock or a zero-time VRAM fill.

Settings `SNESRECOMP_FOUNDATION_NATIVE_CLEAR=original`, `reduced` and `fast`
select the proof routes. Diagnostic tests clear inherited SNESRECOMP variables,
disable unrelated presentation/fast-menu changes and use copied profiles. The
player's qualified original-cost setting is not silently replaced by this test.

## Qualification and exact limits

`tools/check_foundation_clear_speed.py --exe <side executable> --modes original reduced`
and the equivalent `--modes original fast` capture one immutable executable at
startup, then run finite fixtures. Private reports are:

- `local/runs/clear-speed-reduced-20261009-123648/report.json`.
- `local/runs/clear-speed-fast-20261009-123732/report.json`.

Both reports pass their defined gates. Each natural transition executes 18,432
native instructions and observes all 6,144 zero-word writes, exactly covering
VRAM words `0x4800..0x5FFF`. Every clear entry/store/DEY/BNE/exit semantic field
matches original cost after excluding only absolute CPU/master clocks, beam
position and guest field. Caller, task, flags/registers, stack pointer, PPU
increment/remap/read buffer, destination, original word and resulting zero word
remain in that comparison. Instruction deltas match each stated policy and
the existing refresh tax.

At independently measured full-bright readiness, complete VRAM, OAM, CGRAM,
SRAM, dumped PPU registers and composed framebuffer are byte-identical.
Verified story flags, scene/camera/map/resource records and all three tilemap
rings agree. The checker reports every other ready-snapshot byte difference;
it does not hide them behind a general timer mask.

The script dump counter names the next guest field; the observer names the
field just simulated. The corrected checker includes the measured full-bright
field and explicitly requires dumped INIDISP `15`. Earlier reports ending
`122238` / `122255` captured one field early at brightness 14; their paired
parity remains valid, but their full-bright capture label was incorrect. The
loading-field measurements themselves did not change.

Ready WRAM has 20 differing bytes for reduced and 12 for fast. Both include
`0x0C0B` (original `0x51`, candidate `0x4A`) and bytes near `0x1C82..0x1C92`.
Reduced also differs near `0x1DAB..0x1DB3`. Full ready-WRAM parity is **not**
claimed. The next bounded observation establishes a live behavioral use for
`0x0C0B`, so these policies remain diagnostic even though the defined bus,
restore and ready-render gates pass.

The fast clear can finish between field checkpoint opportunities, so the
continuation proof deliberately uses one genuine original-cost v3 mid-clear
checkpoint as a common anchor. That checkpoint contains 1,830 remaining words
and the coherent pointer `0x6000 - Y`. Each policy restores it, saves a new copy
before advancing, cold-restores that copy, and performs actual same-process
save/load rollback. This tests changing the optional timing policy after a
coherent restore; it does not pretend to have captured an uninterrupted fast
full-run midpoint.

Cold continuation executes 5,490 native instructions per policy. Rollback
executes 10,980, re-enters the coherent partial clear, and matches a same-policy
uninterrupted continuation at the same guest endpoint across every guest dump.
All common-anchor copies retain v3 VRAM access state; no v1/v2 cursor is guessed
and no owner checkpoint is overwritten. Legacy compatibility belongs to the
earlier original-cost/v3 qualification.

Disposable copied v3 states with increment-32 or remap-1 settings execute zero
native clear instructions and match their original fallback in all dumps,
field/CPU traces and seam observations. The finite town walk, two-Red-Slime
battle and ready submenu/back sequence also execute zero clear replacements;
all snapshots and field/CPU traces match between the timing policies. This
establishes ordinary pacing in those controls, not universal story/battle/menu
coverage or a new physical-controller qualification.

## Ready-state first use and final handoff

Private evidence is in `local/evidence/clear-ready-first-use/`. It reuses the
immutable qualified side executable and copied natural house/ready checkpoints;
no runtime patches, guest writes, new timing policy or controller session were
introduced. A narrow `WLOG_ADDR` capture records actual writes to
`0x0C0A..0x0C0C`. Copied-state halt probes use the existing recent-instruction
ring at the first matching write. `INTERP_DTRACE` confirms the scheduler's
`00842B` PLD restores `D=0x0C00`, `S=0x1CF5..0x1CF7`, in field 18,592.
The halt occurs before its matching store commits, so its log is instruction
context evidence, not a normal final checkpoint. No `WLOG_STATE` was enabled:
that option performs additional bus reads and is unsuitable for this proof.

The observed NPC task chain is `01C026 -> 01C02D -> 01C050 -> 01C064 -> 01C07D`.
`01C07F` reads DP `$0B`, masks it with `3`, and writes the direction into
`[$C0]` and DP `$07`. `01C087` reads the same byte again; `01C08A` adds WRAM
`$048B`; `01C08D` stores DP `$0B`; `01C08F/91` then tests the new sign. The
direction feeds `01C214` coordinate candidates and collision checks. This is
a demonstrated read **before** the next overwrite, not a discarded seed.

The shared original NMI routine `008356..00836C` adds `0x0783` to WRAM
`0x048A..048B` and `0x0B0D` to `0x048C..048D`. Faster loading lets the NPC task
consume the evolving high byte one field earlier: its first update occurs at
18,550 for fast and 18,551 for original. Consequently ready DP `$0B` is `0x4A`
versus `0x51`. At the first captured later idle update, field 18,592, the
direction masks differ (`2` versus `1`) and the resulting stores are `0xCE`
versus `0xD5`. The exact narrow trace demonstrates this use; it is not an
exhaustive memory-read trace covering every potential earlier consumer.

The finite continuation confirms actual NPC differences rather than only
scratch differences. After 60 idle fields, WRAM has 56 differing bytes,
including NPC direction `0x4119` (`original 1`, `fast 2`) and other records in
`0x4100..0x422B`. Later movement/submenu/return captures have 64/79/105 differing
WRAM bytes, including NPC coordinate/direction records. These new observations
supersede any inference of equivalent post-loading world behavior from matching
ready pixels or from unrelated town controls that never execute the clear.
They do not establish save corruption, story divergence or a campaign outcome.

The fast ready stack differences at `0x1C82..0x1C92` lie below this task's
identical saved stack pointer `0x1C94` (scheduler task index `0x0C`, DP `0x0B00`).
The current resume frame starts at `0x1C95`; its bytes are identical. Original
`0x1C91..0x1C93` contain `69 84 00`, matching the original `008469` interrupted
yield, whereas fast had reached the NMI poll with the scheduler stack. This
supports residual interrupted-stack contents, not a changed active return
frame. Ordinary push/pop stack reuse writes such lower slots before popping
them. There is no universal proof here against explicit address-based reads or
an unobserved future context; reduced's `0x1DAB..0x1DB3` remains unclassified.

The final loading handoff is now measured directly. Both policies execute
`01C84A` (re-enable NMI) and `01C851 -> 00FF03`, wait `1`, `D=0900`, caller
`01C854`, during field 18,550. Both resume at `01C855` and call `01C87A` during
18,551. Original hits its field deadline while saving the cooperative yield
at `008469`; fast completes the save and reaches the NMI poll earlier. Both
nevertheless reach the same next-field loader continuation. This explains why
an earlier poll alone does not produce an earlier final loading handoff.

The continuation enters `01C406 -> 01D107` and the bounded observed `D=1400`
script task waits at caller `01E059` from 18,551 in both modes. Original fade
routine `01EF62..01EF8F` gates on `$0523`, counts DP `$19/$1A`, updates the
low brightness nibble in `$02A3`, and terminates at the original endpoints.
Measured visible/fade fields remain identical; no cooperative wait or fade
was skipped. Existing wait/cycle trace reruns match all seven same-mode ready
dumps byte for byte. The wait trace reads its proven WRAM return frame and
changes the transient read latch, so that paired parity is recorded explicitly.

## Next focused gate

Keep changed-cost clears diagnostic while defining the desired treatment of
timing-dependent NPC behavior and qualifying any future visible benefit. The two measured
constructors dominate much more loading work than this clear; their verified
map/cell/metatile lookup offers a separate native-computation target, with
conditional terrain and direct-page return contracts retained. Do not bypass
the original cooperative waits globally to manufacture a faster fade.

The OAM scanline limit and native renderer settings are separate rendering
constraints. This clear proof changes neither sprite limits nor actor
activation, collision or camera movement. The owner's scrolling observation,
independent-reference timing/NPC differences and experimental AOT WRAM mismatch
remain open. Tests here are headless with audio disabled; they do not certify
audible transitions, physical controller latency, scanout or campaign fidelity.
