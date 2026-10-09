/* Original map words for additional standard field scenery. All caches are derived
 * host state: no CPU/PPU/MMIO/WRAM/SRAM writes, guest waits or timing edits. */
#include "foundation_field.h"
#include "sha256.h"
#include <string.h>

#ifndef FOUNDATION_FIELD_STANDALONE
#include "common_rtl.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include "snes/cart.h"
extern Snes *g_snes;
#endif

#define ORIGINAL_IMAGE_SIZE 1572864u
static const uint8_t clean_identity[32] = {
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00
};
static const uint8_t *source_rom;
static size_t source_size;
static int identity_ok, cache_valid, eligible;
enum { kMaxSegments = 16, kMaxTiles = kMaxSegments * 32 };
typedef struct FieldLayer {
    unsigned grid, cells, tiles, attributes, width, height, active;
} FieldLayer;
typedef struct FieldResources {
    FieldLayer layers[2];
    unsigned scene, wrap, flag_tiles, stage_tiles, flag_tiles_authenticated;
} FieldResources;
static FieldResources resources;
static uint16_t maps[2][kMaxTiles * kMaxTiles];
static uint8_t ids[2][kMaxTiles * kMaxTiles], attributes[2][256];
static uint16_t boundary[2][4];
static unsigned cells_end[2], tiles_end[2], attributes_end[2];
static int camera[2][2];
static const uint8_t *live_ram;

static unsigned Ram(const uint8_t *ram, unsigned at, unsigned size) {
    unsigned value = 0;
    for (unsigned i = 0; i < size; ++i) value |= (unsigned)ram[at + i] << (i * 8);
    return value;
}

static int ReadRom(unsigned address, unsigned count, unsigned *value) {
    unsigned bank = address >> 16, low = address & 0xffff;
    if (!source_rom || bank >= 0x30 || low < 0x8000 || count > 3 || low + count > 0x10000)
        return 0;
    size_t offset = (size_t)bank * 0x8000 + low - 0x8000;
    if (offset > source_size || count > source_size - offset) return 0;
    *value = Ram(source_rom, (unsigned)offset, count);
    return 1;
}

static int Span(unsigned address, unsigned size) {
    unsigned last;
    return size && ReadRom(address, 1, &last) &&
        (address & 0xffff) + size <= 0x10000 && ReadRom(address + size - 1, 1, &last);
}

static int TableIndex(unsigned table, unsigned count, unsigned bank, unsigned pointer) {
    for (unsigned i = 0; i < count; ++i) {
        unsigned value;
        if (!ReadRom(table + i * 2, 2, &value)) return -1;
        if ((bank | value) == pointer) return (int)i;
    }
    return -1;
}

static unsigned TableEnd(unsigned table, unsigned count, unsigned pointer) {
    unsigned end = table == 0x099000 ? 0xb000 : table == 0x098000 ? 0x9000 : 0x10000;
    unsigned low = pointer & 0xffff;
    for (unsigned i = 0; i < count; ++i) {
        unsigned value;
        if (!ReadRom(table + i * 2, 2, &value)) return 0;
        if (value > low && value < end) end = value;
    }
    return (pointer & 0xff0000) + end;
}

/* Private prototype: original condition selection is evaluated every refresh. */
static unsigned SceneStory(const uint8_t *ram, unsigned selector, unsigned nibble) {
    if (selector < 0x78)
        return ram[0x5360 + ((selector >> 3) & 1)] & (0x80u >> (selector & 7));
    if (selector == 0x7e) return ram[0x5361] & 15;
    if (selector == 255) {
        unsigned value = ram[0x5362 + (nibble >> 1)];
        return nibble & 1 ? value & 15 : value >> 4;
    }
    return ram[0x5362 + ((selector & 127) >> 3)] & (0x80u >> (selector & 7));
}

