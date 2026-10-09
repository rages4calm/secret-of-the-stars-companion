# Host buffer repair release: October 9, 2026

Native **0.1.9** and unchanged **0.1.2 Companion** are installed. Native SHA-256:
`0d2c8fc78be6907e1eb96166672ee14b4927e84821d5d8be1bc5d999772d9490`.
Companion remains
`e26ba4409c062b8f6c3c8ddbd176fe5f1ced43e9325624a05fcfde3fd3789bb8`.
The tested binary was compiled in the isolated project recorded in the current
build receipt; authored/live source mirrors match all 44 compiled game inputs.
The runtime patch now covers 15 files against pin
`7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0` and has SHA-256
`f469f3f19a2f7a66c2284f2cd080cd2c38af214a49c28f0e23b5e586e9cd7726`.
It applies to pristine pin sources and reproduces the compiled runtime changes,
with only Git CRLF normalization excluded from comparison.

Backup: `local/owner-backups/host-buffer-release-20261009-155010`.
It preserves the previous 0.1.8 player, source manifest, two changed runtime
sources, old runtime patch and receipts. All original/working ROM bytes, owner
saves and nonbinary profile files retain their hashes. Fullscreen, enhanced
pixels, controller settings and default-off Widescreen remain as the owner set
them. Launch through the root Companion EXE or repaired CMD.

## Specific allocation repairs

The user's memory/buffering concern prompted a focused audit. Fault injection
reproduced a real access violation in the old audio path: startup's unchecked
`calloc` could leave a null buffer that the callback wrote through. This is a
proven failure mode under allocation failure, not a diagnosis of an earlier
owner session or of EarthBound's cutscenes.

The repaired startup validates stereo layout and positive frequency, computes
block size with widened and bounded arithmetic, and publishes the buffer and
its cursors only after allocation succeeds. Failure closes the still-paused
audio stream/device and exits with failure before gameplay/save writes. Successful
startup retains the same sample rate and block size. Initial buffer cursors now
share the valid allocated base rather than relying on null-pointer subtraction.

OpenGL previously committed the new capacity and freed the old buffer before a
replacement allocation succeeded. A failed growth request could permanently
leave a null buffer, skip retries at the same dimensions and still reach texture
upload. The repaired code validates signed dimensions, pitch and size arithmetic;
retains the old allocation until a replacement succeeds; refuses the failed
draw; and retries the next request. Destroy releases and resets buffer state.
These changes do not alter the owner's selected Direct3D renderer or CPU budget.

## Evidence

The reusable ROM-free [buffer checker](../tools/check_foundation_host_buffers.py)
extracts the actual production functions. Original controls preserve the audio
access violation and failed-OpenGL-retry behavior. Repaired controls pass nine
valid audio rates, nine invalid layouts, allocation failure, seven invalid GL
dimension cases, null output arguments, capacity preservation, same-size retry,
zero calls/uploads after failed draw, and destroy/reinitialize.

Guarded presentation tests cover 48 width/mode/padded-pitch transitions with
32,621,568 flat pixels and 22,020,096 independently checked frame-art pixels.
The exact DSP ring passes 24,579 stereo-pair comparisons across three counter
origins, including integer wrap, bounded full-ring drops and save/restore.
These tests use inaccessible end pages and undefined-behavior traps. See the
[full buffer contract](FOUNDATION-HOST-BUFFER-CONTRACT-2026-10-09.md); its audit
and private proof predate installation, whose authority is this release receipt.

The exact installed executable passes:

- Full map/wide suite: 247 gates over 39 candidate processes, authentic original
  center/guest state, field/title/forest combat transitions and rollback.
- Ordinary actor suite: 78 gates, plus 21 actual single-party lineage gates.
- Seven virtual SDL gameplay/controller profiles, checkpoint refusal and
  legacy/v3 audio initialization; optional frame-art checks.
- Seven paced Direct3D GPU/audio routes with zero steady underflow, missing
  frames or audible overflow.
- Three real OpenGL routes: menu, enhanced wide actors and optional frame art,
  each about 60 presentations/second and zero steady audio counter deltas.
  Actual renderer initialization and requested VSync are checked; a driver
  swap-interval query and new listening test are outside that proof.
- Companion's 52 backend checks, nine UI interaction checks and all six paced
  launch routes against staged 0.1.9, followed by installed title and copied
  legacy-resume helper checks. The identical Companion retains its earlier
  successful direct EXE/CMD visible-window evidence.

Paced audio tests omit synchronous forensic dumps. Guest/pixel parity retains
those captures in separate headless tests. The first OpenGL checker report is
retained: playback passed, but its request check incorrectly expected a
SDL-renderer breadcrumb from the separate OpenGL branch. The corrected checker
checks the requested config plus actual OpenGL initialization and passes in a
fresh output directory. Neither that diagnostic failure nor the earlier
forensic-capture starvation report is erased.

Current artifacts and source archive appear in `local/evidence/build-receipt.json`,
`companion-receipt.json` and `host-buffer-release-final.json`. Historical 0.1.7
and 0.1.8 receipts, candidates, backups and authored-source archives remain local.

## Widescreen and next work

All [0.1.8 selected-map and actor behavior](FOUNDATION-ACTOR-RESOURCE-RELEASE-2026-10-09.md)
carries forward: bounded primary/active-secondary selection, ordinary party and
reserved-slot observers, title panorama and sixteen authored battle-side layouts.
The 409 selected-map resource links and 719 active layers are host-resource
coverage, not completed campaign maps. Exact 256-pixel center, stable 400-pixel
canvas and authentic fallback remain mandatory.

The next private [large-actor integration](FOUNDATION-LARGE-ACTOR-INTEGRATION-2026-10-09.md)
passes 56 synthetic callback/transfer/composition cases, 459 read-only callback
calls and 1,806,336 independently decoded margin pixels through the actual PPU.
Five genuine ordinary packet pairs also match the existing renderer. Those
registered callbacks and transfers are host adapters, not actual guest/DMA
execution. A read-only inventory of 9,866 existing WRAM dumps (586 unique images)
found no active-looking B0 records; it narrows available fixture coverage only.
Large/composite actors remain excluded from this installed executable.

The [wrapping actor contract](FOUNDATION-WRAPPING-ACTOR-CONTRACT-2026-10-09.md)
establishes that the original map-wrap correction changes clipping eligibility,
while OAM emits raw coordinates. Ten genuine world-field captures match 80
ordinary pieces and full 544-byte scanouts. Camera-seam/margin positivity is
still absent; the 3,584-pixel scene0 period needs explicit raster lineage across
its discontinuity. Removing the wrap guard alone is unsafe.

Natural large/multi-party/reserved margin coverage, composite/wrapping actors,
full campaign and story/cutscene effects remain open. CPU budget and guest logic
rate remain original; complete native/AOT game execution and a bounded slowdown
enhancement remain separate work. Further verified journal milestones, a full
replacement HD art pack and a compatible verified MSU-1 driver/audio pack are
also open. No new physical-controller certification or universal crash-free
claim follows from these finite tests.
