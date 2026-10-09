/* Explicitly authored battle edge joins using this title's original cells.
 * This extends presentation, not the guest battle map, actors or CPU budget.
 * Original battle art is 256x256: the extra layout is not hidden scenery.
 * Sixteen checked original-tile recipes; unique motifs stay in the center. */
#include "foundation_battle_wide.h"
#include "common_rtl.h"
#include "sha256.h"
#include "snes/cart.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include <stddef.h>
#include <string.h>

extern Snes *g_snes;
enum { kImageBytes = 1572864, kMapBase = 0x5800, kColumns = 32 };
static const uint8_t clean_hash[32] = {
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00
};
static const uint8_t *bound_rom;
static size_t bound_size;
static int identity;
enum { kBackdrops = 16, kSupported = 0xffff };
static uint16_t original[kBackdrops][32 * 32], sides[kBackdrops][2][9 * 32];
static unsigned graphics[kBackdrops][4], used_graphics[kBackdrops];

/* These are NEW side layouts referring to original 32px cell identities.
 * The opposing edge-tree halves meet across each original viewport boundary;
 * canopy and ground continue the original two-cell/one-cell rhythms. The
 * left 96px column group is cropped from x24, the right group at x72. */
/* Bit8 reflects one32px source cell horizontally. This extends local
 * contours at cloud/cliff edges, never mirrors the complete battle image. */
static const uint16_t edge_cells[kBackdrops][2][8][3] = {
    [0] = {{{1,0,1},{3,2,3},{5,4,5},{7,8,9},{11,11,12},{13,13,13},{13,13,13},{13,13,13}},
        {{0,1,0},{2,3,2},{4,5,4},{6,7,8},{10,11,11},{13,13,13},{13,13,13},{13,13,13}}},
    [1] = {{{258,257,256},{265,264,290},{293,292,291},{43,44,45},{30,48,49},{32,32,52},{33,33,54},{32,32,32}},
        {{262,261,260},{268,267,266},{276,297,296},{42,43,44},{46,47,30},{50,51,32},{53,33,33},{32,32,32}}},
    [2] = {{{258,257,256},{265,264,263},{271,270,269},{279,278,277},{30,30,31},{32,32,32},{33,33,33},{32,32,32}},
        {{262,261,260},{268,267,266},{276,275,274},{284,283,282},{29,30,30},{32,32,32},{33,33,33},{32,32,32}}},
    [3] = {{{3,3,3},{57,58,59},{65,66,67},{73,74,75},{30,30,31},{32,32,32},{33,33,33},{32,32,32}},
        {{3,3,3},{55,56,3},{60,61,62},{68,69,70},{29,30,30},{32,32,32},{33,33,33},{32,32,32}}},
    [4] = {{{258,257,256},{265,264,263},{271,270,269},{279,278,332},{30,30,30},{32,32,32},{33,33,33},{32,32,32}},
        {{262,261,260},{268,267,266},{276,275,274},{333,283,282},{30,30,30},{32,32,32},{33,33,33},{32,32,32}}},
    [5] = {{{3,3,3},{3,3,3},{83,83,83},{89,90,91},{92,92,92},{93,93,93},{94,94,94},{93,93,93}},
        {{3,3,3},{3,3,3},{83,83,83},{84,85,86},{92,92,92},{93,93,93},{94,94,94},{93,93,93}}},
    [6] = {{{258,257,256},{265,264,290},{293,292,291},{78,78,78},{79,79,79},{81,80,81},{80,81,80},{81,80,81}},
        {{262,261,260},{268,267,266},{276,297,296},{78,78,78},{79,79,79},{80,81,80},{81,80,81},{80,81,80}}},
    [7] = {{{0,1,2},{4,5,6},{8,9,10},{30,31,32},{34,34,34},{36,35,36},{35,36,35},{36,35,36}},
        {{0,1,2},{4,5,6},{8,9,10},{30,31,32},{34,34,34},{35,36,35},{36,35,36},{35,36,35}}},
    [8] = {{{0,1,2},{4,5,6},{8,9,10},{12,13,14},{16,16,16},{18,17,18},{17,18,17},{18,17,18}},
        {{0,1,2},{4,5,6},{8,9,10},{12,13,14},{16,16,16},{17,18,17},{18,17,18},{17,18,17}}},
    [9] = {{{19,20,21},{22,23,24},{25,26,27},{29,28,29},{16,16,16},{18,17,18},{17,18,17},{18,17,18}},
        {{21,19,20},{24,22,23},{27,25,26},{28,29,28},{16,16,16},{17,18,17},{18,17,18},{17,18,17}}},
    [10] = {{{293,293,293},{299,298,297},{307,306,305},{314,313,312},{16,16,16},{18,17,18},{17,18,17},{18,17,18}},
        {{296,295,294},{304,303,302},{311,310,309},{319,318,317},{16,16,16},{17,18,17},{18,17,18},{17,18,17}}},
    [11] = {{{14,15,16},{23,23,23},{28,28,28},{33,33,33},{38,38,38},{39,39,39},{40,40,40},{40,40,40}},
        {{16,16,16},{23,23,23},{28,28,28},{33,33,33},{38,38,38},{39,39,39},{40,40,40},{40,40,40}}},
    [12] = {{{2,3,4},{10,11,12},{17,18,19},{24,24,24},{28,28,28},{29,29,29},{30,30,30},{31,31,31}},
        {{5,6,7},{13,14,15},{20,21,22},{25,26,27},{28,28,28},{29,29,29},{30,30,30},{31,31,31}}},
    [13] = {{{1,1,1},{1,1,1},{1,1,1},{24,24,24},{30,30,30},{33,33,33},{36,36,36},{100,100,100}},
        {{7,6,7},{12,13,14},{19,19,19},{24,24,24},{30,30,30},{33,33,33},{36,36,36},{100,100,100}}},
    [14] = {{{42,43,44},{49,40,45},{49,40,50},{57,55,58},{62,61,63},{64,64,65},{67,67,67},{68,68,68}},
        {{37,38,39},{45,46,47},{50,51,41},{52,53,54},{59,60,61},{64,64,64},{66,67,67},{68,68,68}}},
    [15] = {{{72,72,72},{78,78,78},{78,78,78},{89,89,89},{94,94,94},{96,96,96},{97,97,97},{101,101,101}},
        {{72,72,72},{78,78,78},{78,78,78},{89,89,89},{94,94,94},{96,96,96},{97,97,97},{101,101,101}}}
};

