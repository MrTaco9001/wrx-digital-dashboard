# formatted with yapf
# Bryce Happel Walton

import platform
import subprocess
import sys
import tomllib
import can
from math import pi
from time import time
from qutil import change_image_color
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, pyqtSlot
from PyQt5.QtGui import (QColor, QCursor, QFont, QImage, QPalette, QPixmap,
                         QTransform)
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from can_handle import CanApplication, can_ids
from dial import Dial

system = platform.system()

screen_size = [1920, 720]
screen_refresh_rate = 75 if system == "Linux" else 60 if system == "Darwin" else 144

visual_update_intervals = {"coolant_temp": 0.75, "oil_temp": 0.75}

with open("config/gauge_config.toml", "rb") as f:
    gauge_params = tomllib.load(f)

for i in can_ids.keys():
    if not i in visual_update_intervals:
        visual_update_intervals[i] = 1 / (screen_refresh_rate * 2)

original_dial_size = 660

c_to_f_scale = 1.8
c_to_f_offset = 32
kph_to_mph = 0.62137119
gear_calc = (5280 * 12) / (pi * 60)
gear_ratios_l = [3.454, 1.947, 1.296, 0.972, 0.78, 0.666]
tire = 26
final_drive = 4.111


def calcGear(rpm: int, speed: int):
    ratio = (rpm * tire) / (final_drive * speed * kph_to_mph * gear_calc)

    for i, v in enumerate(gear_ratios_l):
        if ratio >= v:
            return f'{i+1}'

    return 'N'


