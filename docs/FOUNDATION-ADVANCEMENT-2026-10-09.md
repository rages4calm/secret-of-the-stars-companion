# Secret of the Stars foundation advancement

**Later October 9 update:** [field-menu repair and native UI interface evidence](FOUNDATION-MENU-2026-10-09.md)
supersedes this document's installed executable/receipt list. Its `FastMenus`
improvement is installed with protected saves. The earlier evidence below remains
historical; all native-coverage, reference-fidelity, HD/widescreen and MSU limits remain.

October 9, 2026. This continuation supersedes the October 8 proof's installed
build, forced-resume behavior and pending owner-test statements. The owner
confirmed video, sound, controller operation, a Ctrl+R restart, outdoor movement
and entering combat, then authorized autonomous work. The foundation remains a
hybrid Windows game: most guest CPU execution is interpreted. No complete native
conversion, campaign certification or HD/widescreen release is claimed.

## Installed player build

Run `Start Foundation Demo.cmd`. It follows the normal boot/title flow rather
than silently loading the research checkpoint. `Resume Foundation Fixture.cmd`
explicitly resumes a disposable copy of slot 0; F1 still loads that slot in-game.
`Start Original View.cmd` disables optional presentation for that launch without
changing saved preferences. See [the controls card](FOUNDATION-CONTROLS.md).

The installed release SHA256 is
`72d48a45a36486df3fb0ade62be6c9b8c4b220d45ae21ea98bcdcd2f4c0be3bf`.
The pinned shared runtime remains
`7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`.
The refreshed runtime patch SHA256 is
`0f5147747c9a0158dea72843b590a47c8fff1939c4ddd540f60554163993e69a`.
All 24 authored source/config files in `native/foundation/authored-files.json`
match the live build tree. The shared patch passes application checking against
the pinned Git tree. Original assets and generated ROM-derived CPU code stay local.

Before work, the player profile was backed up under
`local/owner-backups/20261008-234156`. Installation also backed up the previous
executable/settings/saves under
`local/player-foundation/backups/20261009-003108-380`.
The original ROM, both SRAM files, slot 0 checkpoint, `config.ini` and
`keybinds.ini` retain their exact hashes. The installation was prepare-only;
runtime verification used a separate copied profile and never advanced owner progress.
See `local/evidence/player-upgrade-20261009.json`.

## Implemented and qualified changes

| Feature | Evidence and scope |
| --- | --- |
| Title-first launch and explicit resume | Windows launch tests confirm normal launch does not resume. A refused pending state remains intact and does not create a success marker. |
| Cold-resume audio repair | Actual Windows SDL/WASAPI callback PCM becomes nonzero at about 0.271 seconds for the guarded legacy state and 0.0167 seconds for a new v2 state. No menu interaction is needed. Two new-state guest replays match. |
| Controller, rewind and fullscreen | Virtual SDL gameplay input matches the scripted equivalent and differs from idle; keyboard and controller rewind exits resume the guest. Actual Windows fullscreen flags transition through all configured shortcuts. The owner previously confirmed the repaired original presentation in combat; this enhanced build's new presentation is automated/visually inspected only. |
| Native enemy-HP panel | Independently selectable display reads enemy slots without changing guest state. X on the controller, or S on the keyboard, hides it. Original guest memory/video state remains identical; hiding restores the original composed surface. Enemy labels are IDs pending a named enemy-data interface. |
| Enhanced original pixels | Independent color-preserving Scale2x-style pass produces a 512x448 composed surface. Field/battle captures preserve original source colors, change diagonal edges versus nearest-neighbor output, and leave guest state unchanged. This is enhanced original art, not replacement HD artwork. |
| Native gameplay-edit proof | Private diagnostic changes two recorded lethal physical hits from 13/12 to 26/24 while the original kill/subtract and battle completion paths run. The normal player launch clears this diagnostic switch. |
| Editable tile import/export | Indexed PNG export of 512 background and 256 object tiles round-trips exactly to captured 4bpp bytes. A one-pixel edit changes only tile 0; the other 511 background tiles remain identical. No ROM write, live injection or runtime HD asset binding is implemented. |
| New checkpoint rejection checks | Corrupt CRC, truncation, valid-CRC foreign identity, unknown schema and incorrect payload layout all reject before guest mutation, preserve the input and match a clean boot's six captured guest surfaces/memories. |

Audio failure diagnosis: the earlier guarded checkpoint restored SPC/DSP state
without the host's APU frame clock. A cold process resumed from a zero clock
against a much later guest anchor and stalled audio until a music-port change
rebased it. Schema v2 serializes the four 64-bit clock values. Guarded v1 states
recover a clock from the restored guest/port anchors; their source files are not
rewritten. The successful host resume resets its audio output timeline. The
identity remains `sots-clean-foundation-v1` for this explicitly supported v1/v2
family, while the internal payload schema is versioned separately.

