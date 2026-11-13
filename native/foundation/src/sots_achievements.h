/* Offline host achievements. No serialized guest-state fields or game writes. */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef struct SotsAchievementEntry {
 const char *id,*title,*description;
 uint32_t progress,target;
 uint64_t unlocked_at;
} SotsAchievementEntry;
/* Set before Init from actual launch script/fixture state. Init also checks
 * diagnostic environment flags. Diagnostic sessions expose only the catalog. */
void SotsAchievements_SetDiagnostic(bool diagnostic);
bool SotsAchievements_Init(const char *absolute_profile_directory);
void SotsAchievements_Shutdown(void);
void SotsAchievements_OnLoaded(uint64_t generation);
/* eligible is the host's completed non-speculative original-field eligibility.
 * Adapter additionally validates the original idle field/party/chapter guards. */
void SotsAchievements_Observe(const uint8_t *ram,size_t size,uint64_t generation,bool eligible);
/* Root calls only from qualified original success/producer/UI owners.
 * NotifyWalk marks a qualified vector tick; Observe counts actual tiny axis
 * motion into16-pixel tile-equivalent steps. No movement -> no progress. */
void SotsAchievements_NotifyVictory(void);
void SotsAchievements_NotifyWalk(void);
void SotsAchievements_NotifyMapOpen(void);
void SotsAchievements_NotifyGuideOpen(void);
size_t SotsAchievements_Count(void);
bool SotsAchievements_GetEntry(size_t index,SotsAchievementEntry *entry);
size_t SotsAchievements_Unlocked(void);
const char *SotsAchievements_Status(void);
const char *SotsAchievements_ProfilePath(void);
bool SotsAchievements_PopNotice(size_t *index);
/* Test/shutdown only; never wait for storage in a gameplay frame. */
bool SotsAchievements_WaitIdle(unsigned timeout_ms);