class MainWindow(QMainWindow):

    def __init__(self, scale: float = 1) -> None:
        super().__init__()

        self.setWindowTitle("Digital Cluster")

        font_group = "Sans Serif"
        if system != "Windows":
            font_group = "Microsoft Sans Serif"
        font_weight = 600
        big_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32

        dial_size_int = int(original_dial_size * scale)
        dial_size = QSize(dial_size_int, dial_size_int)

        dial_params_minor = {
            "buffer_radius": 20 * scale,
            "num_radius": 50 * scale,
            "section_radius": 15 * scale,
            "minor_section_rad_offset": 3 * scale,
            "middle_section_rad_offset": 58 * scale,
            "major_section_rad_offset": 40 * scale
        }

        dial_params_major = {
            "buffer_radius": 20 * scale,
            "num_radius": 54 * scale,
            "section_radius": 20 * scale,
            "minor_section_rad_offset": 3 * scale,
            "middle_section_rad_offset": 43 * scale,
            "major_section_rad_offset": 40 * scale
        }

        for i, v in dial_params_minor.items():
            dial_params_minor[i] = int(v)
        for i, v in dial_params_major.items():
            dial_params_major[i] = int(v)

        dial_opacity = 0.3
        dial_width = 120 * scale

        self.coolant_temp_gauge = Dial(
            self,
            size=dial_size,
            min_unit=gauge_params["coolant_temp"]["min"],
            max_unit=gauge_params["coolant_temp"]["max"],
            redline=gauge_params["coolant_temp"]["redline"],
            blueline=gauge_params["coolant_temp"]["blueline"],
            blueline_color=QColor(125, 125, 255),
            dial_opacity=dial_opacity,
            dial_width=30,
            mid_sections=gauge_params["coolant_temp"]["mid_sections"],
            no_font=True,
            visual_num_gap=gauge_params["coolant_temp"]["visual_num_gap"],
            angle_offset=big_dial_angle_range - pi + pi / 2.5,
            angle_range=2 * pi - big_dial_angle_range - pi / 4 * 2,
            **dial_params_minor)
        self.coolant_temp_gauge.move(int(dial_size_int / 4),
                                     int(screen_size[1] / 2 - dial_size_int / 2))

        self.tachometer = Dial(
            self,
            size=dial_size,
            min_unit=gauge_params["tachometer"]["min"],
            max_unit=gauge_params["tachometer"]["max"],
            redline=gauge_params["tachometer"]["redline"],
            mid_sections=gauge_params["tachometer"]["mid_sections"],
            denomination=gauge_params["tachometer"]["denomination"],
            visual_num_gap=gauge_params["tachometer"]["denomination"],
            label_font=QFont(font_group, int(19 * scale), font_weight),
            angle_offset=pi,
            dial_opacity=dial_opacity,
            dial_width=dial_width,
            angle_range=big_dial_angle_range,
            **dial_params_major)
        self.tachometer.frame.setStyleSheet("background:transparent")
        self.tachometer.move(int(dial_size_int / 4),
                             int(screen_size[1] / 2 - dial_size_int / 2))

        self.speedometer = Dial(
            self,
            size=dial_size,
            min_unit=gauge_params["speedometer"]["min"],
            max_unit=gauge_params["speedometer"]["max"],
            redline=gauge_params["speedometer"]["max"] + 1,
            mid_sections=gauge_params["speedometer"]["mid_sections"],
            visual_num_gap=20,
            dial_opacity=dial_opacity,
            dial_width=dial_width,
            label_font=QFont(font_group, int(18 * scale), font_weight),
            angle_offset=pi,
            angle_range=big_dial_angle_range,
            **dial_params_major)
        self.speedometer.move(int(screen_size[0] - dial_size_int - dial_size_int / 4),
                              int(screen_size[1] / 2 - dial_size_int / 2))

        color_black = QColor(0, 0, 0)
        color_green = QColor(0, 255, 0)
        vertical_mirror = QTransform().rotate(180)
        symbol_blue_color = QColor(0, 0, 255)
        symbol_green_color = QColor(0, 230, 0)
        symbol_white_color = QColor(255, 255, 255)
        symbol_yellow_color = QColor(255, 179, 0)
        symbol_red_color = QColor(255, 0, 0)

        right_arrow_image_black = QImage("resources/turn-signal-arrow.png")
        change_image_color(right_arrow_image_black, color_black)
        right_arrow_image_black = QPixmap.fromImage(right_arrow_image_black)

        right_arrow_image_green = QImage("resources/turn-signal-arrow.png")
        change_image_color(right_arrow_image_green, color_green)
        right_arrow_image_green = QPixmap.fromImage(right_arrow_image_green)

        left_arrow_image_black = QImage("resources/turn-signal-arrow.png")
        change_image_color(left_arrow_image_black, color_black)
        left_arrow_image_black = QPixmap.fromImage(left_arrow_image_black)
        left_arrow_image_black = left_arrow_image_black.transformed(
            vertical_mirror)

        left_arrow_image_green = QImage("resources/turn-signal-arrow.png")
        change_image_color(left_arrow_image_green, color_green)
        left_arrow_image_green = QPixmap.fromImage(left_arrow_image_green)
        left_arrow_image_green = left_arrow_image_green.transformed(
            vertical_mirror)

        traction_mode_image = QImage(
            "resources/traction-mode-indicator-light.png")
        change_image_color(traction_mode_image, symbol_green_color)
        traction_mode_image = QPixmap.fromImage(traction_mode_image)

        traction_control_off_image = QImage(
            "resources/vehicle-dynamics-control-off-indicator-light.png")
        change_image_color(traction_control_off_image, symbol_yellow_color)
        traction_control_off_image = QPixmap.fromImage(
            traction_control_off_image)

        seatbelt_warning_image = QImage("resources/seatbelt-warning-light.png")
        change_image_color(seatbelt_warning_image, symbol_red_color)
        seatbelt_warning_image = QPixmap.fromImage(seatbelt_warning_image)

        cruise_control_image = QImage(
            "resources/cruise-control-indicator-light.png")
        change_image_color(cruise_control_image, symbol_white_color)
        cruise_control_image = QPixmap.fromImage(cruise_control_image)

        high_beam_image = QImage("resources/highbeam-indicator-light.png")
        change_image_color(high_beam_image, symbol_blue_color)
        high_beam_image = QPixmap.fromImage(high_beam_image)

        low_beam_image = QImage("resources/headlight-indicator-light.png")
        change_image_color(low_beam_image, symbol_green_color)
        low_beam_image = QPixmap.fromImage(low_beam_image)

        drl_image = low_beam_image

        fog_light_image = QImage("resources/front-fog-indicator-light.png")
        change_image_color(fog_light_image, symbol_green_color)
        fog_light_image = QPixmap.fromImage(fog_light_image)

        turn_signal_offset = int(-30 * scale)
        turn_signal_size = int(55 * scale)
        symbol_size = int(55 * scale)
        bottom_symbol_y_offset = 10

        self.traction_mode_image = QLabel(self)
        self.traction_mode_image.setPixmap(traction_mode_image)
        self.traction_mode_image.setStyleSheet("background:transparent")
        self.traction_mode_image.move(
            int(screen_size[0] / 2 - symbol_size / 2),
            int(screen_size[1] - symbol_size - bottom_symbol_y_offset))
        self.traction_mode_image.setScaledContents(True)
        self.traction_mode_image.resize(symbol_size, symbol_size)

        self.traction_control_off_image = QLabel(self)
        self.traction_control_off_image.setPixmap(traction_control_off_image)
        self.traction_control_off_image.setStyleSheet("background:transparent")
        self.traction_control_off_image.move(
            int(screen_size[0] / 2 - symbol_size / 2 + symbol_size + 5),
            int(screen_size[1] - symbol_size - bottom_symbol_y_offset))
        self.traction_control_off_image.setScaledContents(True)
        self.traction_control_off_image.resize(symbol_size, symbol_size)

        self.seatbelt_warning_image = QLabel(self)
        self.seatbelt_warning_image.setPixmap(seatbelt_warning_image)
        self.seatbelt_warning_image.setStyleSheet("background:transparent")
        self.seatbelt_warning_image.move(
            int(screen_size[0] / 2 - symbol_size / 2 + 4 * (symbol_size + 5)),
            int(screen_size[1] - symbol_size - bottom_symbol_y_offset))
        self.seatbelt_warning_image.setScaledContents(True)
        self.seatbelt_warning_image.resize(symbol_size, symbol_size)

        self.cruise_control_image = QLabel(self)
        self.cruise_control_image.setPixmap(cruise_control_image)
        self.cruise_control_image.setStyleSheet("background:transparent")
        self.cruise_control_image.move(
            int(screen_size[0] - dial_size_int - dial_size_int / 4 + dial_size_int / 2 -
                symbol_size / 2 - 4),
            int(screen_size[1] / 2 - symbol_size / 2 - symbol_size))
        self.cruise_control_image.setScaledContents(True)
        self.cruise_control_image.resize(symbol_size, symbol_size)

        self.high_beam_image = QLabel(self)
        self.high_beam_image.setPixmap(high_beam_image)
        self.high_beam_image.setStyleSheet("background:transparent")
        self.high_beam_image.move(int(dial_size_int / 4 + symbol_size),
                                  int(screen_size[1] / 2 - dial_size_int / 2))
        self.high_beam_image.setScaledContents(True)
        self.high_beam_image.resize(int(symbol_size * 1.25), int(symbol_size * 1.25))

        self.low_beam_image = QLabel(self)
        self.low_beam_image.setPixmap(low_beam_image)
        self.low_beam_image.setStyleSheet("background:transparent")
        self.low_beam_image.move(int(screen_size[0] - dial_size_int - dial_size_int / 4 + dial_size_int - symbol_size * 2),
                                 int(screen_size[1] / 2 - dial_size_int / 2))
        self.low_beam_image.setScaledContents(True)
        self.low_beam_image.resize(int(symbol_size * 1.25), int(symbol_size * 1.25))

        self.fog_light_image = QLabel(self)
        self.fog_light_image.setPixmap(fog_light_image)
        self.fog_light_image.setStyleSheet("background:transparent")
        self.fog_light_image.move(int(dial_size_int / 4),
                                  int(screen_size[1] / 2 - dial_size_int / 2 + symbol_size + 5))
        self.fog_light_image.setScaledContents(True)
        self.fog_light_image.resize(symbol_size, symbol_size)

        self.right_turn_signal_image = QLabel(self)
        self.right_turn_signal_image.setPixmap(right_arrow_image_black)
        self.right_turn_signal_image.setStyleSheet("background:transparent")
        self.right_turn_signal_image.move(
            int(screen_size[0] - dial_size_int - dial_size_int / 4 - turn_signal_offset),
            int(screen_size[1] / 2 - dial_size_int / 2))
        self.right_turn_signal_image.setScaledContents(True)
        self.right_turn_signal_image.resize(turn_signal_size, turn_signal_size)

        self.right_turn_signal_image_active = QLabel(self)
        self.right_turn_signal_image_active.setPixmap(right_arrow_image_green)
        self.right_turn_signal_image_active.setStyleSheet(
            "background:transparent")
        self.right_turn_signal_image_active.move(
            int(screen_size[0] - dial_size_int - dial_size_int / 4 - turn_signal_offset),
            int(screen_size[1] / 2 - dial_size_int / 2))
        self.right_turn_signal_image_active.setScaledContents(True)
        self.right_turn_signal_image_active.resize(turn_signal_size,
                                                   turn_signal_size)

        self.left_turn_signal_image = QLabel(self)
        self.left_turn_signal_image.setPixmap(left_arrow_image_black)
        self.left_turn_signal_image.setStyleSheet("background:transparent")
        self.left_turn_signal_image.move(
            int(dial_size_int / 4 + dial_size_int - turn_signal_size +
                turn_signal_offset), int(screen_size[1] / 2 - dial_size_int / 2))
        self.left_turn_signal_image.setScaledContents(True)
        self.left_turn_signal_image.resize(turn_signal_size, turn_signal_size)

        self.left_turn_signal_image_active = QLabel(self)
        self.left_turn_signal_image_active.setPixmap(left_arrow_image_green)
        self.left_turn_signal_image_active.setStyleSheet(
            "background:transparent")
        self.left_turn_signal_image_active.move(
            int(dial_size_int / 4 + dial_size_int - turn_signal_size +
                turn_signal_offset), int(screen_size[1] / 2 - dial_size_int / 2))
        self.left_turn_signal_image_active.setScaledContents(True)
        self.left_turn_signal_image_active.resize(turn_signal_size,
                                                  turn_signal_size)

        speed_label_size = rpm_label_size = 200
        label_font = QFont(font_group, int(30 * scale))
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        self.speed_label = QLabel(self)
        self.speed_label.setStyleSheet("background:transparent")
        self.speed_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.speed_label.setFont(label_font)
        self.speed_label.setPalette(palette)
        self.speed_label.setText("0")
        sl_size = self.speed_label.frameGeometry().size()
        self.speed_label.move(
            int(screen_size[0] - dial_size_int - dial_size_int / 4 + dial_size_int / 2 -
                sl_size.width() / 2),
            int(screen_size[1] / 2 - sl_size.height() / 2))

        self.gear_label = QLabel(self)
        self.gear_label.setStyleSheet("background:transparent")
        self.gear_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.gear_label.setFont(label_font)
        self.gear_label.setPalette(palette)
        self.gear_label.setText("N")
        gl_size = self.speed_label.frameGeometry().size()
        self.gear_label.move(
            int(dial_size_int / 4 + dial_size_int / 2 - gl_size.width() / 2),
            int(screen_size[1] / 2 - gl_size.height() / 2))

        label_font = QFont(font_group, int(16 * scale))
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        self.oil_temp_label = QLabel(self)
        self.oil_temp_label.setStyleSheet("background:transparent")
        self.oil_temp_label.setText(f"Oil Temp: {0} F")
        self.oil_temp_label.setFont(label_font)
        self.oil_temp_label.setPalette(palette)
        self.oil_temp_label.resize(int(150 * scale),
                                   int(rpm_label_size * scale))
        self.oil_temp_label.move(
            int(screen_size[0] / 2 -
                self.oil_temp_label.frameGeometry().width() / 2 * scale),
            int(screen_size[1] / 2 -
                self.oil_temp_label.frameGeometry().height() / 2 * scale))

        label_font = QFont(font_group, int(17 * scale))
        color = QColor(255, 0, 0)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        self.hand_brake_label = QLabel(self)
        self.hand_brake_label.setStyleSheet("background:transparent")
        self.hand_brake_label.setText(f"BRAKE")
        self.hand_brake_label.setFont(label_font)
        self.hand_brake_label.setPalette(palette)
        self.hand_brake_label.resize(int(80 * scale), int(75 * scale))
        self.hand_brake_label.move(
            int(screen_size[0] - dial_size_int - dial_size_int / 4 + dial_size_int / 2 -
                self.hand_brake_label.frameGeometry().width() / 2 * scale),
            int(screen_size[1] / 2 - dial_size_int / 2 + speed_label_size * scale +
                self.hand_brake_label.frameGeometry().height() * 4 * scale))


