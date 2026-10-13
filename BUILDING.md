# Developer builds on Windows

This repository is a source snapshot. Source-first Companion can build the native
foundation from an owned ROM and launch an isolated profile without private
fixtures. The ROM-free portable launcher package includes the self-contained
GUI and authored source; native setup still requires the tools below.
Compilation status stays explicit. Never copy another build's qualification receipt.

## Requirements

- Windows x64.
- Git with network access to fetch the pinned runtime and its submodules.
- Python 3.11 or newer.
- Rust/rustup and Cargo. The pinned upstream analyzer requests Rust 1.97.1.
- CMake 3.20 or newer, Ninja, and a Windows-compatible Clang/Clang++ toolchain
  with matching C/C++ headers and libraries. `clang` alone without a working
  Windows toolchain is insufficient.
- SDL3. The runtime fetches pinned SDL3 3.4.10 when no suitable package is found;
  `--sdl3-dir` can point to an existing SDL3 CMake package.
- Your own exact clean, unheadered USA ROM: 1,572,864 bytes, CRC32 `ef968ed1`,
  SHA-256 `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.

No ROM download or patched-image bypass is provided.

## Native developer helper

From the repository root:

```powershell
python tools/build_public_foundation.py --rom "D:\My Games\Secret of the Stars (USA).sfc"
```

Optional tool paths and an existing SDL package can be specified:

```powershell
python tools/build_public_foundation.py --rom "D:\My Games\Secret of the Stars (USA).sfc" `
  --cmake "D:\Toolchain\bin\cmake.exe" --cc "D:\Toolchain\bin\clang.exe" `
  --cxx "D:\Toolchain\bin\clang++.exe" --ninja "D:\Toolchain\bin\ninja.exe" `
  --sdl3-dir "D:\Toolchain\lib\cmake\SDL3" --jobs 8
```

To choose a new native build folder explicitly:

```powershell
python tools/build_public_foundation.py --rom "D:\My Games\Secret of the Stars (USA).sfc" `
  --output-dir "local/source-builds/native053-fresh"
