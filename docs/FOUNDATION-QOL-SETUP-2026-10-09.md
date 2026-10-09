# Foundation and Companion 0.2.0

This continuation adds public source-first setup and the requested editable
reward rates, held movement boost and keyboard/controller hotkeys. Preserve
the original visual direction: enhanced original pixel art and genuine wider
scenery/actors, with replacement world artwork deferred. Widescreen remains
experimental and default-off; unsupported states keep the exact original center.

## Player controls

Companion **Enhancements** exposes independent battle XP and gold rates from
100–1000%, and movement boost from 100–300%. Rewards default to 100%; held
movement defaults to 200%. Original View disables these for that launch without
rewriting saved settings. Rewards scale the original completed battle total
once. Ordinary walking keeps original collision/event decisions and tile
completion; scripts, currents and unsupported motion retain original pace.
[Native seams, caps and restore contract](FOUNDATION-QOL-2026-10-09.md).

**Controls** edits the single player's keyboard and controller game buttons.
**Hotkeys** edits keyboard/controller actions, modifier/button chords, explicit
unbinding and all twenty checkpoint save/load slots. Defaults are Tab/R2 for
fast-forward and Left Shift/L2 for movement boost. Fast-forward offers hold or
toggle. Existing explicit mappings take priority; unchanged legacy settings
remain. Rebinding the HUD/journal removes their hidden hardwired shortcuts.
Escape and mapped cancel controls close overlays. Fast-forward/movement input
is cleared on focus loss, controller disconnect, reset and checkpoint restore.
Screenshot support remains OpenGL-only.

## Source-first setup

The ROM-free Companion builder freezes authored source, publishes a
self-contained Windows EXE with dependency notices and records an explicit
compilation receipt. The public CMD validates that exact EXE and opens Setup.
Setup validates an owned clean USA ROM by size/SHA without copying it, builds
the native foundation with progress and cancellation, or adopts a prior real
source receipt. Adoption creates a fresh isolated profile. Play starts at the
title; Resume accepts a selected profile checkpoint and launches a protected
copy. The public path needs no private development fixtures. Compile/adopt
status stays `compiled_unqualified`; adoption never manufactures gameplay proof.
[Prerequisites and instructions](../BUILDING.md).

## Exact artifacts and bounded evidence

Native EXE SHA-256:
`9241f79ea1a685e0932282c300081a90f9becf503f9a17c5fe6a94b34a08a7e0`.
Companion EXE SHA-256:
`f0cdd03358c0d97d70e0ebe74d27c11765fb9b7f87444f4c0fc242bc59f567ba`.
Runtime remains pinned to `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`;
the seventeen-file patch SHA-256 is
`526f7d87b5cf736ce8b57da9db5f4435cce8d33ed1686a587a6a02ca66d73318`.
The build freezes all 48 native and 19 Companion authored inputs.

The exact native artifact passed 104 reward/walking checks, 21 actual-C guards,
21 restore/menu/opening checks, 23 SDL hotkey/overlay checks, three ROM-free
binding probes, 247 map/widescreen gates and checkpoint/controller regression
checks. Seven Direct3D and three OpenGL paced audio routes passed; Direct3D
presentations were approximately 60 fps with no steady underflow, missing-frame
or audible-overflow counter increments. Playback tests omit synchronous full
forensic dumps, which can starve audio; independent headless parity captures
remain separate.

The exact self-contained Companion passed 60 source-first backend checks,
31 interactive QoL/binding GUI checks, a separate 180-frame public native boot,
and legacy backend/UI plus all six title/resume/original/preview launch routes
against copied profiles. GUI layout was checked at both supported window sizes.
The protected local installation uses those exact qualified EXEs; the root
Companion EXE and CMD have checked visible-window readiness. Owner saves,
checkpoint, configuration and original/working ROM hashes stayed unchanged.
These are finite routes and virtual inputs; full-campaign, listening and broad
physical-controller/hardware qualification remain open. Private receipts,
checkpoints and captures stay under ignored `local/`.

## Next work

Finish portable package/update/rollback handling, then qualify original large,
composite and wrapping actor producers with natural guest execution and complete
OAM transfers. Preserve the installed guards until original-center/guest state,
terrain/OBJ overlap and color math pass. Expand story/party/cutscene fixtures,
promote understood routines to native/AOT with state checks, and verify additional
journal milestones. Guest CPU headroom requires its own evidence; walking boost
and fast-forward do not establish a slowdown fix. MSU-1 remains conditional on a
verified compatible driver and track map. No ROM, generated game code, extracted
assets, soundtrack or saves are distributed.
