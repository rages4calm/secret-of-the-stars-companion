# Native 0.5.12 WIP — release sign-off and changes

This release publishes native update111/source140 with the unchanged Companion0.3.6 launcher. Setup builds the native game locally from your owned supported USA ROM. The download contains authored source, the launcher and license notices. ROMs, generated game code, extracted assets, saves, checkpoints and the native game executable remain local.

## Changes since 0.5.6

- Original save-point UI and SRAM-save production: the focused 1,151-frame comparison reduced 8,981 interpreter calls to zero in 0.5.7.
- Original Continue, Delete/cancel and empty-load handling: three comparisons reduced 1,470, 87 and 168 calls to zero in 0.5.8.
- New-game entry through original name entry: 12 calls reduced to zero over 249 frames in 0.5.9.
- Ordinary encounter and preemptive entry: 8 and 6 calls reduced to zero in 0.5.10. A separate original preemptive RUN/world-return check already had zero fallback and was not counted as conversion progress.
- Additional enemy combat paths: 65 original formations loaded all 94 targeted types lacking retained proof, with no crashes or setup refusals. Ten discovery cases exposed missing entries; five representative paced comparisons reduced 260 calls to zero in 0.5.11.
- Original battle SET message speed: increase, decrease and the original carry/threshold/borrow/zero-correction branches now run natively. Two 0.5.12 comparisons reduced 865 and 1,010 calls to zero over 743 and 429 frames. The second starts from the first action's checkpoint; these are separate finite comparisons, not independent campaign samples or a merged end-to-end route.

The changed-path comparisons preserve CPU/master clocks, all compared guest dumps and full native DSP audio. Checkpoints are compared byte-for-byte under a declared profile that permits only the source-proven host audio-consumer read counter and its validated derived CRC to differ. All game/hardware state, DSP production and audio-ring contents remain exact. Any failed raw comparison remains failed; a separate profile proof records the permitted host-only difference. No checkpoint bytes are rewritten and no passing gameplay cases are rerun to chase audio-thread timing.

The original ROM, game loaders/producers, input, rendering, audio and hardware ownership remain authoritative. Source-backed progression or party cheats were used on isolated copies when needed; these checks are staged evidence, not natural acquisition or a full campaign playthrough. Existing controls, guide/journal, maps, reward/travel options, enhanced pixels, Original View and guarded widescreen remain implemented.

## Native execution sign-off

Native execution is enabled by default. The final audit found no additional reproduced required gameplay fallback ready for conversion. Focused field-CONFIG, indexed shop/direct-transaction and inventory-full/refusal source checks found no concrete new missing path; these static results do not independently certify runtime coverage or every mode.

Normal operation still uses **automatic guarded interpreter fallback** when native execution cannot handle a path or source binding. Strict-native developer mode (`SNESRECOMP_NATIVE_ONLY=1`) stops on a missing native path instead. Therefore the interpreter is not developer-only in the normal package, and this release does not claim campaign-wide 100% native/AOT execution.

Historical strict-native/decoder-disabled tests retain their original binary and route scope. They are not relabelled as a new strict campaign test of 0.5.12. Instruction-key counts and the absence of a newly found gap are not completeness proof.

## Build and package boundary

The current source uses 98 ordered runtime patches, including 68 extensions. The original runtime/compiler/helper lineage, 13 architectural compiler pins and declared execution-state ABI are retained. The 0.5.12 local game binary has a separately preserved first `compiled_unqualified` receipt and exact-artifact execution qualification; qualification is not copied onto end-user builds.

The release source keeps the existing public provenance checks and complete source packager. Companion0.3.6 is reused from its byte-identical previously qualified donor. Release-package integrity and first-run checks are separate from gameplay qualification. Users need the tools listed in [BUILDING.md](../BUILDING.md) to compile the game locally.

Campaign/story feedback and broader controller/hardware reports continue as ordinary playtesting. Existing checks are reused; exhaustive campaign completion and repeated enemy sweeps are not release prerequisites.
