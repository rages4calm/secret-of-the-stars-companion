/* Title-owned host actions. This module never writes guest state. */
#include "foundation_hotkeys.h"
#include "desktop/config.h"
#include "host_main.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned requests;
static int movement_held;
static unsigned test_frame;
static SDL_Joystick *test_pad;
static SDL_JoystickID test_pad_id;
static int test_mode;
static void TestAxis(int axis, int value) {
#if SNESRECOMP_SDL3
    SDL_SetJoystickVirtualAxis(test_pad, axis, value);
#else
    SDL_JoystickSetVirtualAxis(test_pad, axis, value);
#endif
}
static void TestButton(int button, int down) {
#if SNESRECOMP_SDL3
    SDL_SetJoystickVirtualButton(test_pad, button, down != 0);
#else
    SDL_JoystickSetVirtualButton(test_pad, button, down);
#endif
}
void FoundationHotkeysReset(void) {
    requests = 0;
    movement_held = 0;
}
void FoundationHotkeysInit(void) {
    FILE *file = fopen("foundation.ini", "r");
    char line[256], key[96]; int value, toggle = 0, legacy = 1;
    if (file) {
        while (fgets(line, sizeof(line), file)) {
            if (sscanf(line, " %95[^=]=%d", key, &value) != 2) continue;
            size_t len = strlen(key);
            while (len && (key[len-1] == ' ' || key[len-1] == '\t')) key[--len] = 0;
            if (!strcmp(key, "FastForwardToggle")) toggle = value == 1;
            if (!strcmp(key, "LegacyControllerGestures")) legacy = value == 1;
        }
        fclose(file);
    }
    snesrecomp_desktop_set_fast_forward_toggle(toggle);
    snesrecomp_desktop_set_legacy_controller_gestures(legacy);
    if (!legacy) {
        /* Config is read again on the next process; source INI text stays exact. */
        snprintf(g_config.rewind_gesture, sizeof(g_config.rewind_gesture), "none");
        snprintf(g_config.launcher_gesture, sizeof(g_config.launcher_gesture), "none");
    }
    FoundationHotkeysReset();
    const char *test = getenv("SNESRECOMP_FOUNDATION_HOTKEY_INPUT_TEST");
    const char *map_test = getenv("SNESRECOMP_FOUNDATION_MAP_INPUT_TEST");
    if (map_test) test = !strncmp(map_test, "pad", 3) ? "pad" : "keyboard";
    if (!test) test = getenv("SNESRECOMP_FOUNDATION_MOVEMENT_INPUT_TEST");
    test_mode = test && !strcmp(test, "keyboard") ? 1 :
                test && !strcmp(test, "pad") ? 2 :
                test && !strcmp(test, "combined") ? 3 : 0;
    fprintf(stderr, "[foundation] fast-forward mode=%s; hotkeys from config.ini\n",
            toggle ? "toggle" : "hold");
}
/* Finite developer fixtures exercise SDL delivery and the normal resolver.
 * Bind T/R2 to Turbo, M/L2 to MovementBoost, U/R3 to BattleInfo and I/L3
 * to Journal in the isolated test profile. Ordinary launches are inert. */