static int SceneCondition(const uint8_t *ram, unsigned selector, unsigned a, unsigned b) {
    unsigned stage = ram[0x5372];
    switch (selector) {
    case 0: return stage < a || (stage == a && !SceneStory(ram, b, b));
    case 1: return stage == a && SceneStory(ram, b, b);
    case 2: return stage <= a;
    case 3: return stage == a && SceneStory(ram, 0x7e, 0) == b;
    case 4: return SceneStory(ram, a | 128, b) != 0;
    case 5: return SceneStory(ram, a | 128, b) == 0;
    case 6: return SceneStory(ram, 255, a) == b;
    case 7: return (ram[0x04b6] & 128) != 0;
    case 255: return 1;
    default: return 0;
    }
}

static int SelectedStream(unsigned scene, const uint8_t *ram, unsigned *stream) {
    unsigned pointer;
    if (scene >= 337 || !ReadRom(0x088000 + scene * 2, 2, &pointer)) return 0;
    pointer |= 0x080000;
    for (unsigned records = 0; records < 52; ++records) {
        unsigned selector, a = 0, b = 0, value;
        if (pointer < 0x0882a2 || pointer >= 0x0887e5 ||
            !ReadRom(pointer, 1, &selector) || (selector != 255 && selector > 7)) return 0;
        unsigned size = selector == 255 ? 3 : 5;
        if (selector != 255 && (!ReadRom(pointer + 1, 1, &a) ||
                               !ReadRom(pointer + 2, 1, &b))) return 0;
        if (!ReadRom(pointer + size - 2, 2, &value)) return 0;
        if (SceneCondition(ram, selector, a, b)) {
            *stream = 0x080000 | value;
            return 1;
        }
        pointer += size;
    }
    return 0;
}

static int Take(unsigned *cursor, unsigned size, unsigned *value) {
    if (!ReadRom(*cursor, size, value)) return 0;
    *cursor += size;
    return 1;
}

/* Membership is derived from actual original scene-stream references. */
static uint8_t referenced_flag_lists[55];
static int flag_lists_ready;
static int AuthenticatedFlagList(unsigned pointer) {
    if (!flag_lists_ready) {
        memset(referenced_flag_lists, 0, sizeof(referenced_flag_lists));
        for (unsigned scene = 0; scene < 337; ++scene) {
            unsigned record;
            if (!ReadRom(0x088000 + scene * 2, 2, &record)) return 0;
            record |= 0x080000;
            for (unsigned n = 0; n < 52; ++n) {
                unsigned selector, stream, flags, value;
                if (!ReadRom(record, 1, &selector) || (selector != 255 && selector > 7)) return 0;
                unsigned size = selector == 255 ? 3 : 5;
                if (!ReadRom(record + size - 2, 2, &stream)) return 0;
                stream |= 0x080000;
                if (!ReadRom(stream, 2, &flags)) return 0;
                unsigned cursor = stream + 15;
                if ((flags & 0x6000) && !Take(&cursor, 2, &value)) return 0;
                if ((flags & 0x1000) && !Take(&cursor, 1, &value)) return 0;
                if ((flags & 0x0080) && !Take(&cursor, 2, &value)) return 0;
                if ((flags & 0x0040) && !Take(&cursor, 1, &value)) return 0;
                if (flags & 0x0020) {
                    if (!Take(&cursor, 1, &value) || value >= 55) return 0;
                    referenced_flag_lists[value] = 1;
                }
                if (selector == 255) break;
                record += size;
            }
        }
        flag_lists_ready = 1;
    }
    unsigned end = 0x08ec00;
    int member = 0;
    for (unsigned index = 0; index < 55; ++index) {
        unsigned value;
        if (!ReadRom(0x08e900 + index * 2, 2, &value)) return 0;
        value |= 0x080000;
        if (value == pointer && referenced_flag_lists[index]) member = 1;
        if (value > pointer && value < end) end = value;
    }
    if (!member || pointer < 0x08e96e || pointer >= end) return 0;
    for (unsigned offset = 0; offset <= 252; offset += 4) {
        unsigned location;
        if (pointer + offset + 2 > end || !ReadRom(pointer + offset, 2, &location)) return 0;
        if (location == 0xffff) return 1;
        if (pointer + offset + 4 > end || !Span(pointer + offset, 4)) return 0;
    }
    return 0;
}

