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
        str(entry_script),
    ]

    if sys.platform == "darwin":
        pyinstaller_cmd[1:1] = ["--icon", str(ROOT / "resources" / "pacifier.icns")]
    elif os.name == "nt":
        ico_path = ROOT / "resources" / "pacifier.ico"
        if ico_path.exists():
            pyinstaller_cmd[1:1] = ["--icon", str(ico_path)]

    run(pyinstaller_cmd)
    print("[build] Build complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
