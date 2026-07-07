#!/usr/bin/env python3

import json
import os
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QFrame,
    QSlider,
    QProgressBar,
)


DOTS = "/home/kasonf/Projects/kurodots"
EQ_FILE = Path(f"{DOTS}/themes/kuro/audio-eq.json")


EQ_PRESETS = {
    "Flat":   [50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
    "Bass":   [75, 72, 68, 58, 50, 45, 42, 40, 40, 40],
    "Treble": [40, 40, 42, 45, 50, 58, 64, 70, 74, 78],
    "Vocal":  [45, 48, 52, 58, 66, 68, 64, 56, 50, 46],
    "Pop":    [60, 58, 54, 50, 48, 52, 58, 64, 66, 62],
    "Rock":   [70, 65, 58, 52, 48, 52, 58, 66, 72, 74],
    "Jazz":   [54, 58, 60, 58, 54, 52, 56, 60, 62, 60],
    "Classic":[56, 58, 60, 62, 60, 56, 54, 52, 50, 48],
}

BANDS = ["31", "63", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"]


def run(cmd: str) -> str:
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def spawn(cmd: str):
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def player_status() -> str:
    return run("playerctl status") or "Stopped"


def player_meta(field: str) -> str:
    return run(f"playerctl metadata --format '{{{{ {field} }}}}'")


def player_position() -> int:
    raw = run("playerctl position")
    try:
        return int(float(raw))
    except Exception:
        return 0


def player_length() -> int:
    raw = run("playerctl metadata mpris:length")
    try:
        return int(int(raw) / 1_000_000)
    except Exception:
        return 0


def fmt_time(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"


def volume() -> int:
    raw = run("pamixer --get-volume")
    try:
        return int(raw)
    except Exception:
        return 0


def is_muted() -> bool:
    return run("pamixer --get-mute").lower() == "true"


def sink_name() -> str:
    name = run("pactl get-default-sink")
    if not name:
        return "Speaker"

    desc = run(f"pactl list sinks | grep -A30 'Name: {name}' | grep 'Description:' | head -n1 | cut -d ':' -f2- | xargs")
    return desc or "Speaker"


class KuroAudio(QWidget):
    def __init__(self):
        super().__init__()

        self.sliders = []
        self.preset_buttons = []

        self.setWindowTitle("Kuro Audio")
        self.setFixedSize(720, 650)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setObjectName("Root")

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(18)

        top = QHBoxLayout()
        top.setSpacing(28)

        self.disc = QLabel("")
        self.disc.setObjectName("Disc")
        self.disc.setFixedSize(205, 205)

        info = QVBoxLayout()
        info.setSpacing(14)

        self.title = QLabel("Not Playing")
        self.title.setObjectName("Title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.artist = QLabel("")
        self.artist.setObjectName("Sub")
        self.artist.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.device = QLabel("Speaker / VIA Offline")
        self.device.setObjectName("Device")
        self.device.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setObjectName("Progress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)

        time_row = QHBoxLayout()
        self.elapsed = QLabel("00:00")
        self.elapsed.setObjectName("TimeSmall")
        self.total = QLabel("00:00")
        self.total.setObjectName("TimeSmall")
        time_row.addWidget(self.elapsed)
        time_row.addStretch()
        time_row.addWidget(self.total)

        control_row = QHBoxLayout()
        control_row.setSpacing(20)
        control_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        prev_btn = QPushButton("󰒮")
        prev_btn.setObjectName("ControlButton")
        prev_btn.clicked.connect(lambda: spawn("playerctl previous"))

        self.play_btn = QPushButton("")
        self.play_btn.setObjectName("PlayButton")
        self.play_btn.clicked.connect(lambda: spawn("playerctl play-pause"))

        next_btn = QPushButton("󰒭")
        next_btn.setObjectName("ControlButton")
        next_btn.clicked.connect(lambda: spawn("playerctl next"))

        control_row.addWidget(prev_btn)
        control_row.addWidget(self.play_btn)
        control_row.addWidget(next_btn)

        vol_row = QHBoxLayout()
        self.vol_label = QLabel("Vol 0%")
        self.vol_label.setObjectName("Sub")

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setObjectName("VolSlider")
        self.vol_slider.setRange(0, 150)
        self.vol_slider.setValue(volume())
        self.vol_slider.valueChanged.connect(self.set_volume)

        mute_btn = QPushButton("Mute")
        mute_btn.setObjectName("TinyButton")
        mute_btn.clicked.connect(lambda: spawn("pamixer -t"))

        vol_row.addWidget(self.vol_label)
        vol_row.addWidget(self.vol_slider, 1)
        vol_row.addWidget(mute_btn)

        info.addWidget(self.title)
        info.addWidget(self.artist)
        info.addWidget(self.device)
        info.addWidget(self.progress)
        info.addLayout(time_row)
        info.addLayout(control_row)
        info.addLayout(vol_row)
        info.addStretch()

        top.addWidget(self.disc)
        top.addLayout(info, 1)

        root.addLayout(top)

        line = QFrame()
        line.setObjectName("Line")
        line.setFixedHeight(1)
        root.addWidget(line)

        eq_top = QHBoxLayout()
        eq_title = QLabel("Equalizer")
        eq_title.setObjectName("EqTitle")

        self.saved = QLabel("Saved")
        self.saved.setObjectName("SavedBadge")

        self.current_preset = QLabel("Flat")
        self.current_preset.setObjectName("PresetLabel")
        self.current_preset.setAlignment(Qt.AlignmentFlag.AlignRight)

        eq_top.addWidget(eq_title)
        eq_top.addStretch()
        eq_top.addWidget(self.saved)
        eq_top.addWidget(self.current_preset)

        root.addLayout(eq_top)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(18)

        for band in BANDS:
            col = QVBoxLayout()
            col.setSpacing(8)

            slider = QSlider(Qt.Orientation.Vertical)
            slider.setObjectName("EqSlider")
            slider.setRange(0, 100)
            slider.setValue(50)
            slider.setFixedHeight(170)
            slider.valueChanged.connect(self.save_custom)

            label = QLabel(band)
            label.setObjectName("BandLabel")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            col.addWidget(slider, alignment=Qt.AlignmentFlag.AlignCenter)
            col.addWidget(label)

            self.sliders.append(slider)
            slider_row.addLayout(col)

        root.addLayout(slider_row)

        preset_grid = QGridLayout()
        preset_grid.setSpacing(12)

        names = ["Flat", "Bass", "Treble", "Vocal", "Pop", "Rock", "Jazz", "Classic"]

        for i, name in enumerate(names):
            btn = QPushButton(name)
            btn.setObjectName("PresetButton")
            btn.clicked.connect(lambda checked=False, n=name: self.apply_preset(n))
            self.preset_buttons.append(btn)
            preset_grid.addWidget(btn, i // 4, i % 4)

        root.addLayout(preset_grid)

        self.setStyleSheet(STYLE)
        self.center_on_screen()
        self.load_eq()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

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

    def set_volume(self, value):
        spawn(f"pamixer --set-volume {value}")
        self.vol_label.setText(f"Vol {value}%")

    def apply_preset(self, name: str):
        values = EQ_PRESETS.get(name, EQ_PRESETS["Flat"])

        for slider, value in zip(self.sliders, values):
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)

        self.current_preset.setText(name)
        self.save_eq(name, values)

    def save_custom(self):
        values = [s.value() for s in self.sliders]
        self.current_preset.setText("Custom")
        self.save_eq("Custom", values)

    def save_eq(self, preset: str, values):
        EQ_FILE.parent.mkdir(parents=True, exist_ok=True)
        EQ_FILE.write_text(json.dumps({"preset": preset, "values": values}, indent=2))

    def load_eq(self):
        if not EQ_FILE.exists():
            self.apply_preset("Flat")
            return

        try:
            data = json.loads(EQ_FILE.read_text())
            values = data.get("values", EQ_PRESETS["Flat"])
            preset = data.get("preset", "Custom")

            for slider, value in zip(self.sliders, values):
                slider.blockSignals(True)
                slider.setValue(int(value))
                slider.blockSignals(False)

            self.current_preset.setText(preset)
        except Exception:
            self.apply_preset("Flat")

    def refresh(self):
        status = player_status()
        title = player_meta("title")
        artist = player_meta("artist")

        if status == "Playing":
            self.play_btn.setText("")
        else:
            self.play_btn.setText("")

        if title:
            self.title.setText(title[:38])
        else:
            self.title.setText("Not Playing")

        if artist:
            self.artist.setText(artist[:42])
        else:
            self.artist.setText("")

        pos = player_position()
        length = player_length()

        if length > 0:
            self.progress.setRange(0, length)
            self.progress.setValue(min(pos, length))
            self.total.setText(fmt_time(length))
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.total.setText("00:00")

        self.elapsed.setText(fmt_time(pos))

        vol = volume()
        self.vol_slider.blockSignals(True)
        self.vol_slider.setValue(vol)
        self.vol_slider.blockSignals(False)

        muted = is_muted()
        self.vol_label.setText(f"Muted" if muted else f"Vol {vol}%")

        device = sink_name()
        self.device.setText(f"󰓃 {device}")


STYLE = """
#Root {
    background-color: rgba(24, 24, 37, 0.98);
    color: #cdd6f4;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", "Noto Sans";
    border: 1px solid rgba(203, 166, 247, 0.45);
    border-radius: 24px;
}

#Disc {
    background-color: rgba(108, 112, 134, 0.52);
    border: 3px solid rgba(166, 173, 200, 0.38);
    border-radius: 102px;
}

#Disc::after {
    background-color: #11111b;
    border-radius: 20px;
}

#Title {
    color: #cdd6f4;
    font-size: 22px;
    font-weight: 900;
}

#Sub,
#Device {
    color: #a6adc8;
    font-size: 13px;
    font-weight: 800;
}

#Progress {
    background-color: rgba(17, 17, 27, 0.8);
    border: 1px solid rgba(203, 166, 247, 0.12);
    border-radius: 999px;
}

#Progress::chunk {
    background-color: #cdd6f4;
    border-radius: 999px;
}

#TimeSmall {
    color: #a6adc8;
    font-size: 12px;
    font-weight: 800;
}

#ControlButton {
    background-color: transparent;
    color: #a6adc8;
    border: none;
    font-size: 28px;
    font-weight: 900;
    min-width: 54px;
    min-height: 54px;
}

#ControlButton:hover {
    color: #f5c2e7;
}

#PlayButton {
    background-color: transparent;
    color: #cba6f7;
    border: none;
    font-size: 42px;
    font-weight: 900;
    min-width: 70px;
    min-height: 70px;
}

#PlayButton:hover {
    color: #f5c2e7;
}

#VolSlider::groove:horizontal {
    background-color: rgba(49, 50, 68, 0.88);
    height: 10px;
    border-radius: 999px;
}

#VolSlider::handle:horizontal {
    background-color: #cdd6f4;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

#VolSlider::sub-page:horizontal {
    background-color: #89b4fa;
    border-radius: 999px;
}

#TinyButton,
#PresetButton {
    background-color: rgba(203, 166, 247, 0.16);
    color: #cdd6f4;
    border: 1px solid rgba(203, 166, 247, 0.18);
    border-radius: 12px;
    padding: 8px 12px;
    font-weight: 900;
}

#TinyButton:hover,
#PresetButton:hover {
    background-color: rgba(245, 194, 231, 0.24);
    color: #f5c2e7;
}

#Line {
    background-color: rgba(203, 166, 247, 0.22);
}

#EqTitle {
    color: #f5c2e7;
    font-size: 16px;
    font-weight: 900;
}

#SavedBadge {
    background-color: rgba(166, 173, 200, 0.2);
    color: #cdd6f4;
    border-radius: 10px;
    padding: 6px 14px;
    font-weight: 900;
}

#PresetLabel {
    color: #cdd6f4;
    font-size: 14px;
    font-weight: 900;
    min-width: 80px;
}

#EqSlider::groove:vertical {
    background-color: rgba(49, 50, 68, 0.88);
    width: 10px;
    border-radius: 999px;
}

#EqSlider::handle:vertical {
    background-color: #cdd6f4;
    height: 18px;
    margin: 0 -5px;
    border-radius: 9px;
}

#EqSlider::sub-page:vertical {
    background-color: #89b4fa;
    border-radius: 999px;
}

#BandLabel {
    color: #89b4fa;
    font-size: 11px;
    font-weight: 800;
}
"""


if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationName("kuro-audio")
    app.setDesktopFileName("kuro-audio")

    window = KuroAudio()
    window.show()

    app.exec()
