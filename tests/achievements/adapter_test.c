/* ROM-free adapter regression checks. Root builds/runs; fresh private roots only.
 * argv1: fresh absolute normal progress root; argv2: fresh diagnostic root.
 * Test stubs replace only the host generation/speculation queries. */
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint64_t generation=1;
static bool speculative;
uint64_t RtlStateGeneration(void){return generation;}
bool RtlSpeculativeFrame(void){return speculative;}
#define SOTS_ACHIEVEMENTS_TEST 1
void SotsAchievements_TestBeforeCommit(void){}
#include "../../native/foundation/src/sots_achievements.c"
static uint8_t ram[0x20000];
static void frame(void){SotsAchievements_Observe(ram,sizeof ram,generation,true);}
static uint32_t progress(const char *id){for(size_t i=0;i<SotsAchievements_Count();i++){SotsAchievementEntry e;assert(SotsAchievements_GetEntry(i,&e));if(!strcmp(e.id,id))return e.progress;}assert(!"unknown achievement ID");return 0;}
static void settled(void){assert(SotsAchievements_WaitIdle(5000));}
static void field(void){ram[0x20]=1;frame();}
int main(int argc,char **argv){
 assert(argc==3);assert(SDL_Init(0));
 SDL_setenv("SNESRECOMP_SCRIPT","0",1);SDL_setenv("SNESRECOMP_RUN_FRAMES","0",1);SDL_setenv("SOTS_ACHIEVEMENTS_DIAGNOSTIC","0",1);SDL_setenv("SNESRECOMP_FOUNDATION_STAGED","0",1);
 memset(ram,0,sizeof ram);memset(ram+0x5373,0xff,64);ram[0x20]=1;ram[0x401]=4;ram[0x46d]=ram[0x46e]=1;ram[0x407]=1;ram[0x2ad]=ram[0x2af]=32;ram[0x40e]=1;
 SotsAchievements_SetDiagnostic(false);assert(SotsAchievements_Init(argv[1]));settled();assert(!strcmp(SotsAchievements_Status(),"Tracking locally"));assert(SotsAchievements_Count()==16);frame();
 SotsAchievements_NotifyMapOpen();SotsAchievements_NotifyMapOpen();SotsAchievements_NotifyGuideOpen();settled();assert(progress("ui.map")==1&&progress("ui.guide")==1);
 ram[0x20]=5;frame();speculative=true;SotsAchievements_NotifyVictory();speculative=false;settled();assert(progress("battle.first")==0);
 SotsAchievements_NotifyVictory();SotsAchievements_NotifyVictory();settled();assert(progress("battle.first")==1&&progress("battle.ten")==1);
 for(unsigned i=0;i<9;i++){field();ram[0x20]=5;frame();SotsAchievements_NotifyVictory();}settled();assert(progress("battle.ten")==10);field();
 ram[0x5373]=0;frame();settled();assert(progress("item.starcrest")==1&&progress("item.dogpill")==0);
 ram[0x4b6]=0x80;frame();settled();assert(progress("party.swap")==1);
 ram[0x5372]=6;frame();settled();assert(progress("route.town6")==0);ram[0x5372]=5;frame();ram[0x5372]=6;frame();settled();assert(progress("route.town6")==1);
 /* A producer tick against a wall is not a traveled step. */
 for(unsigned i=0;i<800;i++){SotsAchievements_NotifyWalk();frame();}settled();assert(progress("walk.500")==0);
 for(unsigned i=0;i<8000;i++){SotsAchievements_NotifyWalk();ram[0x2ad]++;frame();}settled();assert(progress("walk.500")==500&&progress("walk.1000")==500);
 SotsAchievements_NotifyWalk();ram[0x2ad]+=40;frame();settled();assert(progress("walk.1000")==500);
 ++generation;SotsAchievements_OnLoaded(generation);ram[0x5372]=24;ram[0x5374]=0x6d;ram[0x5375]=0x6e;ram[0x5376]=1;ram[0x5377]=0x70;SotsAchievements_NotifyVictory();frame();settled();assert(progress("item.dogpill")==0&&progress("route.ship16")==0&&progress("route.jeep24")==0);
 size_t notice;while(SotsAchievements_PopNotice(&notice)){}SotsAchievements_Shutdown();
 assert(SotsAchievements_Init(argv[1]));settled();assert(progress("battle.ten")==10&&progress("walk.1000")==500);assert(!SotsAchievements_PopNotice(&notice));SotsAchievements_Shutdown();
 SotsAchievements_SetDiagnostic(true);assert(SotsAchievements_Init(argv[2]));assert(strstr(SotsAchievements_Status(),"diagnostic"));frame();SotsAchievements_NotifyMapOpen();settled();assert(SotsAchievements_Unlocked()==0&&SotsAchievements_ProfilePath()[0]==0);SotsAchievements_Shutdown();SDL_Quit();puts("PASS: transition guards, committed counters, walking, restore baseline, persistence, diagnostic no-write");return 0;
}

