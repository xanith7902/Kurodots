#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)


DOTS = "/home/kasonf/Projects/kurodots"
STATE_FILE = Path(f"{DOTS}/themes/kuro/stream-source.json")


SOURCES = [
    {
        "name": "Local Library",
        "tag": "Best for downloaded/legal files",
        "command": "xdg-open ~/Videos",
    },
    {
        "name": "Jellyfin",
        "tag": "Self-hosted media server",
        "command": "xdg-open http://localhost:8096",
    },
    {
        "name": "Plex",
        "tag": "Personal streaming server",
        "command": "xdg-open https://app.plex.tv",
    },
    {
        "name": "YouTube",
        "tag": "Free/legal streaming",
        "command": "xdg-open https://youtube.com",
    },
    {
        "name": "Netflix",
        "tag": "Subscription service",
        "command": "xdg-open https://netflix.com",
    },
    {
        "name": "Prime Video",
        "tag": "Subscription service",
        "command": "xdg-open https://primevideo.com",
    },
    {
        "name": "Disney+",
        "tag": "Subscription service",
        "command": "xdg-open https://disneyplus.com",
    },
    {
        "name": "Crunchyroll",
        "tag": "Anime streaming",
        "command": "xdg-open https://crunchyroll.com",
    },
]


def spawn(cmd: str):
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def load_state():
    if not STATE_FILE.exists():
        return {"selected": 0, "working": None}

    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"selected": 0, "working": None}


def save_state(data):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2))


class SourceRow(QPushButton):
    def __init__(self, name: str, tag: str):
        super().__init__()
        self.name = name
        self.tag = tag
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setObjectName("SourceRow")
        self.setText(f"{name}\n{tag}")


