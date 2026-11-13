/* Local host-only CompanionAchievements adapter, adapted from Lagoon.
 * The unchanged MIT core commits before notices. All storage runs on one worker;
 * the game frame only publishes immutable events. No guest/time/state writes. */
#include "sots_achievements.h"
#include "sots_achievements_catalog.generated.h"
#include "common_rtl.h"
#include "desktop/sdl_compat.h"
#include "cJSON.h"
#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#define SOTS_HOST_WINDOWS_PATHS 1
#else
#include <sys/stat.h>
#include <sys/file.h>
#include <fcntl.h>
#include <unistd.h>
#define SOTS_HOST_WINDOWS_PATHS 0
#endif
#if SNESRECOMP_SDL3
typedef SDL_Mutex AchMutex;
typedef SDL_Condition AchCondition;
#define AchCreateCondition SDL_CreateCondition
#define AchDestroyCondition SDL_DestroyCondition
#define AchWaitCondition SDL_WaitCondition
#define AchWaitConditionTimeout SDL_WaitConditionTimeout
#define AchSignalCondition SDL_SignalCondition
#define AchBroadcastCondition SDL_BroadcastCondition
#else
typedef SDL_mutex AchMutex;
typedef SDL_cond AchCondition;
#define AchCreateCondition SDL_CreateCond
#define AchDestroyCondition SDL_DestroyCond
#define AchWaitCondition SDL_CondWait
#define AchWaitConditionTimeout SDL_CondWaitTimeout
#define AchSignalCondition SDL_CondSignal
#define AchBroadcastCondition SDL_CondBroadcast
#endif

