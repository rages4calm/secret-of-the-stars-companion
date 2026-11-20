#!/usr/bin/env python3
"""Build Secret of the Stars on Linux x86-64 from an owned clean USA ROM."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys


TOOLS = Path(__file__).resolve().parents[1]
TARGET = "SecretOfTheStarsSNESRecomp"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_launcher(output, executable, rom):
    launcher = output / "play.sh"
    with launcher.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(f"#!/bin/sh\nset -eu\ncd {shlex.quote(str(executable.parent))}\n")
        stream.write(f"exec ./{TARGET} --no-launcher --rom {shlex.quote(str(rom))} \"$@\"\n")
    launcher.chmod(0o700)
    return launcher


def setup(rom, output, jobs, source_build, runtime):
    for tool in ("git", "clang", "clang++", "cmake", "ninja", "pkg-config"):
        if not shutil.which(tool):
            raise RuntimeError(f"Required command is missing: {tool}. See docs/PLATFORMS.md.")
    if source_build is None and not shutil.which("cargo"):
        raise RuntimeError("Cargo is required for first-time ROM setup. See docs/PLATFORMS.md.")
    rom = rom.resolve(strict=True)
    if not rom.is_file():
        raise ValueError("Choose the ROM file, not its containing folder.")
    identity = TOOLS.parent / "native/foundation/rom_identity.txt"
    values = dict((key.strip(), value.strip()) for line in identity.read_text(encoding="utf-8").splitlines()
                  for key, sep, value in [line.partition("=")] if sep and not key.lstrip().startswith("#"))
    expected = values["expected_sha256"]
    if rom.stat().st_size != int(values["rom_size"]) or sha256(rom) != expected:
        raise ValueError("Choose the exact clean, unheadered USA ROM described in BUILDING.md.")
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    output = output.resolve()
    env = dict(os.environ, CC="clang", CXX="clang++", CARGO_BUILD_JOBS=str(jobs))

    if source_build is None:
        source_build = output / "sources"
        print("Preparing private game sources from your ROM...", flush=True)
        subprocess.run([sys.executable, str(TOOLS / "build_public_foundation.py"),
                        "--prepare-platform-sources", "--rom", str(rom),
                        "--output-dir", str(source_build)], env=env, check=True)

    source_build = source_build.resolve(strict=True)
    receipt = source_build / "platform-source-receipt.json"
    if not receipt.is_file():
        raise ValueError("Select the private output from --prepare-platform-sources.")
    prepared = json.loads(receipt.read_bytes())
    if expected != prepared["rom_sha256"]:
        raise ValueError("The ROM does not match the prepared Linux build inputs.")
    if runtime is None:
        runtime = Path(prepared["runtime_source_provenance"]["runtime_dir"])

    platform_dir = output / "native"
    print("Configuring the native Linux build...", flush=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("prepare.py")),
                    "--platform", "linux", "--source-build", str(source_build),
                    "--runtime", str(runtime), "--output", str(platform_dir), "--configure"],
                   env=env, check=True)
    build = platform_dir / "build"
    print("Compiling the Linux game...", flush=True)
    subprocess.run(["cmake", "--build", str(build), "--target", TARGET, "--parallel", str(jobs)], check=True)
    game = build / TARGET
    with game.open("rb") as stream:
        header = stream.read(20)
    if not header.startswith(b"\x7fELF\x02\x01") or header[18:20] != b"\x3e\x00" or not os.access(game, os.X_OK):
        raise RuntimeError("The build did not produce an executable Linux x86-64 game.")
    if sha256(rom) != prepared["rom_sha256"]:
        raise ValueError("The ROM changed during setup. Build output was kept for diagnosis.")

    with (output / "linux-build-receipt.json").open("x", encoding="utf-8") as stream:
        json.dump({"status": "compiled_unqualified", "executable": str(game),
                   "executable_sha256": sha256(game), "rom_sha256": prepared["rom_sha256"],
                   "source_receipt_sha256": sha256(receipt),
                   "platform_plan_sha256": sha256(platform_dir / "platform-plan.json")}, stream, indent=2)
        stream.write("\n")
    launcher = write_launcher(output, game, rom)
    print(f"Setup complete. Run {shlex.quote(str(launcher))} to play.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="Clean, unheadered Tecmo Secret of the Stars (USA) ROM")
    parser.add_argument("--output", type=Path, help="New private build folder (default: ~/.local/share/secret-of-the-stars)")
    parser.add_argument("--jobs", type=int, default=2, help="Parallel compile jobs (default: 2)")
    parser.add_argument("--source-build", type=Path, help="Reuse existing verified --prepare-platform-sources output")
    parser.add_argument("--runtime", type=Path, help="Local location of the pinned runtime when reusing relocated inputs")
    args = parser.parse_args()
    if sys.platform != "linux" or platform.machine() != "x86_64":
        parser.error("This setup command requires Linux x86-64. See docs/PLATFORMS.md for cross-builds.")
    if args.runtime is not None and args.source_build is None:
        parser.error("--runtime requires --source-build")
    if not 1 <= args.jobs <= 64:
        parser.error("--jobs must be between 1 and 64")
    output = args.output or (Path.home() / ".local/share/secret-of-the-stars")
    try:
        setup(args.rom, output, args.jobs, args.source_build, args.runtime)
    except FileExistsError as exc:
        parser.exit(1, f"Setup stopped because this path exists: {exc.filename}. Use a new --output folder.\n")
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Setup stopped: {exc}\n")


if __name__ == "__main__":
    main()
