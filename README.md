<p align="center">
  <img src="resources/pacifier.png" alt="PacifierShop icon" width="88" />
</p>
<p align="center">
  <em>"Because silence became unberable in the post-capitalist 2026"</em>
</p>
<p align="center">
  A vibe coding test.
</p>

# PacifierShop

PacifierShop is a lightweight Python desktop app that wraps `spotdl` and `yt-dlp` in a single GUI for Spotify and YouTube links.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Testing and CI](#testing-and-ci)
- [Acknowledgements](#acknowledgements)
- [Legal Disclaimer](#legal-disclaimer)
- [License](#license)

## Overview

PacifierShop routes media URLs automatically:

- Spotify links use `spotdl`
- YouTube links use `yt-dlp`

The app supports both single links and playlist links, writes downloads to a chosen folder, and streams logs in-app.

## Features

- Automatic routing by URL type
- Quality presets: `max` and `efficient`
- Playlist-aware output organization
- Desktop app packaging via PyInstaller

## Requirements

- Python `3.11`
- `pip` or Conda (Anaconda or Miniconda)
- Platform support for the bundled binary tooling (`spotdl`, `yt-dlp`, `ffmpeg`, `ffprobe`)
- `ffmpeg` and `ffprobe` available in your environment `PATH` when vendoring binaries

## Installation

### Option A: pip

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest pyinstaller
```

### Option B: Conda

```bash
conda env create -f environment.yml
conda activate pacifiershop
```

## Usage

Run the app:

```bash
python scripts/run.py
```

Build a standalone app bundle:

```bash
python scripts/build.py
```

Expected build output:

- macOS: `dist/PacifierShop.app`
- Other platforms: `dist/PacifierShop/`

## Testing and CI

Run tests locally:

```bash
pytest -q
```

Automated checks run on `pull_request` and non-`main` pushes via `.github/workflows/ci.yml`.

Automated releases run only for release-candidate tags via `.github/workflows/release.yml`.

Tag format:

```bash
release-<candidate-name>
```

Release assets:

- `PacifierShop-windows-<tag>.zip` (Windows executable package)
- `PacifierShop-macos-<tag>.dmg` (DMG containing `PacifierShop.app`)

## Acknowledgements

Thanks to the maintainers and contributors of:

- [Python](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [spotDL](https://github.com/spotDL/spotify-downloader)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
- [PyInstaller](https://pyinstaller.org/)
- [pytest](https://docs.pytest.org/)
- [Conda](https://conda.io/)

Icon credit: `resources/pacifier.png` is included as a project asset in this repository.

## Legal Disclaimer

This repository is for practice and vibe-coding purposes.

- The project is not affiliated with Spotify, YouTube, `spotdl`, `yt-dlp`, FFmpeg, or their maintainers.
- The author bears no legal responsibility for platform misuse or copyright violations.
- Users are responsible for complying with platform Terms of Service, local law, and copyright rules.

## License

MIT License. See `LICENSE`.
