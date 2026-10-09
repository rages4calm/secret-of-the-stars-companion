# Next game: editable native port and reusable tools

Planning snapshot copied October 8, 2026 for Secret of the Stars. Original reference document: `C:\Users\crono\Documents\Game Porting\NEXT-GAME-PLAN.md`. Local game selection and scope are in the project-root handoff. Evidence-cache links point back to the existing Game Porting reference folder; no upstream code or game assets were copied.

Prepared October 8, 2026. This is a plan for the next selected game, not an EarthBound feature expansion. EarthBound remains in maintenance. No new framework, editor or port has been implemented by this planning pass.

Updated through the October 8 discussion of patch-first recompilation, HD Mode 7, performance and the owner's EarthBound/Zelda presentation. The next game is still unselected; this document is ready for that decision and does not start a new build or ongoing monitoring task.

## The goal in plain language

Make a native PC version we can meaningfully edit: gameplay rules, characters/items, dialogue, art, maps or selected ROM-hack features. Give it practical PC settings and a clear mod workflow. Build or extend tools that make changes visible and testable, instead of depending on repeated full playthroughs and enormous late audits.

**Required enhancement scope:** assume content beyond the base ROM, selected ROM/QoL hacks, true widescreen and replacement HD graphics/textures. These are core selection requirements, not optional launcher extras. For a 2D game, HD graphics means replacement sprites, tiles/backgrounds and applicable UI art; textures apply where the chosen game/renderer uses them. A higher display resolution alone does not meet this requirement.

Preserve an attractive enhanced-pixel-art mode like the owner's existing EarthBound and Zelda ports, alongside independently selectable replacement artwork. The recent discussion explains why existing art can look excellent fullscreen; it does not remove the previously requested HD replacement capability. Agree the replacement pack's art style and coverage when selecting the game.

The exact game, console and desired hacks have not been selected. Choose the implementation after those are known. There is no single best engine for every console/game.

## Preferred approach

1. **A proven, editable native port is the first candidate when available.** Prefer readable gameplay code, working desktop support, documented build/distribution terms and usable debugging over a project that merely produces a ROM or starts a game. Verify that the actual edition and desired changes fit.
2. **Otherwise use a shared recompilation runtime with a named map of game functions and state.** Public decompilation/disassembly knowledge can identify movement, damage, inventory and script routines. Replace or extend the specific routines we need without requiring a complete game rewrite.
3. **A bare recompiler output is only the starting point.** Require editable interfaces, content access and focused comparison tests. Keep authored changes separate from generated files so regeneration does not erase our work.

Evaluate a **patched-ROM-first recompilation** early when desired hacks already exist. Compare its actual effort with adapting a mature native port before deciding to recreate QoL changes manually. Known working hacks can save substantial implementation work when their changed code/data become the input to a suitable recompiler; compatibility remains specific to the chosen game, hack set and runtime.

My default architecture is a shared runtime plus understood game logic, explicit mod interfaces and our own inspection/replay tools. A mature native port may already supply much of this. Choose the base with the least missing infrastructure for the actual feature wishlist, rather than choosing from the words “decomp” or “recomp.”

Require an enhancement renderer that can load external higher-resolution art and draw it at the appropriate resolution, independently of the original low-resolution hardware surface. Preserve original gameplay coordinates/collision and translate those into presentation coordinates. New content, scripts and mod state need an explicit native loading path, not unused files in a folder. A base limited to a stretched ROM framebuffer is insufficient without renderer work; include that work honestly in the choice.

Matthew Stanley's [decomp-annotated recomp approach](https://1379.tech/recomp-vs-decomp-wrong-question/) combines reusable execution infrastructure with game-specific names/understanding. This supports substantial modifications; recompilation does not inherently make gameplay uneditable. The article's demos are examples, not a promise that another game or hack is already supported.

## What to prove before a large adaptation

Inspect at most three credible foundations initially. Record a short comparison and the largest unknown for each. Avoid a whole-source audit as the initial task. Start with the owner's three most important desired changes and a representative hack, if any.

For the leading candidate, make a small playable proof:

