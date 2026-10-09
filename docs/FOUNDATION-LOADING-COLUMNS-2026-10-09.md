# Direct loading columns and a bounded native lookup

October 9, 2026. This focused continuation qualifies the original direct
30-word column producer and a separate, default-off native computation seam.
Installation status remains in the current release receipt. This document
does not enable player CPU acceleration or supersede the existing controller,
campaign, HD, widescreen, MSU-1 and reference-fidelity limits.

## Read-only constructor evidence

`foundation_loading.c` now accepts the separate diagnostic path
`SNESRECOMP_FOUNDATION_COLUMNS_TRACE`. It composes observers at the direct
producer `01:B4B8`, store `01:B50C`, immediate post-store `01:B510`, return
`01:B59B`, camera/segment/split helpers, attribute selectors and constructor.
The existing clear CSV schema remains unchanged. Observation uses WRAM/PPU
peeks and guarded direct ROM reads; it performs no CPU-bus reads, guest writes,
redirects, input or cycle charges. Captured original binary/data stay in `local/`.

The first qualification is
`local/runs/columns-20261009-122035/report.json`. Observer-off/on use the same
immutable executable and copied natural house-exit fixture. Five dump points,
each with all seven guest/presentation payloads, match exactly; complete CPU
and field traces also match. Original ROM and fixture hashes remain unchanged.
An initial checker incorrectly required an explicit zero replacement counter
from a disabled clear module; its report is retained. The corrected predicate
checks the actual disabled-policy log and absence of native replacements.

The earlier integrated diagnostic proof is
`local/runs/columns-20261009-123001/report.json`, executable SHA-256
`e6a07a296ef18840d175e7b3827774f71d1e977393e4bff1b52435ca6ce493be`.
Ten copied cases pass 61 checks, including the separate fast policies below.

The earlier **0.1.4 original-cost release qualification** is
`local/runs/columns-20261009-124058/report.json`, executable SHA-256
`661ae810501abc58225ad6cece3b4d7758f91a4709fc3a83aaf75a7944eb1dd4`.
Its ten copied cases pass all 55 checks.

The latest **0.1.5 original-cost release qualification** is
`local/runs/columns-20261009-125106/report.json`, executable SHA-256
`987554031d343fbc54e89b4fbc54e40058147aa6f26e75ee486391b4ff00c00e`.
The checker freezes that artifact before its ten copied cases; all 55 checks
pass, including both player configuration routes and cold/rollback continuation.
The host's cached compositor staging does not change the checked guest beam,
CPU/scheduler traces or column output. This result does not certify physical
scanout or audible playback.

