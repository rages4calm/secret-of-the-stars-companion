# Navigation map continuation: native 0.2.6 / Companion 0.3.2

**Qualified continuation for native 0.2.6 / Companion 0.3.2.** Source compilation receipts stay separate from the following exact-artifact qualification. Full campaign and complete native/AOT execution remain unfinished.

This update adds an optional current-area terrain overview, player-position marker, original world-town markers and a blinking current-objective marker when its location is verified. The game continues running while the map is open. Widescreen remains optional and defaults off; the map works within the existing presentation rather than expanding campaign rendering coverage.

## Using the map

In Companion **Enhancements**, enable **Current-area map**. **Show current objective on map** controls the optional blinking marker independently. Turning the map off retains that preference. Both settings default on for new profiles and when an older configuration omits the keys; loading an existing profile does not rewrite its files. The overlay starts closed.

The default shortcut is **M** on keyboard or **Back/Select + left-stick click** on controller. Press the assigned shortcut again to close it. Both bindings are editable on **Hotkeys**. Explicit bindings, including `None`, win over defaults. When an omitted default is already occupied by another exact binding, Companion displays the map action as unbound. `Ctrl+M` is distinct from `M`; plain left-stick click is distinct from the complete controller chord. The guest's ordinary Select button and configured legacy checkpoint/rewind gestures remain available.

**Original View** disables the map and its objective marker for that launch. Map edits require native 0.2.6 or newer. Apply/Revert, source-profile locks, stale-write refusal and changed-only binding-conflict checks remain in place.

The overlay uses gold for the player, cyan for world-town entrances and blinking pink for a verified current objective. It can show the closest world-town name. A supported local area shows terrain and the player position without invented town or objective coordinates. Unsupported field states show **MAP UNAVAILABLE HERE**. Opening the journal hides the map, and opening the map hides the journal.

## What the locations mean

Terrain comes from the original currently selected map resources and loaded tile/palette data. The player marker follows the original active-party navigation anchor and camera/wrapping behavior. This is an overview of the current area's terrain, including terrain the player may not have visited; it keeps no exploration history, fog-of-war record, item/enemy markers or route planner.

World-town positions are decoded at runtime from the owned clean game's original exit lists and selected location-name streams. Adjacent duplicate entrance records become one centered marker. The mutable original town name is read from current game state. There is no shipped ROM-derived coordinate or town-name table. The parser validates the complete selected list, bounds, conditions and marker capacity before exposing its results; unsupported or malformed metadata produces no partial set of town markers.

Objective locations come from the journal's verified original destination scene. An exact world entrance can produce a pin. An interior destination can identify its town only when a single bounded, unconditional original exit hop establishes that relationship; ambiguous or unavailable destinations have no pin. Local maps do not guess an indoor location from a world destination. The pink marker is current advice, not proof that a quest was completed or its item naturally acquired. Disabling objective markers keeps ordinary town markers.

## Current journal advice

The existing journal continues to use current checkpoint state. This continuation adds verified town-building and Morgan/Dynamite advice through chapters 4 and 5. Isolated original Uncle Save dialogue sets the chapter-4 town clue. Original Morgan dialogue sets the current route clue; the original payment branch consumes an explicitly staged gold prerequisite, resets chapter flags, advances to chapter 5 and loads its destination. Original movement from that outcome returns to the chapter-5 world with the game's own resources.

These are original event executions with declared prerequisite staging, not a natural campaign playthrough. Ringo victory, the Dynamite weapon award, Starcrest completion and permanent quest history remain unqualified. Existing item summaries describe current possession and can be disabled.

## Bounded map work and preserved execution

Map terrain is cached and built incrementally, with at most **1,024 output samples per host frame**. Completed terrain stays visible while a replacement snapshot is built. Animated graphics/palette changes can refresh a completed snapshot after at least **120 host frames**; scene/resource/story changes invalidate the derived map. Town metadata is cached against current scene, selectors, verified destination and mutable name, and is decoded while the map is open rather than scanned every frame. Image identity is checked on first use or image replacement. Reset/restore discards derived caches.

Six paired Direct3D playback routes compare map-off and map-open field/world walking and settled playback after checkpoint restore. They run near 60 fps with zero steady underflow, missing-frame and audible-overflow deltas. On the checked wide opening routes, mean host game-hook work is 0.012–0.013 ms and the first-use peak is 3.75–3.83 ms; mean composition remains below 0.6 ms. These finite local measurements are separate from silent forensic dumps and are not a universal performance guarantee.

The original checkpoint-browser self-test intentionally pumps 30 presentation passes without guest simulation. Its whole-window interruption occurs in both map-off and map-open tests (23 underflows / 12,105 missing frames each). Those failed whole-window results are retained; settled post-restore profiling starts at host frame 400 and audio sample 7. The update does not claim seamless checkpoint-browser audio. See private `local/evidence/continuation026-20261011/map-audio-qualification.json` for both windows and exact counters.

