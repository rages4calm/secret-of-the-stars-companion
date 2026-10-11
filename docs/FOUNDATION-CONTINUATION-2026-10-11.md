# Map, vehicle and journal continuation: native 0.2.7 / Companion 0.3.2

**Native 0.2.7 is qualified and installed; Companion 0.3.2 is unchanged.** Compilation receipts retain `compiled_unqualified`; the finite qualification below is recorded separately. Complete native/AOT execution and full campaign coverage remain unfinished.

This continuation makes the map legend match its gold player, cyan town and pink objective markers, preserves the completed terrain map during ordinary same-area movement, widens selected original compound vehicle allocations, and adds current Graviton directions from the original chapter-five event. Existing bindings, optional widescreen and original gameplay timing remain intact.

## Map continuity and legend

The legend now uses the same colors as the markers. The optional blinking objective still requires a verified original destination; unknown locations produce no guessed pin. Map and journal remain nonpausing, close each other, and use the existing configurable M / Back + left-stick-click and J / left-stick-click defaults. Explicit bindings win; Original View disables these enhancements.

Two original writers explain needless terrain-generation restarts. Original `01:B248` changes the `051C/051D` camera-stream cursor. Original `01:93B8` writes the low nibble of the current-cell attribute to `0402`; this byte is not a direction value. Both are excluded only from the derived terrain cache key. Independent selected-resource, story and eligibility guards remain required. Separate original-terrain comparisons cover 131,072 cursor-witness pixels and 98,304 cell-attribute-witness pixels; these are finite pixel checks, not map or campaign counts.

Terrain work remains capped at 1,024 output samples per host frame, with the completed front image retained during replacement. Graphics refresh remains bounded by the existing 120-frame interval. Reset/restore discards derived caches. Actual walking, cold generation and warm reopen tests establish continuity on the copied routes; they do not certify every area.

## Guarded compound vehicles

Selected original saved A0/A8 and Algos A8/B0 allocations now widen as a complete authenticated roster. The implementation uses original allocation writers, completed 544-byte displayed packets, descriptors and phases, selected resources, palettes, original slot order and independently decoded art. Four recorded staged-coordinate contexts and two original-loader refusal contexts preserve the exact original center and guest state. Saved Algos X=3584 and unsupported secondary identity retain fallback.

The compound suite checks overlapping/separated actors, both descriptor phases and same-process restore. It records 384 guest comparisons, eight CPU-trace comparisons, 24 original centers, 18 displayed-packet digests and four staging-to-displayed-packet joins. Independent art accounts for 6,324 changed margin pixels. A separate existing-single-family replay preserves native 0.2.6 output. Neither proof establishes natural vehicle acquisition, broader party/effect coverage or a full campaign. Activation, collision, culling, allocation and guest CPU budgets remain original.

## Current Graviton advice

The original chapter-five NPC/event route is now executed in isolated copied checkpoints with declared prerequisites. Original event `29:C3FA` supplies item argument `6E`; the original insertion path writes it into the active inventory, and the original text displays **GOT GRAVITON!**. The original item-name stream independently identifies `6E` as Graviton. No item, interaction packet, VRAM or OAM data is fabricated for this award proof.

The original offer sets current flag `40` before insertion. The later escort branch sets current flag `10` before movement and reaches scene 321 while chapter five and the weapon remain current. These flags alone do not prove successful item insertion or completed escort history. No chapter-five-to-six advancement is established.

The journal combines the current chapter, original flags and both current inventory groups. With the offer and current weapon it advises taking Dynamite to town. After the escort-route flag it advises finding a way to defeat Golan and using Graviton; if the weapon is removed, its possession line changes accordingly. Current/other-pack labels remain distinct. Restore and rollback recompute the panel without remembering future events. The old lab objective is suppressed after either qualified route flag, including when the weapon is removed. Golan's exact world location and scene 321's world relationship are unverified, so no replacement pin is invented.

The original-loader prerequisite staging is recorded separately from natural campaign progress. Existing earlier-chapter advice remains covered. This update does not establish Starcrest acquisition/completion, Ringo victory or permanent quest history.

## Exact artifacts and qualification