void FoundationHotkeysBeforeFrame(void) {
    if (!test_mode) return;
    unsigned f = ++test_frame;
    if ((test_mode & 2) && f == 1) {
#if SNESRECOMP_SDL3
        SDL_VirtualJoystickDesc desc;
        SDL_INIT_INTERFACE(&desc);
        desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
        desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
        desc.nbuttons = 15;
        desc.name = "foundation configurable hotkey test controller";
        SDL_JoystickID id = SDL_AttachVirtualJoystick(&desc);
        test_pad_id = id;
        test_pad = id ? SDL_OpenJoystick(id) : NULL;
#else
        int id = SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,
                                          SDL_CONTROLLER_AXIS_MAX, 15, 0);
        test_pad = id >= 0 ? SDL_JoystickOpen(id) : NULL;
#endif
        fprintf(stderr, "[foundation_hotkey_test] virtual pad %s\n", test_pad ? "attached" : "FAILED");
        if (test_pad) {
#if SNESRECOMP_SDL3
            SDL_SetJoystickPlayerIndex(test_pad, 0);
#else
            SDL_JoystickSetPlayerIndex(test_pad, 0);
#endif
            TestAxis(SDL_CONTROLLER_AXIS_TRIGGERLEFT, -32768);
            TestAxis(SDL_CONTROLLER_AXIS_TRIGGERRIGHT, -32768);
            SDL_JoystickUpdate();
        }
    }
    const char *safety = getenv("SNESRECOMP_FOUNDATION_HOTKEY_SAFETY_TEST");
    const char *map_test = getenv("SNESRECOMP_FOUNDATION_MAP_INPUT_TEST");
    if (map_test) {
        int open_only = strstr(map_test, "open") != NULL;
        int reopen = strstr(map_test, "reopen") != NULL;
        /* Finite combined guide/map fixture: first choose a guide town, then
         * open its map. Avoid simultaneous journal/map openers at field30. */
        int from_guide = strstr(map_test, "guide") != NULL;
        if (reopen) open_only = 0;
        int event_frame = (!from_guide && (f == 30 || (f >= 31 && f < 60) || f == 60)) ||
                          (!open_only && (f == 90 || f == 120)) ||
                          (reopen && (f == 130 || f == 140));
        if ((test_mode & 1) && event_frame) {
            SDL_Event event = {0};
            event.type = f == 60 || f == 120 || f == 140 ? SDL_KEYUP : SDL_KEYDOWN;
#if SNESRECOMP_SDL3
            event.key.key = SDLK_m; event.key.repeat = f > 30 && f < 60;
#else
            event.key.keysym.sym = SDLK_m; event.key.repeat = f > 30 && f < 60;
#endif
            SDL_PushEvent(&event);
        }
        if (test_pad && event_frame && !(f > 30 && f < 60)) {
            int down = f == 30 || f == 90 || f == 130;
            TestButton(SDL_CONTROLLER_BUTTON_BACK, down);
            TestButton(SDL_CONTROLLER_BUTTON_LEFTSTICK, down);
            SDL_JoystickUpdate();
        }
        return;
    }
    if (getenv("SNESRECOMP_FOUNDATION_HOTKEY_GESTURE_TEST")) {
        if (test_pad) {
            if (f == 20 || f == 50 || f == 70 || f == 100)
                TestButton(SDL_CONTROLLER_BUTTON_BACK, f == 20 || f == 70);
            if (f == 30 || f == 40)
                TestButton(SDL_CONTROLLER_BUTTON_RIGHTSTICK, f == 30);
            if (f == 80 || f == 90)
                TestButton(SDL_CONTROLLER_BUTTON_RIGHTSHOULDER, f == 80);
            SDL_JoystickUpdate();
        }
        return;
    }
    if (getenv("SNESRECOMP_FOUNDATION_MOVEMENT_INPUT_TEST")) {
        if (f == 10 || f == 130) {
            if (test_pad) {
                TestAxis(SDL_CONTROLLER_AXIS_TRIGGERLEFT, f == 10 ? 32767 : -32768);
                SDL_JoystickUpdate();
            } else {
                SDL_Event event = {0}; event.type = f == 10 ? SDL_KEYDOWN : SDL_KEYUP;
#if SNESRECOMP_SDL3
                event.key.key = SDLK_m;
#else
                event.key.keysym.sym = SDLK_m;
#endif
                SDL_PushEvent(&event);
            }
        }
        return;
    }
    const char *overlay = getenv("SNESRECOMP_FOUNDATION_HOTKEY_OVERLAY_TEST");
    if (overlay) {
        int journal = !strcmp(overlay, "journal");
        int old = f == 10 || f == 11 || f == 15 || f == 16;
        int current = f == 30 || f == 31 || f == 60 || f == 90 || f == 120;
        if (old || ((test_mode & 1) && current)) {
            SDL_Event event = {0};
            event.type = f == 11 || f == 16 || f == 60 || f == 120 ? SDL_KEYUP : SDL_KEYDOWN;
            int key = old ? f < 15 ? SDLK_h : SDLK_j : journal ? SDLK_i : SDLK_u;
#if SNESRECOMP_SDL3
            event.key.key = key; event.key.repeat = f == 31;
#else
            event.key.keysym.sym = key; event.key.repeat = f == 31;
#endif
            SDL_PushEvent(&event);
        }
        if (test_pad && current && f != 31) {
            TestButton(journal ? SDL_CONTROLLER_BUTTON_LEFTSTICK : SDL_CONTROLLER_BUTTON_RIGHTSTICK,
                       f == 30 || f == 90);
            SDL_JoystickUpdate();
        }
        return;
    }
    if ((test_mode & 1) && (f == 20 || f == 25 || f == 40 || f == 60 || f == 70 || f == 90 || f == 95 ||
         f == 100 || f == 110 || f == 130 || f == 140 || f == 141 || f == 150 || f == 151)) {
        if (safety && !strcmp(safety, "overlay") && (f == 90 || f == 95)) return;
        SDL_Event event = {0};
        event.type = f == 40 || f == 70 || f == 95 || f == 130 || f == 141 || f == 151 ? SDL_KEYUP : SDL_KEYDOWN;
        int key = f < 100 ? SDLK_t : f < 140 ? SDLK_m : f < 150 ? SDLK_u : SDLK_i;
        int modifier_test = getenv("SNESRECOMP_FOUNDATION_HOTKEY_MODIFIER_TEST") != NULL;
        if (modifier_test && key == SDLK_m) key = SDLK_LSHIFT;
#if SNESRECOMP_SDL3
        event.key.key = key; event.key.repeat = f == 25 || f == 110;
        event.key.mod = modifier_test && event.type == SDL_KEYDOWN
                        ? key == SDLK_LSHIFT ? KMOD_LSHIFT : key == SDLK_t ? KMOD_CTRL : 0 : 0;
#else
        event.key.keysym.sym = key; event.key.repeat = f == 25 || f == 110;
        event.key.keysym.mod = modifier_test && event.type == SDL_KEYDOWN
                               ? key == SDLK_LSHIFT ? KMOD_LSHIFT : key == SDLK_t ? KMOD_CTRL : 0 : 0;
#endif
        SDL_PushEvent(&event);
    }
    if (test_pad) {
        /* Analog triggers are runtime L2/R2; no extra gameplay buttons. */
        if (f == 30 || f == 50 || f == 60 || f == 70 || f == 90 || f == 95)
            TestAxis(SDL_CONTROLLER_AXIS_TRIGGERRIGHT,
                     f == 30 || f == 60 || f == 90 ? 32767 : -32768);
        if (f == 100 || f == 130)
            TestAxis(SDL_CONTROLLER_AXIS_TRIGGERLEFT, f == 100 ? 32767 : -32768);
        if (f == 140 || f == 141 || f == 150 || f == 151)
            TestButton(f < 150 ? SDL_CONTROLLER_BUTTON_RIGHTSTICK : SDL_CONTROLLER_BUTTON_LEFTSTICK,
                       f == 140 || f == 150);
        SDL_JoystickUpdate();
    }
    if (f == 120) {
        SDL_Event event = {0};
#if SNESRECOMP_SDL3
        event.type = SDL_EVENT_WINDOW_FOCUS_LOST;
#else
        event.type = SDL_WINDOWEVENT; event.window.event = SDL_WINDOWEVENT_FOCUS_LOST;
#endif
        SDL_PushEvent(&event);
    }
    if (safety && strcmp(safety, "overlay") && (f == 155 || f == 156)) {
        if (test_pad) TestAxis(SDL_CONTROLLER_AXIS_TRIGGERRIGHT, f == 155 ? 32767 : -32768);
        else {
            SDL_Event event = {0}; event.type = f == 155 ? SDL_KEYDOWN : SDL_KEYUP;
#if SNESRECOMP_SDL3
            event.key.key = SDLK_t;
#else
            event.key.keysym.sym = SDLK_t;
#endif
            SDL_PushEvent(&event);
        }
        if (test_pad) SDL_JoystickUpdate();
    }
    if (safety && !strcmp(safety, "disconnect") && f == 160 && test_pad) {
        SDL_JoystickClose(test_pad); test_pad = NULL;
#if SNESRECOMP_SDL3
        SDL_DetachVirtualJoystick(test_pad_id);
#endif
        fprintf(stderr, "[foundation_hotkey_test] pad disconnected\n");
    }
    if (safety && (!strcmp(safety, "reset") || !strcmp(safety, "restore")) &&
        (f == 160 || f == 161)) {
        SDL_Event event = {0}; event.type = f == 160 ? SDL_KEYDOWN : SDL_KEYUP;
        int restore = !strcmp(safety, "restore");
#if SNESRECOMP_SDL3
        event.key.key = restore ? SDLK_F2 : SDLK_r;
        event.key.mod = restore ? 0 : KMOD_CTRL;
#else
        event.key.keysym.sym = restore ? SDLK_F2 : SDLK_r;
        event.key.keysym.mod = restore ? 0 : KMOD_CTRL;
#endif
        SDL_PushEvent(&event);
    }
}
void FoundationHotkeysShutdown(void) {
    if (test_pad) { SDL_JoystickClose(test_pad); test_pad = NULL; }
    FoundationHotkeysReset();
}
void FoundationHotkeysCommand(unsigned command, int pressed) {
    if (command == kKeys_MovementBoost) movement_held = pressed != 0;
    else if (pressed && command == kKeys_BattleInfo) requests |= 1;
    else if (pressed && command == kKeys_Journal) requests |= 2;
    else if (pressed && command == kKeys_Map) requests |= 4;
    if (getenv("SNESRECOMP_HOTKEY_TRACE"))
        fprintf(stderr, "[foundation_hotkey] command=%u pressed=%d movement=%d\n",
                command, pressed, movement_held);
}
int FoundationHotkeysMovementHeld(void) { return movement_held; }
int FoundationHotkeysConsumeBattleInfo(void) {
    int result = (requests & 1) != 0; requests &= ~1u; return result;
}
int FoundationHotkeysConsumeJournal(void) {
    int result = (requests & 2) != 0; requests &= ~2u; return result;
}
int FoundationHotkeysConsumeMap(void) {
    int result = (requests & 4) != 0; requests &= ~4u; return result;
}
