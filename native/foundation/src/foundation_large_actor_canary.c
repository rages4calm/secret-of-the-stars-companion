/* Read-only B0 host contract. No guest opcode, activation or timing work. */
#include "foundation_large_actor_canary.h"
#include "sha256.h"
#include <string.h>
static const uint8_t *bound_rom;
static size_t bound_size;
static int identity;
static const uint8_t clean_hash[32] = {
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00
};
static unsigned Read16(const uint8_t *data, unsigned at) {
    return data[at] | (unsigned)data[at + 1] << 8;
}
static int Signed(unsigned value) { return (int16_t)value; }
static int Nearest512(int value, int center) {
    return ((value - center + 256) & 511) + center - 256;
}
static unsigned RomWord(unsigned address) {
    unsigned offset = (address >> 16) * 32768 + (address & 32767);
    return Read16(bound_rom, offset);
}
static void Resource(const LargeView *view, uint8_t key[34]) {
    memcpy(key, view->ram + 0x500, 12);
    memcpy(key + 12, view->ram + 0x513, 6);
    memcpy(key + 18, view->ram + 0x537, 3);
    memcpy(key + 21, view->ram + 0x55c, 3);
    memcpy(key + 24, view->ram + 0x46d, 4);
    memcpy(key + 28, view->ram + 0x40e, 2);
    key[30] = view->ram[0x407]; key[31] = !!view->ram[0x400];
    key[32] = view->ram[0x401]; key[33] = view->obsel;
}
static int SameResource(const LargeReplay *state, const LargeView *view) {
    uint8_t key[34]; Resource(view, key);
    return !memcmp(state->resource, key, sizeof(key));
}
static int Overlap(const void *a, size_t an, const void *b, size_t bn) {
    if (!a || !b || !an || !bn) return 0;
    uintptr_t av = (uintptr_t)a, bv = (uintptr_t)b;
    return av <= bv ? bv - av < an : av - bv < bn;
}
static int InputAlias(const LargeView *view, const void *output, size_t bytes) {
    return Overlap(output, bytes, view->ram, view->ram_size) ||
        Overlap(output, bytes, view->vram, view->vram_words * sizeof(uint16_t)) ||
        Overlap(output, bytes, view->cgram, view->cgram_words * sizeof(uint16_t)) ||
        Overlap(output, bytes, bound_rom, bound_size);
}
/* Original selected-world saved parked allocation relation. No story or activation writes.
 * CFED TSB0401 owns bit08 on top of the original field route. The authentic
 * C400 world loader produces0E; retained0C route uses the same exact roster.
 * Route0E is admitted by ViewValid only with these full wrapping/resource guards. */
int LargeWrappingParked(const uint8_t *ram, size_t size) {
    static const uint8_t selected[12] = {0x58,0x87,3,0x58,0x8f,3,0x18,0x84,10,0x18,0x88,10};
    static const uint8_t grids[6] = {0x5c,0xa8,9,0,0x97,9};
    if (!ram || size != 131072 || ram[0x20] != 1 || (ram[0x401] != 12 && ram[0x401] != 14) ||
        ram[0x407] != 1 || ram[0x400] || Read16(ram,0x40e) ||
        ram[0x5372] != 17 || (ram[0x5361] & 0x40) || (ram[0x409] & 0x80) ||
        Read16(ram,0x5441) || Read16(ram,0x46d) != 0x0e0e || Read16(ram,0x46f) != 0x0404 ||
        memcmp(ram+0x500,selected,12) || memcmp(ram+0x513,grids,6) ||
        Read16(ram,0x537) != 0x8110 || ram[0x539] != 9 ||
        Read16(ram,0x55c) != 0x8210 || ram[0x55e] != 9) return 0;
    unsigned sx=Read16(ram,0x544b),sy=Read16(ram,0x5455);
    if (sx>=3584 || sy>=3584) return 0;
    for (unsigned i=0;i<19;++i) {
        unsigned at=0x4100+25*i;
        if (i<2) {
            if (ram[at] != (i ? 0 : 2) || Read16(ram,at+1) != 1536 ||
                Read16(ram,at+3) != (i ? 544 : 528) || Read16(ram,at+5) != 0x598) return 0;
        } else if (i==16 || i==18) {
            unsigned x=i==16?sx:(sx+3584-8)%3584;
            unsigned y=i==16?sy:(sy+3584-48)%3584;
            if (ram[at]!=2 || Read16(ram,at+1)!=x || Read16(ram,at+3)!=y ||
                Read16(ram,at+5)!=(i==16?0xa8:0xb0)) return 0;
        } else if (ram[at]!=255) return 0;
    }
    for (unsigned i=0;i<5;++i) {
        unsigned at=0x4000+18*i,base=Read16(ram,at+3);
        unsigned gfx=base+ram[at]*2+(ram[at+10]>>7);
        if (ram[at]!=255 && (base==0xb0 || (gfx&0xfff8)==0xa8 || ram[at]>3)) return 0;
    }
    return 1;
}
/* Original01:CEEB..CF92 and01:CFD2..D05D may both run in the same scene.
 * This additional exact roster keeps the existing single-roster predicate
 * byte-identical. All coordinates come from saved original loader sources;
 * no record is activated or changed by the presentation observer. */
