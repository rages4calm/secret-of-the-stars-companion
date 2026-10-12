# Native 0.4.1 original-return continuations

The generator can now emit an isolated native caller suffix and resume it after
an original interpreted routine completes its real return. Previously, a call
that yielded into original execution could leave already-generated caller code
running through the interpreter afterward.

This is a restricted continuation feature, not complete native/AOT execution.
The original guest clocks, bus transfers, stack pops and raster scheduler remain
authoritative. Unsupported or ambiguous entries continue through original code.
The owner and play testers verify the campaign; developer checks target the
changed execution path, actual rendering, restoration and audio service.

## Admission and generation

The analyzer adds a separate `native_continuations` certificate collection.
Certificates do not become ordinary callable roots or change sibling CFG
boundaries. They bind an exact entry and mode, owner, direct callsite, callee,
original return sites, original ROM identity and decoded suffix bytes.

Admission requires native E0, exact M/X, a proved balanced remaining two- or
three-byte return frame and closed direct-call dependencies. Conflicting
contracts at the same entry/mode, masks, unknown control or stack behavior,
recursive dependencies and mixed return widths refuse. The emitter independently
re-decodes the certificate before exporting its separate continuation table.
Normal generation currently produces 18 certificates. That count describes
generated entries, not campaign execution coverage.

The bridge accepts only the actual landing after an original RTS/RTL. Its
preflight reads bounded WRAM/ROM without guest bus transactions. Existing
deadline, interrupt, hook, owner and callback gates run first. A refused arrival
does zero guest work and remains original; no arrival token survives a field.

The native root consumes a one-shot return snapshot and publishes the actual
committed return PC and stack pointer. Nested returns cannot publish root
completion. No stack frame is invented, repaired or popped twice. Missing return
publication or an unowned nonlocal unwind stops execution, preventing replay.
Bounded transient host slots are reset at each field and session, and invalidate
on watchdog or restored state generation. No serialized CPU or checkpoint member
is added.

## Build and diagnostics

The generic twelfth runtime patch is
`patches/runtime-native-continuations.patch`, SHA-256
`0644e52f0c41520fb582270f38f06871f6bc9a002bf12765b4063561546c42db`.
Its twelve-file predecessor/final source binding is recorded separately in
`patches/runtime-native-continuations.json`. The runtime stays at the recorded
upstream pin, with cache key `7931b53c4968-622935e6df63ce81`.

Public Setup enables `--certify-native-continuations` through the normal build
helper. `--no-native-continuations` omits the generated certificates for a
diagnostic build. `SNESRECOMP_DISABLE_NATIVE_CONTINUATIONS=1` disables admissions
on the same compiled artifact. The all-original diagnostic also sets this
variable; disabling ordinary dispatch targets alone would not disable the
separate table. The generated output cache has format 6; the program manifest
retains format 3.

Native 0.4.1's fresh executable has SHA-256
`d0615ea02b17918ab4b889c636ab5518616270d0fe5906bb74a011a8d474ee8d`.
Its immutable compilation receipt is
`67187ff16e947bc99c63afb72c1b01994a2359ad24107b9ec677a25db3f4da3e`
and remains **compiled_unqualified**. Execution/render checks and installation
are recorded separately. Companion remains the exact 0.3.6 artifact.

The declared execution ABI changes because the per-game frame/reset hook clears
transient native activations. Strict copied source-profile updates from 0.4.0
refuse the declaration mismatch; fresh adoption is available. The checkpoint
identity, writes-v3/reads-v1-v2-v3 schema and SRAM layout remain unchanged.
Finite restoration checks are separate from campaign compatibility.

## Focused implementation checks

Fourteen Rust and 41 Python generator checks pass, including mixed two/three-byte
frame directions and admission refusals. Runtime C11 syntax, 125 enabled and
three disabled UBSan controls, plus 14 source/layout checks pass. These synthetic
checks do not replace actual-device execution. The final candidate's line-ending
normalization preserves their source text exactly.

The original execution witness uses `00:ABD0 -> 00:AC42 JSL01:8009`, whose original
callee can yield across fields, then `01:81A3 RTL -> 00:AC46`. AC46 still owes the
distinct outer RTS/two-byte frame. The generated suffix includes ordinary
original-byte-derived bodies for its four later accumulator ASLs. Actual
same-artifact original/disabled/enabled execution results are recorded separately
from this generation fact.

The exact compiled artifact passes 114 focused checks across five finite runs.
All 24,744 completed instruction boundaries match its same-artifact all-original
and continuation-disabled controls. The affected ABD0 activation executes
225 native / zero original instructions, versus 112 native / 113 original with
continuations disabled. The full three-field window executes 1,864 native
instructions versus 1,751 in the disabled control. These are actual committed
instruction counts, not generated-node counts or whole-game coverage.

The inner RTL and outer RTS each pop their distinct frames exactly once. The
unsupported original INC and memory shifts retain their original path. Guest
state, input, bus/CPU/master clocks, restoration and cold controls match. The
three compared presentation frames occur during original brightness-zero fade;
they establish identical output for that transition, not visible battle art.
An additional 800-by448 enhanced-wide guide composition was captured and
visually inspected. The paced Direct3D11/VSync route runs at 59.9809 FPS with
zero steady audio underflows, missing frames or audible overflow. Listening,
physical-controller variation and campaign verification remain separate.

Native 0.4.1 is installed in both canonical local executable paths; Companion
0.3.6 is unchanged. Source mirrors and compilation receipt hashes match, and
settings, saves and selectors remain unchanged. The installation changes 12
paths. These finite results do not certify the complete game.

The initial integration attempts caught a mixed line-ending source binding and
a stale format-5 cache expectation. The first execution harness used guest
indices where screenshots require local presentation indices and exceeded its
15 MB transient output cap. These are retained harness/build failures, not
campaign or product defects; the corrected output remains bounded in Temp.

Full native/AOT execution, broader scene/effect rendering and physical-controller
variation remain unfinished. The 42-page story guide and existing map continue
with their documented scopes; this native change adds no quest-completion rules
or map destinations.
