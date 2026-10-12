# Secret of the Stars Companion

**A Windows PC-port foundation for Tecmo Secret of the Stars, with a Companion launcher, controller support, enhanced pixel art and experimental widescreen.**

[![Stage](https://img.shields.io/badge/stage-active%20development-244b6b)](ROADMAP.md)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-244b6b)](BUILDING.md)
[![Contents](https://img.shields.io/badge/contents-ROM--free%20source-244b6b)](docs/VALIDATION.md)

**Latest WIP: native0.3.8 / Companion0.3.5.** Verified bridge-to-Bonzley journal advice and broader faithful native instruction execution are described in the [latest continuation](docs/FOUNDATION-BRIDGE-ACCUMULATOR-2026-10-12.md). Complete native/AOT execution and full campaign testing remain unfinished.

**Discord:** chrono.trigger

> [!IMPORTANT]
> Bring your own clean, unheadered **Tecmo Secret of the Stars (USA)** ROM. This repository contains authored source, development tools, documentation and six reviewed feature screenshots. **No ROM, generated game code, extracted art, soundtrack, save, checkpoint or playable game binary is included.** Your game data stays local.

> [!NOTE]
> **Early development: native foundation 0.3.8 / Companion 0.3.5.** A local Windows build runs opening gameplay, menus and combat, with focused automated checks. This is **not yet a complete native/AOT recompilation or a full-campaign-qualified widescreen port**. Substantial guest execution still uses the pinned SNES runtime's interpreter. HLE host staging and native presentation enhancements do not change that coverage claim.

The [preceding update](docs/FOUNDATION-MORGAN-WRAP-2026-10-12.md) adds Morgan/WIN-KEY
journal guidance, fixes four verified world-wrap scenery flashes, and broadens
automatic native generation through a generic analyzer repair. The launcher,
map, reward/travel modifiers and editable encounter rate remain available.

The aim is to give this overlooked RPG a polished PC edition that is easier to play and easier to understand: attractive original pixel art, a genuinely wider world view, reliable controls and audio, a useful quest journal, and a map showing your position, towns and verified destinations. The launcher follows the familiar Companion approach used in [EarthBound Companion](https://github.com/rages4calm/earthbound-companion) and [Zelda Companion](https://github.com/rages4calm/zelda-companion).

## PC feature screenshots

These are actual captures of features added for this PC project. **[View all six screenshots and captions](docs/FEATURE-GALLERY.md)**, including configurable rewards, movement and keyboard/controller hotkeys.

![Widescreen world with an original vehicle beyond the original viewport](docs/screenshots/widescreen-world.png)

*Guarded wider scenery and original vehicle rendering.*

![Optional native enemy HP sidebar](docs/screenshots/battle-health-sidebar.png)

*Toggleable enemy HP information alongside the battle view.*

![Quest journal with verified Mayor and Ringo route advice](docs/screenshots/quest-journal.png)

*Quest directions and current progress while the game runs.*

<img src="docs/screenshots/navigation-map.png" alt="Navigation map with your position, towns and a blinking verified destination" width="1200">

*Captured from the running game at 1080p with enhanced pixels and widescreen enabled. Gold shows your position, cyan marks towns, and the optional pink marker blinks at a verified next destination.*

The gameplay images use isolated development checkpoints. Widescreen is optional and uses the original view where a scene is not qualified; the journal is still being expanded. Upscaling preserves original artwork. See the gallery for exact capture scope and example launcher settings.

The [0.3.6 encounter update](docs/FOUNDATION-ENCOUNTER-RATE-2026-10-11.md) adds a 0–100% random encounter setting in Companion 0.3.5. Default 100% retains the original check; 0% disables qualified ordinary random battles while scripted battles retain their separate original path. The setting narrows integer bins in the original threshold, so a reduced value does not promise an exact campaign fight frequency.

The preceding [0.3.5 continuation](docs/FOUNDATION-CIRCUS-PRIEST-2026-10-11.md) adds circus-ticket guidance, the current Cody/priest request and a verified Decatas world-map destination. Companion remains 0.3.4. Exact overlay, map, original-loader graphics, launcher and finite playback checks have separate reports; initial failed tests and the intermittent modal audio limitation remain explicit. The [0.3.4 source continuation](docs/FOUNDATION-REVIEWED-ROOTS-2026-10-11.md) retains the reviewed generation available through normal Setup using only your owned ROM and public source.

## What works today

| Area | Implemented behavior | Current limit |
| --- | --- | --- |
| Windows foundation | Compiled C/SDL3 host with native game-specific enhancements and guarded original execution | Complete native/AOT game execution is still future work |
| Companion launcher | ROM validation, source-build progress/cancellation, isolated profile updates/rollback, explicit title/selected-copy resume and protected settings edits; downloadable ROM-free WIP launcher/source package | Requires your owned ROM and Windows development tools to build the native game |
| Enhanced pixels | Independently selectable Scale2x presentation, exact window sizes, pixel shape and fullscreen output | Upscaling preserves original artwork; it is not a replacement HD world pack |
| Widescreen scenery | Stable 400-pixel canvas, selected original primary/secondary map resources, title panorama and sixteen authored battle-side layouts using original cells | Original 256-pixel center stays exact; selected overworld edge crossings retain terrain margins; unsupported states retain centered imagery and side bars |
| Widescreen actors | Ordinary party, regular/reserved packets, guarded driving/parked and selected compound vehicle rosters, and selected later world-map actors, plus selected qualified interior and original town/house NPC families | Original allocation, packet and art checks authenticate supported contexts; broader party/effect/vehicle contexts remain open |
| Controls | Editable keyboard/controller game buttons and hotkeys, twenty checkpoint bindings, fullscreen and reachable HUD/journal/rewind controls | Broader physical-controller testing remains open |
| Menu and battle QoL | Optional faster field menus and toggleable HP bars with a widescreen battle sidebar | The HP panel is an authored enhancement, not a bundled ROM hack |
| Rewards and travel | Independently adjustable 1–10× battle XP/gold; bindable 1–3× field movement boost; 0–100% ordinary random encounter modifier; hold/toggle fast-forward | Movement and encounters use guarded original seams; unsupported contexts retain original behavior and scripted battles stay enabled |
| Quest journal | Objective, route/advice and current-progress panel; verified opening, Badbad/Dog Pill, town building, Morgan and current chapter-five Graviton/GIANT directions and selected chapter-six farming, Decatas ballot/election/circus-ticket advice and the verified chapter-seven Cody/priest request with active-party and current-item checks; J / left-stick click toggles it | Current flags and possession recompute after restore; further chapters and deterministic quest history remain open |
| Navigation map | Original current-area terrain and your position; original world towns and an optional blinking verified destination; M / Back + left-stick click | Unsupported areas use a clear fallback; no exploration history or guessed objective coordinates |
| Audio and stability | Original SNES audio, cached host composition, repaired mosaic overrun and checked audio/OpenGL allocations | Finite paced GPU/audio routes pass; every cutscene and hardware configuration is not certified |
| Saves and rollback | Guarded checkpoint loading, restore/cache reset and protected copied-save testing | Local state schemas are build-specific; test on copies and keep in-game saves backed up |

**Widescreen is experimental and defaults off.** It expands scenery and observed actors without spawning extra actors or changing collision, activation or game speed.

## Build from your own ROM

[Download the WIP launcher/source package](https://github.com/rages4calm/secret-of-the-stars-companion/releases), extract it and open **Start Secret of the Stars Companion.cmd**. Its Setup page validates your owned ROM and builds the native game locally. The package includes the launcher, authored source and notices; it does not include a playable game binary or original game data. Install the prerequisites in [BUILDING.md](BUILDING.md) first.

Developers can also build from this source snapshot:

```powershell
git clone https://github.com/rages4calm/secret-of-the-stars-companion.git
cd secret-of-the-stars-companion
python tools/build_public_foundation.py --rom "D:\My Games\Secret of the Stars (USA).sfc"
```

The helper fetches the pinned runtime, applies eleven separately checked patches, and uses the standard analyzer/emitter with authored reviewed entry metadata and proved instruction prefixes. It generates game code locally, compiles a fresh native executable and creates an isolated profile under ignored `local/`. No private recordings are required by normal Setup. It does not copy your ROM, replace your existing installation or manufacture a passing gameplay receipt. Existing modified runtime checkouts are preserved rather than reset.

Build the self-contained launcher with `python tools/build_public_companion.py`, then open `Start Secret of the Stars Companion.cmd` or the generated Companion EXE. Its Setup page validates your ROM and builds/adopts a fresh native profile without private gameplay fixtures. See [BUILDING.md](BUILDING.md). Historical native preview scripts and fixture checkers remain development adapters.

In **Enhancements**, 100% means the original XP/gold payout; 200% means 2×. Movement boost defaults to **Left Shift / controller L2**, and fast-forward to **Tab / controller R2**. Change these and other bindings in **Controls** and **Hotkeys**; fast-forward can be held or toggled. Existing custom profile bindings are retained. [QoL implementation and limits](docs/FOUNDATION-QOL-2026-10-09.md).

Companion **0.3.5** adds **Random encounter rate (%)** under **Battle rewards and travel**. Close the game, choose 0–100 and Apply; Revert restores the loaded choice. Missing settings default to 100, and Original View uses 100 for that launch without changing your saved value. The control requires native 0.3.6; older builds show an update hint.

Companion **0.3.3** adds Auto and 720p–4K window sizes, preserves custom sizes, and offers **Original CRT shape / Square pixels / Square frame**. Apply validates changed values; Revert restores the loaded profile. These controls preserve sound, rewards and bindings, and do not add scenery.

Companion **0.3.2** adds map and objective-marker settings and an assignable Map action. Missing bindings use **M / Back + left-stick click** unless that exact shortcut is already occupied. Existing explicit bindings win. Map and journal panels close each other.

Companion **0.3.1** added **Original pixels / Enhanced pixels / Experimental widescreen** display choices, **Revert changes**, current fullscreen/hotkey hints and a journal item-summary setting. Presets preserve sound, rewards and custom bindings.

Companion 0.3.0 adds **Update selected profile** and **Use previous profile** in Setup. Updates create a new isolated folder with checked copies of settings/saves; rollback selects the retained earlier folder and preserves newer progress separately. Different native builds require compatible save declarations and matching execution-state ABI. A ROM-free source-first ZIP can bundle the self-contained GUI, authored source and notices; native game compilation still needs the documented tools. [Packaging instructions](BUILDING.md#package-the-source-first-launcher) · [Update and package qualification](docs/FOUNDATION-PACKAGE-UPDATES-2026-10-09.md).

## Verification and remaining work

**Native 0.3.6 / Companion 0.3.5** passes focused settings, source adoption and copied-profile update/rollback checks, including an unavailable control on native 0.3.5. Default/100% original behavior, reduced random checks and scripted producers have separate native evidence. Installation, package and playback status is recorded in the [encounter continuation](docs/FOUNDATION-ENCOUNTER-RATE-2026-10-11.md).

**Preceding native 0.3.4 / unchanged Companion 0.3.4** reproduces the qualified expanded generation without local capture inputs. Its fresh public build passes 468 strict original/native checks across 24 copied runs, registered-hook controls, original laboratory packet/art checks and launcher adoption. The analyzer emits 151 full contexts, 93 proved prefixes and one interpreted context; these are generation counts, not whole-game or campaign certification. Thirteen separate normal playback routes pass near 60 FPS with zero steady audio-counter failures. A full nine-route modal repeat also passes. Two initial modal audio failures remain retained with an unproven cause. Installation and 18 copied Play/Resume/visible-GUI checks pass. Package/publication integrity is checked separately. [Reviewed inputs and exact artifact](docs/FOUNDATION-REVIEWED-ROOTS-2026-10-11.md).

**Native 0.3.0 / Companion 0.3.4** corrects Starcrest inventory detection, extends guarded actor margins to the settled laboratory, and generates another original loading routine. Original recruitment and SWAP between both parties, their current inventories, journal/map behavior, cold restore and rollback pass focused checks. Ten separate Direct3D playback routes and nine checkpoint/rewind routes pass with zero steady audio-counter failures. Bun's original recruitment and door exit are verified; his later construction trigger remains in progress. [Exact artifacts and tested limits](docs/FOUNDATION-PARTIES-CONSTRUCTOR-2026-10-11.md).

**Native 0.2.9 / Companion 0.3.3** adds authenticated underground/laboratory actor margins, current chapter-six town/farming advice, exact window-size/pixel-shape controls and a faithfully generated original loading routine. The repaired build resumes sound using genuine guest DSP audio and consumes each keyboard rewind request once. Rendering, journal, restore, input and actual launcher update/rollback checks pass, with nine clean modal GPU/audio routes. Separate pacing qualifies 15 distinct routes across 19 attempts: 13 passed initially; two failed routes and two comparison controls passed a repeat on the unchanged executable. Initial failures remain retained; their cause is unknown. Installation and 18 copied-installed checks pass. ROM-free source-first package qualification is a separate release stage. [Exact artifacts, qualification and remaining limits](docs/FOUNDATION-INTERIOR-TOWN-DISPLAY-2026-10-11.md).

The preceding native **0.2.8 / unchanged Companion 0.3.2** adds generated original-cost loading instructions and current journal/map guidance toward GIANT after Dynamite joins. Exact state/timing, rendering, input/restore, launcher update/rollback and separate actual-GPU audio checks pass. The real checkpoint and rewind modal pumps have keyboard/indexed-controller close and audio-counter evidence. Full game AOT and campaign coverage remain unfinished. [Current build and precise limits](docs/FOUNDATION-GENERATED-CLEAR-GIANT-2026-10-11.md).

The preceding **native0.2.7 / unchanged Companion0.3.2** continuation adds a matching map legend, fixes two movement-driven terrain-cache restarts, expands guarded compound vehicle rendering, and adds current Graviton advice from the original chapter-five award/escort route. Exact copied-game journal, map, input/restore and launcher update/rollback checks pass. Eight separate Direct3D playback routes run near 60 fps with zero steady audio-counter failures. Staged original-event execution is recorded separately from natural campaign progress. [Current update and precise limits](docs/FOUNDATION-CONTINUATION-2026-10-11.md). [Preceding map update](docs/FOUNDATION-NAVIGATION-MAP-2026-10-11.md).

The earlier integrated 0.2.0 build passed reward/walking and restore proofs, configurable-input checks, 247 map/widescreen gates, controller/checkpoint checks and ten paced Direct3D/OpenGL audio routes. The exact self-contained launcher passed 60 source-first backend and 31 interactive GUI checks, plus all six legacy launch routes. [Release scope](docs/FOUNDATION-QOL-SETUP-2026-10-09.md). The guarded map decoder covers 409 selected resource links and 719 active layers. Those are **resource checks, not a count of completed playable maps**. Synthetic actor tests and natural gameplay coverage are recorded separately.

A new source build receives its own hash and remains unqualified until tested. The public build path has been exercised separately; see [VALIDATION.md](docs/VALIDATION.md) for what was checked and what remains private. Historical foundation documents retain their dates and coverage limits; referenced `local/` reports and fixtures are intentionally not published.

Next priorities are displayed-packet/raster proof through world seams, broader story/cutscene and party coverage, further verified journal chapters, and broader package/hardware checks. The navigation map is implemented; wider area and story coverage remain ongoing. Automatic GUI release updates remain open. A replacement HD artwork pack is deferred so it does not stall the playable foundation. [Full roadmap](ROADMAP.md).

Original-loader staged checks retain their explicit prerequisite edits and source hashes. They do not certify natural story progression. [Staged developer tooling](docs/FOUNDATION-STAGED-PROGRESSION-2026-10-09.md) and [isolated replay](BUILDING.md#isolated-developer-replay) explain how to use copied checkpoints beside copied executables.

## Contribute

Small, focused contributions are welcome: renderer fixes, reverse-engineering notes, controller checks, bounded replay tools, verified journal events and documentation. Please report a reproducible route rather than feeling obliged to play the whole game again. [Contribution guide](CONTRIBUTING.md) · [Report a bug](https://github.com/rages4calm/secret-of-the-stars-companion/issues/new?template=bug-report.yml).

Never attach ROMs, generated ROM-derived code, extracted packs, soundtrack audio, private saves or unlicensed cached hack source to an issue or pull request. Keep copyright/provenance notices intact and separate observed facts from hypotheses.

## Credits and licensing

Built on **[RetroPortingToolKit/snesrecomp](https://github.com/RetroPortingToolKit/snesrecomp), by Matthew Stanley and contributors**, with the runtime's retained snesrev, LakeSnes and other upstream lineage. Scale2x credit goes to **Andrea Mazzoleni**. The launcher reuses Carl Prewitt Jr.'s MIT-licensed EarthBound Companion UI patterns; Zelda Companion informed the workflow and presentation direction. Tecmo and the original game's creators/rightsholders deserve the game credit.

This is an unofficial fan project with no affiliation or endorsement from Tecmo or the original game's rightsholders. Project licenses do not grant rights to original game content.

The native foundation, runtime patch, project tools and documentation are **source available under PolyForm Noncommercial 1.0.0**, with retained third-party exceptions. Companion code is **MIT**. This repository is not uniformly MIT licensed. [Credits](CREDITS.md) · [License](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md).
