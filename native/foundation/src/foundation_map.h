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
} FoundationMapPoint;
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
/* Scene-locked metadata supplied by the title's verified town/event module.
 * Unknown/unverified objectives must never be supplied here. */
void FoundationMapSetPoints(unsigned scene, const FoundationMapPoint *points, size_t count);
void FoundationMapDraw(uint8_t *dst, size_t pitch, int w, int h);
void FoundationMapShutdown(void);
#endif
