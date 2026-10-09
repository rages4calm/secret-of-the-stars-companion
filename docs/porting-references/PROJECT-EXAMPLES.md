# Examples for the next editable native game port

Planning snapshot copied October 8, 2026 for Secret of the Stars. Original reference document: `C:\Users\crono\Documents\Game Porting\PROJECT-EXAMPLES.md`. Local game selection and scope are in the project-root handoff. Evidence-cache links point back to the existing Game Porting reference folder; no upstream code or game assets were copied.

Reviewed October 8, 2026. These are implementation references for an unselected future game. This research does not expand the frozen EarthBound feature set or select one of these games as our next project.

Updated through the October 8 discussion of Lunar IPS/patch-first recompilation, HD Mode 7 and the owner's existing EarthBound/Zelda presentation. Links to moving upstream branches are reference points to refresh when the next game is selected; pinned inspections below retain their historical scope.

Scope: selected public READMEs, architecture/rendering documentation, menu-layout implementation, mod activation code and repository metadata. No upstream project was built, installed or played. Upstream test results below describe the authors' evidence, not tests performed here. A source checkout and a published release can differ; refresh the relevant revision when choosing a foundation.

## What each example contributes

### Star Fox Enhanced: separate simulation, rendering and asset interpretation

[Project](https://github.com/kandowontu2/starfox-enhanced), inspected at `43bece01fb876d9a5ddb5d2d9efc827ab32d8375`.

The [architecture](https://github.com/kandowontu2/starfox-enhanced/blob/43bece01fb876d9a5ddb5d2d9efc827ab32d8375/docs/ARCHITECTURE.md) describes fixed 20 Hz game updates with interpolated presentation. Input presses are retained until an update consumes them. Increasing render FPS therefore need not accelerate movement, damage or random-number use.

Its canonical model pipeline decodes assembled game data into an intermediate representation retaining face order, animation commands, textures, lighting, LOD and collision information. Generic model export is useful for inspection but loses information needed to reproduce the game. World geometry and PPU-facing backgrounds/HUD remain separate.

The [enhanced-backdrop notes](https://github.com/kandowontu2/starfox-enhanced/blob/43bece01fb876d9a5ddb5d2d9efc827ab32d8375/assets/enhanced-backdrops/README.md) document actual replacement art, layer protection and seam handling, with incomplete stage/VR coverage. This is distinct from filtering existing art. The README also documents known-input ROM preparation and source-built patches, rather than arbitrary hack compatibility.

**Use for our next game:** preserve gameplay timing; make renderer and asset representations editable without discarding animation or collision semantics. Require runtime evidence for replacement artwork.

### UrbanRecomp: reconstruct extra scenery from meaningful game data

[Project](https://github.com/blackerking/UrbanRecomp), inspected at `1d01b4b671185dd94f0c0bfca6aaa997731ac1a3`.

Its [Adaptive Widescreen renderer](https://github.com/blackerking/UrbanRecomp/blob/1d01b4b671185dd94f0c0bfca6aaa997731ac1a3/docs/ADAPTIVE_RENDERER.md) reads the live city map and current graphics/palette state to draw additional terrain. It preserves the original view, adapts to portrait or wide windows, and positions advisor pages separately from the city/HUD. It does not change game memory or invent simulation actors outside the original interaction area.

The documented checks compare game state with the renderer enabled/disabled, but also inspect new margins: an unchanged original rectangle alone cannot prove the added scenery correct. Save snapshots must retain hardware latches and timing state for reliable replay.

The README documents ROM maps, graphics/text extraction, scenario-map extraction and a native equivalent of a save/load power fix. Its default execution is interpreter-led; AOT execution is an opt-in path, so the repository name is not enough to classify every execution route.

**Use for our next game:** extend the world from decoded map data, keep UI placement independent, and test the newly exposed picture as well as unchanged gameplay.

### MegaManX2Recomp: widescreen reaches beyond the drawing surface

[Project](https://github.com/mstan/MegaManX2Recomp), inspected at `eef9f1be59f2e6e12d63aaa6d04c23095e47f3e7`.

The [widescreen notes](https://github.com/mstan/MegaManX2Recomp/blob/eef9f1be59f2e6e12d63aaa6d04c23095e47f3e7/docs/WIDESCREEN.md) separately cover map margins, HUD anchoring, weather, actor activation, culling and record streaming. They warn that formulas can transfer from another game while addresses cannot. Guarded changes cover both generated code and interpreter paths; an effective hook must reach the execution route actually used.

The [activation plugin](https://github.com/mstan/MegaManX2Recomp/blob/eef9f1be59f2e6e12d63aaa6d04c23095e47f3e7/src/mods/x2_widescreen_plugin.c) toggles an implementation already linked into the game. Its package declares the target ROM, feature, default and save compatibility. This is a useful mod contract, not a demonstration of arbitrary executable mods loaded from a ZIP.

The documentation explicitly leaves broader stage testing pending. The README describes LLE-first execution, Cx4 support and debugging tools; it does not establish a finished replacement-HD-art edition.

**Use for our next game:** handle camera, effects, spawn and visibility as separate concerns. Decide whether earlier actor activation is an intended gameplay change and test it explicitly.

### Lufia2SNESRecomp: editable menus and gradual semantic replacements

[Project](https://github.com/Cellenseres/Lufia2SNESRecomp), inspected at `05752dc74dc87bc447484b57e3231529f4cd1b8f`.

The [menu implementation](https://github.com/Cellenseres/Lufia2SNESRecomp/blob/05752dc74dc87bc447484b57e3231529f4cd1b8f/src/lufia2_menu_ui.c) loads separate layout records, rejects invalid headers/checksums/geometry/duplicates and reloads valid file changes. It identifies menu elements and supports placement overrides. The [panel asset tool](https://github.com/Cellenseres/Lufia2SNESRecomp/blob/05752dc74dc87bc447484b57e3231529f4cd1b8f/scripts/ui_asset_tool.py) crops and compacts panel artwork, exports runtime images and previews tiled/stretched nine-slice panels.

**Editor uncertainty:** I verified these files and tools, but did not locate a separate public visual menu editor in the linked checkout or inspected dependency trees. It may be external or unpublished. Do not label the command-line panel tool a drag-and-drop editor.

The README documents optional verified decomp replacements, reference/fallback paths and a per-build function-source report. It distinguishes HD Mode 7 sampling from artwork filtering and display refresh from motion interpolation. Room metadata coverage is limited; authored records do not prove every transition works. Battle effects and original sprite geometry receive separate treatment.

**Use for our next game:** export real UI structure, edit it as data, preview/reload it, and preserve a reference path while replacing understood gameplay routines gradually.

### LakeSnes: hardware support and comparison reference

[Project](https://github.com/angelo-wf/LakeSnes), inspected at `9db90b86e46a377609305e298dd92d71cd1d4c8a`.

This is a C SNES emulator, with hardware components and an SDL2 frontend. It can inform reusable CPU/PPU/audio support or reference comparisons; it is not itself an editable native game's content/mod system. The original repository is archived and its README points to [dinkc64's fork](https://github.com/dinkc64/LakeSnes). That fork was not reviewed in this pass.

**Use for our next game:** reuse appropriate hardware knowledge or components where relevant. It does not remove the need to understand the game's own maps, scripts, rules and assets.

### Asar: build and understand source ROM hacks

[Project](https://github.com/RPGHacker/asar), inspected at `5fd539cd510e4a26afef66fc14e35ca6d8ff0497`.

Asar assembles SNES patch source into ROM changes, supporting 65c816, SPC700 and Super FX code. Its README describes command-line use, library bindings and byte/error-output tests. It is an assembler rather than a renderer or port engine.

**Use for our next game:** where a selected hack uses Asar, build its source against the correct input, identify what it changes, and adapt the relevant behavior/data to our native port. Assembling a hack does not by itself make those machine-code changes compatible with an existing native replacement.

## Follow-up: the two Lufia companion projects

Reviewed separately on October 8, 2026 after the owner supplied their links. The earlier dependency checks were only inventories; this follow-up inspected selected documentation, public interfaces and function metadata. No build or gameplay verification was performed.

### Lufia2Decomp: portable game behavior, with explicit integration boundaries

[Project](https://github.com/Cellenseres/Lufia2Decomp), inspected at `b0822005f40020b244df0708e18ec69014ff6a1e`. This is newer than the Lufia port's previously inspected decomp submodule pin, so its current interfaces cannot be assumed compatible with that older consumer.

The [architecture](https://github.com/Cellenseres/Lufia2Decomp/blob/b0822005f40020b244df0708e18ec69014ff6a1e/docs/ARCHITECTURE.md) separates reconstructed game behavior from the PC port. It supplies portable C, named functions, memory maps and per-function metadata. The consuming port owns integration bridges, original-ROM comparisons and enhancements. A verified routine does not activate automatically: the consumer must bind it separately.

Public [party interfaces](https://github.com/Cellenseres/Lufia2Decomp/blob/b0822005f40020b244df0708e18ec69014ff6a1e/include/lufia2/party.h) expose named operations for experience, derived stats and equipment totals. Some interfaces still preserve CPU state and original calling requirements; readable names do not make every routine independent of its old execution contract. Partial implementations can return at an original-code continuation boundary. The architecture also documents optional visibility policies and execution checkpoints through which the consumer can supply controlled behavior.

Its [README](https://github.com/Cellenseres/Lufia2Decomp/blob/b0822005f40020b244df0708e18ec69014ff6a1e/README.md) describes a separate compressed-resource decoder and command-line extraction tool. There is no compressor, so extraction alone is not an editing/import round trip. This is semantic reconstruction, not byte-matching reassembly or a standalone playable port. Function metadata describes the catalogued routines; it does not establish complete game coverage or our own verification.

**Lesson:** build named game interfaces and replace understood behavior incrementally, retaining original execution where necessary. Keep asset decoding usable by tools independently of the full game host.

### snesrecomp-platform: shared presentation and host support

[Project](https://github.com/Cellenseres/snesrecomp-platform), inspected at `233ab8b7a2f2cf75e3daa49b9d93ec5f125fe417`, matching the Lufia port's inspected platform pin.

The [README](https://github.com/Cellenseres/snesrecomp-platform/blob/233ab8b7a2f2cf75e3daa49b9d93ec5f125fe417/README.md) documents SDL, OpenGL and optional Vulkan presentation, aspect/scaling policies, portable PPU semantics and separate game/presentation pacing. It explicitly distinguishes more frequent presentation from future motion interpolation. HD Mode 7 reconstructs the affine plane at finer sampling; it does not supply a replacement art pack.

The [presenter interface](https://github.com/Cellenseres/snesrecomp-platform/blob/233ab8b7a2f2cf75e3daa49b9d93ec5f125fe417/include/snesrecomp_platform/presenter.h) accepts ordinary frames, semantic Mode 7 frames and independent overlays. UI can follow game coordinates or physical presentation coordinates. Games supply already-drawn UI surfaces; the platform positions/composites them and reports backend capabilities. This is useful infrastructure for crisp native menus, but it is not a menu-authoring tool, a universal content editor or a complete external texture-replacement system.

**Lesson:** share window/backend/pacing and presentation contracts across titles while keeping game-specific cameras, content, UI layout and mod behavior in the consuming port. The actual game still needs its own adapters and tests.

### The combined structure we should borrow

| Layer | Responsibility |
|---|---|
| Shared execution/platform | CPU/hardware support, window, input integration, graphics output and presentation timing. |
| Understood game logic | Named gameplay functions, state, scripts and resource formats, with preserved original behavior. |
| Game port and tools | Integration, selected QoL/mod changes, new content, HD replacements, widescreen policies and editors. |

Neither companion checkout revealed a separate public visual menu editor in the inspected inventories. The earlier menu-layout/tool findings remain valid; the location of the visual editor remains unconfirmed. These two libraries strengthen the recommended separation of responsibilities without establishing universal ROM-hack compatibility.

[Follow-up source manifest](<C:/Users/crono/Documents/Game Porting/references/2026-10-08-lufia-components/sources.json>) records the pinned revisions and selected files. Current GitHub-rendered pages can lag repository contents; the downloaded pinned files were used for the detailed findings.

## Follow-up: patching before making the port

The owner's [Romhacking.net utility link](https://www.romhacking.net/utilities/240/) identifies Lunar IPS. That page returned HTTP 403 during lookup; the [author's primary page](https://fusoya.eludevisibility.org/lips/) was available and confirms IPS creation/application. Lunar IPS applies binary file changes; Asar builds changes from assembly source. Neither tool supplies native-port compatibility.

**Practical conclusion:** preparing the desired patched game before ROM-based recompilation can save us recreating compatible QoL behavior. The recompiler must analyze the actual patched code/data, and the resulting game still needs integration and focused validation. [snesrecomp's pipeline and compatibility documentation](https://github.com/RetroPortingToolKit/snesrecomp#rom-compatibility) makes per-title analysis/integration requirements explicit.

An existing decomp-based native port executes its reconstructed source, so changing ROM instructions does not update that source automatically. In a hybrid, a native replacement can supersede the patched original routine; both routes must preserve the selected behavior. Patch combinations can overlap, move routines or change cartridge requirements. Keep a clean reference, a reproducible ordered recipe and an exact supported input identity. Decide which changes are a fixed baseline and which need independent mod controls.

This is an early candidate to compare with native adaptation, not a commitment to pre-patch every future game. The [next-game plan](NEXT-GAME-PLAN.md) now includes the proof and preparation steps.

## Follow-up: why the existing ports look good fullscreen

Selected local settings/source were checked on October 8, 2026, without launching either game or changing files. These findings explain the presentation path; they are not new frame-rate measurements or proof of every renderer effect at runtime.

| Port | Confirmed settings and implementation references |
|---|---|
| EarthBound Companion | Installed settings select 1920x1080 fullscreen, Scale2x-enhanced filtering, color grading and non-integer scaling. The SDL video implementation provides Scale2x/EPX processing and nearest-neighbour final sampling for this filter selection. Widescreen expands the world view. |
| Zelda Companion | Installed game configuration selects OpenGL with `xbrz-freescale.glslp`, 16:9, enhanced Mode 7, preserved aspect and no sprite limits. Its documented Smooth presentation scales/smooths original pixel artwork. |

Existing pixel art can look attractive fullscreen through suitable scaling, filtering, proportions and expanded scenery. Replacement art is a separately selectable creative enhancement with new detail. Retain the good enhanced-pixel-art experience while providing the replacement-HD capability already requested for the next game. This discussion does not cancel that requirement.

Local evidence locations (owner settings may change after this check):

- EarthBound source: `C:\Users\crono\Desktop\Projects\eb\native-source\port\unix\platform\sdl2_video.c`; settings/UI references in `github-repo\Companion\Program.cs` and `github-repo\README.md`.
- EarthBound installed selection: `C:\Users\crono\Games\EarthBound Redux Playthrough\v0.5.0-redux-dev.31\Game\earthbound.ini` and adjacent installation `UserData\settings.json`.
- Zelda configured presentation: `C:\Users\crono\Desktop\Projects\TheLegendOfZeldaALinkToThePast-SnesrevZelda3Launcher\Zelda Companion\Game\zelda3.ini`; documented profile in that workspace's `github-repo\README.md`.

### HD Mode 7 and smoother performance

[snesrecomp's HD Mode 7 documentation](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/docs/HD_MODE7.md) describes finer sampling of source tilemaps at fractional screen coordinates, with ordinary-frame fallbacks. It is separate from artwork replacement, CPU execution, widescreen and temporal interpolation. Supported game integration must be checked; the feature is not a universal upgrade for all sprites or background modes.

Higher output resolution, HD Mode 7, replacement artwork, wider scenery, higher presentation rates and removed sprite limits are separate capabilities. Record evidence for each. Star Fox Enhanced's inspected architecture uses fixed 20 Hz simulation plus interpolated rendering, allowing smoother presentation while preserving game pace. That is more than merely running the old update loop faster. Removing hardware sprite limits can improve completeness of drawing without itself creating higher-rate animation.

The [next-game plan](NEXT-GAME-PLAN.md) now distinguishes these deliverables and includes a timing/performance proof. Exact upstream contracts should be refreshed at project selection; no new game or graphics system was implemented by this documentation update.

## How this connects to the blog

Matthew Stanley's [decomp-annotated recomp article](https://1379.tech/recomp-vs-decomp-wrong-question/) argues for shared execution infrastructure plus game-specific understanding. His [custom-renderer article](https://1379.tech/faithful-first-then-let-go-experimenting-with-custom-renderers/) treats faithful rendering as a reference from which enhancements can depart. The examples above make those ideas concrete: different projects combine native routines, compatibility execution, meaningful game-data decoding and custom presentation in different proportions.

Our recommendation is an engineering inference from these sources: choose the foundation by how easily it supports the requested edits, not by its name. The desired result includes added content, selected hack/QoL behavior, actual replacement artwork and correct widescreen. Those still need game-specific implementation and proof.

## Changes to our next-game workflow

1. **UI editing belongs near the first prototype.** Prove a captured menu can become editable layout data and return to the game. A future editor should preview real labels/numbers/cursors and flag clipping, including equipment comparisons and long names. Reuse a verified editor if available; otherwise build a small adapter and visual editor when the game is selected.
2. **Separate clocks.** Establish simulation/input/audio timing before adding interpolation or higher presentation rates. Showing an unchanged frame more often is different from drawing interpolated movement.
3. **Use stable asset identities.** Decode game-specific records into an editable representation, then map them to external art. Preserve animation timing, anchors, priorities and collision independently of the artwork resolution.
4. **Make rendering policies scene-aware.** World, HUD, menus, single-target effects, whole-screen effects, credits and transition history need explicit ownership and bounds. This directly addresses the kinds of problems encountered during the EarthBound playthrough.
5. **Compare both original and added regions.** Replay fixed inputs, compare stable game state, and inspect expanded scenery/effects. Restore checkpoints in a fresh process; avoid treating a successful in-process rewind as proof of cold-save correctness.
6. **Treat enhancements as declared changes.** Record activation, target versions, source/runtime coverage and save compatibility. Keep authored logic separate from generated output. A selectable package is only useful if it actually activates the implementation.

These are prototype requirements and tool priorities, not tools built during this research. We will choose or extend components after the next game's console, edition and desired changes are known. No additional owner full playthrough is proposed.

## Local evidence

[Pinned source manifest](<C:/Users/crono/Documents/Game Porting/references/2026-10-08-project-examples/sources.json>) records the six project revisions and downloaded files. The adjacent directories contain selected upstream files and repository-tree inventories for navigation. For large implementation files, only relevant sections were inspected; a cached file is not a whole-file audit. GitHub's `NOASSERTION` license metadata is not a claim that a repository has no license.

Additional dependency trees inspected to locate Lufia's menu tooling:

- `Cellenseres/snesrecomp-platform` at the game-pinned `233ab8b7a2f2cf75e3daa49b9d93ec5f125fe417`.
- `Cellenseres/Lufia2Decomp` at the game-pinned `ab1e9c1d7e0d9e198948c08f34ab7262283f9b90`.
- `Cellenseres/snesrecomp` at the CMake-pinned `678b0656de909ffb9b762ff32dabc9e13425c811`.

The original dependency checks were file inventories. The follow-up section above records the later selected inspection of Lufia2Decomp and snesrecomp-platform. No upstream code or assets have been incorporated into our game or tooling.
