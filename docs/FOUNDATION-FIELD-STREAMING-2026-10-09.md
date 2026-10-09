# Field streaming and a bounded widescreen resource contract

Current live implementation and installation are recorded in
`FOUNDATION-LIKADO-PREVIEW-2026-10-09.md`. This document preserves the earlier
read-only resource proof and its historical receipts.

October 9, 2026. Focused read-only inspection of the clean USA ROM and two
existing Likado captures. No executable, authored game source, ROM, checkpoint,
owner profile or previous receipt was changed. This adds concrete map/resource
identities to the latest UI continuation; it does not enable player widescreen,
claim replacement HD art or certify other maps.

## The producer behind the missing scenery

Original jump entries `01:B000`, `01:B003` and `01:B006` lead respectively to
the field streaming task `01:B015`, camera update `01:B071` and streaming
producer `01:B1D6`. These are semantic names inferred from the inspected code,
not newly traced dynamic hook coverage. The active path remains interpreted;
the generated `bank00_v2.c` covers the separate observed DMA routine, not these
bank-01 producers.

The task waits at `00:FF03` before updating camera and checking direction/state
at WRAM `0x0408`. Producer `B1D6` processes BG1 then BG2, with temporary direct
page offsets selecting camera pair `0x02AD/0x02AF` or `0x02B1/0x02B3`, map bases
`0x4800/0x5800` in VRAM words and three-byte resource-pointer records.
`01:D080` explicitly installs direct page `0x0B00` before calling `01:B006`
during initial field construction. Do not treat the producer's `$03`, `$15` or
`$29` as absolute WRAM offsets without its live direct-page contract.

| Site | Concrete operation |
| --- | --- |
| `01:B23E..B248` | Compares camera X masked with `0xF8` against last streamed position `0x051C`, per layer. |
| `01:B24B..B25C` | Requests `0x1E` (30) tile words vertically for a newly exposed column. Uses queued producer `B3A8`, or direct PPU producer `B4B8` while `0x0531` is negative. |
| `01:B262..B26C` | Compares masked camera Y with `0x051D`, per layer. |
| `01:B26F..B273` | Requests `0x22` (34) tile words horizontally through row producer `B2A2`. |
| `01:B59C..B63A` | Resolves the viewport edge, tilemap word address, and quadrant selectors from camera/direction. Direction offsets live at `01:B6F8..B703`. |
| `01:B65E..B6B6` | Resolves map segment and the 32-pixel cell within it; detects coordinates outside the map. |
| `01:B2A2..B3A7` | Builds horizontal contiguous queue records, splitting at a 32-column tilemap page boundary. |
| `01:B3A8..B4B7` | Builds vertical queue records, splitting at the 32-row wrap. |
| `01:B28F..B29E` | Terminates the queue and marks `0x02A0` ready. |
| `00:8120..816A` | Selects PPU increment mode from `0x02A0`, consumes count/address/tile-word records at WRAM `0x0100`, then clears the queue flag. |
| `01:D080..D106` | Initial construction streams 34 successive columns, temporarily walking camera X by eight pixels, then restores the original camera. |

The initial constructor and ongoing row width are both based on 34 columns.
Increasing only the final output width therefore reads beyond the populated
ring, precisely the failure already recorded in the advancement document.
Changing the constants alone is unsafe: queue capacity, edge offsets, initial
construction, page splits, wrap, alternate producers and asynchronous task
ownership would all require qualification.

## Camera and authored bounds

The captured PPU mode is Mode 1 with BG3 priority. BG1/BG2 use 64-by-32 tile
rings: BGxSC `0x49/0x59`, byte bases `0x9000/0xB000`, 512-by-256 sample periods.
These are caches, not the full world-map dimensions.

WRAM `0x046D/0x046E` supplies BG1 map dimensions in 256-pixel segments;
`0x046F/0x0470` supplies BG2 dimensions. The checked scene has 2-by-2 segments
for BG1 (512-by-512 world pixels) and 4-by-4 for BG2 (1024-by-1024). The loader
at `01:C4C8..C4D6` decodes primary dimensions from the two nibbles of one scene
byte; `01:C76D..C77B` does the equivalent for the secondary layer.

`01:B071` updates original scroll words using the fixed-point velocity/offset
records near `0x0459..0x046A` and `0x0471/0x0473`. If WRAM `0x0407` is nonzero,
it wraps out-of-range high bytes according to the per-layer dimensions. If it
is zero, this routine does not clamp every camera coordinate. The existing east
capture has signed camera X = -16, Y = 112; the later capture has X = 48,
Y = 176. The PPU's ten-bit X value 1008 is that negative original camera
coordinate masked for the tile ring, not a location 1008 pixels into Likado.