The companion clear/loading qualification is
`local/runs/loading-20261009-125106/report.json`: seventeen cases and all 55
checks pass against the frozen 0.1.2 reference, SHA-256
`c6ace23e4cc71436a8b4ad02933ab9200f6e460960b9b8aad5df1dec96b8c288`.
Its log is `local/evidence/har-loading-final.log`; both input executables are
preserved under `local/evidence/hle-loading-final-inputs-20261009-125100`.
Neither final release check runs a fast timing policy. The exact clean USA ROM
remains SHA-256
`7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.

The natural exit performs two constructor calls:

| Constructor caller continuation | Observed output | Active resource contract |
| --- | --- | --- |
| `01:C6FE` | 34 BG1 columns, DP layer 0, dimensions 2x2 | Map `09:96A2`, cells `0A:8818`, tiles `03:8F58`, attributes `09:8210` |
| `01:C7B3` | 34 BG2 columns, DP layer 2, dimensions 4x4 | Map `09:9700`, same cell/tile/attribute tables |

Every direct-column call returns to `01:B25C`, with stack `0x1C28`, data/program
bank 1 and DP `0x0B00`. The active camera/resource selectors are 0/0 for BG1
and 4/3 for BG2. Loading flag is `0x80`, direction `0x81`, wrapping is disabled,
and the PPU is forced blank with unremapped increment-32/on-high writes.

The first call's **inactive BG2** resources are still the previous house:
map `09:A43E`, cells `0A:96D0`, tiles `03:AE70`, attributes `09:8610`, dimensions
2x2. Its attribute table contains selector E entries. Guarding both layers by
the ready-Likado identity would wrongly reject the valid BG1 constructor;
accepting an arbitrary scene-5 resource set would be unsafe. Native eligibility
therefore validates the active DP layer, not a universal scene-only predicate.

There are 68 complete columns and 2,040 word writes. Every pre-store accumulator
matches the guarded ROM tile-word load, and every immediate post-store matches
the actual VRAM value, pointer increment and write-count increment. Original
long STA costs are 6 CPU/44 master clocks; 64 stores additionally pay the
existing 40-clock refresh charge. The constructor splits columns at the ring
and map-segment boundaries; those original helper paths remain in charge.

The independent segment/cell/metatile reconstruction matches 1,870 inside-map
words. Another 170 BG1 words use the original outside-map metatile zero rather
than invented terrain. The inside samples select segment IDs `0x013E/0x013F`
at `0D:8F80/8FC0`; BG2 selects segment zero at `09:BF00`. These join the earlier
field-streaming identities rather than replacing them with transient VRAM slots.

All 986 captured attribute calls use active table `09:8210`: selectors 0/1/8/4
occur 811/162/11/2 times. No E/F condition-record scan executes. Both condition
pointer records, the exact 256-byte `53F9` range indexed by selector E, stage
bytes, selected/input metatiles and attribute hashes are retained in the CSV.
Recording them does not qualify a missing conditional path. Negative camera,
wrapping and other maps remain outside this natural-exit capture.

## Authored original-cost native seam

`foundation_column_lookup.c/.h` implements the fourteen original instructions
at `01:B4F3..B50B`: metatile/quadrant index arithmetic, DP scratch writes and
the final indirect ROM tile-word load. Conditional selection, segment lookup,
all PPU stores, splits and cooperative waits remain original.

`NativeColumns=1` in `foundation.ini` optionally enables the original-cost
route. Absence/0 keeps it off; values other than 1 do not enable it. This player
setting cannot select fast timing. The diagnostic equivalent is
`SNESRECOMP_FOUNDATION_NATIVE_COLUMNS=original`; an explicit environment value
overrides the setting, with 0 disabling it. The final 0.1.5 artifact qualification
above checks the rebuilt parser and both configuration routes.

The checker now adds two copied `--native-proof` cases with no native-columns
environment variable: configuration 0 must reproduce the original route with
zero replacements, and configuration 1 must reproduce the environment-selected
native-original route with the same positive count. Both require every guest
dump, complete CPU trace, field trace and observed column row to match their
respective reference. The final release check confirms zero replacements with
configuration 0 and 17,136 replacements with configuration 1, both with
`fast_fetch=0`. Configuration 1 matches the diagnostic original-cost route's
complete CPU trace, including its interpreter counters.

Each callback handles one instruction using the shared
native bus transaction and original cost, then returns to the interpreter's
IRQ/deadline boundary. There is no retained native progress cursor. Guards pin
the whole ROM/opcode sequence, captured caller/stack/task, active DP resource
contract, native 16-bit widths, decimal-off arithmetic and loading PPU state.
Unsupported context executes the original instruction. Register flags, packed
P, bus/open-bus effects and DP writes are preserved.

The complete replay replaces **17,136 interpreted instructions**, confirmed by
both the native counter and interpreter-count difference. It preserves every
column CSV row, all guest dumps, field timing and complete CPU/scheduler values
apart from the two interpreter-only counters. The 1,088 complete arithmetic/load
blocks cost 48 CPU/372 master clocks plus refresh. A further 952 second-quadrant
words take the shorter load loop; its M=8 REP instruction deliberately falls
back, explaining why the actual replacement count is below the initial 18,088
prediction. The native route covers 62,696 original CPU cycles, about 18.5% of
the 339,218 CPU cycles captured inside these direct-column calls.

A new copied v3 save inside the constructor resumes at iteration 20. Cold
original-cost continuation replaces 12,302 instructions; same-process save and
rollback replace 23,295. Both match original guest dumps, CPU/scheduler traces,
fields and observed column rows with positive native coverage. Source state
hashes are retained. The observer does not reconstruct the unfinished column's
pre-save history: initial resumed instructions before the next column entry
are covered by exact CPU/guest continuation, not a fabricated complete column.

## Separate fast-fetch diagnostic

Only after exact original-cost and continuation parity passes, the checker
tests `SNESRECOMP_FOUNDATION_NATIVE_COLUMNS=fast`. It leaves WRAM/table reads,
DP writes and PPU ports paced while omitting verified opcode-fetch charges.
Committed CPU cost is `max(1, original cycles - instruction bytes)`; the
one-cycle minimum is explicit, including immediate AND. It retains every
architectural boundary and uses the same original bus values/open-bus effects.
This is a guest timing enhancement, not original timing or a measured host gain.

Each complete block then costs 24 CPU/178 master clocks plus refresh. Captured
column CPU work falls from 339,218 to 309,298 cycles. All 2,040 original port
words and every observed column semantic row remain identical after excluding
only clock/beam/field values. No resume eviction or interpreter step cap occurs.

| Diagnostic policy | Forced-blank release | First nonblack field | Full brightness |
| --- | --- | --- | --- |
| Original | 18551 | 18554 | 18582 |
| Fast lookup only | 18551 | 18554 | 18582 |
| Fast clear plus fast lookup | 18550 | 18553 | 18581 |

The combined policy saves **one field in this copied transition**. Original
fade intervals remain 3 and 31 fields from release. Fast lookup alone reduces
work without crossing a visible transition boundary. Later fixed-field NPC/audio
state is not certified as identical after an intentional timing change. A
later root-task fast-policy comparison confirmed a shifted NPC direction
counter, so the policy must remain experimental and absent from standard
launches. Fast
partial restores, physical-controller use, listening and display scanout are
not qualified by these headless original-cost continuation checks. No player
default or global CPU budget is changed by the optional original-cost setting.

Reproduce with a fresh private run:

```powershell
python tools/check_foundation_columns.py --exe local/native-proof/SecretOfTheStarsSNESRecomp/build-hle/SecretOfTheStarsSNESRecomp.exe --native-proof
```

The separate historical fast-policy experiment uses the additional flags:

```powershell
python tools/check_foundation_columns.py --exe local/native-proof/SecretOfTheStarsSNESRecomp/build-menu/SecretOfTheStarsSNESRecomp.exe --native-proof --fast-proof --combined-fast-clear
```

The checker snapshots the executable before running, protects the ROM/source
fixture, and does not run fast policies unless original-cost parity succeeds.
Authored observer and native lookup files are mirrored to the live tree;
main/CMake/lifecycle integration and release installation remain coordinated
by the root task. Do not claim this bounded loading improvement fixes outdoor
scrolling, supplies HD artwork or expands actors beyond the original viewport.
