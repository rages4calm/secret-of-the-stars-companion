# Developer builds on Windows

This repository is a source snapshot, not a ready-to-play release. The native
foundation can be assembled from a developer's own ROM; the existing Companion
Play/Resume adapter still expects a qualified local installation and private
fixtures. Do not copy someone else's qualification receipt into a fresh build.

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

The engine's default input and hotkeys may differ from an already configured
Companion installation. See its local configuration and the source settings
pages; physical-controller coverage is still being expanded.

## Build Companion separately

Install the .NET 8 SDK on Windows, then:

```powershell
dotnet publish Companion/Companion.csproj -c Release -r win-x64 `
  --self-contained true -p:PublishSingleFile=true -o local/public-companion
```

The project pins Windows Desktop runtime 8.0.27 and publishes a self-contained
WinForms application. Retain the corresponding licenses/notices for any future
binary distribution. Source-level settings/backend/readiness tests are in
`Companion/`; successful GUI startup does not certify native gameplay.

**Current integration gap:** `ProfileService` and the historical launch scripts
require ignored build receipts, a canonical installed executable and copied
test fixtures. A source-first public ROM/setup/profile path is still required
before Companion can offer reliable Play/Resume on a fresh clone. The developer
native run above is the supported source-build route for now.

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
