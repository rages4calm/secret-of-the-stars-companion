"""Finite map-settings GUI checks using genuine source builds and disposable profiles.

This does not run the native game. Actual map/POI, controller gameplay and paced
audio/performance proofs belong to separate native qualification.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def reject_links(path):
    for entry in [path, *path.parents]:
        if entry.exists() and (entry.is_symlink() or getattr(entry.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Linked test input/output is unsupported: " + str(entry))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gui", type=Path, required=True)
    parser.add_argument("--gui-receipt", type=Path, required=True)
    parser.add_argument("--native-build", type=Path, required=True)
    parser.add_argument("--older-build", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protect", type=Path, action="append", default=[], help="Explicit additional files/directories to hash without changing them.")
    args = parser.parse_args()
    gui, gui_receipt, native, older, rom = [x.resolve(strict=True) for x in (args.gui, args.gui_receipt, args.native_build, args.older_build, args.rom)]
    output = args.output.absolute()
    for path in [args.gui, args.gui_receipt, args.native_build, args.older_build, args.rom, output, *args.protect]:
        reject_links(path.absolute())
    if output.exists():
        raise ValueError("Use a fresh output directory; prior evidence is retained.")
    # Prevent recursive copying into an input tree or changing an owner source.
    for path in [native, older, gui.parent, *[x.resolve(strict=True) for x in args.protect if x.is_dir()]]:
        if output.is_relative_to(path) or path.is_relative_to(output):
            raise ValueError("Output must be separate from all input/protected directories.")
    gr, nr, old = [read(x) for x in (gui_receipt, native / "source-build-receipt.json", older / "source-build-receipt.json")]
    for receipt in (gr, nr, old):
        assert receipt["status"] == "compiled_unqualified" and receipt["public_build"] is True
    assert gr["version"] == "0.3.2" and sha(gui) == gr["executable_sha256"]
    assert tuple(map(int, nr["version"].split("."))) >= (0, 2, 6)
    assert tuple(map(int, old["version"].split("."))) < (0, 2, 6)
    assert sha(rom) == "7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600"
    protected = {}
    def protect(path):
        reject_links(path)
        if path.is_dir():
            for child in path.rglob("*"):
                reject_links(child)
                if child.is_file():
                    protected[str(child)] = sha(child)
        else:
            protected[str(path)] = sha(path)
    for path in [gui, gui_receipt, rom, Path(__file__).resolve(), *[x.resolve(strict=True) for x in args.protect]]:
        protect(path)
    for build in (native, older):
        protect(build / "source-build-receipt.json")
        protect(build / "build/SecretOfTheStarsSNESRecomp.exe")
        if (build / "profile").is_dir():
            protect(build / "profile")
    checkpoint = args.checkpoint.resolve(strict=True) if args.checkpoint else None
    if checkpoint:
        protect(checkpoint)
    output.mkdir(parents=True)
    write(output / "protected-before.json", protected)
    copied_gui = output / "Companion.exe"
    shutil.copy2(gui, copied_gui)
    def copy_build(root, name, source):
        target = root / "local/source-builds" / name
        (target / "build").mkdir(parents=True)
        (target / "profile").mkdir()
        for name in ("source-build-receipt.json", "build/SecretOfTheStarsSNESRecomp.exe"):
            original = source / name
            shutil.copy2(original, target / name)
            assert sha(original) == sha(target / name)
        receipt = read(target / "source-build-receipt.json")
        assert sha(target / "build/SecretOfTheStarsSNESRecomp.exe") == receipt["executable_sha256"]
        for name in ("config.ini", "foundation.ini", "keybinds.ini"):
            if (source / "profile" / name).is_file():
                shutil.copy2(source / "profile" / name, target / "profile" / name)
        return target
    root = output / "source-root"
    copy_build(root, "actual-map-build", native)
    def run(arguments):
        result = subprocess.run([str(copied_gui), *map(str, arguments)], timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0, (arguments, result.returncode)
    failure = None
    try:
        run(["--root", root, "--public-self-test", output / "source-adoption", "--rom", rom, "--report", output / "adoption-error.json"])
        adopted = read(output / "source-adoption/report.json")
        isolated, profile = Path(adopted["test_root"]), Path(adopted["adopted_profile"])
        preceding = copy_build(isolated, "actual-preceding-build", older)
        if checkpoint:
            shutil.copy2(checkpoint, profile / "saves/save8.sav")
        run(["--root", isolated, "--profile", profile, "--map-ui-test", output / "map-ui.json", "--older-receipt", preceding / "source-build-receipt.json", "--report", output / "map-error.json"])
    except Exception as error:
        failure = repr(error)
    after = {path: sha(Path(path)) if Path(path).is_file() else None for path in protected}
    changed = {path: after[path] for path, digest in protected.items() if after[path] != digest}
    write(output / "protected-after.json", {"passed": not changed, "changed": changed, "hashes": after})
    reports = {}
    for name in ("source-adoption/report.json", "map-ui.json"):
        path = output / name
        if path.is_file():
            value = read(path)
            reports[name] = {"passed": value.get("passed") is True, "checks": value.get("checks"), "sha256": sha(path)}
    result = {"passed": failure is None and not changed and len(reports) == 2 and all(x["passed"] for x in reports.values()), "failure": failure,
              "gui_sha256": sha(gui), "gui_receipt_sha256": sha(gui_receipt), "native_sha256": nr["executable_sha256"], "older_native_sha256": old["executable_sha256"],
              "native_receipt_sha256": sha(native / "source-build-receipt.json"), "older_receipt_sha256": sha(older / "source-build-receipt.json"),
              "checkpoint_sha256": sha(checkpoint) if checkpoint else None, "reports": reports, "protected_count": len(protected), "protected_unchanged": not changed,
              "source_compilation_status_retained": "compiled_unqualified", "gameplay_executed": False,
              "limits": "GUI/configuration and source launch-environment checks only. No map raster/POI, audible pacing, physical-pad or campaign qualification; legacy native launch is tested separately."}
    write(output / "report.json", result)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