| Artifact | SHA-256 |
| --- | --- |
| Native 0.2.7 executable | `3ed0364374f670679f82aebb1d70bc92acc837ba34de7afeadfd8273ef5bf87a` |
| Native source-build receipt | `9bf48b56fe4a2d544fd4800128b64687d2c004a0f575a5611eb8c4f567cf4385` |
| Unchanged Companion 0.3.2 executable | `3d1846f8a781ebc572dab49059ef804afffde3e6c3e08a7d8191d6210cc87554` |
| Companion source-build receipt | `0f45b7909bc5e59c212f465be2094194d1f7239570c752efb1433bc96b5282ce` |

The fresh build is `local/source-builds/20261011-101621` within the public checkout. All 54 native inputs match its compilation snapshot; the 24 Companion inputs are unchanged. Runtime pin `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`, base seventeen-file patch `526f7d87b5cf736ce8b57da9db5f4435cce8d33ed1686a587a6a02ca66d73318` and separate host-only navigation patch `91fea10b53d3eca67364eceebfb802a2c1c79432ff7424d02c5f8755438dc028` are unchanged. Checkpoint writes remain schema 3, reads remain 1/2/3, and the declared guest execution-state ABI is unchanged.

| Exact-artifact suite | Passing scope |
| --- | --- |
| Map/legend/cache | 333 checks across 11 copied-native runs |
| Compound roster | 30 checks across 24 copied-native runs |
| Existing single-family regression | 62 checks across 30 copied-native runs |
| Focused Graviton journal | 125 checks across 34 copied-native runs |
| Public journal checker | 729 checks across 150 copied-native runs; 1,900,544 pure predicates |
| Core regression | Seven hotkey, controls, QoL, restore, checkpoint and menu suites |
| Unchanged GUI with new native | 60 source-adoption and 52 actual changed-binary profile update/rollback checks |
| Paced Direct3D/audio | Eight exclusive routes, 60.011–60.028 fps; zero steady underflows, missing frames and dropped-audible deltas |

Silent journal checks include 256/400 font bounds, original guest/graphics parity, keyboard/indexed virtual-controller toggles, cold restore, rollback and mutable inventory/refusal controls. Indexed input does not certify a new physical-controller playthrough. GUI updates execute copied checkpoints in the new profile and retained predecessor; rollback does not merge newer progress.

The eight paced routes are separate from forensic dumps and concurrent native tests. Six check compound presentation off/terrain/actors; two check chapter-five world walking with the map off/open. The first playback report retained a false harness requirement for side actors during ordinary walking; a fresh corrected gate requires them only in the deliberate compound-overlap contexts. Earlier map-readiness/cache failures remain retained. The previous checkpoint-browser interruption limitation remains: this release does not claim seamless audio while that browser intentionally pumps presentation without simulation.

Private reports remain under `local/evidence/continuation027-20261011`, `map-legend-colors-20261011`, `combined-world-roster-20261011` and `journal-chapter5-award-20261011` in the owner workspace. Final map, compound/single, journal `last-*`, core `core-last`, GUI `G-last` and `paced-qualification.json` reports bind the exact executable above. Installation passes separately in `installation-report.json`, with all 121 owner userdata files, both ROMs and the unchanged GUI preserved. The backup is `local/owner-backups/native027-install-20261011-103007-0343d320`. All 18 copied installed-artifact checks pass in `installed-runtime-report.json`, including title-first launch, explicit original owner-v1 Resume and visible GUI. Packaging remains a separate qualification step. ROMs, generated original code/assets, saves and these private fixtures are not published.

One reviewed actual 400×224 map screenshot replaces the earlier map capture in the six-image [feature gallery](FEATURE-GALLERY.md); the other five captures retain their historical scopes. The image is documentation, not a replacement-art pack.

## Remaining work

Further original Golan/story guidance, broader party/effect and difficult-scene rendering, package/hardware coverage and full native/AOT execution remain open. Widescreen remains optional/default-off; unsupported contexts retain the original centered picture. CPU experiments stay archived. Enhanced pixels preserve original art, replacement HD artwork remains deferred, and optional MSU-1 still requires a verified compatible driver and track map. The ongoing implementation loop remains active; this finite release milestone does not complete the project.
