/*
 * Secret of the Stars — desktop host shim.
 *
 * Identity and hooks, nothing else. The host itself is the framework's
 * (snesrecomp/runner/src/desktop/host_main.h): the pre-boot launcher, ROM
 * resolution and digest checks, config.ini and keybinds.ini, the window and
 * the SDL / OpenGL presenters, audio, gamepads, the in-game save-state
 * browser and rewind filmstrip, the OSD, the pacing clock, crash handlers and
 * the post-mortem report, mod packages, Generate & rebuild, and the netplay
 * barrier when the project is built with it. A fix there reaches this
 * project on a submodule pull; nothing in this file needs to change for it.
 *
 * This file used to BE the host -- a ~700-line copy made at scaffold time --
 * so every project scaffolded before a fix kept the bug. Two ports of the
 * same game, a week apart, had different hosts.
 *
 * Nothing here ever ships a ROM. The player supplies one; the host makes
 * that easy (launcher, then positional argument, then a copy beside the
 * executable, then the rom.cfg cache, then a file picker) and checks what it
 * is handed against the digests in rom_identity.txt.
 *
 * Grow this file only with what is specific to THIS title: a custom
 * presenter (prepare_frame / draw_frame), an SPC player, a pacing rule
 * (keep_pacing_debt), a Mods provider. See SnesDesktopHostGame for the
 * complete list of hooks and what each is for.
 */

#include "host_main.h"
#include "sots_achievements.h"
#include "foundation_achievements_ui.h"
#include <string.h>
#include <stdlib.h>
#include "game_rtl.h"
#include "desktop/config.h"
#include "foundation_presentation.h"
#include "foundation_diagnostics.h"
#include "foundation_menu.h"
#include "foundation_journal.h"
#include "foundation_map.h"
#include "foundation_map_points.h"
#include "common_rtl.h"
#include "foundation_loading.h"
#include "foundation_clear.h"
#include "foundation_column_lookup.h"
#include "foundation_wide_actors.h"
#include "foundation_hotkeys.h"
#include "foundation_native_backend.h"
#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */

#ifndef __ANDROID__
#define SDL_MAIN_HANDLED 1
#endif
#include "desktop/sdl_compat.h"
#ifdef __ANDROID__
/* SDLActivity loads libmain.so and dlsyms its SDL_main. */
#define main SDL_main
#endif

#ifndef SNES_GAME_VERSION
#define SNES_GAME_VERSION "dev"
#endif

/* This title has one input seat. Ignore a controller's stale SDL player-2
 * preference rather than silently routing it to an unused guest port. */
static void FoundationAfterConfig(void) {
    FoundationHotkeysInit();
    g_config.enable_gamepad[1] = false;
    g_config.player_src[1] = 0;
    FoundationPresentationInit();
    FoundationMenuInit();
    FoundationJournalInit();
    FoundationMapInit();
    FoundationMapPointsInit();
    FoundationLoadingInit();
    FoundationClearInit();
    FoundationColumnLookupInit();
    FoundationWideActorsInit();
}

static int achievement_started;
static void FoundationBeforeFrame(void) {
    FoundationAchievementsBeforeFrame();
    FoundationHotkeysBeforeFrame();
    FoundationPresentationBeforeFrame();
    FoundationJournalBeforeFrame();
    FoundationMapBeforeFrame();
    FoundationLoadingBeforeFrame();
    FoundationClearBeforeFrame();
    FoundationColumnLookupBeforeFrame();
    FoundationWideActorsBeforeFrame();
    FoundationNativeBackendBeforeFrame();
}
static void FoundationAfterFrame(const SnesDesktopHostFrameStats *stats) {
    if(!achievement_started){
        const char *base=SDL_GetBasePath();
        SotsAchievements_Init(base);achievement_started=1;
#if !SNESRECOMP_SDL3
        SDL_free((void *)base);
#endif
    }
    SotsAchievements_Observe(g_ram,0x20000,RtlStateGeneration(),!RtlSpeculativeFrame());
    FoundationPresentationAfterFrame(stats);
    FoundationJournalAfterFrame(stats);
    FoundationMapAfterFrame(stats);
    FoundationMapPointsAfterFrame((int)FoundationJournalDestinationState(g_ram, 0x20000));
}
static void FoundationReset(void) {
    SotsAchievements_OnLoaded(RtlStateGeneration());
    FoundationNativeBackendReset();
    FoundationHotkeysReset();
    FoundationPresentationReset();
    FoundationJournalReset();
    FoundationMapReset();
    FoundationMapPointsReset();
    FoundationLoadingReset();
    FoundationClearReset();
    FoundationColumnLookupReset();
}
static void FoundationShutdown(void) {
    FoundationAchievementsUIShutdown();
    SotsAchievements_Shutdown();
    FoundationHotkeysShutdown();
    FoundationLoadingShutdown();
    FoundationClearShutdown();
    FoundationColumnLookupShutdown();
    FoundationWideActorsShutdown();
    FoundationJournalShutdown();
    FoundationMapShutdown();
    FoundationPresentationShutdown();
}

static const SnesDesktopHostGame kGameHost = {
    .display_name        = "Secret of the Stars",
    .window_title        = "Secret of the Stars",
    .region              = SNESRECOMP_ROM_REGION,
    .rom_file            = SNESRECOMP_ROM_FILE,
    .expected_sha256_hex = SNESRECOMP_ROM_EXPECTED_SHA256,
    .expected_crc32_hex  = SNESRECOMP_ROM_EXPECTED_CRC32,
    .game_id             = SNESRECOMP_ROM_GAME_ID,
    .build_version       = SNES_GAME_VERSION,
    .game_info           = &kGameInfo,
    .num_players         = 1,
    .after_config        = FoundationAfterConfig,
    .on_rom_loaded       = FoundationNativeBackendOnRom,
    .before_run_frame    = FoundationBeforeFrame,
    .on_reset            = FoundationReset,
    .on_shutdown         = FoundationShutdown,
    .native_widescreen   = 1,
    .prepare_frame       = FoundationPresentationPrepare,
    .after_run_frame     = FoundationAfterFrame,
    .end_sim_frame       = FoundationDiagnosticsRendered,
    .draw_frame          = FoundationPresentationDraw,
    .presentation_scale  = FoundationPresentationScale,
    .title_hotkey        = FoundationHotkeysCommand,
    /* Battery-backed SRAM shows the launcher's SAVES panel. Leave NULL for a
     * title without one. The path is exe-relative. */
    .sram_path           = "saves/save.srm",
};

#ifndef __ANDROID__
#undef main   /* desktop: keep plain main() even if SDL_main.h remapped it */
#endif
int main(int argc, char **argv)
{
    int achievement_diagnostic=0;
    for(int i=1;i<argc;++i)if(!strcmp(argv[i],"--script")||!strncmp(argv[i],"--script=",9))achievement_diagnostic=1;
    SotsAchievements_SetDiagnostic(achievement_diagnostic!=0);
    FoundationNativeBackendConfigure();
    ConfigUseFoundationHotkeyDefaults();
    return snesrecomp_desktop_main(&kGameHost, argc, argv);
}
