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

The helper checks the ROM identity before generating anything. It creates a
fresh timestamped `local/source-builds/<timestamp>/` containing an authored
source copy, private generated code, build logs, executable and fresh profile.
The ROM is read from the supplied path and is not copied into the repository.
The runtime lives under ignored `local/upstream/snesrecomp`.

Runtime pin: `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`.
Its two recorded submodule pins are in
[`native/foundation/framework_pins.txt`](native/foundation/framework_pins.txt).
The script checks those pins, applies `patches/runtime-foundation.patch`, and
checks the resulting source hashes before reusing a checkout. Unexpected
revisions or edits stop the build without deleting or resetting that checkout.

Generation invokes the pinned `snesrecomp_cli.py generate` with the checked
CRC32/SHA-256, `recomp/symbols.toml` and `recomp/bank00.cfg`. The CMake build uses
`SNESRECOMP_FRAME_IMPL=HLE`, SDL3 and no netplay. HLE selects host staging; it does
not make the entire game AOT/native. All generated bodies and `recomp/funcs.h`
remain under ignored `local/`.

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
The 0.2.7 snapshot includes guarded original single/compound vehicle and selected world-map actor policies.
Journal current possession defaults on within the existing Journal feature;
`JournalPossession=0` in foundation.ini disables its inventory line.
Verified current advice now extends through selected chapter-five Graviton states;
loading an earlier checkpoint removes later advice. Item possession and story
flags are not permanent completion history.
See [current scope](docs/FOUNDATION-CONTINUATION-2026-10-11.md) and the retained
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
fast-forward there. **Enhancements** exposes independent XP/gold rates (100–1000%)
and movement boost (100–300%). Defaults are Tab/R2 for fast-forward and Left
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

## Navigation map (native 0.2.7 / Companion 0.3.2)

Enhancements exposes **Current-area map** and **Show current objective on map**.
Hotkeys exposes **Map** for keyboard and controller. Defaults are **M** and
**Back + left-stick click**; occupied implicit shortcuts remain unbound rather
than replacing an existing action. Explicit custom bindings are retained.
Original View disables both map and objective marker for that launch.

The public builder applies the pinned seventeen-file base runtime patch and the
separately audited three-file host navigation/input patch. It preserves previous
runtime caches, records both patch hashes, and produces a real
`compiled_unqualified` receipt. The host-only changes retain the declared guest
execution-state ABI; matching metadata is still required for changed-binary
profile updates. There are 54 native authored inputs and 24 Companion inputs.
The matching legend and source-proven cache-key fixes preserve completed terrain
during checked same-area movement. Work remains capped at 1,024 samples per
host frame, with the existing 120-frame graphics refresh and restore reset.
[Exact qualification and remaining limits](docs/FOUNDATION-CONTINUATION-2026-10-11.md).
