# Secret of the Stars: starter handoff

Latest continuation: [host buffer repair release](docs/FOUNDATION-HOST-BUFFER-RELEASE-2026-10-09.md).
Native 0.1.9 and Companion 0.1.2 are installed with protected saves/settings.
Double-click Secret of the Stars Companion.exe or the repaired CMD.
Optional Widescreen pairs selected terrain and ordinary actor margins on the
stable 400-pixel canvas; enhanced pixels apply throughout normal presentation.
Unsupported states retain the authentic center with side bars. Current stream
selection, secondary resources, party records and ordinary reserved OAM slots
have bounded observers with original center/guest/packet/restore parity.
Seven paced GPU/audio routes and all six launcher routes pass. Large/composite
and wrapping actors, natural multi-party/reserved margin positivity and campaign
coverage remain open. The private B0 canary is excluded from the installed build.
No guest CPU-budget, logic-rate, full native/AOT or HD/MSU claim is added.
Read current receipts for hashes, compilation inputs and protected backups.
Audio allocation failure now exits cleanly; OpenGL growth refuses failed draws
and retries without losing the prior buffer. Actual fault controls, guarded
presentation/queue checks, original-view parity and ten paced renderer/audio
routes pass. Private large-actor integration and wrapping contracts remain
uninstalled pending live qualification. Earlier continuation blocks are historical.

Owner's latest visual priority (October 9): polished enhanced pixel art and
true widescreen in the EarthBound/Zelda style; defer a full replacement HD art
pack to keep the playable port moving. Reuse the Companion launcher approach
and suitable local shared code. Existing eight-frame artwork is optional.
This supersedes the earlier requirement that a full HD pack be core near-term
scope. The 0.1.4 preview's choppy audio/gameplay requires a host-composition fix;
early nonzero audio alone does not qualify smooth playback. See the current
build receipt and continuation documents for the fixed artifact.

Current continuation: [cached presentation and steady audio, version 0.1.5](docs/FOUNDATION-PRESENTATION-AUDIO-2026-10-09.md).
It supersedes installed status below and repairs the 0.1.4 preview's measured
composition/audio starvation. Normal enhanced pixels and copied Likado terrain
width hold about 60 presentations/second in paced Windows checks; optional
frame art is also smooth in the tested route. Original game state and pictures
remain identical. Native original-cost clear/columns remain default-off, and
v3 checkpoints preserve the VRAM port state. v1/v2 remain accepted without
rewriting. Normal launch stays title-first with widescreen off until actors
and other scenes are qualified. A full replacement HD art pack is deferred.
Guest CPU acceleration, campaign/actor width, further journal events, MSU-1
and complete native execution remain open. Read the receipt for protected
installation hashes and the Companion launcher direction for the next UI work.

Prepared October 8, 2026 for a new Codex chat. Treat this as the continuation of the owner's game-port planning, with **Secret of the Stars on SNES** now selected. Research and architecture decisions are carried forward; development of this game has not yet begun.

## Read these first

1. This handoff.
2. [Next-game plan](docs/porting-references/NEXT-GAME-PLAN.md).
3. [Project examples and research](docs/porting-references/PROJECT-EXAMPLES.md).

The two supporting files are local snapshots of the documents already reviewed with the owner. Their text about an unselected next game describes the earlier planning stage; this handoff selects Secret of the Stars and takes precedence on that point. The original documents remain at `C:\Users\crono\Documents\Game Porting`. Evidence-cache links resolve to that existing folder, so downloaded upstream source does not need to be copied into this new project.

Absolute project root: `C:\Users\crono\Desktop\Projects\Secret of the Stars`.

## Current state and honest unknowns

- The project folder exists. Before this handoff preparation, its only observed root file was `Tecmo Secret of the Stars (USA).sfc`, an owner-provided ROM.
- This chat created this handoff and the two reference-document snapshots. It did not modify, patch, execute or extract the ROM.
- The ROM's actual revision, hash, header, cartridge layout and integrity have not been verified. The filename suggests USA; verify the input rather than treating the filename as identity.
- No game-specific build, source checkout, renderer, launcher, editor or playable proof has been prepared here. No porting foundation has been chosen.
- The owner has not supplied a particular hack list, art style or three prioritized gameplay changes for this title. No existing Secret of the Stars decomp/recomp or suitable hack has been established by this research.

