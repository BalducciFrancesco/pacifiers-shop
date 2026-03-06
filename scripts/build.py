#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def run(cmd: list[str]) -> None:
    print(f"[build] {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=ROOT)


def main() -> int:
    sep = ";" if os.name == "nt" else ":"

    run([sys.executable, "-m", "pytest", "-q"])
    run([sys.executable, str(ROOT / "scripts" / "vendor_binaries.py")])

    if DIST.exists():
        shutil.rmtree(DIST)
    if BUILD.exists():
        shutil.rmtree(BUILD)

    entry_script = ROOT / "scripts" / "run.py"
    icon_path = ROOT / "resources" / "pacifier.icns"

    pyinstaller_cmd = [
        "pyinstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        "PacifierShop",
        "--clean",
        "--paths",
        str(ROOT / "src"),
        "--add-data",
        f"{ROOT / 'resources' / 'bin'}{sep}resources/bin",
        "--add-data",
        f"{ROOT / 'resources' / 'pacifier.png'}{sep}resources",
        "--icon",
        str(icon_path),
        str(entry_script),
    ]

    run(pyinstaller_cmd)
    print("[build] Build complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