static int LayerMatches(const FieldLayer *map, unsigned defs, unsigned index,
                        unsigned dimensions, int secondary) {
    unsigned grid, cells, tiles, attributes;
    unsigned ci = secondary ? defs & 15 : defs >> 4;
    unsigned ti = secondary ? defs >> 4 : defs & 15;
    if (index >= 328 || !ReadRom(0x099000 + index * 2, 2, &grid) ||
        !ReadRom(0x0a8000 + ci * 2, 2, &cells) ||
        !ReadRom(0x038000 + ti * 2, 2, &tiles) ||
        !ReadRom(0x098000 + ti * 2, 2, &attributes)) return 0;
    return map->active && map->grid == (0x090000 | grid) &&
        map->cells == (0x0a0000 | cells) && map->tiles == (0x030000 | tiles) &&
        map->attributes == (0x090000 | attributes) &&
        map->width == (dimensions >> 4) && map->height == (dimensions & 15);
}

static int StreamMatches(FieldResources *candidate, const uint8_t *ram, unsigned stream) {
    unsigned flags, defs, index, dims, value;
    if (!Span(stream, 15) || !ReadRom(stream, 2, &flags) ||
        !ReadRom(stream + 2, 1, &defs) || !ReadRom(stream + 3, 2, &index) ||
        !ReadRom(stream + 5, 1, &dims) ||
        !LayerMatches(&candidate->layers[0], defs, index & 0x3fff, dims, 0) ||
        candidate->wrap != ((flags >> 15) & 1)) return 0;
    unsigned cursor = stream + 15;
    if ((flags & 0x6000) && !Take(&cursor, 2, &value)) return 0;
    if ((flags & 0x1000) && !Take(&cursor, 1, &value)) return 0;
    if ((flags & 0x0080) && !Take(&cursor, 2, &value)) return 0;
    if ((flags & 0x0040) && !Take(&cursor, 1, &value)) return 0;
    candidate->flag_tiles_authenticated = (flags & 0x0020) != 0;
    if (candidate->flag_tiles_authenticated) {
        unsigned pointer;
        if (!Take(&cursor, 1, &value) || !ReadRom(0x08e900 + value * 2, 2, &pointer) ||
            candidate->flag_tiles != (0x080000 | pointer)) return 0;
    }
    candidate->flag_tiles_authenticated = AuthenticatedFlagList(candidate->flag_tiles);
    value = 0;
    if ((flags & 0x0010) && !Take(&cursor, 2, &value)) return 0;
    unsigned stage_pointer;
    if (!ReadRom(0x08f600 + value * 2, 2, &stage_pointer) ||
        candidate->stage_tiles != (0x080000 | stage_pointer)) return 0;
    unsigned mode = 0;
    if (flags & 8) {
        if (!Take(&cursor, 1, &mode) || !Take(&cursor, 1, &defs) ||
            !Take(&cursor, 2, &index)) return 0;
        if (mode & 128) {
            if (!Take(&cursor, 1, &dims) ||
                !LayerMatches(&candidate->layers[1], defs, index, dims, 1)) return 0;
        } else {
            /* Original velocity-only branch clears mode/producer but retains
             * old resource pointers/dimensions. It consumes no dimensions. */
            if (!Take(&cursor, 2, &value) || !Take(&cursor, 2, &value)) return 0;
            mode = 0;
            if (candidate->layers[1].active) return 0;
        }
    } else if (candidate->layers[1].active) return 0;
    if (ram[0x0452] != mode) return 0;
    if ((flags & 4) && !Take(&cursor, 2, &value)) return 0;
    if ((flags & 2) && !Take(&cursor, 1, &value)) return 0;
    if ((flags & 1) && !Take(&cursor, 1, &value)) return 0;
    return 1;
}

