# Secret of the Stars: first local foundation proof

Historical October 8 proof. Read [the October 9 advancement](FOUNDATION-ADVANCEMENT-2026-10-09.md)
for the latest executable, title-first launcher, audio-clock recovery, enhanced
presentation, battle/edit/import evidence and remaining gaps. Earlier installed
hashes, forced-resume behavior and pending physical-confirmation statements below
are retained as history and superseded by that continuation.

October 8, 2026. The pinned snesrecomp route now builds a local Windows executable,
reaches a new game and the outdoor map through ordinary input, and restores a copied
checkpoint correctly in a fresh process. This is an early hybrid foundation, with
most CPU execution still interpreted. It is not a complete native conversion or an
HD/widescreen release. Read this after the assessment; it supersedes its pre-build
status statements.

## Use the local demo

Double-click `../Start Foundation Demo.cmd`. The first launch resumes an isolated
fixture outside the starting house, with the test character named A. Later launches
use the normal title screen; F1 loads slot 0. Arrow keys move, X maps to SNES A for
talking/confirmation, and Z maps to SNES B for the menu/cancel. Alt+Enter toggles
fullscreen; F11/F12 now also toggle fullscreen. F8 opens rewind and closes it again;
Escape or Z also cancels rewind. F7 opens the save browser. Shift+F1 saves slot 0.
Check `local/player-foundation/keybinds.ini` for
the generated full key map after launching. Ctrl+R resets to start a new game.

The script verifies the executable and clean working ROM, uses a separate
`local/player-foundation` profile and preserves existing settings/saves. It enables
original audio, an enlarged window and normal pacing. The owner subsequently
confirmed working video, audio and basic controller input, then reported becoming
stuck in rewind while searching for fullscreen. The controls/launch repair below
supersedes the original untested desktop status. Enlarging the original pixels does
not constitute HD replacement art.

## What actually passed