The HP panel and edge pass are game-owned C. The generic Scale2x rule was checked
against its [published algorithm](https://www.scale2x.it/algorithm). Targeted
read-only inspection of EarthBound's EPX renderer informed the palette tolerance;
EarthBound and Zelda installations and saves were not modified.

## Battle and patch-first evidence

Staged ordinary input reached Likado, the David story gate, the field and a
two-enemy battle. A copied pre-command checkpoint at
`local/runs/world-cave-a/saves/save0.sav` supports repeatable combat.
`fixtures/battle-badbad.txt` is the historical fixture filename; the recorded
encounter is two Red Slimes, not Badbad. Ray's attacks do 13 and 12 damage,
an enemy hit reduces HP from 32 to 31, and victory displays 4 EP and 4 Gold.
The final original-damage build matches the earlier battle baseline across seven
capture points, including WRAM, VRAM, SRAM, OAM, CGRAM and the guest framebuffer.
See `local/evidence/battle-release-reference.json`.

The native diagnostic at 00DC97 runs immediately before the interpreted original
`CMP $0497`. It guards the original instruction, 16-bit accumulator, Y=1,
battle mode, enemy-slot pointer, enemy ID 1 and max HP 11, then adjusts the
original damage value. Only two lethal physical hits are qualified. Nonlethal,
other enemies, overflow, multitarget attacks and compiled replacements are not.
Future AOT conversion of that path must explicitly call the native modifier.
See `local/evidence/native-damage-proof.json`.

The source-available [Battle Info hack](https://github.com/BlueImp78/Secret-of-The-Stars-Battle-Info-Hack/tree/650721747fd808daeb4e2a9745f16150b2d00c91)
was assembled with pinned Asar 1.91 after explicit FF padding to 2 MiB, with
verified checksum and a separate regenerated/compiled hybrid project.
Patched ROM SHA256:
`16acc6e9bd659080597192e920b133056fd95704e00d42861dab1a15087d7081`.
`tools/build_battle_info_variant.py --compile` reproduces that private variant;
its recipe/source/tool receipts are in `local/patch-proof/battle-info-padded`.
It boots, but its six hijacks and full HP/EP/drop behavior have not yet been
qualified in combat. It is not installed as the player build. No license file was
found in the pinned source; retain the private-use evidence boundary.
The player setting `BattleInfo` currently enables our native HP panel, not the
whole third-party hack.

An attempted combined fresh-boot route did not reach the intended battle in
either tested path. `fixtures/research/opening-to-battle-attempt.txt` is retained
as unqualified research. The staged recipe and copied battle replay pass;
they do not establish a single cold-boot end-to-end battle script.
`local/evidence/battle-route-recipe.json` records checkpoint/input provenance.

## Rendering, assets and remaining gates

The experimental compositor produces a 400x224 field view while retaining the
original center and keeping battle width at 256. Inspection shows garbage in
outer columns because the game has not populated those tilemap slots.
`ExperimentalFieldWide=0` is therefore the player default. The report's mechanical
checks pass, but `wide_visual_gate_passed` is explicitly false. Real widescreen
needs the game's map loading/streaming and actor visibility rules before enabling
it. In these checked field/battle scenes, BG mode 9 means Mode 1 with BG3 priority;
populated Mode 7 matrix registers alone do not prove Mode 7 rendering.

`tools/foundation_assets.py` supports local indexed-tile round trips:

```powershell
python tools/foundation_assets.py local/runs/native-damage-original/dump/battle-ready local/assets/new-bg-export --base 0 --count 512 --palette 1
python tools/foundation_assets.py local/assets/new-bg-export/manifest.json local/assets/new-bg-import --import-sheet local/assets/new-bg-export/tiles-indexed.png
```

Use a fresh output directory for each operation. Keep indexed PNG dimensions and
indices 0..15. CGRAM palette content is separate from tile bytes. Tile identities
are captured VRAM offsets/content hashes; ROM compression, persistent resource
IDs and animation bindings remain unproven. This export/import is a tool gate,
not an in-game replacement-art gate. Actual HD replacements and added content
still need explicit game data/render interfaces.

MSU-1 remains conditional. Exact-title/alias research has not verified a compatible
Secret of the Stars/Aqutallion driver and music pack. No MSU option or unrelated
soundtrack was added. Original SPC audio is the qualified audio path.

The seven experimental AOT WRAM differences and independent-reference NPC/timing
differences from October 8 remain unresolved. Do not promote more native routines
or declare the reference-fidelity gate closed from these enhancement checks.
Reward messages are verified, but candidate memory words at 624C/435C/0A50 are
temporary animation/stat/text consumers rather than established EP storage.
Do not turn their observed delta of four into an EP multiplier.

Next focused work: identify map streaming for meaningful side scenery; establish
named enemy/resource data and live replacement-art bindings; qualify the patched
hack at its actual dispatch points; then prove a small added-content interface.
Continue with copied checkpoints and finite fixtures, preserving an original path.

## Qualification receipts

`local/evidence/build-receipt.json` points to the current executable and reports:

- `local/runs/controls-20261009-002449/report.json`
- `local/runs/audio-20261009-002449/report.json`
- `local/runs/desktop-20261009-002842/report.json`
- `local/runs/presentation-20261009-002112/report.json`
- `local/runs/checkpoints-20261009-003207/report.json`
- `local/evidence/battle-release-reference.json`
- `local/evidence/native-damage-proof.json`
- `local/evidence/tile-import-proof.json`
- `local/evidence/player-upgrade-20261009.json`

Tests are reusable Python tools under `tools/`; diagnostics never need the owner's
profile. The battle/presentation captures and extracted tiles remain ignored local
assets. A representative inspected preview is
`local/runs/presentation-20261009-002112/battle-enhanced-info/present.png`.