int LargeWrappingCombined(const uint8_t *ram, size_t size) {
    static const uint8_t selected[12] = {0x58,0x87,3,0x58,0x8f,3,0x18,0x84,10,0x18,0x88,10};
    static const uint8_t grids[6] = {0x5c,0xa8,9,0,0x97,9};
    if (!ram || size != 131072 || ram[0x20] != 1 || (ram[0x401] != 12 && ram[0x401] != 14) ||
        ram[0x407] != 1 || ram[0x400] || Read16(ram,0x40e) || ram[0x4b6] ||
        ram[0x5372] != 17 || (ram[0x5361] & 0x40) ||
        (ram[0x409] != 0 && ram[0x409] != 2) ||
        Read16(ram,0x543f) || Read16(ram,0x5441) ||
        Read16(ram,0x46d) != 0x0e0e || Read16(ram,0x46f) != 0x0404 ||
        memcmp(ram+0x500,selected,12) || memcmp(ram+0x513,grids,6) ||
        Read16(ram,0x537) != 0x8110 || ram[0x539] != 9 ||
        Read16(ram,0x55c) != 0x8210 || ram[0x55e] != 9) return 0;
    unsigned x=Read16(ram,0x5449),y=Read16(ram,0x5453);
    unsigned sx=Read16(ram,0x544b),sy=Read16(ram,0x5455);
    unsigned shadow=!!(ram[0x5457]&0x40);
    if (x>=3584 || y>=3584 || sx>=3584 || sy>=3584) return 0;
    for (unsigned i=0;i<19;++i) {
        unsigned at=0x4100+25*i,wx=0,wy=0,base=0,pose=2;
        if (i<2) { wx=1536; wy=i?544:528; base=0x598; pose=i?0:2; }
        else if (i==15 && shadow) { wx=x; wy=y; base=0xa8; }
        else if (i==16) { wx=sx; wy=sy; base=0xa8; }
        else if (i==17) { wx=x; wy=shadow?(y+3584-32)%3584:y; base=0xa0; }
        else if (i==18) { wx=(sx+3584-8)%3584; wy=(sy+3584-48)%3584; base=0xb0; }
        else { if (ram[at]!=255) return 0; continue; }
        if (ram[at]!=pose || Read16(ram,at+1)!=wx || Read16(ram,at+3)!=wy ||
            Read16(ram,at+5)!=base) return 0;
    }
    for (unsigned i=0;i<5;++i) {
        unsigned at=0x4000+18*i,base=Read16(ram,at+3);
        unsigned gfx=base+2*ram[at]+(ram[at+10]>>7);
        if (ram[at]!=255 && (base==0xb0 || (gfx&0xfff8)==0xa8 || ram[at]>3)) return 0;
    }
    return 1;
}
int LargeWrappingRoster(const uint8_t *ram, size_t size) {
    return LargeWrappingParked(ram,size) || LargeWrappingCombined(ram,size);
}
/* Original CB87 active82 allocation in the already authenticated selected
 * chapter17 world. Regular0/1 retain source bases/poses and world-sized motion;
 * CEEB/CFD2 parked families and inactive/variable prefix admission stay separate.
 * Packed partyB0 ignores0471/0473; this predicate never transforms coordinates. */
