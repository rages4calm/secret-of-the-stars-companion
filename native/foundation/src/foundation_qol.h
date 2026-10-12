/* Title-owned optional gameplay QoL; original rewards remain the default. */
#pragma once
#include <stdint.h>
void FoundationQolInit(void);
uint16_t FoundationQolScaleReward(uint16_t amount, unsigned percent);
int FoundationQolRandomEncounterAccepted(uint8_t threshold, uint8_t counter, unsigned percent);
