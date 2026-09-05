"""
Builds a standalone, single-file executable using PyInstaller.

Usage:
    pip install -r requirements.txt
    python build.py

Output lands in dist/YTChannelDownloader(.exe)
"""
from __future__ import annotations

import os
import shutil
import sys

import PyInstaller.__main__

APP_NAME = "YTChannelDownloader"
HERE = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(HERE, "ytchdl", "assets", "icon.ico")
ASSETS_DIR = os.path.join(HERE, "ytchdl", "assets")


def main() -> None:
    # Clean previous builds so stale artifacts never sneak into a release.
    for folder in ("build", "dist"):
        path = os.path.join(HERE, folder)
        if os.path.exists(path):
            shutil.rmtree(path)
    spec_file = os.path.join(HERE, f"{APP_NAME}.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # PyInstaller's --add-data separator is ';' on Windows and ':' elsewhere.
    data_sep = ";" if sys.platform == "win32" else ":"

    args = [
        os.path.join(HERE, "main.py"),
        f"--name={APP_NAME}",
        "--onefile",
        "--windowed",              # no console window on Windows/macOS
        "--noconfirm",
        "--clean",
        "--collect-all=yt_dlp",    # yt-dlp dynamically loads its extractors
    ]

    if os.path.exists(ASSETS_DIR):
        args.append(f"--add-data={ASSETS_DIR}{data_sep}ytchdl/assets")

    if os.path.exists(ICON_PATH):
        args.append(f"--icon={ICON_PATH}")
    elif sys.platform == "win32":
        print("Note: no icon found at ytchdl/assets/icon.ico — building with the default icon.")

    PyInstaller.__main__.run(args)

    print()
    print("=" * 60)
    print(f"Build complete. Find your executable in: {os.path.join(HERE, 'dist')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
