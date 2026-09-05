"""
Shared utility helpers: app-data paths, filename sanitizing, number
formatting, and PyInstaller-safe resource resolution.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


APP_NAME = "YTChannelDownloader"
GITHUB_URL = "https://github.com/Sewer2K"


def is_frozen() -> bool:
    """True when running from a PyInstaller-built executable."""
    return getattr(sys, "frozen", False)


def resource_path(relative_path: str) -> str:
    """
    Resolve a path to a bundled resource (e.g. icon) whether running from
    source or from a PyInstaller onefile executable.
    """
    if is_frozen():
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_app_data_dir() -> Path:
    """
    Persistent, writable directory for the database, cache, and settings.
    Lives outside the exe/install folder so it survives updates/reinstalls.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home())
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")

    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    (path / "thumb_cache").mkdir(parents=True, exist_ok=True)
    return path


_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str, max_length: int = 150) -> str:
    """Make a string safe to use as a Windows/macOS/Linux filename."""
    if not name:
        return "untitled"
    cleaned = _INVALID_CHARS.sub("_", name).strip().rstrip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = "untitled"
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    return cleaned


def format_count(n) -> str:
    """Format a view/like count as a short human string, e.g. 1.2M."""
    if n is None:
        return "—"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    sign = "-" if n < 0 else ""
    n = abs(n)
    for unit, div in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if n >= div:
            val = n / div
            formatted = f"{val:.1f}".rstrip("0").rstrip(".")
            return f"{sign}{formatted}{unit}"
    return f"{sign}{int(n)}"


def format_duration(seconds) -> str:
    """Format a duration in seconds as H:MM:SS or M:SS."""
    if seconds is None:
        return "—"
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return "—"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_bytes(n) -> str:
    if not n:
        return ""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def normalize_channel_input(raw: str) -> str:
    """
    Accept a channel URL, an @handle, or a bare handle/name, and return a
    normalized base channel URL (without /videos or /shorts suffix).
    """
    raw = raw.strip()
    if not raw:
        return raw

    # Strip an existing tab suffix if the user pasted a /videos or /shorts URL.
    for suffix in ("/videos", "/shorts", "/streams", "/featured", "/playlists", "/community", "/about"):
        if raw.rstrip("/").endswith(suffix):
            raw = raw.rstrip("/")[: -len(suffix)]
            break

    if raw.startswith("http://") or raw.startswith("https://"):
        return raw.rstrip("/")

    if raw.startswith("@"):
        return f"https://www.youtube.com/{raw}"

    if raw.startswith("youtube.com") or raw.startswith("www.youtube.com"):
        return f"https://{raw}".rstrip("/")

    # Bare word -> treat as a handle.
    return f"https://www.youtube.com/@{raw}"
