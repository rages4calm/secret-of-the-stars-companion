#pragma once
#include <stdint.h>
/* Read-only guest CPU-half observer; disabled without the explicit trace path. */
void FoundationDiagnosticsBeginFrame(void);
void FoundationDiagnosticsFrame(void);
void FoundationDiagnosticsRendered(const uint8_t *field, unsigned frame);