static unsigned Rom(unsigned address, unsigned size) {
    size_t offset = (size_t)(address >> 16) * 0x8000 + (address & 0x7fff);
    unsigned value = bound_rom[offset];
    if (size == 2) value |= (unsigned)bound_rom[offset + 1] << 8;
    return value;
}

static uint16_t CellWord(unsigned cells, unsigned tiles, unsigned cell,
                         unsigned x, unsigned y) {
    unsigned metatile = Rom(cells + cell * 4 + ((y >> 4) & 1) * 2 +
                           ((x >> 4) & 1), 1);
    return (uint16_t)Rom(tiles + metatile * 8 + ((y >> 3) & 1) * 4 +
                        ((x >> 3) & 1) * 2, 2);
}

static int Bind(void) {
    if (!g_snes || !g_snes->cart || !g_rom) return 0;
    size_t size = g_snes->cart->romImageSize;
    if (g_rom == bound_rom && size == bound_size) return identity;
    bound_rom = g_rom; bound_size = size; identity = 0;
    if (size != kImageBytes) return 0;
    uint8_t hash[32];
    sha256_compute(bound_rom, size, hash);
    if (memcmp(hash, clean_hash, sizeof(hash))) return 0;
    /* Original B8E8/B81B tables: sixteen 8x8-cell grids; each produces
     * exactly one 32x32 tileword map. Unsupported layouts remain absent. */
    for (unsigned selector = 0; selector < kBackdrops; ++selector) {
        if (!(kSupported & (1u << selector))) continue;
        unsigned kind = Rom(0x0ed800 + selector, 1);
        unsigned cells = 0x0e0000 | Rom(0x0ef800 + (kind & 15) * 2, 2);
        unsigned tiles = 0x0e0000 | Rom(0x0edc10 + (kind >> 4) * 2, 2);
        unsigned set = Rom(0x0f9400 + selector * 4, 1);
        for (unsigned chunk = 0; chunk < 4; ++chunk) {
            unsigned id = Rom(0x0f9200 + set * 4 + chunk, 1);
            graphics[selector][chunk] = ((0x10 + (id >> 3)) << 16) |
                                        (0x8000 + ((id & 7) << 12));
        }
        used_graphics[selector] = 0;
        for (unsigned y = 0; y < 32; ++y) {
            for (unsigned x = 0; x < 32; ++x) {
                unsigned cell = Rom(0x0ed810 + selector * 64 + (y / 4) * 8 + x / 4, 1);
                uint16_t word = CellWord(cells, tiles, cell, x * 8, y * 8);
                unsigned tile = word & 1023;
                if (tile < 512 || ((word >> 10) & 7) < 6) return 0;
                original[selector][y * 32 + x] = word;
                used_graphics[selector] |= 1u << ((tile >> 7) - 4);
            }
            for (unsigned side = 0; side < 2; ++side) {
                for (unsigned x = 0; x < 9; ++x) {
                    unsigned px = x * 8 + (side ? 0 : 24);
                    unsigned entry = edge_cells[selector][side][y / 4][px / 32];
                    unsigned cell_x = px & 31;
                    if (entry & 256) cell_x = 31 - cell_x;
                    uint16_t word = CellWord(cells, tiles, entry & 255, cell_x, y * 8);
                    if (entry & 256) word ^= 0x4000;
                    unsigned tile = word & 1023;
                    if (tile < 512 || ((word >> 10) & 7) < 6) return 0;
                    sides[selector][side][y * 9 + x] = word;
                    used_graphics[selector] |= 1u << ((tile >> 7) - 4);
                }
            }
        }
    }
    identity = 1;
    return 1;
}