- The original ROM still hashes to
  `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.
- Release build and a separate trace build pass on the existing Clang/SDL toolchain.
- `fixtures/clean-to-outdoors.txt` runs 16,554 simulated frames from a clean boot:
  opening/prelude, title, name entry, starting house, directional movement, Sonya's
  greeting and the indoor-to-outdoor transition. No WRAM pokes or fabricated game
  state are used. Captures and coverage are under `local/runs/clean-to-outdoors`.
- An opening checkpoint saved at frame 4,280 restores in two fresh processes.
  Both continuations match each other and the uninterrupted run for 6,586 frames:
  WRAM CRC and CPU registers on every traced frame (excluding the host frame number),
  plus exact WRAM, VRAM, SRAM, OAM, palette and framebuffer captures at three points.
- Five checkpoint controls reject corruption, truncation, declared-length damage,
  a foreign identity with a valid CRC, and a wrong title schema with a valid CRC.
  The post-rejection WRAM matches clean boot. The rejected copies remain on disk.

Tests use headless software rendering, dummy SDL devices, physical gamepad input
disabled and audio output disabled. Their unpaced throughput is not a measured
gameplay/presentation rate or proof of correct audible music.

## Runtime fixes and execution evidence

Runtime pin: `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`.
The offline scaffold initially failed to compile/link because networking calls
were unguarded. The local patch adds guards in the desktop host and save menu.
The trace build also needed `errno.h` on Windows.

The stock scaffold's hardware-only snapshot restored repeatably but resumed the
wrong execution path: it stayed on the star scene waiting in the SPC upload routine,
while a fresh run returned to the title. The game-owned adapter now serializes the
runtime's existing CPU/interpreter/APU execution residue and the beam driver's resume
PC/WAI state. It applies them after generic load cleanup. A guarded title identity,
CRC, exact size/version and extension preflight reject incomplete or foreign states.
These checkpoints are specific to the pinned build/schema; do not import the earlier
unguarded proof snapshots or promise cross-build campaign compatibility.

`Observed_00816B_M1X0` was generated from an observed call. A bounded trace confirms
its native entry at frames 50–52. Six captures retain identical framebuffer, VRAM
and SRAM compared with the interpreter-led baseline, but seven WRAM bytes differ at
`1BCC`, `1BCE`, `1BD0`, `1BD1`, `1DAB`, `1DAD`, `1DAF`. Their semantics and safety
have not been qualified; the promotion is experimental. No routine's semantic name
is invented. Generated IRQ bodies alone did not establish active native coverage.

The outdoor fixture logs 435 distinct gap tuples. The report's `total_tier_hits=0`
counts particular generated tier-down dispatches, not all interpreted execution or
compiled entries. Do not convert either value into a coverage percentage.

All shared edits are retained in `../patches/runtime-foundation.patch`; authored
game/configuration files are in `../native/foundation`. Generated CPU code remains
in the ignored local checkout. The runtime's PolyForm Noncommercial license and
upstream notices still apply. No publication or ROM redistribution occurred.

## Independent reference and remaining gate

The independent snesref frontend loads official libretro Snes9x `1.63 fae2fea`.
Its DLL and the SDL2 development archive are hash-recorded in
`local/evidence/build-receipt.json`. It receives the same clean input and zero-filled
WRAM; it is separate from the built game.

The reference reaches the same opening room/dialogue, cutscene, title, name entry,
starting house and menu. The initial later-room capture differs by 12 WRAM bytes,
1,024 VRAM bytes and framebuffer channel values. SRAM matches. These differences
remain unresolved; do not dismiss all of them as harmless color quantization.

The full outdoor input route does **not** produce the same result in Snes9x:
the wandering NPC occupies a different position, so the script misses Sonya and the
house exit stays locked. The progression requirement is described in
[Darth_Ragnarok's walkthrough](https://gamefaqs.gamespot.com/snes/588647-tecmo-secret-of-the-stars/faqs/43520)
and was exercised naturally in the local build. Reference qualification needs a
scene-aware interaction fixture and investigation of the timing/state differences.
The prelude is not a demanding battle test.

Next gate: compare a real battle through actions/damage/rewards; validate the battle
slots; build the selected Battle Info source on a separate private ROM copy; then
prove an original-default native reward adjustment. Do not build a large enhancement
stack before the content/import and renderer interfaces are established.

## Preserved feature direction and reuse

HD redraws, enhanced original pixel art, true widescreen scenery, mod/content import,
new external content and editable menus remain separate work items. None is claimed
implemented by the current output scaling or shared-runtime capability flags.

The owner superseded the earlier last-resort restriction and authorized targeted
reuse of EarthBound/Zelda tools, assets and guides to speed development. Read-only
checks covered EarthBound's dev.32 handoff and two fixture/menu tools, plus Zelda's
workspace instructions, source notes and MSU test driver. Their profile-isolation,
real-input and save-protection practices are useful. No game-specific engine code,
artwork, music, ROM or personal save was copied, and neither project was modified.
Reuse suitable launcher/asset/audio tooling when its contract is actually needed;
their game rules and assets are not evidence for this title's formats.

MSU-1 is an optional requested enhancement. The current
[Zeldix master catalog](https://www.zeldix.net/t2684-alphabetical-list-every-snes-msu1-hack)
has no located Secret of the Stars/Aqutallion entry, and focused title searches found
no verified compatible driver/pack. This does not establish that none exists.
The pinned runtime implements MSU-1, but this game still needs a driver and correct
track mapping. Its launcher capability flag remains off. Retain original SPC music;
add a separately selectable compatible MSU-1 pack if one is verified.

## Rerun and evidence

From the project root, use a new fixture name for each run:

```powershell
python tools/run_foundation_fixture.py outdoor-check fixtures/clean-to-outdoors.txt --frames 17000 --save-at 16530
python tools/inspect_checkpoint.py local/runs/guarded-long/saves/save0.sav
python tools/compare_foundation_runs.py local/runs/guarded-long local/runs/guarded-restore-a --tags down left long-wait --trace-offset 4280
```

The finite runner copies the binary, inputs and any checkpoint into fresh folders,
records hashes and refuses a reused run directory. One-shot resume deletes only its
new temporary copy. A failed resume is reported as a failed fixture even though the
shared host otherwise continues to clean boot.

Local reports: `build-receipt.json`, `guarded-recovery.json`,
`recovery-comparator.json`, `snapshot-rejection.json`,
`aot-baseline-comparison.json`, `original-after-proof.json` under `local/evidence`.
Earlier `cold-replay.json` describes the faulty unguarded restores; it is retained
as diagnostic evidence and is superseded by the guarded recovery checks.

Build working directory: `local/native-proof/SecretOfTheStarsSNESRecomp`.
Regenerate with Git-for-Windows Bash `tools/regen.sh`, then `cmake --build build -j 8`.
The existing configured build uses Ninja, Release, Clang 22.1.8, SDL3 3.4.10,
`SNESRECOMP_FRAME_IMPL=LLE` and no networking/UI submodule. LLE here names the frame
compositor; CPU compiled/interpreted execution is a separate decision. The trace
build uses `SNESRECOMP_ENABLE_TRACE=ON` and is for finite diagnostics, not the demo.

## Desktop controls and launch repair

Controller support is mandatory. The single-player host now disables the unused
second input seat, so an SDL player-two preference falls back to player one. The
demo maps south/east buttons to SNES A/B (Xbox A confirms, B opens the field menu or
backs out). D-pad and left-stick support remain available. See
[the controls card](FOUNDATION-CONTROLS.md).

Rewind now accepts the configured keyboard cancel key and a second press of its
opening shortcut, with repeated key-downs ignored for that toggle. Escape and
controller SNES B close it, and the strip displays `ESC CLOSE`. Held cancel inputs
are masked until release before the guest resumes. F11/F12 and Alt+Enter are now
fullscreen shortcuts; F8 is rewind and F7 is the save browser. This also prevents
the old F11/F12 overlay shortcuts from surprising a player seeking fullscreen.

`tools/check_foundation_controls.py` exercises a virtual SDL gamepad through actual
device events. Its right/down movement, B field-menu open, A magic submenu and two
B exits produce identical per-frame WRAM/register traces and all guest dumps to a
scripted equivalent over 242 frames. The menu/submenu/field captures were inspected.
The idle control differs as expected. Separate pad, Escape, Z and F8 exit fixtures
all open and close rewind and resume the guest. The physical controller's repaired
mapping and exits still need owner confirmation; battle input and other controller
models are not qualified by this opening fixture.

`tools/check_foundation_desktop.py` verifies real Windows video/WASAPI audio startup,
player-one assignment for the connected Xbox controller, and actual SDL fullscreen
flags switching on/off through F11, F12 and Alt+Enter's configured key resolver.
It also checks first-start marking after successful resume and refusal of an invalid
pending checkpoint without discarding it or writing a success marker. The launcher
now records timestamped stdout/stderr logs, verifies reaching its main loop, retries
a pending resume and keeps unrelated tool paths/diagnostic variables out of player
launches. Windows PowerShell's own module directory is preferred when launched from
a parent PowerShell 7 environment.

The owner's original `0xc0000142` startup error was not reproduced in desktop tests;
the owner later confirmed a successful launch. No specific loader root cause or
permanent cure is claimed. Executable imports are system libraries, with SDL linked
statically; copying an arbitrary SDL DLL was not warranted by the import evidence.

The installed repair executable SHA256 is
`becccb3ba5d472f1668bac4a342e00c533505972b4122085ff0c793e6a67cd9a`.
The prior build and settings were backed up under
`local/player-foundation/backups/20261008-233436-444`; both save files retained their
exact hashes during installation. Current qualification evidence is
`local/runs/controls-20261008-233304/report.json`,
`local/runs/desktop-20261008-233418/report.json` and
`local/evidence/player-repair.json`. The earlier full opening/guarded-recovery proofs
belong to the pre-repair build; the new build is qualified for the copied outdoor
controller/desktop fixtures, not a new campaign run. The trace build remains the
earlier diagnostic version. Existing CPU/reference/HD/widescreen/MSU limits above
are unchanged by this controls repair.
