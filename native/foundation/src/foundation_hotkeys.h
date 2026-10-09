#pragma once
/* Host-only requests, resolved by the runtime's editable key/pad maps. */
void FoundationHotkeysInit(void);
void FoundationHotkeysBeforeFrame(void);
void FoundationHotkeysShutdown(void);
void FoundationHotkeysReset(void);
void FoundationHotkeysCommand(unsigned command, int pressed);
int FoundationHotkeysMovementHeld(void);
int FoundationHotkeysConsumeBattleInfo(void);
int FoundationHotkeysConsumeJournal(void);
