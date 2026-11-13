/* Host-only local achievement browser/toasts; original guest input is only
 * masked while browsing. No guest writes, pacing change or audio callback. */
#include "foundation_achievements_ui.h"
#include "sots_achievements.h"
#include "common_rtl.h"
#include "foundation_journal.h"
#include "foundation_map.h"
#include "snes_overlay_draw.h"
#include "desktop/sdl_compat.h"
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
static atomic_int requests,shown,back_held;
static int installed,selected,close_guard;
static uint16_t blocked,previous;
static size_t notice_index;
static uint64_t notice_until;
#if SNESRECOMP_SDL3
static bool Watch(void *ignored,SDL_Event *e) {
#else
static int Watch(void *ignored,SDL_Event *e) {
#endif
 (void)ignored;
 if(e->type==SDL_KEYDOWN&&!e->key.repeat) {
#if SNESRECOMP_SDL3
  SDL_Keycode key=e->key.key;SDL_Keymod mods=e->key.mod;
#else
  SDL_Keycode key=e->key.keysym.sym;SDL_Keymod mods=e->key.keysym.mod;
#endif
  if(key==SDLK_j&&(mods&KMOD_CTRL))atomic_fetch_or(&requests,1);
  else if(atomic_load(&shown)) {
   if(key==SDLK_ESCAPE)atomic_fetch_or(&requests,2);
   if(key==SDLK_UP||key==SDLK_LEFT)atomic_fetch_or(&requests,4);
   if(key==SDLK_DOWN||key==SDLK_RIGHT)atomic_fetch_or(&requests,8);
  }
 }
#if SNESRECOMP_SDL3
 if(e->type==SDL_EVENT_GAMEPAD_BUTTON_DOWN||e->type==SDL_EVENT_GAMEPAD_BUTTON_UP) {
  int down=e->type==SDL_EVENT_GAMEPAD_BUTTON_DOWN,b=e->gbutton.button;
  if(b==SDL_GAMEPAD_BUTTON_BACK)atomic_store(&back_held,down);
  if(down&&b==SDL_GAMEPAD_BUTTON_NORTH&&atomic_load(&back_held))atomic_fetch_or(&requests,1);
  if(down&&atomic_load(&shown)) {
   if(b==SDL_GAMEPAD_BUTTON_EAST)atomic_fetch_or(&requests,2);
   if(b==SDL_GAMEPAD_BUTTON_DPAD_UP)atomic_fetch_or(&requests,4);
   if(b==SDL_GAMEPAD_BUTTON_DPAD_DOWN)atomic_fetch_or(&requests,8);
  }
 }
#else
 if(e->type==SDL_CONTROLLERBUTTONDOWN||e->type==SDL_CONTROLLERBUTTONUP) {
  int down=e->type==SDL_CONTROLLERBUTTONDOWN,b=e->cbutton.button;
  if(b==SDL_CONTROLLER_BUTTON_BACK)atomic_store(&back_held,down);
  if(down&&b==SDL_CONTROLLER_BUTTON_Y&&atomic_load(&back_held))atomic_fetch_or(&requests,1);
  if(down&&atomic_load(&shown)) {
   if(b==SDL_CONTROLLER_BUTTON_B)atomic_fetch_or(&requests,2);
   if(b==SDL_CONTROLLER_BUTTON_DPAD_UP)atomic_fetch_or(&requests,4);
   if(b==SDL_CONTROLLER_BUTTON_DPAD_DOWN)atomic_fetch_or(&requests,8);
  }
 }
#endif
 return 1;
}
void FoundationAchievementsBeforeFrame(void) {
 if(RtlSpeculativeFrame())return;
 if(!installed){SDL_AddEventWatch(Watch,NULL);installed=1;}
 int r=atomic_exchange(&requests,0),was_shown=atomic_load(&shown);
 if(r&1){atomic_store(&shown,!atomic_load(&shown));if(atomic_load(&shown)){FoundationJournalHide();FoundationMapHide();}}
 if(r&2)atomic_store(&shown,0);
 if(was_shown&&!atomic_load(&shown))close_guard=1;
 if(atomic_load(&shown)) {
  if((r&4)&&selected>0)--selected;
  if((r&8)&&(size_t)(selected+1)<SotsAchievements_Count())++selected;
 }
 size_t i;if(SotsAchievements_PopNotice(&i)){notice_index=i;notice_until=(uint64_t)SDL_GetTicks()+4000;}
}
int FoundationAchievementsVisible(void){return atomic_load(&shown);}
uint16_t FoundationAchievementsFilterInput(uint16_t b) {
 if(RtlSpeculativeFrame())return 0;
 uint16_t edge=b&~previous;previous=b;blocked&=b;
 if(close_guard){blocked|=b;close_guard=0;}
 if(atomic_load(&shown)){blocked|=b;if(edge&1u)atomic_store(&shown,0);return 0;}
 return b&~blocked;
}
static void Wrap(uint32_t *p,int stride,int h,int x,int y,const char *text) {
 char line[31];size_t n=strlen(text),at=0;
 for(int row=0;row<2&&at<n;++row){size_t take=n-at;if(take>29)take=29;if(at+take<n){size_t q=take;while(q&&text[at+q]!=' ')--q;if(q)take=q;}memcpy(line,text+at,take);line[take]=0;snes_ovl_draw_text(p,stride,h,x,y+row*10,line,0xffd5e0ef,1);at+=take;while(text[at]==' ')++at;}
}
void FoundationAchievementsDraw(uint8_t *dst,size_t pitch,int w,int h) {
 uint32_t *p=(uint32_t *)dst;int stride=(int)(pitch/4);SotsAchievementEntry e;char text[64];
 if(atomic_load(&shown)&&w>=256&&h>=208){int x=(w-256)/2,y=(h-208)/2;snes_ovl_fill_rect(p,stride,h,x,y,256,208,0xff101827);snes_ovl_stroke_rect(p,stride,h,x,y,256,208,0xffa9bdd5);snprintf(text,sizeof(text),"ACHIEVEMENTS %zu/%zu",SotsAchievements_Unlocked(),SotsAchievements_Count());snes_ovl_draw_text(p,stride,h,x+8,y+8,text,0xffffdf78,1);
  int first=selected/5*5;for(int row=0;row<5;++row){int i=first+row;if(!SotsAchievements_GetEntry((size_t)i,&e))break;int yy=y+28+row*23;if(i==selected)snes_ovl_fill_rect(p,stride,h,x+5,yy-2,246,22,0xff293a57);snprintf(text,sizeof(text),"%c %.27s",e.unlocked_at?'*':'-',e.title);snes_ovl_draw_text(p,stride,h,x+8,yy,text,e.unlocked_at?0xffffdf78:0xfff0f3fa,1);snprintf(text,sizeof(text),"  %u/%u%s",e.progress,e.target,e.unlocked_at?"  UNLOCKED":"");snes_ovl_draw_text(p,stride,h,x+8,yy+10,text,0xffa7b9d8,1);}
  if(SotsAchievements_GetEntry((size_t)selected,&e))Wrap(p,stride,h,x+8,y+150,e.description);
  const char *status=SotsAchievements_Status();snprintf(text,sizeof(text),"%.29s",status?status:"Local progress");snes_ovl_draw_text(p,stride,h,x+8,y+176,text,0xffa7b9d8,1);snes_ovl_draw_text(p,stride,h,x+8,y+192,"U/D: SELECT  B/ESC: CLOSE",0xffffdf78,1);
 }else if(notice_until>(uint64_t)SDL_GetTicks()&&SotsAchievements_GetEntry(notice_index,&e)){int x=(w-240)/2;snes_ovl_fill_rect(p,stride,h,x,4,240,28,0xff101827);snes_ovl_stroke_rect(p,stride,h,x,4,240,28,0xffffdf78);snes_ovl_draw_text(p,stride,h,x+6,7,"ACHIEVEMENT UNLOCKED",0xffffdf78,1);snprintf(text,sizeof(text),"%.28s",e.title);snes_ovl_draw_text(p,stride,h,x+6,19,text,0xfff0f3fa,1);}
}
void FoundationAchievementsUIShutdown(void){if(installed)SDL_DelEventWatch(Watch,NULL);installed=0;}
