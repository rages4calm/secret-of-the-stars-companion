# Native field-menu continuation

October 9, 2026. The owner reported delayed field-menu opening and closing and
asked to continue foundation work. This continuation supersedes the installed
binary in the earlier advancement while preserving its decisions and limits.

## Installed result

Use `Start Foundation Demo.cmd` as before. Normal startup still follows the title
screen. `FastMenus=1` is now enabled in `local/player-foundation/foundation.ini`.
Existing saves, original ROM, `config.ini` and `keybinds.ini` are unchanged by hash.
The settings migration adds only the missing FastMenus preference; an existing
`FastMenus=0` is preserved. Independent enhancement settings remain editable.
`Start Original View.cmd` disables FastMenus and optional presentation for that
launch without changing stored preferences.

| Checked outdoor menu | Original | FastMenus |
| --- | --- | --- |
| Open to complete labels and HP/MP panel | 21 guest frames, about 350 ms | 3 frames, about 50 ms |
| Close to both panels disappearing | 8 guest frames, about 133 ms | 1 frame, about 17 ms |

These are guest-frame measurements at nominal 60 Hz, excluding physical controller
and display latency. The improvement is deliberately small and bounded: it batches
the game's field-menu transfers/slides without advancing extra game/world frames.
It does not promise instantaneous behavior for every screen or party composition.

Current release SHA256:
`a34aa2a239b2593bba71e04637946082e28fac2a1b4d5eb9fbdbbacefdc9b2ea`.
Previous qualified build:
`72d48a45a36486df3fb0ade62be6c9b8c4b220d45ae21ea98bcdcd2f4c0be3bf`.
The runtime pin and shared patch are unchanged. The authored manifest now contains
26 files, synchronized with the generated build's authored subset.

Backups before installation:
`local/owner-backups/pre-menu-install-20261009-053409` and
`local/player-foundation/backups/20261009-053410-402`.
The upgrade receipt is `local/evidence/player-menu-upgrade-20261009.json`.
An installed-profile copy passed a Windows/audio menu replay; first nonzero SDL
callback audio was at 0.271 seconds. Its menu/field VRAM, SRAM and CGRAM match the
qualified fixture. No test advanced the owner profile.

## Diagnosis and native execution contract

The guest sees the menu-button press in the expected frame: diagnostic input and
pressed word at 02E3 change on host frame 31. The original menu finishes at frame
52. Enhanced pixels are not the cause: original/enhanced guest captures match,
and median enhanced composition costs about 0.25 ms in Windows. Most elapsed time
is the original staged menu routine, not host input processing.

A separate Snes9x fixture also takes 21 frames to open its menu. That independent
route ends inside Ray's house rather than the native outdoor checkpoint because
the earlier timing/NPC divergence persists. It is corroborating animation evidence
in a second scene, not an exact scene match or a closed fidelity gate.
The private reference frames are under `local/runs/menu-reference`.

`foundation_menu.c` registers a pre-opcode hook at the interpreted 00FF03 wait
entry. Only these validated UI wait callers are eligible:
0291CD, 029242, 008514, 008675, 008692, 0086B4 and 0086CF.
The scope requires field mode 1, D=0A00, DB=1, an 8-bit accumulator and a bounded
active coroutine stack. That stack must contain both a validated field-interaction
JSL return and a validated menu-phase JSL return. Full original JSL operands are
checked for the four menu phases. Unrelated story waits, polling, mandatory
first/last waits and unsupported transfers keep their original behavior.

The field dispatcher at 018C00 leads to menu setup at 02911B, called through the
field interaction return at 0188A4/0188BE. Menu-phase returns are 029136 (02910F),
02913F (00FF3B), 029152 (02C000) and 029162 (00FF23). These are observed clean-USA
execution points, not a general ABI for other ROM variants.

The original NMI consumer at 008118 exposes a concrete UI data interface:

| Data | Meaning in the checked path |
| --- | --- |
| WRAM 02A0 | Transfer flags: accepted forms 81, 83, C1, C3 |
| WRAM 0100 onward | Records: byte count, word VRAM address, count tile words; zero terminator |
| Flag bit 1 | VRAM increment of 32 words rather than one |
| Flag bit 6 | Transfer only each tile word's high byte |
| BG3 map | Base VRAM word address 5000, Mode 1, checked map footprint |

The entire queue is checked before a write: record lengths/counts, buffer bounds,
targets and current PPU mode/map geometry. Transfers use the original PPU ports
2115/2116/2118/2119, keeping their cache/register side effects. After draining an
accepted queue, the hook resumes through the original RTL at 008460. A budget of
256 redirects resets each guest frame. This is not a blanket wait bypass or an
extra-frame/run-ahead scheme.