```

`--output-dir` must not already exist. The default remains a fresh timestamped
folder; this option does not overwrite an earlier build or profile.

The helper checks the ROM identity before generating anything. It creates a
fresh timestamped `local/source-builds/<timestamp>/` containing an authored
source copy, private generated code, build logs, executable and fresh profile.
The ROM is read from the supplied path and is not copied into the repository.
The runtime lives under ignored `local/upstream/<pin-prefix>-<combined-patch-prefix>`.
The current42-patch key is `7931b53c4968-f7024d97f1a4c5fe`. All42 full ordered
hashes remain in the marker and receipt. Fresh builds use the public helper and
verified runtime/SDL dependencies; changed existing caches are preserved, never
reset to make a build pass. Keep required active caches and remove closed
rebuildable outputs under the required-only storage policy.

Runtime pin: `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`.
Its two recorded submodule pins are in
[`native/foundation/framework_pins.txt`](native/foundation/framework_pins.txt).
The helper checks both submodule pins and applies all42 individually hashed
runtime patches in order. The public `patches/` bindings record exact prior and
final source hashes; each new stage validates its predecessor before applying,
then validates final sources and source accounting. Unexpected edits or cache
markers stop the build while preserving the existing checkout.

The current native instruction and continuation families run inside the original
scheduler. Registered callbacks finish before a certified instruction can run;
original stack/return ownership, buses, clocks, deadlines, IRQ, masks, forced
original entries and unknown-mode/call refusal remain authoritative. Independent
instruction bodies preserve source flags and conditional branches before prefix
activation transforms. Supported indirect-Y and direct stack-relative data
operations remain separate from unsupported addressing forms.

The selected original-call and redirect continuations require live source bytes,
owner/epoch and consumed-frame proofs. Dormant task and redirect observers return
before unnecessary view/recipe work when no authorization is live. They do not
cache a positive match or bypass an active guard. Complete native/AOT conversion
remains unfinished; these are bounded source contracts.

Normal generation uses the pinned analyzer/emitter with the checked
CRC32/SHA-256, `recomp/symbols.toml`, all three bank configurations and
`recomp/reviewed-roots.json`. Reviewed roots, proved prefixes and converged-exit
certification default on. `--no-converged-exits` is a diagnostic opt-out.
The supported SDK regeneration command forwards `--cfg-roots`,
`--no-host-root-scan`, `--faithful-prefixes`, `--certify-converged-exits` and the single
`--reviewed-root-manifest` input. The builder may invoke the same emitter directly.
The current default emitter produces an exact allowlist of 25 generated outputs;
the prototype header is also generated locally. The earlier 19-output SDK
comparisons retain their historical scope. Start without a prior
generated `recomp/funcs.h`: feeding that output back as an input can change
interrupt aliases and the module digest. The public builder always creates a
fresh source folder. The automatic faithful patch retains upstream decoded instruction
and IR generation while committing original bus transfers and internal clocks
one instruction at a time. Unsupported modes return to the original interpreter.
The three reviewed inline-data ranges remain hard-masked; their special return
dispatchers stay interpreted. ROM-derived generated files remain private. The CMake build uses
`SNESRECOMP_FRAME_IMPL=HLE`, SDL3 and no netplay. HLE selects host staging; it does
not make the entire game AOT/native. All generated bodies and `recomp/funcs.h`
remain under ignored `local/`.

Native 0.2.9 also runs `tools/generate_faithful_clear.py` from the copied native
project. It generates the observed original call, setup, loop and return across
13 instruction addresses into private `src/gen`, with ROM/generator provenance
bound by the source receipt. Original bus accesses, timing, scheduler and return
behavior remain intact. Generated execution defaults on under its exact context
and port guards; unsupported states retain the original path.

For explicit developer comparisons, `SNESRECOMP_FOUNDATION_GENERATED_CLEAR=0`
together with `NativeClear=0` and no native-clear override selects the interpreter.
`SNESRECOMP_FOUNDATION_GENERATED_ROUTINE=0` retains the earlier three-instruction
loop when generated execution is enabled. The handwritten original-cost route
remains separately selectable for diagnostics. These are one bounded loading
routine and comparison routes, not complete game AOT.

Native 0.3.0 also generates the observed outer constructor and its long-call/return
sites:60 instruction addresses and62 observed mode contexts. Its original
producer/coordinate callees remain interpreted. Each generated instruction
retains original bus, stack, timing and scheduler behavior. Generated outputs
stay private and their hashes bind the real compilation receipt. Unsupported
party/resource/port contexts retain the original path. For explicit developer
comparison, `SNESRECOMP_FOUNDATION_GENERATED_CONSTRUCTOR=0` disables this
constructor separately from the clear options. This is another bounded routine,
not complete game AOT.

Native 0.3.3 records the automatic generation manifest, discovered mode contexts,
refusal dispositions and its private original-entry diagnostic list in the
compilation receipt. These counts describe generation, not executed campaign
coverage. Normal launches retain the existing guarded clear and constructor
islands. For a strict automatic-only comparison, disable both islands using
`SNESRECOMP_FOUNDATION_GENERATED_CLEAR=0` and
`SNESRECOMP_FOUNDATION_GENERATED_CONSTRUCTOR=0`. To select the original-byte
oracle too, set `SNESRECOMP_LLE_INTERP_TARGET_FILE` to the receipt's generated
`automatic-original-targets.txt` path. Actual execution counters and exact guest
comparisons must verify each diagnostic route. No profile setting enables this
oracle by default. See [native generation, renderer boundaries and exact scope](docs/FOUNDATION-DECATAS-NATIVE-2026-10-11.md).

Default Setup needs no local captures. The authored reviewed metadata lists
183 additional exact PC/M/X/native-E0 entry contexts and hash-only review
provenance. It supplies analysis seeds, not instruction bytes or forced native
dispositions. Existing data masks, forced-original entries, unknown modes/calls
and registered callbacks remain authoritative. With the existing roots, the
reviewed-root continuation reported 196 roots and 245 contexts: 151 full
bodies, 93 proved prefixes and one interpreted context under its nine-patch
generator. Those are historical generation counts. Read each new compilation
receipt for its actual current ordered-patch identities and dispositions; they are not campaign execution
coverage.

For generation diagnostics, `--no-reviewed-roots` omits the authored additional
seeds and `--no-proven-prefixes` disables prefix emission. Neither option is
needed for normal Setup. `--emit-proven-prefixes` remains accepted explicitly.
The optional `--profile-*` inputs retain their separate exact original
five-patch receipt/program/analyzer/runtime checks; they are not a default or
a public dependency. Captured-source identity and current target generator
identity remain separate. ROM-derived output stays ignored and local.
[Reviewed metadata, reproducibility and limits](docs/FOUNDATION-REVIEWED-ROOTS-2026-10-11.md).

The resulting `source-build-receipt.json` says **compiled_unqualified** and
records exact input/executable hashes. Compilation is separate from gameplay
qualification. Source modifications are recorded as differing from the
authored snapshot; the helper does not label them verified.

## Run the fresh developer build

Use the profile path printed by the helper:

```powershell
Set-Location ".\local\source-builds\<timestamp>\profile"
.\SecretOfTheStarsSNESRecomp.exe --no-launcher --rom "D:\My Games\Secret of the Stars (USA).sfc"
```

This starts with a fresh profile, title-first, enhanced pixels on and widescreen
off. It does not load, convert or advance an existing owner save. In that
profile's `foundation.ini`, enable both `ExperimentalFieldWide=1` and
`ExperimentalFieldActors=1` to exercise the experimental wide presentation.
Unsupported states retain the original centered picture with side bars.
The 0.2.9 source continuation includes guarded original single/compound vehicles,
selected world-map actors and two authenticated interior actor families.
Journal current possession defaults on within the existing Journal feature;
`JournalPossession=0` in foundation.ini disables its inventory line.
The full 42-page / 14-section story guide remains browsable through the ending.
Current has dedicated cards for all 25 original chapters, plus the existing
finer opening-through-Sidon predicates. The guide starting section follows the
current original chapter. Loading an earlier checkpoint
recomputes current advice. Item possession, chapter suggestions and written
walkthrough pages are not permanent completion history.
See [guide controls and feature checks](docs/FOUNDATION-STORY-GUIDE-2026-10-12.md)
and [content sources](docs/JOURNAL-GUIDE-SOURCES.md).
See [current release scope](docs/FOUNDATION-GROUPED-NATIVE-2026-10-12.md) and the retained
[integrated actor scope](docs/FOUNDATION-INTEGRATED-RELEASE-2026-10-09.md).

The engine's default input and hotkeys may differ from an already configured
Companion installation. See its local configuration and the source settings
pages; physical-controller coverage is still being expanded.

## Isolated developer replay

The native executable keeps settings and saves beside its own file. Changing
only the working directory does not isolate a test. Use a copied checkpoint
and this helper to run beside a copied executable in a fresh private folder:

```powershell
New-Item -ItemType Directory -Path "local/probes" -Force
python tools/run_foundation_probe.py --exe "<build>/build/SecretOfTheStarsSNESRecomp.exe" `
  --rom "D:/My Games/Secret of the Stars (USA).sfc" --script "<finite-input.txt>" `
  --state "<copied-checkpoint.sav>" --evidence-root "local/probes" --name "world-walk" `
  --cpu-trace --actor-trace --watch "5360:53b2"
```

