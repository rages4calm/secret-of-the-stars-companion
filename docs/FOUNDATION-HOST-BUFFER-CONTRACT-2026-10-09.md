# Host presentation and audio buffer contract - October 9, 2026

This focused review found no size overrun in the current title's 256/400 by 224
presentation and 1x/2x/4x output paths. Two allocation-failure defects in the
shared desktop host are reproduced separately: failed audio allocation reaches
a null write, and failed OpenGL growth loses its buffer while retaining capacity,
preventing a later same-size retry. Neither is evidence that the owner's running
session exhausted memory or that these defects caused the earlier visual report.

The baseline is the host source accompanying qualified native 0.1.8, whose release
receipt records executable SHA-256
`79b91e99c0645672da127feb087f390ff92e4039882fd789bbabdd69f8ee0a95`.
The repair discussed below is a separate private two-file candidate. This
document does not change installation status; a subsequent executable,
runtime-patch and installation receipt owns any promoted release claim.
No native/runtime source, owner profile, ROM, save or receipt was edited by this
review. Only this document, a new ROM-free checker and private evidence were added.

## Actual dimensions and ownership

`FoundationPresentationPrepare` chooses exactly width 256 or 400 and height 224.
The wide path holds a stable 400-pixel canvas during menus, fades, cutscenes and
unsupported resources; declined extensions leave the original centered picture
with side bars. Window and fullscreen drawable dimensions change the destination
viewport, not this title's logical framebuffer dimensions.

`PreparePpuFrame` in `desktop/host_main.c` bounds generic native field width to
`kPpuBufWidth=800` and height to 240, then binds the same static field allocation
with the active packed row pitch. The title's stronger 400-by-224 restriction
is required by its private wide scratch and upscale intermediates. The generic
800-pixel ceiling is not permission to widen this title further without revisiting
those capacities. In particular, the HD-plus-Enhanced intermediate would require
more space for an 800-pixel logical canvas.

| Buffer | Allocated capacity | Current largest use |
| --- | --- | --- |
| Host `g_my_pixels` field | 800 x 240 x 4 = 768,000 bytes | 400 x 224 x 4 = 358,400 bytes |
| Wide private `scratch` | 400 x 224 x 4 = 358,400 bytes | Same; observer lines are exactly 1 through 224 |
| Wide private VRAM `shadow` | 32,768 words = 65,536 bytes | Full copied VRAM, then private tileword edits |
| Presentation `logical` | 800 x 240 x 4 = 768,000 bytes | 400 x 224 x 4 = 358,400 bytes |
| Presentation `intermediate` | 800 x 480 x 4 = 1,536,000 bytes | 800 x 448 x 4 = 1,433,600 bytes |
| Enhanced original-center copy | 256 x 240 x 4 = 245,760 bytes | 256 x 224 x 4 = 229,376 bytes |
| Host staging and frozen frame, each | 4096 x 960 x 4 = 15,728,640 bytes | 1600 x 896 x 4 = 5,734,400 bytes |
| HD frame bindings | 224 x 256 entries, 8 bytes each | Same; only original center is bound |
| HD original-palette rows | 224 x 4 x 4 = 3,584 bytes | Same |
| HD authored weight atlas | 8 x 32 x 32 x 3 = 24,576 bytes | Same |

`FoundationPresentationScale` selects 4 when HD menu frames are enabled, otherwise
2 for EnhancedPixels, otherwise 1. EnhancedPixels alone writes Scale2x directly
to the supplied surface; HD alone repeats each logical pixel four times in each
axis; both first write Scale2x into the private 800-by-448 intermediate and repeat
that two times. HD menu replacement then writes only checked center bindings.
The original-center Scale2x override begins at output column 144 and writes 512
columns, within the wide 800-pixel 2x surface.

The host requests the renderer's scaled dimensions before composing. SDL streaming
texture dimensions are recreated when they change, and the texture supplies its
pitch. The compositor uses that pitch, including padding. Host staging uses the
packed output pitch and uploads one row at a time into the renderer pitch; frozen
copies likewise pack their rows. Both host arrays have explicit byte-capacity
checks. Presentation callbacks assume valid non-null buffers and sufficient pitch;
the host skips the callback when acquisition returns null. This is a caller
contract, not a public arbitrary-dimension rendering API.

