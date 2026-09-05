"""
Async thumbnail fetching with a disk cache, so re-opening a channel doesn't
re-download every thumbnail. Uses QThreadPool so it never blocks the UI.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import requests
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QPixmap

from .utils import get_app_data_dir

_CACHE_DIR = get_app_data_dir() / "thumb_cache"


def _cache_path(video_id: str) -> Path:
    key = hashlib.sha1(video_id.encode("utf-8")).hexdigest()
    return _CACHE_DIR / f"{key}.jpg"


class _ThumbnailSignals(QObject):
    loaded = Signal(str, QPixmap)  # video_id, pixmap
    failed = Signal(str)


class _ThumbnailTask(QRunnable):
    def __init__(self, video_id: str, url: str):
        super().__init__()
        self.video_id = video_id
        self.url = url
        self.signals = _ThumbnailSignals()

    def run(self) -> None:
        try:
            cache_file = _cache_path(self.video_id)
            if cache_file.exists() and cache_file.stat().st_size > 0:
                data = cache_file.read_bytes()
            else:
                resp = requests.get(self.url, timeout=12)
                resp.raise_for_status()
                data = resp.content
                cache_file.write_bytes(data)

            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                self.signals.loaded.emit(self.video_id, pixmap)
            else:
                self.signals.failed.emit(self.video_id)
        except Exception:
            self.signals.failed.emit(self.video_id)


class ThumbnailLoader(QObject):
    """
    Fire-and-forget thumbnail loading. Connect to `loaded`/`failed` once,
    then call request() for each video row.
    """

    loaded = Signal(str, QPixmap)
    failed = Signal(str)

    def __init__(self, max_concurrent: int = 8, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(max_concurrent)
        self._pending: set[str] = set()

    def request(self, video_id: str, url: str) -> None:
        if not url or video_id in self._pending:
            return
        self._pending.add(video_id)
        task = _ThumbnailTask(video_id, url)
        task.signals.loaded.connect(self._on_loaded)
        task.signals.failed.connect(self._on_failed)
        self._pool.start(task)

    def _on_loaded(self, video_id: str, pixmap: QPixmap) -> None:
        self._pending.discard(video_id)
        self.loaded.emit(video_id, pixmap)

    def _on_failed(self, video_id: str) -> None:
        self._pending.discard(video_id)
        self.failed.emit(video_id)

    def clear_pending(self) -> None:
        self._pending.clear()
