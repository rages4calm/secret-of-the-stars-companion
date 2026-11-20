# Android SDLActivity loads libmain.so; desktop targets remain executables.
function(sots_add_application target)
    if(ANDROID)
        # Our frozen turbo-cadence patch retained one desktop-only OpenGL
        # policy call. Android uses the SDL renderer's actual vsync update.
        set(_sots_host_main "${SNESRECOMP_ROOT}/runner/src/desktop/host_main.c")
        file(SHA256 "${_sots_host_main}" _sots_host_main_sha)
        if(NOT _sots_host_main_sha STREQUAL "71726831fa08da3d8bd99cbd0144ffdcd39292e0ba0f4f3713bfd15f2f918804")
            message(FATAL_ERROR "Android host compatibility input changed; review host_main.c before updating this guard")
        endif()
        set_property(SOURCE "${_sots_host_main}" APPEND PROPERTY COMPILE_OPTIONS
            "-include" "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/android_host_compat.h")
        # The pinned runner fetcher otherwise forces static SDL. Android's
        # SDLActivity loads libSDL3.so, so establish the shared target first.
        if(NOT TARGET SDL3::SDL3)
            if(NOT EXISTS "${SNESRECOMP_SDL3_SOURCE_DIR}/CMakeLists.txt")
                message(FATAL_ERROR "Android requires SNESRECOMP_SDL3_SOURCE_DIR pointing to pinned SDL3 3.4.10 sources")
            endif()
            set(SDL_SHARED ON CACHE BOOL "" FORCE)
            set(SDL_STATIC OFF CACHE BOOL "" FORCE)
            set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)
            set(SDL_TESTS OFF CACHE BOOL "" FORCE)
            set(SDL_EXAMPLES OFF CACHE BOOL "" FORCE)
            set(SDL_INSTALL OFF CACHE BOOL "" FORCE)
            add_subdirectory("${SNESRECOMP_SDL3_SOURCE_DIR}" "${CMAKE_BINARY_DIR}/sots-sdl3")
        endif()
        add_library(${target} SHARED ${ARGN})
        set_target_properties(${target} PROPERTIES OUTPUT_NAME main)
    else()
        add_executable(${target} ${ARGN})
    endif()
endfunction()
