# PacifierShop

PacifierShop is a small Python desktop app that wraps `spotdl` and `yt-dlp` behind a simple GUI to download media from Spotify or YouTube URLs.

## Disclaimer

This repository is a **practice project for vibe coding** and learning.

- I am **not affiliated** with Spotify, YouTube, `spotdl`, `yt-dlp`, or FFmpeg.
- I bear **no legal responsibility** for how this software is used.
- You are responsible for complying with platform Terms of Service, local laws, and copyright rules in your jurisdiction.

## Features

- Detects URL type and routes automatically:
  - Spotify links -> `spotdl`
  - YouTube links -> `yt-dlp`
- Lets you select output folder from the UI
- Supports quality presets (`max`, `efficient`)
- Streams command logs in-app
- Handles single links and playlist links

## Tech Stack / Credits

Thanks to the maintainers and contributors of:

- [Python](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [spotDL](https://github.com/spotDL/spotify-downloader)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
- [PyInstaller](https://pyinstaller.org/)
- [pytest](https://docs.pytest.org/)
- [Conda](https://conda.io/)

## Setup (Conda)

```bash
conda env update -n dtu02450 -f environment.yml
```

## Run (Development)

```bash
conda run -n dtu02450 python scripts/run.py
```

## Tests

Run locally:

```bash
conda run -n dtu02450 pytest -q
```

## CI Checks (Every Push)

GitHub Actions is configured to run the test suite on:

- every `push`
- every `pull_request`

Workflow file:

- `.github/workflows/ci.yml`

## Vendor Binaries

```bash
conda run -n dtu02450 python scripts/vendor_binaries.py
```

This vendors `spotdl`, `yt-dlp`, `ffmpeg`, and `ffprobe` into `resources/bin`.

## Build App Bundle

```bash
conda run -n dtu02450 python scripts/build.py
```

Build outputs:

- macOS: `dist/PacifierShop.app`
- other platforms: `dist/PacifierShop/`

## Project Layout

```text
src/pacifiershop/      app code
tests/                 automated tests
scripts/               run/build/vendor helper scripts
resources/             app assets and vendored binaries
.github/workflows/     CI workflows
```

## License

This project is licensed under the MIT License. See `LICENSE`.
