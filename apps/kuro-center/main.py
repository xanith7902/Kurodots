#!/usr/bin/env python3

import calendar
import datetime as dt
import json
import urllib.parse
import urllib.request

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
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
)


DOTS = "/home/kasonf/Projects/kurodots"
LOCATION_FILE = f"{DOTS}/themes/kuro/location.txt"


def read_location() -> str:
    try:
        with open(LOCATION_FILE, "r", encoding="utf-8") as f:
            loc = f.read().strip()
            return loc or "Morrinsville,NZ"
    except Exception:
        return "Morrinsville,NZ"


def icon_for_weather(text: str) -> str:
    t = text.lower()
    if "thunder" in t:
        return "⛈"
    if "rain" in t or "drizzle" in t or "shower" in t:
        return "🌧"
    if "snow" in t:
        return "❄"
    if "fog" in t or "mist" in t:
        return "🌫"
    if "clear" in t or "sunny" in t:
        return "☀"
    if "cloud" in t or "overcast" in t:
        return "☁"
    return "☁"


def fmt_hour(raw: str) -> str:
    try:
        raw = raw.zfill(4)
        return f"{int(raw[:2]):02d}:00"
    except Exception:
        return "--:--"


class WeatherWorker(QThread):
    finished = pyqtSignal(dict, list)

    def run(self):
        location = read_location()
        encoded = urllib.parse.quote(location)
        url = f"https://wttr.in/{encoded}?format=j1"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kuro-center"})
            with urllib.request.urlopen(req, timeout=2.5) as response:
                data = json.loads(response.read().decode("utf-8"))

            current = data["current_condition"][0]
            today = data["weather"][0]
            hourly = today.get("hourly", [])

            desc = current["weatherDesc"][0]["value"]

            current_data = {
                "ok": True,
                "location": location,
                "temp": current.get("temp_C", "?"),
                "feels": current.get("FeelsLikeC", "?"),
                "desc": desc,
                "icon": icon_for_weather(desc),
                "wind": current.get("windspeedKmph", "?"),
                "humidity": current.get("humidity", "?"),
                "rain": hourly[0].get("chanceofrain", "0") if hourly else "0",
            }

            hourly_data = []
            for item in hourly[::2][:7]:
                h_desc = item["weatherDesc"][0]["value"]
                hourly_data.append(
                    {
                        "time": fmt_hour(item.get("time", "")),
                        "temp": item.get("tempC", "?"),
                        "icon": icon_for_weather(h_desc),
                    }
                )

            self.finished.emit(current_data, hourly_data)

        except Exception:
            self.finished.emit(
                {
                    "ok": False,
                    "location": location,
                    "temp": "?",
                    "feels": "?",
                    "desc": "Weather unavailable",
                    "icon": "☁",
                    "wind": "?",
                    "humidity": "?",
                    "rain": "?",
                },
                [],
            )


