# Broader widescreen release: October 9, 2026

Native 0.1.7 and Companion 0.1.2 are installed. Their exact qualified artifacts
are recorded in `local/evidence/build-receipt.json` and
`local/evidence/companion-receipt.json`. The native SHA-256 is
`9344cef6680e6d9811ce9ae950cdb5acc5da24e5c08519d539be604791ace5dd`;
Companion is `e26ba4409c062b8f6c3c8ddbd176fe5f1ced43e9325624a05fcfde3fd3789bb8`.
Installation backup: `local/owner-backups/map-release-20261009-145437`.
All owner saves, settings and both original/working ROMs retain their hashes.

## Presentation and coverage

The optional Companion Widescreen checkbox pairs terrain and regular actors.
Expansion keeps a stable 400-pixel canvas, preserving the original 256-pixel
center. Checked standard-map resources, the original title panorama and all 16
authored battle-side layouts use original graphics. Battle extensions compose
original cells; they are additional layouts, not hidden original widescreen art.
Unsupported states retain the centered original picture with side bars.
Enhanced pixels apply independently throughout normal presentation. Widescreen
remains off in the owner's existing settings until explicitly selected.

The map release has 262 passing gates, 1,121 paired captures and 42 successful
candidate processes, plus one expected crashing old-build control. Natural
routes cover the world, Likado, opening houses/island, title, forest combat,
menus, transitions, restore and rollback. Original center, guest framebuffer,
CPU/state traces and captured guest memory remain identical. The primary
resource decoder also matches all 248 unique original primary tuples through
3,053,568 host-decoded grid words and 10,416 boundary words. Those tuples are
resource identities, not a count of completed playable maps.

All 16 battle resources pass actual-PPU host checks covering 1,835,008 original
center pixels, 16,704 independently checked margin words and 288 refusal cases.
Only forest combat has natural gameplay coverage; other layouts are host
fixtures. Regular actors require original producer/completed OAM packet identity.
Party, special/composite actors, wrapping-world actors, secondary stream
provenance and full campaign coverage remain open.

## Buffer safety and steady playback

A reproduced old-build crash came from a negative mosaic run length after a
mid-frame size/cache mismatch. The loop could read beyond the priority buffer.
The runtime patch refreshes derived mosaic state at the render boundary, uses
signed phase in margins and bounds its pixel loops. Original effects remain
enabled. The focused harness passes captured mismatch, empty-span, signed-phase
and original-center parity checks; formerly crashing natural transitions pass.
See [the repair evidence](FOUNDATION-MOSAIC-REPAIR-2026-10-09.md).

An initial audible verification failed because a synchronous forensic dump
wrote about 616 KB across 14 files, occupying about 134 ms on the gameplay
thread. Preserve its failed report:
`local/runs/frame-audio-20261009-144654/report.json`. Forensic guest captures
remain in separate parity checks; steady-playback checks now omit those dumps.
The clean rerun, `local/runs/frame-audio-20261009-145024/report.json`, passes
seven Windows D3D11/VSync cases at about 60 fps, with zero post-startup audio
underflows, missing audio frames or audible overflows. This is bounded measured
coverage, not a guarantee for every system load or an owner listening test.

## Installation and continuation

The Companion's 52 backend and nine UI checks pass, together with six actual
launch routes against the exact native candidate: title, Original View, selected
v3 resume, guarded legacy resume, isolated wide preview and optional HD-frame
preview. Installed project-root EXE and CMD visible windows pass. Actual
installed native helpers pass title/legacy-copy and protected-file checks in
`local/runs/map-installed-20261009-145641/report.json`.

Controls, checkpoints, audio initialization and optional HD frames have focused
current-artifact checks. New physical-controller or full-campaign certification
is not claimed. The original guest CPU budgets and activation/collision rules
remain unchanged. Full replacement HD world artwork stays deferred; MSU-1 still
requires a verified compatible game driver and pack. Current execution remains
the documented compatibility-led foundation, with unresolved native/AOT coverage.

The additive authored-source bundle and final protection checks are linked by
both local receipts and `local/evidence/map-release-final.json`. Subsequent
party and secondary-scene work starts in private prototypes/contracts; do not
overwrite this qualified source/artifact without a new matching receipt.
