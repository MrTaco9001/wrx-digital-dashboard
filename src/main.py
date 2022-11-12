# formatted with yapf
# Bryce Happel Walton

#todo: This program is far too slow on the RPi

import platform
import subprocess
import sys
from math import pi
from random import randrange
from time import sleep, time

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCursor, QFont, QPixmap, QPalette, QColor, QImage, QTransform
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

from can_handle import CanApplication
from dial import Dial

screen_size = [1920, 720]
rpm_params = {
    "min": 0,
    "max": 8000,
    "redline": 6700,
    "mid_sections": 10,
    "denomination": 1000
}
speed_params = {"min": 0, "max": 180, "units": "MPH", "mid_sections": 10}

cluster_size = 600


def change_image_color(image: QImage, color: QColor):
    for x in range(image.width()):
        for y in range(image.height()):
            pcolor = image.pixelColor(x, y)
            if pcolor.alpha() > 0:
                n_color = QColor(color)
                n_color.setAlpha(pcolor.alpha())
                image.setPixelColor(x, y, n_color)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Digital Cluster")

        font_group = "Sans Serif Collection"
        font_weight = 600
        big_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32

        rpm_gauge = Dial(self,
                         size=cluster_size,
                         min_unit=rpm_params["min"],
                         max_unit=rpm_params["max"],
                         redline=rpm_params["redline"],
                         mid_sections=rpm_params["mid_sections"],
                         denomination=rpm_params["denomination"],
                         visual_num_gap=rpm_params["denomination"],
                         label_font=QFont(f"{font_group}", 21, font_weight),
                         angle_offset=pi,
                         angle_range=big_dial_angle_range)

        rpm_gauge.move(int(cluster_size / 4),
                       int(screen_size[1] / 2 - cluster_size / 2))

        rpm_gauge.show()
        self.tachometer = rpm_gauge

        speed_gauge = Dial(self,
                           size=cluster_size,
                           min_unit=speed_params["min"],
                           max_unit=speed_params["max"],
                           redline=speed_params["max"] + 1,
                           mid_sections=speed_params["mid_sections"],
                           units=speed_params["units"],
                           visual_num_gap=20,
                           label_font=QFont(f"{font_group}", 18, font_weight),
                           angle_offset=pi,
                           angle_range=big_dial_angle_range)

        speed_gauge.move(int(screen_size[0] - cluster_size - cluster_size / 4),
                         int(screen_size[1] / 2 - cluster_size / 2))
        speed_gauge.show()

        color_black = QColor(0, 0, 0)
        color_green = QColor(0, 255, 0)
        transform = QTransform().rotate(180)

        right_arrow_image_black = QImage("resources/turn-signal-arrow.png")
        change_image_color(right_arrow_image_black, color_black)
        right_arrow_image_black = QPixmap.fromImage(right_arrow_image_black)

        right_arrow_image_green = QImage("resources/turn-signal-arrow.png")
        change_image_color(right_arrow_image_green, color_green)
        right_arrow_image_green = QPixmap.fromImage(right_arrow_image_green)

        left_arrow_image_black = QImage("resources/turn-signal-arrow.png")
        change_image_color(left_arrow_image_black, color_black)
        left_arrow_image_black = QPixmap.fromImage(left_arrow_image_black)
        left_arrow_image_black = left_arrow_image_black.transformed(transform)

        left_arrow_image_green = QImage("resources/turn-signal-arrow.png")
        change_image_color(left_arrow_image_green, color_green)
        left_arrow_image_green = QPixmap.fromImage(left_arrow_image_green)
        left_arrow_image_green = left_arrow_image_green.transformed(transform)

        self.right_arrow_image_black = right_arrow_image_black
        self.right_arrow_image_green = right_arrow_image_green
        self.left_arrow_image_black = left_arrow_image_black
        self.left_arrow_image_green = left_arrow_image_green

        label_font = QFont("Sans-serif", 17)
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        turn_signal_offset = 80
        turn_signal_size = 50

        right_turn_signal_image = QLabel(self)
        right_turn_signal_image.setPixmap(right_arrow_image_black)
        right_turn_signal_image.move(
            int(screen_size[0] - cluster_size - cluster_size / 4 - turn_signal_offset),
            int(screen_size[1] / 2 - cluster_size / 2))
        right_turn_signal_image.setScaledContents(True)
        right_turn_signal_image.resize(turn_signal_size, turn_signal_size)
        right_turn_signal_image.show()

        left_turn_signal_image = QLabel(self)
        left_turn_signal_image.setPixmap(left_arrow_image_black)
        left_turn_signal_image.move(
            int(cluster_size / 4 + cluster_size - turn_signal_size + turn_signal_offset),
            int(screen_size[1] / 2 - cluster_size / 2))
        left_turn_signal_image.setScaledContents(True)
        left_turn_signal_image.resize(turn_signal_size, turn_signal_size)
        left_turn_signal_image.show()

        rpm_label = QLabel(self)
        rpm_label.setStyleSheet("background:transparent")
        rpm_label.setText(f"{0}")
        rpm_label.move(int(cluster_size / 4 + cluster_size / 2 - 25),
                       int(screen_size[1] / 2 - cluster_size / 2 + 200))
        rpm_label.setStyleSheet("background:transparent")
        rpm_label.setFont(label_font)
        rpm_label.setPalette(palette)
        rpm_label.setFont(label_font)
        rpm_label.resize(200, 200)
        rpm_label.show()

        speed_label = QLabel(self)
        speed_label.setText(f"{0}")
        speed_label.setStyleSheet("background:transparent")
        speed_label.setFont(label_font)
        speed_label.setPalette(palette)
        speed_label.move(
            int(screen_size[0] - cluster_size - cluster_size / 4 +
                cluster_size / 2 - 25 / 2),
            int(screen_size[1] / 2 - cluster_size / 2 + 200))
        speed_label.resize(200, 200)
        speed_label.show()

        self.rpm_label = rpm_label
        self.speed_label = speed_label
        self.right_turn_signal_image = right_turn_signal_image
        self.left_turn_signal_image = left_turn_signal_image

        self.speedometer = speed_gauge


