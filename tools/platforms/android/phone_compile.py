#!/usr/bin/env python3
"""Export the pinned Android build inputs and compile a private game module."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile


TARGET = "aarch64-none-linux-android26"
TARGET_LIB = "usr/lib/aarch64-linux-android"
ARCHITECTURE_C = "arch_native/sots_arch78.generated.c"
LEGACY_REGIONS_C = "project/src/gen/native_regions_v2.c"
ARCHITECTURE_PART_SIZE = 4096
ARCHITECTURE_BLOCK = re.compile(rb"static void nb69_block_(\d+)\(CpuState \*cpu,NativeBlockScope \*scope\) \{\r?\n")
ARCHITECTURE_TABLE = b"static const NativeBlockInstruction nb69_instructions[]={"
HIDDEN_LINKAGE = b'__attribute__((visibility("hidden"))) '
LEGACY_STEP = b"bool cpu_native_region_step(CpuState *cpu,uint32 pc24,uint8 mx,uint32 *next_pc) {\n"
LEGACY_SWITCH = b"  switch (((pc24&0x7fffffu)<<2)|mx) {\n"
LEGACY_SWITCH_END = b"    default: return false;\n  }\n}\n"
LEGACY_CASE = re.compile(rb"^    case (\d+)u: \{ /\* ([0-9a-f]{6}) M([01])X([01]) ", re.MULTILINE)
LEGACY_BUCKET_SHIFT = 13
COMPILER_FLAGS = frozenset({
    "-fdata-sections", "-ffunction-sections", "-funwind-tables", "-fstack-protector-strong",
    "-no-canonical-prefixes", "-Wformat", "-Werror=format-security", "-O1", "-O3",
    "-std=gnu11", "-std=gnu++17", "-fPIC", "-w",
})
LINK_DRIVER_FLAGS = (
    "-EL", "--fix-cortex-a53-843419", "-z", "now", "-z", "relro", "-z", "max-page-size=16384",
    "--hash-style=gnu", "--eh-frame-hdr", "-m", "aarch64linux", "-shared", "--build-id=sha1",
    "--no-rosegment", "--no-undefined-version", "--fatal-warnings", "--no-undefined",
    "--gc-sections", "-soname", "libmain.so", "--strip-debug", "--threads=1",
)
LINK_RESOURCE_FILES = (
    "lib/linux/aarch64/libatomic.a", "lib/linux/aarch64/libunwind.a",
    "lib/linux/libclang_rt.builtins-aarch64-android.a",
)
LINK_SYSROOT_FILES = (
    "26/crtbegin_so.o", "26/crtend_so.o", "26/libc.so", "26/libdl.so", "26/libm.so",
    "26/libc++.a", "libc++_static.a", "libc++abi.a",
)


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def export_recipe(args) -> None:
    capsule = args.capsule.resolve()
    project = args.project.resolve()
    runtime = args.runtime.resolve() / "runner/src"
    sdl = args.sdl.resolve() / "include"
    build = args.android_build.resolve()
    arch = args.arch.resolve()
    sysroot = args.ndk_toolchain.resolve() / "sysroot"
    resource = args.ndk_toolchain.resolve() / "lib/clang/19"
    roots = (
        (project / "src/gen", "generated", "project/src/gen"),
        (project / "recomp", "generated", "project/recomp"),
        (arch, "generated", "arch_native"),
        (project, "capsule", "src/game"),
        (runtime, "capsule", "src/runtime"),
        (sdl, "capsule", "src/sdl"),
        (build / "snesrecomp_rom_identity", "capsule", "src/cmake/rom_identity"),
        (build / "sots-sdl3/include-revision", "capsule", "src/cmake/sdl_revision"),
    )

    def relocate(raw: str) -> tuple[str, str]:
        path = Path(raw).resolve()
        for source, owner, destination in roots:
            if path.is_relative_to(source):
                relative = path.relative_to(source)
                return owner, (Path(destination) / relative).as_posix()
        raise ValueError(f"Compiler input is outside the pinned source roots: {raw}")

    def flags_for(row: dict) -> list:
        arguments = shlex.split(row["command"])
        if Path(arguments[0]).name not in {"clang.exe", "clang++.exe"}:
            # Ninja's unquoted Windows compiler name uses backslashes, consumed by shlex.
            compiler = re.match(r'^(?:"([^"]+)"|(\S+)) ', row["command"])
            if not compiler or Path(compiler.group(1) or compiler.group(2)).name not in {"clang.exe", "clang++.exe"}:
                raise ValueError(f"Unexpected compiler in the pinned Ninja recipe: {row['file']}")
        trailer = arguments[arguments.index("-MD"):]
        if len(trailer) != 9 or trailer[1] != "-MT" or trailer[3] != "-MF" or trailer[5] != "-o" or trailer[7] != "-c":
            raise ValueError(f"Unexpected output or dependency flags for {row['file']}")
        flags = []
        original = iter(arguments[1:arguments.index("-MD")])
        saw_target = saw_sysroot = False
        for flag in original:
            if flag == f"--target={TARGET}":
                saw_target = True
            elif flag.startswith("--sysroot=") and Path(flag.split("=", 1)[1]).resolve() == sysroot:
                saw_sysroot = True
            elif flag == "-g":
                continue
            elif flag.startswith("-I"):
                flags.append(["-I", *relocate(flag[2:])])
            elif flag == "-include":
                flags.append(["-include", *relocate(next(original))])
            elif flag.startswith("-D") or flag in COMPILER_FLAGS:
                flags.append(flag)
            else:
                raise ValueError(f"Unrecognized platform compiler option: {flag}")
        if not saw_target or not saw_sysroot:
            raise ValueError(f"Missing Android target or sysroot: {row['file']}")
        return flags

    records = json.loads(args.compdb.read_text(encoding="utf-8-sig"))
    units = []
    inputs = {}

    def register(source: Path, destination: str) -> None:
        if destination in inputs and inputs[destination] != source:
            raise ValueError(f"Two donors provide {destination}")
        inputs[destination] = source

    def register_tree(source: Path, destination: str, accept) -> None:
        if not source.is_dir():
            raise ValueError(f"Source directory is missing: {source}")
        for path in source.rglob("*"):
            if path.is_file() and accept(path):
                register(path, f"{destination}/{path.relative_to(source).as_posix()}")

    for row in records:
        source = Path(row["file"])
        if "SecretOfTheStarsSNESRecomp.dir" not in row.get("output", "") or source.suffix not in {".c", ".cpp"}:
            continue
        owner, relative = relocate(row["file"])
        flags = flags_for(row)
        if owner == "capsule":
            register(source.resolve(), relative)
        elif relative != ARCHITECTURE_C and not relative.startswith("project/src/gen/"):
            raise ValueError(f"Unexpected private generated input: {relative}")
        units.append({"owner": owner, "source": relative, "flags": flags})
    if (not any(unit["source"] == ARCHITECTURE_C for unit in units)
            or not any(unit["source"] == LEGACY_REGIONS_C for unit in units)
            or not any(unit["source"].endswith("/host_main.c") for unit in units)
            or not any(unit["source"].endswith(".cpp") for unit in units)):
        raise ValueError("The pinned Ninja recipe did not provide the expected native target families")

    header = lambda path: path.suffix.lower() in {".h", ".hpp", ".inc"}
    register_tree(runtime, "src/runtime", header)
    for path in (project / "src").iterdir():
        if path.is_file() and header(path):
            register(path, f"src/game/src/{path.name}")
    register_tree(project / "third_party/companion_achievements", "src/game/third_party/companion_achievements", header)
    register(project / "platforms/android_host_compat.h", "src/game/platforms/android_host_compat.h")
    register_tree(sdl, "src/sdl", header)
    for source, _, destination in roots[-2:]:
        register_tree(source, destination, header)
    register_tree(resource / "include", "resource/include", lambda path: True)
    register_tree(sysroot / "usr/include", "sysroot/usr/include", lambda path: True)
    for file in LINK_RESOURCE_FILES:
        register(resource / file, f"resource/{file}")
    for file in LINK_SYSROOT_FILES:
        register(sysroot / TARGET_LIB / file, f"sysroot/{TARGET_LIB}/{file}")

    capsule_files = {}
    for destination, source in sorted(inputs.items()):
        target = capsule / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        if destination.endswith("/snesrecomp_rom_identity.h"):
            content = source.read_text(encoding="utf-8")
            target.write_text(re.sub(r"^/\* Generated from .*?rom_identity\.txt", "/* Generated from rom_identity.txt", content), encoding="utf-8")
        else:
            shutil.copyfile(source, target)
        capsule_files[destination] = _sha256(target)
    recipe = {"format": 1, "target": TARGET, "units": units, "capsule_files": capsule_files}
    (capsule / "recipe.json").write_text(json.dumps(recipe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Exported {len(units)} compile units and {len(capsule_files)} public inputs")


def _located(roots: dict[str, Path], owner: str, relative: str) -> Path:
    root = roots[owner]
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"Compiler input escapes its root: {relative}")
    return result


def _run(command: list, work: Path) -> None:
    with tempfile.TemporaryFile(dir=work) as log:
        result = subprocess.run(command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=False)
        if result.returncode:
            log.seek(max(0, log.tell() - 8192))
            lines = log.read().decode("utf-8", errors="replace").strip().splitlines()
            detail = next((line.strip() for line in lines if "error:" in line.lower()),
                          lines[-1].strip() if lines else "No compiler output was available.")
            raise RuntimeError(f"{command[1]} exited with {result.returncode}: {detail}")


def _compile(zig: Path, capsule: Path, source: Path, output: Path, flags: list[str], work: Path) -> None:
    _run([zig, "clang", f"--target={TARGET}", f"--sysroot={capsule / 'sysroot'}",
          f"-resource-dir={capsule / 'resource'}", *flags, "-c", source, "-o", output], work)


def _link(zig: Path, capsule: Path, sdl: Path, objects: list[Path], output: Path, work: Path) -> None:
    sysroot = capsule / "sysroot"
    arm_lib = sysroot / TARGET_LIB
    api_lib = arm_lib / "26"
    resource_lib = capsule / "resource/lib/linux"
    builtins = resource_lib / "libclang_rt.builtins-aarch64-android.a"
    _run([zig, "ld.lld", f"--sysroot={sysroot}", *LINK_DRIVER_FLAGS, "-o", output,
          api_lib / "crtbegin_so.o", f"-L{resource_lib / 'aarch64'}", f"-L{api_lib}", f"-L{arm_lib}",
          *objects, sdl, "-lm", "-latomic", "-Bstatic", "-lc++", "-Bdynamic", "-lm",
          builtins, "-l:libunwind.a", "-ldl", "-lc", builtins, "-l:libunwind.a", "-ldl",
          api_lib / "crtend_so.o"], work)


def _architecture_parts(source: Path, directory: Path):
    """Separate generated function bodies from the still-contiguous lookup table."""
    with source.open("rb") as original:
        prefix = bytearray()
        for line in original:
            if ARCHITECTURE_BLOCK.fullmatch(line):
                break
            if len(prefix) > 65536:
                raise ValueError("Architectural generator's helper boundary changed")
            prefix.extend(line)
        else:
            raise ValueError("Architectural generator did not emit any instruction bodies")
        table = directory / "native-table.c"
        with table.open("wb") as table_file:
            table_file.write(prefix)
            expected = 0
            while not line.rstrip(b"\r\n") == ARCHITECTURE_TABLE:
                part = directory / f"native-{expected // ARCHITECTURE_PART_SIZE:03d}.c"
                with part.open("wb") as part_file:
                    part_file.write(prefix)
                    for _ in range(ARCHITECTURE_PART_SIZE):
                        match = ARCHITECTURE_BLOCK.fullmatch(line)
                        if not match or int(match.group(1)) != expected:
                            raise ValueError(f"Unexpected architectural instruction body {expected}")
                        signature = line.removeprefix(b"static ").rstrip(b"\r\n").removesuffix(b" {")
                        table_file.write(b"extern " + HIDDEN_LINKAGE + signature + b";\n")
                        part_file.write(HIDDEN_LINKAGE + line.removeprefix(b"static "))
                        for line in original:
                            part_file.write(line)
                            if line.rstrip(b"\r\n") == b"}":
                                break
                        expected += 1
                        line = original.readline()
                        if line.rstrip(b"\r\n") == ARCHITECTURE_TABLE:
                            break
                yield part
                part.unlink()
            table_file.write(line)
            shutil.copyfileobj(original, table_file)
        yield table
        table.unlink()


def _legacy_region_parts(source: Path, directory: Path):
    """Keep scheduler admission in its original entry point and optimize small case switches."""
    original = source.read_bytes().replace(b"\r\n", b"\n")
    prefix, step, remainder = original.partition(LEGACY_STEP)
    guards, switch, remainder = remainder.partition(LEGACY_SWITCH)
    cases, end, trailing = remainder.partition(LEGACY_SWITCH_END)
    includes, bootstrap, bootstrap_body = prefix.partition(b"bool cpu_source_reset_bootstrap_match(")
    if not (step and switch and end and bootstrap and trailing.startswith(b"bool cpu_source_architecture_member(")):
        raise ValueError("Legacy region generator's dispatch boundary changed")

    matches = list(LEGACY_CASE.finditer(cases))
    headers = re.findall(rb"^    case ", cases, re.MULTILINE)
    if not matches or matches[0].start() or len(matches) != len(headers):
        raise ValueError("Legacy region generator's case boundary changed")
    blocks = {}
    previous = -1
    for index, match in enumerate(matches):
        key, pc, m_flag, x_flag = match.groups()
        key = int(key)
        expected_key = ((int(pc, 16) & 0x7fffff) << 2) | (int(m_flag) << 1) | int(x_flag)
        if key != expected_key or key <= previous:
            raise ValueError(f"Unexpected legacy region dispatch key {key}")
        previous = key
        next_case = matches[index + 1].start() if index + 1 < len(matches) else len(cases)
        blocks.setdefault(key >> LEGACY_BUCKET_SHIFT, []).append(cases[match.start():next_case])

    declarations = []
    routes = []
    for bucket, region_cases in blocks.items():
        name = f"sots_legacy_region_{bucket}"
        signature = HIDDEN_LINKAGE + f"bool {name}(CpuState *cpu,uint32 pc24,uint8 mx,uint32 *next_pc)".encode()
        declarations.append(signature + b";\n")
        routes.append(f"    case {bucket}u: return {name}(cpu,pc24,mx,next_pc);\n".encode())
        part = directory / f"legacy-region-{bucket:04d}.c"
        with part.open("wb") as out:
            out.write(includes + signature + b" {\n" + LEGACY_SWITCH)
            out.writelines(region_cases)
            out.write(LEGACY_SWITCH_END)
        yield part
        part.unlink()

    dispatch = directory / "legacy-region-dispatch.c"
    with dispatch.open("wb") as out:
        out.write(includes)
        out.writelines(declarations)
        out.write(bootstrap + bootstrap_body + step + guards)
        out.write(f"  switch ((((pc24&0x7fffffu)<<2)|mx)>>{LEGACY_BUCKET_SHIFT}) {{\n".encode())
        out.writelines(routes)
        out.write(LEGACY_SWITCH_END + trailing)
    yield dispatch
    dispatch.unlink()


def compile_module(recipe_path, capsule_dir, generated_dir, native_dir, work_dir, output_path, *,
                   progress=print, unit_progress=None, zig_path=None):
    """Compile sequentially, then atomically move the private ELF into place."""
    recipe = json.loads(Path(recipe_path).read_text(encoding="utf-8"))
    if recipe["format"] != 1 or recipe["target"] != TARGET:
        raise ValueError("This setup package uses an unsupported native build recipe")
    capsule = Path(capsule_dir).resolve()
    roots = {"capsule": capsule, "generated": Path(generated_dir).resolve()}
    native = Path(native_dir).resolve()
    zig = Path(zig_path).resolve() if zig_path else native / "libzig.so"
    output = Path(output_path).resolve()
    generated_source = _located(roots, "generated", "project/src")
    total = len(recipe["units"])
    if unit_progress is not None:
        unit_progress(0, total)
    with tempfile.TemporaryDirectory(prefix="compile-", dir=work_dir) as temp:
        work = Path(temp).resolve()
        objects = []
        for number, unit in enumerate(recipe["units"], start=1):
            source = _located(roots, unit["owner"], unit["source"])
            flags = []
            for flag in unit["flags"]:
                if isinstance(flag, str):
                    flags.append(flag)
                else:
                    option, owner, relative = flag
                    flags.extend((option, str(_located(roots, owner, relative))))
            # The NDK source tree keeps game C and its gen/ headers together.
            # The APK's authored and generated files have separate roots.
            flags.extend(("-I", str(generated_source)))
            progress(f"Compiling game {number}/{total}: {source.name}")
            if unit["owner"] == "generated" and unit["source"] in (ARCHITECTURE_C, LEGACY_REGIONS_C):
                split = _architecture_parts if unit["source"] == ARCHITECTURE_C else _legacy_region_parts
                for part in split(source, work):
                    progress(f"Compiling native CPU {part.stem}")
                    obj = work / f"{part.stem}.o"
                    _compile(zig, capsule, part, obj, flags, work)
                    objects.append(obj)
            else:
                obj = work / f"unit-{number:03d}.o"
                _compile(zig, capsule, source, obj, flags, work)
                objects.append(obj)
            if unit_progress is not None:
                unit_progress(number, total)
        progress("Linking game")
        linked = work / "libmain.so"
        _link(zig, capsule, native / "libSDL3.so", objects, linked, work)
        os.replace(linked, output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_subparsers(dest="command", required=True)
    exporter = command.add_parser("export")
    for option in ("compdb", "project", "runtime", "android-build", "sdl", "ndk-toolchain", "arch", "capsule"):
        exporter.add_argument(f"--{option}", type=Path, required=True)
    compile_parser = command.add_parser("compile")
    for option in ("capsule", "generated", "native", "work", "output"):
        compile_parser.add_argument(f"--{option}", type=Path, required=True)
    compile_parser.add_argument("--zig", type=Path)
    args = parser.parse_args()
    if args.command == "export":
        export_recipe(args)
    else:
        compile_module(args.capsule / "recipe.json", args.capsule, args.generated, args.native,
                       args.work, args.output, zig_path=args.zig)


if __name__ == "__main__":
    main()
