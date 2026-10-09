# Expanded field, title and battle presentation — October 9, 2026

This continuation records broader original-art widescreen qualification. The
renderer reconstructs standard field resources instead of identifying Likado
alone, extends the visible title's original BG2 panorama using actual raster
scroll, and supplies guarded original-tile side arrangements for all 16 original
battle backdrop resources. Natural combat coverage remains the forest. A requested wide view
keeps a 400-pixel canvas during unsupported states, with guarded black margins.
Original View remains 256 pixels wide. Enhanced pixels are available throughout
these presentation paths; replacement HD artwork is a separate deferred task.

This document records candidate qualification. The installed artifact and
player settings are governed by the separate local release receipt. Neither
the candidate checks nor prototype results establish campaign-wide completion.

## Frozen 0.1.7 candidate qualification

The all-backdrop candidate is
`local/evidence/map-wide-all16-candidate-20261009-144314/candidate.exe`, SHA-256
`9344cef6680e6d9811ce9ae950cdb5acc5da24e5c08519d539be604791ace5dd`.
`local/runs/map-wide-all16-20261009-final/report.json` passes **262 of 262 gates**
on this exact executable. Checker SHA-256 is
`7d231dd281741bddc721fafc6b7c739deedb697556b317c43319a929f2a120ce`.

The complete run includes 42 candidate processes exiting normally, one explicit
earlier-build crash control and **1,121 paired composed captures**. Five field
scenes, actual title panorama and forest command/target/damage pass in ordinary
and enhanced pixels. The natural house-to-Likado transition, menu, warm
world-to-forest battle entry, formerly crashing legacy world replay, fresh cold
checkpoint and actual rollback also pass. All compared guest files, complete
candidate CPU/state/field traces and original 256-pixel composed centers are
byte-identical between original-width and expanded-width runs. Requested wide
surfaces remain 400 logical pixels through guarded fallback; Original View
remains 256. Protected source and owner-profile hash checks pass.

A fresh private cold boot generates its own visible-title checkpoint. The
restored enhanced title pair accepts **53,760 title raster lines across 240
fields**, with actual BG2 scroll spanning 55..679. Completed actor packet
lineage is positive in scenes 12 and 5, including their natural transition.
Observed packets use start slot 16 and mask EFFF; supporting a variable original
allocation cursor in source does not certify an additional-party fixture.
Representative final title, field and real forest-damage images are visually
checked locally. The all-16 background host proof is described separately below.

The first 0.1.7 candidate, SHA-256
`90f888352ef59546b1b96ebb7c93a078dab0e27c40c1df52b6f764e7cf70eae5`,
also passes its complete 262-gate receipt at
`local/runs/map-wide-20261009-final/report.json`. It was superseded by the
all-backdrop candidate above; its evidence remains as an immutable prior result.

## Checker and protected inputs

`tools/check_foundation_map_wide.py` freezes the selected executable and runs
paired original-width/expanded-width processes in fresh private directories
under ignored `local/`. Audio and gamepads are disabled for these deterministic
scripted checks. Each pair uses the same enhanced-pixel setting. Every source
ROM, checkpoint and executable is hashed before and after testing; owner profile
files and recursive saves are also hash-protected. Checkpoints generated during
the proof belong only to those private profiles.

The full suite checks ordinary and enhanced pixels on five naturally captured
field scenes, a natural house-to-town transition, menu opening/closing, the
visible title, forest command/target/actual damage, copied cold restoration and
an actual within-process checkpoint rollback. It compares all captured WRAM,
VRAM, SRAM, OAM, CGRAM, register and guest-framebuffer files, complete CPU/state/
field traces, and the original 256-pixel composed center. Positive map lines,
scene IDs, margin pixels and actual completed actor packet lineage prevent a
black surface or an unexecuted code path from satisfying the feature gates.

The source fixture selection is:

| Observed content | Private source checkpoint |
| --- | --- |
| Scene 12 house | `local/runs/likado-inside-a/saves/save0.sav` |
| Scene 5 Likado | `local/runs/likado-east-a/saves/save0.sav` |
| Scene 0 world map | `local/runs/likado-loop-exit-a/saves/save0.sav` |
| Scene 38 opening house | `local/runs/first-room/saves/save0.sav` |
| Scene 39 island | `local/runs/clean-to-outdoors/saves/save0.sav` |
| Forest battle | `local/runs/world-cave-a/saves/save0.sav` |
| Visible title | Generated privately from a real cold boot, saved at step 6700 |