Omit `--state` for a cold start. The input script accepts `wait <frames>`,
`press <button> <frames>`, `dump <simple-name>`, `quit` and comment lines.
For example, `wait 60`, `press down 60`, `dump after`, then `quit`, each on its
own line. Dump names cannot include paths. Existing output folders, unsupported
ROMs and unsafe commands are refused before a profile is created.

The helper disables autosave, audio, frame pacing and presentation enhancements
by default, checks the actual profile anchor, and retains input hashes, dumps,
logs and `probe-report.json`. `--wide` and `--enhanced` explicitly select those
presentation options. `--expected-exe-sha256` can freeze the executable identity.
Its report says **developer_replay_only**: a headless silent replay does not
qualify gameplay, campaign coverage, performance under pacing or audio.

## Build Companion separately

Install the .NET 8 SDK on Windows, then:

```powershell
python tools/build_public_companion.py
.\"Start Secret of the Stars Companion.cmd"
```

Optional fresh GUI folders can be selected independently:

```powershell
python tools/build_public_companion.py --source-dir "local/companion-build-sources/gui036-fresh" `
  --output-dir "local/public-companion/builds/gui036-fresh" --no-select
```

Both folders must be new. `--source-dir` holds the frozen authored source and
build intermediates; `--output-dir` holds the published GUI and its receipt.
`--no-select` keeps the existing public launcher selection while building a
candidate. Omit it when deliberately selecting the new build.

The helper freezes authored inputs, publishes an isolated self-contained
Windows x64 application, retains .NET/MIT notices and records a
`compiled_unqualified` source receipt. The project pins Windows Desktop runtime
8.0.27. The CMD checks the exact recorded EXE before opening Setup; you can also
open that EXE directly with `--root <repository>`.

In **Setup**, select your supported original ROM, then build the native
foundation or adopt a prior source-build receipt. The ROM is read and hashed;
it is never copied into the source tree. Build diagnostics stay under ignored
`local/`, and cancellation preserves prior builds and selected profiles.
Adoption creates a fresh profile with autosave disabled and no owner saves.
**Play** starts at the title; **Resume** accepts an explicitly selected checkpoint
from that profile and launches a protected copy. Compilation status stays
visible; adoption does not turn a build into a gameplay-qualified release.

In **Controls**, edit the single player's keyboard and controller game buttons.
**Hotkeys** supports keyboard names/modifier chords, controller buttons/chords,
explicit `None`, and all twenty save/load checkpoint slots. Enable hold/toggle
fast-forward there. **Enhancements** exposes independent XP/gold rates (100Ã¢â‚¬â€œ1000%)
and movement boost (100Ã¢â‚¬â€œ300%). Companion 0.3.5 also exposes
**Random encounter rate (%)** from 0 to 100 for native 0.3.6 or later. Default 100
keeps the original ordinary check; 0 disables qualified random battles, while
scripted battles retain their separate path. Reduced values scale integer
threshold bins, not an exact campaign frequency. Original View forces 100 for
that launch without rewriting the profile. Defaults are Tab/R2 for fast-forward
and Left
Shift/L2 for movement. Explicit existing mappings take priority. Unsupported
scripted movement retains original pace. Changing settings requires the game
to be closed; Apply validates changed bindings and backs up edited files.

Companion 0.3.0 also offers **Update selected profile** and **Use previous profile**
in Setup. Update clones settings/saves into a new profile; the previous folder
is retained, and selection changes atomically after verification. Rollback
selects the retained earlier profile and preserves newer progress separately.
Different native executables require declared compatible checkpoint/SRAM formats
and the same execution-state ABI. Missing legacy metadata permits identical
executables only; use fresh adoption for a different undeclared build.

The historical qualified local installation adapter remains supported, but
public Play/Resume does not require private preview fixtures. Broader hardware
checks and automatic GUI release updates remain open.

## Package the source-first launcher

After building Companion from the current authored snapshot:

```powershell
python tools/package_companion.py --companion-receipt "<build>/source-companion-receipt.json" --output "local/packages/companion-source-first.zip"
```

This adds exactly one self-contained GUI EXE to Git-tracked authored source and
retained notices. Native executables, generated game code, ROMs, artwork/audio,
checkpoints and player profiles are excluded. Extract into a fresh folder and
run `python tools/verify_companion_package.py "<extracted folder>"` to compare
package files with its integrity manifest, then open the root EXE or CMD.
GUI startup needs no .NET SDK; native source setup still needs the prerequisites.
The integrity manifest is not publisher authentication or gameplay certification.
Configured profiles use absolute receipt paths; keep their project root stable.

## Checks

```powershell
python tools/check_public_source.py
```

This ROM-free check validates the tracked-file publication boundary, authored
manifests, Python syntax, runtime pin and license notices. It does not simulate
a campaign. Existing `check_foundation_*` tools generally require a local ROM,
runtime, build or qualified copied fixtures; their historical `local/` defaults
refer to development evidence that is deliberately excluded from GitHub.

A ready-to-install GitHub Actions template is retained at
[`docs/github-workflows/source-checks.yml`](docs/github-workflows/source-checks.yml).
It is not active CI: the initial publication credential cannot upload active
workflows. A maintainer with workflow permission can move it into
`.github/workflows/source-checks.yml` to run this same ROM-free checker on pushes
and pull requests. Local source checks passed before publication.

## Current source and artifact scope (native0.5.2 / Companion0.3.6)

The current snapshot has63 native and24 unchanged Companion authored inputs.
Its35 ordered patches use cache26 / normal instruction metadata12 / task
metadata5 / redirect metadata1. Default generation records9274 normal mode
rows,228 task rows and3 redirect rows in25 outputs. These counts describe
source generation; complete native/AOT execution remains unfinished.

Fresh executable SHA-256:
`fb7f4e4c3771014ece407cc6c7511dffdf2e9dac7b9333f5da884a961ef0cc82`.
Immutable compilation receipt SHA-256:
`4187d5214c79f4b33ff44b7ecaf9633b173d163e56eb49a21f6d9aad897729d0`.
The receipt remains `compiled_unqualified`. Its declared execution-state ABI is
`de6eb89eb74024bc3e57df857a6a14fe6dd4d7d73dedf888fcba425eb5678321`.

Separate exact-artifact checks match12,834 completed original/native states,
clocks and saved output bytes. Five operation routes cover actual wider effect
pixels, keyboard/indexed virtual-controller journal controls and300-frame
D3D11/audio playback. The finite pace is60.027FPS with zero steady underruns,
missing frames and audible drops. Staged original-loader assets are explicit;
this does not certify natural acquisition, all17 new X0 prefixes, physical
controllers or the campaign. Owner/play testers verify campaign directions.
See [grouped scope](docs/FOUNDATION-GROUPED-NATIVE-2026-10-12.md).

Earlier051 and private080 receipts retain their own scopes; current checks do
not rewrite or transfer their qualification. Preserve declared ABI/profile update
rules. Keep only required donors, receipts and inputs, place bounded large build
outputs in Temp, and maintain the5GB steady workspace cap.

Native0.5.3 uses declared execution ABI `a852efdd826b5c79ad88ae5f3539faf1a9490aaab2d819f55f28a87ad08b3a9b`. A source-profile update from native0.5.2 with a different declared ABI must refuse; use separate fresh adoption. Never rewrite an old profile inventory to bypass this check. The host turbo API and its verified runtime headers must be supplied together by the public helper. Original-checkpoint compatibility remains separately tested and does not imply source-profile ABI compatibility.
