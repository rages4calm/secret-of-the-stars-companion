#pragma once
#include <stddef.h>
#include <stdint.h>

typedef struct Ppu Ppu;

/* Read-only standard-field resource decoder. Original/off is the fallback.
 * Eligible refreshes the live ROM/state contract; resolve uses layer 0/1 and
 * signed WORLD PIXELS, not the PPU's masked ring coordinates. */
int FoundationFieldEligible(const Ppu *ppu);
/* Pre-raster eligibility retains every scene/layout guard but permits scroll
 * latches to disagree with WRAM. Rendering must use the actual raster scroll,
 * unwrapped relative to Camera; it must not replace scanout with WRAM scroll. */
int FoundationFieldSceneEligible(const Ppu *ppu);
int FoundationFieldResolve(int layer, int world_x, int world_y, uint16_t *word);
int FoundationFieldLayerActive(int layer);
int FoundationFieldCamera(int layer, int *world_x, int *world_y);
void FoundationFieldReset(void);

/* Portable input adapter for the finite standalone checker. This does not
 * expose cache writes or require runtime globals. Bind verifies the whole
 * headerless original image; check never mutates its input. */
typedef struct FoundationFieldView {
    const uint8_t *ram;
    size_t ram_size;
    uint8_t inidisp, bgmode, mosaic, setini;
    uint8_t bgsc[4], tm, ts;
    uint16_t bg_tile_adr, hscroll[2], vscroll[2];
} FoundationFieldView;
int FoundationFieldBind(const uint8_t *rom, size_t image_size);
int FoundationFieldCheckView(const FoundationFieldView *view);
int FoundationFieldCheckSceneView(const FoundationFieldView *view);

#ifdef FOUNDATION_FIELD_STANDALONE
/* Private prototype checker only: direct stream bypass is NOT eligibility. */
int FoundationFieldPrivateProvenance(const uint8_t *ram, size_t size, unsigned stream);
unsigned FoundationFieldPrivateSelected(const uint8_t *ram, size_t size);
int FoundationFieldPrivateCondition(const uint8_t *ram, size_t size,
                                    unsigned selector, unsigned a, unsigned b);
#endif
