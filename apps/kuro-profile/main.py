#!/usr/bin/env python3

import os
import platform
import subprocess
import psutil

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
    QStackedWidget,
    QGridLayout,
    QProgressBar,
)


HOME = os.path.expanduser("~")
DOTS = "/home/kasonf/Projects/kurodots"


def run(cmd: str) -> str:
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "Unknown"


def get_gpu() -> str:
    gpu = run("lspci | grep -Ei 'vga|3d|display' | head -n 1")
    if ":" in gpu:
        gpu = gpu.split(":", 2)[-1].strip()
    return gpu or "Unknown GPU"


def get_kernel() -> str:
    return platform.release()


def get_distro() -> str:
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            data = f.read()

        for line in data.splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].replace('"', "")
    except Exception:
        pass

    return "Linux"


def get_cpu() -> str:
    cpu = platform.processor()
    if cpu:
        return cpu

    return run("lscpu | grep 'Model name' | cut -d ':' -f2 | xargs")


class KuroProfile(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Kuro Profile")
        self.setFixedSize(1100, 720)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setObjectName("Root")

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(18)

        self.sidebar = self.build_sidebar()
        self.stack = QStackedWidget()

        self.stack.addWidget(self.build_system_page())
        self.stack.addWidget(self.build_settings_page())
        self.stack.addWidget(self.build_modules_page())
        self.stack.addWidget(self.build_about_page())

        root.addWidget(self.sidebar)
        root.addWidget(self.stack, 1)

        self.setStyleSheet(STYLE)
        self.center_on_screen()

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return

        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def nav_button(self, text: str, page: int, active: bool = False):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setCheckable(True)
        btn.setMinimumHeight(46)
        btn.setObjectName("NavActive" if active else "NavButton")
        btn.clicked.connect(lambda: self.switch_page(page))
        return btn

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)

        buttons = self.sidebar.findChildren(QPushButton)

        for btn in buttons:
            if btn.text() in ["System", "Settings", "Modules", "About"]:
                btn.setObjectName("NavButton")
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        label = ["System", "Settings", "Modules", "About"][index]

        for btn in buttons:
            if btn.text() == label:
                btn.setObjectName("NavActive")
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def build_sidebar(self):
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(230)

        layout = QVBoxLayout(side)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        logo = QLabel("K")
        logo.setObjectName("Logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(48, 48)

        title = QLabel("KuroMiro")
        title.setObjectName("SideTitle")

        version = QLabel("v0.6 beta")
        version.setObjectName("SideSub")

        header = QHBoxLayout()
        header.addWidget(logo)

        title_box = QVBoxLayout()
        title_box.addWidget(title)
        title_box.addWidget(version)

        header.addLayout(title_box)

        layout.addLayout(header)
        layout.addSpacing(24)

        layout.addWidget(self.nav_button("System", 0, True))
        layout.addWidget(self.nav_button("Settings", 1))
        layout.addWidget(self.nav_button("Modules", 2))
        layout.addWidget(self.nav_button("About", 3))

        layout.addStretch()

        bottom = QPushButton("Open Folder")
        bottom.setObjectName("BottomButton")
        bottom.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom.clicked.connect(lambda: subprocess.Popen(f"xdg-open {DOTS}", shell=True))
        layout.addWidget(bottom)

        return side

    def card(self, title: str, subtitle: str):
        box = QFrame()
        box.setObjectName("Card")

        layout = QVBoxLayout(box)
        layout.setContentsMargins(18, 14, 18, 14)

        t = QLabel(title)
        t.setObjectName("CardTitle")

        s = QLabel(subtitle)
        s.setObjectName("CardSub")
        s.setWordWrap(True)

        layout.addWidget(t)
        layout.addWidget(s)

        return box

    def action_button(self, title: str, command: str):
        btn = QPushButton(title)
        btn.setObjectName("SmallButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(46)
        btn.clicked.connect(lambda: subprocess.Popen(command, shell=True))
        return btn

    def build_profile_header(self):
        card = QFrame()
        card.setObjectName("ProfileCard")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        avatar = QLabel("K")
        avatar.setObjectName("Avatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(92, 92)

        info = QVBoxLayout()

        name = QLabel(os.getenv("USER", "kasonf"))
        name.setObjectName("ProfileName")

        tag = QLabel("@cachyos-x86_64")
        tag.setObjectName("ProfileTag")

        specs = QLabel(
            f"{get_distro()}  •  Kernel {get_kernel()}\n"
            f"{get_cpu()}\n"
            f"{get_gpu()}"
        )
        specs.setObjectName("ProfileSpecs")
        specs.setWordWrap(True)

        info.addWidget(name)
        info.addWidget(tag)
        info.addSpacing(8)
        info.addWidget(specs)

        layout.addWidget(avatar)
        layout.addLayout(info, 1)

        return card

    def build_system_page(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(18)

        layout.addWidget(self.build_profile_header())

        repo = QFrame()
        repo.setObjectName("RepoCard")

        repo_layout = QHBoxLayout(repo)
        repo_layout.setContentsMargins(18, 12, 18, 12)

        repo_text = QVBoxLayout()

        repo_title = QLabel("Kurodots")
        repo_title.setObjectName("RepoTitle")

        repo_sub = QLabel("~/Projects/kurodots")
        repo_sub.setObjectName("RepoSub")

        repo_text.addWidget(repo_title)
        repo_text.addWidget(repo_sub)

        repo_layout.addLayout(repo_text)
        repo_layout.addStretch()

        open_btn = QPushButton("Open Folder")
        open_btn.setObjectName("SmallButton")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(lambda: subprocess.Popen(f"xdg-open {DOTS}", shell=True))

        repo_layout.addWidget(open_btn)

        layout.addWidget(repo)

        heading = QLabel("System Architecture")
        heading.setObjectName("Heading")
        layout.addWidget(heading)

        grid = QGridLayout()
        grid.setSpacing(14)

        cards = [
            ("Hyprland", "Wayland compositor"),
            ("Waybar", "Top status bar"),
            ("Rofi Wayland", "App launcher"),
            ("Kitty", "Terminal emulator"),
            ("SwayNC", "Notifications"),
            ("Hyprlock", "Lockscreen"),
            ("wlogout", "Power menu"),
            ("Kuro Scripts", "Preview / backup / apply"),
        ]

        for i, (title, sub) in enumerate(cards):
            grid.addWidget(self.card(title, sub), i // 2, i % 2)

        layout.addLayout(grid)
        layout.addStretch()

        return page

    def build_settings_page(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setObjectName("Heading")
        layout.addWidget(title)

        main_box = QFrame()
        main_box.setObjectName("ProfileCard")

        main_layout = QVBoxLayout(main_box)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        desc = QLabel("Manage KuroMiro configs and preview tools from one place.")
        desc.setObjectName("AboutText")
        desc.setWordWrap(True)

        main_layout.addWidget(desc)

        grid = QGridLayout()
        grid.setSpacing(12)

        buttons = [
            ("Compact Bar", f"bash {DOTS}/scripts/kuro-bar-compact"),
            ("Full Bar", f"bash {DOTS}/scripts/kuro-bar-full"),
            ("Restart Preview", f"bash {DOTS}/scripts/kuro-restart"),
            ("Edit Colors", f"bash {DOTS}/scripts/kuro-edit-colors"),
            ("Open Hyprland Rules", f"bash {DOTS}/scripts/kuro-open-hypr-rules"),
            ("Run Check", f"bash {DOTS}/scripts/kuro-check-terminal"),
            ("Open Folder", f"xdg-open {DOTS}"),
            ("Stream Picker", f"bash {DOTS}/scripts/kuro-stream"),
            ("Open Rofi", f"rofi -show drun -config {DOTS}/.config/rofi/config.rasi"),
            ("Notifications", "swaync-client -t"),
            ("Edit Waybar CSS", f"kitty --config {DOTS}/.config/kitty/kitty.conf nano {DOTS}/.config/waybar/style.css"),
            ("Edit Waybar Config", f"kitty --config {DOTS}/.config/kitty/kitty.conf nano {DOTS}/.config/waybar/config.jsonc"),
            ("Edit Rofi Theme", f"kitty --config {DOTS}/.config/kitty/kitty.conf nano {DOTS}/.config/rofi/theme.rasi"),
            ("Edit Kitty Theme", f"kitty --config {DOTS}/.config/kitty/kitty.conf nano {DOTS}/.config/kitty/kitty.conf"),
            ("Edit SwayNC CSS", f"kitty --config {DOTS}/.config/kitty/kitty.conf nano {DOTS}/.config/swaync/style.css"),
        ]
        for i, (name, command) in enumerate(buttons):
            grid.addWidget(self.action_button(name, command), i // 2, i % 2)

        main_layout.addLayout(grid)
        layout.addWidget(main_box)

        warning_box = QFrame()
        warning_box.setObjectName("RepoCard")

        warning_layout = QVBoxLayout(warning_box)
        warning_layout.setContentsMargins(18, 14, 18, 14)

        warning = QLabel(
            "Apply and restore are not included as buttons yet. "
            "Those are powerful commands, so keep running them manually in the terminal for now."
        )
        warning.setObjectName("AboutText")
        warning.setWordWrap(True)

        warning_layout.addWidget(warning)
        layout.addWidget(warning_box)

        layout.addStretch()

        return page

    def build_modules_page(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(18)

        title = QLabel("Modules")
        title.setObjectName("Heading")
        layout.addWidget(title)

        stats = QFrame()
        stats.setObjectName("ProfileCard")

        stats_layout = QVBoxLayout(stats)
        stats_layout.setContentsMargins(24, 20, 24, 20)
        stats_layout.setSpacing(18)

        cpu = QProgressBar()
        cpu.setValue(int(psutil.cpu_percent(interval=0.2)))
        cpu.setFormat("CPU  %p%")

        ram = QProgressBar()
        ram.setValue(int(psutil.virtual_memory().percent))
        ram.setFormat("RAM  %p%")

        disk = QProgressBar()
        disk.setValue(int(psutil.disk_usage("/").percent))
        disk.setFormat("Disk  %p%")

        for bar in [cpu, ram, disk]:
            bar.setMinimumHeight(28)
            bar.setObjectName("Progress")
            stats_layout.addWidget(bar)

        layout.addWidget(stats)

        grid = QGridLayout()
        grid.setSpacing(14)

        modules = [
            ("Preview", "Run ./scripts/kuro-preview"),
            ("Backup", "Run ./scripts/kuro-backup"),
            ("Apply", "Run ./scripts/kuro-apply"),
            ("Restore", "Run ./scripts/kuro-restore"),
        ]

        for i, (title_text, sub) in enumerate(modules):
            grid.addWidget(self.card(title_text, sub), i // 2, i % 2)

        layout.addLayout(grid)
        layout.addStretch()

        return page

    def build_about_page(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(18)

        title = QLabel("About KuroMiro")
        title.setObjectName("Heading")
        layout.addWidget(title)

        about = QLabel(
            "KuroMiro is a custom CachyOS Hyprland rice built safely inside "
            "~/Projects/kurodots before being applied to the live system.\n\n"
            "Inspired by glassy anime/minimal Linux setups, but written as your own dotfiles."
        )
        about.setObjectName("AboutText")
        about.setWordWrap(True)

        box = QFrame()
        box.setObjectName("ProfileCard")

        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(24, 20, 24, 20)
        box_layout.addWidget(about)

        layout.addWidget(box)
        layout.addStretch()

        return page


STYLE = """
#Root {
    background-color: #11111b;
    color: #cdd6f4;
    font-family: "JetBrains Mono", "Noto Sans";
}

#Sidebar {
    background-color: rgba(30, 30, 46, 0.92);
    border: 1px solid rgba(203, 166, 247, 0.28);
    border-radius: 22px;
}

#Logo {
    background-color: #cba6f7;
    color: #181825;
    border-radius: 14px;
    font-size: 24px;
    font-weight: 900;
}

#SideTitle {
    color: #cdd6f4;
    font-size: 16px;
    font-weight: 900;
}

#SideSub {
    color: #89b4fa;
    font-size: 11px;
}

#NavButton {
    background-color: transparent;
    color: #bac2de;
    border: none;
    border-radius: 12px;
    text-align: left;
    padding-left: 16px;
    font-size: 14px;
    font-weight: 800;
}

#NavButton:hover {
    background-color: rgba(203, 166, 247, 0.14);
    color: #f5c2e7;
}

#NavActive {
    background-color: #cba6f7;
    color: #181825;
    border: none;
    border-radius: 12px;
    text-align: left;
    padding-left: 16px;
    font-size: 14px;
    font-weight: 900;
}

#BottomButton,
#SmallButton {
    background-color: rgba(203, 166, 247, 0.14);
    color: #cdd6f4;
    border: 1px solid rgba(203, 166, 247, 0.28);
    border-radius: 14px;
    padding: 10px 14px;
    font-weight: 800;
}

#BottomButton:hover,
#SmallButton:hover {
    background-color: rgba(245, 194, 231, 0.22);
    color: #f5c2e7;
}

#ProfileCard {
    background-color: rgba(49, 50, 68, 0.72);
    border: 1px solid rgba(203, 166, 247, 0.26);
    border-radius: 18px;
}

#Avatar {
    background-color: rgba(203, 166, 247, 0.18);
    color: #cdd6f4;
    border: 3px solid rgba(203, 166, 247, 0.42);
    border-radius: 46px;
    font-size: 38px;
    font-weight: 900;
}

#ProfileName {
    color: #cdd6f4;
    font-size: 28px;
    font-weight: 900;
}

#ProfileTag {
    color: #bac2de;
    font-size: 14px;
    font-weight: 700;
}

#ProfileSpecs {
    color: #a6adc8;
    font-size: 13px;
    font-weight: 700;
}

#RepoCard {
    background-color: rgba(30, 30, 46, 0.78);
    border: 1px solid rgba(203, 166, 247, 0.22);
    border-radius: 16px;
}

#RepoTitle {
    color: #f5c2e7;
    font-size: 16px;
    font-weight: 900;
}

#RepoSub {
    color: #a6adc8;
    font-size: 12px;
}

#Heading {
    color: #cdd6f4;
    font-size: 24px;
    font-weight: 900;
}

#Card {
    background-color: rgba(30, 30, 46, 0.72);
    border: 1px solid rgba(203, 166, 247, 0.24);
    border-radius: 16px;
}

#Card:hover {
    background-color: rgba(203, 166, 247, 0.12);
    border: 1px solid rgba(245, 194, 231, 0.35);
}

#CardTitle {
    color: #cdd6f4;
    font-size: 16px;
    font-weight: 900;
}

#CardSub {
    color: #a6adc8;
    font-size: 12px;
    font-weight: 700;
}

#Progress {
    background-color: rgba(17, 17, 27, 0.8);
    color: #181825;
    border: 1px solid rgba(203, 166, 247, 0.2);
    border-radius: 14px;
    text-align: center;
    font-weight: 900;
}

#Progress::chunk {
    background-color: #cba6f7;
    border-radius: 13px;
}

#AboutText {
    color: #bac2de;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.5;
}
"""


if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationName("kuro-profile")
    app.setDesktopFileName("kuro-profile")

    window = KuroProfile()
    window.show()

    app.exec()