enum { PATH_CAP=4096, UNKNOWN_CAP=64, EVENT_CAP=32 };
enum Status { OFF, INITIALIZING, READY, DIAGNOSTIC, IO_ERROR, CORRUPT, LOCKED, WORKER_ERROR };
typedef struct SotsUnknownAchievement {char id[81];uint32_t progress;uint64_t when;} SotsUnknownAchievement;
typedef struct Event {const char *name;uint32_t amount;uint64_t when;} Event;
typedef struct Snapshot {uint8_t item_mask,party,chapter;} Snapshot;
static struct {
 ca_engine engine;ca_state published[CA_MAX_ACHIEVEMENTS];
 AchMutex *mutex;AchCondition *condition;SDL_Thread *thread;
 Event events[EVENT_CAP];unsigned pending;
 size_t notices[CA_MAX_ACHIEVEMENTS],notice_read,notice_count;
 size_t newly_unlocked[CA_MAX_ACHIEVEMENTS],new_count;
 SotsUnknownAchievement unknown[UNKNOWN_CAP];size_t unknown_count;
 char directory[PATH_CAP],profile[PATH_CAP];enum Status status;
 bool stop,busy,tracking,baseline,observed_ready,battle_armed,walk_pending,position_valid;
 uint64_t generation;Snapshot previous;unsigned mode,scene,position_party,walk_pixels;
 int x,y;
#ifdef _WIN32
 HANDLE lock;
#else
 int lock;
#endif
} a;
static bool requested_diagnostic;
static bool separator(char c){return c=='/'||(SOTS_HOST_WINDOWS_PATHS&&c=='\\');}
static bool present(const char *name){const char *p=getenv(name);return p&&*p&&strcmp(p,"0");}
#ifdef _WIN32
static bool wide(const char*p,wchar_t*out){return MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,p,-1,out,PATH_CAP)!=0;}
static FILE *open_file(const char*p,const wchar_t*mode){wchar_t w[PATH_CAP];return wide(p,w)?_wfopen(w,mode):NULL;}
static bool directory_one(const char*p){wchar_t w[PATH_CAP];if(!wide(p,w))return false;DWORD attr=GetFileAttributesW(w);if(attr!=INVALID_FILE_ATTRIBUTES)return (attr&FILE_ATTRIBUTE_DIRECTORY)&&!(attr&FILE_ATTRIBUTE_REPARSE_POINT);return CreateDirectoryW(w,NULL)!=0;}
static bool regular_target(const char*p){wchar_t w[PATH_CAP];if(!wide(p,w))return false;DWORD attr=GetFileAttributesW(w);return attr==INVALID_FILE_ATTRIBUTES?GetLastError()==ERROR_FILE_NOT_FOUND:!(attr&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT));}
#else
static FILE *open_file(const char*p,const char*mode){return fopen(p,mode);}
static bool directory_one(const char*p){struct stat s;if(lstat(p,&s)==0)return S_ISDIR(s.st_mode)&&!S_ISLNK(s.st_mode);return errno==ENOENT&&mkdir(p,0700)==0;}
static bool regular_target(const char*p){struct stat s;if(lstat(p,&s)==0)return S_ISREG(s.st_mode)&&!S_ISLNK(s.st_mode);return errno==ENOENT;}
#endif
static bool directories(const char*path){
  char p[PATH_CAP];size_t n=strlen(path);if(!n||n>=PATH_CAP-64)return false;
#ifdef _WIN32
  if(!((n>=3&&path[1]==':'&&(path[2]=='/'||path[2]=='\\'))||(n>=5&&path[0]=='\\'&&path[1]=='\\')))return false;
#else
  if(path[0]!='/')return false;
#endif
  memcpy(p,path,n+1);unsigned unc=SOTS_HOST_WINDOWS_PATHS&&path[0]=='\\'&&path[1]=='\\'?2:0;
  for(size_t i=1;i<n;i++)if(separator(p[i])){
    if(SOTS_HOST_WINDOWS_PATHS&&i==2&&p[1]==':')continue;
    if(separator(p[i-1]))continue;
    if(unc){--unc;continue;}char c=p[i];p[i]=0;bool ok=directory_one(p);p[i]=c;if(!ok)return false;
  }
  return directory_one(p);
}
static bool acquire_lock(void){
  char path[PATH_CAP];if(snprintf(path,sizeof path,"%s.lock",a.profile)>=(int)sizeof path||!regular_target(path))return false;
#ifdef _WIN32
  wchar_t w[PATH_CAP];if(!wide(path,w))return false;
  a.lock=CreateFileW(w,GENERIC_READ|GENERIC_WRITE,0,NULL,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);return a.lock!=INVALID_HANDLE_VALUE;
#else
  a.lock=open(path,O_RDWR|O_CREAT,0600);if(a.lock<0)return false;if(flock(a.lock,LOCK_EX|LOCK_NB)==0)return true;close(a.lock);a.lock=-1;return false;
#endif
}
static void release_lock(void){
#ifdef _WIN32
  if(a.lock!=INVALID_HANDLE_VALUE)CloseHandle(a.lock);a.lock=INVALID_HANDLE_VALUE;
#else
  if(a.lock>=0)close(a.lock);a.lock=-1;
#endif
}
static bool integer(const cJSON*x,double maximum){return cJSON_IsNumber(x)&&isfinite(x->valuedouble)&&x->valuedouble>=0&&x->valuedouble<=maximum&&floor(x->valuedouble)==x->valuedouble;}
static bool object_keys(const cJSON*x,const char*const*keys,size_t count){
  if(!cJSON_IsObject(x))return false;unsigned seen=0;size_t actual=0;
  for(cJSON*c=x->child;c;c=c->next){size_t k=0;for(;k<count;k++)if(c->string&&!strcmp(c->string,keys[k]))break;if(k==count||(seen&(1u<<k)))return false;seen|=1u<<k;actual++;}
  return actual==count;
}
static bool logical_id(const char*p){if(!p||!*p||strlen(p)>80)return false;for(;*p;p++)if(!((*p>='a'&&*p<='z')||(*p>='0'&&*p<='9')||*p=='-'||*p=='_'||*p=='.'))return false;return true;}
static size_t definition_index(const char*id){size_t i=0;for(;i<a.engine.count;i++)if(!strcmp(id,sots_definitions[i].id))break;return i;}
static bool restore(FILE*f){
  char text[32769];size_t n=fread(text,1,sizeof text-1,f);if(ferror(f)||!feof(f)||n==sizeof text-1)return false;text[n]=0;
  if(memchr(text,0,n)||strstr(text,"\\u0000"))return false;
  const char*end=NULL;cJSON*r=cJSON_ParseWithLengthOpts(text,n+1,&end,1);if(!r)return false;
  const char*keys[]={"schemaVersion","gameId","editionId","seedId","catalogVersion","achievements"};
  const char*itemkeys[]={"id","progress","unlockedAt"};
  cJSON*schema=cJSON_GetObjectItemCaseSensitive(r,"schemaVersion"),*game=cJSON_GetObjectItemCaseSensitive(r,"gameId"),*edition=cJSON_GetObjectItemCaseSensitive(r,"editionId"),*seed=cJSON_GetObjectItemCaseSensitive(r,"seedId"),*version=cJSON_GetObjectItemCaseSensitive(r,"catalogVersion"),*items=cJSON_GetObjectItemCaseSensitive(r,"achievements");
  bool ok=object_keys(r,keys,6)&&integer(schema,1)&&schema->valuedouble==1&&cJSON_IsString(game)&&!strcmp(game->valuestring,SOTS_GAME_ID)&&cJSON_IsString(edition)&&!strcmp(edition->valuestring,SOTS_EDITION_ID)&&cJSON_IsNull(seed)&&integer(version,SOTS_CATALOG_VERSION)&&version->valuedouble>=1&&cJSON_IsArray(items);
  char seen[CA_MAX_ACHIEVEMENTS+UNKNOWN_CAP][81];size_t seen_count=0;
  for(cJSON*i=items?items->child:NULL;ok&&i;i=i->next){
    cJSON*id=cJSON_GetObjectItemCaseSensitive(i,"id"),*p=cJSON_GetObjectItemCaseSensitive(i,"progress"),*t=cJSON_GetObjectItemCaseSensitive(i,"unlockedAt");
    ok=object_keys(i,itemkeys,3)&&cJSON_IsString(id)&&logical_id(id->valuestring)&&integer(p,UINT32_MAX)&&integer(t,253402300799.0)&&seen_count<CA_MAX_ACHIEVEMENTS+UNKNOWN_CAP;
    if(!ok)break;for(size_t k=0;k<seen_count;k++)if(!strcmp(seen[k],id->valuestring)){ok=false;break;}if(!ok)break;
    strcpy(seen[seen_count++],id->valuestring);size_t index=definition_index(id->valuestring);
    if(index<a.engine.count)ok=ca_restore(&a.engine,id->valuestring,(uint32_t)p->valuedouble,(uint64_t)t->valuedouble);
    else if(a.unknown_count==UNKNOWN_CAP)ok=false;
    else{SotsUnknownAchievement*u=a.unknown+a.unknown_count++;strcpy(u->id,id->valuestring);u->progress=(uint32_t)p->valuedouble;u->when=(uint64_t)t->valuedouble;}
  }
  cJSON_Delete(r);return ok;
}
static bool store(void*context,const ca_state*states,size_t count){
#ifdef SOTS_ACHIEVEMENTS_TEST
  extern void SotsAchievements_TestBeforeCommit(void);
  SotsAchievements_TestBeforeCommit();
#endif
  (void)context;cJSON*r=cJSON_CreateObject(),*items=cJSON_CreateArray();if(!r||!items){cJSON_Delete(r);cJSON_Delete(items);return false;}
  cJSON_AddNumberToObject(r,"schemaVersion",1);cJSON_AddStringToObject(r,"gameId",SOTS_GAME_ID);cJSON_AddStringToObject(r,"editionId",SOTS_EDITION_ID);cJSON_AddNullToObject(r,"seedId");cJSON_AddNumberToObject(r,"catalogVersion",SOTS_CATALOG_VERSION);if(!cJSON_AddItemToObject(r,"achievements",items)){cJSON_Delete(items);cJSON_Delete(r);return false;}
  for(size_t i=0;i<count+a.unknown_count;i++){
    cJSON*x=cJSON_CreateObject();if(!x){cJSON_Delete(r);return false;}if(!cJSON_AddItemToArray(items,x)){cJSON_Delete(x);cJSON_Delete(r);return false;}
    cJSON_AddStringToObject(x,"id",i<count?sots_definitions[i].id:a.unknown[i-count].id);
    cJSON_AddNumberToObject(x,"progress",i<count?states[i].progress:a.unknown[i-count].progress);
    cJSON_AddNumberToObject(x,"unlockedAt",(double)(i<count?states[i].unlocked_at:a.unknown[i-count].when));
  }
  const char*rootkeys[]={"schemaVersion","gameId","editionId","seedId","catalogVersion","achievements"};const char*itemkeys[]={"id","progress","unlockedAt"};
  bool complete=object_keys(r,rootkeys,6)&&(size_t)cJSON_GetArraySize(items)==count+a.unknown_count;for(cJSON*i=items->child;complete&&i;i=i->next)complete=object_keys(i,itemkeys,3);
  char*data=complete?cJSON_PrintUnformatted(r):NULL;cJSON_Delete(r);if(!data)return false;
  char temp[PATH_CAP];bool ok=snprintf(temp,sizeof temp,"%s.tmp",a.profile)<(int)sizeof temp&&regular_target(a.profile)&&regular_target(temp);FILE*f=NULL;
#ifdef _WIN32
  if(ok)f=open_file(temp,L"wb");
#else
  if(ok)f=open_file(temp,"wb");
#endif
  if(f){size_t length=strlen(data);ok=fwrite(data,1,length,f)==length&&fflush(f)==0;
#ifdef _WIN32
    if(ok)ok=_commit(_fileno(f))==0;
#else
    if(ok)ok=fsync(fileno(f))==0;
#endif
    if(fclose(f))ok=false;
    if(ok){
#ifdef _WIN32
      wchar_t from[PATH_CAP],to[PATH_CAP];ok=wide(temp,from)&&wide(a.profile,to)&&MoveFileExW(from,to,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH);
#else
      ok=rename(temp,a.profile)==0;
#endif
    }
  }else ok=false;
  cJSON_free(data);return ok;
}
static void notify(void*context,const ca_definition*d,const ca_state*s){(void)context;(void)s;if(a.new_count<CA_MAX_ACHIEVEMENTS)a.newly_unlocked[a.new_count++]=(size_t)(d-sots_definitions);}

