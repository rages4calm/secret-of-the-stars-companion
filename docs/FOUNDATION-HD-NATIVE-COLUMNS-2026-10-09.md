# HD menu-frame binding and native columns continuation

Historical version 0.1.4 continuation. It was installed after the initial
fixture/GPU checks, but the owner then reproduced choppy preview audio/gameplay.
Its steady-audio qualification was inadequate. Version 0.1.5 supersedes it:
see [cached presentation and steady audio](FOUNDATION-PRESENTATION-AUDIO-2026-10-09.md)
and the current `local/evidence/build-receipt.json` for the fixed artifact.

## What changes

`foundation_hd_ui` binds eight original BG3 frame resources (A0..A7) to new
authored 32x32 analytic art. Quarter-pixel curve coverage and an inner bevel
add actual finer detail to menu borders. This is a small UI art replacement,
not a world/sprite/portrait/font HD pack. It embeds no original resource pixels.
The clean owner ROM supplies the resource identity at 05:8A00. Per-line
observation checks the live characters, tilemap, palette, priority, windows,
brightness and scroll that produced the original raster. Unknown contexts
retain the normal picture. Original field/menu state and scheduling are not
changed by this art pass.

`HdMenuFrames=1` selects a 4x presentation surface. World and text retain the
existing enhanced-pixel pass (if enabled), enlarged to that surface. The
original view explicitly disables the replacement and both native loading
options for that launch. Existing owner preferences are preserved; missing
HdMenuFrames means off. New profiles list the optional setting at zero.

`Start HD Menu Preview.cmd` opens a separate fresh profile with a copied house
fixture and copied controller/display preferences. Open the field menu using
the controller's east/B button. The preview does not run the owner's current
save or mutate that profile. Normal launch still starts at the title.

`foundation_column_lookup` adds a bounded native equivalent of the straight
lookup seam at 01B4F3..01B50B. `NativeColumns=1` enables original-cost execution;
missing/0 stays off. Exact clean-ROM, stack, task, direct-page resource, scene,
forced-blank and VRAM port checks precede replacements. Each instruction
commits through the shared bus/clock bridge, with original scheduler boundaries.
Original port stores, attribute helpers, split points and cooperative waits
remain in their original paths. Details and continuation proof are in
[the column assessment](FOUNDATION-LOADING-COLUMNS-2026-10-09.md).

## Timing experiments and reference

[Mega Man X source](FOUNDATION-MEGAMANX-REFERENCE-2026-10-09.md) helped separate
native CPU execution, guest cycle accounting and host raster performance.
[Clear timing experiments](FOUNDATION-CLEAR-SPEED-2026-10-09.md) and native
lookup together save one field in the tested house exit. They also alter a
live NPC direction accumulator and subsequent movement. Changed-cost policies
remain explicit diagnostics, stripped from ordinary player launches; they
are not promoted as behavior-identical performance fixes.

[Actual sprite-cap controls](FOUNDATION-SPRITE-LIMITS-2026-10-09.md) prove that
NoSpriteLimits removes scanline sprite/sliver caps. Sampled natural scenes
remain below those caps, so no scrolling or battle improvement is claimed.
The normal setting stays zero. The separate HLE host-composition experiment
has only a bounded original-cost loading/checkpoint pass; it is not installed.

## Preserved decisions and outstanding work

Subsequent owner steering prioritizes enhanced pixel art/upscaling and true
widescreen like the EarthBound/Zelda projects. A full replacement HD art pack
is deferred. The owner also reported choppy sound/gameplay in this 0.1.4 HD
preview; the initial GPU gate checked early PCM but failed to require steady
frame service and audio underflow counters. Do not use that gate as evidence
of smooth playback. The cached host-composition fix is a later continuation.

Checkpoint v3, guarded v1/v2 acceptance, original audio, fast outer menus,
interactive submenu repair, controller/HUD controls, opening journal and the
separate Likado terrain preview remain available. HD menu frames do not change
the save schema. The journal still covers one verified opening lead. Most
CPU execution remains interpreted. This is not complete static recompilation.

True actor/campaign widescreen, world/sprite HD art, further verified quests,
general slowdown fixes and a compatible MSU-1 title driver/track pack remain
outstanding. Original view and unchanged-cost fallback remain available.
Focused tests use copied fixtures; new physical-controller, listening,
monitor-scanout and campaign certification are not implied by those checks.