`snes_beam_frame_driver_draw_ppu_frame_observed` invokes wide/HD observers only
after each original line 1..224 has been drawn. Private line copies therefore
stay inside the 400-by-224 scratch. Unsupported mosaic/interlace/layout states
decline side reconstruction. The separately fixed priority-buffer mosaic defect
is documented in [FOUNDATION-MOSAIC-REPAIR-2026-10-09.md](FOUNDATION-MOSAIC-REPAIR-2026-10-09.md);
this review neither reopens nor independently requalifies that renderer repair.

## Audio queue and restore contract

The DSP ring holds 8,192 stereo pairs, or 32,768 sample bytes. Producer/consumer
counters are unsigned 32-bit values; physical indices mask by 8191. A full ring
declines a new pair rather than writing beyond the buffer. Consumer advancement
clamps to available pairs. At 32,040 Hz the physical capacity is about 256 ms;
the normal priming target is 2,136 native pairs, about 67 ms. These are different
from the device callback block size.

The desktop host allocates one stereo mixer block:
`round(534 * obtained_frequency / 32040)` frames times four bytes. Requested
configuration rates are clamped to 11,025..48,000 Hz before opening the device.
The usual 32,040-Hz block is 534 frames / 2,136 bytes; 48,000 Hz is 800 frames /
3,200 bytes. Current SDL3 stream input is requested as signed-16 stereo. Its
additional-byte scratch grows with the library's positive `int` request, retains
the largest successful allocation, and leaves the old pointer/capacity intact on
`realloc` failure. A failed resize returns before filling or submitting bytes and
can retry later. This scratch is not another guest DSP ring.

PCM production and consumption share the APU mutex. `RtlRenderAudio` consumes
guest-produced samples without inventing guest SPC cycles. During paced realtime
guest execution, `RtlApuUnlock` yields when occupancy exceeds 4,096 pairs, releases
the mutex while waiting, and caps its wait at 250 ms. A stalled consumer disables
repeated waits until callback progress rearms them. Ring overflow still means
dropped audio, not a memory overrun; this policy cannot guarantee uninterrupted
sound under arbitrary host stalls, turbo or disabled audio.

Successful snapshot loads replace the DSP queue under the APU lock and reset
delivery interpolation/priming there. `FoundationStateApply` restores the saved
guest audio clock and CPU position, then calls `FoundationWideReset`. Terrain,
battle and actor lineage caches invalidate; actor reset also clears transient
DMA notification state. Host pointers/pitches are not serialized as PPU state;
`PreparePpuFrame` rebinds the static field before drawing. HD bindings are cleared
at the next raster begin rather than reused across a new simulated picture.

The host observes the state generation and calls `ResetAudioTimeline`, discarding
the remaining mixer-block tail, resetting priming, then clearing the SDL3 stream
outside the APU mutex. Modal save/rewind loops pause the device before guest
changes, clear the timeline before resuming, and reset frame blending so it never
mixes across a jump. Startup resume follows the same clear/reset path. This is a
source-level ordering review, not a concurrent-device stress test or a claim that
all restore/cutscene audio has been listened to.

The earlier ~134-ms synchronous forensic dump and its audible stall are separate
measured evidence in [FOUNDATION-MAP-RELEASE-2026-10-09.md](FOUNDATION-MAP-RELEASE-2026-10-09.md).
A stall that starves playback does not establish a framebuffer allocation fault.

## Reproduced failure paths and bounded repair

Baseline `host_main.c:3642` assigns the result of `calloc` without checking it.
The callback later writes that buffer in `FillAudioBuffer`. Injected allocator
failure in an isolated child reproduces access violation `0xC0000005`; it was not
an actual owner-process failure. Initial mixer cursors also begin null rather
than sharing a valid empty allocation boundary.