The map is host presentation. Original gameplay timing, CPU budgets, collision and actor allocation remain unchanged. The existing original-center/guest-state fidelity contracts remain required; exact final map/journal/core/rendering checks pass. No new serialized checkpoint fields are introduced.

## Artifacts and evidence

The public source manifests contain **54 native inputs** and **24 Companion inputs**. The original seventeen-file runtime patch remains unchanged at SHA256 `526f7d87b5cf736ce8b57da9db5f4435cce8d33ed1686a587a6a02ca66d73318`, with runtime pin `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`. A separate three-file host-only navigation patch has SHA256 `91fea10b53d3eca67364eceebfb802a2c1c79432ff7424d02c5f8755438dc028`; it appends the map action and its parser/default/dispatch handling without changing previous command IDs or the declared guest execution-state ABI.

Build receipts are immutable records of source compilation and retain `compiled_unqualified`. Qualification, installation and package records are separate. Checkpoint writes remain schema 3, reads remain schemas 1/2/3, and declared SRAM/execution-state compatibility remains required for profile updates. Updates clone into a new profile; rollback selects the retained predecessor without merging newer progress.

| Artifact | Recorded state |
| --- | --- |
| Companion 0.3.2 final2 | EXE SHA256 `3d1846f8a781ebc572dab49059ef804afffde3e6c3e08a7d8191d6210cc87554`; source receipt `0f45b7909bc5e59c212f465be2094194d1f7239570c752efb1433bc96b5282ce` |
| Current native compilation candidate | EXE `adf0a16b04c262e7247c84d92d85a6865d0a05bfc781af10039e0a33932d5d6a`; source receipt `04097b79e1e84d3b48d17ca0795b1d744d078a1f2e7e5b06f765f466714b11e2`; exact map, journal, core, rendering, launcher and paced playback checks pass |
| Qualified native/receipt | Same exact adf0a16b artifact and immutable 04097b79 compilation receipt above; qualification is recorded separately |
| Final combined map, journal, core, rendering and audio reports | Private continuation026, navigation-map-input and journal-later evidence; exact reports below |
| Installation record | Private `local/evidence/continuation026-20261011/installation-report.json`; installed-copy checks and byte-preserved owner data are recorded separately |

The independent map-points checker passes **539 finite controls**, including the original world list's **113 exit records**, 512 synthetic chapter/story combinations, mutable-name controls and malformed-list refusal. Exit-record counts are not town counts or campaign coverage. The private corruption harness bypasses SHA admission only to test the bounded parser; production image admission is separately checked.

The replacement native artifact passes **259 focused map checks in 13 isolated copied-EXE runs**, recorded in `local/evidence/navigation-map-input-20261011/actual-final/report.json` (SHA256 `f4b7665a0eede41c85e01f7fa44d80d5520348ed7971460a3e2a010d9797866f`). They check ordinary-field and world readiness, repeated keyboard presses, indexed virtual-controller input, map-chord Select consumption, existing journal input, guest CPU/register/memory parity, complete checkpoint parity, movement, restore and Original View. The actual original world entrance and independently checked pixels produce a blinking objective; switching objective markers off retains town markers. At host frame 131, warm reopen is immediately ready with zero sampling or new terrain generations; later periodic refresh preserves the completed front image. These are finite silent replay and pixel/cache checks, not paced audio, physical-controller or campaign qualification.

The exact final2 Companion passes **60 source-adoption checks and 81 actual GUI/settings checks**, with 140 protected files unchanged. This GUI proof used the earlier native compilation for settings/capability validation and did not execute native gameplay. Its report is `local/evidence/companion-map-navigation-20261011/final2-GUI/report.json`; the parser report is `local/evidence/navigation-map-points-20261011/parser-malformed-final/report.json`. The final GUI/native pair also passes 31 QoL and 72 presentation GUI checks, 52 actual changed-binary profile update/rollback checks and 43 checks across six source/legacy launch routes (`local/evidence/continuation026-20261011/GUI-QA/report.json`). The native025 rollback and native026 updated copies both execute the real copied checkpoint. Deep Windows process paths remain unqualified after a deliberately deep evidence folder exceeded the process-start path limit; a shorter isolated path passed.

The first native `db5990fb…` candidate failed map readiness and is retained as failed evidence. Its results are not promoted to the replacement candidate. The replacement excludes changing animation scalars from the resource cache key; the focused final-artifact map checks establish its behavior separately. ROMs, saves, original extracted data and private reports remain local. One reviewed actual map documentation capture is published; it is not a reusable original asset pack.

## Remaining work

The exact artifact also passes 729 journal checks across 150 finite native runs and 1,376,256 pure predicates, all seven input/QoL/menu/checkpoint regression suites, 249 selected-resource map checks, 78 ordinary actor checks, 78 optional frame-art checks and 129 battle HUD checks. These finite fixtures preserve guest state and original centers; they do not expand the preceding renderer's qualified campaign scope. Broader campaign coverage, further verified journal destinations, full static recompilation/AOT and a compatible optional MSU-1 driver/pack remain incomplete. This update does not certify a new physical-controller playthrough or a complete HD replacement-art pack.
