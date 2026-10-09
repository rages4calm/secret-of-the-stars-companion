#pragma once
#include <stddef.h>
#include <stdint.h>
struct Ppu;
void FoundationHdUiInit(void);
int FoundationHdUiEnabled(void);
void FoundationHdUiBeginFrame(void);
void FoundationHdUiObserve(const struct Ppu *ppu, unsigned line, void *unused);
void FoundationHdUiDraw(uint8_t *dst, size_t pitch, const uint32_t *logical,
                        int w, int h);
