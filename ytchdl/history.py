"""
Persistent download history, backed by SQLite. Thread-safe for the simple
read/write patterns used by this app (one writer thread at a time).
"""
from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .utils import get_app_data_dir


@dataclass
class HistoryEntry:
    video_id: str
    title: str
    url: str
    channel: str
    video_type: str
    filepath: str
    filesize: int
    downloaded_at: float
    status: str  # "completed" | "failed"


class HistoryManager:
    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or (get_app_data_dir() / "history.db")
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    channel TEXT,
                    video_type TEXT,
                    filepath TEXT,
                    filesize INTEGER,
                    downloaded_at REAL,
                    status TEXT
                )
                """
            )
            conn.commit()

    def is_downloaded(self, video_id: str) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM history WHERE video_id = ? AND status = 'completed'",
                (video_id,),
            ).fetchone()
            return row is not None

    def get_entry(self, video_id: str) -> Optional[dict]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM history WHERE video_id = ?", (video_id,)
            ).fetchone()
            return dict(row) if row else None

    def add_or_update(self, entry: HistoryEntry) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO history
                    (video_id, title, url, channel, video_type, filepath,
                     filesize, downloaded_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    title=excluded.title,
                    url=excluded.url,
                    channel=excluded.channel,
                    video_type=excluded.video_type,
                    filepath=excluded.filepath,
                    filesize=excluded.filesize,
                    downloaded_at=excluded.downloaded_at,
                    status=excluded.status
                """,
                (
                    entry.video_id,
                    entry.title,
                    entry.url,
                    entry.channel,
                    entry.video_type,
                    entry.filepath,
                    entry.filesize,
                    entry.downloaded_at,
                    entry.status,
                ),
            )
            conn.commit()

    def all_entries(self, limit: int = 2000) -> list[dict]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY downloaded_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_entry(self, video_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM history WHERE video_id = ?", (video_id,))
            conn.commit()

    def clear_all(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM history")
            conn.commit()

    @staticmethod
    def now() -> float:
        return time.time()
