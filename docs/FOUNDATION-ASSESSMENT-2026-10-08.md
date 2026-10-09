# Secret of the Stars foundation assessment

October 8, 2026. Continue with a **provisional snesrecomp foundation plus game-specific understanding**, using the clean USA ROM as the reference input. Evaluate the source-available Battle Info hack as a separate patched input before deciding whether its behavior should become a native toggle. No playable game foundation has been qualified yet.

This document records the initial pre-build assessment. The later [local foundation proof](FOUNDATION-PROOF-2026-10-08.md) supersedes its build/gameplay/recovery status and records remaining comparison gaps.

The owner delegates routine choices to Codex. Zelda and EarthBound project files are last-resort references; neither project was accessed for this assessment. The original handoff and both planning snapshots remain the governing design decisions.

Later owner steering permits targeted Zelda/EarthBound reuse to speed development and requests optional MSU-1 if a compatible title driver/pack is found. See the proof document for the bounded reuse checks and soundtrack search.

## Verified input

| Property | Result |
|---|---|
| File | `Tecmo Secret of the Stars (USA).sfc` |
| Size | 1,572,864 bytes, 1.5 MiB, without a copier header |
| Header | `SECRET OF THE STARS`, USA region, revision byte 0 |
| Mapping | Standard LoROM, map byte `0x20`, SlowROM |
| Cartridge | Type `0x02`, ROM with battery-backed RAM; no enhancement chip indicated |
| SRAM | 8 KiB indicated by the header |
| Header ROM capacity | 2 MiB; this is different from the actual 1.5 MiB file size |
| CRC32 | `EF968ED1` |
| SHA-1 | `958a0a835e2e39f382cb37a99098a3cdd4812cf7` |
| SHA-256 | `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600` |
| Checksum | Stored and computed mirrored checksum both `0x1157`; complement `0xEEA8` |
| Entry vectors | Reset `$00:8000`, native NMI `$00:80E6` |

