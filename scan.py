# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import asyncio
# import shutil
import subprocess
import time
import os
import websockets

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QMainWindow, QSizePolicy, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QPushButton, QSpinBox, QFormLayout
from PyQt5.QtWidgets import QAbstractSpinBox
from PyQt5.QtWidgets import QScrollArea, QScrollBar
from PyQt5.QtCore import QEvent, Qt, QTimer, QThread, pyqtSignal, QRect
import numpy as np
import cv2
import datetime
import zipfile

from PyQt5 import QtGui
from vassal import Terminal
from threading import Thread
import json
import xml.etree.ElementTree as Xml

from imutils.video import VideoStream

from scan_settings_dialog import SettingsDialog, ProgramSettings


# Класс главного окна
class ScanWindow(QMainWindow):
    # Инициализация
    def __init__(self, main_window):
        super().__init__()
        self.test = False
        self.test_only_camera = False
        self.main_window = main_window
        # self.micros_controller = TableController('localhost', 5001)
        self.loop = asyncio.get_event_loop()
        self.program_settings = ProgramSettings(self.test)
        # self.lbl_img = LabelImg()
        self.lbl_img = QLabel(self)
        self.scroll_area_img = QScrollArea(self)
        self.scrollbar_img_hor = QScrollBar(Qt.Horizontal, self)
        self.scrollbar_img_vert = QScrollBar(Qt.Vertical, self)

        self.dir_for_img = "SavedImg"
        self.path_for_xml_file = os.path.join(self.dir_for_img, "settings.xml")

        # Перенос параметров с MicrosController
        if self.test:
            self.test_img_path = os.path.join("TEST", "MotherBoard_3.jpg")
            # self.test_img_path = os.path.join("TEST", "MotherBoard_2.jpg")
            # self.test_img_path = os.path.join("TEST", "MotherBoard_5.jpg")
            self.test_img = cv2.imread(self.test_img_path)[:, :, :]
        # self.frame = list()
        self.video_img = None
        self.video_check = False

        if not self.test:
            max_video_streams = 5
            video_stream_index = -1
            # vs = VideoStream(src=video_stream_index).start()
            check_next_stream = True
            while check_next_stream:
                video_stream_index += 1
                if video_stream_index > max_video_streams:
                    time.sleep(1.0)
                    video_stream_index = 0

                # self.video_stream = VideoStream(src=video_stream_index).start()
                # self.video_stream = VideoStream(src=video_stream_index, usePiCamera=True,
                #                                 resolution=(1920, 1080)).start()
                self.video_stream = cv2.VideoCapture(video_stream_index)
                self.video_stream.set(3, 1920)
                self.video_stream.set(4, 1080)

                # noinspection PyBroadException
                try:
                    self.video_check, self.video_img = self.video_stream.read()
                    if not self.video_check:
                        continue
                    # check_frame = img[:, :, :]
                    check_next_stream = False
                except Exception:
                    # self.video_stream.stop()
                    check_next_stream = True
        else:
            self.video_stream = None

        self.vidik = VideoStreamThread(self.video_stream, self.video_img, self)
        if not self.test:
            self.vidik.changePixmap.connect(self.lbl_img.setPixmap)
            self.vidik.start()

        self.table_controller = TableController(self.loop, self.program_settings, self.vidik, self.test)
        # TEST Для удобства тестирования передаю в контроллер стола контроллер камеры
        # self.micros_controller = MicrosController(self.program_settings, self.test, self.lbl_img)
        # if self.table_controller.test:
        #     self.table_controller.micros_controller = self.micros_controller
        #     self.table_controller.program_settings = self.program_settings

        # if not self.table_controller.thread_server or not self.table_controller.thread_server.is_alive():

        if not self.test and not self.test_only_camera:
            self.table_controller.thread_server.start()
        time.sleep(2.0)
        # self.micros_controller.coord_check()
        self.continuous_mode = False
        self.closed = False
        self.key_shift_pressed = False
        # self.keyboard_buttons = {Qt.Key_Up: KeyboardButton(), Qt.Key_Right: KeyboardButton(),
        #                          Qt.Key_Down: KeyboardButton(), Qt.Key_Left: KeyboardButton(),
        #                          Qt.Key_Plus: KeyboardButton(), Qt.Key_Minus: KeyboardButton()}
        self.keyboard_buttons = {Qt.Key_W: KeyboardButton(), Qt.Key_D: KeyboardButton(),
                                 Qt.Key_S: KeyboardButton(), Qt.Key_A: KeyboardButton(),
                                 Qt.Key_Plus: KeyboardButton(), Qt.Key_Minus: KeyboardButton()}
        # Пока отключу лишний процесс ручного управления temp
        # self.thread_continuous = Thread(target=self.continuous_move)

        # self.thread_continuous = QThread()
        # self.thread_continuous.started.connect(self.continuous_move)

        self.timer_continuous = QTimer()
        self.timer_continuous.setInterval(1)
        self.timer_continuous.timeout.connect(self.continuous_move)

        # if not self.test:
        #     self.thread_continuous.start()

        # self.thread_video = Thread(target=self.video_thread)
        # self.thread_video.start()



        # self.table_controller.steps_in_mm = self.program_settings.table_settings.steps_in_mm
        # self.table_controller.limits_mm = self.program_settings.table_settings.limits_mm
        # self.table_controller.limits_step = self.program_settings.table_settings.limits_step

        # self.table_controller.limits_step = list()
        # for limit_mm in self.table_controller.limits_mm:
        #     self.table_controller.limits_step.append(limit_mm * self.table_controller.steps_in_mm)

        # self.pixels_in_mm = self.program_settings.snap_settings.pixels_in_mm
        # self.snap_width = self.program_settings.snap_settings.snap_width
        # self.snap_height = self.program_settings.snap_settings.snap_height
        # self.snap_width_mm = self.snap_width / self.pixels_in_mm
        # self.snap_height_mm = self.snap_height / self.pixels_in_mm
        # self.work_height = self.program_settings.snap_settings.work_height
        #
        # # self.micros_controller.frame = self.program_settings.snap_settings.frame
        # self.frame_width = self.micros_controller.frame[2] - self.micros_controller.frame[0]
        # self.frame_height = self.micros_controller.frame[3] - self.micros_controller.frame[1]
        # self.frame_width_mm = self.frame_width / self.pixels_in_mm
        # self.frame_height_mm = self.frame_height / self.pixels_in_mm
        #
        # self.delta_x = int(self.frame_width / 10)
        # self.delta_y = int(self.frame_height / 10)

        # Наличие несохраненного изображения
        self.unsaved = False

        if self.test:
            print("Внимание! Программа работает в тестовом режиме!")

        # Доступные для взаимодействия компоненты формы
        self.lbl_coord = QLabel("Текущие координаты:")
        self.btn_init = QPushButton("Инициализация")
        self.btn_move_work_height = QPushButton("Занять рабочую высоту")
        self.btn_move_mid = QPushButton("Двигать в середину")
        self.btn_move = QPushButton("Двигать в ...")
        self.btn_manual = QPushButton("Ручной режим")
        self.edt_border_x1 = QSpinBox()
        self.edt_border_y1 = QSpinBox()
        self.edt_border_x2 = QSpinBox()
        self.edt_border_y2 = QSpinBox()
        self.btn_border = QPushButton("Определить границы")
        self.btn_scan = QPushButton("Новая съемка")
        self.btn_scan_without_borders = QPushButton("Съемка без границ")
        self.btn_save_scan = QPushButton("Сохранить съемку")

        self.clear_test_data()

        self.init_ui()

    # Создание элементов формы
    def init_ui(self):

        # keyboard.add_hotkey("Ctrl + 1", lambda: print("Left"))

        # Основное меню
        menu_bar = self.menuBar()
        # Меню "Станок"
        device_menu = menu_bar.addMenu("&Станок")
        device_menu_action_init = QAction("&Инициализация", self)
        device_menu_action_init.setShortcut("Ctrl+I")
        device_menu_action_init.triggered.connect(self.device_init)
        device_menu.addAction(device_menu_action_init)

        device_menu.addSeparator()
        device_menu_action_check = QAction("&Проверка", self)
        device_menu_action_check.setShortcut("Ctrl+C")
        device_menu_action_check.triggered.connect(self.device_check)
        device_menu.addAction(device_menu_action_check)

        device_menu.addSeparator()
        device_menu_action_move = QAction("&Двигать", self)
        device_menu_action_move.setShortcut("Ctrl+M")
        device_menu_action_move.triggered.connect(self.device_move)
        device_menu.addAction(device_menu_action_move)

        device_menu.addSeparator()
        device_menu_action_test_circle = QAction("&Круг", self)
        device_menu_action_test_circle.triggered.connect(self.test_circle)
        device_menu.addAction(device_menu_action_test_circle)

        device_menu.addSeparator()
        device_menu_action_exit = QAction("&Выйти", self)
        device_menu_action_exit.setShortcut("Ctrl+Q")
        device_menu_action_exit.setStatusTip("Закрыть приложение")
        device_menu_action_exit.triggered.connect(self.close)
        device_menu.addAction(device_menu_action_exit)
        menu_bar.addMenu(device_menu)

        # Меню "Настройки"
        services_menu = menu_bar.addMenu("&Сервис")
        services_menu_action_settings = QAction("&Настройки", self)
        services_menu_action_settings.triggered.connect(self.services_menu_action_settings_click)
        services_menu.addAction(services_menu_action_settings)
        menu_bar.addMenu(services_menu)

        # установка центрального виджета и лайаута
        main_widget = QWidget(self)
        central_layout = QHBoxLayout()
        main_widget.setLayout(central_layout)
        self.setCentralWidget(main_widget)

        # левый лайаут с изображением
        left_layout = QVBoxLayout()
        central_layout.addLayout(left_layout)

        self.scroll_area_img.setWidget(self.lbl_img)
        self.scroll_area_img.setWidgetResizable(True)
        # self.scroll_area_img.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.scroll_area_img.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scrollbar_img_hor.setMaximum(self.scroll_area_img.horizontalScrollBar().maximum())
        self.scrollbar_img_hor.valueChanged.connect(self.sync_scroll)
        self.scrollbar_img_vert.setMaximum(self.scroll_area_img.verticalScrollBar().maximum())
        self.scrollbar_img_vert.valueChanged.connect(self.sync_scroll)

        self.lbl_img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_img.setStyleSheet("border: 1px solid red")

        # left_layout.addWidget(self.lbl_img)
        left_layout.addWidget(self.scroll_area_img)
        # left_layout.addWidget(self.scrollbar_img_hor)
        # left_layout.addWidget(self.scrollbar_img_vert)

        # правый лайаут с панелью
        right_layout = QVBoxLayout()
        central_layout.addLayout(right_layout)
        right_layout.addWidget(self.lbl_coord)
        self.btn_init.clicked.connect(self.device_init)
        right_layout.addWidget(self.btn_init)
        self.btn_move.clicked.connect(self.device_move)
        right_layout.addWidget(self.btn_move)
        self.btn_move_work_height.clicked.connect(self.device_move_work_height)
        right_layout.addWidget(self.btn_move_work_height)
        self.btn_move_mid.clicked.connect(self.device_move_mid)
        right_layout.addWidget(self.btn_move_mid)

        self.btn_manual.setCheckable(True)
        self.btn_manual.setChecked(False)
        self.btn_manual.toggled["bool"].connect(self.device_manual)
        right_layout.addWidget(self.btn_manual)

        # self.edt_border_x1.setLineWrapMode(QTextEdit_LineWrapMode=QTextEdit.NoWrap)
        border_layout = QVBoxLayout()
        right_layout.addStretch()
        right_layout.addLayout(border_layout)
        border_layout.addWidget(QLabel("Границы съемки:"))
        # border_form_layout = QGridLayout()
        border_form_layout = QFormLayout()
        # self.edt_border_x1.setWordWrapMode(QtGui.QTextOption.NoWrap)
        for edt in [self.edt_border_x1, self.edt_border_y1, self.edt_border_x2, self.edt_border_y2]:
            edt.setMaximumHeight(30)
            edt.setMinimum(0)
            edt.setSuffix(" mm")
            edt.setButtonSymbols(QAbstractSpinBox.NoButtons)
            edt.setSingleStep(0)

        self.edt_border_x1.setMaximum(self.program_settings.table_settings.limits_mm[0])
        self.edt_border_x2.setMaximum(self.program_settings.table_settings.limits_mm[0])
        self.edt_border_y1.setMaximum(self.program_settings.table_settings.limits_mm[1])
        self.edt_border_y2.setMaximum(self.program_settings.table_settings.limits_mm[1])

        border_form_layout.addRow(QLabel("x1"), self.edt_border_x1)
        border_form_layout.addRow(QLabel("y1"), self.edt_border_y1)
        border_form_layout.addRow(QLabel("x2"), self.edt_border_x2)
        border_form_layout.addRow(QLabel("y2"), self.edt_border_y2)
        border_form_layout.setSpacing(0)
        # border_form_layout.setSpacing(2)
        # border_form_layout.addWidget(QLabel("x1"), 0, 0)
        # border_form_layout.addWidget(self.edt_border_x1, 1, 0)
        # border_form_layout.addWidget(QLabel("y1"), 2, 0)
        # border_form_layout.addWidget(self.edt_border_y1, 3, 0)
        # border_form_layout.addWidget(QLabel("x2"), 0, 1)
        # border_form_layout.addWidget(self.edt_border_x2, 1, 1)
        # border_form_layout.addWidget(QLabel("y2"), 2, 1)
        # border_form_layout.addWidget(self.edt_border_y2, 3, 1)

        border_layout.addLayout(border_form_layout)

        right_layout.addWidget(self.btn_border)
        self.btn_border.clicked.connect(self.border_find)
        right_layout.addWidget(self.btn_scan)
        self.btn_scan.clicked.connect(self.scan)

        right_layout.addWidget(self.btn_scan_without_borders)
        self.btn_scan_without_borders.clicked.connect(self.scan_without_borders)

        right_layout.addWidget(self.btn_save_scan)
        self.btn_save_scan.clicked.connect(self.save_scan)
        self.btn_save_scan.setEnabled(False)

        self.installEventFilter(self)

        self.resize(1280, 720)
        self.move(300, 300)
        self.setMinimumSize(800, 600)
        # self.show()
        # print(self.pixels_in_mm)

    def sync_scroll(self):
        self.scroll_area_img.horizontalScrollBar().setValue(self.scrollbar_img_hor.value())

    def __get_pixels_in_mm(self):
        return self.program_settings.snap_settings.pixels_in_mm
    pixels_in_mm = property(__get_pixels_in_mm)

    def __get_snap_width(self):
        return self.program_settings.snap_settings.snap_width
    snap_width = property(__get_snap_width)

    def __get_snap_height(self):
        return self.program_settings.snap_settings.snap_height
    snap_height = property(__get_snap_height)

    def __get_snap_width_mm(self):
        return self.snap_width / self.pixels_in_mm[0]
    snap_width_mm = property(__get_snap_width_mm)

    def __get_snap_height_mm(self):
        return self.snap_height / self.pixels_in_mm[1]
    snap_height_mm = property(__get_snap_height_mm)

    def __get_work_height(self):
        return self.program_settings.snap_settings.work_height
    work_height = property(__get_work_height)

    def __get_delta_x(self):
        return int(self.frame_width / 10)
    delta_x = property(__get_delta_x)
    # def delta_x(self):
    #     return int(self.frame_width / 10)

    def __get_delta_y(self):
        return int(self.frame_height / 10)
    delta_y = property(__get_delta_y)
    # def delta_y(self):
    #     return int(self.frame_height / 10)

    def __get_frame_width(self):
        return self.program_settings.snap_settings.frame[2] - self.program_settings.snap_settings.frame[0]
    frame_width = property(__get_frame_width)
    # def frame_width(self):
    #     return self.program_settings.snap_settings.frame[2] - self.program_settings.snap_settings.frame[0]

    def __get_frame_height(self):
        return self.program_settings.snap_settings.frame[3] - self.program_settings.snap_settings.frame[1]
    frame_height = property(__get_frame_height)
    # def frame_height(self):
    #     return self.program_settings.snap_settings.frame[3] - self.program_settings.snap_settings.frame[1]

    def __get_frame_width_mm(self):
        return self.frame_width / self.pixels_in_mm[0]
    frame_width_mm = property(__get_frame_width_mm)

    def __get_frame_height_mm(self):
        return self.frame_height / self.pixels_in_mm[1]
    frame_height_mm = property(__get_frame_height_mm)

    def __get_frame(self):
        return self.program_settings.snap_settings.frame
    frame = property(__get_frame)

    def snap(self, x1: int, y1: int, x2: int, y2: int, crop=False):
        if self.test:
            time.sleep(0.05)
            # return np.copy(self.test_img[y1:y2, x1:x2, :])
            # Переворачиваем координаты съемки
            y2_r = 6400 - y1
            y1_r = 6400 - y2
            return np.copy(self.test_img[y1_r:y2_r, x1:x2, :])
        else:
            # self.video_timer.stop()
            time.sleep(0.15)
            # for i in range(10):
            #     self.video_stream.read()
            # Прогревочные съемки
            for i in range(10):
                self.video_stream.read()
            check, img = self.video_stream.read()
            self.lbl_img.setPixmap(self.vidik.numpy_to_pixmap(img))
            self.lbl_img.repaint()

            # img = self.vidik.video_img
            # self.video_timer.start()
            if crop:
                # return np.copy(img[self.frame[3]-1:self.frame[1]:-1, self.frame[2]-1:self.frame[0]:-1, :])
                # return np.copy(img[self.frame[1]:self.frame[3], self.frame[0]:self.frame[2], :][::-1, ::-1, :])
                return np.copy(img[self.frame[1]:self.frame[3], self.frame[0]:self.frame[2], :])
            else:
                # return np.copy(img[::-1, ::-1, :])
                return np.copy(img)

    # Тестовая обертка функции движения, чтобы обходиться без подключенного станка
    def coord_move(self, coord, mode="discrete", crop=False):
        if not self.test and mode != "continuous":
            self.vidik.work = False
        self.table_controller.coord_move(coord, mode)
        self.setWindowTitle(str(self.table_controller))
        if self.table_controller.test or mode != "continuous":
            # snap = self.micros_controller.snap(int(self.pixels_in_mm * (self.table_controller.coord_mm[0]
            #                                                             - self.snap_width_mm_half)),
            #                                    int(self.pixels_in_mm * (self.table_controller.coord_mm[1]
            #                                                             - self.snap_height_mm_half)),
            #                                    int(self.pixels_in_mm * (self.table_controller.coord_mm[0]
            #                                                             + self.snap_width_mm_half)),
            #                                    int(self.pixels_in_mm * (self.table_controller.coord_mm[1]
            #                                                             + self.snap_height_mm_half)),
            #                                    crop=crop)
            snap = self.snap(int(self.pixels_in_mm[0] * (self.table_controller.coord_mm[0])),
                             int(self.pixels_in_mm[1] * (self.table_controller.coord_mm[1])),
                             int(self.pixels_in_mm[0] * (self.table_controller.coord_mm[0] + self.snap_width_mm)),
                             int(self.pixels_in_mm[1] * (self.table_controller.coord_mm[1] + self.snap_height_mm)),
                             crop=crop)
            if self.test:
                self.lbl_img.setPixmap(self.vidik.numpy_to_pixmap(snap))
                self.lbl_img.repaint()
            return snap
        # self.lbl_img.setPixmap(self.vidik.numpy_to_pixmap(snap))
        # self.lbl_img.repaint()
        self.vidik.work = True
        return None

    def closeEvent(self, event):
        if self.unsaved:
            dlg_result = QMessageBox.question(self,
                                              "Confirm Dialog",
                                              "Данные последней съемки не сохранены. Хотите сперва их сохранить?",
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                              QMessageBox.Yes)
            if dlg_result == QMessageBox.Yes:
                if not self.save_scan():
                    event.ignore()
                    return
            elif dlg_result == QMessageBox.Cancel:
                event.ignore()
                return
        self.main_window.show()
        time.sleep(0.01)
        self.hide()
        event.ignore()
        self.closed = True

    def services_menu_action_settings_click(self):
        if self.program_settings.test:
            QMessageBox.warning(self, "Warning!",
                                "Программа работает в тестовом режиме. Настройки не будут сохраняться!",
                                QMessageBox.Ok, QMessageBox.Ok)
        settings_dialog = SettingsDialog(self.program_settings)
        settings_dialog.setAttribute(Qt.WA_DeleteOnClose)
        dlg_result = settings_dialog.exec()
        if dlg_result > 0:
            self.table_controller.server_status = 'uninitialized'

    # def device_init(self):
    #     init_thread = Thread(target=self.device_init_in_thread)
    #     init_thread.start()
    #     print("init start")

    def device_init(self):
        self.vidik.work = False
        self.control_elements_enabled(False)
        self.table_controller.coord_init()
        self.setWindowTitle(str(self.table_controller))
        self.coord_move(self.table_controller.coord_mm, mode="discrete", crop=True)
        self.control_elements_enabled(True)
        self.vidik.work = True

    def device_check(self):
        self.table_controller.coord_check()
        self.setWindowTitle(str(self.table_controller))

    # def device_move(self):
    #     move_thread = Thread(target=self.device_move_in_thread)
    #     move_thread.start()
    #     print("move start")

    def device_move(self):
        self.vidik.work = False
        self.control_elements_enabled(False)
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self,
                                        "Введите координаты в миллиметрах",
                                        "Координаты:",
                                        QLineEdit.Normal,
                                        "{0:.2f}; {1:.2f}; {2:.2f}".format(self.table_controller.coord_mm[0],
                                                                         self.table_controller.coord_mm[1],
                                                                         self.table_controller.coord_mm[2]))

        if ok:
            coord = [float(item) for item in str.replace(str.replace(text, ',', '.'), ' ', '').split(';')]
            if len(coord) == 3:
                self.coord_move(coord)
                self.setWindowTitle(str(self.table_controller))

        self.control_elements_enabled(True)
        self.vidik.work = True

    def device_move_mid(self):
        self.vidik.work = False
        self.control_elements_enabled(False)
        x = int(self.table_controller.limits_mm[0] / 2)
        y = int(self.table_controller.limits_mm[1] / 3)
        self.coord_move([x, y, self.table_controller.coord_mm[2]])
        self.setWindowTitle(str(self.table_controller))
        self.control_elements_enabled(True)
        self.vidik.work = True

    def device_move_work_height(self):
        self.vidik.work = False
        self.control_elements_enabled(False)
        self.coord_move([self.table_controller.coord_mm[0],
                         self.table_controller.coord_mm[1],
                         self.work_height])
        self.setWindowTitle(str(self.table_controller))
        self.control_elements_enabled(True)
        self.vidik.work = True

    def device_manual(self, status):
        if status:
            self.continuous_mode = True
            # self.thread_continuous.start()
            self.timer_continuous.start()
            # print("thread started")
        else:
            # self.thread_continuous.terminate()
            self.timer_continuous.stop()
            self.continuous_mode = False
            # print("thread joined")

        # self.continuous_mode = status

        # self.control_elements_enabled(not status)
        # print("device manual finished")

    def control_elements_enabled(self, status):
        self.btn_init.setEnabled(status)
        self.btn_move.setEnabled(status)
        self.btn_move_mid.setEnabled(status)
        self.btn_move_work_height.setEnabled(status)
        self.btn_border.setEnabled(status)
        self.btn_scan.setEnabled(status)
        self.btn_save_scan.setEnabled(status)
        self.edt_border_x1.setEnabled(status)
        self.edt_border_y1.setEnabled(status)
        self.edt_border_x2.setEnabled(status)
        self.edt_border_y2.setEnabled(status)

    @staticmethod
    def save_test_data(data):
        f = open('test.txt', 'a')
        now = datetime.datetime.now()
        f.write(now.strftime("%d.%m.%Y %H:%M:%S") + "<=" + str(data) + '\r\n')
        f.close()

    @staticmethod
    def clear_test_data():
        f = open('test.txt', 'w+')
        f.seek(0)
        f.close()

    # Тестовая функция для рисования круга и спирали
    def test_circle(self):
        self.main_window.show()
        self.close()
        # self.table_controller.coord_check()
        # count = 200
        # r = 0.0
        # # r = 20
        # for i in range(20*count + 1):
        #     r += 1 / 10
        #     alfa = (i / count) * 2 * math.pi
        #     dx = int(r * math.sin(alfa))
        #     dy = int(r * math.cos(alfa))
        #     self.coord_move([dx, dy, 0], mode='continuous')
        #     self.micros_controller.coord_move([self.micros_controller.coord[0] + dx,
        #                                        self.micros_controller.coord[1] + dy,
        #                                        self.micros_controller.coord[2]])
        # for d in range(1, 7):
        #     print(d)
        #     d_steps = int(2 ** d)
        #     for i in range(100):
        #         self.micros_controller.coord_move([d_steps, 0, 0], mode='continuous')
        #     for i in range(100):
        #         self.micros_controller.coord_move([-d_steps, 0, 0], mode='continuous')
        #     for i in range(100):
        #         self.micros_controller.coord_move([0, d_steps, 0], mode='continuous')
        #     for i in range(100):
        #         self.micros_controller.coord_move([0, -d_steps, 0], mode='continuous')

    # Функция идет по границе изделия и записывает пределы для съемки
    def border_find(self):
        self.vidik.work = False
        self.control_elements_enabled(False)
        try:
            if self.table_controller.server_status == 'uninitialized':
                self.table_controller.coord_init()

            # Перевод камеры к позиции, где должна располагаться микросхема
            x = int(self.table_controller.limits_mm[0] / 2)
            y = int(self.table_controller.limits_mm[1] / 3)
            if self.test:
                y = int(self.table_controller.limits_mm[1] / 2)
            snap = self.coord_move([x, y, self.table_controller.coord_mm[2]], mode="discrete", crop=True)

            all_x = list()
            all_y = list()
            all_x.append(x)
            all_y.append(y)

            # Направления для поиска краев
            # direction_sequence = [[1, 0], [0, 1], [-1, 0], [0, -1], [1, 0], [0, 1]]
            # previous_direction = None
            direction = Direction()
            while direction.abs_index < 6:
                print(direction)
                # Параметр захода за середину для ускорения обхода (от 0 до 4)
                forward_over_move = 4
                forward_count_total = 0
                previous_direction = direction.previous()
                # for direction in direction_sequence:
                # Берем следующий фрейм до тех пор, пока не выйдем за границу изделтя
                self.save_test_data("direction=" + str(direction))
                while True:
                    # При наличии предыдущего направления движения (все, кроме первого направления)
                    # проверяем, не смещается ли изделие поперек линии поиска
                    # if previous_direction:
                    if direction.abs_index > 0:
                        # Проверяем - не ушли ли мы вовнутрь или наружу объекта
                        # stuck - это проверка, что мы попали в петлю
                        stuck = False
                        correction_list = list()
                        while not stuck:
                            correction_count = self.check_object_middle(snap,
                                                                        previous_direction,
                                                                        [self.delta_x, self.delta_y])
                            correction_list.append(correction_count)
                            if len(correction_list) >= 4:
                                # Проверка на повторяющиеся коррекции
                                if correction_list[-1] == correction_list[-3]:
                                    if correction_list[-2] == correction_list[-4]:
                                        if correction_list[-1] * correction_list[-2] < 0:
                                            correction_count //= 2
                                            stuck = True
                                            self.save_test_data("unstuck doubled!")
                                # На особенно запущенный случай зацикливания
                                if len(correction_list) >= 12:
                                    stuck = True
                                    self.save_test_data("unstuck loop repeatedly!")
                            if correction_count == 0:
                                break
                            # Проверяем - не вышли ли мы за пределы стола
                            while True:
                                x += int(self.delta_x * correction_count * previous_direction[0] / self.pixels_in_mm[0])
                                y -= int(self.delta_y * correction_count * previous_direction[1] / self.pixels_in_mm[1])
                                if x < 0 or y < 0 or x > self.table_controller.limits_mm[0] or y > \
                                        self.table_controller.limits_mm[1]:
                                    x = all_x[-1]
                                    y = all_y[-1]
                                    correction_count -= int(abs(correction_count) / correction_count)
                                    if correction_count == 0:
                                        break
                                else:
                                    break
                            if correction_count == 0:
                                break
                            # x += int(self.delta_x * correction_count * previous_direction[0] / self.pixels_in_mm)
                            # y -= int(self.delta_y * correction_count * previous_direction[1] / self.pixels_in_mm)
                            all_x.append(x)
                            all_y.append(y)
                            snap = self.coord_move([x, y, self.table_controller.coord_mm[2]], mode="discrete", crop=True)
                            if correction_count > 0:
                                self.save_test_data('x = ' + str(x) + '; y = ' + str(y) + ' inside correction')
                            elif correction_count < 0:
                                self.save_test_data('x = ' + str(x) + '; y = ' + str(y) + ' outside correction')

                    forward_count = self.find_border_in_image(snap,
                                                              direction,
                                                              [self.delta_x, self.delta_y],
                                                              forward_over_move)
                    # Можно идти в направлении поиска границы еще
                    if forward_count > 0:
                        # Проверяем - не вышли ли мы за пределы стола
                        while True:
                            x += int(self.delta_x * direction[0] * forward_count / self.pixels_in_mm[0])
                            y -= int(self.delta_y * direction[1] * forward_count / self.pixels_in_mm[1])
                            if x < 0 or y < 0 or x > self.table_controller.limits_mm[0] or y > \
                                    self.table_controller.limits_mm[1]:
                                x = all_x[-1]
                                y = all_y[-1]
                                forward_count -= 1
                                if forward_count <= 0:
                                    break
                            else:
                                break
                        if forward_count <= 0:
                            break
                        # x += int(self.delta_x * direction[0] * forward_count / self.pixels_in_mm)
                        # y -= int(self.delta_y * direction[1] * forward_count / self.pixels_in_mm)
                        all_x.append(x)
                        all_y.append(y)
                        forward_count_total += forward_count
                        snap = self.coord_move([x, y, self.table_controller.coord_mm[2]], mode="discrete", crop=True)

                        self.save_test_data('x = ' + str(x) + '; y = ' + str(y))
                    else:
                        if forward_count_total > forward_over_move:
                            all_x.pop()
                            all_y.pop()
                            x += int(self.delta_x * direction[0] * (-forward_over_move) / self.pixels_in_mm[0])
                            y -= int(self.delta_y * direction[1] * (-forward_over_move) / self.pixels_in_mm[1])
                            all_x.append(x)
                            all_y.append(y)
                            snap = self.coord_move([x, y, self.table_controller.coord_mm[2]], mode="discrete", crop=True)
                            self.save_test_data('x = ' + str(x) + '; y = ' + str(y) + ' forward correction')
                        break
                # previous_direction = direction
                direction = direction.next()
            print("all_x=" + str(all_x))
            print("all_y=" + str(all_y))
            min_x = min(all_x) + 3 * self.delta_x / self.pixels_in_mm[0]
            min_y = min(all_y) + 3 * self.delta_y / self.pixels_in_mm[1]
            max_x = max(all_x) - 3 * self.delta_x / self.pixels_in_mm[0]
            max_y = max(all_y) - 3 * self.delta_y / self.pixels_in_mm[1]

            # self.edt_border_x1.setValue(min(all_x))
            # self.edt_border_y1.setValue(min(all_y))
            # self.edt_border_x2.setValue(max(all_x))
            # self.edt_border_y2.setValue(max(all_y))
            self.edt_border_x1.setValue(min_x)
            self.edt_border_y1.setValue(min_y)
            self.edt_border_x2.setValue(max_x)
            self.edt_border_y2.setValue(max_y)
        except Exception as e:
            raise
            QMessageBox.critical(self, "Критическая ошибка", "Произошла ошибка выполнения" + str(e),
                                 QMessageBox.Ok, QMessageBox.Ok)
        finally:
            self.control_elements_enabled(True)
            QMessageBox.information(self, "Info Dialog", "Границы определены", QMessageBox.Ok, QMessageBox.Ok)
            self.vidik.work = True

    def exp_border_find(self):
        pass

    # Вспомогательная функция для определения - достигла ли камера границы при поиске в заданном направлении
    @staticmethod
    def find_border_in_image(img, direction, delta, forward_over_move=0):
        index = abs(direction[1])
        # Проверяем - не стало ли по направлению движения "чисто" (все линии)
        middle = int(img.shape[1 - index] / 2)
        if direction[index] > 0:
            middle -= 1
        coord = [0, 0]
        for i in range(5, -4, -1):
            coord[index] = middle + i * delta[index] * direction[index]
            for j in range(img.shape[index]):
                coord[1 - index] = j
                for k in range(3):
                    if img[coord[1]][coord[0]][k] < 128:
                        return i + forward_over_move
        return 0

    @staticmethod
    # Комбинированный метод, следящий за тем, чтобы граница объекта при поиске находилась в середине изображения
    # (в направлении поперек обхода)
    # Возвращает число линий, на которое смещена граница объекта от середины изображения
    def check_object_middle(img, direction, delta):
        index = abs(direction[1])
        non_white_limit = int(0.03 * img.shape[index])
        middle = int(img.shape[1 - index] / 2)
        # По-моему это смещение мида на 1 пиксель - фигня. Ниже сделал перестраховку от выхода за пределы картинки
        if direction[index] > 0:
            middle -= 1
        # Ищем пиксели объекта по цвету
        coord = [0, 0]
        # for i in range(0, 6):
        for i in range(5, -6, -1):
            coord[index] = middle + i * delta[index] * direction[index]
            if coord[index] >= img.shape[1 - index]:
                coord[index] -= img.shape[1 - index] - 1
            if coord[index] < 0:
                coord[index] = 0
            non_white_count = 0
            for j in range(img.shape[index]):
                coord[1 - index] = j
                for k in range(3):
                    if img[coord[1]][coord[0]][k] < 128:
                        non_white_count += 1
                        break
            if non_white_count > non_white_limit:
                return i
        return -5

    # Сканирование по указанным координатам
    def scan(self):
        self.vidik.work = False
        if self.unsaved:
            dlg_result = QMessageBox.question(self,
                                              "Confirm Dialog",
                                              "Данные последней съемки не сохранены. Хотите сперва их сохранить?",
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                              QMessageBox.Yes)
            if dlg_result == QMessageBox.Yes:
                if not self.save_scan():
                    return
            elif dlg_result == QMessageBox.Cancel:
                return
        try:
            coord = [float(self.edt_border_x1.value()), float(self.edt_border_y1.value()),
                     float(self.edt_border_x2.value()), float(self.edt_border_y2.value())]
        except ValueError:
            print("Неверный формат данных")
            return

        if self.table_controller.server_status == 'uninitialized':
            self.table_controller.coord_init()

        frame_size_mm = [self.frame_width_mm, self.frame_height_mm]
        count = [0, 0]
        for i in range(2):
            # Определяем на сколько мм выступает все поле съемки из целого числа кадров
            x_overage = (coord[i + 2] - coord[i]) % frame_size_mm[i]
            count[i] = int((coord[i + 2] - coord[i]) // frame_size_mm[i]) + 1
            if x_overage > 0:
                # А это - сколько надо добавить к полю съемки, чтобы получилось целое число кадров
                x_deficit = frame_size_mm[i] - x_overage
                count[i] += 1
                coord[i] -= x_deficit / 2
                coord[i + 2] += x_deficit / 2
                # Проверка выхода за пределы стола
                if coord[i] < 0:
                    coord[i + 2] -= coord[i]
                    coord[i] = 0
                if coord[i + 2] > self.table_controller.limits_mm[i]:
                    coord[i] -= coord[i + 2] - self.table_controller.limits_mm[i]
                    coord[i + 2] = self.table_controller.limits_mm[i]
                # Если изображение никак не хочет влазить в пределы стола, то надо наоборот его уменьшить...
                if coord[i] < 0:
                    coord[i] += x_overage / 2
                    coord[i + 2] -= x_overage / 2
                    count[i] -= 1

        print("x1={0}; y1={1}; x2={2}; y2={3}".format(coord[0], coord[1], coord[2], coord[3]))
        # Работа с директорией для сохранения изображений
        # shutil.rmtree(self.dir_for_img)
        if not os.path.exists(self.dir_for_img):
            os.mkdir(self.dir_for_img)
        for file in os.listdir(self.dir_for_img):
            os.remove(os.path.join(self.dir_for_img, file))
        # Получение и сохранение изображений в директорию
        left_dir = abs(self.table_controller.coord_mm[0] - coord[0]) > abs(self.table_controller.coord_mm[0] - coord[2])

        # выбираем обход изображения, исходя из того - ближе мы к его верху или низу
        j_start = 0
        j_finish = count[1]
        j_delta = 1
        if abs(self.table_controller.coord_mm[1] - coord[1]) > abs(self.table_controller.coord_mm[1] - coord[3]):
            j_start = count[1] - 1
            j_finish = -1
            j_delta = -1

        for j in range(j_start, j_finish, j_delta):
            y = coord[1] + j * self.frame_height_mm
            # В проге просмотра ось y вернута вниз
            j_r = count[1] - 1 - j
            if left_dir:
                x_range = range(count[0] - 1, -1, -1)
            else:
                x_range = range(0, count[0], 1)
            for i in x_range:
                x = coord[0] + i * self.frame_width_mm
                snap = self.coord_move([x, y, self.table_controller.coord_mm[2]], mode="discrete")
                cv2.imwrite(os.path.join(self.dir_for_img, "S_{0}_{1}.jpg".format(j_r + 1, i + 1)), snap[:, :, :])
                print('x = ' + str(x) + '; y = ' + str(y))

            left_dir = not left_dir

        # Создание файла описания XML
        root = Xml.Element("Root")
        elem_rc = Xml.Element("RowCount")
        elem_rc.text = str(count[1])
        root.append(elem_rc)
        elem_cc = Xml.Element("ColCount")
        elem_cc.text = str(count[0])
        root.append(elem_cc)
        elem_img = Xml.Element("Image")
        root.append(elem_img)
        img_format = Xml.SubElement(elem_img, "Format")
        img_format.text = "jpg"
        img_size = Xml.SubElement(elem_img, "ImgSize")
        img_size_width = Xml.SubElement(img_size, "Width")
        img_size_width.text = str(self.snap_width)
        img_size_height = Xml.SubElement(img_size, "Height")
        img_size_height.text = str(self.snap_height)
        img_con_area = Xml.SubElement(elem_img, "ConnectionArea")
        # HERE orientation param need
        ica_x = Xml.SubElement(img_con_area, "X")
        # ica_x.text = str(self.micros_controller.frame[0])
        ica_x.text = str(self.program_settings.snap_settings.frame[0])
        ica_y = Xml.SubElement(img_con_area, "Y")
        # ica_y.text = str(self.micros_controller.frame[1])
        ica_y.text = str(self.program_settings.snap_settings.frame[1])
        ica_width = Xml.SubElement(img_con_area, "Width")
        # ica_width.text = str(int(self.frame_width_mm * self.pixels_in_mm))
        ica_width.text = str(self.program_settings.snap_settings.frame[2]
                             - self.program_settings.snap_settings.frame[0])
        ica_height = Xml.SubElement(img_con_area, "Height")
        # ica_height.text = str(int(self.frame_height_mm * self.pixels_in_mm))
        ica_height.text = str(self.program_settings.snap_settings.frame[3]
                              - self.program_settings.snap_settings.frame[1])

        tree = Xml.ElementTree(root)
        with open(self.path_for_xml_file, "w"):
            tree.write(self.path_for_xml_file)
        self.btn_save_scan.setEnabled(True)
        # QMessageBox.information(self, "Info Dialog", "Сканирование завершено", QMessageBox.Ok, QMessageBox.Ok)
        self.unsaved = True
        self.vidik.work = True

        self.save_scan()

    @staticmethod
    # функция проверки, что на изображении - ничего нет
    def img_is_empty(img, delta):
        # Проверяем горизонтальные и вертикальные линии на пустоту
        coord = [0, 0]
        for index in range(2):
            non_white_limit = int(0.03 * img.shape[index])
            middle = int(img.shape[1 - index] / 2)
            for i in range(-5, 6):
                coord[index] = middle + i * delta[index]
                if i == 5:
                    coord[index] -= 1
                non_white_count = 0
                for j in range(img.shape[index]):
                    coord[1 - index] = j
                    for k in range(3):
                        if img[coord[1]][coord[0]][k] < 128:
                            non_white_count += 1
                            break
                if non_white_count > non_white_limit:
                    return False
        return True

    # Сканирование без указания координат
    def scan_without_borders(self):
        self.vidik.work = False
        files_img_count = 0
        if self.unsaved:
            dlg_result = QMessageBox.question(self,
                                              "Confirm Dialog",
                                              "Данные последней съемки не сохранены. Хотите сперва их сохранить?",
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                              QMessageBox.Yes)
            if dlg_result == QMessageBox.Yes:
                if not self.save_scan():
                    return
            elif dlg_result == QMessageBox.Cancel:
                return

        if self.table_controller.server_status == 'uninitialized':
            self.table_controller.coord_init()
            # Перевод камеры к позиции, где должна располагаться микросхема
            x = int(self.table_controller.limits_mm[0] / 2)
            y = int(self.table_controller.limits_mm[1] / 3)
            if self.test:
                y = int(self.table_controller.limits_mm[1] / 2)
                # x = int(self.table_controller.limits_mm[0] / 3) - 50
            z = self.work_height
            snap = self.coord_move([x, y, z], mode="discrete", crop=True)
        else:
            snap = self.coord_move(self.table_controller.coord_mm, mode="discrete", crop=True)

        # 1. Ищем изделие - фотаем под камерой, составляем матрицу стола, разбив пространство на кадры
        delta = [self.delta_x, self.delta_y]
        current_pos_index = []
        coordinates_x_mm = []
        x_mm = self.table_controller.coord_mm[0] % self.frame_width_mm
        current_pos_index.append(int(self.table_controller.coord_mm[0] // self.frame_width_mm))
        while x_mm < self.table_controller.limits_mm[0]:
            coordinates_x_mm.append(x_mm)
            x_mm += self.frame_width_mm

        coordinates_y_mm = []
        y_mm = self.table_controller.coord_mm[1] % self.frame_height_mm
        current_pos_index.append(int(self.table_controller.coord_mm[1] // self.frame_height_mm))
        while y_mm < self.table_controller.limits_mm[1]:
            coordinates_y_mm.append(y_mm)
            y_mm += self.frame_height_mm
        img_file_matrix = []
        img_obj_matrix = []
        for i in range(len(coordinates_x_mm)):
            new_file_x = []
            new_obj_x = []
            for j in range(len(coordinates_y_mm)):
                new_file_x.append('')
                new_obj_x.append(False)
            img_file_matrix.append(new_file_x)
            img_obj_matrix.append(new_obj_x)

        # Если кадр пуст, то идем несколько шагов вверх до непустого кадра
        # Число кадров поиска от стартовой позиции
        check_range = 3

        img_empty = self.img_is_empty(snap, delta)
        # Если не найдено изделие, то идем вниз от центра, потом ищем справа и слева
        offset = [0, 0]
        index = 1
        if (current_pos_index[0] - check_range >= 0 and current_pos_index[1] - check_range >= 0
            and current_pos_index[0] + check_range < len(coordinates_x_mm)
                and current_pos_index[1] + check_range < len(coordinates_y_mm)):

            while img_empty:
                if offset[index] < check_range:
                    offset[index] += 1
                else:
                    if offset[1 - index] == 0:
                        offset[1 - index] -= check_range
                    else:
                        offset[index] -= check_range
                        index = 1 - index
                if index == 1 and offset[0] == 0 and offset[1] == 0:
                    break
                x = coordinates_x_mm[current_pos_index[0] + offset[0]]
                y = coordinates_y_mm[current_pos_index[1] + offset[1]]
                z = self.table_controller.coord_mm[2]
                snap = self.coord_move([x, y, z], mode="discrete", crop=True)
                if not self.img_is_empty(snap, delta):
                    img_empty = False

        self.save_test_data("img_empty=" + str(img_empty))
        self.save_test_data("offset=" + str(offset))
        if img_empty:
            QMessageBox.warning(self, "Внимание!", "Изделие не найдено!", QMessageBox.Ok, QMessageBox.Ok)
            return

        current_pos_index[0] += offset[0]
        current_pos_index[1] += offset[1]

        if not os.path.exists(self.dir_for_img):
            os.mkdir(self.dir_for_img)
        for file in os.listdir(self.dir_for_img):
            os.remove(os.path.join(self.dir_for_img, file))
        file_name = os.path.join(self.dir_for_img, "scan_{0}.jpg".format(files_img_count))
        cv2.imwrite(file_name, snap)
        # self.save_test_data("file={0}, x={1}, y={2}".format(file_name, current_pos_index[0], current_pos_index[1]))
        img_file_matrix[current_pos_index[0]][current_pos_index[1]] = file_name
        img_obj_matrix[current_pos_index[0]][current_pos_index[1]] = True
        files_img_count += 1
        # 2. Как только найден первый кадр с изделием - идем вверх и фотаем до получения пустого кадра
        # Введем еще предельные значения индексов съемки - все-таки мы снимаем прямоугольную область
        # snap_area_rect = QRect(current_pos_index[0], current_pos_index[1], 1, 1)
        snap_area_limits_x = [current_pos_index[0], current_pos_index[0]]
        snap_area_limits_y = [current_pos_index[1], current_pos_index[1]]
        # direction_y определяет направление съемки вверх или вниз по y, direction_x - по x:  -1 или 1
        direction_y = -1
        start_x_pos_index = current_pos_index[0]
        empty_column = False
        # Цикл направлений по x
        for direction_x in [-1, 1]:
            self.save_test_data("direction_x={0}".format(direction_x))
            dir_index_x = direction_x - int((direction_x - 1) / 2)
            current_pos_index[0] = start_x_pos_index + dir_index_x
            # Цикл шагов по x
            while (dir_index_x == 0 and current_pos_index[0] >= 0) \
                    or (dir_index_x == 1 and current_pos_index[0] <= len(coordinates_x_mm) - 1):
                empty_column = True
                # Цикл направлений по y
                for direction_y in [direction_y, -direction_y]:
                    # Просто преобразую так -1 в 0, а 1 в 1
                    self.save_test_data("direction_y={0}".format(direction_y))
                    dir_index_y = direction_y - int((direction_y - 1) / 2)
                    # current_pos_index[1] = snap_area_limits_y[dir_index_y]
                    # Цикл шагов по y
                    while (dir_index_y == 0 and current_pos_index[1] >= 0) \
                            or (dir_index_y == 1 and current_pos_index[1] <= len(coordinates_y_mm) - 1):

                        if not img_file_matrix[current_pos_index[0]][current_pos_index[1]]:
                            snap = self.coord_move([coordinates_x_mm[current_pos_index[0]],
                                                    coordinates_y_mm[current_pos_index[1]],
                                                    self.table_controller.coord_mm[2]],
                                                   mode="discrete", crop=True)
                            file_name = os.path.join(self.dir_for_img, "scan_{0}.jpg".format(files_img_count))
                            cv2.imwrite(file_name, snap)
                            # self.save_test_data(
                            # "file={0}, x={1}, y={2}".format(file_name, current_pos_index[0], current_pos_index[1]))
                            img_file_matrix[current_pos_index[0]][current_pos_index[1]] = file_name
                            files_img_count += 1
                            img_is_empty = self.img_is_empty(snap, delta)
                            self.save_test_data("snap: x={0}, y={1}. empty={2}"
                                                .format(current_pos_index[0], current_pos_index[1], img_is_empty))
                        else:
                            img_is_empty = not img_obj_matrix[current_pos_index[0]][current_pos_index[1]]
                            self.save_test_data("move: x={0}, y={1}. empty={2}"
                                                .format(current_pos_index[0], current_pos_index[1], img_is_empty))
                        if img_is_empty:
                            if snap_area_limits_y[dir_index_y] + direction_y == current_pos_index[1]:
                                break
                        else:
                            if current_pos_index[1] * direction_y > snap_area_limits_y[dir_index_y] * direction_y:
                                snap_area_limits_y[dir_index_y] = current_pos_index[1]
                                self.save_test_data("limit Y[{0}]={1}".format(dir_index_y, snap_area_limits_y[dir_index_y]))
                            img_obj_matrix[current_pos_index[0]][current_pos_index[1]] = True
                            empty_column = False

                        current_pos_index[1] += direction_y
                if empty_column:
                    # current_pos_index[0] -= direction_x
                    break
                else:
                    if current_pos_index[0] * direction_x > snap_area_limits_x[dir_index_x] * direction_x:
                        snap_area_limits_x[dir_index_x] = current_pos_index[0]
                        self.save_test_data("limit X[{0}]={1}".format(dir_index_x, snap_area_limits_x[dir_index_x]))
                current_pos_index[0] += direction_x
        # Тут блок "добивания" картинок, которые не засняли в предыдущем блоке из-за недооценки габаритов
        while True:
            count_missed = 0
            closest_cell = [0, 0]
            closest_dist = 1000000
            for i in range(snap_area_limits_x[0], snap_area_limits_x[1] + 1):
                for j in range(snap_area_limits_y[0], snap_area_limits_y[1] + 1):
                    if not img_file_matrix[i][j]:
                        count_missed += 1
                        dist = (abs(i - current_pos_index[0]) * self.frame_width_mm
                                + abs(j - current_pos_index[1]) * self.frame_height_mm)
                        if dist < closest_dist:
                            closest_dist = dist
                            closest_cell = [i, j]

            if count_missed == 0:
                break
            else:
                delta_x = 0
                delta_y = 0
                if closest_cell[1] > snap_area_limits_y[0] \
                        and not img_file_matrix[closest_cell[0]][closest_cell[1] - 1]:
                    delta_y = -1
                elif closest_cell[1] < snap_area_limits_y[1] \
                        and not img_file_matrix[closest_cell[0]][closest_cell[1] + 1]:
                    delta_y = +1
                elif closest_cell[0] > snap_area_limits_x[0] \
                        and not img_file_matrix[closest_cell[0] - 1][closest_cell[1]]:
                    delta_x = -1
                elif closest_cell[0] < snap_area_limits_x[1] \
                        and not img_file_matrix[closest_cell[0] + 1][closest_cell[1]]:
                    delta_x = +1

                while True:
                    current_pos_index[0] = closest_cell[0]
                    current_pos_index[1] = closest_cell[1]
                    snap = self.coord_move([coordinates_x_mm[current_pos_index[0]],
                                            coordinates_y_mm[current_pos_index[1]],
                                            self.table_controller.coord_mm[2]],
                                           mode="discrete", crop=True)
                    file_name = os.path.join(self.dir_for_img, "scan_{0}.jpg".format(files_img_count))
                    cv2.imwrite(file_name, snap)
                    # self.save_test_data(
                    #     "file={0}, x={1}, y={2}".format(file_name, current_pos_index[0], current_pos_index[1]))
                    img_file_matrix[current_pos_index[0]][current_pos_index[1]] = file_name
                    files_img_count += 1
                    img_is_empty = self.img_is_empty(snap, delta)
                    self.save_test_data("snap+: x={0}, y={1}. empty={2}"
                                        .format(current_pos_index[0], current_pos_index[1], img_is_empty))
                    closest_cell[0] += delta_x
                    closest_cell[1] += delta_y
                    if closest_cell[0] < snap_area_limits_x[0] or closest_cell[0] > snap_area_limits_x[1] \
                            or closest_cell[1] < snap_area_limits_y[0] or closest_cell[1] > snap_area_limits_y[1]:
                        break
                    if img_file_matrix[closest_cell[0]][closest_cell[1]]:
                        break

        # Теперь надо переименовать нужные файлы и удалить все лишние
        for i in range(snap_area_limits_x[0], snap_area_limits_x[1] + 1):
            for j in range(snap_area_limits_y[0], snap_area_limits_y[1] + 1):
                j_r = snap_area_limits_y[1] - j
                os.rename(img_file_matrix[i][j], os.path.join(self.dir_for_img,
                                                              "S_{0}_{1}.jpg".format(j_r + 1,
                                                                                     i - snap_area_limits_x[0] + 1)))

        if not os.path.exists(self.dir_for_img):
            os.mkdir(self.dir_for_img)
        for file in os.listdir(self.dir_for_img):
            if file.find('scan') == 0:
                os.remove(os.path.join(self.dir_for_img, file))
            # cv2.imwrite(os.path.join(self.dir_for_img, "S_{0}_{1}.jpg".format(j_r + 1, i + 1)), snap[:, :, :])
            # print('x = ' + str(x) + '; y = ' + str(y))
        # Создание файла описания XML
        root = Xml.Element("Root")
        elem_rc = Xml.Element("RowCount")
        elem_rc.text = str(snap_area_limits_y[1] - snap_area_limits_y[0] + 1)
        root.append(elem_rc)
        elem_cc = Xml.Element("ColCount")
        elem_cc.text = str(snap_area_limits_x[1] - snap_area_limits_x[0] + 1)
        root.append(elem_cc)
        elem_img = Xml.Element("Image")
        root.append(elem_img)
        img_format = Xml.SubElement(elem_img, "Format")
        img_format.text = "jpg"
        img_size = Xml.SubElement(elem_img, "ImgSize")
        img_size_width = Xml.SubElement(img_size, "Width")
        # img_size_width.text = str(self.snap_width)
        img_size_width.text = str(self.program_settings.snap_settings.frame[2]
                                  - self.program_settings.snap_settings.frame[0])
        img_size_height = Xml.SubElement(img_size, "Height")
        # img_size_height.text = str(self.snap_height)
        img_size_height.text = str(self.program_settings.snap_settings.frame[3]
                                   - self.program_settings.snap_settings.frame[1])
        img_con_area = Xml.SubElement(elem_img, "ConnectionArea")
        # HERE orientation param need
        ica_x = Xml.SubElement(img_con_area, "X")
        # ica_x.text = str(self.program_settings.snap_settings.frame[0])
        ica_x.text = "0"
        ica_y = Xml.SubElement(img_con_area, "Y")
        # ica_y.text = str(self.program_settings.snap_settings.frame[1])
        ica_y.text = "0"
        ica_width = Xml.SubElement(img_con_area, "Width")
        ica_width.text = str(self.program_settings.snap_settings.frame[2]
                             - self.program_settings.snap_settings.frame[0])
        ica_height = Xml.SubElement(img_con_area, "Height")
        ica_height.text = str(self.program_settings.snap_settings.frame[3]
                              - self.program_settings.snap_settings.frame[1])

        tree = Xml.ElementTree(root)
        with open(self.path_for_xml_file, "w"):
            tree.write(self.path_for_xml_file)
        self.btn_save_scan.setEnabled(True)
        # QMessageBox.information(self, "Info Dialog", "Сканирование завершено", QMessageBox.Ok, QMessageBox.Ok)
        self.unsaved = True
        self.vidik.work = True
        self.save_scan()

    # Сохранение изображений в архивный файл
    def save_scan(self):
        if not os.path.exists(self.path_for_xml_file):
            return False
        file_filter = "Microscope scans (*.misc)"
        a = QFileDialog.getSaveFileName(self, "Выберите место сохранения файла", "/",
                                        "All files (*.*);;Microscope scans (*.misc)", file_filter)
        file_name = a[0]
        if len(file_name) > 0:
            ext = os.path.splitext(file_name)
            if ext[1] == ".misc":
                file_name = file_name
            else:
                file_name = ext[0] + ".misc"
            if os.path.exists(file_name):
                dlg_result = QMessageBox.question(self, "Confirm Dialog",
                                                  "Файл уже существует. " +
                                                  "Хотите его перезаписать?" +
                                                  " Это удалит данные в нем",
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if dlg_result == QMessageBox.No:
                    return False
        else:
            return False

        self.vidik.work = False
        z = zipfile.ZipFile(file_name, 'w')
        for root, dirs, files in os.walk(self.dir_for_img):
            for file in files:
                if file:
                    z.write(os.path.join(self.dir_for_img, file), file, compress_type=zipfile.ZIP_DEFLATED)
        z.close()
        QMessageBox.information(self, "Info Dialog", "Файл сохранен", QMessageBox.Ok, QMessageBox.Ok)
        self.unsaved = False

        self.main_window.open_file(file_name)
        self.vidik.work = True
        return True

    # Обработчики событий формы и ее компонентов
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            # print("Press " + str(event.key()))
            if event.key() == Qt.Key_Shift:
                self.key_shift_pressed = True
            elif event.key() in self.keyboard_buttons:
                self.keyboard_buttons[event.key()].key_press()
        elif event.type() == QEvent.KeyRelease:
            # print("Release " + str(event.key()))
            if event.key() in self.keyboard_buttons:
                self.keyboard_buttons[event.key()].key_release()
            elif event.key() == Qt.Key_Shift:
                self.key_shift_pressed = False
        return QMainWindow.eventFilter(self, obj, event)

    # def keyPressEvent(self, event):
    #     print(event.key())

    def continuous_move(self):
        # print("continuous start")
        # while True:
        # if self.continuous_mode:
        # someone_clicked = False
        steps_count = 24
        if self.key_shift_pressed:
            steps_count = 8
        if self.keyboard_buttons[Qt.Key_W].check_click():
            self.coord_move([0, steps_count, 0], mode="continuous")
            # someone_clicked = True
        if self.keyboard_buttons[Qt.Key_D].check_click():
            self.coord_move([steps_count, 0, 0], mode="continuous")
            # someone_clicked = True
        if self.keyboard_buttons[Qt.Key_S].check_click():
            self.coord_move([0, -steps_count, 0], mode="continuous")
            # someone_clicked = True
        if self.keyboard_buttons[Qt.Key_A].check_click():
            self.coord_move([-steps_count, 0, 0], mode="continuous")
            # someone_clicked = True
        if self.keyboard_buttons[Qt.Key_Plus].check_click():
            self.coord_move([0, 0, steps_count], mode="continuous")
            # someone_clicked = True
        if self.keyboard_buttons[Qt.Key_Minus].check_click():
            self.coord_move([0, 0, -steps_count], mode="continuous")

            # someone_clicked = True
        # if someone_clicked:
        time.sleep(0.01)
        # i += 1
        # print("continuous " + str(i))
        # else:
        #     time.sleep(1)
        # print("continuous finish")

    # def video_thread(self):
    #     while True:
    #         self.micros_controller.video_check, self.micros_controller.video_img \
    #             = self.micros_controller.video_stream.read()
    #         self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(self.micros_controller.video_img))
    #         self.lbl_img.repaint()


# class LabelImg(QLabel):
#     def __init__(self):
#         super().__init__()
#         self.can_set = True
#
#     def setPixmapMy(self, a0: QtGui.QPixmap) -> None:
#         if self.can_set:
#             self.setPixmap(a0)


# Класс направления - умеет выдавать следующее и предыдущее направление
class Direction:
    def __init__(self, index=0, direction=None):
        self.__abs_index = index
        if not direction:
            self.__direction = [1, 0]
        else:
            self.__direction = direction

    def __getitem__(self, key):
        return self.__direction[key]

    def __repr__(self):
        return str(self.__abs_index) + str(self.__direction)

    def __get_abs_index(self):
        return self.__abs_index
    abs_index = property(__get_abs_index)

    # @property
    # def abs_index(self):
    #     return self.__abs_index

    def previous(self):
        return Direction(self.__abs_index - 1, [self.__direction[1], -self.__direction[0]])

    def next(self):
        return Direction(self.__abs_index + 1, [-self.__direction[1], self.__direction[0]])


# Класс-помощник для отслеживания ручного управления установкой клавишами
class KeyboardButton:
    def __init__(self):
        # Считается ли, что сейчас кнопка нажата (и необходимо выполнять движение установки)
        self.clicked = False
        # Последний полученный сигнал от кнопки был release? Если нет, то последний сигнал был press
        self.released = True
        # Время получения последнего сигнала release
        self.time_released = 0.0

    # Получен сигнал нажатия
    def key_press(self):
        self.clicked = True
        self.released = False
        # print(self.clicked)

    # Получен сигнал отпуска
    def key_release(self):
        self.released = True
        self.time_released = time.time()
        # print(self.clicked)

    # Проверка - нажата ли кнопка и обработка таймера
    def check_click(self):
        if self.clicked:
            if self.released:
                #
                if time.time() - self.time_released > 0.02:
                    self.clicked = False
            else:
                # Слишком длительное отсутствие сигнала press воспринимается, как необходимость остановки
                if time.time() - self.time_released > 1.00:
                    self.clicked = False

        # print(self.clicked)
        return self.clicked


class TableServerThread(QThread):
    def __init__(self, hostname, parent=None):
        self.hostname = hostname
        self.work = True
        self.stopped = False
        QThread.__init__(self, parent=parent)

    def run(self) -> None:
        shell = Terminal(["ssh pi@" + self.hostname, "python3 server.py", ])
        shell.run()
        while self.work:
            time.sleep(1)
        shell = None
        self.stopped = True
        # subprocess.run(["ssh", "-tt", "pi@" + self.hostname])
        # subprocess.run(["python3", "server.py"])


class VideoStreamThread(QThread):
    changePixmap = pyqtSignal(QPixmap)

    def __init__(self, video_stream, video_img, parent=None):
        self.video_stream = video_stream
        self.video_img = video_img
        self.work = True
        QThread.__init__(self, parent=parent)

    def run(self):
        while True:
            if self.work:
                ret, self.video_img = self.video_stream.read()
                if ret:
                    self.changePixmap.emit(self.numpy_to_pixmap(self.video_img))
                    time.sleep(0.02)
                    # self.lbl.repaint()
            else:
                time.sleep(0.1)

    @staticmethod
    def numpy_to_q_image(image):
        q_img = QImage()
        if image.dtype == np.uint8:
            if len(image.shape) == 2:
                channels = 1
                height, width = image.shape
                bytes_per_line = channels * width
                q_img = QImage(
                    image.data, width, height, bytes_per_line, QImage.Format_Indexed8
                )
                q_img.setColorTable([QtGui.qRgb(i, i, i) for i in range(256)])
            elif len(image.shape) == 3:
                if image.shape[2] == 3:
                    height, width, channels = image.shape
                    bytes_per_line = channels * width
                    q_img = QImage(
                        # image.data, width, height, bytes_per_line, QImage.Format_RGB888
                        image.data, width, height, bytes_per_line, QImage.Format_BGR888
                    )
                elif image.shape[2] == 4:
                    height, width, channels = image.shape
                    bytes_per_line = channels * width
                    # fmt = QImage.Format_ARGB32
                    q_img = QImage(
                        # image.data, width, height, bytes_per_line, QImage.Format_ARGB32
                        image.data, width, height, bytes_per_line, QImage.Format_BGR888
                    )
        return q_img

    @staticmethod
    def numpy_to_pixmap(img):
        q_img = VideoStreamThread.numpy_to_q_image(img)
        pixmap = QPixmap.fromImage(q_img)
        return pixmap


# Класс управления микроскопом (пока тестовая подделка)
# class MicrosController:
#     def __init__(self, program_settings: ProgramSettings, test: bool, lbl_img: QLabel):
#         # vst = VideoStreamThread(self)
#         # vst.start()
#
#         if test:
#             self.test_img_path = "/home/andrey/Projects/MicrosController/TEST/MotherBoard_3.jpg"
#             # self.test_img_path = "/home/andrey/Projects/MicrosController/TEST/MotherBoard_2.jpg"
#             # self.test_img_path = "/home/andrey/Projects/MicrosController/TEST/MotherBoard_5.jpg"
#             self.test_img = cv2.imread(self.test_img_path)[:, :, :]
#         self.test = test
#         # self.frame = list()
#         self.program_settings: ProgramSettings = program_settings
#         self.video_img = None
#         self.video_check = False
#         self.lbl_img = lbl_img
#
#         if not self.test:
#             max_video_streams = 6
#             video_stream_index = -1
#             # vs = VideoStream(src=video_stream_index).start()
#             check_next_stream = True
#             while check_next_stream:
#                 video_stream_index += 1
#                 if video_stream_index > max_video_streams:
#                     time.sleep(1.0)
#                     video_stream_index = 0
#
#                 # self.video_stream = VideoStream(src=video_stream_index).start()
#                 # self.video_stream = VideoStream(src=video_stream_index, usePiCamera=True,
#                 #                                 resolution=(1920, 1080)).start()
#                 self.video_stream = cv2.VideoCapture(video_stream_index)
#                 self.video_stream.set(3, 1920)
#                 self.video_stream.set(4, 1080)
#
#                 # noinspection PyBroadException
#                 try:
#                     self.video_check, self.video_img = self.video_stream.read()
#                     if not self.video_check:
#                         continue
#                     # check_frame = img[:, :, :]
#                     check_next_stream = False
#                 except Exception:
#                     # self.video_stream.stop()
#                     check_next_stream = True

    #         self.video_fps = 60
    #         self.video_timer = QTimer()
    #         self.video_timer.timeout.connect(self.next_video_frame)
    #         self.video_timer.start(1000. / self.video_fps)
    #
    # def next_video_frame(self):
    #     self.video_check, self.video_img = self.video_stream.read()
    #     self.lbl_img.setPixmap(self.numpy_to_pixmap(self.video_img))

    # def __get_frame(self):
    #     return self.program_settings.snap_settings.frame
    # frame = property(__get_frame)

    # @staticmethod
    # def numpy_to_q_image(image):
    #     q_img = QImage()
    #     if image.dtype == np.uint8:
    #         if len(image.shape) == 2:
    #             channels = 1
    #             height, width = image.shape
    #             bytes_per_line = channels * width
    #             q_img = QImage(
    #                 image.data, width, height, bytes_per_line, QImage.Format_Indexed8
    #             )
    #             q_img.setColorTable([QtGui.qRgb(i, i, i) for i in range(256)])
    #         elif len(image.shape) == 3:
    #             if image.shape[2] == 3:
    #                 height, width, channels = image.shape
    #                 bytes_per_line = channels * width
    #                 q_img = QImage(
    #                     # image.data, width, height, bytes_per_line, QImage.Format_RGB888
    #                     image.data, width, height, bytes_per_line, QImage.Format_BGR888
    #                 )
    #             elif image.shape[2] == 4:
    #                 height, width, channels = image.shape
    #                 bytes_per_line = channels * width
    #                 # fmt = QImage.Format_ARGB32
    #                 q_img = QImage(
    #                     # image.data, width, height, bytes_per_line, QImage.Format_ARGB32
    #                     image.data, width, height, bytes_per_line, QImage.Format_BGR888
    #                 )
    #     return q_img
    #
    # def numpy_to_pixmap(self, img):
    #     q_img = self.numpy_to_q_image(img)
    #     pixmap = QPixmap.fromImage(q_img)
    #     return pixmap

    # def snap(self, x1: int, y1: int, x2: int, y2: int, crop=False):
    #     if self.test:
    #         time.sleep(0.3)
    #         # return np.copy(self.test_img[y1:y2, x1:x2, :])
    #         # Переворачиваем координаты съемки
    #         y2_r = 6400 - y1
    #         y1_r = 6400 - y2
    #         return np.copy(self.test_img[y1_r:y2_r, x1:x2, :])
    #     else:
    #         self.video_timer.stop()
    #         time.sleep(0.1)
    #         # for i in range(10):
    #         #     self.video_stream.read()
    #         # Прогревочные съемки
    #         for i in range(10):
    #             self.video_stream.read()
    #         check, img = self.video_stream.read()
    #         self.video_timer.start()
    #         if crop:
    #             # return np.copy(img[self.frame[3]-1:self.frame[1]:-1, self.frame[2]-1:self.frame[0]:-1, :])
    #             # return np.copy(img[self.frame[1]:self.frame[3], self.frame[0]:self.frame[2], :][::-1, ::-1, :])
    #             return np.copy(img[self.frame[1]:self.frame[3], self.frame[0]:self.frame[2], :])
    #         else:
    #             # return np.copy(img[::-1, ::-1, :])
    #             return np.copy(img)


# Класс, который общается с контроллером станка
# 1. Проверяет наличие сервера
# 2. Запускает сервер на Raspberry pi
# 3. Управляет движениями станка
class TableController:
    def __init__(self, loop, program_settings: ProgramSettings, vidik: VideoStreamThread, test=False,
                 hostname="192.168.42.100", port=8080):
        self.program_settings = program_settings
        self.vidik = vidik
        # Параметры подключения к серверу raspberry pi
        self.hostname = hostname
        self.port = port
        # Текущий статус севрера
        self.server_status = 'uninitialized'
        # Текущий статус станка: работает или нет
        self.operation_status = ''
        self.coord_step = [-1, -1, -1]
        self.coord_mm = [-1.0, -1.0, -1.0]
        self.manual_mode = True
        self.manual_left_count = 0
        self.manual_right_count = 0
        self.loop = loop
        self.execute = False
        # self.thread_server = Thread(target=self.server_start)

        self.thread_server = TableServerThread(self.hostname)

        # self.thread_server = QThread()
        # self.thread_server.started.connect(self.server_start)
        # self.steps_in_mm = 80
        # self.limits_step = []
        # self.limits_mm = []
        # self.steps_in_mm = 80
        # self.limits_step = (340 * self.steps_in_mm, 640 * self.steps_in_mm, 70 * self.steps_in_mm)
        # Режим тестирования - без работы с установкой
        self.test = test
        # self.micros_controller: MicrosController = None
        # self.programSettings: ProgramSettings = None

    def __repr__(self):
        # return "coord = " + str(self.coord_mm) + "; server status = " + self.server_status \
        #        + "; last op status = " + self.operation_status
        return "coord = [{0:.2f}, {1:.2f}, {2:.2f}]; server status = {3}; last op status = {4}".format(
            self.coord_mm[0], self.coord_mm[1], self.coord_mm[2], self.server_status, self.operation_status
        )

    def __get_steps_in_mm(self):
        return self.program_settings.table_settings.steps_in_mm
    steps_in_mm = property(__get_steps_in_mm)

    def __get_limits_step(self):
        return self.program_settings.table_settings.limits_step
    limits_step = property(__get_limits_step)

    def __get_limits_mm(self):
        return self.program_settings.table_settings.limits_mm
    limits_mm = property(__get_limits_mm)

    async def consumer(self):
        url = f"ws://{self.hostname}:{self.port}"
        async with websockets.connect(url) as web_socket:
            await self.hello(web_socket)

    @staticmethod
    async def hello(web_socket) -> None:
        async for message in web_socket:
            print(message)

    @staticmethod
    async def produce(message: str, host: str, port: int) -> None:
        async with websockets.connect(f"ws://{host}:{port}")as ws:
            await ws.send(message)
            result = await ws.recv()
            return result

    def get_request(self, x_step: int, y_step: int, z_step: int, mode: str):
        self.execute = True
        # self.vidik.work = False
        data = {
            "x": -x_step,
            "y": y_step,
            "z": z_step,
            "mode": mode  # continuous/discrete/init/check
        }
        data_string = json.dumps(data)
        return data_string

    def result_unpack(self, result):
        result_str = json.loads(result)
        # Переворот по оси Х
        self.coord_step = [self.limits_step[0] - result_str['x'], result_str['y'], result_str['z']]
        self.coord_mm = [(self.coord_step[0] / self.steps_in_mm),
                         (self.coord_step[1] / self.steps_in_mm),
                         (self.coord_step[2] / self.steps_in_mm)]

        self.operation_status = result_str['status']
        self.server_status = result_str['status']
        self.execute = False
        # self.vidik.work = True
    # def coord_init(self):
    #     init_thread = Thread(target=self.coord_init_in_thread)
    #     init_thread.start()

    def coord_init(self):
        if not self.test:
            data = self.get_request(x_step=0, y_step=0, z_step=0, mode="init")
            result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
            self.result_unpack(result)
        else:
            self.coord_step = [self.limits_step[0], 0, 0]
            self.coord_mm = [self.limits_mm[0], 0, 0]
            self.operation_status = 'init'
            self.server_status = 'init'

    def coord_check(self):
        if not self.test:
            # loop = asyncio.get_event_loop()
            data = self.get_request(x_step=0, y_step=0, z_step=0, mode="check")
            result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
            self.result_unpack(result)

    # Команда движения установки
    def coord_move(self, coord, mode="discrete"):
        if not self.test:
            if min(self.coord_step) < 0:
                return
            # В режиме точечного перемещения надо передавать миллиметры
            if mode == "discrete":
                dx = coord[0] * self.steps_in_mm - self.coord_step[0]
                dy = coord[1] * self.steps_in_mm - self.coord_step[1]
                dz = coord[2] * self.steps_in_mm - self.coord_step[2]
            # В режиме непрерывного перемещения надо передавать шаги
            else:
                # if mode == "continuous"
                dx = coord[0]
                dy = coord[1]
                dz = coord[2]
            # loop = asyncio.get_event_loop()
            data = self.get_request(x_step=int(dx), y_step=int(dy), z_step=int(dz), mode=mode)
            result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
            self.result_unpack(result)
        else:
            if mode == "discrete":
                self.coord_mm[0] = coord[0]
                self.coord_mm[1] = coord[1]
                self.coord_mm[2] = coord[2]
                self.coord_step[0] = int(self.coord_mm[0] * self.steps_in_mm)
                self.coord_step[1] = int(self.coord_mm[1] * self.steps_in_mm)
                self.coord_step[2] = int(self.coord_mm[2] * self.steps_in_mm)
            else:
                # if mode == "continuous"
                coord[0] = -coord[0]
                for i in range(3):
                    self.coord_step[i] += coord[i]
                    if self.coord_step[i] < 0:
                        self.coord_step[i] = 0
                    if self.coord_step[i] > self.limits_step[i]:
                        self.coord_step[i] = self.limits_step[i]
                    self.coord_mm[i] = self.coord_step[i] / self.steps_in_mm

                # snap = self.micros_controller.snap(self.programSettings.pixels_in_mm * (self.coord_mm[0] -
        #                                                                         self.programSettings.snap_width_half),
        #                                    self.programSettings.pixels_in_mm * (self.coord_mm[1] -
        #                                                                         self.programSettings.snap_height_half),
        #                                    self.programSettings.pixels_in_mm * (self.coord_mm[0] +
        #                                                                         self.programSettings.snap_width_half),
        #                                    self.programSettings.pixels_in_mm * (self.coord_mm[1] +
        #                                                                         self.programSettings.snap_height_half))

        # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
        # self.lbl_img.repaint()
        self.operation_status = 'init'
        self.server_status = 'init'

    def server_check(self):
        pass

    def server_start(self):
        # os.system("python3 /home/andrey/Projects/MicrosController/ServerExamples/server.py")
        # shell = Terminal(["python3 /home/andrey/Projects/MicrosController/ServerExamples/server.py"])

        shell = Terminal(["ssh pi@" + self.hostname, "python3 server.py", ])
        shell.run()

    def server_connect(self):
        pass

    # def init(self):
    #     return self.send_json_request("init request")

    # # функция отправки json для управления станком
    # @staticmethod
    # def send_json_request(json_request):
    #     answer = "ok"
    #     return answer


# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = ScanWindow()
#     sys.exit(app.exec_())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
