# Secret of the Stars: first authored HD menu-frame proof

The optional `HdMenuFrames` proof replaces eight original menu-frame tiles with
new authored curved edges and bevels at four times the original pixel density.
It passes the bounded copied-fixture gate on candidate 0.1.5. This establishes a
real high-resolution replacement interface for these frame tiles. It does not
establish replacement terrain, fonts, actors, or a complete HD port.

This document adds feature evidence to the October 9 continuation. Installation,
launcher defaults and the newest qualified executable remain the responsibility
of the latest continuation/build receipt; this checker changes none of them.

## Authored art and binding

`native/foundation/src/foundation_hd_ui.c` constructs eight 32×32 analytic frame
tiles. Quarter-pixel coverage and an inner bevel create new curves and palette
blends. The atlas contains authored weight geometry rather than copied original
pixels. The live original palette supplies navy, bevel and highlight colors.

The binding is deliberately narrow:

- Exact clean USA ROM identity and length, checked by SHA-256.
- BG3 tile IDs `A0..A7`, priority/palette word bits equal to `0x2000`.
- Exact current VRAM resource bytes `8A00..8A7F` equal to the local clean ROM
  source `05:8A00` (file offset `28A00`).
- Guest field state, BG mode register `9`, BG3 character word base `4000`,
  BG3 map word base `5000`, map register `51` (64 columns).
- Full brightness, no forced blank/mosaic/interlace, BG3 enabled; no BG3
  window/color-math, clipping or direct-color mode.

Each scanline observes current scroll, tilemap, tile flips and palette. It binds
only opaque original tile pixels whose actual raster RGB equals the expected
original BG3 color. A second RGB check after native HUD/journal composition
protects host foreground pixels. Transparent original tile holes retain the
existing picture. The proof writes only the composed host surface, never guest
VRAM, ROM, OAM or story state.

`HdMenuFrames=1` or `SNESRECOMP_FOUNDATION_HD_MENU_FRAMES=1` selects fourfold output
even when the resource guard refuses replacement. Fallback is the existing
EnhancedPixels 2× picture enlarged by nearest-neighbor to 4×, or the original 1×
picture enlarged to 4× when EnhancedPixels is off. HD off retains the existing
2×/1× contract. The prototype is optional and initially off.

The host presentation contract now accepts scale `1..4` and reserves fourfold
staging/frozen surfaces. An initial diagnostic candidate with the old twofold
host clamp crashed on the first fourfold frame. Its retained evidence is under
`local/runs/hd-menu-20261009-123806`; it is superseded by the passing candidate
below. A composed-surface check alone would not have caught that host allocation
error without launching the actual executable.

## Passing evidence

Checker: `tools/check_foundation_hd_ui.py`.

Final candidate report:
`local/runs/hd-menu-20261009-125025/report.json`.

- Executable SHA-256:
  `987554031d343fbc54e89b4fbc54e40058147aa6f26e75ee486391b4ff00c00e`.
- HD source SHA-256:
  `c59ab9fc2c89d34dac51222b69f91805cbe71a6528baef91f40529379e9a7418`.
- 78 feature checks and 58 cross-version parity checks passed (136 total).
  All 19 finite processes exited normally. The selected executable was frozen
  before running any pair.

The 0.1.5 candidate changes the framework's host compositor execution route to
cached composition. This checker compares it directly with the qualified 0.1.4
candidate under `local/runs/hd-menu-20261009-124105`, whose executable SHA-256 is
`661ae810501abc58225ad6cece3b4d7758f91a4709fc3a83aaf75a7944eb1dd4`.
All 770 guest dump files, 67 CPU/state/field/HD trace files and 499 composed BGRX
captures across the same 19 cases are byte-identical. The art source also retains
its hash. `--reference <prior-report-directory>` makes this exact cross-version
comparison repeatable. Host logs, elapsed times and executable bytes are
expected to differ and are excluded.