class Application(QApplication):

    awakened = pyqtSignal()
    started = pyqtSignal()
    cluster_vars = {
        "rpm": 0,
        "vehicle_speed": 0,
        "left_sw_stock": {
            "left_turn_signal": 0,
            "right_turn_signal": 0
        }
    }
    awaken_sequence_duration_ms = 2500
    awaken_sequence_steps = 2000

    def __init__(self):
        super().__init__([])
        self.setOverrideCursor(QCursor(Qt.BlankCursor))
        primary_container = MainWindow()

        self.start_time = time()
        self.primary_container = primary_container

        self.awaken_clusters()

    def awaken_clusters(self):
        timer = QTimer(self)

        self._awaken_a = 0
        self._awaken_t = 0

        t_step = self.awaken_sequence_duration_ms / self.awaken_sequence_steps
        a_step = t_step / self.awaken_sequence_duration_ms

        self.primary_container.tachometer.setDial(0)
        self.primary_container.speedometer.setDial(0)

        self._last_time = time() * 1000
        start_time = self._last_time

        def dialMove():
            current_time = time() * 1000
            dt = current_time - self._last_time
            tdt = current_time - start_time

            if tdt >= self.awaken_sequence_duration_ms:
                timer.stop()
                timer.deleteLater()
                self.awakened.emit()
            elif dt >= t_step:
                step = dt / t_step * a_step * 2

                if tdt >= self.awaken_sequence_duration_ms / 2:
                    self._awaken_a -= step
                else:
                    self._awaken_a += step

            self.primary_container.tachometer.setDial(self._awaken_a)
            self.primary_container.speedometer.setDial(self._awaken_a)

            self._last_time = time() * 1000

        timer.timeout.connect(dialMove)
        timer.start(t_step)

    def clusterUpdate(self):
        #self.primary_container.tachometer.setUnit(self.cluster_vars["rpm"])
        #self.primary_container.speedometer.setUnit(self.cluster_vars["vehicle_speed"])
        rpm = self.cluster_vars["rpm"]
        speed = self.cluster_vars["vehicle_speed"]
        self.primary_container.rpm_label.setText(f"{rpm}")
        self.primary_container.speed_label.setText(f"{speed}")

        sw_stock = self.cluster_vars["left_sw_stock"]
        if sw_stock["left_turn_signal"]:
            self.primary_container.left_turn_signal_image.setPixmap(self.primary_container.left_arrow_image_green)
        else:
            self.primary_container.left_turn_signal_image.setPixmap(self.primary_container.left_arrow_image_black)
        if sw_stock["right_turn_signal"]:
            self.primary_container.right_turn_signal_image.setPixmap(self.primary_container.right_arrow_image_green)
        else:
            self.primary_container.right_turn_signal_image.setPixmap(self.primary_container.right_arrow_image_black)

    def updateVar(self, var, val):
        self.cluster_vars[var] = val
        self.clusterUpdate()


if __name__ == "__main__":
    system = platform.system()

    if system == "Darwin":
        shrink_rate = 1
        screen_size = [1920 / shrink_rate, 720 / shrink_rate]
        cluster_size /= shrink_rate

    app = Application()
    screens = app.screens()

    if system != "Linux":
        import can_data

        if len(screens) > 1:
            screen = screens[1]
            app.primary_container.move(screen.geometry().topLeft())
            app.primary_container.showFullScreen()
        else:
            app.primary_container.setFixedSize(screen_size[0], screen_size[1])

        turn_signal_data = [
            [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x30],  # hazards
            [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20],  # right turn
            [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10],  # left turn
            [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]  # everything off
        ]

        def emulate_can():
            app.updateVar("vehicle_speed",
                          randrange(speed_params["min"], speed_params["max"]))
            app.updateVar("rpm", randrange(rpm_params["min"],
                                           rpm_params["max"]))
            app.updateVar(
                "left_sw_stock",
                can_data.left_sw_stock(turn_signal_data[randrange(
                    0,
                    len(turn_signal_data) - 1)]))

        def run():
            timer = QTimer(app)
            timer.timeout.connect(emulate_can)
            timer.start(0.01)

        app.awakened.connect(run)
    else:
        screen = screens[0]
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
        app.primary_container.setFixedSize(screen_size[0], screen_size[1])

        try:
            shutdown_can = subprocess.run(
                ["sudo", "/sbin/ip", "link", "set", "can0", "down"],
                check=True)
            setup_can = subprocess.run([
                "sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can",
                "bitrate", "500000"
            ],
                                       check=True)
            can_app = CanApplication()
        except:
            print("Could not find PiCan device! Quitting.")
            del app
            exit()

        can_app.updated.connect(app.updateVar)

        def read_can():
            msg = can_app.get_data()

            if msg:
                can_app.parse_data(msg)

        def run():
            timer = QTimer(app)
            timer.timeout.connect(read_can)
            timer.start(0.001)

        app.awakened.connect(run)

    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