static int LargeWrappingTravelCore(const uint8_t *ram, size_t size) {
    static const uint8_t selected[12] = {0x58,0x87,3,0x58,0x8f,3,0x18,0x84,10,0x18,0x88,10};
    static const uint8_t grids[6] = {0x5c,0xa8,9,0,0x97,9};
    if (!ram || size!=131072 || ram[0x20]!=1 ||
        (ram[0x401]!=12 && ram[0x401]!=14) || ram[0x407]!=1 || ram[0x409]!=0x82 ||
        ram[0x400] || Read16(ram,0x40e) || ram[0x4b6] || ram[0x5372]!=17 ||
        (ram[0x5361]&0x40) || Read16(ram,0x46d)!=0x0e0e || Read16(ram,0x46f)!=0x0404 ||
        memcmp(ram+0x500,selected,12) || memcmp(ram+0x513,grids,6) ||
        Read16(ram,0x537)!=0x8110 || ram[0x539]!=9 ||
        Read16(ram,0x55c)!=0x8210 || ram[0x55e]!=9 ||
        ram[0x4000]>3 || ram[0x4000]!=ram[0x4012] || ram[0x4009]!=ram[0x4000] ||
        ram[0x401b]!=0x42 || Read16(ram,0x4003)!=0xa8 || Read16(ram,0x4015)!=0xb0 ||
        Read16(ram,0x4001)!=0x7080 || Read16(ram,0x4013)!=0x4078 || ram[0x4005] ||
        (ram[0x4017]!=0 && ram[0x4017]!=0x80) ||
        ram[0x4024]!=255 || ram[0x4036]!=255 || ram[0x4048]!=255) return 0;
    for (unsigned i=0;i<19;++i) {
        unsigned at=0x4100+25*i;
        if (i<2) {
            if (ram[at]!=(i?0:2) || Read16(ram,at+5)!=0x598 ||
                Read16(ram,at+1)>=3584 || Read16(ram,at+3)>=3584) return 0;
        } else if (ram[at]!=255) return 0;
    }
    return 1;
}
/* Keep the installed inactive-prefix admission independent. Source D80F also
 * dispatches DC15 before this exact82 party; its separate predicate admits only
 * the roster/resource core. The title observer still owns all resolved-prefix,
 * cursor/capacity/full544/DMA checks before drawing any effect. */
int LargeWrappingTravel(const uint8_t *ram, size_t size) {
    if (!LargeWrappingTravelCore(ram,size)) return 0;
    for (unsigned i=0;i<8;++i) if (ram[0x4300+21*i]) return 0;
    return 1;
}
int LargeWrappingTravelVariable(const uint8_t *ram, size_t size) {
    return LargeWrappingTravelCore(ram,size) && ram[0x401]==14;
}
static int TravelFamily(const uint8_t *ram, size_t size) {
    return LargeWrappingTravel(ram,size) || LargeWrappingTravelVariable(ram,size);
}
static int ViewValid(const LargeView *view) {
    return identity && view && view->ram && view->ram_size == 131072 &&
        view->vram && view->vram_words == 32768 && view->cgram && view->cgram_words == 256 &&
        view->field_eligible && view->obsel == 3 && !view->rotation && !view->setini &&
        view->ram[0x20] == 1 &&
        (view->ram[0x401] == 12 ||
         (view->ram[0x401] == 14 && view->ram[0x407] == 1 &&
          (LargeWrappingRoster(view->ram,view->ram_size) || TravelFamily(view->ram,view->ram_size)))) &&
        (!view->ram[0x407] || LargeWrappingRoster(view->ram,view->ram_size) ||
         TravelFamily(view->ram,view->ram_size));
}
/* Production coordinates are coherent only while both signed offset words stay
 * in the begun epoch. They are transient producer inputs, not loaded art identity. */
