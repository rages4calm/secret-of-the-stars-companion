# Linux and Android development builds

These targets are started, not released or gameplay-qualified. Windows remains
the supported release. Neither a Linux binary nor an APK is included in the
source package. Generated game code and ROMs remain private.

## Reuse a prepared native build

`tools/platforms/prepare.py` uses an existing public-helper source build. It
checks its compilation receipt, authored inputs, generated-output cache hashes,
architectural native C, patched runtime files and Git revision before writing
commands into a fresh private output directory. It does not regenerate game
code, alter a working installation or upload game data. Requested CMake/Gradle
configuration may fetch pinned development dependencies.
First compilation receipts remain `compiled_unqualified`; another platform
needs its own compilation and runtime qualification.

On Linux, place your private generated project, source receipt, architectural C
and matching pinned runtime on that machine. The generated source build retains
its `project/` and `arch_native/` layout. Paths to the runtime and dependencies
must refer to their Linux locations. Install Clang, CMake, Ninja and the SDL3
build dependencies, then run:

```sh
python3 tools/platforms/prepare.py --platform linux \
  --source-build /private/sots-native-build --runtime /private/pinned-runtime \
  --output /tmp/sots-linux-build --configure
cmake --build /tmp/sots-linux-build/build --target SecretOfTheStarsSNESRecomp -j4
```

Run the resulting binary from a private writable profile with `--no-launcher
--rom /path/to/your/game.sfc`. The Windows C# Companion is not a Linux launcher.
Native keyboard/gamepad input remains SDL-owned. No Linux runtime test has
passed here: this Windows host has no usable WSL distribution and reports
virtualization/Virtual Machine Platform unavailable. A real Linux machine or
configured WSL2 environment is needed for compilation and visible/audio checks.

## Android preview project

The native CMake target becomes `libmain.so` on Android and remains an executable
on desktop. The Android adapter builds the pinned SDL3 source as a shared
`libSDL3.so` before the runtime helper can choose its desktop static default. The existing native Android host supplies `SDL_main`, writable app
storage, gamepad input, graphics and audio. The new setup Activity imports only
an exact clean USA ROM through Android's document picker and checks SHA-256.
The ROM stays in app storage. No ROM, generated C or private inputs are APK assets.

The frozen authored turbo-cadence patch retained one desktop OpenGL policy call
without its Android guard. An Android-only, source-specific compatibility header
omits that absent presenter's setter while retaining the immediately preceding
real SDL renderer vsync update. CMake checks the exact reviewed host source hash
before enabling it. Current upstream already guards its desktop OpenGL calls;
this missing guard belongs to our authored patch, not a reproduced upstream bug.

Use the **next** prepared public-helper build containing
`platforms/application.cmake`, plus matching SDL3 **3.4.10** sources:

```sh
python3 tools/platforms/prepare.py --platform android \
  --source-build /private/sots-native-build --runtime /private/pinned-runtime \
  --sdl-source /private/SDL3-3.4.10 --output /tmp/sots-android-preview
```

That writes a Gradle application referencing your private native source tree.
With JDK17+, Android SDK36, NDK28.2.13676358, CMake/Ninja and Gradle available,
run the command in its `platform-plan.json` (`gradle --project-dir ...
assembleDebug`). The Android Gradle plugin is pinned to8.10.1; the Gradle build
may fetch missing development dependencies. This preparer itself does not.
The first ABI is arm64-v8a. Native compilation, APK assembly, installation and
phone graphics/audio remain unqualified; no Android performance claim is made.

The original touch HUD follows the same SNES controls used in the other ports:
direction buttons, A/B/X/Y, L/R, Select/Start, plus Journal, Map, Boost and Turbo.
**Controls** hides or restores the overlay and persists that preference, so a
controller can be used without covering the picture. Hiding, pausing or losing
focus releases held touch keys. SDL continues to own physical gamepad input.
Touches use the native default keyboard mapping; custom remaps must be matched
by a future remapping UI. Layout/phone usability has not been visually tested.

EarthBound's Android code was inspected as a behavior reference. Its Java touch
implementation is GPL-licensed, so it was not copied into this repository's
PolyForm code. These small Activities are original implementations. SDL's own
Java code is supplied by the external pinned SDL source tree at build time.

## Checks performed

- Both new Activities and the pinned SDL3 Java sources compiled with `javac21.0.10` in Java17 source/target mode
  against Android API36 (deprecation warning only).
- Python preparer help/import passed and an existing real private1191 receipt
  produced a Linux configuration plan after source/cache/runtime checks.
- CMake's platform adapter preserves desktop executable creation and selects a
  shared library named `main` only for Android.
- The initial native configuration refused the incomplete NDK placeholder.
  The exact official NDK28.2.13676358 archive was then downloaded, checked
  against Google's repository size/SHA1, and installed without removing the
  old placeholder. Google's current SDK Manager redirects to Android CLI;
  that CLI returned "No url for ndk", so the verified official archive was
  used directly.
- Actual arm64/API26 native CMake configuration now passes with NDK Clang19.0.1.
  SDL_SHARED is ON and SDL_STATIC is OFF, and generated build rules name both
  `libmain.so` and `libSDL3.so`. Native game compilation was not run by this
  configuration check. No APK or Android device execution is qualified.
- These are source/Java compile checks and successful native configuration,
  not an APK, Linux-run or campaign verdict.

## Frozen runtime compatibility

The Android adapter verifies the exact pinned desktop-host source before
force-including one Android-only compatibility header. The frozen local turbo
patch accidentally calls a desktop-only OpenGL setter on Android; its preceding
SDL renderer vsync update remains active. The adapter does not modify runtime
caches or affect Windows. A future runtime pin must review or remove this shim.
