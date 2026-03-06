from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class ToolChoice(str, Enum):
    SPOTDL = "spotdl"
    YTDLP = "yt-dlp"


@dataclass(frozen=True)
class RoutingResult:
    tool: ToolChoice
    reason: str


SPOTIFY_HOSTS = {
    "open.spotify.com",
    "spotify.com",
}

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def choose_tool(url: str) -> RoutingResult:
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower().strip()

    if not parsed.scheme or not host:
        raise ValueError("Please provide a valid URL including scheme (https://...).")

    if host in SPOTIFY_HOSTS:
        return RoutingResult(ToolChoice.SPOTDL, "Spotify URL detected")

    if host in YOUTUBE_HOSTS:
        return RoutingResult(ToolChoice.YTDLP, "YouTube URL detected")

    if "spotify.com" in host:
        return RoutingResult(ToolChoice.SPOTDL, "Spotify-like URL detected")

    if "youtube.com" in host or host.endswith("youtu.be"):
        return RoutingResult(ToolChoice.YTDLP, "YouTube-like URL detected")

    raise ValueError(
        "Unsupported URL. Use Spotify links for spotdl or YouTube links for yt-dlp."
    )