| Proof | Useful result |
|---|---|
| Baseline | Run ordinary gameplay, a transition and a demanding representative scene; distinguish real progression from a prepared checkpoint. |
| Gameplay edit | Change one real rule, such as movement speed or damage. Confirm the actual consumer changed and disabling it returns the reference behavior. |
| Content edit | Change an asset or dialogue/map record through a repeatable import path and see it in the running game. |
| Added content | Load one genuinely new native content record or script outside the ROM and demonstrate its real gameplay use. |
| HD replacement | Render one external higher-resolution asset at real added detail; verify animation, positioning, clipping, toggling and cold restore. Display scaling alone fails this proof. |
| Widescreen | Show actual additional world area, retain correct HUD/menus/effect bounds and exercise a transition. Check camera/world reachability and early event/spawn activation. |
| Hack feature | Prove one representative feature through patched-ROM recompilation or native adaptation, compare its behavior with the intended patched reference, and list the remaining requirements. |
| Timing/performance | Record game-update and presentation rates separately. Verify input, audio and game pace; measure demanding scenes before claiming reduced slowdown or higher-rate motion. |
| Recovery/replay | Restore a copied checkpoint in a fresh process and run the same recorded inputs twice; compare stable state, not host pointer addresses. |
| Tool usefulness | Produce one concise report showing which changed function/record took effect and where a deliberately injected error is detected. |

If those proofs expose an unsuitable base, reassess before building the launcher or adapting hundreds of features. Do not call a successful opening proof full-game compatibility. Give the owner a compact decision, the concrete evidence and the next bounded step.

## Tools we can build or extend

These are intended capabilities, not a request to build a universal engine before choosing a game. Reuse applicable components and write the missing parts. The user's preference explicitly permits original tools and extensions.

| Tool | What it lets us do | Build it when |
|---|---|---|
| Named state inspector | See the room, actor, inventory, flags, camera and relevant script state without guessing from a screenshot. | First gameplay modification. |
| Asset/script editor and importer | Edit supported art, text or map/data records; preview the real result and report invalid references. | First content modification. Reuse a suitable game editor where available. |
| Menu layout editor/preview | Capture real menu elements, edit layout records, reload them and flag text/number/cursor clipping. | First UI change; prove one menu round trip before building a large editor. |
| Replay/comparison runner | Load a test copy, replay inputs, capture frames/state and identify the first difference from a reference. | Early proof, before large modifications. |
| Renderer inspector | Show camera/effect bounds, layer ownership and authored scene edges; inspect the first frame after a transition. | Widescreen or rendering work. |
| HD asset browser/preview | Map stable game asset IDs to replacement sprites/tiles/textures; inspect resolution, palettes, anchors, frame timing and missing coverage. | Before producing or importing the HD pack. |
| Mod/hack change inventory | Track every selected change as implemented, unnecessary on PC, unsupported or untested, with a concrete test/evidence version. | At the start of each hack adaptation. |
| Mod packaging and compatibility checker | Validate targets, options, dependencies/conflicts and save compatibility before activation. | Before supporting more than one independently selectable mod. |

Start with a small useful inspector/replay runner; grow it from actual failures. Do not spend weeks on an unused editor, speculative netplay or a universal patch translator. A reusable command/report format can serve multiple games, while each game supplies its state, inputs, symbols and asset adapter.

## How mods and ROM hacks should work

Treat a mod as a declared change to a supported game version. Separate cosmetic/data changes from gameplay code and progression changes. Record target game/base hashes, version, options, dependencies, conflicts and state/save requirements. Verify enable, disable and restart behavior. Code-changing hooks must be rebuilt against a documented interface or use an explicitly supported extension mechanism; a ZIP alone does not create one.

For each desired ROM hack, identify changed content, altered routines, scripts/events, expanded memory/cartridge layout and save changes. A patched ROM can sometimes be a recompilation input, but it needs analysis, hardware/mapping support and its own tests. In an existing high-level native port, those altered machine instructions usually need native equivalents. Do not promise that arbitrary IPS/BPS files will work as drop-in PC mods.

Prefer public hack source and a named change list. For a binary-only hack, first assess whether its changes can be understood and validated at a reasonable scope. Keep original reference behavior available and isolate modded progression where compatibility requires it. An old save should never silently load into incompatible gameplay/state. Save all deterministic custom state needed for replay; suppress duplicate external effects during replay.

### Patch-first route: evaluate before manually recreating QoL