This result qualifies unchanged guest/output behavior on these fixtures. Root's
performance/audio/desktop measurements qualify whether the cached compositor
actually removes the reported skipping; this parity checker makes no frame-rate
or audio-quality claim.

The copied house and Likado routes cover field → opening menu → main menu →
STATUS → SORT cursor → returned menu → closing menu → field. Both the original
menu timing and the optional FastMenus path were paired. The comparison includes
all captured WRAM, VRAM, SRAM, OAM, CGRAM, guest framebuffer and register dumps,
plus every recorded CPU/state/field trace. HD on and off are byte-identical for
these guest observations. The original fixture files retain their hashes.

Independent stable BG3 resource masks contain every changed base pixel in the
main, STATUS and SORT captures, in both house and Likado. Slide/close frames are
also captured; their live bindings use the per-scanline observer rather than an
end-of-frame snapshot guess. Closed-field captures retain the nearest-expanded
existing picture.

At house main-menu frame 119, the new art changes 31,564 output pixels in 2,037
base-pixel blocks. It adds detail inside 2,128 nearest-expanded 2× pixel blocks
and produces 23 palette-blend colors absent from the enlarged existing picture.
These checks distinguish new high-resolution geometry from output scaling.

Likado's bounded 400-column terrain preview composes with the frame art at
1600×896. The house retains 1024×896. The wide terrain/actor/campaign limitations
of the separate widescreen proof still apply.

Visual inspection of the actual house and wide STATUS captures shows smooth
rounded frames, intact labels and no clipped STATUS/SORT window. Original font
and terrain pixels remain visible as such. Local comparison images:

- `local/runs/hd-menu-20261009-124105/hd-status-comparison.png`
- `local/runs/hd-menu-20261009-124105/hd-corner-detail.png`
- `local/runs/hd-menu-20261009-124105/town-on/captures/frame-250-1600x896.png`

## Fallback, restoration and refusal

The copied two-Red-Slime battle binds no frame art and is pixel-identical to
nearest expansion of the existing EnhancedPixels surface. A 600-frame cold boot
also binds no art and preserves all guest observations and the exact enlarged
surface. That cold boot is still black/full dim in both variants, matching older
`boot-clean` evidence. It does **not** qualify a visibly rendered title screen;
the report's `title_*` names identify this cold-start case. Visible-title fallback
must be covered by a separate known title fixture or the desktop gate.

A fresh private menu checkpoint restores in separate cold processes and binds
the current menu resource immediately. An actual within-process host save at
frame 80 and load at frame 390 rebinds the restored picture; HD on/off guest
dumps and CPU/state/field traces remain identical. Interactive rewind-timeline
selection was not newly exercised.

The native journal card remains pixel-identical inside its complete rectangle
while original menu borders underneath it are eligible. The module's second RGB
check prevents frame art from painting over native foreground.

An isolated harness compiles the actual HD module and SHA-256 implementation,
with private synthetic PPU memory. Its valid-resource control binds eight base
pixels. All 17 refusal controls bind zero: altered resource, wrong mode,
character base/map, disabled BG3, blank, dim, mosaic, interlace, BG3 window,
color math, clipping, direct color, title guest state, changed host foreground
RGB, wrong ROM hash, and out-of-range scanline. The wrong-ROM test alters a
private allocated buffer; no ROM file or gameplay checkpoint is changed.

## Limits and next use

This is the first bounded authored HD replacement, covering eight menu-frame
tiles. The tests do not certify every UI, party configuration, dialogue, battle,
fade or later chapter. Declining uncertain rendering contexts is intentional.
No additional physical-controller, audio-listening, display-scanout or campaign
claim follows from headless captures. The desktop/GPU preview and installed
receipt are separate gates owned by the continuation.

The owner's updated direction prioritizes attractive enhanced pixel art and
widescreen so the project can progress without a full replacement-art pack.
Further replacement artwork is deferred. This existing eight-frame proof stays
optional and off; its performance fix still matters for that preview and wider
host surfaces. Increasing output dimensions alone does not extend the HD
coverage recorded here.