Baseline `opengl.c:363` commits the larger pixel capacity and frees the old
buffer before `malloc` succeeds. Failure leaves a null pointer with the new
capacity. The next same-size request does not retry; the host skips CPU composition
but still calls `EndDraw`, which performs a null OpenGL upload. The ROM-free
service spies reproduce both the lost retry and the upload. Baseline GL destroy
does not free this host allocation. The normal SDL/Direct3D path is separate:
texture recreation failure already calls the existing fatal reporter, and failed
texture locking returns null for the host to skip composition.

The root-owned private repair is narrowly appropriate:

- `AllocateAudioBuffer` validates positive obtained rate and stereo layout,
  widens frame arithmetic, checks byte bounds and allocation, and publishes all
  three cursors at the same valid base only on success. On startup refusal, close
  the still-paused stream/device, clear its handles, report failure and return 1,
  matching existing initialization-failure status. Do not unpause or enter the
  frame loop with an incomplete block. The existing early-init failure style
  returns to process exit; this is not a general startup-resource cleanup refactor.
- GL growth allocates first, retains the previous pointer/capacity on failure,
  and commits only a successful allocation. Clear draw dimensions and outputs
  before attempting a frame; reject invalid dimensions and byte/pitch arithmetic.
  A refused acquisition makes `EndDraw` return before any GL call or swap. The
  next same-size request retries. Free/reset the host allocation during destroy.

Private frozen repair source SHA-256:

- `host_main.c`: `b16f4ce73d133381b6a0f0d64d6865190ea1a89300b15470bbbc3665c0e62259`
- `opengl.c`: `4ac96b3503d69c3363eb4eddec1b7d83a001b91250920910fae0162f510111b0`

Baseline source SHA-256:

- `host_main.c`: `0cbcaa38ee6392fecbd8b374df315f1289f022173711e0b99d5f7f1d565def67`
- `opengl.c`: `ae9f2c9bef6af0d0eb148d06ac5b582cd2605681b392742ff31f9c85abd12461`

## ROM-free exact-function evidence

New authored [check_foundation_host_buffers.py](../tools/check_foundation_host_buffers.py)
extracts the actual production presentation, Scale2x, HD-frame draw, allocation,
GL begin/end/destroy, SDL3 callback and DSP-ring functions without editing them.
External SDL/GL services and unrelated overlays are stubs/spies. Inputs are
synthetic colors and metadata; no game, original asset, ROM, save or device is used.
Compilation enables UBSan traps; children set Windows error mode 3.

Frozen reports are
`local/evidence/host-buffer-contract-20261009/authored-original/report.json` and
`local/evidence/host-buffer-contract-20261009/authored-candidate/report.json`.
Both pass their expected original-control / repaired-candidate assertions:

- 48 alternating 400/256 width, Enhanced/HD and padded-pitch cases; 32,621,568
  flat-color output pixels and 22,020,096 seeded HD-binding pixels checked.
  Exact caller allocations end against a no-access page, with a leading guard
  page before alignment padding; output row padding remains unchanged.
- Candidate allocation refusal, nine valid audio rates, nine invalid audio
  layouts, seven invalid GL dimensions, null output arguments, old-allocation
  retention, same-size retry, zero GL calls after failed acquisition and
  destroy/reinitialize pass. SDL3 scratch resize refusal/retry passes both versions.
- Actual DSP ring write/read/restore/retire code checks 24,579 stereo pairs across
  three counter origins including unsigned wrap, three full-ring drops,
  negative/zero sample requests and clamped retirement. No trap or guard hit.
- All inspected source hashes remain unchanged; report files contain the full
  source hash inventory. Original failure reports and frozen controls remain local.

Run against current source, or a copied two-file override, into fresh private
evidence (the default output is automatically fresh):

```powershell
python tools/check_foundation_host_buffers.py
python tools/check_foundation_host_buffers.py --candidate-dir local/evidence/host-buffer-fix-20261009/src
```

These proofs establish bounded host memory and the tested allocator behavior.
They do not exercise actual GPU allocation failure, device disconnect races,
thread scheduling, physical controllers, audible campaign playback or every
cutscene. Fresh compiled-candidate integration, runtime-patch application and
release receipts remain necessary before promoting the private repair.