class KuroCenter(QWidget):
    def __init__(self):
        super().__init__()

        self.month_offset = 0
        self.hour_cards = []
        self.weather_worker = None

        self.setWindowTitle("Kuro Center")
        self.setFixedSize(1280, 440)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setObjectName("Root")

        root = QHBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(28)

        self.calendar_box = self.build_calendar()
        self.middle_box = self.build_middle()
        self.weather_box = self.build_weather()

        root.addWidget(self.calendar_box)
        root.addWidget(self.middle_box, 1)
        root.addWidget(self.weather_box)

        self.setStyleSheet(STYLE)
        self.center_on_screen()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self.start_weather_update)
        self.weather_timer.start(10 * 60 * 1000)

        self.update_calendar()
        self.update_clock()

        QTimer.singleShot(80, self.start_weather_update)

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

        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def build_calendar(self):
        box = QFrame()
        box.setObjectName("CalendarBox")
        box.setFixedWidth(330)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        top = QHBoxLayout()

        prev_btn = QPushButton("‹")
        prev_btn.setObjectName("MiniButton")
        prev_btn.clicked.connect(self.prev_month)

        self.month_label = QLabel("")
        self.month_label.setObjectName("MonthTitle")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setMinimumWidth(170)

        next_btn = QPushButton("›")
        next_btn.setObjectName("MiniButton")
        next_btn.clicked.connect(self.next_month)

        today_btn = QPushButton("+")
        today_btn.setObjectName("MiniButton")
        today_btn.clicked.connect(self.reset_month)

        top.addWidget(prev_btn)
        top.addWidget(self.month_label, 1)
        top.addWidget(next_btn)
        top.addWidget(today_btn)

        layout.addLayout(top)

        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(8)

        layout.addLayout(self.calendar_grid)
        layout.addStretch()

        return box

    def build_middle(self):
        box = QFrame()
        box.setObjectName("MiddleBox")

        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(12)

        self.arc = QLabel("•     •     •     •     •")
        self.arc.setObjectName("Arc")
        self.arc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_label = QLabel("00:00:00")
        self.time_label.setObjectName("TimeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.date_label = QLabel("Wednesday, July 08")
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hour_row = QHBoxLayout()
        self.hour_row.setSpacing(10)

        for _ in range(7):
            card = QLabel("--:--\n☁\n--°")
            card.setObjectName("HourCard")
            card.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card.setFixedSize(72, 92)
            self.hour_cards.append(card)
            self.hour_row.addWidget(card)

        layout.addWidget(self.arc)
        layout.addStretch()
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        layout.addSpacing(14)
        layout.addLayout(self.hour_row)
        layout.addStretch()

        return box

    def build_weather(self):
        box = QFrame()
        box.setObjectName("WeatherBox")
        box.setFixedWidth(310)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)

        top = QHBoxLayout()

        left = QPushButton("‹")
        left.setObjectName("MiniButton")

        self.day_label = QLabel("TODAY")
        self.day_label.setObjectName("DayTitle")
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right = QPushButton("›")
        right.setObjectName("MiniButton")

        top.addWidget(left)
        top.addWidget(self.day_label, 1)
        top.addWidget(right)

        self.current_icon = QLabel("☁")
        self.current_icon.setObjectName("WeatherIcon")
        self.current_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.current_temp = QLabel("...")
        self.current_temp.setObjectName("WeatherTemp")
        self.current_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.current_desc = QLabel("Loading weather")
        self.current_desc.setObjectName("WeatherDesc")
        self.current_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stats = QGridLayout()
        stats.setSpacing(10)

        self.wind = self.stat_card("Wind", "...")
        self.humid = self.stat_card("Humid", "...")
        self.rain = self.stat_card("Rain", "...")
        self.feels = self.stat_card("Feels", "...")

        stats.addWidget(self.wind, 0, 0)
        stats.addWidget(self.humid, 0, 1)
        stats.addWidget(self.rain, 1, 0)
        stats.addWidget(self.feels, 1, 1)

        layout.addLayout(top)
        layout.addStretch()
        layout.addWidget(self.current_icon)
        layout.addWidget(self.current_temp)
        layout.addWidget(self.current_desc)
        layout.addStretch()
        layout.addLayout(stats)

        return box

    def stat_card(self, title: str, value: str):
        box = QLabel(f"{value}\n{title}")
        box.setObjectName("StatCard")
        box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.setFixedHeight(62)
        return box

    def update_clock(self):
        now = dt.datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%A, %B %d"))
        self.day_label.setText(now.strftime("%A").upper())

    def start_weather_update(self):
        if self.weather_worker and self.weather_worker.isRunning():
            return

        self.weather_worker = WeatherWorker()
        self.weather_worker.finished.connect(self.apply_weather)
        self.weather_worker.start()

    def apply_weather(self, current, hourly):
        self.current_icon.setText(current["icon"])
        self.current_temp.setText(f"{current['temp']}°")
        self.current_desc.setText(current["desc"])

        self.wind.setText(f"{current['wind']} km/h\nWind")
        self.humid.setText(f"{current['humidity']}%\nHumid")
        self.rain.setText(f"{current['rain']}%\nRain")
        self.feels.setText(f"{current['feels']}°\nFeels")

        for i, card in enumerate(self.hour_cards):
            if i < len(hourly):
                item = hourly[i]
                card.setText(f"{item['time']}\n{item['icon']}\n{item['temp']}°")
            else:
                card.setText("--:--\n☁\n--°")

    def update_calendar(self):
        today = dt.date.today()
        base_month = today.month + self.month_offset
        year = today.year + (base_month - 1) // 12
        month = (base_month - 1) % 12 + 1

        self.month_label.setText(f"{calendar.month_abbr[month].upper()} {year}")

        while self.calendar_grid.count():
            item = self.calendar_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, day in enumerate(days):
            label = QLabel(day)
            label.setObjectName("WeekDay")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.calendar_grid.addWidget(label, 0, col)

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(year, month)

        for row, week in enumerate(weeks, start=1):
            for col, day in enumerate(week):
                label = QLabel("" if day == 0 else str(day))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setFixedSize(34, 34)

                if day == today.day and month == today.month and year == today.year:
                    label.setObjectName("Today")
                elif day == 0:
                    label.setObjectName("EmptyDay")
                else:
                    label.setObjectName("Day")

                self.calendar_grid.addWidget(label, row, col)

    def prev_month(self):
        self.month_offset -= 1
        self.update_calendar()

    def next_month(self):
        self.month_offset += 1
        self.update_calendar()

    def reset_month(self):
        self.month_offset = 0
        self.update_calendar()