class KuroStream(QWidget):
    def __init__(self):
        super().__init__()

        self.state = load_state()
        self.selected = int(self.state.get("selected", 0))
        self.working = self.state.get("working")
        self.rows = []

        self.setWindowTitle("Kuro Stream")
        self.setFixedSize(520, 620)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setObjectName("Root")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 16, 18, 16)

        title_box = QVBoxLayout()

        self.title = QLabel("Stream Ready!")
        self.title.setObjectName("Title")

        self.subtitle = QLabel("Choose a legal/local source")
        self.subtitle.setObjectName("Subtitle")

        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)

        close = QPushButton("×")
        close.setObjectName("CloseButton")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(self.close)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        header_layout.addWidget(close)

        root.addWidget(header)

        body = QFrame()
        body.setObjectName("Body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(10)

        self.rows_box = QVBoxLayout()
        self.rows_box.setSpacing(10)

        for i, source in enumerate(SOURCES):
            row = SourceRow(source["name"], source["tag"])
            row.clicked.connect(lambda checked=False, index=i: self.choose(index))
            self.rows.append(row)
            self.rows_box.addWidget(row)

        body_layout.addLayout(self.rows_box)

        root.addWidget(body, 1)

        footer = QFrame()
        footer.setObjectName("Footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 14, 16, 14)
        footer_layout.setSpacing(12)

        self.mark_btn = QPushButton("Mark as Working")
        self.mark_btn.setObjectName("MarkButton")
        self.mark_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mark_btn.clicked.connect(self.mark_working)

        self.try_btn = QPushButton("Try Next")
        self.try_btn.setObjectName("TryButton")
        self.try_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.try_btn.clicked.connect(self.try_next)

        self.open_btn = QPushButton("Open Source")
        self.open_btn.setObjectName("OpenButton")
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.clicked.connect(self.open_source)

        footer_layout.addWidget(self.mark_btn, 1)
        footer_layout.addWidget(self.try_btn)
        footer_layout.addWidget(self.open_btn)

        root.addWidget(footer)

        self.setStyleSheet(STYLE)
        self.refresh_rows()
        self.center_on_screen()

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return

        geo = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(geo.center())
        self.move(frame.topLeft())

    def refresh_rows(self):
        for i, row in enumerate(self.rows):
            source = SOURCES[i]
            prefix = "✓ " if i == self.selected else "  "
            working = "  • Working" if source["name"] == self.working else ""
            row.setText(f"{prefix}{source['name']}{working}\n{source['tag']}")

            if i == self.selected:
                row.setObjectName("SourceRowSelected")
            else:
                row.setObjectName("SourceRow")

            row.style().unpolish(row)
            row.style().polish(row)

        self.subtitle.setText(SOURCES[self.selected]["name"])

    def choose(self, index: int):
        self.selected = index
        self.state["selected"] = self.selected
        save_state(self.state)
        self.refresh_rows()

    def try_next(self):
        self.selected = (self.selected + 1) % len(SOURCES)
        self.state["selected"] = self.selected
        save_state(self.state)
        self.refresh_rows()

    def mark_working(self):
        self.working = SOURCES[self.selected]["name"]
        self.state["working"] = self.working
        save_state(self.state)
        self.refresh_rows()

    def open_source(self):
        spawn(SOURCES[self.selected]["command"])


STYLE = """
#Root {
    background-color: rgba(24, 24, 37, 0.98);
    color: #cdd6f4;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", "Noto Sans";
    border: 1px solid rgba(203, 166, 247, 0.42);
    border-radius: 22px;
}

#Header {
    background-color: rgba(49, 50, 68, 0.95);
    border-top-left-radius: 22px;
    border-top-right-radius: 22px;
    border-bottom: 1px solid rgba(203, 166, 247, 0.22);
}

#Title {
    color: #a6e3a1;
    font-size: 20px;
    font-weight: 900;
}

#Subtitle {
    color: #bac2de;
    font-size: 12px;
    font-weight: 800;
}

#CloseButton {
    background-color: transparent;
    color: #cdd6f4;
    border: none;
    font-size: 28px;
    font-weight: 900;
    min-width: 42px;
    min-height: 42px;
}

#CloseButton:hover {
    color: #f38ba8;
}

#Body {
    background-color: rgba(24, 24, 37, 0.98);
}

#SourceRow,
#SourceRowSelected {
    text-align: left;
    padding-left: 18px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 900;
}

#SourceRow {
    background-color: rgba(49, 50, 68, 0.88);
    color: #cdd6f4;
    border: 1px solid rgba(203, 166, 247, 0.16);
}

#SourceRow:hover {
    background-color: rgba(203, 166, 247, 0.14);
    border: 1px solid rgba(245, 194, 231, 0.32);
}

#SourceRowSelected {
    background-color: rgba(166, 227, 161, 0.12);
    color: #a6e3a1;
    border: 1px solid rgba(166, 227, 161, 0.72);
}

#Footer {
    background-color: rgba(30, 30, 46, 0.98);
    border-bottom-left-radius: 22px;
    border-bottom-right-radius: 22px;
    border-top: 1px solid rgba(203, 166, 247, 0.22);
}

#MarkButton,
#TryButton,
#OpenButton {
    border-radius: 12px;
    padding: 12px 14px;
    font-weight: 900;
}

#MarkButton {
    background-color: rgba(166, 227, 161, 0.16);
    color: #a6e3a1;
    border: 1px solid rgba(166, 227, 161, 0.34);
}

#TryButton {
    background-color: rgba(203, 166, 247, 0.14);
    color: #cdd6f4;
    border: 1px solid rgba(203, 166, 247, 0.26);
}

#OpenButton {
    background-color: rgba(137, 180, 250, 0.16);
    color: #89b4fa;
    border: 1px solid rgba(137, 180, 250, 0.34);
}

#MarkButton:hover,
#TryButton:hover,
#OpenButton:hover {
    background-color: rgba(245, 194, 231, 0.22);
    color: #f5c2e7;
    border: 1px solid rgba(245, 194, 231, 0.42);
}
"""


if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationName("kuro-stream")
    app.setDesktopFileName("kuro-stream")

    window = KuroStream()
    window.show()

    app.exec()
