"""Dialog that lists all previously downloaded videos."""
from __future__ import annotations

import os
import subprocess
import sys
import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .history import HistoryManager
from .utils import format_bytes


def _open_in_file_manager(path: str) -> None:
    folder = os.path.dirname(path) if os.path.isfile(path) else path
    if not folder or not os.path.exists(folder):
        return
    if sys.platform == "win32":
        os.startfile(folder)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.Popen(["open", folder])
    else:
        subprocess.Popen(["xdg-open", folder])


class HistoryDialog(QDialog):
    def __init__(self, history: HistoryManager, parent=None):
        super().__init__(parent)
        self.history = history
        self.setWindowTitle("Download History")
        self.resize(820, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(QLabel(f"<b>Download History</b>"))
        header.addStretch(1)
        clear_btn = QPushButton("Clear History")
        clear_btn.setObjectName("dangerButton")
        clear_btn.clicked.connect(self._clear_all)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Title", "Channel", "Type", "Size", "Downloaded"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._open_selected)
        layout.addWidget(self.table)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("Double-click a row to open its folder."))
        footer.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        layout.addLayout(footer)

        self._reload()

    def _reload(self) -> None:
        entries = self.history.all_entries()
        self.table.setRowCount(len(entries))
        self._entries = entries
        for row, e in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(e["title"]))
            self.table.setItem(row, 1, QTableWidgetItem(e["channel"] or ""))
            self.table.setItem(row, 2, QTableWidgetItem(e["video_type"] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(format_bytes(e["filesize"])))
            ts = e["downloaded_at"]
            ts_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else ""
            self.table.setItem(row, 4, QTableWidgetItem(ts_str))

    def _open_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        path = self._entries[row]["filepath"]
        if path and os.path.exists(path):
            _open_in_file_manager(path)
        else:
            QMessageBox.information(self, "Not found", "That file no longer exists on disk.")

    def _clear_all(self) -> None:
        confirm = QMessageBox.question(
            self, "Clear history",
            "This removes all history entries (files on disk are not deleted). Continue?",
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.history.clear_all()
            self._reload()
