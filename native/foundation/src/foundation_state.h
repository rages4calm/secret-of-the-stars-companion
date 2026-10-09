#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
struct SaveLoadInfo;
void FoundationStateSave(struct SaveLoadInfo *sli);
void FoundationStateLoad(struct SaveLoadInfo *sli, uint32_t version);
void FoundationStateApply(uint32_t version);
const char *FoundationStateIdentity(void);
bool FoundationStatePreflight(const void *data, size_t size);