[Lunar IPS](https://fusoya.eludevisibility.org/lips/) creates/applies IPS file changes; [Asar](https://github.com/RPGHacker/asar) assembles patch source. These can prepare a patched game input, while the port integration still establishes compatibility. Use the patch format and tool required by the selected hack.

| Foundation | How pre-patching can help |
|---|---|
| Fresh ROM-based recompilation | Analyze and generate code from the exact patched image. Compatible hack logic/data can carry into the native executable. Original-game analysis configuration may need changes. |
| Existing reconstructed native source | Adapt the relevant source behavior/data. Applying machine-code changes to a ROM does not update independently reconstructed C/C++ routines. |
| Hybrid with native replacements | Trace which implementation actually executes. Native replacements must include desired hack behavior even if the patched original routine remains available. |

For a credible patch-first candidate:

1. Retain a clean original and a separate working copy. Record input revision/hash, header/mapping expectations, patch versions/hashes and application order.
2. Apply selected patches one at a time and check representative behavior. Examine overlapping changes when combining hacks; successful file patching alone does not establish compatibility.
3. Confirm the runtime supports the resulting cartridge layout/chips and changed code/data. Regenerate against the patched image and adapt affected symbols, function boundaries and hooks. Preserve ROM identity checks with an explicit supported recipe rather than disabling them.
4. Compare the port with that patched reference in focused scenes, including progression/save behavior and any native replacements. Keep an original reference build available for diagnosis.
5. Automate a reproducible local preparation/generation recipe. Owner ROMs and derived assets stay local. Decide which changes form a fixed QoL baseline and which need native toggles or separate build variants; baked-in patches do not automatically become independently selectable mods.

Choose this route when the proof shows a net saving for the actual wishlist. Keep new native content, external HD artwork, PC UI and scene-aware widescreen as explicit integration work.

## Presentation, artwork and performance are separate capabilities

| Capability | What to prove |
|---|---|
| High-resolution output | The intended window/fullscreen resolution, proportions and usable UI. Output size alone does not establish finer game-art detail. |
| Enhanced pixel-art scaling | Original sprites/tiles remain attractive and readable at the selected size. Offer sharp and smoothing options appropriate to the art. |
| HD Mode 7 | Where applicable, rotated/scaled backgrounds are sampled more finely from their source data. This is a distinct renderer feature, with its own fallbacks and performance cost. |
| Replacement HD art | External higher-detail sprites, tiles, backgrounds/UI or textures are actually loaded and used, with declared coverage. |
| True widescreen | Additional scene area is drawn correctly, with suitable camera, HUD, effects, transitions and actor-visibility policies. |
| Higher presentation rate | Distinguish repeating existing frames, interpolating new frames and changing simulation frequency. Preserve intended gameplay speed, input and audio. |
| Fewer hardware restrictions | Verify the specific removal of slowdown or sprite limits. More visible sprites and smoother motion are separate results. |

The owner's EarthBound settings were checked as Scale2x-enhanced output with sharp final scaling and color grading. Zelda Companion was configured for OpenGL/xBRZ, 16:9, enhanced Mode 7 and no sprite limits. These show useful presentation without a replacement art pack; settings inspection is not a new performance measurement or renderer test. See the [local presentation references](PROJECT-EXAMPLES.md).

[snesrecomp's HD Mode 7](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/docs/HD_MODE7.md) is opt-in and distinct from CPU execution, widescreen and temporal interpolation. Confirm surface binding/backend support and game-specific coverage before advertising it. [Star Fox Enhanced's architecture](https://github.com/kandowontu2/starfox-enhanced/blob/43bece01fb876d9a5ddb5d2d9efc827ab32d8375/docs/ARCHITECTURE.md) demonstrates fixed 20 Hz logic with interpolated presentation; that is a project-specific implementation, not an automatic guarantee for every recompiled game.

## HD artwork and new-content delivery

An editable port, an HD-capable renderer and a finished HD art pack are separate deliverables. The requested project needs all applicable deliverables; source availability does not automatically supply the artwork.

- Inventory the chosen game's sprites, environments, UI and textures. Record which are replaced, reused intentionally or still awaiting work. Define art coverage when the game is selected; do not label a single high-resolution demo a complete HD edition.
- Source permitted community artwork or produce our own original assets as appropriate. Preserve a consistent art direction, readable silhouettes, frame counts/timing and anchors. Track source/author/terms with each pack.
- Load replacements using stable IDs and declared game/pack versions. Report missing assets, bad dimensions, duplicate/conflicting overrides and incompatible frame layouts. Keep a reliable original-art fallback for diagnosis.
- Test dense scenes, transparency, transitions and large effects. Measure memory/performance and resource lifetime rather than relying on the original SNES-sized buffers.
- Keep wide drawing from changing collision or triggering progression early. Test first visible frames, camera limits, authored arenas and screen-bound effects; decorative margins are not evidence that every map is safely widened.
- Implement new game content through defined records/scripts or understood gameplay functions. Version any extra deterministic state, include it in snapshots/replays and establish save compatibility before release.

If the selected foundation cannot meet these requirements reasonably, choose another foundation or expose the substantial engine work before committing. This is why proving HD replacement, widescreen and one added content feature belongs near the beginning.

## Lessons from the supplied project examples

The focused [project-example review](PROJECT-EXAMPLES.md), prepared October 8, 2026, records pinned references from Star Fox Enhanced, UrbanRecomp, MegaManX2Recomp, Lufia2SNESRecomp, LakeSnes and Asar. It distinguishes source/documentation inspection from runtime verification and notes the unconfirmed location of Lufia's separate visual menu editor.

Apply these concrete lessons when choosing the next game's foundation:

- Separate game update timing from presentation rate. Repeated frames, interpolated motion and actual higher-rate simulation are different features.
- Decode meaningful world/model/UI data rather than trying to recover everything from a final framebuffer. Preserve game-specific animation and collision semantics.
- Prove a real menu capture/edit/reload workflow. Layouts should be data with validation; a launcher settings panel is not an in-game menu editor.
- Define scene-specific camera, UI, actor-visibility, spell/effect and transition policies. Rendering more scenery and activating more enemies are different changes.
- Compare stable gameplay state and the newly rendered regions. An unchanged original rectangle does not prove widescreen margins correct.
- Trace mod hooks through generated and compatibility execution paths. A package's activation must reach the implementation used by the game.

These are selection and prototype requirements; this review did not install a framework, build an editor or alter EarthBound.

The [Lufia companion-project follow-up](PROJECT-EXAMPLES.md) makes the separation concrete: `Lufia2Decomp` owns portable reconstructed game behavior and resource decoding; `snesrecomp-platform` owns shared presentation/host support; the game port owns integration and enhancements. Borrow that organization where appropriate. Preserve explicit bindings between verified routines and active replacements, and verify that asset extraction has a working import path before promising an editor.

## Where the reviewed resources fit

- [snesrecomp](https://github.com/RetroPortingToolKit/snesrecomp): candidate for an appropriate SNES game, not a universal runner for other consoles. It translates 65816 code and models surrounding hardware. Each title still needs integration and validation. Check its current mapper/chip support against the real game and any expanded hack.
- [HD Mode 7](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/docs/HD_MODE7.md): opt-in finer background sampling, separate from artwork replacement and frame-rate changes. It needs host/game integration and measured coverage; it does not apply an HD upgrade to all drawing modes.
- [Lunar IPS](https://fusoya.eludevisibility.org/lips/) and [Asar](https://github.com/RPGHacker/asar): tools for preparing selected ROM changes. Evaluate the patch-first route alongside source adaptation; patch application is not port compatibility validation.
- [Routine replacement](https://github.com/RetroPortingToolKit/snesrecomp/blob/7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0/docs/HLE_FUNC.md): the current `hle_func` seam lets a port replace an understood guest routine with authored C. Original/reference builds can omit replacements for comparison. Caller coverage and interpreter paths need checking; this is not an unrestricted source-editing engine.
- [Mod packages](https://github.com/RetroPortingToolKit/snesrecomp/blob/7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0/docs/MOD_PACKAGES.md): current packages contain data and activate trusted behavior already linked into the title. They do not carry arbitrary DLLs/native code. A richer game editor or new gameplay plugin capability would require deliberate extension. Investigate the specific title integration rather than assuming every mod demo is a general package feature.
- [recomp-ui](https://github.com/RetroPortingToolKit/recomp-ui): candidate for shared launcher/in-game settings; the host still owns applying settings, input routing, persistence and renderer lifecycle. It can provide presentation for tools, not the tools' game-specific behavior.
- [Lufia2Decomp](https://github.com/Cellenseres/Lufia2Decomp): a concrete example of portable semantic game logic, named interfaces and per-function verification/binding boundaries. Its game-specific code is not reusable gameplay logic for another title, but its organization and integration pattern are useful.
- [snesrecomp-platform](https://github.com/Cellenseres/snesrecomp-platform): candidate shared SNES presentation/host layer with backend selection, separate UI overlays, semantic HD Mode 7 and pacing. It does not supply a full HD replacement pack, game editor or game-specific widescreen implementation. Check contracts against the selected runtime and consumer revision.
- [rbengine](https://github.com/RetroPortingToolKit/rbengine): small offline snapshot store, potentially useful for replay/rewind. It does not supply a game's serializer. The prior 18-check snapshot unit test is not a future game's state/replay qualification.
- [recomp-net](https://github.com/RetroPortingToolKit/recomp-net): consider if multiplayer is requested and the game has defined multiplayer semantics. It is not needed just to make a moddable single-player port.
- [Faithful and custom rendering](https://1379.tech/faithful-first-then-let-go-experimenting-with-custom-renderers/) and [widescreen patterns](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/docs/WIDESCREEN_PATTERNS.md): maintain a reference path, then add enhancements with real scene/effect boundaries. Better output resolution does not automatically mean replacement HD artwork or correct expanded visibility.
- [Co-simulation](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/SNES_COSIM.md): reference for earliest-difference investigation and proving that a comparison detects injected faults; adapt only the applicable layers.

Sources were reviewed for planning, not installed or certified for an unselected game. snesrecomp was inspected at `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`; refresh all framework contracts and terms at project start. Other consoles require their own appropriate foundations.

## A bounded working process

- Keep a clear feature inventory from day one, including actual implementation and test status. Avoid having to infer completeness from old audit prose at the end.
- Preserve a clean original baseline and pinned tool/runtime versions. Record supported inputs and keep owner-derived ROM/assets/saves local.
- Prove changes in narrow scenes and repeatable tests. Broaden when a defect reveals a shared risk; do not rerun every suite for a small isolated edit.
- Verify the actual release package/setup/recovery when binaries change. Keep historical evidence tied to its exact build.
- Use short volunteer tests and selected natural-play checks. A complete campaign is useful evidence, but repeated owner campaigns are not the default debugging tool.
- Report scope, findings and remaining uncertainty early. Obtain explicit new scope before a large expansion, broad audit or agent review. Never silently build every proposed tool.
- Freeze the agreed features when complete and move to report-driven maintenance. Research can remain a reference without keeping the project open.

## Ready-to-use project request

> I want to build an editable native PC version of **[game / console / edition]**. My priorities are **[three gameplay/content changes]**, and I want **[specific mods or ROM hacks, if any]**. Compare at most three credible foundations: mature native ports, decompilations/disassemblies and appropriate shared recompilation runtimes. Select the one that makes these changes easiest to understand, implement and test. Do not choose a base solely because it launches the game.

> Treat added content outside the base ROM, selected ROM/QoL hacks, true widescreen and real replacement HD graphics/textures as core requirements. Select or extend a renderer and asset pipeline that can deliver them. Separate high output resolution from new artwork, track the full agreed art coverage, and establish memory/performance/save behavior for extra content.
>
> Evaluate applying compatible QoL hacks to a private ROM copy before recompilation as an early candidate, and compare that effort with adapting an existing native port. Record patch order/hashes, regenerate from the intended input, and verify active native replacements preserve the changes. Keep enhanced pixel-art presentation independently selectable from replacement artwork. Assess HD Mode 7 where applicable, and distinguish simulation speed, interpolation, presentation rate and sprite-limit removal.
>
> Before a large adaptation, prove original gameplay, one real gameplay edit, one imported content edit, one added content feature, actual HD asset replacement, true widescreen, one representative requested hack feature, and copied-checkpoint replay/recovery. Build or extend practical inspectors, editors/importers, asset previews and replay/comparison tools wherever they reduce work. Keep authored changes separate from generated output and define explicit mod/save compatibility.
>
> Maintain a checklist of each requested feature and its implementation/test evidence. Keep a faithful reference mode, protect my progress, and use focused tests instead of repeated full playthroughs. Do not promise universal ROM-hack compatibility. Give me a concise recommendation and a playable proof with honest coverage limits before committing to a large conversion. Avoid broad audits or agent reviews unless I explicitly request them. Finish the agreed scope and move to maintenance.