## What the owner wants

Build an editable native PC game, with practical settings and mod/content interfaces. Assume added content outside the base ROM, selected QoL/ROM-hack features, true widescreen and actual replacement HD graphics/textures. For this 2D title, assess sprites, tiles/backgrounds and UI rather than promising a generic 3D texture system.

Keep attractive enhanced-pixel-art presentation independently selectable from replacement art. The owner liked how EarthBound and Zelda looked fullscreen; that visual approach is valuable too. Agree HD art direction and coverage for this game rather than silently substituting output scaling for new artwork.

Original tools and extensions are explicitly welcome. Reuse useful existing components and build missing inspectors, editors/importers and replay tools where they reduce real work. Avoid building a universal engine before proving this game's foundation.

The owner wants an easier, more reliable workflow than the EarthBound project. Avoid repeated owner full playthroughs, hours-long broad audits and unrequested agent reviews. Use bounded comparisons, focused fixtures, copied checkpoints and short playable proofs. Explain conclusions in plain language and distinguish implemented behavior from research or guesses.

## Decisions to preserve

- Compare at most three credible foundations initially: an editable native port if one exists, game-specific decomp/disassembly knowledge, and a suitable shared recompilation runtime. Choose for the actual feature needs and missing integration work, not the label.
- A useful default organization is shared execution/platform support, named/understood game logic, and game-owned enhancements/content/tools. A recompiler output alone is a starting point.
- **Evaluate patch-first recompilation early.** Compatible existing QoL hacks applied to a private ROM copy may save recreating their behavior. Record original identity, patch versions/hashes/order and resulting identity; regenerate/analyze the actual patched input. Verify native replacements and interpreter paths preserve the intended changes.
- Patching a ROM does not automatically change reconstructed native C/C++ routines. A hybrid needs explicit coverage of the routines actually executed. A patch application tool does not establish compatibility or turn baked-in changes into independent mod toggles.
- Keep authored code separate from generated output and maintain a runnable original/reference path. Decode meaningful assets/scripts/maps into editable formats while preserving timing, collision and references.
- Treat output resolution, filtering, replacement artwork, HD Mode 7, widescreen, presentation FPS, interpolation and sprite-limit removal as separate capabilities. Verify which are relevant to this game; do not assume it needs Mode 7 or that recompilation automatically unlocks smooth high-FPS motion.
- Widescreen needs scene-specific camera, map bounds, actor visibility, HUD, menus, single-target/full-screen effects, transitions and credits handling. Check both the original view and the new regions.
- Define target versions, dependencies/conflicts and save compatibility for mods. Serialize added deterministic state for replay/recovery. Protect owner progress before changing an installed game or reproducing a save issue.
- Owner ROMs, extracted original assets and personal saves stay local. Sharing software is separate from sharing those files.

## Best next step in the new chat

Start with a short confirmation of the game, current state and intended next step, then proceed with the bounded foundation assessment:

1. Read project instructions and the three documents. Inspect the prepared folder and establish the ROM's identity/layout without altering the original.
2. Look up current primary sources for this title: credible native/decomp/disassembly efforts, documented resource formats/editors and relevant QoL hacks. Use the supplied ecosystem references as candidates, not proof that they support this game. Keep the shortlist small.
3. If priorities would materially change the choice, ask one concise question about desired hacks/content/art direction while continuing independent investigation. Do not make routine research or reversible implementation depend on repeated permission requests.
4. Present a compact comparison, recommended foundation, major unknown and concrete initial proof. Explain whether a patched-ROM-first path actually saves work here. Identify shared runtime versus game-specific work honestly.
5. Proceed to a local playable proof with original gameplay, a transition and a representative demanding scene. Add one real gameplay edit, one import/edit path, one added content feature, one actual HD replacement, true widescreen, one representative selected hack feature and copied-checkpoint recovery as the foundation is established. Keep proofs incremental; an opening scene is not full-game compatibility.
6. Include a useful small state/replay or renderer-inspection tool early. Prove menu capture/edit/reload when changing UI. Record evidence per feature from the beginning so completeness does not require an enormous late audit.

