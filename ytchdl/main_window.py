from __future__ import annotations

import os

from PySide6.QtCore import QSettings, Qt, QSize, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .history import HistoryEntry, HistoryManager
from .history_dialog import HistoryDialog
from .styles import STYLESHEET
from .thumbnails import ThumbnailLoader
from .utils import GITHUB_URL, normalize_channel_input, resource_path, sanitize_filename
from .video_row import VideoRowWidget
from .workers import DownloadItem, DownloadWorker, FetchWorker, VideoInfo

ORG_NAME = "SewerTools"
APP_NAME = "YTChannelDownloader"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Channel Downloader")
        self.resize(1080, 760)
        self.setStyleSheet(STYLESHEET)

        self.app_icon = QIcon(resource_path("ytchdl/assets/icon.ico"))
        self.setWindowIcon(self.app_icon)

        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.history = HistoryManager()
        self.thumb_loader = ThumbnailLoader()
        self.thumb_loader.loaded.connect(self._on_thumb_loaded)
        self.thumb_loader.failed.connect(self._on_thumb_failed)

        self.fetch_worker: FetchWorker | None = None
        self.download_worker: DownloadWorker | None = None

        self.videos: dict[str, VideoInfo] = {}
        self.rows: dict[str, VideoRowWidget] = {}
        self.list_items: dict[str, QListWidgetItem] = {}
        self.selected_ids: set[str] = set()
        self.current_channel_display = ""

        self._build_ui()
        self._restore_settings()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # Header ------------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        logo_label = QLabel()
        logo_label.setPixmap(self.app_icon.pixmap(28, 28))
        header_row.addWidget(logo_label)

        title = QLabel("YT Channel Downloader")
        title.setObjectName("titleLabel")
        header_row.addWidget(title)
        header_row.addStretch(1)

        self.github_btn = QPushButton(" Sewer2K")
        self.github_btn.setObjectName("flatButton")
        github_icon_path = resource_path("ytchdl/assets/link_icon.png")
        if os.path.exists(github_icon_path):
            self.github_btn.setIcon(QIcon(github_icon_path))
        self.github_btn.setToolTip(GITHUB_URL)
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        header_row.addWidget(self.github_btn)

        self.history_btn = QPushButton("History")
        self.history_btn.setObjectName("flatButton")
        self.history_btn.clicked.connect(self._open_history)
        header_row.addWidget(self.history_btn)
        root.addLayout(header_row)

        # Channel input row --------------------------------------------
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Paste a channel URL or @handle…")
        self.channel_input.returnPressed.connect(self._start_fetch)
        input_row.addWidget(self.channel_input, 1)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("All (Videos + Shorts)", "all")
        self.mode_combo.addItem("Videos only", "videos")
        self.mode_combo.addItem("Shorts only", "shorts")
        input_row.addWidget(self.mode_combo)

        self.fetch_btn = QPushButton("Fetch Channel")
        self.fetch_btn.setObjectName("primaryButton")
        self.fetch_btn.clicked.connect(self._start_fetch)
        input_row.addWidget(self.fetch_btn)
        root.addLayout(input_row)

        # Toolbar row ----------------------------------------------------
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(8)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setObjectName("flatButton")
        self.select_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        toolbar_row.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("Select None")
        self.select_none_btn.setObjectName("flatButton")
        self.select_none_btn.clicked.connect(lambda: self._set_all_checked(False))
        toolbar_row.addWidget(self.select_none_btn)

        self.select_new_btn = QPushButton("Select Not Downloaded")
        self.select_new_btn.setObjectName("flatButton")
        self.select_new_btn.clicked.connect(self._select_not_downloaded)
        toolbar_row.addWidget(self.select_new_btn)

        toolbar_row.addStretch(1)

        self.count_label = QLabel("0 videos")
        self.count_label.setObjectName("statusLabel")
        toolbar_row.addWidget(self.count_label)
        root.addLayout(toolbar_row)

        # Video list -------------------------------------------------
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(0)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        root.addWidget(self.list_widget, 1)

        # Output + quality row -----------------------------------------
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        out_label = QLabel("Save to:")
        out_label.setObjectName("statusLabel")
        out_row.addWidget(out_label)

        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Choose a download folder…")
        out_row.addWidget(self.output_dir_input, 1)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_output_dir)
        out_row.addWidget(browse_btn)

        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Best quality", "best")
        self.quality_combo.addItem("1080p max", "1080p")
        self.quality_combo.addItem("720p max", "720p")
        self.quality_combo.addItem("Audio only (MP3)", "audio")
        out_row.addWidget(self.quality_combo)
        root.addLayout(out_row)

        # Download / stop row --------------------------------------------
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("statusLabel")
        action_row.addWidget(self.status_label, 1)

        self.overall_progress = QProgressBar()
        self.overall_progress.setFixedWidth(220)
        self.overall_progress.setValue(0)
        self.overall_progress.setVisible(False)
        action_row.addWidget(self.overall_progress)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.clicked.connect(self._stop_all)
        self.stop_btn.setEnabled(False)
        action_row.addWidget(self.stop_btn)

        self.download_btn = QPushButton("Download Selected")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.clicked.connect(self._start_download)
        self.download_btn.setEnabled(False)
        action_row.addWidget(self.download_btn)

        root.addLayout(action_row)

    # ------------------------------------------------------------ settings
    def _restore_settings(self) -> None:
        last_dir = self.settings.value("output_dir", "")
        if last_dir:
            self.output_dir_input.setText(last_dir)
        last_channel = self.settings.value("last_channel", "")
        if last_channel:
            self.channel_input.setText(last_channel)
        last_quality = self.settings.value("quality", "best")
        idx = self.quality_combo.findData(last_quality)
        if idx >= 0:
            self.quality_combo.setCurrentIndex(idx)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self.settings.setValue("output_dir", self.output_dir_input.text().strip())
        self.settings.setValue("last_channel", self.channel_input.text().strip())
        self.settings.setValue("quality", self.quality_combo.currentData())
        if self.fetch_worker and self.fetch_worker.isRunning():
            self.fetch_worker.stop()
            self.fetch_worker.wait(2000)
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.download_worker.wait(2000)
        super().closeEvent(event)

    # ------------------------------------------------------------ fetching
    def _start_fetch(self) -> None:
        raw = self.channel_input.text().strip()
        if not raw:
            QMessageBox.warning(self, "Missing channel", "Paste a channel URL or @handle first.")
            return
        if self.fetch_worker and self.fetch_worker.isRunning():
            return

        base_url = normalize_channel_input(raw)
        self.current_channel_display = raw
        mode = self.mode_combo.currentData()

        self._clear_list()
        self.status_label.setText("Fetching channel…")
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Fetching…")

        self.fetch_worker = FetchWorker(base_url, mode)
        self.fetch_worker.video_found.connect(self._on_video_found)
        self.fetch_worker.status.connect(lambda s: self.status_label.setText(s))
        self.fetch_worker.finished_ok.connect(self._on_fetch_finished)
        self.fetch_worker.failed.connect(self._on_fetch_failed)
        self.fetch_worker.start()

    def _clear_list(self) -> None:
        self.list_widget.clear()
        self.videos.clear()
        self.rows.clear()
        self.list_items.clear()
        self.selected_ids.clear()
        self.thumb_loader.clear_pending()
        self._update_count_label()
        self.download_btn.setEnabled(False)

    def _on_video_found(self, video: VideoInfo) -> None:
        self.videos[video.video_id] = video
        already = self.history.is_downloaded(video.video_id)

        row_widget = VideoRowWidget(video, already)
        row_widget.toggled.connect(self._on_row_toggled)

        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(0, 96))
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, row_widget)

        self.rows[video.video_id] = row_widget
        self.list_items[video.video_id] = item

        if video.thumbnail:
            self.thumb_loader.request(video.video_id, video.thumbnail)

        self._update_count_label()
        self.download_btn.setEnabled(True)

    def _on_fetch_finished(self, total: int) -> None:
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Channel")
        if total == 0:
            self.status_label.setText("No videos found. Check the URL and try again.")
        else:
            self.status_label.setText(f"Found {total} video(s).")

    def _on_fetch_failed(self, message: str) -> None:
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Channel")
        self.status_label.setText("Fetch failed.")
        QMessageBox.critical(self, "Fetch failed", message)

    def _update_count_label(self) -> None:
        total = len(self.videos)
        selected = len(self.selected_ids)
        self.count_label.setText(f"{total} video(s) · {selected} selected")

    # ------------------------------------------------------------ thumbs
    def _on_thumb_loaded(self, video_id: str, pixmap) -> None:
        row = self.rows.get(video_id)
        if row:
            row.set_thumbnail(pixmap)

    def _on_thumb_failed(self, video_id: str) -> None:
        row = self.rows.get(video_id)
        if row:
            row.set_thumbnail_failed()

    # ------------------------------------------------------------ selection
    def _on_row_toggled(self, video_id: str, checked: bool) -> None:
        if checked:
            self.selected_ids.add(video_id)
        else:
            self.selected_ids.discard(video_id)
        self._update_count_label()

    def _set_all_checked(self, checked: bool) -> None:
        for vid, row in self.rows.items():
            row.set_checked(checked)
            if checked:
                self.selected_ids.add(vid)
            else:
                self.selected_ids.discard(vid)
        self._update_count_label()

    def _select_not_downloaded(self) -> None:
        for vid, row in self.rows.items():
            already = self.history.is_downloaded(vid)
            row.set_checked(not already)
            if already:
                self.selected_ids.discard(vid)
            else:
                self.selected_ids.add(vid)
        self._update_count_label()

    # ------------------------------------------------------------ output dir
    def _browse_output_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Choose download folder", self.output_dir_input.text().strip() or os.path.expanduser("~")
        )
        if chosen:
            self.output_dir_input.setText(chosen)

    # ------------------------------------------------------------ download
    def _start_download(self) -> None:
        if not self.selected_ids:
            QMessageBox.information(self, "Nothing selected", "Select at least one video to download.")
            return
        out_dir = self.output_dir_input.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "No output folder", "Choose a download folder first.")
            return
        os.makedirs(out_dir, exist_ok=True)

        if self.download_worker and self.download_worker.isRunning():
            QMessageBox.information(self, "Busy", "A download is already in progress.")
            return

        quality = self.quality_combo.currentData()
        items = [
            DownloadItem(video=self.videos[vid], channel=self.current_channel_display)
            for vid in self.selected_ids
            if vid in self.videos
        ]

        self.overall_progress.setVisible(True)
        self.overall_progress.setRange(0, len(items))
        self.overall_progress.setValue(0)
        self.download_btn.setEnabled(False)
        self.fetch_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText(f"Downloading 0/{len(items)}…")

        self.download_worker = DownloadWorker(items, out_dir, quality)
        self.download_worker.item_started.connect(self._on_item_started)
        self.download_worker.item_progress.connect(self._on_item_progress)
        self.download_worker.item_finished.connect(self._on_item_finished)
        self.download_worker.overall_progress.connect(self._on_overall_progress)
        self.download_worker.all_finished.connect(self._on_all_finished)
        self.download_worker.log.connect(lambda s: self.status_label.setText(s))
        self.download_worker.start()

    def _on_item_started(self, video_id: str, title: str) -> None:
        row = self.rows.get(video_id)
        if row:
            row.start_progress()

    def _on_item_progress(self, video_id: str, percent: float, text: str) -> None:
        row = self.rows.get(video_id)
        if row:
            row.update_progress(percent, text)

    def _on_item_finished(self, video_id: str, success: bool, path_or_error: str, size: int) -> None:
        row = self.rows.get(video_id)
        if row:
            row.finish_progress(success, "" if success else path_or_error)

        video = self.videos.get(video_id)
        if success and video:
            entry = HistoryEntry(
                video_id=video_id,
                title=video.title,
                url=video.url,
                channel=self.current_channel_display,
                video_type=video.video_type,
                filepath=path_or_error,
                filesize=size,
                downloaded_at=HistoryManager.now(),
                status="completed",
            )
            self.history.add_or_update(entry)

    def _on_overall_progress(self, completed: int, total: int) -> None:
        self.overall_progress.setValue(completed)
        self.status_label.setText(f"Downloading {completed}/{total}…")

    def _on_all_finished(self) -> None:
        self.download_btn.setEnabled(True)
        self.fetch_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.overall_progress.setVisible(False)
        self.status_label.setText("Download complete.")

    def _stop_all(self) -> None:
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.status_label.setText("Stopping…")
        if self.fetch_worker and self.fetch_worker.isRunning():
            self.fetch_worker.stop()

    # ------------------------------------------------------------ history
    def _open_history(self) -> None:
        dlg = HistoryDialog(self.history, self)
        dlg.exec()
