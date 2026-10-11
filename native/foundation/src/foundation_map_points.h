#pragma once
#include "foundation_map.h"

/* Original current-world exits/name streams only. No authored coordinate/name
 * table, visited history, guest writes or serialized state. A negative objective
 * scene means no verified current destination is available. */
int FoundationMapPointsBuild(const uint8_t *rom, size_t rom_size,
    const uint8_t *ram, size_t ram_size, unsigned scene,
    unsigned width, unsigned height, int verified_destination,
    FoundationMapPoint *output, size_t capacity, size_t *count);

#ifndef FOUNDATION_MAP_POINTS_STANDALONE
void FoundationMapPointsInit(void);
void FoundationMapPointsAfterFrame(int verified_destination);
void FoundationMapPointsReset(void);
#endif