This handoff is planning continuity, not a request to port every reference game, implement all proposed tools at once or reopen EarthBound development. The initial deliverable is a focused recommendation and a concrete local proof for Secret of the Stars.

## Where the references fit

The supporting documents carry the original links and pinned inspections:

- Matthew Stanley's `1379.tech` articles: shared recomp infrastructure plus decomp understanding; faithful reference behavior and separate enhancement rendering.
- RetroPortingToolKit `snesrecomp`, `recomp-ui`, `rbengine`, `recomp-net`: execution/hardware, settings UI, snapshots and optional networking respectively. Check actual contracts and title integration; single-player editing does not require netplay.
- Star Fox Enhanced, UrbanRecomp and MegaManX2Recomp: timing/render separation, meaningful extra scenery, and complete camera/visibility/effect handling.
- Lufia2SNESRecomp, Lufia2Decomp and snesrecomp-platform: reconstructed C behavior, explicit activation boundaries, shared presentation and editable menu-layout workflow. A separate public visual menu editor was not located in the inspected files.
- LakeSnes: emulator/hardware knowledge and reference behavior. Asar: assemble patch source. Lunar IPS: apply/create IPS changes. These have different roles; none alone supplies a moddable native port.

The reference-project work was selected documentation/source inspection, not gameplay certification. Refresh changing upstream contracts when selecting the foundation. Preserve the existing coverage limits rather than promoting a demo or metadata count into complete support.

## Continuation from the foundation assessment

The October 8 continuation read all three documents and began the focused assessment. Read [the foundation assessment](docs/FOUNDATION-ASSESSMENT-2026-10-08.md) for input identity, current primary sources, the provisional snesrecomp recommendation, Battle Info patch-first findings and the next local proof. The original ROM is unchanged; no playable build or patch has been prepared yet.

The owner subsequently directed Codex to choose routine priorities and use Zelda/EarthBound project files only as a last resort. Battle information is the selected first hack proof. Neither prior project was accessed in the assessment. These directions supplement the decisions above.

## Latest implementation continuation

Read [the first local foundation proof](docs/FOUNDATION-PROOF-2026-10-08.md) for the current state. A local hybrid Windows build reaches naming, controllable house movement, Sonya's required greeting and an outdoor transition. Its guarded checkpoint restores match an uninterrupted continuation, and corruption/foreign-schema controls reject safely. Most CPU execution remains interpreted; the experimental compiled routine and independent-reference timing/NPC differences still need qualification. Battle Info patching, reward edits, import/new content, HD art and true widescreen are outstanding.

The owner subsequently superseded the last-resort restriction: targeted reuse of EarthBound/Zelda tools, assets and guides is authorized when it speeds development. Only selected source/documents were read; neither project or installation was changed. MSU-1 is requested conditionally; no compatible Secret of the Stars/Aqutallion driver/pack has been verified. Keep original SPC audio available.

`Start Foundation Demo.cmd` prepares a separate local player profile and offers the early proof. Authored files are retained under `native/foundation`, shared edits under `patches/runtime-foundation.patch`, and all ROM-derived output/saves remain under ignored `local/`. The initial handoff and assessment's "not built" statements are historical snapshots.

## Desktop controls continuation

Controller support is an absolute requirement. The owner confirmed working video,
audio and basic controller input after the reported `0xc0000142` startup error,
then got stuck in rewind while trying F11/F12 for fullscreen. The demo now binds
F11/F12/Alt+Enter to fullscreen and F8 to rewind; Escape, Z, controller B and F8 again
close rewind. Player-two assignment is disabled for this single-player title.
The repaired executable/settings are installed with backups and both saves unchanged
by hash. Read the desktop repair section in the proof and
[the controls card](docs/FOUNDATION-CONTROLS.md). SDL virtual-pad movement/menu and
rewind-exit fixtures plus Windows fullscreen/audio/startup checks pass. The owner
has not yet confirmed the repaired mapping/exit behavior physically. The original
startup error was not reproduced and its loader cause remains unknown.
Resume the battle/content foundation gate next; retain all native-coverage and
reference-fidelity limits, HD/widescreen direction and conditional MSU-1 request.

