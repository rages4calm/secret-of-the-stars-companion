"""Create a ROM-free Android setup shell for on-device build development."""
import argparse
from pathlib import Path
from shutil import copyfile

from android_project import ANDROID, android_sdl_sources, write_android_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdl-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sdl = args.sdl_source.resolve(strict=True)
    android_sdl_sources(sdl)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cmake = output / 'CMakeLists.txt'
    copyfile(ANDROID / 'SDLOnly.cmake.in', cmake)
    write_android_project(output, sdl, cmake, [
        '-DSNESRECOMP_SDL3_SOURCE_DIR=' + sdl.as_posix(), '-DANDROID_STL=c++_static',
    ], 'SDL3-shared', local_module=True)
    print(f'Gradle setup shell: {output}')
    print('Developer shell only. On-device code generation and compilation are pending.')


if __name__ == '__main__':
    main()
