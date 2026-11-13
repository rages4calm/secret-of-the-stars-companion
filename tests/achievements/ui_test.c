/* ROM-free host-input regression. Root alone compiles/runs with verified SDL3.
 * Include actual canonical UI: no copied UI behavior or game/runtime engine. */
#define SDL_MAIN_HANDLED 1
#define SNESRECOMP_SDL3 1
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#ifndef SOTS_UI_SOURCE
#define SOTS_UI_SOURCE "../../native/foundation/src/foundation_achievements_ui.c"
#endif
#include SOTS_UI_SOURCE
static bool speculative;
static unsigned hidden_journal,hidden_map;
bool RtlSpeculativeFrame(void){return speculative;}
void FoundationJournalHide(void){hidden_journal++;}
void FoundationMapHide(void){hidden_map++;}
size_t SotsAchievements_Count(void){return 16;}
size_t SotsAchievements_Unlocked(void){return 0;}
const char *SotsAchievements_Status(void){return "Tracking locally";}
bool SotsAchievements_PopNotice(size_t *i){(void)i;return false;}
bool SotsAchievements_GetEntry(size_t i,SotsAchievementEntry *e){if(i>=16||!e)return false;*e=(SotsAchievementEntry){"test","Test","Test description",0,1,0};return true;}
void snes_ovl_fill_rect(uint32_t *d,int s,int h,int x,int y,int w,int z,uint32_t c){(void)d;(void)s;(void)h;(void)x;(void)y;(void)w;(void)z;(void)c;}
void snes_ovl_stroke_rect(uint32_t *d,int s,int h,int x,int y,int w,int z,uint32_t c){(void)d;(void)s;(void)h;(void)x;(void)y;(void)w;(void)z;(void)c;}
void snes_ovl_draw_text(uint32_t *d,int s,int h,int x,int y,const char *t,uint32_t c,int z){(void)d;(void)s;(void)h;(void)x;(void)y;(void)t;(void)c;(void)z;}
static void button(Uint32 type,Uint8 which){SDL_Event e={0};e.type=type;e.gbutton.type=type;e.gbutton.which=1;e.gbutton.button=which;e.gbutton.down=type==SDL_EVENT_GAMEPAD_BUTTON_DOWN;assert(SDL_PushEvent(&e));}
static void ctrl_j(void){SDL_Event e={0};e.type=SDL_EVENT_KEY_DOWN;e.key.type=e.type;e.key.key=SDLK_j;e.key.mod=KMOD_CTRL;e.key.down=true;e.key.repeat=false;assert(SDL_PushEvent(&e));}
int main(void){
 assert(SDL_Init(SDL_INIT_EVENTS));
 FoundationAchievementsBeforeFrame();assert(installed&&!FoundationAchievementsVisible());
 /* Push through real SDL event-watch dispatch, never call Watch directly. */
 button(SDL_EVENT_GAMEPAD_BUTTON_DOWN,SDL_GAMEPAD_BUTTON_BACK);
 button(SDL_EVENT_GAMEPAD_BUTTON_DOWN,SDL_GAMEPAD_BUTTON_NORTH);
 assert(atomic_load(&requests)&1);FoundationAchievementsBeforeFrame();
 assert(FoundationAchievementsVisible()&&hidden_journal==1&&hidden_map==1);
 const uint16_t held=(1u<<2)|(1u<<9);
 assert(FoundationAchievementsFilterInput(held)==0);
 button(SDL_EVENT_GAMEPAD_BUTTON_DOWN,SDL_GAMEPAD_BUTTON_DPAD_DOWN);
 FoundationAchievementsBeforeFrame();assert(selected==1&&FoundationAchievementsVisible());
 button(SDL_EVENT_GAMEPAD_BUTTON_DOWN,SDL_GAMEPAD_BUTTON_EAST);
 FoundationAchievementsBeforeFrame();assert(!FoundationAchievementsVisible());
 assert(FoundationAchievementsFilterInput(held|1u)==0); /* closing B must not reach guest */
 assert(FoundationAchievementsFilterInput(0)==0);
 assert(FoundationAchievementsFilterInput(held)==held); /* released then pressed */
 FoundationAchievementsFilterInput(0);
 button(SDL_EVENT_GAMEPAD_BUTTON_UP,SDL_GAMEPAD_BUTTON_BACK);
 ctrl_j();FoundationAchievementsBeforeFrame();assert(FoundationAchievementsVisible());
 assert(hidden_journal==2&&hidden_map==2);
 assert(FoundationAchievementsFilterInput(held)==0);
 ctrl_j();assert(atomic_load(&requests)&1);
 uint16_t old_blocked=blocked,old_previous=previous;
 speculative=true;FoundationAchievementsBeforeFrame();
 assert(FoundationAchievementsVisible()&&(atomic_load(&requests)&1));
 assert(FoundationAchievementsFilterInput(0)==0);
 assert(blocked==old_blocked&&previous==old_previous);
 speculative=false;FoundationAchievementsBeforeFrame();
 assert(!FoundationAchievementsVisible()&&atomic_load(&requests)==0);
 assert(FoundationAchievementsFilterInput(held)==0);
 assert(FoundationAchievementsFilterInput(0)==0);
 assert(FoundationAchievementsFilterInput(held)==held);
 FoundationAchievementsUIShutdown();assert(!installed);
 SDL_Quit();puts("PASS: SDL3 event-watch controller/keyboard browser controls, input release mask, speculative request preservation");return 0;
}