`B65E` detects map bounds before selecting the metatile; the checked out-of-map
result uses metatile ID zero. That word is `0x1F80` in this tileset. Preserve the
original map boundary pattern; do not invent new terrain beyond it.
Actor/camera-follow constraints elsewhere, special
scripted camera motion and other maps' wrap policies are not established here.

## ROM resource identities and exact capture comparison

Target ROM SHA-256 remains
`7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.
Both captures have scene selector WRAM `0x040E = 5`, wrapping disabled and
`0x0531 = 0`. Both attribute-pointer records are `09:8210`; all 256 entries in
that table lack the `0x0E/0x0F` conditional selectors inspected at `01:B704`.
That makes the simple resource lookup applicable across this checked scene's
map, rather than merely skipping a known conditional field cell.
The scene pointer selector is `01:C91D`, using the table at
`08:8000`; `C955/C960` consume its selected scene stream. Map selection itself
uses `09:9000` at `01:C4AF/C75A`. Conditional scene selection still needs its
own coverage; scene ID alone must not identify every possible asset variant.

| Resource | Checked identity and source |
| --- | --- |
| BG1 segment grid | WRAM `0x0513..0x0515 = 09:96A2`, entry 5 of `09:9000`. |
| BG2 segment grid | WRAM `0x0516..0x0518 = 09:9700`, entry 13 of `09:9000`. |
| Segment pointer table | `09:B000`, three bytes per 16-bit segment ID. |
| BG1 segment IDs | `0x013C..0x013F`, pointing to `0D:8F00/8F40/8F80/8FC0`. |
| BG2 segment in the captures | ID zero, pointing to `09:BF00`. |
| 32px-cell definitions | WRAM `0x0506..0x0508 = 0A:8818`, entry 2 of `0A:8000`; secondary layer shares it here. |
| 16px-metatile definitions | WRAM `0x0500..0x0502 = 03:8F58`, entry 2 of `03:8000`; secondary layer shares it here. |

The complete tile-word lookup inferred from these consumers is:

1. Select the 256-pixel segment: grid index `floor(y/256) * width + floor(x/256)`.
   Grid entries are little-endian 16-bit segment IDs.
2. Resolve the ID through `09:B000 + 3 * segment_id`. Its record contains an
   8-by-8 byte grid of 32-pixel cell IDs, index `((y >> 5) & 7) * 8 + ((x >> 5) & 7)`.
3. Select the 16px metatile byte at `cell_definitions + cell_id * 4 +
   ((y >> 4) & 1) * 2 + ((x >> 4) & 1)`.
4. Select the final 8px tile word at `metatile_definitions + metatile_id * 8 +
   ((y >> 3) & 1) * 4 + ((x >> 3) & 1) * 2`.
5. Retain the original word's tile number, palette, priority and flip bits.

Original producer `01:B704` can alter selected metatile IDs according to
attribute records and progression bits. It is called after resetting
`0x0520`, before the producer looks up tile words. Conditional terrain must
therefore join the resource contract rather than being inferred from a ROM
grid alone. The simpler lookup above is exactly supported in these captures;
it is not a claim that all game maps are unconditional.

A read-only Python reconstruction compared 32-by-28 visible tile words per
layer against the existing VRAM rings. All 3,584 words matched: two layers in
each of these two captures:

- `local/runs/likado-east-a/dump/east`.
- `local/runs/scroll-pacing-20261009-102819/walk-enhanced/dump/end`.

This checks the resource decode against original generated tile words, not
the compositor, host FPS, physical scanout or a new gameplay run. In the nine
new tile columns to the right of the original 256-pixel view, 224 of 252 words
per layer differ from the current ring in each capture. All 252 positions are
inside the corresponding authored map bounds. For example, at world (256,112),
BG1's decoded word is `0x1F73` while the current ring contains zero. The new
picture can be populated from actual map data; stretching or mirroring is
unnecessary. The left margin of the east capture is outside authored bounds;
it should preserve the original boundary policy.

Seven contiguous 4,096-byte graphics blocks in captured VRAM match ROM bytes
exactly, at both camera positions:

| VRAM byte range start | ROM source | SHA-256 of 4 KiB |
| --- | --- | --- |
| `0x0000` | `17:A000` | `d6954e4be30e94fc1725cbe352b45b9e95b045c264681b7cdb1000ec5d83b9b3` |
| `0x1000` | `17:8000` | `46ba62fedaa2da672a753d1fecdb4c6c5b280858fa0aaa47859835ad306e2360` |
| `0x2000` | `16:9000` | `6e3ae6f865dbf3e81b2114c8b0164d86d41281510b1a3f87790ebce86b31cb36` |
| `0x3000` | `15:C000` | `ee0465a4edb36fed33c7286147b59491452cec42dfe177f7a64d974abc2b82a4` |
| `0x4000` | `16:8000` | `ddf9ce7435e32742c5ad92941e590b936b8b9129f3434a62171f04f3a1ad0874` |
| `0x5000` | `15:A000` | `311c66a972224cf524c7db88482364e4be5d17168fbed9d0bd6981354aa9317c` |
| `0x6000` | `17:C000` | `b578f9586aa569f4d8d88f6307f987ebb728edbdbc2170bda97464ba4f8bd01e` |

The initial east capture's final block at VRAM `0x7000` matches ROM `17:B000`
(`1223e9d1775643596974c376a59788014126582be3fad64786c47e75aa9c493a`).
The later capture changes 560 bytes in tiles 992..1022. This is an observed
mutable resource, with animation dispatch untraced; do not assign its later
pixels the initial static block identity. The tool reports this separately as
`mutable-capture-unqualified`, with no usable static binding ID for that capture.

These are stronger identities than transient VRAM slot numbers. A first HD
binding can use target ROM identity, graphics source/block hash, 4bpp tile
offset within that block and expected palette/flip/priority contract. They
are byte-identical source matches; the complete graphics loader/animation
dispatch has not been traced, and no universal named art catalog is implied.
Original extracted artwork remains local.

## Reusable inspector and private evidence

`tools/inspect_foundation_field.py` now implements the checked resource lookup.
It accepts a copied dump prefix, the exact clean ROM and a fresh output folder
under ignored `local/`. It refuses another ROM hash, another scene/resource
contract, outputs outside `local/` and existing output directories. Camera must
be tile aligned for its explicit 32-by-28 center comparison. Nonaligned visible
footprints require a separate 33-by-29-cell comparison rather than silently
reusing the smaller count.

For example, use a new output name:

```powershell
python tools/inspect_foundation_field.py local/runs/likado-east-a/dump/east local/inputs/clean-usa.sfc local/assets/likado-field-new --export-cache
```

The report includes original tile-word comparisons, side-ring mismatches,
authored map bounds, segment/definition IDs, input hashes and graphics-source
matches. Optional caches are complete row-major little-endian uint16 maps for
both layers. They contain original derived tile words and remain private.
They are identical across both checked camera positions, as expected for these
unchanged scene records. The descriptor is a renderer integration foundation;
it has no live binding or new artwork.

Current final reports:

- `local/evidence/field-streaming-20261009/qualified-east/field-report.json`.
- `local/evidence/field-streaming-20261009/qualified-walk-end/field-report.json`.
- `local/evidence/field-streaming-20261009/qualification.json` records the total
  3,584 exact center comparisons, identical full-map cache checks, tool hash and
  the four guarded negative cases.

An initial extended-graphics diagnostic report is retained in `walk-end/`; it
failed a blanket all-eight-block static-source condition and led to the explicit
mutable-block classification above. The qualified reports supersede it. This
refinement preserves the discovered graphics uncertainty; it does not erase
the difference or promote animation behavior to verified.

## Smallest safe expanded-column proof

Use the same copied Likado scene and a game-owned, read-only tile-word resolver
for extra scenery. Preserve the original guest-produced center and add nine
columns on each side for the existing 400-pixel experiment. A renderer-owned
side cache can read the confirmed map records and current story conditions;
it must never write to guest VRAM, the shared queue, CPU state or progression.
This avoids disturbing the original producers and their field timing.

Initially guard exact ROM, scene selector 5, the two map-table pointers,
dimension bytes, definition pointers, non-wrapping policy and recognized
original PPU layout. Unknown resource/conditional-animation cases fall back
to the original 256-pixel view. Clear/rebuild the derived cache on reset,
restore and scene change; do not serialize a cache that can be reconstructed
from restored guest state. Retain BG3's centered menus and original battle
fallback. Do not widen actor activation or collisions merely because scenery
is now visible.

First compare the resolver's original-view words with the captured VRAM
contract, then verify extra columns against the same locations when ordinary
movement later brings them into the original viewport. Exercise horizontal
and vertical 8px streaming boundaries, the 256px segment boundary, a map edge,
menu close, copied cold restore and a natural transition with exact guest
on/off dumps. Only then consider an opt-in player preview for that scene.

Actor visibility/OAM culling outside 256 pixels, variable parallax, conditional
terrain changes, animated tiles, screen-bound effects and the first visible
transition frame remain separate gates. This proof is deliberately a small
correct additional-scenery contract, not whole-game widescreen.
