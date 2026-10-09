/* Color-preserving Scale2x/EPX presentation, based on the published algorithm:
 * https://www.scale2x.it/algorithm . Implemented here for ARGB8888 surfaces.
 * The owner's EarthBound implementation informed the 8-level tolerance:
 * one SNES color step should not toggle text-edge decisions every frame. */
#include "foundation_scale2x.h"

static int Similar(uint32_t a, uint32_t b) {
    for (int shift = 0; shift <= 16; shift += 8) {
        int difference = (int)((a >> shift) & 255) - (int)((b >> shift) & 255);
        if (difference < -8 || difference > 8) return 0;
    }
    return 1;
}

void FoundationScale2x(const uint32_t *src, int w, int h, uint8_t *dst, size_t pitch) {
    for (int y = 0; y < h; ++y) {
        uint32_t *upper = (uint32_t *)(dst + (size_t)y * 2 * pitch);
        uint32_t *lower = (uint32_t *)(dst + ((size_t)y * 2 + 1) * pitch);
        for (int x = 0; x < w; ++x) {
            uint32_t e = src[y*w+x], b = src[(y ? y-1 : y)*w+x];
            uint32_t hval = src[(y+1 < h ? y+1 : y)*w+x];
            uint32_t d = src[y*w+(x ? x-1 : x)], f = src[y*w+(x+1 < w ? x+1 : x)];
            uint32_t corners[4] = {e, e, e, e};
            if (!Similar(b, hval) && !Similar(d, f)) {
                if (Similar(d, b)) corners[0] = d;
                if (Similar(b, f)) corners[1] = f;
                if (Similar(d, hval)) corners[2] = d;
                if (Similar(hval, f)) corners[3] = f;
            }
            upper[x*2] = corners[0]; upper[x*2+1] = corners[1];
            lower[x*2] = corners[2]; lower[x*2+1] = corners[3];
        }
    }
}
