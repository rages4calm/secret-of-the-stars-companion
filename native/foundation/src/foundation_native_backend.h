#pragma once
#include <stddef.h>
#include <stdint.h>
void FoundationNativeBackendConfigure(void);
void FoundationNativeBackendOnRom(const uint8_t *,size_t);
void FoundationNativeBackendBeforeFrame(void);
void FoundationNativeBackendReset(void);
