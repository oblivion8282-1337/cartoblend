"""Build a self-contained CartoBlend release zip with bundled Python wheels.

Downloads wheels for pyproj and Pillow across all supported Blender platforms
and Python versions, copies the addon into a staging dir, injects the wheel
list into blender_manifest.toml, and zips the result into dist/.

Usage:
    python build_release.py [--out DIR]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
ADDON_NAME = "cartoblend"

# Packages to bundle as wheels. GDAL is intentionally excluded: PyPI wheel
# coverage is inconsistent across platforms and the addon has working fallbacks
# (vendored ImageIO + Pillow) for the raster paths that don't strictly need it.
PACKAGES = ["pyproj", "Pillow"]

# Each target lists candidate pip --platform tags from oldest-deployment-target
# to newest. Pip is invoked with all of them so it can pick whichever the
# package publisher actually shipped (different packages raise their macOS
# deployment-target floor at different times).
LINUX_X64   = ["manylinux2014_x86_64", "manylinux_2_17_x86_64", "manylinux_2_28_x86_64"]
LINUX_ARM64 = ["manylinux2014_aarch64", "manylinux_2_17_aarch64", "manylinux_2_28_aarch64"]
MACOS_X64   = ["macosx_10_9_x86_64", "macosx_10_10_x86_64", "macosx_10_13_x86_64",
               "macosx_11_0_x86_64", "macosx_12_0_x86_64"]
MACOS_ARM64 = ["macosx_11_0_arm64", "macosx_12_0_arm64", "macosx_13_0_arm64",
               "macosx_14_0_arm64", "macosx_15_0_arm64"]
WIN_X64     = ["win_amd64"]

# (candidate platform tags, pip --python-version, Blender manifest platform tag)
TARGETS = [
    (LINUX_X64,   "3.11", "linux-x64"),
    (LINUX_X64,   "3.13", "linux-x64"),
    (LINUX_ARM64, "3.11", "linux-arm64"),
    (LINUX_ARM64, "3.13", "linux-arm64"),
    (MACOS_X64,   "3.11", "macos-x64"),
    (MACOS_X64,   "3.13", "macos-x64"),
    (MACOS_ARM64, "3.11", "macos-arm64"),
    (MACOS_ARM64, "3.13", "macos-arm64"),
    (WIN_X64,     "3.11", "windows-x64"),
    (WIN_X64,     "3.13", "windows-x64"),
]

# Files/dirs that must never end up in the release zip.
EXCLUDE_NAMES = {".git", ".github", "__pycache__", "dist", "build",
                 "_staging", "wheels"}


def download_wheels(dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    misses: list[tuple[str, str, str]] = []
    for plat_tags, pyver, label in TARGETS:
        for pkg in PACKAGES:
            cmd = [
                sys.executable, "-m", "pip", "download",
                "--only-binary=:all:",
                "--no-deps",
                "--python-version", pyver,
                "--implementation", "cp",
                "-d", str(dest),
            ]
            for tag in plat_tags:
                cmd += ["--platform", tag]
            cmd.append(pkg)

            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                misses.append((pkg, pyver, label))
                print(f"  miss: {pkg} py{pyver} {label}", file=sys.stderr)
    if misses:
        print(f"\n{len(misses)} wheel(s) unavailable on PyPI — see above. "
              "Coverage gap, but continuing.\n", file=sys.stderr)
    return sorted(dest.glob("*.whl"))


def build_zip(version: str, wheels: list[Path], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    staging = out_dir / "_staging"
    if staging.exists():
        shutil.rmtree(staging)
    pkg_root = staging / ADDON_NAME

    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {n for n in names if n in EXCLUDE_NAMES or n.endswith(".pyc")}

    shutil.copytree(ROOT, pkg_root, ignore=ignore)

    wheels_dir = pkg_root / "wheels"
    wheels_dir.mkdir(exist_ok=True)
    for w in wheels:
        shutil.copy2(w, wheels_dir / w.name)

    inject_manifest(pkg_root / "blender_manifest.toml", wheels)

    base = out_dir / f"{ADDON_NAME}-{version}"
    out_zip = base.parent / (base.name + ".zip")
    if out_zip.exists():
        out_zip.unlink()
    shutil.make_archive(str(base), "zip", staging)

    shutil.rmtree(staging)
    return out_zip


def inject_manifest(manifest_path: Path, wheels: list[Path]) -> None:
    """Insert top-level ``platforms`` and ``wheels`` keys before the first
    TOML section header so they don't become part of an existing table.
    """
    text = manifest_path.read_text(encoding="utf-8")

    platforms = sorted({tag for _, _, tag in TARGETS})
    platforms_block = (
        "platforms = [\n"
        + "".join(f'  "{p}",\n' for p in platforms)
        + "]\n"
    )
    wheel_lines = "".join(f'  "./wheels/{w.name}",\n' for w in wheels)
    wheels_block = f"wheels = [\n{wheel_lines}]\n"

    addition = ""
    if "\nplatforms = " not in text and not text.lstrip().startswith("platforms"):
        addition += platforms_block
    if "\nwheels = " not in text and not text.lstrip().startswith("wheels"):
        addition += wheels_block
    if not addition:
        return

    lines = text.splitlines(keepends=True)
    insert_at = len(lines)
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("[") and not stripped.startswith("[["):
            insert_at = i
            break

    if insert_at < len(lines) and lines[insert_at - 1].strip() != "":
        addition = "\n" + addition
    if insert_at < len(lines) and not addition.endswith("\n\n"):
        addition += "\n"

    lines.insert(insert_at, addition)
    manifest_path.write_text("".join(lines), encoding="utf-8")


def get_version() -> str:
    data = tomllib.loads((ROOT / "blender_manifest.toml").read_text(encoding="utf-8"))
    return data["version"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "dist"),
                    help="Output directory for the built zip (default: ./dist)")
    args = ap.parse_args()

    version = get_version()
    out_dir = Path(args.out).resolve()

    with tempfile.TemporaryDirectory(prefix="cartoblend-wheels-") as tmp:
        wheels = download_wheels(Path(tmp))
        if not wheels:
            sys.exit("no wheels downloaded — aborting")
        zip_path = build_zip(version, wheels, out_dir)

    print(f"built {zip_path}")


if __name__ == "__main__":
    main()