static void publish_status(enum Status status,bool tracking){
 SDL_LockMutex(a.mutex);a.status=status;a.tracking=tracking;SDL_UnlockMutex(a.mutex);
}
static bool start_storage(void){
 if(!directories(a.directory)||!regular_target(a.profile)){publish_status(IO_ERROR,false);return false;}
 if(!acquire_lock()){publish_status(LOCKED,false);return false;}
 errno=0;
#ifdef _WIN32
 FILE *f=open_file(a.profile,L"rb");
#else
 FILE *f=open_file(a.profile,"rb");
#endif
 bool ok=f?restore(f):errno==ENOENT;if(f)fclose(f);
 if(!ok){release_lock();publish_status(CORRUPT,false);return false;}
 if(!f&&!store(NULL,a.engine.states,a.engine.count)){release_lock();publish_status(IO_ERROR,false);return false;}
 SDL_LockMutex(a.mutex);memcpy(a.published,a.engine.states,sizeof a.published);a.tracking=true;a.status=READY;a.busy=false;AchBroadcastCondition(a.condition);SDL_UnlockMutex(a.mutex);return true;
}
static int worker(void *unused){
 (void)unused;if(!start_storage()){SDL_LockMutex(a.mutex);a.busy=false;AchBroadcastCondition(a.condition);SDL_UnlockMutex(a.mutex);return 0;}
 for(;;){
  SDL_LockMutex(a.mutex);while(!a.stop&&!a.pending)AchWaitCondition(a.condition,a.mutex);
  if(a.stop&&!a.pending){SDL_UnlockMutex(a.mutex);break;}
  unsigned slot=0;while(slot<EVENT_CAP&&!a.events[slot].name)slot++;
  Event event=a.events[slot];a.events[slot].name=NULL;--a.pending;a.busy=true;bool tracking=a.tracking;SDL_UnlockMutex(a.mutex);
  a.new_count=0;bool ok=!tracking||ca_event(&a.engine,event.name,event.amount,event.when);
  SDL_LockMutex(a.mutex);
  if(ok){memcpy(a.published,a.engine.states,sizeof a.published);for(size_t i=0;i<a.new_count&&a.notice_count<CA_MAX_ACHIEVEMENTS;i++)a.notices[(a.notice_read+a.notice_count++)%CA_MAX_ACHIEVEMENTS]=a.newly_unlocked[i];}
  else{a.tracking=false;a.status=IO_ERROR;memset(a.events,0,sizeof a.events);a.pending=0;}
  a.busy=false;AchBroadcastCondition(a.condition);SDL_UnlockMutex(a.mutex);
 }
 return 0;
}
static void queue_event(const char *name,uint32_t amount){
 time_t now=time(NULL);if(now<=0||!a.mutex||!amount)return;
 bool counter=false;for(size_t i=0;i<SOTS_ACHIEVEMENT_COUNT;i++)if(!strcmp(name,sots_definitions[i].event)&&sots_definitions[i].rule==CA_COUNTER){counter=true;break;}
 SDL_LockMutex(a.mutex);
 if(a.tracking){
  unsigned slot=0;for(;slot<EVENT_CAP;slot++)if(a.events[slot].name&&!strcmp(a.events[slot].name,name))break;
  if(slot<EVENT_CAP){if(counter){uint32_t old=a.events[slot].amount;a.events[slot].amount=UINT32_MAX-old<amount?UINT32_MAX:old+amount;}else if(amount>a.events[slot].amount)a.events[slot].amount=amount;}
  else{for(slot=0;slot<EVENT_CAP&&a.events[slot].name;slot++){}if(slot<EVENT_CAP){a.events[slot]=(Event){name,amount,(uint64_t)now};++a.pending;}else{a.tracking=false;a.status=WORKER_ERROR;}}
  AchSignalCondition(a.condition);
 }
 SDL_UnlockMutex(a.mutex);
}
void SotsAchievements_SetDiagnostic(bool value){requested_diagnostic=value;}
bool SotsAchievements_Init(const char *root){
 fprintf(stderr,"[SOTS_ACHIEVEMENTS_V1] local host tracking\n");
 SotsAchievements_Shutdown();memset(&a,0,sizeof a);
#ifdef _WIN32
 a.lock=INVALID_HANDLE_VALUE;
#else
 a.lock=-1;
#endif
 a.mutex=SDL_CreateMutex();a.condition=AchCreateCondition();
 if(!a.mutex||!a.condition){a.status=WORKER_ERROR;return false;}
 if(!ca_init(&a.engine,sots_definitions,SOTS_ACHIEVEMENT_COUNT,store,notify,NULL)){a.status=WORKER_ERROR;return false;}
 bool diagnostic=requested_diagnostic||present("SNESRECOMP_SCRIPT")||present("SNESRECOMP_RUN_FRAMES")||present("SOTS_ACHIEVEMENTS_DIAGNOSTIC")||present("SNESRECOMP_FOUNDATION_STAGED");
 if(diagnostic){a.status=DIAGNOSTIC;return true;}
 if(!root||!*root||!((SOTS_HOST_WINDOWS_PATHS&&strlen(root)>=3&&((root[1]==':'&&separator(root[2]))||(root[0]=='\\'&&root[1]=='\\')))||(!SOTS_HOST_WINDOWS_PATHS&&root[0]=='/'))||
    snprintf(a.directory,sizeof a.directory,"%s/Achievements/%s/%s/unseeded",root,SOTS_GAME_ID,SOTS_EDITION_ID)>=(int)sizeof a.directory||
    snprintf(a.profile,sizeof a.profile,"%s/progress.json",a.directory)>=(int)sizeof a.profile){a.status=IO_ERROR;return false;}
 a.status=INITIALIZING;a.busy=true;a.thread=SDL_CreateThread(worker,"SOTS achievements",NULL);
 if(!a.thread){a.busy=false;a.status=WORKER_ERROR;return false;}return true;
}
void SotsAchievements_Shutdown(void){
 if(a.thread){SDL_LockMutex(a.mutex);a.stop=true;AchSignalCondition(a.condition);SDL_UnlockMutex(a.mutex);SDL_WaitThread(a.thread,NULL);a.thread=NULL;}
 if(a.profile[0])release_lock();if(a.condition)AchDestroyCondition(a.condition);if(a.mutex)SDL_DestroyMutex(a.mutex);
 a.condition=NULL;a.mutex=NULL;a.tracking=false;a.status=OFF;
}
void SotsAchievements_OnLoaded(uint64_t generation){a.baseline=a.observed_ready=a.battle_armed=a.walk_pending=a.position_valid=false;a.generation=generation;a.walk_pixels=0;a.mode=0;}
static unsigned word(const uint8_t *r,unsigned at){return r[at]|(unsigned)r[at+1]<<8;}
static bool snapshot(const uint8_t *r,size_t size,Snapshot *s){
 /* Exact original idle field/party/chapter guards from foundation_current_data.h. */
 if(!r||size<0x53b3||r[0x20]!=1||(r[0x4b6]!=0&&r[0x4b6]!=0x80)||r[0x5372]>24||r[0x434]||r[0x435]||r[0x532]||r[0x1410]||r[0x1411]||r[0x1415]||r[0x1416]||r[0x1417])return false;
 s->party=r[0x4b6];s->chapter=r[0x5372];s->item_mask=0;
 static const uint8_t items[]={0x00,0x6d,0x6e,0x01,0x70};
 for(unsigned i=0;i<5;i++)for(unsigned slot=0;slot<64;slot++)if(r[0x5373+slot]==items[i]){s->item_mask|=(uint8_t)(1u<<i);break;}
 return true;
}
static bool position(const uint8_t *r,int *x,int *y){
 /* Original navigation anchor, identical to FoundationMapPosition's reader. */
 if(!(r[0x401]&4)||r[0x4000]>3||(r[0x4005]&3)||!r[0x46d]||!r[0x46e]||r[0x46d]>15||r[0x46e]>15||word(r,0x471)||word(r,0x473))return false;
 *x=(int16_t)word(r,0x2ad)+(r[0x4001]&0xf0);*y=(int16_t)word(r,0x2af)+(r[0x4002]&0xf0);
 int w=r[0x46d]*256,h=r[0x46e]*256;if(r[0x407]){*x%=w;*y%=h;if(*x<0)*x+=w;if(*y<0)*y+=h;}
 return *x>=0&&*y>=0&&*x<w&&*y<h;
}
static bool tracking(void){bool value=false;if(a.mutex){SDL_LockMutex(a.mutex);value=a.tracking;SDL_UnlockMutex(a.mutex);}return value;}
static bool current(void){return !RtlSpeculativeFrame()&&tracking()&&a.baseline&&a.generation==RtlStateGeneration();}
void SotsAchievements_Observe(const uint8_t *r,size_t size,uint64_t generation,bool eligible){
 if(!eligible||!r||size<0x53b3||!tracking()){a.observed_ready=false;a.position_valid=false;a.walk_pending=false;return;}
 if(generation!=a.generation)SotsAchievements_OnLoaded(generation);
 unsigned mode=r[0x20];
 if(mode==5&&a.mode==1&&a.baseline)a.battle_armed=true;
 if(mode!=5&&a.mode==5)a.battle_armed=false;
 a.mode=mode;Snapshot s;
 if(!snapshot(r,size,&s)){a.observed_ready=false;a.position_valid=false;a.walk_pending=false;return;}
 if(!a.baseline||s.chapter<a.previous.chapter){a.baseline=true;a.previous=s;a.position_valid=false;a.walk_pixels=0;a.battle_armed=false;a.walk_pending=false;}
 else{
  static const char *events[]={"item.starcrest","item.dogpill","item.graviton","item.winkey","item.moustache"};
  for(unsigned i=0;i<5;i++)if(!(a.previous.item_mask&(1u<<i))&&(s.item_mask&(1u<<i)))queue_event(events[i],1);
  if(s.party!=a.previous.party)queue_event("party.swap",1);
  if(s.chapter==(unsigned)a.previous.chapter+1){switch(s.chapter){case 6:queue_event("route.town6",1);break;case 12:queue_event("route.east12",1);break;case 16:queue_event("route.ship16",1);break;case 24:queue_event("route.jeep24",1);break;default:break;}}
 }
 int x,y;unsigned scene=word(r,0x40e);
 if(position(r,&x,&y)){
  if(a.walk_pending&&a.position_valid&&a.scene==scene&&a.position_party==s.party){
   int dx=x-a.x,dy=y-a.y;
   if(r[0x407]){int w=r[0x46d]*256,h=r[0x46e]*256;if(dx>w/2)dx-=w;if(dx< -w/2)dx+=w;if(dy>h/2)dy-=h;if(dy< -h/2)dy+=h;}
   unsigned distance=(unsigned)(abs(dx)+abs(dy));
   /* BeforeCoherentWalkVectors accepts1..3 original pixels; supported boost
    * up to300percent produces at most9actual pixels, axis-aligned. */
   if((!dx||!dy)&&distance&&distance<=9){a.walk_pixels+=distance;if(a.walk_pixels>=16){queue_event("travel.steps",a.walk_pixels/16);a.walk_pixels%=16;}}
  }
  if(!a.position_valid||a.scene!=scene||a.position_party!=s.party)a.walk_pixels=0;
  a.x=x;a.y=y;a.scene=scene;a.position_party=s.party;a.position_valid=true;
 }else{a.position_valid=false;a.walk_pixels=0;}
 a.walk_pending=false;a.previous=s;a.observed_ready=true;
}
void SotsAchievements_NotifyVictory(void){if(current()&&a.battle_armed&&a.mode==5){a.battle_armed=false;queue_event("battle.victories",1);}}
void SotsAchievements_NotifyWalk(void){if(current()&&a.mode==1)a.walk_pending=true;}
void SotsAchievements_NotifyMapOpen(void){if(current()&&a.observed_ready&&a.mode==1)queue_event("ui.map",1);}
void SotsAchievements_NotifyGuideOpen(void){if(current()&&a.observed_ready&&a.mode==1)queue_event("ui.guide",1);}
size_t SotsAchievements_Count(void){return SOTS_ACHIEVEMENT_COUNT;}
bool SotsAchievements_GetEntry(size_t i,SotsAchievementEntry *out){
 if(!out||i>=SOTS_ACHIEVEMENT_COUNT)return false;ca_state s={0};if(a.mutex){SDL_LockMutex(a.mutex);s=a.published[i];SDL_UnlockMutex(a.mutex);}const ca_definition *d=sots_definitions+i;*out=(SotsAchievementEntry){d->id,d->title,d->description,s.progress,d->target,s.unlocked_at};return true;
}
size_t SotsAchievements_Unlocked(void){size_t n=0;if(a.mutex){SDL_LockMutex(a.mutex);for(size_t i=0;i<SOTS_ACHIEVEMENT_COUNT;i++)n+=a.published[i].unlocked_at!=0;SDL_UnlockMutex(a.mutex);}return n;}
const char *SotsAchievements_Status(void){enum Status s=OFF;if(a.mutex){SDL_LockMutex(a.mutex);s=a.status;SDL_UnlockMutex(a.mutex);}static const char *text[]={"Achievements unavailable","Loading local achievements","Tracking locally","Tracking disabled for this diagnostic session","Progress could not be saved; gameplay continues","Progress unreadable or unsupported; file preserved","Another game copy owns achievement progress","Achievement worker unavailable; gameplay continues"};return text[s<=WORKER_ERROR?s:OFF];}
const char *SotsAchievements_ProfilePath(void){return a.profile;}
bool SotsAchievements_PopNotice(size_t *index){if(!index||!a.mutex)return false;SDL_LockMutex(a.mutex);bool found=a.notice_count!=0;if(found){*index=a.notices[a.notice_read];a.notice_read=(a.notice_read+1)%CA_MAX_ACHIEVEMENTS;--a.notice_count;}SDL_UnlockMutex(a.mutex);return found;}
bool SotsAchievements_WaitIdle(unsigned timeout){if(!a.mutex)return true;uint32_t start=SDL_GetTicks();SDL_LockMutex(a.mutex);while(a.pending||a.busy){uint32_t elapsed=SDL_GetTicks()-start;if(elapsed>=timeout){SDL_UnlockMutex(a.mutex);return false;}AchWaitConditionTimeout(a.condition,a.mutex,timeout-elapsed);}SDL_UnlockMutex(a.mutex);return true;}