static int SelectedMatches(FieldResources *candidate, const uint8_t *ram) {
    unsigned stream;
    return SelectedStream(candidate->scene, ram, &stream) && StreamMatches(candidate, ram, stream);
}

static int ValidateResources(void) {
    unsigned value;
    if (resources.scene >= 337 || !ReadRom(0x088000 + resources.scene * 2, 2, &value) ||
        value < 0x82a2 || value > 0x87e4) return 0;
    for (unsigned layer = 0; layer < 2; ++layer) {
        const FieldLayer *map = &resources.layers[layer];
        if (!map->active) continue;
        cells_end[layer] = TableEnd(0x0a8000, 16, map->cells);
        tiles_end[layer] = TableEnd(0x038000, 16, map->tiles);
        /* Original B704/B70A uses raw8bit ID as [$2C],Y. Neighboring
         * pointer table entries are not declared attribute-array lengths. */
        unsigned bank_end = (map->attributes & 0xff0000) + 0x10000;
        attributes_end[layer] = map->attributes + 256;
        if (attributes_end[layer] > bank_end) attributes_end[layer] = bank_end;
        int tiles = TableIndex(0x038000, 16, 0x030000, map->tiles);
        if (tiles < 0 || !ReadRom(0x098000 + (unsigned)tiles * 2, 2, &value) ||
            map->attributes != (0x090000 | value) ||
            TableIndex(0x0a8000, 16, 0x0a0000, map->cells) < 0 ||
            TableIndex(0x099000, 328, 0x090000, map->grid) < 0 ||
            !map->width || !map->height || map->width > 15 || map->height > 15 ||
            !Span(map->grid, map->width * map->height * 2) ||
            map->grid + map->width * map->height * 2 > TableEnd(0x099000, 328, map->grid)) return 0;
    }
    return resources.layers[0].active;
}

static int Decode(unsigned layer, unsigned x, unsigned y, uint16_t *word, unsigned *id) {
    const FieldLayer *map = &resources.layers[layer];
    unsigned segment, pointer, cell, metatile, value;
    if (!ReadRom(map->grid + 2 * ((y / 256) * map->width + x / 256), 2, &segment) || segment >= 1280 ||
        !ReadRom(0x09b000 + segment * 3, 3, &pointer) ||
        !Span(pointer, 64) ||
        !ReadRom(pointer + ((y >> 5) & 7) * 8 + ((x >> 5) & 7), 1, &cell) ||
        map->cells + cell * 4 + 4 > cells_end[layer] ||
        !ReadRom(map->cells + cell * 4 + ((y >> 4) & 1) * 2 + ((x >> 4) & 1), 1, &metatile) ||
        map->tiles + metatile * 8 + 8 > tiles_end[layer] ||
        !ReadRom(map->tiles + metatile * 8 + ((y >> 3) & 1) * 4 + ((x >> 3) & 1) * 2, 2, &value))
        return 0;
    *id = metatile;
    *word = (uint16_t)value;
    return 1;
}

static int BuildCache(void) {
    /* Cache original IDs as well as static words. Story-dependent E/F tiles
     * are resolved from current restored flags without guest accessor writes. */
    if (!ValidateResources()) return 0;
    for (unsigned layer = 0; layer < 2; ++layer) {
        const FieldLayer *map = &resources.layers[layer];
        if (!map->active) continue;
        unsigned width = map->width * 32, height = map->height * 32;
        uint8_t checked[256] = {0};
        unsigned value;
        if (!ReadRom(map->attributes, 1, &value)) return 0;
        attributes[layer][0] = value & 15;
        checked[0] = 1;
        for (unsigned i = 0; i < 4; ++i) {
            if (!ReadRom(map->tiles + i * 2, 2, &value)) return 0;
            boundary[layer][i] = (uint16_t)value;
        }
        for (unsigned y = 0; y < height; ++y) for (unsigned x = 0; x < width; ++x) {
            unsigned id;
            unsigned offset = y * width + x;
            if (!Decode(layer, x * 8, y * 8, &maps[layer][offset], &id)) return 0;
            ids[layer][offset] = (uint8_t)id;
            if (!checked[id]) {
                if (map->attributes + id >= attributes_end[layer] ||
                    !ReadRom(map->attributes + id, 1, &value)) return 0;
                attributes[layer][id] = value & 15;
                checked[id] = 1;
            }
        }
    }
    return 1;
}

