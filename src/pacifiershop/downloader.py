from __future__ import annotations

import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

from .routing import ToolChoice


LogFn = Callable[[str], None]


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    output_dir: Path
    tool: ToolChoice
    quality: str = "max"


def _resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def _bundled_bin_dir() -> Path:
    return _resource_root() / "resources" / "bin"


def _binary_name(base: str) -> str:
    if os.name == "nt":
        return f"{base}.exe"
    return base


def _ensure_tool_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing bundled dependency: {label} at {path}")


def _spotdl_cmd(url: str, output_dir: Path, quality: str) -> list[str]:
    spotdl_bin = _bundled_bin_dir() / _binary_name("spotdl")
    _ensure_tool_exists(spotdl_bin, "spotdl")
    bitrate = "320k" if quality == "max" else "128k"
    return [
        str(spotdl_bin),
        "download",
        url,
        "--bitrate",
        bitrate,
        "--output",
        str(output_dir / "{artists} - {title}.{output-ext}"),
    ]


def _ytdlp_cmd(url: str, output_dir: Path, quality: str) -> list[str]:
    yt_dlp_bin = _bundled_bin_dir() / _binary_name("yt-dlp")
    _ensure_tool_exists(yt_dlp_bin, "yt-dlp")
    if quality == "max":
        format_selector = "bestvideo*+bestaudio/best"
    else:
        format_selector = "bestvideo*[height<=720]+bestaudio/best[height<=720]/best"
    return [
        str(yt_dlp_bin),
        "-f",
        format_selector,
        "--merge-output-format",
        "mp4",
        "-o",
        str(output_dir / "%(title)s.%(ext)s"),
        url,
    ]


def _is_spotify_playlist_url(url: str) -> bool:
    return "/playlist/" in urlparse(url).path.lower()


def _is_youtube_playlist_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parse_qs(parsed.query)
    return "/playlist" in path or bool(query.get("list"))


def _is_playlist_url(url: str, tool: ToolChoice) -> bool:
    if tool == ToolChoice.SPOTDL:
        return _is_spotify_playlist_url(url)
    if tool == ToolChoice.YTDLP:
        return _is_youtube_playlist_url(url)
    return False


def _clean_segment(value: str) -> str:
    lowered = value.lower().strip()
    cleaned = "".join(char if char.isalnum() or char in "-_" else "-" for char in lowered)
    return cleaned.strip("-_") or "playlist"


def _playlist_folder_name(url: str, tool: ToolChoice) -> str:
    parsed = urlparse(url)
    path_segments = [segment for segment in parsed.path.split("/") if segment]

    if tool == ToolChoice.SPOTDL:
        marker = "playlist"
        if marker in path_segments:
            idx = path_segments.index(marker)
            if idx + 1 < len(path_segments):
                return f"spotify-playlist-{_clean_segment(path_segments[idx + 1])}"
        return "spotify-playlist"

    if tool == ToolChoice.YTDLP:
        query = parse_qs(parsed.query)
        playlist_id = query.get("list", [None])[0]
        if playlist_id:
            return f"youtube-playlist-{_clean_segment(playlist_id)}"
        if path_segments:
            return f"youtube-playlist-{_clean_segment(path_segments[-1])}"
        return "youtube-playlist"

    return "playlist"


def _target_output_dir(request: DownloadRequest) -> Path:
    if not _is_playlist_url(request.url, request.tool):
        return request.output_dir
    return request.output_dir / _playlist_folder_name(request.url, request.tool)


def _env_with_binaries() -> dict[str, str]:
    env = os.environ.copy()
    bin_dir = _bundled_bin_dir()
    ffmpeg_dir = bin_dir
    existing_path = env.get("PATH", "")
    env["PATH"] = f"{ffmpeg_dir}{os.pathsep}{existing_path}" if existing_path else str(ffmpeg_dir)
    return env


def run_download(request: DownloadRequest, log: LogFn) -> int:
    target_dir = _target_output_dir(request)
    target_dir.mkdir(parents=True, exist_ok=True)
    quality = request.quality.lower().strip()
    if quality not in {"max", "efficient"}:
        quality = "max"

    if request.tool == ToolChoice.SPOTDL:
        cmd = _spotdl_cmd(request.url, target_dir, quality)
    elif request.tool == ToolChoice.YTDLP:
        cmd = _ytdlp_cmd(request.url, target_dir, quality)
    else:
        raise RuntimeError(f"Unsupported tool selection: {request.tool}")

    log(f"Running: {' '.join(shlex.quote(part) for part in cmd)}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=_env_with_binaries(),
    )

    assert proc.stdout is not None
    for line in proc.stdout:
        log(line.rstrip())

    proc.wait()
    return proc.returncode
