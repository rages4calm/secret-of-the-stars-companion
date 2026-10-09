# Roadmap

The target is a polished, editable Windows PC edition with attractive original
pixels, true wider scenery/actors, reliable controls/audio and a useful journal.
This is active foundation work, not a completed native recompilation.

## 1. Public first-run setup and packaging

Companion now connects ROM selection/validation, source-build progress and
cancellation, isolated profile adoption, explicit compilation status, title-first
launch and selected copied-save resume. Public Play no longer requires private
fixture/checkpoint data. XP/gold rates, guarded movement boost and keyboard/
controller hotkeys are editable in the launcher.
Source-profile updates now create verified new folders and retain old profiles
for selection-only rollback. A source-first package tool includes one
self-contained GUI, authored source and notices; native game and original data
stay excluded. Finish broader package/hardware checks and automatic GUI release
updates. Configured profile roots currently retain absolute paths.
Do not distribute the ROM or generated game code.

## 2. Finish widescreen actors and difficult scenes

Large B0 sprites have a private registered-callback/PPU composition prototype.
It passes synthetic metadata/transfer/pixel checks, but needs real guest producer
and DMA execution, terrain/OBJ overlap and subscreen/half-color qualification.
It is not enabled in the 0.2.0 foundation.

Wrapping-world actors need authenticated current-line camera lineage across
map seams. Original clipping corrections and emitted OAM coordinates differ;
simply removing the wrap guard is insufficient. Add bounded natural seam,
multi-party and reserved-slot margin fixtures, then broader story/cutscene and
effect coverage. Keep exact original center and safe fallback until each family
qualifies. Resource enumeration alone does not certify a campaign.
The [natural allocation trace](docs/FOUNDATION-ACTOR-ALLOCATION-2026-10-09.md)
proves that one naturally selected world record uses transparent artwork and
executes the original reserved-B0 refusal. A different naturally selected visible
source is needed; further camera movement of the same blank entry is insufficient.
The [Algos acquisition chain](docs/FOUNDATION-B0-MODE-ACQUISITION-2026-10-09.md)
now identifies its original message/bootstrap and travel/exit modes. The exact
selecting field event and a natural checkpoint remain missing. A later ordinary
[wrapping source](docs/FOUNDATION-WRAPPING-VISIBLE-SOURCE-2026-10-09.md) requires
stage 17 and clear flag selector 9. No stage 17 fixture is established.
The [experimental B0 module](experiments/b0/README.md) builds separately from
the canonical snapshot. Actual ordinary guest/DMA fidelity passes; original B0
constructors remain unreached. Keep synthetic B0 raster and actual ordinary
guest checks distinct. Do not enable the experimental module in normal builds.

## 3. Native execution and original slowdown

Identify meaningful guest update boundaries and productive CPU work. Promote
understood routines into native/AOT code with explicit state/side-effect checks.
Measure missed guest updates separately from PC frame rate and audio callbacks.
Only then add bounded title-specific CPU headroom or separated presentation
where justified. Preserve movement, collision, activation and intentional waits.
Current guest cycle accounting remains original. The optional movement boost
changes guarded player walking only, and configurable fast-forward explicitly
accelerates the whole game; neither feature proves a guest slowdown fix.

## 4. Expand the quest journal

The current journal exposes one verified opening-stage lead. Add natural Crest
acquisition and later dialogue/progression fixtures; verify actual item/story
writers before enabling completion rules. Define deterministic event history,
new-game reset, cold restore and rewind behavior. Avoid spoilers or an external
append-only log that remembers a future state after rollback.
The [Crest assessment](docs/FOUNDATION-JOURNAL-CREST-ASSESSMENT-2026-10-09.md)
establishes item identity and generic insertion/removal, but not the title-specific
award or durable completion event. Opening victories are not a Crest fixture.

## 5. Audio and presentation polish

Keep enhanced original pixels and experimental widescreen moving toward a
consistent whole-game presentation. A replacement HD world/sprite pack is
deferred. Optional finer menu-frame art has only bounded coverage.

MSU-1 is conditional: first establish a compatible title driver, event/track
mapping, authorized local soundtrack input, loops/fades and original-audio
fallback. No verified compatible driver/pack is integrated today.

## 6. Wider testing

Use small copied-save and reproducible routes for story transitions, combat,
menus, controllers, listening checks, long sessions and hardware variation.
Protect the newest owner save and keep failures/coverage gaps in the evidence.
A full campaign, every actor/effect and every physical controller are still
unqualified. Volunteer micro-tests are welcome; another owner playthrough is
not the default requirement.
