# Actor and selected-map release: October 9, 2026

Native **0.1.8** is installed with the unchanged qualified **0.1.2 Companion**.
Native SHA-256: `79b91e99c0645672da127feb087f390ff92e4039882fd789bbabdd69f8ee0a95`.
Companion SHA-256: `e26ba4409c062b8f6c3c8ddbd176fe5f1ced43e9325624a05fcfde3fd3789bb8`.
Read `local/evidence/build-receipt.json`, `companion-receipt.json` and
`actor-resource-release-final.json` for the exact artifacts and final checks.
Protected installation backup:
`local/owner-backups/actor-resource-release-20261009-153236`.

Double-click the root `Secret of the Stars Companion.exe` or repaired CMD.
Enhanced pixels apply throughout normal presentation. Display's optional
Widescreen checkbox pairs terrain and actors on the stable 400-pixel canvas.
Existing owner settings, saves, original ROM and working ROM keep their hashes.
Widescreen remains off in the existing owner profile; this release does not
change that preference. The original 256-pixel picture remains centered and
unchanged, including authentic fallback with side bars for unsupported states.

## Changes in this release

The field decoder now verifies the currently selected scene stream against
restored stage, story flags and party state before accepting either primary or
active secondary resources. The check covers original conditional tables,
secondary modes, dimensions, wrap state and optional stream fields. A live
resource change invalidates the derived cache. A missing replacement-list
header can retain an earlier loader pointer exactly as the original game does,
but only an authenticated, bounded original list is accepted.

Two quarter-size secondary backgrounds previously failed a conservative
attribute-table boundary check. Original code explicitly reads a raw 8-bit tile
ID from the selected attribute base, including the adjacent byte in those two
resources. The corrected bound follows that original 256-byte addressable span
inside the ROM bank. Eight independently decoded quadrant words and the actual
adjacent attribute byte qualify these two cases. This does not enlarge the
guest's memory or make arbitrary pointers acceptable.

The actor observer now follows five ordinary party records and nineteen
ordinary regular records. Ordinary records 17/18 use the game's reserved OAM
slots, independently of the regular append cursor. Party pose/own animation
phase, producer clipping, packet order and complete 544-byte OAM transfers are
observed before publishing private margin pixels. Unsupported composite poses,
large B0 actors, wrapping-world actors and incomplete/ambiguous packets remain
refused. No actors are spawned, moved or made active by the observer.

See [party contracts](FOUNDATION-PARTY-ACTOR-CONTRACT-2026-10-09.md),
[reserved and special contracts](FOUNDATION-SPECIAL-ACTOR-CONTRACT-2026-10-09.md)
and [selected-map contracts](FOUNDATION-SECONDARY-MAP-CONTRACT-2026-10-09.md).
Title panorama, all sixteen authored battle-side layouts, optional frame art,
controller bindings, HUD/journal controls and the mosaic buffer repair carry
forward from the [0.1.7 release](FOUNDATION-MAP-RELEASE-2026-10-09.md).

## Qualification

The exact installed executable passes the full map/wide suite's **247 gates**
across **39 candidate processes**, covering natural scenes 0/5/12/38/39, title,
forest combat, transitions, menus, cold restoration and rollback. The separate
actor suite passes 78 gates, checking original guest/center parity and original
sprite art in the margins. Party lineage passes 21 gates through actual capture,
staging, completed transfer and presentation. Its natural coverage is a single
visible, centered party member; synthetic party margins and multi-record ordering
are separate host proofs. Ordinary reserved actors were inactive in the natural
routes. Their positive coverage is synthetic replay of actual registered observer
and transfer callbacks, with 53 cases and 14 qualification gates.

The selected-stream host proof passes 1,893 gates, compares 172,576 conditional
selections and covers 409 original selected resource links. These are resource
identities, not completed campaign maps. Guarded-memory qualification accepts
all 409 selected views and 719 active layers, checks 58,239 extreme coordinate
pairs, refuses 17,863 malformed cases and verifies recovery/reset. Exact ROM and
WRAM allocations have inaccessible pages at both ends, with undefined-behavior
traps enabled. Three natural secondary-layer captures additionally match 5,376
original center words. Retained loader-history fixtures remain synthetic.

Seven paced Windows GPU/audio routes pass without steady underflow, missing
audio frames or overflow. Audible playback checks exclude synchronous forensic
dumps, which previously caused measured game-thread stalls. Full captures remain
in separate headless parity checks. This is counter-based route qualification,
not a new listening or universal system-load guarantee. Seven controller/input
profiles, malformed-checkpoint refusal, legacy/v3 audio initialization and
optional menu-frame tests pass on the exact executable.

The actual unchanged Companion passes 52 backend checks, nine UI interaction
checks and all six paced GPU launch routes against staged 0.1.8. Installed
native title and copied legacy-resume routes pass afterward. Earlier direct
visible EXE/CMD window checks remain valid for the identical Companion artifact.
Physical-controller gameplay has not been retested by the owner this release.

Compilation used the isolated private project recorded in the receipt, with
all 44 authored inputs and generated local inputs frozen by hash. Authored and
live game-source mirrors now match those 44 inputs. Shared runtime sources and
the clean-applying runtime patch remain unchanged from qualified 0.1.7. The
installed binary is the exact tested private compilation; a future rebuild
must qualify its own binary hash. Generated bodies and original data stay local.

## Remaining work

Full-campaign widescreen remains unqualified. Large B0 actors have a separate
private metadata/pixel canary prototype; they are excluded from this executable
until actual hooks, composition and gameplay routes qualify. Composite actors,
wrapping-world actors, natural multi-member party margins, reserved-actor
positivity and further story/cutscene effects need focused checks.

CPU accounting, guest logic rate, activation and collision remain original.
The host audio/frame fixes do not constitute a guest CPU speed enhancement.
Complete native/AOT game execution, more verified journal milestones, a full
replacement HD art pack and a compatible verified MSU-1 driver/audio pack remain
open. Guard pages and the reproduced mosaic repair address specific failures;
they do not certify every possible cutscene or allocation.

The previous 0.1.7 release report and source archive remain historical evidence.
The new additive authored-source archive and its hash appear in the receipts;
it contains no original game binary, ROM, saves, extracted art or generated CPU
bodies. Continue from this document and the current receipts, not older status
blocks in the handoff.