## October 9 autonomous continuation

Read [the latest advancement](docs/FOUNDATION-ADVANCEMENT-2026-10-09.md) before
resuming work. The owner confirmed video/audio/controller operation, restart,
outdoor movement and combat, and authorized autonomous progress. The latest
installed build now starts at the normal title screen, fixes cold-resume audio
through checkpoint schema v2 with guarded v1 compatibility, and offers separately
selectable enhanced original pixels and a native enemy-HP panel. Original View
and explicit fixture-resume shortcuts are provided. Save files, original ROM
and existing key/controller settings remain unchanged by hash.

A copied natural battle replay, a narrow native damage edit and lossless indexed
tile export/edit/import have evidence. A separate source-assembled Battle Info
variant boots, but its full battle features are not qualified. The attempted
combined cold-boot battle route failed and is marked research. A wider compositor
preserves the center but exposes unloaded map columns, so widescreen stays off.
Actual HD replacements, added content, MSU-1, full native conversion, broad gameplay
and previous AOT/reference fidelity gaps remain open. Use the latest document's
receipts and next focused steps; do not repeat broad audits or owner campaign runs.

## October 9 UI and scrolling continuation

Newest continuation: [opening journal, CPU observation and field resources](docs/FOUNDATION-JOURNAL-CPU-2026-10-09.md).
Version 0.1.1 is installed with verified save/settings backups. The optional
opening lead card uses J/left-stick click and original restored David/stage state;
natural introduction, unrelated dialogue, copied cold restore and same-process
rollback checks pass. CPU telemetry distinguishes useful-work completion from the
NMI wait; 11 loading fields are a concrete next native-work target. Both Likado
layers reconstruct 3,584 center tile words exactly, establishing missing side
column and graphics identities. No CPU budget enhancement, live widescreen or
actual replacement HD art is installed. Read the newest receipt for current SHA
and bounded coverage. The earlier continuation below remains historical.

Read [menu/HUD/synchronized presentation and journal assessment](docs/FOUNDATION-UI-REPAIR-2026-10-09.md)
for the latest build, replacing the menu continuation below. Owner observed real
downward scrolling tearing during our Windows diagnostic. Software reported actual
VSync off despite its setting; synchronized Direct3D 11 is qualified on copied
fixtures. Original SNES CPU slowdown remains a separate investigation, explicitly
requested using Star Fox Enhanced as a reference. Owner authorizes focused agents.
The clipped submenu reproduces on the old build; interactive row batching is
excluded in the repair. H/right-stick click controls the optional enemy-HP display.
The first journal candidate is David's observed Crest of Stars/mountain clue;
completion and location flags are not yet verified and no journal is implemented.

## Message to paste into the new chat (original starter prompt)

Latest continuation: [native field-menu repair and UI interface evidence](docs/FOUNDATION-MENU-2026-10-09.md).
The owner reported slow menu opening/closing. Optional `FastMenus` is now installed
with backups: the checked opening drops from 21 to three guest frames, closing
from eight to one. Controller gameplay/overlay checks, a mid-menu cold checkpoint,
copied dialogue/battle regressions and Windows/audio checks pass. Saves, ROM and
existing bindings remain unchanged by hash. Read the continuation for the current
binary/receipts, 2bpp UI asset proof and next map-streaming work. Original View
retains original timing. Previous native/HD/widescreen/MSU/fidelity limits persist.


> Continue the prepared Secret of the Stars SNES project in `C:\Users\crono\Desktop\Projects\Secret of the Stars`. Read `HANDOFF-2026-10-08-Secret-of-the-Stars.md`, then both Markdown files under `docs\porting-references`. Treat them as a handoff and preserve the decisions. Briefly confirm the goal/current state/next step, flag genuine unknowns and begin the bounded foundation assessment. Evaluate patch-first QoL recompilation alongside editable native/decomp approaches. Work toward a native PC port with mods, added content, true widescreen, selectable enhanced pixel art and replacement HD artwork, using useful custom or existing tools. Protect my ROM and progress, keep scope/evidence clear, and use focused proofs rather than broad audits or another full owner playthrough.
