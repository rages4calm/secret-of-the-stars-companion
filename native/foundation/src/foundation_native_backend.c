/* Architectural native programs adapted from Lagoon native69.
 * Existing feature callbacks and reviewed native services retain priority.
 * Original ROM and actual runtime image are attested separately; no saved
 * state layout, original game content or physical device owner changes here. */
#include "foundation_native_backend.h"
#include "native_blocks.h"
#include "snes/interp_bridge.h"
#include "snes/snes.h"
#include "common_rtl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern Snes *g_snes;
extern const NativeBlockProgram sots_arch78_program;
static int requested,registered,bound;
static uint64_t generation;
static const uint8_t *image;
static size_t image_size;
static void refused(const char *reason) {
 fprintf(stderr,"[native-arch78] refused reason=%s\n",reason);fflush(stderr);_Exit(87);
}
void FoundationNativeBackendConfigure(void) {
 const char *value=getenv("SOTS_ARCH_NATIVE");
 if(!value) {
#ifdef _WIN32
  if(_putenv_s("SOTS_ARCH_NATIVE","1"))refused("policy-default");
#else
  if(setenv("SOTS_ARCH_NATIVE","1",0))refused("policy-default");
#endif
  value=getenv("SOTS_ARCH_NATIVE");
 }
 if(!value || (strcmp(value,"0")&&strcmp(value,"1")))refused("invalid-backend-policy");
 requested=!strcmp(value,"1");
 const char *strict=getenv("SNESRECOMP_NATIVE_ONLY");
 if(strict&&strcmp(strict,"0")&&strcmp(strict,"1"))refused("invalid-strict-policy");
 if(strict&&!strcmp(strict,"1")&&!requested)refused("strict-with-backend-disabled");
}
void FoundationNativeBackendOnRom(const uint8_t *rom,size_t size) {
 FoundationNativeBackendConfigure();
 interp_bridge_clear_native_program();registered=bound=0;image=NULL;image_size=0;
 if(!requested)return;
 const NativeBlockProgram *programs[]={&sots_arch78_program};
 if(!interp_bridge_register_native_programs(programs,1,rom,size))refused("original-source-registration");
 registered=1;
 fprintf(stderr,"[native-arch78] registered keys=%zu source=%s\n",sots_arch78_program.instruction_count,sots_arch78_program.source_sha256);
}
void FoundationNativeBackendReset(void) {bound=0;image=NULL;image_size=0;}
void FoundationNativeBackendBeforeFrame(void) {
 if(!requested)return;
 if(!registered||!g_snes||!g_snes->cart||!g_rom)refused("runtime-image-unavailable");
 uint64_t next=RtlStateGeneration();size_t size=g_snes->cart->romImageSize;
 if(!bound||generation!=next||image!=g_rom||image_size!=size) {
  if(!interp_bridge_bind_native_program(&sots_arch78_program,g_rom,size,next)) {
   const char *strict=getenv("SNESRECOMP_NATIVE_ONLY");
   if(strict&&!strcmp(strict,"1"))refused("runtime-source-binding");
   interp_bridge_clear_native_program();bound=0;requested=0;
   fprintf(stderr,"[native-arch78] source mismatch; existing guarded execution retained\n");return;
  }
  image=g_rom;image_size=size;generation=next;bound=1;
  fprintf(stderr,"[native-arch78] bound generation=%llu\n",(unsigned long long)generation);
 }
}
