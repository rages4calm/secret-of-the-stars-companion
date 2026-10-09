# Cached presentation and steady audio continuation

Version 0.1.5 is qualified and installed, SHA-256
`987554031d343fbc54e89b4fbc54e40058147aa6f26e75ee486391b4ff00c00e`.
The current build receipt governs completed qualification and installation.
Protected installation evidence is
`local/evidence/player-hd-audio-release-20261009.json`; the previous executable,
all owner settings and saves were hash-verified in a new backup before installation.
Both normal launch and the isolated optional preview now use the fixed bytes.
This supersedes the 0.1.4 preview's audio/presentation qualification.

## Owner report and reproduced cause

The owner heard skipping in the HD preview and confirmed that both movement
and sound felt repeatedly paused. The 0.1.4 GPU test established early nonzero
PCM and a correct captured menu but omitted steady service/underrun gates.
That omission mattered: its four-times surface overwhelmed the direct mapped
GPU composition path. No guest pause/resume control or CPU-speed patch caused
this regression. The optional preview was temporarily disabled in the receipt
until a corrected artifact passed stronger tests.

`tools/check_foundation_frame_audio.py` reproduces the failure using frozen
0.1.4 and 0.1.5 copies and actual Windows Direct3D 11/VSync/SDL callbacks.
The reference menu measures 43.15 presentations/second after warmup, 19.263 ms
mean composition, and 141 recurring output underflows / 70,290 missing output
frames in the sampled steady interval. The earlier shorter preview measured
about 41 presentations/second. This is measured host service starvation.

## Fix and focused evidence

Use the pinned runtime's cached host-memory composition via
`SNESRECOMP_FRAME_IMPL=HLE`. The title still uses its original beam-aligned guest
CPU/raster scheduler. Here HLE names host frame staging, not replacement game
logic or a modified guest CPU budget. Compose the picture, frozen overlay and
OSD in cached RAM; copy it linearly into the mapped presenter buffer once.
The previous 4x surface-capacity repair remains in the runtime patch.

Measured on the same machine with real GPU/audio, discarding startup samples:

| Copied route | Presentations/second | Mean composition ms | Recurring underflows / missing frames / audible drops |
| --- | ---: | ---: | --- |
| 0.1.4 direct HD menu | 43.15 | 19.263 | 141 / 70290 / 0 |
| 0.1.5 cached optional frame art | 59.96 | 0.679 | 0 / 0 / 0 |
| 0.1.5 standard enhanced pixels | 59.93 | 0.192 | 0 / 0 / 0 |
| 0.1.5 Likado enhanced terrain width | 59.91 | 0.537 | 0 / 0 / 0 |

Report: `local/runs/frame-audio-20261009-125320/report.json`. Captured steady
intervals exclude the first two per-second samples for startup/prefill and
contain at least three later samples. This checks ongoing output rather than
just hearing the first sound. It does not guarantee every future Windows load
or replace owner listening feedback.

The final authored-frame checker passes 136 checks at
`local/runs/hd-menu-20261009-125025/report.json`: 78 feature checks and 58
comparisons with 0.1.4. Across 19 copied cases, all 770 guest dump files, 67
CPU/state/field/frame-art traces and 499 composed surfaces are byte-identical.
The separate Windows GPU menu and loading proofs supplement headless parity.
Native original-cost columns pass 55 checks / 10 cases and original-cost clear
loading/checkpoints pass 55 checks / 17 cases. Receipt paths identify the exact
artifact for all remaining menu, journal, controls, recovery and audio gates.

## New visual priority and next steps

The owner now prioritizes attractive enhanced pixel art/upscaling and true
widescreen like EarthBound/Zelda. A full replacement HD world/sprite art pack
is deferred so it does not slow the playable port. The eight menu-frame tiles
already authored remain optional/off, with their isolated preview available
after qualification. Standard launch keeps enhanced pixels, current controls,
fast outer menus and the opening journal. Owner settings/saves are preserved.

Continue with the familiar Companion launcher adapter, expanded world/actor
visibility and scene bounds, and further verified journal events. The current
Likado preview expands terrain only; normal width stays original until actor
and scene coverage is qualified. Full static native execution, broader guest
slowdown remedies and optional compatible MSU-1 remain separate work. Diagnostic
fast loading changes NPC movement timing and stays out of normal launch.

## Reproduction

The qualified executable is built in
`local/native-proof/SecretOfTheStarsSNESRecomp/build-hle`, Release/Clang/Ninja,
with `-DSNESRECOMP_FRAME_IMPL=HLE`, SDL3 static runtime, networking disabled.
The exact tested bytes are copied to the normal build entry point and installed
player profile; a later rebuild must refresh qualification for its own hash.
Keep `native/foundation` and the live authored source synchronized and apply
the runtime patch against pin `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`.
New v3 states, v1/v2 guarded compatibility, owner backups and source-only
packaging remain governed by the protected installation receipt.