STYLE = """
#Root {
    background-color: rgba(24, 24, 37, 0.96);
    color: #cdd6f4;
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", "Noto Sans";
    border-radius: 24px;
}

#CalendarBox,
#WeatherBox {
    background-color: rgba(30, 30, 46, 0.74);
    border: 1px solid rgba(203, 166, 247, 0.22);
    border-radius: 20px;
}

#MiddleBox {
    background-color: transparent;
    border: none;
}

#MiniButton {
    background-color: transparent;
    color: #cdd6f4;
    border: none;
    border-radius: 10px;
    font-size: 24px;
    font-weight: 900;
    min-width: 34px;
    min-height: 34px;
}

#MiniButton:hover {
    background-color: rgba(203, 166, 247, 0.18);
    color: #f5c2e7;
}

#MonthTitle,
#DayTitle {
    color: #cdd6f4;
    font-size: 17px;
    font-weight: 900;
    letter-spacing: 1px;
}

#WeekDay {
    color: #7f849c;
    font-size: 13px;
    font-weight: 900;
}

#Day {
    color: #cdd6f4;
    font-size: 14px;
    font-weight: 800;
}

#EmptyDay {
    color: rgba(108, 112, 134, 0.25);
}

#Today {
    background-color: #f5e8c7;
    color: #11111b;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 900;
}

#Arc {
    color: rgba(205, 214, 244, 0.35);
    font-size: 46px;
    font-weight: 900;
}

#TimeLabel {
    color: #cdd6f4;
    font-size: 72px;
    font-weight: 900;
}

#DateLabel {
    color: #a6adc8;
    font-size: 16px;
    font-weight: 800;
}

#HourCard {
    background-color: rgba(49, 50, 68, 0.82);
    border: 1px solid rgba(203, 166, 247, 0.2);
    border-radius: 24px;
    color: #cdd6f4;
    font-size: 12px;
    font-weight: 900;
}

#WeatherIcon {
    color: #cdd6f4;
    font-size: 38px;
}

#WeatherTemp {
    color: #cdd6f4;
    font-size: 64px;
    font-weight: 900;
}

#WeatherDesc {
    color: #f5e8c7;
    font-size: 15px;
    font-weight: 900;
}

#StatCard {
    background-color: rgba(49, 50, 68, 0.75);
    border: 1px solid rgba(203, 166, 247, 0.2);
    border-radius: 18px;
    color: #cdd6f4;
    font-size: 12px;
    font-weight: 900;
}
"""


if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationName("kuro-center")
    app.setDesktopFileName("kuro-center")

    window = KuroCenter()
    window.show()

    app.exec()
