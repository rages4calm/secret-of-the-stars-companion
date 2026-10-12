#pragma once
#include <stddef.h>
#include <stdint.h>

/* Read-only current-area overview. All state is disposable host presentation;
 * there are no visited bits, guest writes or serialized checkpoint fields. */
enum { FOUNDATION_MAP_WIDTH = 224, FOUNDATION_MAP_HEIGHT = 128 };
typedef struct FoundationMapPoint {
    int x, y; /* Original primary-area world pixels. */
    unsigned objective; /* Verified current objective; zero is a town. */
    char label[24]; /* Optional verified town/objective name, copied safely. */
    unsigned name_index; /* Original 04:C200 identity; name0 may be renamed. */
} FoundationMapPoint;
/* Manual tracking resolves a unique accepted ordinary point in world0.
 * Text labels and authored coordinates never establish its identity. */
static inline int FoundationMapTownByName(const FoundationMapPoint *points,
    size_t count, unsigned scene, unsigned name_index, FoundationMapPoint *output) {
    if (!points || !output || count > 32 || scene != 0 || name_index >= 23) return 0;
    const FoundationMapPoint *found = NULL;
    for (size_t i = 0; i < count; ++i)
        if (!points[i].objective && points[i].name_index == name_index && points[i].label[0]) {
            if (found) return 0;
            found = &points[i];
        }
    if (!found) return 0;
    *output = *found;
    return 1;
}
int FoundationMapPosition(const uint8_t *ram, size_t size, int *x, int *y);
int FoundationMapSample(const uint8_t *ram, size_t size,
                        const uint16_t *vram, size_t words,
                        const uint16_t *cgram, size_t colors,
                        int x, int y, uint32_t *color);
#ifndef FOUNDATION_MAP_STANDALONE
#include "host_main.h"
void FoundationMapInit(void);
void FoundationMapBeforeFrame(void);
void FoundationMapAfterFrame(const SnesDesktopHostFrameStats *stats);
void FoundationMapReset(void);
int FoundationMapVisible(void);
void FoundationMapHide(void);
int FoundationMapBounds(unsigned *scene, unsigned *width, unsigned *height);
int FoundationMapTrackGuideTown(unsigned name_index);
int FoundationMapGuideTown(void);
void FoundationMapClearGuideTown(void);
/* Scene-locked metadata supplied by the title's verified town/event module.
 * Unknown/unverified objectives must never be supplied here. */
void FoundationMapSetPoints(unsigned scene, const FoundationMapPoint *points, size_t count);
void FoundationMapDraw(uint8_t *dst, size_t pitch, int w, int h);
void FoundationMapShutdown(void);
#endif
