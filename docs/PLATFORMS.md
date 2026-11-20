# Linux and Android development builds

These are development previews. Each tester builds the playable program locally
from their own clean USA ROM. The public source includes the platform build tools
and Android app source. Generated game code and the resulting binaries stay local.

## Reuse a prepared native build

Generate the private inputs on a machine with the toolchain from [BUILDING.md](../BUILDING.md).
Use the matching runtime path printed by the helper. This step does not compile a
Windows executable. An existing public-helper build also works as input.

```sh
python tools/build_public_foundation.py --prepare-platform-sources \
  --rom /private/secret-of-the-stars-usa.sfc --output-dir /private/sots-native-build
```

`tools/platforms/prepare.py` checks the receipt, generated sources and pinned
runtime before writing platform build commands. CMake and Gradle may fetch build
dependencies. Preparation receipts record generation only.

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

Launch the resulting executable with `--no-launcher --rom /path/to/your/game.sfc`.
Keep it in a private writable folder so the game can save settings and progress.
Keyboard and gamepad input use SDL. The Windows Companion is a separate app.
For a cross-build, pass `--toolchain-file` with a target Linux CMake toolchain.
Use `--sdl-source` to build against a local copy of the pinned SDL3 source.

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

Use the prepared private sources from above with matching SDL3 **3.4.10** sources:

```sh
python3 tools/platforms/prepare.py --platform android \
  --source-build /private/sots-native-build --runtime /private/pinned-runtime \
  --sdl-source /private/SDL3-3.4.10 --output /tmp/sots-android-preview
```

That writes a Gradle application referencing your private native source tree.
With JDK17+, Android SDK36, NDK28.2.13676358, CMake/Ninja and Gradle available,
run the command in its `platform-plan.json` (`gradle --project-dir ...
assembleDebug`). The Android Gradle plugin is pinned to 8.10.1. Install CMake
and Ninja through SDK Manager, or set `cmake.dir` in the generated project's
`local.properties` to the installation containing `bin/cmake`. Gradle may fetch
missing build dependencies.
The local preview APK has been compiled and signed for ARM64 on Android 8.0 or
newer. Community testing is needed for ROM import, startup, graphics, sound,
touch controls, and controllers on physical devices.

### On-device setup development

The phone setup preview packages an Android ARM64 Python runtime and analyzer,
the Zig compiler, SDL3, and the pinned authored build sources. Pick a clean,
unheadered USA ROM in **Choose ROM**. The app generates and compiles the native
game locally, then opens it. Later launches reuse the installed module for the
same setup package. Keep the app open during first-time setup and allow room for
the unpacked tools, generated C, temporary objects, and the final library.

The APK contains no ROM or generated native game code. Phone compatibility,
setup time, and physical graphics, audio, touch, and controller behavior are
community preview checks. Have the APK version, phone model, Android version,
and the last setup step handy when reporting a problem.

The separate developer setup shell builds with SDL3 and the launcher Activities
alone. It uses a separate application ID and omits the phone toolchain.

```sh
python tools/platforms/prepare_android_shell.py \
  --sdl-source /private/SDL3-3.4.10 --output /tmp/sots-android-setup-shell
gradle --project-dir /tmp/sots-android-setup-shell assembleDebug
```

The preview setup worker writes the read-only module and a receipt under the app's
private no-backup directory. The receipt binds the module bytes, ROM identity, and
setup package. The document picker only imports the ROM. `prepare_android_phone.py`
stages the ROM-free build capsule and builds a Gradle project with the pinned tool
inputs. Developers can export its compiler recipe with `android/phone_compile.py`
from a matching NDK configuration. The third-party notices travel with the tools.

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

- The Linux x86-64 game compiled and linked against the Debian glibc sysroot
  using SDL3 with X11 and ALSA support. A single-core software-only Linux VM
  ran 180 frames each from a cold start and a copied battle checkpoint. Both
  runs exited cleanly and rendered offscreen. The battle run produced nonzero
  game audio. Physical playback, desktop graphics drivers, and physical input
  checks remain open.
- The Android ARM64 native library, SDL3, and Java Activities compiled, and a
  signed local test APK assembled successfully. Gradle also configured the
  native build from the new private-source preparation command. Testing on a
  physical Android device remains open.
- To report a problem, include the platform and version, the device or Linux
  distribution, your input device, and the steps to reproduce it. Share text
  diagnostics with personal paths removed. Keep ROMs and saves private.

## Frozen runtime compatibility

The Android adapter verifies the exact pinned desktop-host source before
force-including one Android-only compatibility header. The frozen local turbo
patch accidentally calls a desktop-only OpenGL setter on Android; its preceding
SDL renderer vsync update remains active. The adapter does not modify runtime
caches or affect Windows. A future runtime pin must review or remove this shim.