Menu context is derived from the active guest stack every time, with no persistent
native menu latch to serialize. A checkpoint saved inside the faster menu reloads
in a fresh process and reproduces subsequent menu and field captures exactly.
Future compilation of these UI instructions into AOT bodies must explicitly call
the native integration; interpreter hooks do not automatically patch authored C.

Earlier candidate bytes 0063..0067 are APU queue state, not a menu interface.
042B is a changing window/actor record in this path, not a persistent menu-active
flag. Do not build features around either discarded interpretation.

## Foundation work advanced: actual UI tiles

The decoded menu uses a 2bpp BG3 character region at VRAM byte offset 8000 and a
64x32 tilemap at byte offset A000. This captured menu uses 32 distinct tile IDs.
`tools/inspect_foundation_ui.py` exports cell positions, palette/priority/flip
attributes, tile content hashes and a transparent layer preview. After accounting
for the captured raster's first visible line, all 30,208 opaque BG3 preview pixels
match the guest menu pixels exactly. This validates the captured font/window
interface rather than inferring it from screenshot appearance.

`tools/foundation_assets.py` now supports both 2bpp and 4bpp indexed sheets. The UI
2bpp export/import is bit-exact; the existing 4bpp battle-tile round trip still
passes. A one-pixel edit changes only the selected 16-byte tile. An invalid 2bpp
index of four is rejected before output is created. Palette content remains a
separate asset from planar tile bytes.

```powershell
python tools/inspect_foundation_ui.py local/runs/fast-menus-20261009-052642/fast/dump/menu local/assets/new-ui-map
python tools/foundation_assets.py local/runs/fast-menus-20261009-052642/fast/dump/menu local/assets/new-ui-export --base 0x8000 --count 512 --bpp 2 --palette 0
python tools/foundation_assets.py local/assets/new-ui-export/manifest.json local/assets/new-ui-import --import-sheet local/assets/new-ui-export/tiles-indexed.png
```

Use fresh output directories. Captured IDs/addresses are not yet persistent ROM
resource identities, a text-encoding map, or live HD replacement bindings. The
preview omits scene scroll, sprite/priority composition and color math. Private
derived assets stay under `local/assets/menu-ui-20261009`; the proof receipt is
`local/evidence/ui-asset-interface-20261009.json`.

## Qualification and next steps

`local/evidence/build-receipt.json` references the current results:

- `local/runs/fast-menus-20261009-052642/report.json`: original-off exact regression,
  menu latency, early confirm/back, restored BG3 map, exact mid-menu checkpoint,
  copied two-Red-Slime battle and David dialogue regressions. No field batching
  occurs in either checked dialogue/battle replay.
- `local/runs/controls-20261009-052536/report.json`: SDL virtual-pad movement/menu
  input exactly matches scripted gameplay with FastMenus and enhanced presentation;
  all checked rewind/browser exits pass.
- `local/runs/audio-20261009-052536/report.json`: guarded v1/v2 cold audio and
  repeatable v2 replay.
- `local/runs/desktop-20261009-053115/report.json`: title-first launch, Windows
  fullscreen/audio, enhancement defaults/original override and refused resume.
- `local/runs/checkpoints-20261009-052915/report.json`: five damaged/foreign v2
  layouts rejected without applying guest state.
- `local/runs/presentation-20261009-052536/report.json`: presentation regressions;
  widescreen's visual gate still fails and remains disabled.
- `local/runs/menu-20261009-052745/report.json`: real Windows/headless host timing
  and exact original/enhanced guest captures with FastMenus enabled. Case names
  "original" here mean original pixels; the menu policy is recorded separately.
- `local/runs/menu-upgrade-settings-20261009-053234/report.json`: existing off
  preference and bindings preserved; missing FastMenus added with backup.

The owner previously confirmed physical-controller gameplay on the repaired
original build. This release has automated SDL gameplay coverage, not a new
physical-controller or full-campaign certification. The earlier seven AOT WRAM
differences and independent-reference timing/NPC divergence remain unresolved.
Most CPU execution remains interpreted.

Next focused work remains map loading/streaming for populated side scenery, then
persistent resource identities and a bounded live artwork replacement. The newly
decoded UI interface can support a small font/window replacement proof. Keep
original behavior available and qualify changes on copied fixtures. No broad
audit or another owner playthrough is needed. True widescreen, HD replacement art,
added content and a verified compatible MSU-1 driver/pack remain outstanding.
