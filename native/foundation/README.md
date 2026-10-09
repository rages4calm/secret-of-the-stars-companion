# Authored foundation source snapshot

This directory retains game-owned host glue, the guarded execution-state adapter,
ROM identity, build configuration and progressive symbol decisions. No ROM bytes,
extracted assets, saves or generated CPU bodies are included.

The built working project is `../../local/native-proof/SecretOfTheStarsSNESRecomp`.
Its generated `src/gen` remains local. This is an authored-file snapshot of the
scaffolder result, not a complete standalone checkout of every scaffold utility.
Use the matching pinned runtime and the local build recipe in the proof document.
`../../patches/runtime-foundation.patch` records all shared-runtime edits against
`7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`.

`Observed_00816B` is experimental: its live entry was traced, but seven WRAM
bytes differ from the initial interpreter-led baseline. Keep the baseline binary
and evidence; do not promote this into a broad native-coverage claim. Checkpoints
are specific to this schema and pinned execution build, not portable campaign saves.

Current source is 0.2.0. Read
`../../docs/FOUNDATION-QOL-2026-10-09.md` for the guarded native reward and
ordinary-walking hooks and configurable input contract. The source-first build
helper freezes all 48 authored inputs and the runtime patch in an isolated
ignored build folder. Public Companion Setup builds/adopts those receipts
without private fixtures; compilation status remains explicit.

Read `../../docs/FOUNDATION-MAP-RELEASE-2026-10-09.md` and
`../../docs/FOUNDATION-MAP-WIDE-2026-10-09.md` for historical native 0.1.9 and
Companion 0.1.2 qualification, with exact hashes in the local receipts. Earlier actor and
Companion documents describe historical 0.1.6/0.1.1 checkpoints. The shared map
resource decoder, title panorama and checked battle layouts use a stable
400-pixel canvas; unsupported states have original centered pixels with side
bars. `foundation_wide_actors` follows ordinary party, regular and reserved actor producers and completed
OAM DMA packets into private margins, preserving the original center and guest
timing. Both wide flags default off. `foundation_state` v3 preserves the VRAM port cursor,
read buffer, increment and remap settings in addition to the v2 audio clock.
Guarded v1/v2 checkpoints remain accepted without rewriting their source files;
their absent port state cannot be reconstructed generally.
`foundation_presentation` owns the optional enemy-HP panel and scene width policy;
`foundation_scale2x` owns the independently selectable enhanced-pixel pass.
`foundation_diagnostics` writes opt-in scene/audio/enemy traces.
It also supports read-only per-field CPU-budget/wait observation.
`foundation_journal` derives the opening current lead from original restored
story state and draws an optional J/left-stick card without schema/guest writes.
`foundation_menu` implements optional field-menu batching through guarded
interpreter callbacks and the original PPU write ports. It finishes validated
BG3 row transfers/window slide loops without advancing extra guest frames.
Its context comes from the active guest stack, so mid-menu checkpoints and rewind
need no persistent native latch. Unsupported contexts retain the original wait.
Interactive submenu row producers retain their original frame handoff after
the clipping repair. H/right-stick click toggles the optional battle display.
The launcher uses synchronized Direct3D 11; guest CPU slowdown is assessed
separately in `../../docs/FOUNDATION-CPU-PERFORMANCE-2026-10-09.md`.
`foundation_rules` contains a diagnostic-only native damage proof at 00DC97;
ordinary player launch removes its environment switch. Original damage remains
the default. Its interpreter hook is not a contract for future compiled bodies:
an AOT replacement of that path must explicitly call the native modifier.

`foundation_field` resolves original standard full field maps; `foundation_wide`
renders terrain margins from private per-line PPU/VRAM copies while retaining
the original center and guest state. A separate launcher opens a copied fixture
in a new profile. Regular actors have separately qualified packet-bound margin
rendering; party/composite/effect actors and wrapping-world actors remain unqualified.
`foundation_battle_wide` binds qualified side layouts to exact original battle
tile maps and graphics, while retaining actual CGRAM and centered commands/enemies.
These extra layouts refer to original cells; they are newly authored scenery
extensions, not hidden original 400-pixel art. Full-campaign coverage is open.
Normal expansion stays off until selected. Neither enhanced pixels nor bounded
terrain/actor expansion implements actual HD replacement. `foundation_hd_ui`
adds independently optional authored 4x menu-frame artwork, bound to eight
live BG3 resources with per-line guards. It is not an HD world-art pack.
`foundation_column_lookup` adds default-off original-cost native map lookup;
the changed-cost clear/lookup policies remain diagnostic because they alter
live NPC movement timing. `foundation_loading` provides
an opt-in read-only loading observer. `foundation_clear` implements three native
instruction equivalents in the verified Likado VRAM clear, with original bus,
clock, audio and scheduler boundaries. `NativeClear=1` opts in; absent/0 remains
the original execution route. This proof does not reduce guest loading costs.
Read the native-loading continuation before changing loops or DMA timing.
Tile exports/imports belong under ignored `local/`; no original assets belong here.