void FoundationFieldReset(void) {
    source_rom = NULL;
    source_size = 0;
    identity_ok = cache_valid = eligible = 0;
    live_ram = NULL;
    flag_lists_ready = 0;
    memset(&resources, 0, sizeof(resources));
    memset(camera, 0, sizeof(camera));
}

int FoundationFieldBind(const uint8_t *rom, size_t image_size) {
    /* Host image buffers are immutable between binds. Reset forces re-hash on
     * checkpoint/new-game/content reload. A caller mutating a private test ROM
     * at the same address must reset before rebinding. */
    if (rom == source_rom && image_size == source_size) return identity_ok;
    FoundationFieldReset();
    source_rom = rom;
    source_size = image_size;
    if (!rom || image_size != ORIGINAL_IMAGE_SIZE) return 0;
    uint8_t hash[32];
    sha256_compute(rom, image_size, hash);
    identity_ok = !memcmp(hash, clean_identity, sizeof(hash));
    if (!identity_ok) return 0;
    return identity_ok;
}

static int CheckView(const FoundationFieldView *view, int check_scroll) {
    eligible = 0;
    if (!identity_ok || !view || !view->ram || view->ram_size != 0x20000 ||
        view->inidisp != 15 || view->bgmode != 9 || (view->mosaic & 0xf0) || view->setini ||
        view->tm != 0x17 || (view->ts & ~16u) || view->bg_tile_adr != 0x0400 ||
        view->bgsc[0] != 0x49 || view->bgsc[1] != 0x59 || view->bgsc[2] != 0x51) return 0;
    const uint8_t *ram = view->ram;
    if (ram[0x20] != 1 || ram[0x0531]) return 0;
    FieldResources candidate = {0};
    candidate.scene = Ram(ram, 0x040e, 2);
    candidate.wrap = ram[0x0407] != 0;
    candidate.flag_tiles = Ram(ram, 0x0453, 3);
    candidate.stage_tiles = Ram(ram, 0x0456, 3);
    for (unsigned layer = 0; layer < 2; ++layer) {
        unsigned triple = layer * 3, pair = layer * 2;
        FieldLayer *map = &candidate.layers[layer];
        map->grid = Ram(ram, 0x0513 + triple, 3);
        map->tiles = Ram(ram, 0x0500 + triple, 3);
        map->cells = Ram(ram, 0x0506 + triple, 3);
        map->attributes = Ram(ram, layer ? 0x055c : 0x0537, 3);
        map->width = ram[0x046d + pair]; map->height = ram[0x046e + pair];
        map->active = ram[0x050c + layer] != 0;
        unsigned x = Ram(ram, 0x02ad + layer * 4, 2);
        unsigned y = Ram(ram, 0x02af + layer * 4, 2);
        if (check_scroll && (view->hscroll[layer] != (x & 1023) ||
                             view->vscroll[layer] != (y & 1023))) return 0;
        camera[layer][0] = x & 0x8000 ? (int)x - 0x10000 : (int)x;
        camera[layer][1] = y & 0x8000 ? (int)y - 0x10000 : (int)y;
    }
    if (!SelectedMatches(&candidate, ram)) return 0;
    if (memcmp(&resources, &candidate, sizeof(candidate))) {
        resources = candidate;
        cache_valid = BuildCache();
    }
    if (!cache_valid) return 0;
    live_ram = ram;
    eligible = 1;
    return 1;
}

int FoundationFieldCheckView(const FoundationFieldView *view) {
    return CheckView(view, 1);
}

int FoundationFieldCheckSceneView(const FoundationFieldView *view) {
    return CheckView(view, 0);
}

