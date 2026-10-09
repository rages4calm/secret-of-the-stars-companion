# Secret of the Stars Companion

Windows launcher for the qualified local native foundation. Familiar Companion
navigation and reusable UI patterns come from the owner's EarthBound/Zelda
projects; this game's settings and launch adapter are title-specific.

`dotnet publish Companion/Companion.csproj -c Release -o local/companion-build`
builds a self-contained Windows x64 application. The qualified installation
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
hands a copy to the original guarded launcher. Preview actions use fresh
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

`--visible-test <report.json>` opens a real on-screen window, verifies native
visibility, taskbar presence, working-area intersection and its main-window
handle, writes the report, then closes. Interactive launches also record their
own window readiness under `local/companion/logs`. Offscreen capture remains
separate from interactive verification.