File size, CRC32, MD5 and SHA-1 match the USA entry in the [libretro No-Intro catalog](https://github.com/libretro/libretro-database/blob/bf825e3ec48d43557ad024da6a7b93e512043525/metadat/no-intro/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System.dat). The pinned entry is retained in [catalog-match.json](../research/2026-10-08/catalog-match.json). The original SHA-256 remained unchanged after inspection. No ROM patching, game execution or asset extraction occurred. No save files were observed in this project's initial file inventory; other save locations were not searched.

The upstream ROM probe checks the checksum/complement pair, rather than computing the image checksum. Its standalone fallback also assumes LoROM when its mapping module is absent. Our [input inspector](../tools/inspect_foundation.py) independently checks the exact known image and computes its mirrored checksum; the two reports should not be treated as equivalent integrity checks.

## Foundation comparison

The assessment covers three routes, with only one actionable runtime candidate identified.

| Route | Evidence and fit | Largest missing piece | Decision |
|---|---|---|---|
| Existing editable native port | No credible title-specific implementation found in the bounded title and Aqutallion searches. `danzinho007/SecretOfTheStars` contains README, link-list and repository metadata files, without game implementation. | A real implementation, build and content interface. | No usable candidate established. |
| Title-specific decompilation or disassembly | No full game decompilation or disassembly established. Battle Info assembly supplies six hook sites and partial battle state knowledge. | Gameplay routines, event/map formats, graphics identity and verified resource import. | Use the partial knowledge alongside a runtime; it cannot run the game independently. |
| Shared snesrecomp runtime | Standard LoROM is supported. Current source provides a beam-aligned frame driver, progressive symbols, native routine replacements, desktop host and data-mod packages. | Qualification of this title and game-owned content/render adapters. | Leading candidate for the first playable proof. |

The discovery checks used public GitHub repository searches for the full title, `SecretOfTheStars` and `Aqutallion`, plus web searches for native/decomp/disassembly/editor and hack resources. This is a bounded discovery result, not proof that no private, unindexed or differently named project exists. No working game-specific resource editor or map/script specification was established.

Pin [snesrecomp](https://github.com/RetroPortingToolKit/snesrecomp/tree/7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0) at `7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`. It is the same revision recorded in the planning snapshot and was still the queried `main` revision. Its compatibility table describes mapping support, not Secret of the Stars qualification.

The [scaffolder](https://github.com/RetroPortingToolKit/snesrecomp/blob/7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0/tools/new_project/README.md) and selected host templates are cached locally. Do not turn a successful scaffold or interpreter-led boot into a claim of native CPU coverage. Record generated/native versus interpreted execution in the chosen test scenes. Preserve the timing driver until evidence requires a title-specific change.

The pinned runtime's [license](https://github.com/RetroPortingToolKit/snesrecomp/blob/7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0/LICENSE) is PolyForm Noncommercial 1.0.0. Preserve its notices and account for that restriction in any eventual distribution plan. The Battle Info tree contains no license file; public source availability alone does not establish redistribution terms.

## Patch first assessment

Choose [BlueImp78's Battle Info hack](https://github.com/BlueImp78/Secret-of-The-Stars-Battle-Info-Hack/tree/650721747fd808daeb4e2a9745f16150b2d00c91) as the first representative hack. Its README describes enemy HP, XP/gold, drops and turn/damage displays, with X cycling views. It also lists minor graphics glitches before battles and inaccurate HP display above 9999. These are upstream claims awaiting our own tests.

The pinned source at `650721747fd808daeb4e2a9745f16150b2d00c91` provides concrete integration leads:

- Six assembly hook sites: `$00:8366`, `$02:9122`, `$00:84A0`, `$00:DCA4`, `$00:DCAB`, `$1C:8069`. These are hook locations, not automatically safe native function-entry addresses.
- Enemy slots start at WRAM `$7E:6100`, with source logic advancing by `0x1C` across four slots. It reads current/max HP at offsets `+1` and `+3`. Validate those observations in live battles before naming them confirmed game interfaces.
- New code starts at `$B2:8000`, standard LoROM file offset `0x190000`. That is beyond the clean image's `0x180000` end. Patch preparation must measure the actual expanded image, padding, checksum and mapping behavior.
- New scratch state includes `$1F00` onward and a damage array at `$3000`. Exact occupied ranges and collisions with original game state need checking; copied snapshots must include this state.
- Reward/drop information is also copied into the hack's `data.asm` table. A later reward or enemy edit could leave the display stale unless we update that table or replace it with a live native data adapter.

The source uses Asar syntax and has no complete source-build recipe or exact base hash in its README. **Patch-first is credible but its net saving is unproved.** Build one private working image, inventory every changed span and its resulting identity, and compare an ordinary battle and an action phase against a faithful patched reference. Keep this branch separate from the clean baseline.

Do not use the hook names as native replacements without instruction boundaries and calling contracts. [The runtime replacement contract](https://github.com/RetroPortingToolKit/snesrecomp/blob/7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0/docs/HLE_FUNC.md) has specific interpreter entry limitations: interpreted jumps/fall-through and excluded bounce targets can still execute ROM instructions. A patch baked into a compiled input will initially be a build variant; an independent toggle needs explicit game-owned activation.

An Easy Type hack appeared in secondary search results, but no primary source or verified patch recipe was established. It is not selected as our baseline. No additional hack stack is proposed.

## Shared support and game owned work

Reuse CPU/hardware support, desktop window/input/audio, frame scheduling and existing snapshot plumbing where the proof validates them. Keep authored game interfaces and tools separate from generated output. Start single-player with networking disabled.

Game-owned work includes named state, reward and movement rules, map/script/asset decoding and import, added-content execution, scene-aware widescreen, HD replacements and menu layout editing. Runtime [mod packages](https://github.com/RetroPortingToolKit/snesrecomp/blob/7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0/docs/MOD_PACKAGES.md) contain data and activate trusted code already linked into the game. They do not supply these game interfaces automatically.

Choose a faithful high-resolution 2D redraw direction initially, preserving readable silhouettes, palette relationships, animation timing and anchors. Keep enhanced original pixel art independently selectable. Start artwork work with one identified battle sprite once its frames and ownership are understood; one replacement will establish the path, not full art coverage. No art pack has been produced or imported.

True widescreen must draw decoded world data into additional space. The first scene adapter must preserve the original rectangle and check camera edges, actors, events, HUD and transition history in the new margins. Battle and menu policies are separate. Mode 7 usage has not been established for this game; do not make it an early dependency or advertise it.

The largest technical unknown is access to meaningful map, script and asset identities. A runnable hardware path could still leave substantial content and renderer work. Establish a working import and new-content path before committing to a large conversion.

## Concrete first proof

The next implementation step is a local clean-input host pinned to the runtime above, with generated code stored locally and a separate data directory for fixture saves. Use the existing project scaffolder in an isolated `native-proof/` directory, one player, no netplay, no GitHub creation, no publication and no automatic art download. Inspect its flags and pinned dependencies before running it.

1. Reach ordinary controllable gameplay naturally. Capture one outdoor/indoor transition and a multi-enemy battle through menu selection, damage and reward completion. Record input events, frame counts, native/interpreted coverage, state hashes and screenshots; qualify only these scenes.
2. Add a small battle-state inspector using live-validated enemy slot data. Capture a checkpoint in the fixture directory, restore it in a fresh process and replay identical input twice. Check SRAM and hardware/custom state, rather than host pointers.
3. Prepare the Battle Info source on a private copy. Record assembler revision, ordered preparation, source hashes, patch spans and resulting ROM hash. Compare its display and restored state against the intended patched reference, including the author's listed glitches. No patch was applied during this assessment.
4. Make one adjustable native XP-reward rule with the original value as default and a 2x setting used only in fixtures. Verify the consumer, displayed reward, actual XP gain, disabling and restart. This is a bounded behavior proof, not a decision to rebalance the campaign.
5. Decode one real asset or dialogue record and complete an edit/import round trip. Then load one genuinely new external record with a real game consumer, one actual HD sprite and one decoded widescreen scene. Include a menu capture/edit/reload round trip when UI changes begin.

Gate further adaptation on these incremental results. Do not make an opening boot, framebuffer stretching or unused external file count as completion. Reassess the foundation if its content or rendering seams require an unreasonable rewrite. Owner full playthroughs and broad agent reviews are not part of these proofs.

## Feature evidence

| Requirement | Current status | Next evidence |
|---|---|---|
| Protected known input | Verified; original unchanged | Recheck before copying and after each experiment |
| Native executable and gameplay | Not built | Gameplay, transition, battle and execution-path report |
| Real gameplay rule edit | Planned XP fixture | Actual reward consumer and enable/disable comparison |
| Content edit and import | Format unknown | One visible edit round trip |
| Added native content | Not implemented | External record loaded and used by game logic |
| Replacement HD art | Direction chosen; not implemented | Real detailed asset, frames, placement, toggle and cold restore |
| Enhanced original pixel art | Required; not implemented | Fullscreen proportions and sharp/smooth choices |
| True widescreen | Game map adapter unknown | Added scenery, scene edges, actors/effects and transition |
| Representative hack | Source inspected; no patch built | Battle Info reference comparison and execution coverage |
| Timing, input and audio | Not measured | Separate update/presentation rates and battle/audio check |
| Save recovery and replay | No runtime fixture yet | Fresh-process restore and repeated state comparison |
| Practical inspector | ROM preflight implemented | Live named battle state and injected-error detection |
| Menu editing | Not implemented | Capture, edit, validate and reload a real menu |
| Mod compatibility | Contract understood; no game integration | Exact targets, activation, conflicts and save policy |

## Local evidence and rerun

Run from the project root:

```powershell
python tools\inspect_foundation.py 'Tecmo Secret of the Stars (USA).sfc' --report local\evidence\foundation-preflight.json
```

The inspector verifies the supported hash, header and computed mirrored checksum, then reports source-derived hook locations. A changed input is rejected before game-specific interpretation. It accepts the same normalized image with a copier header. Its report path cannot be the ROM or a non-JSON filename. Focused checks passed for copier-header normalization, one-byte corruption rejection, ROM report-overwrite rejection and preservation of the original.

Metadata evidence is in `local/evidence/foundation-preflight.json` and `local/evidence/rom-probe-upstream.json`. Selected upstream source files and their hashes are pinned by [sources.json](../research/2026-10-08/sources.json). Cached source is inspection evidence, not an installed runtime or a game build. Source/metadata were inspected within the scope above; no full-source or campaign audit was performed.