static int FloorTile(int pixel) {
    /* Defined for negative values and INT_MIN; no signed negative shift or
     * negation of INT_MIN. This preserves original metatile quadrants. */
    return pixel >= 0 ? pixel / 8 : -1 - (-(pixel + 1)) / 8;
}

static int StoryValue(unsigned threshold, unsigned selector) {
    if (selector < 0x78)
        return (live_ram[0x5360 + ((selector >> 3) & 1)] & (0x80u >> (selector & 7))) != 0;
    if (selector == 0x7e) return live_ram[0x5361] & 15;
    if (selector == 0xff) {
        unsigned value = live_ram[0x5362 + (threshold >> 1)];
        return threshold & 1 ? value & 15 : value >> 4;
    }
    return (live_ram[0x5362 + ((selector & 0x7f) >> 3)] & (0x80u >> (selector & 7))) != 0;
}

static int Conditional(unsigned layer, unsigned id, int x, int y, unsigned *selected) {
    *selected = id;
    unsigned type = attributes[layer][id], pointer;
    if (type != 14 && type != 15) return 1;
    if (type == 14 && !resources.flag_tiles_authenticated) return 0;
    pointer = type == 14 ? resources.flag_tiles : resources.stage_tiles;
    if (!pointer) return 0;
    int mx = x >= 0 ? x / 2 : -1 - (-(x + 1)) / 2;
    int my = y >= 0 ? y / 2 : -1 - (-(y + 1)) / 2;
    unsigned key = ((unsigned)mx & 255) << 8 | ((unsigned)my & 255);
    unsigned stride = type == 14 ? 4 : 5;
    for (unsigned offset = 0; offset + stride <= 256; offset += stride) {
        unsigned record, value;
        if (!ReadRom(pointer + offset, 2, &record)) return 0;
        if (record == 0xffff) return 1;
        if (record != key) continue;
        if (type == 14) {
            if (!ReadRom(pointer + offset + 2, 2, &value)) return 0;
            if (live_ram[0x53f9 + ((value >> 3) & 255)] & (0x80u >> (value & 7))) *selected = 2;
        } else {
            unsigned threshold, selector, replacement;
            if (!ReadRom(pointer + offset + 2, 1, &threshold) ||
                !ReadRom(pointer + offset + 3, 1, &selector) ||
                !ReadRom(pointer + offset + 4, 1, &replacement)) return 0;
            unsigned stage = live_ram[0x5372];
            int value = StoryValue(threshold, selector);
            if (threshold == 255 ? value != 0 : threshold < stage ||
                (threshold == stage && (selector == 255 || value))) *selected = replacement;
        }
        return 1;
    }
    return 0; /* Unterminated/overflowing table is not a supported resource. */
}

int FoundationFieldResolve(int layer, int world_x, int world_y, uint16_t *word) {
    if (!eligible || !word || layer < 0 || layer > 1) return 0;
    int x = FloorTile(world_x), y = FloorTile(world_y);
    int width = (int)resources.layers[layer].width * 32;
    int height = (int)resources.layers[layer].height * 32;
    if (!resources.layers[layer].active) return 0;
    if (resources.wrap) {
        x %= width; y %= height;
        if (x < 0) x += width;
        if (y < 0) y += height;
    }
    int outside = x < 0 || y < 0 || x >= width || y >= height;
    unsigned id = outside ? 0 : ids[layer][y * width + x], selected;
    if (outside) selected = 0;
    else if (!Conditional((unsigned)layer, id, x, y, &selected)) return 0;
    if (id == selected)
        *word = outside ? boundary[layer][((unsigned)y & 1) * 2 + ((unsigned)x & 1)] : maps[layer][y * width + x];
    else {
        unsigned value, part = ((unsigned)y & 1) * 4 + ((unsigned)x & 1) * 2;
        const FieldLayer *map = &resources.layers[layer];
        if (map->tiles + selected * 8 + part + 2 > tiles_end[layer] ||
            !ReadRom(map->tiles + selected * 8 + part, 2, &value)) return 0;
        *word = (uint16_t)value;
    }
    return 1;
}

