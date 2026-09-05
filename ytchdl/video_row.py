"""Custom row widget used inside the video QListWidget."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .utils import format_count, format_duration
from .workers import VideoInfo

THUMB_W, THUMB_H = 120, 68


class VideoRowWidget(QWidget):
    toggled = Signal(str, bool)  # video_id, checked

    def __init__(self, video: VideoInfo, already_downloaded: bool, parent=None):
        super().__init__(parent)
        self.video = video
        self._downloaded = already_downloaded
        self.setObjectName("videoRowDownloaded" if already_downloaded else "videoRow")

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 8, 12, 8)
        root.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setFixedWidth(20)
        self.checkbox.stateChanged.connect(
            lambda state: self.toggled.emit(self.video.video_id, state == Qt.CheckState.Checked.value)
        )
        root.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignVCenter)

        self.thumb_label = QLabel()
        self.thumb_label.setObjectName("thumbLabel")
        self.thumb_label.setFixedSize(THUMB_W, THUMB_H)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setText("…")
        root.addWidget(self.thumb_label, 0)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        self.title_label = QLabel(video.title)
        self.title_label.setObjectName("videoTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_col.addWidget(self.title_label)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)
        type_badge = "Short" if video.video_type == "short" else "Video"
        meta_text = f"{type_badge}  ·  {format_count(video.view_count)} views  ·  {format_duration(video.duration)}"
        self.meta_label = QLabel(meta_text)
        self.meta_label.setObjectName("videoMeta")
        meta_row.addWidget(self.meta_label)
        meta_row.addStretch(1)

        self.badge_label = QLabel("✓ Downloaded" if already_downloaded else "")
        self.badge_label.setObjectName("downloadedBadge")
        meta_row.addWidget(self.badge_label)
        text_col.addLayout(meta_row)

        self.progress = QProgressBar()
        self.progress.setObjectName("miniProgress")
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        text_col.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setObjectName("videoMeta")
        self.status_label.setVisible(False)
        text_col.addWidget(self.status_label)

        root.addLayout(text_col, 1)

    # -- external API -----------------------------------------------------
    def set_checked(self, checked: bool) -> None:
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            THUMB_W, THUMB_H, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.thumb_label.setPixmap(scaled)
        self.thumb_label.setText("")

    def set_thumbnail_failed(self) -> None:
        self.thumb_label.setText("No\nimage")

    def start_progress(self) -> None:
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Starting…")
        self.checkbox.setEnabled(False)

    def update_progress(self, percent: float, text: str) -> None:
        self.progress.setValue(int(max(0, min(100, percent))))
        self.status_label.setText(text or f"{percent:.0f}%")

    def finish_progress(self, success: bool, message: str = "") -> None:
        self.progress.setVisible(False)
        self.checkbox.setEnabled(True)
        if success:
            self.status_label.setVisible(False)
            self.badge_label.setText("✓ Downloaded")
            self.setObjectName("videoRowDownloaded")
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            self.status_label.setVisible(True)
            self.status_label.setText(f"Failed: {message}"[:120])
