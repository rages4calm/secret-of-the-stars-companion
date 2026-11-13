#pragma once
#include <stdint.h>
#include <stddef.h>
void FoundationAchievementsBeforeFrame(void);
uint16_t FoundationAchievementsFilterInput(uint16_t buttons);
void FoundationAchievementsDraw(uint8_t *dst,size_t pitch,int w,int h);
void FoundationAchievementsUIShutdown(void);
int FoundationAchievementsVisible(void);