class Application(QApplication):

    awakened = pyqtSignal()

    cluster_vars = {}
    cluster_vars_update_ts = {
        i: time()
        for i in visual_update_intervals.keys()
    }

    awaken_sequence_duration_ms = 1750

    def __init__(self, scale: float = 1) -> None:
        super().__init__([])
        self.setOverrideCursor(QCursor(Qt.BlankCursor))
        primary_container = MainWindow(scale)
        background_color = (15, 15, 15)
        primary_container.setStyleSheet(
            f"background-color: rgb({background_color[0]}, {background_color[1]}, {background_color[2]})"
        )

        self.start_time = time()
        self.primary_container = primary_container

        self.update_funcs = {}

        self.awakenClusters()

    def awakenClusters(self) -> None:
        timer = QTimer(self)

        self._awaken_a = 0
        self._awaken_t = 0

        t_step = self.awaken_sequence_duration_ms // 1000
        a_step = t_step / self.awaken_sequence_duration_ms

        self.primary_container.tachometer.setDial(0)
        self.primary_container.speedometer.setDial(0)

        self._last_time = time() * 1000
        start_time = self._last_time

        @pyqtSlot()
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

    def updateGearIndicator(self) -> None:
        speed = self.cluster_vars.get('vehicle_speed', 1)
        rpm = self.cluster_vars.get('rpm', 0)
        neutral = self.cluster_vars.get('neutral_switch', 0)
        reverse = self.cluster_vars.get('reverse_switch', 0)
        clutch = self.cluster_vars.get('clutch_switch', 0)

        if reverse:
            gear = 'R'
        elif neutral:
            gear = 'N'
        else:
            if speed == 0:
                gear = ''
            else:
                gear = calcGear(rpm, speed)

        self.primary_container.gear_label.setText(gear)

    @pyqtSlot(tuple)
    def updateVar(self, new_vars: tuple) -> None:
        t = time()
        var, val = new_vars
        self.cluster_vars[var] = val

        if t - self.cluster_vars_update_ts[var] <= visual_update_intervals[var]:
            return

        if var == "vehicle_speed":
            self.primary_container.speed_label.setText(
                f"{val * kph_to_mph:.0f}")
            self.primary_container.speedometer.setUnit(val * kph_to_mph)
        elif var == "rpm":
            self.updateGearIndicator()
            self.primary_container.tachometer.setUnit(val)
        elif var == "turn_signals":
            left_turn_signal = val["left_turn_signal"]
            right_turn_signal = val["right_turn_signal"]

            self.primary_container.left_turn_signal_image.setVisible(
                not left_turn_signal)
            self.primary_container.left_turn_signal_image_active.setVisible(
                left_turn_signal)
            self.primary_container.right_turn_signal_image.setVisible(
                not right_turn_signal)
            self.primary_container.right_turn_signal_image_active.setVisible(
                right_turn_signal)
        elif var == "fuel_level":
            pass
        elif var == "oil_temp":
            self.primary_container.oil_temp_label.setText(
                f"Oil Temp: {val * c_to_f_scale + c_to_f_offset:.0f} F")
        elif var == "coolant_temp":
            self.primary_container.coolant_temp_gauge.setUnit(val *
                                                              c_to_f_scale +
                                                              c_to_f_offset)
        elif var == "handbrake":
            self.primary_container.hand_brake_label.setVisible(val)
        elif var == "neutral_switch":
            self.updateGearIndicator()
        elif var == "reverse_switch":
            self.updateGearIndicator()
        elif var == "traction_control":
            self.primary_container.traction_control_off_image.setVisible(val)
        elif var == "trac_mode":
            self.primary_container.traction_mode_image.setVisible(val)
        elif var == "seatbelt_driver":
            self.primary_container.seatbelt_warning_image.setVisible(val)
        elif var == "cruise_control":
            self.primary_container.cruise_control_image.setVisible(val)
        elif var == "fog_lights":
            self.primary_container.fog_light_image.setVisible(val)
        elif var == "door_states":
            pass
        elif var == "headlights":
            self.primary_container.low_beam_image.setVisible(val["lowbeams"] or val["drls"])
            self.primary_container.high_beam_image.setVisible(val["highbeams"])

        self.cluster_vars[var] = val
        self.cluster_vars_update_ts[var] = t


