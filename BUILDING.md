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
  --output-dir "local/source-builds/native041-fresh"
```

`--output-dir` must not already exist. The default remains a fresh timestamped
folder; this option does not overwrite an earlier build or profile.

The helper checks the ROM identity before generating anything. It creates a
fresh timestamped `local/source-builds/<timestamp>/` containing an authored
source copy, private generated code, build logs, executable and fresh profile.
The ROM is read from the supplied path and is not copied into the repository.
The runtime lives under ignored `local/upstream/<pin-prefix>-<combined-patch-prefix>`; the current thirteen-patch key is `7931b53c4968-a4be41767ed1b650`. All thirteen full ordered hashes remain in the marker and receipt. Keep caches needed by active builds; remove obsolete rebuildable payloads under the project's required-only storage policy.

Runtime pin: `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`.
Its two recorded submodule pins are in
[`native/foundation/framework_pins.txt`](native/foundation/framework_pins.txt).
The script checks those pins and applies `patches/runtime-foundation.patch`,
`patches/runtime-navigation-map.patch`, `patches/runtime-faithful-clear.patch`,
`patches/runtime-modal-audio.patch` and
`patches/runtime-automatic-faithful.patch`, followed by the separate
`patches/runtime-paired-lifecycle.patch`, `patches/runtime-proven-prefix.patch`,
`patches/runtime-faithful-hook-boundary.patch` and the metadata-only
`patches/runtime-reviewed-roots.patch`, then the separate generic
`patches/runtime-converged-exits.patch`, followed by the exact single-file
`patches/runtime-accumulator.patch`, then
`patches/runtime-native-continuations.patch`, then
`patches/runtime-memory-rmw.patch`.
Each patch has an independently recorded hash in the cache key and marker; the
combined resulting source hashes are checked before reusing a checkout. Unexpected
revisions or edits stop the build without deleting or resetting that checkout.

The eleventh patch admits only decoded, exact one-byte accumulator `ASL`, `LSR`,
`ROL` and `ROR` instructions with known M/X flags through the existing faithful
emitter. At this predecessor, memory read/modify/write forms and `INC`/`DEC`
remain on the original path; the thirteenth patch extends them as described below.
Existing original buses, instruction clocks, masks, unknown-mode/call
yields and registered pre-opcode callbacks retain their contracts. This extends
generic default generation; it is not a whole-game AOT or performance claim.

The helper binds the complete ten-patch predecessor and complete post-apply
emitter before accepting an exact source-bound CRLF-to-LF conversion in the new
eleven-patch cache. The twelfth patch follows that frozen emitter, with separate exact predecessor/final hashes in patches/runtime-native-continuations.json. The resulting emitter must match its current full recorded SHA-256;
mixed, unknown or changed source bytes are refused. The cache marker and real
compilation receipt record the predecessor, patch output, conversion and final
source identities. Earlier ten-patch caches are not rewritten. The source
provenance carries hash-only reviewed offline instruction evidence, with no
private fixture or report-file dependency in public Setup. Source review does
not qualify a newly compiled executable.

Normal generation uses the pinned analyzer/emitter with the checked
CRC32/SHA-256, `recomp/symbols.toml`, all three bank configurations and
`recomp/reviewed-roots.json`. Reviewed roots, proved prefixes and converged-exit
certification default on. `--no-converged-exits` is a diagnostic opt-out.
The supported SDK regeneration command forwards `--cfg-roots`,
`--no-host-root-scan`, `--faithful-prefixes`, `--certify-converged-exits` and the single
`--reviewed-root-manifest` input. The builder may invoke the same emitter directly;
From a fresh authored project, both interfaces reproduce the same graph, all19
generated files and the generated prototype header. Start without a prior
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
receipt for its actual eleven-patch dispositions; they are not campaign execution
coverage.

For generation diagnostics, `--no-reviewed-roots` omits the authored additional
seeds and `--no-proven-prefixes` disables prefix emission. Neither option is
needed for normal Setup. `--emit-proven-prefixes` remains accepted explicitly.
The optional `--profile-*` inputs retain their separate exact original
five-patch receipt/program/analyzer/runtime checks; they are not a default or
a public dependency. Captured-source identity and target eleven-patch generator
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
Native 0.4.0 adds the full 42-page / 14-section story guide. Original current
chapter 0-24 suggests a starting section; fine current advice retains the
bounded opening-through-Sidon predicates. Loading an earlier checkpoint
recomputes current advice. Item possession, chapter suggestions and written
walkthrough pages are not permanent completion history.
See [guide controls and feature checks](docs/FOUNDATION-STORY-GUIDE-2026-10-12.md)
and [content sources](docs/JOURNAL-GUIDE-SOURCES.md).
See [current release scope](docs/FOUNDATION-INTERIOR-TOWN-DISPLAY-2026-10-11.md) and the retained
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
fast-forward there. **Enhancements** exposes independent XP/gold rates (100â€“1000%)
and movement boost (100â€“300%). Companion 0.3.5 also exposes
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

## Navigation and display (native 0.4.0 source / Companion 0.3.6)

Enhancements exposes **Current-area map** and **Show current objective on map**.
Hotkeys exposes **Map** for keyboard and controller. Defaults are **M** and
**Back + left-stick click**; occupied implicit shortcuts remain unbound rather
than replacing an existing action. Explicit custom bindings are retained.
Original View disables both map and objective marker for that launch.

The historical nine-patch builder applied the pinned seventeen-file base runtime patch and the
separately audited three-file host navigation/input patch, plus the two-file
faithful-instruction API supplement, host-only modal/audio repair and generic
automatic-faithful patch, paired lifecycle, explicit proved-prefix support and
original registered-hook boundaries. It preserves previous runtime caches,
recorded all nine patch hashes, and produced a real
`compiled_unqualified` receipt. The host-only changes retain the declared guest
execution-state ABI; matching metadata is still required for changed-binary
profile updates. There are 61 native authored inputs and 24 Companion inputs. The ninth patch
adds reviewed-root validation/forwarding only; the preceding eight patches and
serialized execution-state layout retain their exact identities.
The matching legend and source-proven cache-key fixes preserve completed terrain
during checked same-area movement. Work remains capped at 1,024 samples per
host frame, with the existing 120-frame graphics refresh and restore reset.
[Exact artifact qualification and remaining limits](docs/FOUNDATION-DECATAS-NATIVE-2026-10-11.md).

Companion Display offers Auto or exact 1280Ã—720, 1600Ã—900, 1920Ã—1080,
2560Ã—1440 and 3840Ã—2160 window sizes; existing custom sizes remain editable.
Pixel shape offers Original CRT shape, Square pixels and Square frame. Auto
uses Window scale, while fullscreen follows the display. Neither setting adds
scenery: select Widescreen separately for supported scenes. Apply validates
changed values, and Revert restores the loaded profile.

The preceding installed 0.3.3/0.3.4 pair passes exact-artifact qualification
and 18 copied-installed controls. The fresh native 0.3.4 public build has its
own strict execution/rendering, launcher-adoption and thirteen finite normal
playback checks, followed by a clean nine-route modal repeat. Two initial
modal audio failures remain retained; their cause is unproven. Installation and 18 copied
Play/Resume/visible-GUI controls pass; package/publication integrity is checked separately. The host modal/audio patch waits for genuine guest
DSP prefill before resuming the device and consumes a keyboard rewind request
once, preserving original guest timing and checkpoint ABI. Compilation alone
does not satisfy gameplay, installation or ROM-free package qualification.
Package extraction/relocation checks are recorded separately in the release
document; a package contains the launcher, authored source and notices, with
no ROM, saves, native game executable or ROM-derived generated code.

Native 0.3.1 corrects the original Y,X entrance format used by town/objective pins
and adds current Bun/architect clues. See [the exact continuation](docs/FOUNDATION-MAP-TOWN-2026-10-11.md).
For development captures, coordinate staging must be followed by original loaders
and an independent background check; parity against another corrupt fixture is insufficient.

Native0.3.5 changes only the journal/version among61 authored inputs. Runtime
patches, generated original-game outputs and checkpoint ABI retain034 identity.
[Circus/priest source qualification](docs/FOUNDATION-CIRCUS-PRIEST-2026-10-11.md)
records fresh overlay/map/launcher/playback checks and the corrected original
entrance-produced scene inputs. Do not reuse the old Golan/room227 development
checkpoints for positive scenery evidence.

Native 0.3.6 adds guarded ordinary random encounter control in the QoL module;
Companion 0.3.5 adds its setting and current/older-build tests. The default remains
100%, including profiles without `RandomEncounterPercent`. Close the game before
Apply. The control is unavailable on earlier native builds; use Setup to update
the selected profile with genuine compatible receipts. Custom bindings, rewards,
movement, checkpoint/SRAM formats and execution-state ABI are preserved.
[Encounter settings, exact artifacts and qualification](docs/FOUNDATION-ENCOUNTER-RATE-2026-10-11.md).


## Native 0.3.8 source continuation

The authored native snapshot retains 61 inputs and changes only the version and
journal C/H files relative to 0.3.7. The eleventh generic emitter patch is a
separate runtime input; the preceding ten patch bytes and declared serialized
guest/checkpoint ABI remain unchanged. Companion stays at 0.3.5.

The retained private 0.3.8 build has its own immutable `compiled_unqualified`
receipt and separate qualification evidence. A normal public source-first build
requires a new genuine receipt, fresh exact-artifact execution/journal/rendering
and clock/input/restore checks, launcher adoption/update/rollback and separate
paced/modal playback checks before installation. Package integrity and
publication are separate again. This source draft does not certify a public
0.3.8 executable, installation, package or campaign.

## Native 0.4.0 / Companion 0.3.6 story guide

The native authored manifest now binds 62 inputs, including
`src/foundation_guide_data.h`; Companion retains 24 authored inputs. Runtime
pinning and the eleven ordered patches remain independent build dependencies.
Fresh native and GUI compilation receipts remain `compiled_unqualified`.
The [story-guide continuation](docs/FOUNDATION-STORY-GUIDE-2026-10-12.md) records
separate focused actual page-rendering and input checks.

Journal defaults on in the fresh profile. J / left-stick click opens or closes
by default. Select changes Current / Guide, Left / Right changes page, Up / Down
changes section, and Game B closes. Navigation uses the existing configured
logical game actions rather than hardcoded keyboard/controller face buttons.
The panel consumes browsing controls and waits for held controls to be released
before passing them back to gameplay. It is an overlay while the game continues
running, not a pause screen. Restore resets browsing and recomputes current advice.

Native 0.4.0 declares a changed execution-state ABI for its title input-filter
integration. Normal source-profile update strictly refuses 0.3.9 to 0.4.0 on the
declaration mismatch; use fresh source adoption and preserve the prior profile.
This is not evidence that serialization itself is incompatible: selected legacy
checkpoint resumes worked in separate focused checks. Do not bypass the update
contract or turn that finite result into universal checkpoint compatibility.

The full written guide is manually browsable and covers the ending. Suggested
starting sections use original current chapter 0-24; they are coarse advice,
not automatic detection of every quest event. The owner and play testers verify
campaign directions. Fine automatic advice and map pins retain their existing
bounded predicates. No permanent history, new completion rule or guessed map
marker is introduced. [Source mapping](docs/JOURNAL-GUIDE-SOURCES.md).

Native 0.4.1 adds restricted original-return to certified native suffix admission.
Normal Setup enables certification; `--no-native-continuations` is a generation
diagnostic, and `SNESRECOMP_DISABLE_NATIVE_CONTINUATIONS=1` disables the separate
table on the same artifact. The all-original diagnostic sets this too. Output
cache format is 6; program manifest remains 3. Read the
[continuation contract](docs/FOUNDATION-NATIVE-CONTINUATIONS-2026-10-12.md).
The frame/session reset hook changes the declared execution ABI; strict copied
0.4.0-to0.4.1 profile update refuses, while fresh adoption is available.


## Native memory instructions (0.4.2)

The thirteenth patch admits the exact supported E0 memory INC/DEC, ASL/LSR and
ROL/ROR forms plus accumulator INC/DEC. `patches/runtime-memory-rmw.json` binds
its five exact predecessors and final sources. The builder checks the twelfth
source set before applying this delta, then checks the final union for compilation
and reuse. The source cache contains thirteen ordered full patch identities.
Generated cache format 6, program manifest 3 and the declared execution ABI for
0.4.1 and 0.4.2 remain unchanged. Full native/AOT and campaign verification are
separate.
[Current instruction and rendering scope](docs/FOUNDATION-MEMORY-RMW-2026-10-12.md).
