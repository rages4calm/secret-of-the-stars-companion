#pragma once
#include "host_main.h"
void FoundationPresentationInit(void);
void FoundationPresentationBeforeFrame(void);
void FoundationPresentationReset(void);
void FoundationPresentationShutdown(void);
int FoundationPresentationScale(void);
void FoundationPresentationAfterFrame(const SnesDesktopHostFrameStats *stats);
void FoundationPresentationPrepare(int drawable_w, int drawable_h, int *w, int *h);
int FoundationPresentationDraw(uint8_t *dst, size_t pitch, const uint8_t *field,
                               int w, int h, double alpha);
