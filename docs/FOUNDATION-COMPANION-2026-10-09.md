# Companion launcher continuation

Historical 0.1.0 checkpoint. Read
[the 0.1.1 visible-launch repair and widescreen integration](FOUNDATION-COMPANION-FIX-2026-10-09.md)
for current installation, and [the actor qualification](FOUNDATION-ACTOR-WIDE-2026-10-09.md)
for native 0.1.6. The owner-reported invisible CMD launch reproduced after this
original qualification; offscreen capture had not verified interactive visibility.

The title-specific Companion launcher **0.1.0** is qualified and installed in
`local/companion`. Start it with the root
`Start Secret of the Stars Companion.cmd`. The launcher receipt is
`local/evidence/companion-receipt.json`; executable SHA-256 is
`cc0a4360f59d1e2c9cd7762f6d386470b1808d397e6918d04120678d7a4f915f`.
The exact native game remains the qualified audio-fixed **0.1.5** artifact,
SHA-256 `987554031d343fbc54e89b4fbc54e40058147aa6f26e75ee486391b4ff00c00e`.
This continuation adds a launcher and selected-checkpoint adapter. It does not
supersede the game's existing execution, audio, timing or visual coverage.

## Player workflow

The six pages are Play, Display, Audio, Controls, Enhancements and Saves.
The familiar navigation and useful WinForms patterns were adapted from the
owner's EarthBound Companion under its permissive original-code license.
Read-only references did not change EarthBound or Zelda installations.
This title has a new settings/launch backend; no other game's save conversion,
randomizer, gameplay code or original data was imported.

Play starts at the title. Resume requires choosing an existing checkpoint
from this profile's `saves` folder. It passes a prepared copy to the original
guarded restore path, including accepted v1 checkpoints; the source is never
converted or rewritten. A pending copy conflict or changed source is reported
before launch. This is distinct from using the game's own save menu.

Display offers fullscreen, window scale, VSync, renderer and enhanced pixels.
Audio offers original audio and volume. Controls exposes player-one input and
stick deadzone as a percentage while preserving its exact original raw value
until edited. Custom keyboard/controller bindings are retained. Enhancements
offers fast checked field menus, battle information, the bounded opening lead
journal, scanline sprite limits and the optional finer menu-frame artwork.
The shortcut card includes H/right-stick for enemy HP, J/left-stick for the
journal, F11/F12/Alt+Enter for fullscreen and F8/Escape/Z/controller B for rewind.

Changes become effective after **Apply settings**. Apply validates edited
values, checks the loaded file identities, refuses a running game and makes
verified config backups before replacing files. Comments, unknown keys,
custom bindings, encoding/BOM, line endings and unrelated values survive.
Known duplicates are updated consistently when that setting changes.
Two-file failures restore our completed write while preserving concurrent
outside edits. Backups live in the profile's `backups/settings-*` directories.

Both preview actions get fresh isolated profiles and prepared fixtures.
They now inherit the chosen source profile, including a `--profile` test
override, rather than silently using another installation's settings.
Likado expands checked terrain only; actors beyond the original view and other
maps are not expanded yet. The optional menu preview replaces eight border
tiles. A full replacement-art pack is deferred. No working MSU-1 driver/pack
has been established, so the launcher offers the original soundtrack.

The navy/gold interface uses a local real Likado capture, loaded at runtime
from `local/evidence/companion-play-scene.png`. Neither the source bundle nor
the Companion executable embeds original game imagery. The self-contained
Windows x64 launcher includes .NET/Windows Desktop 8.0.27; its license and
third-party notices are alongside the installed executable.

## Focused qualification and protection

`local/runs/companion-20261009-131645/report.json` records the exact artifact:

- 48 backend/integration checks: byte/BOM/duplicate preservation, exact no-op,
  validation, verified backup, running/stale refusal, partial-write rollback,
  concurrent-edit recovery, structured paths containing spaces, inherited
  diagnostic removal and explicit checkpoint selection/conflict guards.
- Seven actual WinForms interaction checks: controller checkbox and percent
  deadzone reach native settings, dirty state holds Play until Apply, Apply
  restores Play, battle-information settings reach the game config, and saves
  and keybindings survive with separate verified backups for both edits.
- All six actual self-rendered pages were inspected for clipping and layout.
- Real paced Windows GPU game startup through Play, Original View, selected
  v3 and legacy v1 checkpoints, Likado preview and menu-frame preview. All
  start/exit successfully; title actions do not auto-resume. Both preview
  profiles inherit explicit window/audio settings from the selected source.
- Direct PowerShell negative tests reject foreign checkpoints and conflicting
  pending copies while preserving the pending bytes.

The installed bytes also pass the root launcher helper's cold UI capture and
a fresh-profile native title-first GPU launch in
`local/runs/companion-installed-20261009-1320`. Install retains all twelve owner
top-level/save files by hash, including the game executable, original v1
checkpoint and SRAM. Verified backup:
`local/owner-backups/companion-release-20261009-131812`.
The original owner ROM and separate reference projects remain untouched.
Native authored files and the runtime patch are unchanged in this continuation.

These checks do not add physical-controller, human-listening or campaign
certification. Ongoing audio/frame-budget evidence remains the separate 0.1.5
presentation/audio qualification. Cold boot reaches the title flow; the known
headless black title fixture still does not qualify visible title graphics.

## Reproduction and next work

Build with `dotnet publish Companion/Companion.csproj -c Release -o local/companion-candidate`.
The checked SDK was 10.0.300 and the runtime package version is pinned to 8.0.27.
Run `python tools/check_companion.py --exe "local/companion-candidate/Secret of the Stars Companion.exe"`.
Use `tools/install_companion.py` with that candidate and its successful report
after refreshing `Companion/authored-files.json`; installation is additive and
backs up protected owner files. Package with `tools/package_foundation_source.py`.
Source packaging explicitly manifests authored Companion files and excludes
`bin`, `obj`, binaries, captures, ROM-derived code, ROMs and saves.

Continue from `docs/FOUNDATION-WIDE-ACTORS-2026-10-09.md`: the actual actor
records and drawing rejection provide a bounded side-only rendering seam.
Do not globally widen guest activation/collision or change CPU budgets to
solve visibility. Keep normal terrain width off until actor and scene coverage
are qualified. Further verified journal events, full native execution and
compatible optional MSU-1 remain separate work.
