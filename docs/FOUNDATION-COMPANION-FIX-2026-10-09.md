# Visible launcher and Likado actor integration

Native **0.1.6** and Companion **0.1.1** are qualified and installed. This
supersedes the 0.1.0 launcher and 0.1.5 game installation status. Earlier
documents retain their original research and coverage limits.

Double-click the project-root `Secret of the Stars Companion.exe`, or use
`Start Secret of the Stars Companion.cmd`. Display now offers **Expanded Likado
view (experimental)**. Apply enables both guarded terrain and regular-actor
margin passes for the next launch. **Open Likado preview** uses an isolated town
fixture. Other maps and battles retain their original viewport; Original View
disables both passes. Owner settings have not been changed to enable expansion.

The CMD failure reproduced as a live process with no visible main window.
The wrapper had used `WindowStyle Hidden`; offscreen capture had missed that
interactive failure. Interactive startup now uses Normal, waits for an actual
main-window handle and logs readiness. Companion also recovers inherited hidden
startup and verifies its own native visibility, taskbar presence and on-screen
bounds. Offscreen capture stays hidden. The self-contained Windows x64 EXE finds
the project from its own directory even when started from TEMP.

## Artifacts and preservation

- Game SHA-256: `b88a6966bfe6c2a2df7a5a07e291c24f0db76366f712e793d7485c3477e96d8b`.
  Canonical `local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe`
  and `local/player-foundation/SecretOfTheStarsSNESRecomp.exe` match the candidate.
- Companion SHA-256: `2388c4de86502e481f0f0016053e8d4f4ce77daf7ffa8df51c6b14bc2e174a63`.
  Project-root and `local/companion` EXEs match the candidate.
- Both local receipts identify verified backups, qualification and the additive
  authored-source bundle. Settings, bindings, SRAM and checkpoints remain
  byte-identical. Only the game executable changed in the player profile.

## Qualification

`local/runs/companion-20261009-135020/report.json` passes 52 backend checks,
nine copied-profile WinForms interaction checks and six actual native routes:
title-first Play, Original View, selected v3 Resume, selected legacy v1 Resume,
expanded Likado preview and optional menu-frame preview. Source saves and
preferences survive every route. Wide preview requires paired flags and
positive actual actor-margin counts. Original View disables the actor observer.
Six page captures exist; the new Display controls were visually inspected.

`local/runs/companion-wide-20261009-134447/report.json` records the source freeze
and four real-window tests, including hidden-parent recovery. Post-install
`local/evidence/companion-actor-installed-windows.json` verifies the actual root
EXE from TEMP and actual CMD visible window; the installed wrapper's separate
report is `local/evidence/companion-actor-installed-visible.json`. Owned test
windows closed gracefully. No owner game process was terminated.

Native checks apply to the exact game executable above:

- [Actor qualification](FOUNDATION-ACTOR-WIDE-2026-10-09.md): 78 checks, 301
  identical guest files and 667 identical original centers, packet artwork and
  actual rollback invalidation.
- `local/runs/hd-menu-20261009-133823/report.json`: 136 optional-frame/guest/
  picture regression checks against 0.1.5 with actor expansion disabled.
- `local/runs/columns-20261009-134025/report.json` and
  `local/runs/loading-20261009-134337/report.json`: 55 checks each, retaining
  original-cost work and v2/v3 restore contracts. The loading checker now asserts
  its legacy reference really writes v2 before testing the absent cursor.
- `local/runs/frame-audio-20261009-134054/report.json`: about 59.9 fps on current
  menu, standard and actor-wide GPU routes, with zero steady underflows, missing
  samples and dropped audible samples. Actor-wide requires positive rendering.
- `local/runs/audio-20261009-134804/report.json`,
  `local/runs/controls-20261009-134843/report.json` and
  `local/runs/checkpoints-20261009-134925/report.json`: legacy/current audio,
  actual virtual-controller gameplay/overlay input and corrupted/foreign saves.

The first comparison window the owner heard was the old 0.1.4 reference:
about 41.5 fps with repeated underflows. Current checked routes hold about
60 fps without recurring underflows. `--candidate-only` avoids replaying that
known choppy reference; `--wide-actors` verifies actor rendering during GPU
checks. These counters are bounded evidence, not a hardware listening guarantee.

## Retained decisions and next work

Enhanced original pixel art and true expanded scenery remain the immediate
visual priority. Full replacement HD world/sprite artwork stays deferred;
eight optional finer border tiles are separate. No compatible MSU-1 driver/pack
has been verified. Original soundtrack and physical-controller settings remain.

Expansion is qualified for Likado's regular actors. Party/composite/effect
actors and campaign-wide scenes remain open. Substantial CPU execution is still
interpreted; no blanket guest CPU budget or speed change is installed. Original
timing, saved-state schemas, activation, collision and game logic stay intact.
Historical AOT/reference differences and full campaign/hardware coverage persist.

Next identify the next map's resource/actor contract using a focused copied
fixture, then extend exact-center/guest/packet checks. Keep scene guards until
the new contract passes. The owner does not need another complete playthrough.
