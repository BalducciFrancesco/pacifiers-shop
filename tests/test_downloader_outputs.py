from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

import pacifiershop.downloader as downloader
from pacifiershop.downloader import DownloadRequest, run_download
from pacifiershop.routing import ToolChoice


def _url_is_playlist(url: str) -> bool:
    parsed = urlparse(url)
    return "/playlist" in parsed.path.lower() or bool(parse_qs(parsed.query).get("list"))


def _replace_tokens(template: str, title: str, ext: str, artist: str) -> Path:
    path = (
        template.replace("{artists}", artist)
        .replace("{title}", title)
        .replace("{output-ext}", ext)
        .replace("%(title)s", title)
        .replace("%(ext)s", ext)
    )
    return Path(path)


def _simulate_spotdl(cmd: list[str]) -> None:
    url = cmd[2]
    template = cmd[cmd.index("--output") + 1]
    count = 2 if _url_is_playlist(url) else 1
    for i in range(count):
        target = _replace_tokens(template, f"track-{i + 1}", "mp3", f"artist-{i + 1}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"")


def _simulate_ytdlp(cmd: list[str]) -> None:
    url = cmd[-1]
    template = cmd[cmd.index("-o") + 1]
    ext = "mp4"
    if "-x" in cmd and "--audio-format" in cmd:
        ext = cmd[cmd.index("--audio-format") + 1]
    elif "--recode-video" in cmd:
        ext = cmd[cmd.index("--recode-video") + 1]

    count = 2 if _url_is_playlist(url) else 1
    for i in range(count):
        target = _replace_tokens(template, f"video-{i + 1}", ext, "")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"")


class _FakePopen:
    def __init__(
        self,
        cmd: list[str],
        stdout: int | None = None,
        stderr: int | None = None,
        text: bool = False,
        bufsize: int = -1,
        env: dict[str, str] | None = None,
    ) -> None:
        del stdout, stderr, text, bufsize, env
        self.returncode = 0
        self.stdout = iter(["fake-download\n"])
        if "spotdl" in Path(cmd[0]).name.lower():
            _simulate_spotdl(cmd)
        elif "yt-dlp" in Path(cmd[0]).name.lower():
            _simulate_ytdlp(cmd)
        else:
            self.returncode = 1
            self.stdout = iter(["unsupported tool\n"])

    def wait(self) -> None:
        return None


@pytest.fixture
def _fake_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / downloader._binary_name("spotdl")).write_bytes(b"")
    (bin_dir / downloader._binary_name("yt-dlp")).write_bytes(b"")
    monkeypatch.setattr(downloader, "_bundled_bin_dir", lambda: bin_dir)
    monkeypatch.setattr(downloader.subprocess, "Popen", _FakePopen)
    return tmp_path / "out"


def test_single_spotify_track_creates_one_mp3(_fake_runtime: Path) -> None:
    code = run_download(
        DownloadRequest(
            url="https://open.spotify.com/track/123",
            output_dir=_fake_runtime,
            tool=ToolChoice.SPOTDL,
        ),
        lambda _: None,
    )
    assert code == 0
    assert len(list(_fake_runtime.glob("*.mp3"))) == 1


def test_spotify_playlist_creates_folder_with_multiple_mp3(_fake_runtime: Path) -> None:
    code = run_download(
        DownloadRequest(
            url="https://open.spotify.com/playlist/abc123",
            output_dir=_fake_runtime,
            tool=ToolChoice.SPOTDL,
        ),
        lambda _: None,
    )
    assert code == 0
    folders = [path for path in _fake_runtime.iterdir() if path.is_dir()]
    assert len(folders) == 1
    assert len(list(folders[0].glob("*.mp3"))) >= 2


def test_single_youtube_video_creates_one_mp4(_fake_runtime: Path) -> None:
    code = run_download(
        DownloadRequest(
            url="https://www.youtube.com/watch?v=3_eashrci3Y",
            output_dir=_fake_runtime,
            tool=ToolChoice.YTDLP,
        ),
        lambda _: None,
    )
    assert code == 0
    assert len(list(_fake_runtime.glob("*.mp4"))) == 1


def test_youtube_playlist_creates_folder_with_multiple_mp4(_fake_runtime: Path) -> None:
    code = run_download(
        DownloadRequest(
            url="https://www.youtube.com/playlist?list=PLxyz123",
            output_dir=_fake_runtime,
            tool=ToolChoice.YTDLP,
        ),
        lambda _: None,
    )
    assert code == 0
    folders = [path for path in _fake_runtime.iterdir() if path.is_dir()]
    assert len(folders) == 1
    assert len(list(folders[0].glob("*.mp4"))) >= 2


def test_ytdlp_uses_basic_non_recode_syntax(_fake_runtime: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []
    original = downloader._ytdlp_cmd

    def _capture(url: str, output_dir: Path, quality: str) -> list[str]:
        cmd = original(url, output_dir, quality)
        captured[:] = cmd
        return cmd

    monkeypatch.setattr(downloader, "_ytdlp_cmd", _capture)
    monkeypatch.setattr(downloader, "_has_working_ffmpeg", lambda *_args, **_kwargs: True)

    code = run_download(
        DownloadRequest(
            url="https://www.youtube.com/watch?v=3_eashrci3Y",
            output_dir=_fake_runtime,
            tool=ToolChoice.YTDLP,
        ),
        lambda _: None,
    )

    assert code == 0
    assert "--recode-video" not in captured
    assert "-x" not in captured
    assert "-f" in captured
    assert "--merge-output-format" in captured
    assert "mp4" in captured


def test_ytdlp_without_ffmpeg_uses_progressive_mp4_fallback(
    _fake_runtime: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[str] = []
    original = downloader._ytdlp_cmd

    def _capture(url: str, output_dir: Path, quality: str) -> list[str]:
        cmd = original(url, output_dir, quality)
        captured[:] = cmd
        return cmd

    monkeypatch.setattr(downloader, "_ytdlp_cmd", _capture)
    monkeypatch.setattr(downloader, "_has_working_ffmpeg", lambda *_args, **_kwargs: False)

    code = run_download(
        DownloadRequest(
            url="https://www.youtube.com/watch?v=3_eashrci3Y",
            output_dir=_fake_runtime,
            tool=ToolChoice.YTDLP,
        ),
        lambda _: None,
    )

    assert code == 0
    assert "--merge-output-format" not in captured
    assert "b[ext=mp4]/best[ext=mp4]/best" in captured
