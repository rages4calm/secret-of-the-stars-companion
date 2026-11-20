#pragma once
#ifndef __ANDROID__
#error "This source-specific host compatibility header is Android-only"
#endif
/* The authored frozen turbo-cadence patch calls the desktop OpenGL policy
 * setter once without its Android guard. That presenter is absent on Android.
 * host_main.c updates its real SDL renderer vsync immediately before this call;
 * leave that path and interval evaluation intact. application.cmake binds this
 * header to the exact reviewed host_main source only, never other game files. */
#define snesrecomp_opengl_set_vsync(interval) ((void)(interval))
