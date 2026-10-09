# Secret of the Stars Companion

Windows launcher for source-first setup and the qualified local native foundation. Familiar Companion
navigation and reusable UI patterns come from the owner's EarthBound/Zelda
projects; this game's settings and launch adapter are title-specific.

`python tools/build_public_companion.py` freezes source and
builds a self-contained Windows x64 application with retained dependency notices
and an explicit compilation receipt. Setup validates an owned ROM, builds or
adopts native source receipts and creates isolated title-first profiles without
private fixtures. The qualified development installation
lives in `local/companion` and its launcher receipt identifies the exact bytes.
Launch with the directly double-clickable project-root
`Secret of the Stars Companion.exe` after qualification. The
`Start Secret of the Stars Companion.cmd` entry also starts a visible window
and checks that it becomes ready. Use `--root <project>` and `--profile <copied-profile>` for bounded
tests. The root/profile are never inferred from unrelated game installations.

Opening the launcher reads settings. Apply writes only selected known settings
after validation, optimistic source-hash checks and verified config backups.
Custom lines/bindings remain; saves are never converted or edited by Apply.
Play starts at the title; Resume selects an explicit existing checkpoint and
hands a copy to the guarded native launcher. Public profiles launch their exact
recorded native EXE directly; historical qualified profiles retain the script
adapter. Preview actions use fresh
profiles. A running game must be closed before changing its settings.

The optional scene strip is loaded from ignored
`local/evidence/companion-play-scene.png`. It is original-game capture data and
is excluded from authored-source packages. No game imagery or original payload
is embedded in this project's source or executable. Unknown/deferred features
are not represented as working settings.

Widescreen is an optional, default-off pairing of expanded scenery and checked
regular-actor presentation. The shared field resource decoder supports original
map families; title scenery and qualified battle backgrounds have separate
presentation paths. The canvas stays wide through unsupported scenes, with the
original centered picture and side bars. Original controls and menus stay centered.
Untouched mixed custom terrain/actor flags are preserved; changing the checkbox
intentionally updates both. Campaign coverage and actors beyond regular field
records still need further qualification. No actor activation is changed.

Controls edits the single player's game buttons; Hotkeys edits keyboard/controller
actions and all twenty checkpoint slots. Enhancements provides 100–1000% XP/gold
and a held 100–300% movement boost. Default boost is Left Shift/L2; fast-forward
is Tab/R2, with a hold/toggle option. Existing custom mappings take priority.
Unchanged legacy values are retained, and changed conflicting or unknown
bindings are rejected before writes. Gameplay/native compatibility is gated by
the selected executable version; old binaries keep working without silently
accepting unsupported QoL edits.

`--visible-test <report.json>` opens a real on-screen window, verifies native
visibility, taskbar presence, working-area intersection and its main-window
handle, writes the report, then closes. Interactive launches also record their
own window readiness under `local/companion/logs`. Offscreen capture remains
separate from interactive verification.

Companion 0.3.0 adds source-profile Update and Rollback in Setup. Update creates
a new isolated profile with byte-verified copies of the selected source profile's
settings and saves. Only the selection pointer changes after successful copy
and validation. Rollback selects the retained earlier profile; newer progress
stays in its own folder and is never merged or discarded. Changed executables
require compatible checkpoint declarations and matching execution-state ABI.
Legacy receipts without that metadata can reuse the identical executable;
different builds require fresh adoption. These actions do not import the private
owner installation. Close the selected game and apply pending edits first.

The source-first portable package contains this self-contained GUI, authored
source and notices. It includes no native game or original data. Extract into a
new folder, verify with `tools/verify_companion_package.py`, then open the root
EXE or CMD. Native setup still needs the documented development tools and an
owned ROM. Clean packages can be extracted at another path; configured profile
receipts currently retain absolute paths and should stay in their original root.
