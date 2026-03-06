#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import sys
import urllib.request
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = ROOT / "resources" / "bin"
GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"


def _log(msg: str) -> None:
    print(f"[vendor] {msg}")


def _request_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "PacifierShop-Build",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _pick_asset(assets: list[dict], predicate: Callable[[str], bool], label: str) -> dict:
    for asset in assets:
        if predicate(asset.get("name", "")):
            return asset
    available = ", ".join(asset.get("name", "<unknown>") for asset in assets)
    raise RuntimeError(f"Could not find {label} asset. Available: {available}")


def _download(url: str, target: Path) -> None:
    _log(f"Downloading {url} -> {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "PacifierShop-Build"})
    with urllib.request.urlopen(req, timeout=120) as resp, target.open("wb") as fh:
        shutil.copyfileobj(resp, fh)


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _platform_tag() -> tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    return system, machine


def _spotdl_asset_selector(system: str) -> Callable[[str], bool]:
    if system == "darwin":
        return lambda name: "darwin" in name.lower() and not name.endswith(".sha256")
    if system == "linux":
        return lambda name: "linux" in name.lower() and not name.endswith(".sha256")
    if system == "windows":
        return lambda name: "windows" in name.lower() and name.lower().endswith(".exe")
    raise RuntimeError(f"Unsupported platform for spotdl: {system}")


def _ytdlp_asset_selector(system: str, machine: str) -> Callable[[str], bool]:
    if system == "darwin":
        return lambda name: name == "yt-dlp_macos"
    if system == "linux":
        is_arm = "arm" in machine or "aarch" in machine
        if is_arm:
            return lambda name: name == "yt-dlp_linux_aarch64"
        return lambda name: name == "yt-dlp_linux"
    if system == "windows":
        return lambda name: name == "yt-dlp.exe"
    raise RuntimeError(f"Unsupported platform for yt-dlp: {system}")


def _copy_conda_binary(name: str, dest_name: str | None = None) -> Path:
    source = shutil.which(name)
    if not source:
        raise RuntimeError(
            f"Could not locate `{name}` in PATH. Use Conda or pip with `{name}` available in PATH."
        )

    destination = BIN_DIR / (dest_name or name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    _make_executable(destination)
    _log(f"Copied {name} from {source} -> {destination}")
    return destination


def _download_release_binary(repo: str, selector: Callable[[str], bool], output_name: str) -> Path:
    release = _request_json(GITHUB_API.format(repo=repo))
    asset = _pick_asset(release.get("assets", []), selector, f"{repo}:{output_name}")
    target = BIN_DIR / output_name
    _download(asset["browser_download_url"], target)
    _make_executable(target)
    _log(f"Installed {output_name} from release {release.get('tag_name', '<unknown>')}")
    return target


def main() -> int:
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    system, machine = _platform_tag()
    _log(f"Platform detected: {system}/{machine}")

    _download_release_binary(
        repo="spotDL/spotify-downloader",
        selector=_spotdl_asset_selector(system),
        output_name="spotdl.exe" if system == "windows" else "spotdl",
    )

    _download_release_binary(
        repo="yt-dlp/yt-dlp",
        selector=_ytdlp_asset_selector(system, machine),
        output_name="yt-dlp.exe" if system == "windows" else "yt-dlp",
    )

    _copy_conda_binary("ffmpeg", "ffmpeg.exe" if system == "windows" else "ffmpeg")
    _copy_conda_binary("ffprobe", "ffprobe.exe" if system == "windows" else "ffprobe")

    _log("Vendor binaries are ready in resources/bin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
