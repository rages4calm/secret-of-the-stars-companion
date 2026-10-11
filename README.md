# Secret of the Stars Companion

**A Windows PC-port foundation for Tecmo Secret of the Stars, with a Companion launcher, controller support, enhanced pixel art and experimental widescreen.**

[![Stage](https://img.shields.io/badge/stage-active%20development-244b6b)](ROADMAP.md)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-244b6b)](BUILDING.md)
[![Contents](https://img.shields.io/badge/contents-ROM--free%20source-244b6b)](docs/VALIDATION.md)

**Project author:** Carl Prewitt Jr. / [rages4calm](https://github.com/rages4calm)

> [!IMPORTANT]
> Bring your own clean, unheadered **Tecmo Secret of the Stars (USA)** ROM. This repository contains authored source, development tools, documentation and six reviewed feature screenshots. **No ROM, generated game code, extracted art, soundtrack, save, checkpoint or playable game binary is included.** Your game data stays local.

> [!NOTE]
> **Early development: native foundation 0.2.8 / Companion 0.3.2.** A local Windows build runs opening gameplay, menus and combat, with focused automated checks. This is **not yet a complete native/AOT recompilation or a full-campaign-qualified widescreen port**. Substantial guest execution still uses the pinned SNES runtime's interpreter. HLE host staging and native presentation enhancements do not change that coverage claim.

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

## What works today

| Area | Implemented behavior | Current limit |
| --- | --- | --- |
| Windows foundation | Compiled C/SDL3 host with native game-specific enhancements and guarded original execution | Complete native/AOT game execution is still future work |
| Companion launcher | ROM validation, source-build progress/cancellation, isolated profile updates/rollback, explicit title/selected-copy resume and protected settings edits | Requires Windows development tools for the native source build; no public playable download yet |
| Enhanced pixels | Independently selectable Scale2x-based presentation and fullscreen output | Upscaling preserves original artwork; it is not a replacement HD world pack |
| Widescreen scenery | Stable 400-pixel canvas, selected original primary/secondary map resources, title panorama and sixteen authored battle-side layouts using original cells | Original 256-pixel center stays exact; selected overworld edge crossings retain terrain margins; unsupported states retain centered imagery and side bars |
| Widescreen actors | Ordinary party, regular/reserved packets, guarded driving/parked and selected compound vehicle rosters, and selected later world-map actors | Original allocation, packet and art checks authenticate supported contexts; broader party/effect/vehicle contexts remain open |
| Controls | Editable keyboard/controller game buttons and hotkeys, twenty checkpoint bindings, fullscreen and reachable HUD/journal/rewind controls | Broader physical-controller testing remains open |
| Menu and battle QoL | Optional faster field menus and toggleable HP bars with a widescreen battle sidebar | The HP panel is an authored enhancement, not a bundled ROM hack |
| Rewards and movement | Independently adjustable 1–10× battle XP/gold; bindable 1–3× field movement boost; hold/toggle fast-forward | Movement accelerates guarded ordinary walking; unsupported/scripted motion keeps original pace |
| Quest journal | Objective, route/advice and current-progress panel; verified opening, Badbad/Dog Pill, town building, Morgan and current chapter-five Graviton directions; J / left-stick click toggles it | Current flags and possession recompute after restore; further chapters and deterministic quest history remain open |
| Navigation map | Original current-area terrain and your position; original world towns and an optional blinking verified destination; M / Back + left-stick click | Unsupported areas use a clear fallback; no exploration history or guessed objective coordinates |
| Audio and stability | Original SNES audio, cached host composition, repaired mosaic overrun and checked audio/OpenGL allocations | Finite paced GPU/audio routes pass; every cutscene and hardware configuration is not certified |
| Saves and rollback | Guarded checkpoint loading, restore/cache reset and protected copied-save testing | Local state schemas are build-specific; test on copies and keep in-game saves backed up |

**Widescreen is experimental and defaults off.** It expands scenery and observed actors without spawning extra actors or changing collision, activation or game speed. CPU/metatile/dispatch experiments are archived; original CPU budgets are preserved.

## Build from your own ROM

There is no public playable download yet. Developers can build the native foundation from this source snapshot:

```powershell
git clone https://github.com/rages4calm/secret-of-the-stars-companion.git
cd secret-of-the-stars-companion
python tools/build_public_foundation.py --rom "D:\My Games\Secret of the Stars (USA).sfc"
```

Install the prerequisites in [BUILDING.md](BUILDING.md) first. The helper fetches the pinned runtime, applies this project's patch, generates code locally, compiles a fresh native executable and creates an isolated profile under ignored `local/`. It does not copy your ROM, replace your existing installation or manufacture a passing gameplay receipt. Existing modified runtime checkouts are preserved rather than reset.

Build the self-contained launcher with `python tools/build_public_companion.py`, then open `Start Secret of the Stars Companion.cmd` or the generated Companion EXE. Its Setup page validates your ROM and builds/adopts a fresh native profile without private gameplay fixtures. See [BUILDING.md](BUILDING.md). Historical native preview scripts and fixture checkers remain development adapters.

In **Enhancements**, 100% means the original XP/gold payout; 200% means 2×. Movement boost defaults to **Left Shift / controller L2**, and fast-forward to **Tab / controller R2**. Change these and other bindings in **Controls** and **Hotkeys**; fast-forward can be held or toggled. Existing custom profile bindings are retained. [QoL implementation and limits](docs/FOUNDATION-QOL-2026-10-09.md).

Companion **0.3.2** adds map and objective-marker settings and an assignable Map action. Missing bindings use **M / Back + left-stick click** unless that exact shortcut is already occupied. Existing explicit bindings win. Map and journal panels close each other.

Companion **0.3.1** added **Original pixels / Enhanced pixels / Experimental widescreen** display choices, **Revert changes**, current fullscreen/hotkey hints and a journal item-summary setting. Presets preserve sound, rewards and custom bindings.

Companion 0.3.0 adds **Update selected profile** and **Use previous profile** in Setup. Updates create a new isolated folder with checked copies of settings/saves; rollback selects the retained earlier folder and preserves newer progress separately. Different native builds require compatible save declarations and matching execution-state ABI. A ROM-free source-first ZIP can bundle the self-contained GUI, authored source and notices; native game compilation still needs the documented tools. [Packaging instructions](BUILDING.md#package-the-source-first-launcher) · [Update and package qualification](docs/FOUNDATION-PACKAGE-UPDATES-2026-10-09.md).

## Verification and remaining work

Native **0.2.8 / unchanged Companion 0.3.2** adds generated original-cost loading instructions and current journal/map guidance toward GIANT after Dynamite joins. Exact state/timing, rendering, input/restore, launcher update/rollback and separate actual-GPU audio checks pass. The real checkpoint and rewind modal pumps have keyboard/indexed-controller close and audio-counter evidence. Full game AOT and campaign coverage remain unfinished. [Current build and precise limits](docs/FOUNDATION-GENERATED-CLEAR-GIANT-2026-10-11.md).

The preceding **native0.2.7 / unchanged Companion0.3.2** continuation adds a matching map legend, fixes two movement-driven terrain-cache restarts, expands guarded compound vehicle rendering, and adds current Graviton advice from the original chapter-five award/escort route. Exact copied-game journal, map, input/restore and launcher update/rollback checks pass. Eight separate Direct3D playback routes run near 60 fps with zero steady audio-counter failures. Staged original-event execution is recorded separately from natural campaign progress. [Current update and precise limits](docs/FOUNDATION-CONTINUATION-2026-10-11.md). [Preceding map update](docs/FOUNDATION-NAVIGATION-MAP-2026-10-11.md).

The earlier integrated 0.2.0 build passed reward/walking and restore proofs, configurable-input checks, 247 map/widescreen gates, controller/checkpoint checks and ten paced Direct3D/OpenGL audio routes. The exact self-contained launcher passed 60 source-first backend and 31 interactive GUI checks, plus all six legacy launch routes. [Release scope](docs/FOUNDATION-QOL-SETUP-2026-10-09.md). The guarded map decoder covers 409 selected resource links and 719 active layers. Those are **resource checks, not a count of completed playable maps**. Synthetic actor tests and natural gameplay coverage are recorded separately.

A new source build receives its own hash and remains unqualified until tested. The public build path has been exercised separately; see [VALIDATION.md](docs/VALIDATION.md) for what was checked and what remains private. Historical foundation documents retain their dates and coverage limits; referenced `local/` reports and fixtures are intentionally not published.

Next priorities are displayed-packet/raster proof through world seams, broader story/cutscene and party coverage, further verified journal chapters, and broader package/hardware checks. The navigation map is implemented; wider area and story coverage remain ongoing. Automatic GUI release updates remain open. MSU-1 music is conditional on finding and verifying a compatible driver and track map. A replacement HD artwork pack is deferred so it does not stall the playable foundation. [Full roadmap](ROADMAP.md).

Native 0.2.3 derives Aris advice from the original stage-zero Pennon flag, independently of David's introduction. Its terrain bridge authenticates the displayed packet and full original scroll; actor discontinuity refusals remain intact. Source-only [wrapping-B0](experiments/wrapping-b0/README.md) and [original-cost native metatile](experiments/metatile/README.md) prototypes have their own finite proofs and opt-in helpers; they remain excluded from normal installation. Original-loader staged evidence does not certify natural story progression. [Current staged developer tooling](docs/FOUNDATION-STAGED-PROGRESSION-2026-10-09.md) includes explicit checkpoint edits, and [BUILDING](BUILDING.md#isolated-developer-replay) explains copied-executable replay isolation.

The [October 10 continuation](docs/FOUNDATION-CONTINUATION-2026-10-10.md) records
measured native-metatile costs, displayed boundary proof and the original Pennon event. The current
eleven-hook prototype adds host processing cost on tested routes; it remains
excluded from player builds. Original guest timing remains unchanged.

## Contribute

Small, focused contributions are welcome: renderer fixes, reverse-engineering notes, controller checks, bounded replay tools, verified journal events and documentation. Please report a reproducible route rather than feeling obliged to play the whole game again. [Contribution guide](CONTRIBUTING.md) · [Report a bug](https://github.com/rages4calm/secret-of-the-stars-companion/issues/new?template=bug-report.yml).

Never attach ROMs, generated ROM-derived code, extracted packs, soundtrack audio, private saves or unlicensed cached hack source to an issue or pull request. Keep copyright/provenance notices intact and separate observed facts from hypotheses.

## Credits and licensing

Built on **[RetroPortingToolKit/snesrecomp](https://github.com/RetroPortingToolKit/snesrecomp), by Matthew Stanley and contributors**, with the runtime's retained snesrev, LakeSnes and other upstream lineage. Scale2x credit goes to **Andrea Mazzoleni**. The launcher reuses Carl Prewitt Jr.'s MIT-licensed EarthBound Companion UI patterns; Zelda Companion informed the workflow and presentation direction. Tecmo and the original game's creators/rightsholders deserve the game credit.

This is an unofficial fan project with no affiliation or endorsement from Tecmo or the original game's rightsholders. Project licenses do not grant rights to original game content.

The native foundation, runtime patch, project tools and documentation are **source available under PolyForm Noncommercial 1.0.0**, with retained third-party exceptions. Companion code is **MIT**. This repository is not uniformly MIT licensed. [Credits](CREDITS.md) · [License](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md).