The title source generation reaches actual visible scene 13, mode 0. Its
restored pairs run 240 further fields. Per-line BG2 scroll minima/maxima and
positive accepted title-line counters establish actual HDMA/parallax sampling.
The old `opening-movement` checkpoint fails the current guarded resume; the
checker reports that failure instead of interpreting its subsequent cold boot
as successful restoration. That original checkpoint remains unchanged.

The forest script follows command selection, FIGHT, target selection and attack
confirmation, then performs six bounded A confirmations. The checked prototype
retains mode 5 through command/target/action and changes enemy HP from `[11,11]`
to `[0,11]` at `damage1`. Guest-state and original-center comparisons therefore
include a real attack, rather than only a static battle menu.

## Prototype evidence and a separate runtime failure

The first broader prototype is
`local/evidence/map-title-battle-prototype-20261009-141652/candidate.exe`, SHA-256
`61a8bb434fffe9c8acaeedc51d5c67ec463926691838333982479d835a05aa45`.

- `local/runs/map-wide-prototype-20261009-initial/report.json` records positive
  original-pixel five-map/transition/forest output and exact guest/center/CPU
  comparisons. It intentionally remains failed because the original selected
  legacy world replay crashes; its exit gate was not weakened.
- `local/runs/map-wide-world-exit-prototype-20261009/report.json` qualifies the
  selected natural town-exit world checkpoint on the bounded right/left sweep.
- `local/runs/map-wide-enhanced-prototype-20261009/report.json` passes the five
  enhanced map pairs, enhanced forest battle, menu, cold restore and rollback.
- `local/runs/map-wide-title-fresh-prototype-20261009/report.json` passes fresh
  cold-title generation and both original/enhanced restored title pairs.
  The enhanced title start and step-240 screenshots were visually inspected.

A longer leftward world replay revealed a real existing access violation.
`local/runs/map-wide-world-baseline-20261009/report.json` reproduces it on the
old frozen 0.1.6 executable as well as the broader prototype, at the same guest
point. Both original width and expanded width fail. A natural world-to-battle
attempt with `left80/up180` from the town-exit checkpoint also reproduces the
failure; its report is
`local/runs/map-wide-warm-entry-prototype-20261009-route2/report.json`.
The shorter right32/left40 sweep remains a separate positive route.

These reports distinguish the actual surviving route from the longer failing
route. The warm-entry gate requires a normal exit, observed world and battle
states and actual accepted forest lines; a blocked coastal walk cannot satisfy
it. `--reference-exe` enables a separate legacy failure control. Only that
explicit earlier-build control is allowed to reproduce its known failure; the
candidate's original-width and expanded-width replay must both exit normally.

The corrected mosaic prototype is frozen at
`local/evidence/map-mosaic-fix-prototype-20261009-143321/candidate.exe`, SHA-256
`a50dee2e6ee0db183feac8d3d6f5804c74e9faecafbd47a44d084f6d8a3948bf`.
`local/runs/map-wide-mosaic-fix-focused-final-20261009/report.json` passes all
26 focused gates. The natural world-to-forest battle route and the formerly
crashing legacy world replay now exit normally in both widths, retaining exact
guest snapshots, CPU/state/field traces and the composed original center.

The renderer fix refreshes its derived horizontal mosaic table from the actual
registers being drawn, rather than retaining a previous field's block size after
raster replay. It uses signed block alignment in margins and bounded loops for
empty/partial window spans. This corrects host rendering memory traversal; it
does not grant guest CPU cycles or change world movement pace. Its independent
renderer controls belong to the root-owned mosaic evidence.

The frozen 0.1.6 control still reproduces the access violation. All fourteen
available pre-crash guest files (`start` and `right`, seven file types each),
including original framebuffer bytes and registers, match the corrected
candidate exactly. Complete available CPU and field trace prefixes also match.
The control's `state.csv` has **zero bytes**: `host_main.c` writes that trace
through buffered `fprintf` and closes it on normal exit, which the crashing
control never reaches. The report records this unavailable trace coverage
explicitly; it does not claim empty data establishes state equality. The new
candidate's complete original-versus-wide state trace remains byte-identical.

## Limits and reproducibility

Positive copied coverage applies to the five scene IDs and checked forest
combat, not every story variant or later battle encounter. World terrain wraps are
reconstructed, but distant edge seams need positive routes. Wrapping-world
actors retain their original viewport behavior. Regular actor metadata is
positively linked to completed packets in scenes 12 and 5; additional-party,
composite/effect and special-constructor margin drawing remains unqualified.
Conditional map branches, later story variants, other presentation modes and
full-campaign progression are not certified by these bounded routes.

No guest activation, spawning, collision, CPU budget or original logic rate is
changed. Headless parity does not establish GPU pacing, sustained audible
playback, physical controller behavior or physical display scanout. Those
checks belong to their separate current-candidate receipts. All captures and
ROM-derived resources remain local.