if __name__ == "__main__":
    scale = 1
    if system == "Darwin":
        scale = 1 / 1.3325
    elif system == "Windows":
        scale = 1 / 1.25

    screen_size = [int(1920 * scale), int(720 * scale)]
    app = Application(scale=scale)

    screens = app.screens()
    if system != "Linux":
        if len(screens) > 1:
            screen = screens[1]
            app.primary_container.move(screen.geometry().topLeft())
            app.primary_container.showFullScreen()
        else:
            app.primary_container.setFixedSize(screen_size[0], screen_size[1])
    else:
        screen = screens[0]
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
        app.primary_container.setFixedSize(screen_size[0], screen_size[1])

    if system == "Linux" and len(sys.argv) > 1:
        using_canbus = sys.argv[1] != "nocan"
    elif system != "Linux":
        using_canbus = False
    else:
        using_canbus = True

    if system == "Linux":
        try:
            shutdown_can = subprocess.run(
                ["sudo", "/sbin/ip", "link", "set", "can0", "down"],
                check=True)
            setup_can = subprocess.run([
                "sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can",
                "bitrate", "500000"
            ],
                                       check=True)

            bus = can.interface.Bus(channel='can0',
                                    bustype='socketcan',
                                    bitrate=500000)
        except:
            print("Could not find PiCan device. Switching to emulation.")
            using_canbus = False

    if not using_canbus:
        import test_provider

        bus_virtual_car = can.interface.Bus(channel='test', bustype='virtual')
        bus = can.interface.Bus(channel='test', bustype='virtual')

        @pyqtSlot()
        def emulate_car():
            bus_virtual_car.send(test_provider.provide_random_message())

        @pyqtSlot()
        def run():
            timer = QTimer(app)
            timer.timeout.connect(emulate_car)
            timer.start(1000 // 500000)

        app.awakened.connect(run)

    can_app = CanApplication(app, bus)
    can_app.updated.connect(app.updateVar)

    @pyqtSlot()
    def run():
        can.Notifier(bus, [can_app.parse_data])

    app.awakened.connect(run)
    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
