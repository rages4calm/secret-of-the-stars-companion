# Original variable effects in widescreen — native 0.4.4

Native 0.4.4 extends the wider view to a bounded family of the original field
effects. Companion remains 0.3.6. The story guide, guide-town tracking, map,
battle panel and existing ordinary party/NPC/vehicle paths remain available.

## What changed

The host now observes pieces resolved by the original special-effect drawing
routine before horizontal culling. It carries their position, size, tile and
ordering through the original completed sprite packet and display transfer.
Compatible effects can occupy the additional side scenery instead of making
that entire scene fall back solely because its special layer is active.

The original routine still interprets its own effect descriptors. The host
does not introduce a second descriptor interpreter, spawn actors or advance
events. It decodes current VRAM and palette data for the additional pixels.
The original 256-pixel center, collision, activation and game pace are retained.

Effects keep their original order ahead of ordinary appended party/NPC pieces;
reserved sprites retain their earlier order. Eight- and sixteen-pixel objects,
whole-object flips, palette selection and tile-row wrapping use the actual
displayed resources. Restore and scene changes discard the transient capture.

## Coverage and fallback

The new route requires the existing selected-map, ordinary roster, OBJ layout,
full 544-byte packet, DMA and raster contracts. It preserves signed native
coordinates for pieces that the original emits. Additional right-side pieces
are admitted only when their original resolved anchor lies in the original
viewport and their resolved position lies in the adjacent margin.

Nonzero sprite offsets, ambiguous packed anchors, incompatible layouts and
other unsupported contexts retain the original view. The host bounds capture
to 4,096 visits, 256 retained pieces and 112 actually emitted prefix pieces.
Any capture, capacity or packet mismatch rejects that new epoch. Previously
supported large/world/vehicle routes retain their separate contracts.

Added margin pixels use the existing extra-object compositor. They do not
consume the original SNES sprite/sliver limits; the original center and guest
overflow behavior are preserved. This is a rendering implementation with
explicit limits, not a claim that every campaign effect is covered.

## Focused checks

The actual actor C and PPU compositor pass resolved-piece, prefix/padding,
ordering, flip/size, per-line resource and reset controls, including a separate
undefined-behavior-sanitizer run. A finite staged original-producer engine
check is separate from those synthetic controls and from natural progression.
Guide, battle and ordinary-world captures render with this executable. A
separate paced Direct3D11/audio route runs near 60 FPS without recurring
underflow, missing-frame or audible-overflow counter errors in its checked
post-startup window.

The owner and play testers verify campaign behavior and directions. Developer
work checks implementation, compilation, focused rendering/input and reported
failures; exhaustive campaign replay is not a release gate.

- Native executable SHA-256: `596e7f952d2051ceca5830227c0660783cff1bfe57a73b1d04eae511a05ea679`.
- Immutable compilation receipt SHA-256: `edf345e745208a96deeea4b5e68d1fd78b39c88803b87a1da58255a57c55b138`.
- Sixty-two authored native inputs; thirteen runtime patches unchanged.
- Companion 0.3.6 and the declared execution-state ABI are unchanged.

Compilation receipts retain their genuine compiled_unqualified status.
Installation qualification is a separate report. Full native/AOT execution,
unsupported rendering contexts and broader hardware coverage remain WIP.
The downloadable package contains the ROM-free launcher and authored source;
the native game is built locally using an owned clean USA ROM.