int FoundationFieldLayerActive(int layer) {
    return eligible && layer >= 0 && layer < 2 && resources.layers[layer].active;
}

int FoundationFieldCamera(int layer, int *world_x, int *world_y) {
    if (!eligible || layer < 0 || layer > 1 || !world_x || !world_y) return 0;
    *world_x = camera[layer][0];
    *world_y = camera[layer][1];
    return 1;
}

#ifdef FOUNDATION_FIELD_STANDALONE
/* Private harness metadata hooks, excluded from runtime builds. */
static void PrivateCandidate(const uint8_t *ram, FieldResources *candidate) {
    memset(candidate, 0, sizeof(*candidate));
    candidate->scene = Ram(ram, 0x040e, 2);
    candidate->wrap = ram[0x0407] != 0;
    candidate->flag_tiles = Ram(ram, 0x0453, 3);
    candidate->stage_tiles = Ram(ram, 0x0456, 3);
    for (unsigned layer = 0; layer < 2; ++layer) {
        FieldLayer *map = &candidate->layers[layer];
        map->grid = Ram(ram, 0x0513 + layer * 3, 3);
        map->cells = Ram(ram, 0x0506 + layer * 3, 3);
        map->tiles = Ram(ram, 0x0500 + layer * 3, 3);
        map->attributes = Ram(ram, layer ? 0x055c : 0x0537, 3);
        map->width = ram[0x046d + layer * 2];
        map->height = ram[0x046e + layer * 2];
        map->active = ram[0x050c + layer] != 0;
    }
}
int FoundationFieldPrivateProvenance(const uint8_t *ram, size_t size, unsigned stream) {
    if (!identity_ok || !ram || size != 0x20000) return 0;
    FieldResources candidate;
    PrivateCandidate(ram, &candidate);
    return stream ? StreamMatches(&candidate, ram, stream) : SelectedMatches(&candidate, ram);
}
unsigned FoundationFieldPrivateSelected(const uint8_t *ram, size_t size) {
    unsigned stream = 0;
    if (!identity_ok || !ram || size != 0x20000 ||
        !SelectedStream(Ram(ram, 0x040e, 2), ram, &stream)) return 0;
    return stream;
}
int FoundationFieldPrivateCondition(const uint8_t *ram, size_t size,
                                    unsigned selector, unsigned a, unsigned b) {
    if (!ram || size != 0x20000 || selector > 255 || a > 255 || b > 255) return 0;
    return SceneCondition(ram, selector, a, b);
}
#endif

#ifndef FOUNDATION_FIELD_STANDALONE
static int LiveView(const Ppu *ppu, int check_scroll) {
    eligible = 0;
    if (!ppu || !g_snes || !g_snes->cart || !g_rom ||
        !FoundationFieldBind(g_rom, g_snes->cart->romImageSize)) return 0;
    FoundationFieldView view = {0};
    view.ram = g_ram;
    view.ram_size = sizeof(g_ram);
    view.inidisp = ppu->inidisp;
    view.bgmode = ppu->bgmode;
    view.mosaic = ppu->mosaic;
    view.setini = ppu->setini;
    memcpy(view.bgsc, ppu->bgXsc, sizeof(view.bgsc));
    view.bg_tile_adr = ppu->bgTileAdr;
    view.tm = ppu->screenEnabled[0];
    view.ts = ppu->screenEnabled[1];
    for (unsigned i = 0; i < 2; ++i) {
        view.hscroll[i] = ppu->hScroll[i];
        view.vscroll[i] = ppu->vScroll[i];
    }
    return CheckView(&view, check_scroll);
}

int FoundationFieldEligible(const Ppu *ppu) {
    return LiveView(ppu, 1);
}

int FoundationFieldSceneEligible(const Ppu *ppu) {
    return LiveView(ppu, 0);
}
#endif
