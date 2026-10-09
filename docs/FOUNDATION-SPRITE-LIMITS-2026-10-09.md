# Secret of the Stars: scanline sprite-limit qualification

October 9, 2026. The existing runtime has a real selectable scanline-limit
enhancement. Its private PPU controls pass, and paired copied town, house,
David-dialogue and two-Red-Slime battle replays remain identical with the option
off/on. This does not demonstrate removal of this game's CPU slowdown or expand
its actor allocation. No owner progress, installed settings or game source was
changed by this assessment.

## Actual runtime behavior

In the pinned runtime's `runner/src/snes/ppu.c`, `ppu_runLine` evaluates
sprites at line 839 before choosing the original/reference or span renderer
at line 841. Both renderer paths therefore use the same sprite evaluator.
The original renderer does not automatically bypass the limits.

`ppu_evaluateSprites` scans 128 original OAM entries and uses
`foundSprites[128]`. Without `kPpuRenderFlags_NoSpriteLimits`, it stops accepting
sprites after 32 on a scanline (line 2855), and stops tile fetching after
34 eight-pixel slivers (lines 2895 and 2978). The flag bypasses both caps.
The original OAM remains 512 bytes plus its 32-byte high-bit table.

The host maps `[Graphics] NoSpriteLimits` onto that rendering flag during
frame preparation. `NewRenderer` selects the composition implementation; it
is independent of the sprite-limit option. Either renderer can use:

```ini
[Graphics]
NoSpriteLimits=1
```

Use `NoSpriteLimits=0` to retain the hardware scanline caps. This document
does not change launcher defaults or claim a new settings UI.

The flag also affects original PPU overflow status. Capped rejection sets
`rangeOver` or `timeOver`; `ppu_read(..., 0x3E)` exposes them as bits 6/7
of STAT77. They reset on the pre-render line. When a synthetic scene exceeds
the caps, enabling the option prevents those overflow events as well as
allowing additional OBJ pixels. It is consequently unsafe to promise universal
guest-state invariance without testing a title's status-register consumers.

## Meaningful synthetic controls

`tools/check_foundation_sprite_limits.py` includes the actual runtime `ppu.c`
in a private heap-allocated PPU harness. It also links actual `ppu_legacy.c`
and `ws_shadow.c` support; it does not substitute a reimplementation of the
sprite evaluator. The harness never binds the running game's PPU, ROM or saves.
Its opaque tile data and OAM placements are synthetic test inputs.

It evaluates each control with both `NewRenderer` flags and both limit flags:

| Control | Opaque OBJ-row pixels, capped → uncapped | STAT77, capped → uncapped |
| --- | --- | --- |
| 33 small sprites, distinct witness in slot 32 | 8 → 16 | `0x41` → `0x01` |
| 18 large sprites / 36 slivers, distinct witness in first slot | 16 → 32 | `0x81` → `0x01` |
| All 128 original OAM slots, distinct witness in slot 127 | 16 → 32 | `0xC1` → `0x01` |

The sliver control deliberately puts its distinct witness in the first OAM
slot: original fetching traverses accepted sprites in reverse order. This
checks actual rejection rather than using a placement which remains visible
despite the cap. Pixel counts measure the actual OBJ priority buffer, rather
than claiming a full game framebuffer or a natural crowd was rendered.

The 128-slot control proves the last original slot can be consumed with the
caps lifted. Array sizes and the original 128-iteration scan remain unchanged;
this does not add a 129th original OAM entry.

## Copied gameplay comparisons

Both original-renderer and span-renderer suites passed on diagnostic executable
SHA256 `62968de30e73a22956db8c61e24edb0910c03eae7c20e779ce2a48c81d749afe`.
Within each renderer, capped and uncapped runs match all captured WRAM, SRAM,
VRAM, OAM, CGRAM, guest framebuffer and PPU register dumps. Their per-frame
state, CPU-budget and existing field traces are identical. These comparisons
do not claim the two renderer implementations match each other universally.

| Natural fixture | Capture points | Captured maximum sprites / slivers |
| --- | --- | --- |
| Likado movement | 2 | 2 / 2 |
| House field/menu | 3 | 2 / 2 |
| Initial David dialogue | 20 | 4 / 4 |
| Two-Red-Slime battle/actions | 13 | 6 / 7 |

Density is derived from the captured OAM at these points. It does not observe
every intervening scanline-time OAM change. All these captured densities are
below the caps; the unchanged framebuffer is therefore a useful regression
result, not evidence that a visible crowded scene improved.

Each run uses a dedicated checkpoint copy and disables audio, autosave and
gamepads. Source checkpoint hashes remain unchanged. This adds no physical
controller, audio, display or campaign certification.

## Actor expansion and performance remain separate

The runtime also exposes `PpuSetExtraObjects(ppu, objects, size_t count)` for
additional host-owned presentation objects with normal priority, windows,
brightness and color math. That list can exceed original OAM capacity while
preserving the 128 original slots. A title must provide those objects and
reconstruct them after restore; no Secret of the Stars actor producer has
been implemented here.

Scanline-cap removal cannot make the game create actors that its own allocator
or visibility logic omitted. It also does not grant the original game more CPU
cycles, remove intentional animation waits or fix presentation sync. Those need
their respective title-specific measurements and changes. No CPU-speed or
slowdown benefit is claimed from this option.

## Receipts and repeatability

- Original renderer: `local/runs/sprite-limits-20261009-122344/report.json`.
- Span renderer: `local/runs/sprite-limits-20261009-122242/report.json`.
- Each directory preserves the private harness, compile log, synthetic results
  and copied gameplay captures/traces.

```powershell
python tools/check_foundation_sprite_limits.py --exe local/native-proof/SecretOfTheStarsSNESRecomp/build-menu/SecretOfTheStarsSNESRecomp.exe --renderer 0
python tools/check_foundation_sprite_limits.py --exe local/native-proof/SecretOfTheStarsSNESRecomp/build-menu/SecretOfTheStarsSNESRecomp.exe --renderer 1
```

The checker freezes the selected executable into a new private directory before
running its pairs. It compiles only its standalone PPU control, never a
production title build. The historical first diagnostic had incorrect synthetic
witness placement/expected combined overflow and is superseded by the passing
receipts above; actual natural regressions passed in that diagnostic too.