void FoundationBattleWideReset(void) {
    bound_rom = NULL; bound_size = 0; identity = 0;
}

int FoundationBattleWideEligible(const Ppu *ppu) {
    unsigned selector = g_ram[0x0529];
    if (!ppu || !Bind() || g_ram[0x20] != 5 || selector >= kBackdrops ||
        !(kSupported & (1u << selector)) ||
        ppu->inidisp != 15 || ppu->bgmode != 9 || (ppu->mosaic & 0xf0) ||
        ppu->setini || ppu->obsel != 3 || ppu->bgTileAdr != 0x0400 ||
        ppu->bgXsc[0] != 0x49 || ppu->bgXsc[1] != 0x59 || ppu->bgXsc[2] != 0x51 ||
        ppu->screenEnabled[0] != 0x17 || ppu->screenEnabled[1] ||
        ppu->windowsel != 0x10011 || ppu->screenWindowed[0] != 0x17 ||
        ppu->screenWindowed[1] || ppu->cgadsub || ppu->cgwsel ||
        ppu->hScroll[1] || ppu->vScroll[1]) return 0;
    /* Match every used background character chunk against the original
     * graphics descriptor. Palette animation writes only guest CGRAM and is
     * consumed through the actual per-line PPU; no host phase/color cache. */
    for (unsigned chunk = 0; chunk < 4; ++chunk) {
        if (!(used_graphics[selector] & (1u << chunk))) continue;
        unsigned address = graphics[selector][chunk];
        size_t offset = (size_t)(address >> 16) * 0x8000 + (address & 0x7fff);
        if (memcmp(ppu->vram + 0x2000 + chunk * 0x800, bound_rom + offset, 0x1000))
            return 0;
    }
    /* Full center resource check avoids accepting the first few rows of a
     * transition or a selector whose map has not finished loading. */
    if (memcmp(ppu->vram + kMapBase, original[selector], sizeof(original[selector])))
        return 0;
    return 1;
}

int FoundationBattleWidePrepareLine(const Ppu *source, unsigned line,
                                   Ppu *picture, uint16_t *shadow) {
    if (!picture || !shadow || picture == source || !source ||
        shadow == source->vram || line < 1 || line > 224 ||
        !FoundationBattleWideEligible(source)) return 0;
    unsigned selector = g_ram[0x0529], row = line / 8;
    for (unsigned x = 0; x < 9; ++x) {
        /* Signed x=-72..-8 wraps to columns55..63 of the 64x32 BG2 ring;
         * x=256..320 uses columns32..40. The original0..31 are untouched. */
        shadow[kMapBase + 1024 + row * 32 + 23 + x] = sides[selector][0][row * 9 + x];
        shadow[kMapBase + 1024 + row * 32 + x] = sides[selector][1][row * 9 + x];
    }
    picture->renderVram = shadow;
    PpuSetWidescreenLayerMask(picture, 2);
    /* Mosaic size1 is exactly no pixel grouping in the original center.
     * Avoid the renderer's negative-margin mosaic clamp for BG2 only. */
    picture->mosaic &= (uint8_t)~2u;
    picture->extraObjects = NULL; picture->extraObjectCount = 0;
    uint8_t no_hints[16] = {0};
    PpuWsSetOamLeftHints(picture, no_hints);
    PpuWsSetOamRightHints(picture, no_hints);
    picture->wsOamMotionGraceOn = 0;
    return 1;
}
