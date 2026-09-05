"""Modern dark theme stylesheet for the app."""

STYLESHEET = """
* {
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    outline: none;
}

QWidget {
    background-color: #14151a;
    color: #e7e9ee;
    font-size: 13px;
}

QMainWindow, #centralWidget {
    background-color: #14151a;
}

/* ---------- Top bar ---------- */
QLineEdit {
    background-color: #1d1f27;
    border: 1px solid #2c2f3a;
    border-radius: 8px;
    padding: 9px 12px;
    color: #f2f3f7;
    selection-background-color: #6c5ce7;
}
QLineEdit:focus {
    border: 1px solid #6c5ce7;
}

QComboBox {
    background-color: #1d1f27;
    border: 1px solid #2c2f3a;
    border-radius: 8px;
    padding: 8px 10px;
    color: #f2f3f7;
    min-width: 110px;
}
QComboBox:hover { border: 1px solid #3a3e4d; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #1d1f27;
    border: 1px solid #2c2f3a;
    selection-background-color: #6c5ce7;
    color: #f2f3f7;
    outline: none;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: #262a36;
    border: 1px solid #343847;
    border-radius: 8px;
    padding: 9px 16px;
    color: #f2f3f7;
    font-weight: 600;
}
QPushButton:hover { background-color: #2f3442; border-color: #454b5e; }
QPushButton:pressed { background-color: #23262f; }
QPushButton:disabled { color: #5b5f6b; background-color: #1c1e26; border-color: #262933; }

QPushButton#primaryButton {
    background-color: #6c5ce7;
    border: 1px solid #7d6ef0;
    color: #ffffff;
}
QPushButton#primaryButton:hover { background-color: #7b6cf0; }
QPushButton#primaryButton:pressed { background-color: #5d4fd1; }
QPushButton#primaryButton:disabled { background-color: #3a3550; border-color: #3a3550; color: #8a86a8; }

QPushButton#dangerButton {
    background-color: transparent;
    border: 1px solid #4a3038;
    color: #ff8a8a;
}
QPushButton#dangerButton:hover { background-color: #3a2229; }

QPushButton#flatButton {
    background-color: transparent;
    border: none;
    color: #9aa0b4;
    font-weight: 500;
    padding: 6px 10px;
}
QPushButton#flatButton:hover { color: #f2f3f7; }

/* ---------- List ---------- */
QListWidget {
    background-color: #17181f;
    border: 1px solid #23252e;
    border-radius: 10px;
    padding: 4px;
}
QListWidget::item {
    border: none;
    border-radius: 8px;
    margin: 2px;
}
QListWidget::item:selected { background-color: transparent; }

#videoRow {
    background-color: #1b1c24;
    border-radius: 10px;
    border: 1px solid #24262f;
}
#videoRow:hover { border: 1px solid #3a3e4d; }
#videoRowDownloaded {
    background-color: #171c1a;
    border-radius: 10px;
    border: 1px solid #223228;
}

#videoTitle {
    color: #f2f3f7;
    font-weight: 600;
    font-size: 13px;
}
#videoMeta {
    color: #8b8f9e;
    font-size: 12px;
}
#downloadedBadge {
    color: #5fd487;
    font-size: 11px;
    font-weight: 700;
}
#thumbLabel {
    background-color: #0f1015;
    border-radius: 6px;
    border: 1px solid #23252e;
}

/* ---------- Progress ---------- */
QProgressBar {
    background-color: #1d1f27;
    border: 1px solid #2c2f3a;
    border-radius: 7px;
    text-align: center;
    color: #d7d9e2;
    height: 14px;
}
QProgressBar::chunk {
    background-color: #6c5ce7;
    border-radius: 6px;
}

#miniProgress {
    background-color: #14151a;
    border: none;
    border-radius: 4px;
    height: 6px;
}
#miniProgress::chunk {
    background-color: #5fd487;
    border-radius: 4px;
}

/* ---------- Misc ---------- */
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #3a3e4d;
    background: #1d1f27;
}
QCheckBox::indicator:checked {
    background-color: #6c5ce7;
    border: 1px solid #6c5ce7;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #33364258;
    background-color: #343847;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background-color: #454b5e; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QLabel#sectionLabel {
    color: #8b8f9e;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#statusLabel {
    color: #9aa0b4;
    font-size: 12px;
}

QLabel#titleLabel {
    color: #f2f3f7;
    font-size: 18px;
    font-weight: 700;
}

QLabel#logoDot {
    color: #6c5ce7;
    font-size: 18px;
    font-weight: 700;
}

QDialog { background-color: #14151a; }

QTableWidget {
    background-color: #17181f;
    border: 1px solid #23252e;
    border-radius: 10px;
    gridline-color: #23252e;
    color: #e7e9ee;
}
QHeaderView::section {
    background-color: #1d1f27;
    color: #9aa0b4;
    border: none;
    padding: 8px;
    font-weight: 600;
}
QTableWidget::item:selected {
    background-color: #2a2e3d;
}

QToolTip {
    background-color: #23252e;
    color: #f2f3f7;
    border: 1px solid #343847;
    padding: 4px 8px;
    border-radius: 4px;
}
"""