The separate all-backdrop host proof is recorded in
`docs/FOUNDATION-BATTLE-WIDE-2026-10-09.md` and private
`local/evidence/battle-wide-20261009-readonly/all16-final-proof/report.json`.
It loads all 16 original-ROM background resources into synthetic host PPU views
and tests two CGRAM inputs: **1,835,008 original-center pixels**, **16,704
independently decoded visible margin words**, and **288 guard rejections** pass.
The authored side cells continue each original background's local textures and
contours; they do not reveal extra battle space. These checks use the actual PPU
renderer, but the other 15 backgrounds are not naturally reached campaign
encounters. Original palette-script execution, battle effects and transitions
still need their own positive routes. The frozen battle module C SHA-256 is
`44b1db121ee6807ecb93327249d35129838a8b2c46b051d28a41ffb139533976`;
header SHA-256 is
`cca47f34826157894565eb194da46d1a54bc91548444b22d7d9615ef8eb1dc6a`.

```powershell
python tools/check_foundation_map_wide.py --exe <frozen-candidate.exe>
```

Use `--only` for focused diagnostics and a fresh `--out` under `local/` when
needed. Reports identify whether they ran the full suite or selected cases.
The complete release proof must use the exact frozen candidate hash and current
source checksum; prototype reports are not transferable certification.

## Original primary-resource inventory

The new read-only `tools/inspect_foundation_scene_coverage.py` uses the existing
`OriginalMaps` decoder to enumerate the entire original scene-selector table.
Its private report is
`local/evidence/scene-coverage-20261009-primary-inventory/report.json`. It checks
every referenced primary grid against original record spans, every reachable
segment against the 1,280-entry table and 64-byte mapped source, every cell ID
against its original definition span, and every reachable metatile (including
boundary zero) against original tile/attribute spans. Dimensions must be 1..15.

All **337 scene-selector entries** decode, containing **409 variant references**
and **395 unique stream addresses**. Those streams describe **248 unique primary
resource tuples**; all 248 pass the static reachable-resource checks. They
reference 245 primary map-table indices. These are data-structure counts, never
counts of distinct playable maps, checked gameplay scenes or campaign progress.
Aliased pointers and different selector streams can share a resource tuple.

The inventory identifies the remaining important families without requiring
another owner playthrough:

| Static resource family | Unique primary tuples | Remaining positive evidence |
| --- | ---: | --- |
| Wrapping grids | 118 | Natural map-edge seams; wrapping actor coordinates and culling |
| Reachable conditional attribute E | 57 | Live matching location records and actual flag replacement branch |
| Reachable conditional attribute F | 14 | Live alternatives, stage and selector branches |
| Final definition spans bounded only by ROM bank | 13 | Independently establish exact final cells/tiles resource ends |

These families overlap. Conditional scene selectors observed in the table are
0 and 2, with 23 and 49 references respectively; each scene also has its final
unconditional FF record. Their runtime condition decisions are not certified
by enumeration. The largest referenced dimensions are 14 by 14 segments;
resource sizes range from 1 by 1 through the listed larger grids.

There are **zero static primary resource exceptions** under the documented
span contract. This does not mean that every family is ready for unconditional
presentation. The optional secondary stream remains unparsed, final definition
ends retain the explicit bank-containment limitation, and F replacement targets
depend on live condition records rather than primary headers alone. PPU layout,
story variants, alternate actor constructors and battle themes still require
their separate contracts and positive routes. No original ROM bytes or pixels
are added to authored source or the public source package.

The separate root-owned `tools/check_foundation_scene_resolver.py` compiles the
actual authored `foundation_field.c` in its standalone host adapter and checks
all 248 inventoried primary resource tuples against the independent original
decoder. `local/evidence/scene-native-20261009-143656/report.json` passes all
248 cache-acceptance cases, **3,053,568 full-grid tile words** and **10,416 boundary
words**, with no sampled mismatch. Native source C SHA-256 is
`c94be434bb8f7410b25041cb90f62af1f79cb7f7455a9b4d49e1e6fcc304bbd4`;
header SHA-256 is
`8e1cc13de13baa51b5ee765ef9bb057796e2abfef97389355fa33b5d75552db9`.

These are synthetic host-only resource views backed by the unchanged original
ROM. Story record pointers deliberately use an original no-match sentinel, so
the check proves static decoding/cache acceptance and boundary policy across the
resource inventory. It does not prove matching E/F replacement branches, live
story variant selection, secondary resources, actor behavior, pixel composition,
GPU/audio performance or that those scenes were naturally visited.