static int SameOffsets(const LargeReplay *state, const LargeView *view) {
    return state->offset_x == Signed(Read16(view->ram, 0x471)) &&
           state->offset_y == Signed(Read16(view->ram, 0x473));
}
int LargeBindRom(const uint8_t *rom, size_t size) {
    if (rom != bound_rom || size != bound_size) {
        bound_rom = rom; bound_size = size; identity = 0;
        if (rom && size == 1572864) {
            uint8_t hash[32]; sha256_compute(rom, size, hash);
            identity = !memcmp(hash, clean_hash, sizeof(hash));
        }
    }
    return identity;
}
void LargeReset(LargeReplay *state) {
    if (!state) return;
    unsigned generation = state->generation + 1;
    memset(state, 0, sizeof(*state)); state->generation = generation;
}
int LargeBegin(LargeReplay *state, const LargeView *view,
               const uint8_t *staging, size_t size) {
    if (!state) return 0;
    LargeReset(state);
    if (!ViewValid(view) || !staging || size != LARGE_PACKET_BYTES ||
        staging[0] != 0x80 || staging[1] != 0xf0 || staging[4] != 0x80 || staging[5] != 0xf0)
        return 0;
    memcpy(state->expected_low, staging, 8);
    Resource(view, state->resource);
    state->offset_x = Signed(Read16(view->ram, 0x471));
    state->offset_y = Signed(Read16(view->ram, 0x473));
    state->valid = 1;
    return 1;
}
static int Reject(LargeReplay *state) {
    if (state) state->valid = state->sealed = state->displayed = 0;
    return 0;
}
int LargeCapture(LargeReplay *state, const LargeView *view,
                 const LargeSeam *seam, enum LargeFamily family, unsigned index) {
    if (!state || !state->valid || state->sealed || !ViewValid(view) || !SameResource(state, view) ||
        !SameOffsets(state, view) || !seam ||
        (family != LARGE_PARTY && family != LARGE_REGULAR) ||
        index >= (family == LARGE_PARTY ? 5u : 19u)) return Reject(state);
    const uint8_t *ram = view->ram;
    unsigned at = (family == LARGE_PARTY ? 0x4000 : 0x4100) + index * (family == LARGE_PARTY ? 18 : 25);
    unsigned base = Read16(ram, at + (family == LARGE_PARTY ? 3 : 5));
    unsigned descriptor = 0x0e9800 + base * 8 + ram[at] * 4;
    unsigned mask = ram[0x400] ? 0xefff : 0xffff;
    if (seam->pc != (family == LARGE_PARTY ? 0x01d989u : 0x01db68u) ||
        seam->caller != (family == LARGE_PARTY ? 0x01d865u : 0x01d86fu) ||
        seam->pb != 1 || seam->db != 1 || seam->d != 0x0e00 || seam->s >= 0x1ffd ||
        seam->m || !seam->x || seam->y != 3 || seam->decimal || seam->emulation ||
        seam->record_pointer != 0x7e0000 + at || seam->base != base ||
        base != 0xb0 || ram[at] == 255 || seam->mask != mask ||
        descriptor < 0x0e9800 || descriptor + 4 > 0x0ed800)
        return Reject(state);
    if (ram[0x407]) {
        int parked=LargeWrappingRoster(ram,view->ram_size) && family==LARGE_REGULAR &&
            index==18 && ram[at]==2 && descriptor==0x0e9d88;
        int travel=TravelFamily(ram,view->ram_size) && family==LARGE_PARTY &&
            index==1 && ram[at]<=3 && descriptor==0x0e9d80+ram[at]*4;
        if (!parked && !travel) return Reject(state);
    }
    LargeActor actor = {0}; actor.family = family; actor.index = index;
    actor.pose = ram[at]; actor.descriptor = descriptor;
    actor.camera_x = Signed(Read16(ram, 0x2ad)); actor.camera_y = Signed(Read16(ram, 0x2af));
    int x, y;
    if (family == LARGE_PARTY) {
        actor.world_x = ram[at + 1] | ((ram[at + 5] & 1) << 8);
        actor.world_y = ram[at + 2] | ((ram[at + 5] & 2) << 7);
        x = actor.world_x; y = Signed(actor.world_y - 1);
    } else {
        actor.world_x = Read16(ram, at + 1); actor.world_y = Read16(ram, at + 3);
        /* DB68 receives the original world + signed offset - primary camera
         * result. Capture this once; Prepare only applies displayed raster delta. */
        x = Signed(actor.world_x + state->offset_x - actor.camera_x);
        y = Signed(actor.world_y + state->offset_y - actor.camera_y) - 1;
        if (seam->descriptor != descriptor || seam->coordinate_x != (uint16_t)x ||
            seam->coordinate_y != (uint16_t)(y + 1)) return Reject(state);
    }
    unsigned high = 0;
    for (unsigned part = 0; part < 2; ++part) {
        LargePiece *piece = &actor.pieces[part]; piece->slot = part;
        piece->x = Signed(x + part * 16); piece->y = Signed(y);
        piece->word = RomWord(descriptor + part * 2) & mask;
        unsigned raw_x = (uint16_t)piece->x, raw_y = (uint16_t)piece->y;
        unsigned threshold = family == LARGE_PARTY ? 0x1f9 : 0xfff1;
        piece->emitted = (raw_x >= threshold || raw_x < 255) &&
                         (raw_y >= threshold || raw_y < 239);
        if (piece->emitted) {
            high |= (2 | ((raw_x >> 8) & 1)) << (part * 2);
            state->expected_low[part * 4] = raw_x;
            state->expected_low[part * 4 + 1] = raw_y;
            state->expected_low[part * 4 + 2] = piece->word;
            state->expected_low[part * 4 + 3] = piece->word >> 8;
        }
    }
    if (state->writers && (family < state->last.family ||
        (family == state->last.family && index <= state->last.index))) return Reject(state);
    if (state->writers && (!actor.pieces[0].emitted || !actor.pieces[1].emitted)) {
        state->collision = 1;
        return Reject(state); /* earlier low words may survive with smaller size bits */
    }
    if (state->writers) state->collision = 1;
    state->last = actor; state->expected_high = high; ++state->writers;
    return 1;
}
int LargeSeal(LargeReplay *state, const LargeView *view,
              const uint8_t *staging, size_t size) {
    if (!state || !state->valid || !ViewValid(view) || !SameResource(state, view) ||
        !SameOffsets(state, view) || !state->writers || !staging || size != LARGE_PACKET_BYTES ||
        memcmp(staging, state->expected_low, 8) || staging[512] != state->expected_high)
        return Reject(state);
    memcpy(state->bytes, staging, LARGE_PACKET_BYTES); state->sealed = 1;
    return 1;
}
int LargeComplete(LargeReplay *state, const LargeTransfer *transfer,
                  const uint8_t *actual, size_t size) {
    if (!state || !state->valid || !state->sealed || !transfer ||
        transfer->channel != 7 || transfer->bank != 0x7e || transfer->address != 0x2200 ||
        transfer->size != LARGE_PACKET_BYTES || transfer->b_address != 4 ||
        transfer->mode || transfer->from_b || transfer->fixed || transfer->decrement || !transfer->complete ||
        size != LARGE_PACKET_BYTES || !actual ||
        memcmp(actual, state->bytes, LARGE_PACKET_BYTES)) return Reject(state);
    state->displayed = 1;
    return 1;
}
int LargeDecode(const LargeView *view, uint16_t word, uint16_t pixels[LARGE_PIXELS]) {
    if (!ViewValid(view) || !pixels || !view->vram || view->vram_words != 32768 ||
        !view->cgram || view->cgram_words != 256) return 0;
    if (InputAlias(view, pixels, LARGE_PIXELS * sizeof(uint16_t))) return 0;
    unsigned base = word & 0x100 ? 0x7000 : 0x6000;
    unsigned palette = 128 + 16 * ((word >> 9) & 7);
    for (unsigned row = 0; row < 16; ++row) {
        unsigned sy = word & 0x8000 ? 15 - row : row;
        for (unsigned col = 0; col < 16; ++col) {
            unsigned sx = word & 0x4000 ? 15 - col : col;
            unsigned tile = ((((word & 255) >> 4) + (sy >> 3)) << 4) |
                            (((word & 15) + (sx >> 3)) & 15);
            unsigned at = (base + tile * 16 + (sy & 7)) & 0x7fff;
            uint32_t planes = view->vram[at] | (uint32_t)view->vram[(at + 8) & 0x7fff] << 16;
            unsigned bit = 7 - (sx & 7);
            unsigned pixel = ((planes >> bit) & 1) | ((planes >> (bit + 7)) & 2) |
                ((planes >> (bit + 14)) & 4) | ((planes >> (bit + 21)) & 8);
            pixels[row * 16 + col] = pixel ? 0x8000 | (view->cgram[palette + pixel] & 0x7fff) : 0;
        }
    }
    return 1;
}
unsigned LargePrepare(const LargeReplay *state, const LargeView *view,
                      const uint8_t *actual, size_t size,
                      int dx, int dy, unsigned line,
                      LargePiece output[2], uint16_t pixels[2][LARGE_PIXELS]) {
    if (!state || !state->valid || !state->displayed || !ViewValid(view) || !SameResource(state, view) || !actual ||
        size != LARGE_PACKET_BYTES || memcmp(actual, state->bytes, size) || !output || !pixels ||
        line < 1 || line > 224 || dx < -512 || dx > 511 || dy < -512 || dy > 511) return 0;
    if (InputAlias(view, output, sizeof(LargePiece) * 2) ||
        InputAlias(view, pixels, sizeof(uint16_t) * 2 * LARGE_PIXELS) ||
        Overlap(output, sizeof(LargePiece) * 2, pixels, sizeof(uint16_t) * 2 * LARGE_PIXELS) ||
        Overlap(output, sizeof(LargePiece) * 2, actual, size) ||
        Overlap(pixels, sizeof(uint16_t) * 2 * LARGE_PIXELS, actual, size) ||
        Overlap(output, sizeof(LargePiece) * 2, state, sizeof(*state)) ||
        Overlap(pixels, sizeof(uint16_t) * 2 * LARGE_PIXELS, state, sizeof(*state))) return 0;
    unsigned count = 0;
    for (unsigned part = 0; part < 2; ++part) {
        LargePiece piece = state->last.pieces[part];
        if (state->last.family == LARGE_PARTY) {
            piece.x = Nearest512(piece.x, 128); piece.y = Nearest512(piece.y, 112);
        }
        piece.x -= dx; piece.y -= dy;
        if (view->ram[0x407] && state->last.family==LARGE_REGULAR) {
            /* Margin-only geometry from the immutable original completed packet. */
            if (piece.x-128 < -1792) piece.x+=3584;
            if (piece.x-128 >=1792) piece.x-=3584;
            if (piece.y-112 < -1792) piece.y+=3584;
            if (piece.y-112 >=1792) piece.y-=3584;
        }
        if ((int)line - 1 < piece.y || (int)line - 1 >= piece.y + 16 ||
            piece.x >= 328 || piece.x + 16 <= -72 || (piece.x >= 0 && piece.x + 16 <= 256)) continue;
        if (!LargeDecode(view, piece.word, pixels[count])) return 0;
        output[count++] = piece;
    }
    return count;
}
