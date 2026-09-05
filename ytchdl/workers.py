"""
QThread workers that wrap yt-dlp so the UI thread never blocks.

FetchWorker  - lists a channel's videos/shorts (metadata only, no download).
DownloadWorker - downloads a chosen set of videos with per-item + overall
                 progress and reports results for history logging.
"""
from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass, field
from typing import Optional

import yt_dlp
from PySide6.QtCore import QThread, Signal

from .utils import sanitize_filename


@dataclass
class VideoInfo:
    video_id: str
    title: str
    url: str
    view_count: Optional[int]
    duration: Optional[int]
    thumbnail: str
    video_type: str  # "video" | "short"
    upload_date: Optional[str] = None


@dataclass
class DownloadItem:
    video: VideoInfo
    channel: str


def _best_thumbnail(entry: dict) -> str:
    thumbs = entry.get("thumbnails") or []
    if thumbs:
        # yt-dlp generally orders thumbnails smallest -> largest; a mid-size
        # one is plenty for a list UI and loads faster than the max-res one.
        try:
            usable = [t for t in thumbs if t.get("url")]
            if usable:
                idx = min(len(usable) - 1, max(0, len(usable) // 2))
                return usable[idx]["url"]
        except Exception:
            pass
    return entry.get("thumbnail") or ""


def _entry_to_video_info(entry: dict, video_type: str) -> Optional[VideoInfo]:
    if not entry:
        return None
    vid = entry.get("id")
    if not vid:
        return None
    url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={vid}"
    return VideoInfo(
        video_id=vid,
        title=entry.get("title") or "(untitled)",
        url=url,
        view_count=entry.get("view_count"),
        duration=entry.get("duration"),
        thumbnail=_best_thumbnail(entry),
        video_type=video_type,
        upload_date=entry.get("upload_date"),
    )


class FetchWorker(QThread):
    """Lists videos for a channel without downloading anything."""

    video_found = Signal(object)      # VideoInfo
    status = Signal(str)
    finished_ok = Signal(int)         # total count found
    failed = Signal(str)

    def __init__(self, base_channel_url: str, mode: str, parent=None):
        """
        mode: "videos", "shorts", or "all"
        """
        super().__init__(parent)
        self.base_channel_url = base_channel_url
        self.mode = mode
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def _tabs_for_mode(self) -> list[tuple[str, str]]:
        if self.mode == "videos":
            return [("videos", "video")]
        if self.mode == "shorts":
            return [("shorts", "short")]
        return [("videos", "video"), ("shorts", "short")]

    def run(self) -> None:
        total = 0
        try:
            ydl_opts = {
                "extract_flat": "in_playlist",
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
                "ignoreerrors": True,
            }
            for tab, video_type in self._tabs_for_mode():
                if self._stop_requested:
                    break
                tab_url = f"{self.base_channel_url}/{tab}"
                self.status.emit(f"Fetching {tab}…")
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(tab_url, download=False)
                except Exception as exc:
                    # A missing tab (e.g. channel has no Shorts) shouldn't
                    # kill the whole fetch when mode == "all".
                    if self.mode == "all":
                        continue
                    raise exc

                if not info:
                    continue
                entries = info.get("entries") or []
                for entry in entries:
                    if self._stop_requested:
                        break
                    vi = _entry_to_video_info(entry, video_type)
                    if vi:
                        total += 1
                        self.video_found.emit(vi)

            if self._stop_requested:
                self.status.emit("Stopped.")
            self.finished_ok.emit(total)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{exc}")


class DownloadWorker(QThread):
    """Downloads a list of DownloadItems sequentially with progress signals."""

    item_started = Signal(str, str)              # video_id, title
    item_progress = Signal(str, float, str)       # video_id, percent(0-100), speed/eta text
    item_finished = Signal(str, bool, str, int)   # video_id, success, filepath_or_error, filesize
    overall_progress = Signal(int, int)           # completed, total
    all_finished = Signal()
    log = Signal(str)

    def __init__(self, items: list[DownloadItem], output_dir: str,
                 quality: str = "best", parent=None):
        super().__init__(parent)
        self.items = items
        self.output_dir = output_dir
        self.quality = quality
        self._stop_requested = False
        self._current_video_id: Optional[str] = None

    def stop(self) -> None:
        self._stop_requested = True

    def _format_selector(self) -> str:
        if self.quality == "audio":
            return "bestaudio/best"
        if self.quality == "1080p":
            return "bv*[height<=1080]+ba/b[height<=1080]/best"
        if self.quality == "720p":
            return "bv*[height<=720]+ba/b[height<=720]/best"
        return "bv*+ba/best"

    def _progress_hook(self, d: dict) -> None:
        if self._stop_requested:
            raise yt_dlp.utils.DownloadCancelled("Cancelled by user")
        vid = self._current_video_id
        if not vid:
            return
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            pct = (downloaded / total * 100) if total else 0.0
            speed = d.get("_speed_str", "").strip() if d.get("_speed_str") else ""
            eta = d.get("_eta_str", "").strip() if d.get("_eta_str") else ""
            text = " ".join(x for x in (speed, eta and f"ETA {eta}") if x)
            self.item_progress.emit(vid, pct, text)
        elif d.get("status") == "finished":
            self.item_progress.emit(vid, 100.0, "Finalizing…")

    def run(self) -> None:
        total = len(self.items)
        completed = 0
        for item in self.items:
            if self._stop_requested:
                break
            video = item.video
            self._current_video_id = video.video_id
            self.item_started.emit(video.video_id, video.title)

            safe_title = sanitize_filename(video.title)
            outtmpl = os.path.join(self.output_dir, f"{safe_title}.%(ext)s")

            ydl_opts = {
                "outtmpl": outtmpl,
                "format": self._format_selector(),
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [self._progress_hook],
                "noplaylist": True,
                "merge_output_format": "mp4" if self.quality != "audio" else None,
                "postprocessors": (
                    [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
                    if self.quality == "audio"
                    else []
                ),
            }
            ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}

            final_path = ""
            success = False
            size = 0
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video.url, download=True)
                    final_path = ydl.prepare_filename(info)
                    if self.quality == "audio":
                        base, _ = os.path.splitext(final_path)
                        candidate = base + ".mp3"
                        if os.path.exists(candidate):
                            final_path = candidate
                    if os.path.exists(final_path):
                        size = os.path.getsize(final_path)
                        success = True
                    else:
                        success = True  # yt-dlp reported success; trust it
            except yt_dlp.utils.DownloadCancelled:
                self.log.emit("Download cancelled.")
                self.item_finished.emit(video.video_id, False, "Cancelled", 0)
                break
            except Exception as exc:  # noqa: BLE001
                self.log.emit(f"Failed: {video.title} — {exc}")
                self.item_finished.emit(video.video_id, False, str(exc), 0)
                completed += 1
                self.overall_progress.emit(completed, total)
                continue

            self.item_finished.emit(video.video_id, success, final_path, size)
            completed += 1
            self.overall_progress.emit(completed, total)

        self.all_finished.emit()
