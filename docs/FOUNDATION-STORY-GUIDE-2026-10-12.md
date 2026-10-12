# Native 0.4.0 / Companion 0.3.6 story guide

The journal now contains a manually browsable **42-page story guide in 14
sections**, covering the opening through the ending. It includes the two
controlled parties, town settlers, warehouse transfers, shrine prerequisites
and cooperative final mazes. The owner and play testers verify campaign
directions; development checks focus on implementing and rendering the feature.

Native 0.4.0 and Companion 0.3.6 are installed in the canonical local paths.
The installation checks all 18 changed paths and preserves owner settings,
saves and profile selectors byte-for-byte. Separate focused rendering/input
checks pass. The actual Direct3D11 route runs at 59.9783 FPS with zero steady
audio underflows, missing frames or audible overflow. Compilation receipts
remain **compiled_unqualified**; installation and playback are separate proofs.
Publication and package status are not inferred from the local installation.

## Current advice and the full guide

**Current** retains the existing bounded automatic opening-through-Sidon
advice, including Kaja's moustache request and Bonzley/Garados lead. It reads
current original chapter, flags, party and applicable possession. Its existing
scope and verified map destinations remain those of the
[Kaja/Bonzley continuation](FOUNDATION-KAJA-BONZLEY-2026-10-12.md).

For later supported chapters, Current can offer a coarse starting page from
the written guide. **Guide** lets the player browse every page manually. The
original current chapter suggests a section; it does not automatically detect
each event, prove prerequisites, complete a quest or create a map pin. Guide
sections are editorial, distinct from the original chapter byte.

| Original current chapter | Suggested guide section |
| --- | --- |
| 0 | 1 |
| 1-3 | 2 |
| 4-5 | 3 |
| 6 | 3 or 4, using the existing original branch |
| 7-10 | 4 |
| 11 | 5 |
| 12-15 | 6 |
| 16-22 | 7-13 respectively |
| 23-24 | 14 |
| Outside 0-24 | No chapter suggestion |

Selected earlier states start at a more useful page within their section.
Manual browsing can reveal later objectives. Browsing does not write guest
progression, remember a conversation or record permanent completion. Current
possession remains separate from award history. Restoration resets browsing
and recomputes advice from the restored guest state.

## Controls

Enable **Quest journal** in Companion's Enhancements page. Existing explicit
bindings are retained; change game buttons in Controls and the Journal action
in Hotkeys. The panel opens in the field, using the existing journal eligibility.

| Action | Control |
| --- | --- |
| Open or close journal | Configured Journal action; J / left-stick click by default |
| Change Current / Guide | Configured game Select |
| Previous / next page | Configured game Left / Right |
| Previous / next section | Configured game Up / Down |
| Close panel | Configured game B |

Game B names the logical SNES action; it is not necessarily the controller's
physical B face button. Keyboard and controller navigation share the same
resolved game-button bindings. Companion 0.3.6 displays these instructions in
Enhancements.

The open panel reserves gameplay controls for browsing. Closing keeps held
controls blocked until their actual release, so the closing press is not
replayed into gameplay. Page/section browsing uses new press edges and clamps
to the available content. Run-ahead does not repeatedly advance host pages.
The guest frame and audio continue running; this overlay is not a pause screen.
Journal and map panels continue to close each other.

## Authored content and sources

The new authored header `native/foundation/src/foundation_guide_data.h` defines
42 static pages, each with a title, eight line slots and an editorial section.
Every title/line is ASCII and at most 28 characters. Empty strings pad unused
slots. It contains no flags, coordinate guesses, guest writes or persistence.

[JOURNAL-GUIDE-SOURCES.md](JOURNAL-GUIDE-SOURCES.md) maps every card range to
the written source actually read. RPGClassics parts 1-10 were readable; the
four remaining actual index links returned 404. Readable RPG Gamers,
RetroMaggedon and GameFAQs 8776 text supplies the ending. GameFAQs 43520 and
failed Neoseeker openings are not claimed read. Source prose, stat dumps,
screenshots and maps are not copied. Per-source derived content stays below
180 words.

Written walkthrough coverage does not certify the campaign, original event
writers, every renderer context or automatic quest detection. Corrections from
the owner and play testers can update content without claiming new completion
rules or map objectives.

## Focused checks and artifact boundaries

The fresh native executable checked by the focused smoke report has SHA-256
`f458e697f0340fef708c0e1c0d5267a089cb1e9c3609cc1f2bcd37eb7676b088`.
Its immutable compilation receipt has SHA-256
`f2de3e630847d64bbea80ae9eea770f8beef987fdf9b269ca1eabe613923012b`
and retains **compiled_unqualified**. Compilation and this finite feature
execution proof remain distinct.

The actual rendering/input smoke passes:

- All 42 guide pages are reached and captured on the 400-pixel canvas.
- Keyboard opening, page/section bounds, consumed navigation, held-close
  suppression and control release work in the finite field route.
- An actual indexed SDL virtual controller opens the panel in the 256-pixel
  late-section fixture, reaches final-section pages, returns to Current with
  Select and closes with game B.
- The source checkpoint and owned ROM remain unchanged.

These are 17 focused checks. The installed GUI has SHA-256
`f1bc6792cad8026f5205c91310ae55c64b86d46ebb6e9393d3d8bc6e47bed904`.
The finite paced route has its own report. Its initial harness expected a
nonexistent close log; evaluation was corrected against the existing output,
while the independent input smoke already verifies closing. This does not
claim a product/audio repair or another gameplay run.

The later chapter fixture is staged for rendering; it is not a natural campaign
playthrough. An indexed virtual controller is not physical-controller
certification. This smoke report does not claim exact whole-guest/APU
equivalence, every story transition, every guide prerequisite or full audio
coverage. Separate playback, launcher, installation and package checks retain
their own status.

Private focused evidence is
`local/evidence/continuation040-20261012/smoke-report.json`,
`paced-report.json` and `installation-report.json` in the same folder. Private
recordings, checkpoints and generated code are not public package inputs. Raw
attempt and fixture limits remain separate from the passing finite smoke scope.

## Build and profile compatibility

The authored native manifest now has 62 inputs, including the guide header;
Companion retains 24. Fresh native and GUI receipts remain
**compiled_unqualified**. The pinned runtime and eleven ordered patches retain
their independent identities. Complete native/AOT execution remains open.

Native 0.4.0 changes the declared execution-state ABI for title input filtering.
Strict source-profile update therefore refuses 0.3.9 to 0.4.0. Fresh source
adoption remains available. Selected legacy checkpoint resumes worked in
focused checks; the declaration mismatch does not by itself demonstrate
incompatible serialization or qualify all older checkpoints. Preserve previous
profiles and the normal compatibility refusal.

The native builder accepts a new `--output-dir`; the GUI builder accepts new
`--source-dir` and `--output-dir` folders. Existing folders are refused rather
than overwritten. See [BUILDING.md](../BUILDING.md) for commands and the
source-first, ROM-free package boundary.
