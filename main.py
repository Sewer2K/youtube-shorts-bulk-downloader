"""
YT Channel Downloader — entry point.

Run from source:
    python main.py

Build a standalone Windows/Mac/Linux executable:
    python build.py
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ytchdl.main_window import MainWindow
from ytchdl.utils import resource_path


def main() -> int:
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("YTChannelDownloader")
    app.setOrganizationName("SewerTools")

    app_icon = QIcon(resource_path("ytchdl/assets/icon.ico"))
    app.setWindowIcon(app_icon)

    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
