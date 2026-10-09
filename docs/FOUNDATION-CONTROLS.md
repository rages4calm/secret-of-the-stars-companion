# Foundation demo controls

Launch `Start Foundation Demo.cmd` from the project root.
It now starts at the normal title screen. `Start Original View.cmd` starts at the
title with the optional improvements turned off for that launch.
`Resume Foundation Fixture.cmd` explicitly resumes a copy of slot 0.

| Action | Keyboard | Xbox-style controller |
| --- | --- | --- |
| Move | Arrow keys | D-pad or left stick |
| Talk / confirm | X | A / south button |
| Field menu / back | Z | B / east button |
| Hide / show enemy HP in battle | H; S also remains | Right-stick click; X / west also remains |
| Opening-chapter journal | J | Left-stick click |
| Start | Enter | Start / Menu |
| Fullscreen toggle | Alt+Enter, F11 or F12 | Keyboard shortcut |
| Rewind | F8 | Back/Select + right-stick click |
| Close rewind without changing time | Escape, Z or F8 again | B / east button |
| Select rewind time | Left / Right | D-pad Left / Right |
| Apply selected rewind time | Enter / Space | A / south button |
| Save browser | F7 | Back/Select + right shoulder |
| Load slot 0 | F1 | Select it in save browser |
| Save to slot 0 | Shift+F1 | Save it in save browser |

F1 loads slot 0, initially the supplied early outdoor checkpoint. Shift+F1 replaces that slot with
your current state. Slot and battery-save files live in `local/player-foundation/saves`.
Controller face labels above follow the new PC mapping; other controller labels
can differ. Keyboard buttons are editable in `keybinds.ini`; controller bindings
are under `[GamepadMap]` in `config.ini`. Restart after editing.

The new optional presentation defaults to enhanced original pixels and a small
enemy-HP panel during battle. Edit `local/player-foundation/foundation.ini` and
restart to set `EnhancedPixels=0` or `BattleInfo=0` independently. Original View
temporarily disables them without changing those saved settings. `BattleInfo`
here means the native HP panel, not the complete third-party Battle Info hack.

`FastMenus=1` now completes the field menu's row uploads and slide animation much
sooner. The checked single-party outdoor menu opens in about 50 ms and closes in
one frame, excluding controller/display latency. Set `FastMenus=0` and restart
for original pacing; Original View also disables it for that launch. Unsupported
window contexts retain the original waits. Your existing button bindings are preserved.
Interactive submenu drawing retains original timing to prevent missing borders.
Wait for a panel to finish drawing before backing out; rapid back presses during
construction are not buffered yet.

The synchronized Direct3D 11 presenter now replaces the former software default,
whose actual VSync was off despite the setting. Existing profiles are backed up
before changing only Renderer, OutputMethod and VSync. Fullscreen, sound, custom
bindings and saves are retained. Other custom renderer choices remain editable.

Fullscreen adapts the window to your display. Enhanced pixels use a color-preserving
2x edge pass; replacement HD artwork and true widescreen scenery are later work.
Leave `ExperimentalFieldWide=0`: the research mode exposes unloaded map columns.
Original SPC audio remains available; no compatible MSU-1 driver/pack is verified.
Cold checkpoint resumes now restore the audio clock, including guarded older states.

The optional `Journal=1` card shows David's opening Crest of Stars/mountain lead
after the original introduction event. It starts closed and derives the lead
from restored game progress. Press J or click the left stick again to close it.
It does not pause gameplay. Later chapter objectives and crest completion are
not tracked yet. Set `Journal=0` to disable it; Original View disables it too.
