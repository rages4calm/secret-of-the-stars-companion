#ifndef FOUNDATION_LARGE_ACTOR_CANARY_H
#define FOUNDATION_LARGE_ACTOR_CANARY_H
#include <stddef.h>
#include <stdint.h>
enum { LARGE_PACKET_BYTES = 544, LARGE_PIXELS = 256 };
enum LargeFamily { LARGE_PARTY, LARGE_REGULAR };
typedef struct LargeView {
    const uint8_t *ram;
    size_t ram_size;
    const uint16_t *vram, *cgram;
    size_t vram_words, cgram_words;
    uint8_t obsel, rotation, setini, field_eligible;
} LargeView;
typedef struct LargeSeam {
    uint32_t pc, caller, record_pointer, descriptor;
    uint16_t d, s, y, base, mask, coordinate_x, coordinate_y;
    uint8_t pb, db, m, x, decimal, emulation;
} LargeSeam;
typedef struct LargePiece {
    int x, y;
    uint16_t word;
    uint8_t emitted, slot;
} LargePiece;
typedef struct LargeActor {
    uint32_t descriptor;
    uint16_t world_x, world_y;
    int camera_x, camera_y;
    uint8_t family, index, pose;
    LargePiece pieces[2];
} LargeActor;
typedef struct LargeReplay {
    LargeActor last;
    uint8_t expected_low[8], expected_high, bytes[LARGE_PACKET_BYTES], resource[34];
    unsigned writers, generation;
    uint8_t valid, collision, sealed, displayed;
} LargeReplay;
typedef struct LargeTransfer {
    unsigned channel;
    uint8_t bank;
    uint16_t address, size;
    uint8_t b_address, mode, from_b, fixed, decrement, complete;
} LargeTransfer;
/* Only derived metadata is writable. All input views/ROM/packets are const. */
int LargeBindRom(const uint8_t *rom, size_t size);
int LargeWrappingParked(const uint8_t *ram, size_t size);
int LargeBegin(LargeReplay *state, const LargeView *view,
               const uint8_t *initial_staging, size_t size);
int LargeCapture(LargeReplay *state, const LargeView *view,
                 const LargeSeam *seam, enum LargeFamily family, unsigned index);
int LargeSeal(LargeReplay *state, const uint8_t *staging, size_t size);
int LargeComplete(LargeReplay *state, const LargeTransfer *transfer,
                  const uint8_t *actual_packet, size_t size);
/* Returns at most the last writer's two parts; no duplicate fixed-slot ranks. */
unsigned LargePrepare(const LargeReplay *state, const LargeView *view,
                      const uint8_t *actual_packet, size_t size,
                      int raster_dx, int raster_dy, unsigned line,
                      LargePiece output[2], uint16_t pixels[2][LARGE_PIXELS]);
int LargeDecode(const LargeView *view, uint16_t word, uint16_t pixels[LARGE_PIXELS]);
void LargeReset(LargeReplay *state);
#endif
