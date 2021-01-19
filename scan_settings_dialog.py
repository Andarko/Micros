from PyQt5.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QInputDialog, \
    QLineEdit, QMessageBox, QFormLayout, QDoubleSpinBox, QSpinBox, QAbstractSpinBox, QDialogButtonBox
from PyQt5.QtCore import Qt, QSize, QRect
import xml.etree.ElementTree as Xml


# Класс для хранения всех настроек камер. Он может загружаться из файла и сохраняться в файл
from lxml import etree


class AllSettings(object):
    def __init__(self):
        # Список микроскопов и доступных разрешений
        self.micros_settings = dict()


# Классы для хранения текущих выбранных настроек
# Выбранные настройки микроскопа
class MicrosSettings(object):
    def __init__(self, name=""):
        self.name = name
        self.resolution = QSize()
        self.all_snap_settings = list()


# Выбранные настройки снимка (калибровка)
class SnapSettings(object):
    def __init__(self, name=""):
        self.name = name
        self.pixels_in_mm = 10.0
        self.snap_width = 200
        self.snap_height = 100
        self.offset = [0, 0, 0, 0]
        self.frame = [0, 0, 200, 100]
        self.work_height = 50


# Текущие настройки стола
class TableSettings(object):
    def __init__(self):
        self.steps_in_mm = 80
        self.limits_mm = [340, 640, 70]
        # self.limits_step = 80 * self.limits_mm


# Настройки программы, из которых
class ProgramSettings(object):
    def __init__(self, test=False):
        self.all_micros_settings = list()
        self.micros_settings = MicrosSettings()
        self.snap_settings = SnapSettings()
        self.table_settings = TableSettings()
        self.test = test
        # if not test:
        self.load_settings_from_xml("scan_settings.xml")

    def load_settings_from_xml(self, file_name, test=False):
        with open(file_name) as fileObj:
            xml = fileObj.read()
        root = etree.fromstring(xml)

        for element_main in root.getchildren():
            if element_main.tag == "Table":
                for element_table in element_main.getchildren():
                    if element_table.tag == "StepsInMM":
                        self.table_settings.steps_in_mm = int(element_table.text)
                    elif element_table.tag == "LimitsMM":
                        for el_limit in element_table.getchildren():
                            if el_limit.tag == "X":
                                self.table_settings.limits_mm[0] = int(el_limit.text)
                            elif el_limit.tag == "Y":
                                self.table_settings.limits_mm[1] = int(el_limit.text)
                            elif el_limit.tag == "Z":
                                self.table_settings.limits_mm[2] = int(el_limit.text)

            elif element_main.tag == "AllMicros":
                for element_all in element_main.getchildren():
                    if element_all.tag == "Micros":
                        new_micros_settings = MicrosSettings(element_all.get('name'))
                        self.all_micros_settings.append(new_micros_settings)
                        micros_settings_used = False
                        for element_micros in element_all.getchildren():
                            if element_micros.tag == "Default":
                                if (not self.test and element_micros.text == "True") \
                                        or (self.test and element_micros.text == "Test"):
                                    micros_settings_used = True
                                    self.micros_settings = new_micros_settings

                            elif element_micros.tag == "Resolution":
                                for element_resolution in element_micros.getchildren():
                                    if element_resolution.tag == "Width":
                                        new_micros_settings.resolution.setWidth(int(element_resolution.text))
                                    elif element_resolution.tag == "Height":
                                        new_micros_settings.resolution.setHeight(int(element_resolution.text))
                            elif element_micros.tag == "Mode":
                                new_snap_settings = SnapSettings(element_micros.get('name'))
                                new_micros_settings.all_snap_settings.append(new_snap_settings)
                                new_snap_settings.snap_width = new_micros_settings.resolution.width()
                                new_snap_settings.snap_height = new_micros_settings.resolution.height()
                                for element_mode in element_micros.getchildren():
                                    if element_mode.tag == "Default":
                                        if micros_settings_used and element_mode.text == "True":
                                            self.snap_settings = new_snap_settings
                                    elif element_mode.tag == "Offset":
                                        for element_offset in element_mode.getchildren():
                                            if element_offset.tag == "Left":
                                                new_snap_settings.offset[0] = int(element_offset.text)
                                            elif element_offset.tag == "Top":
                                                new_snap_settings.offset[1] = int(element_offset.text)
                                            elif element_offset.tag == "Right":
                                                new_snap_settings.offset[2] = int(element_offset.text)
                                            elif element_offset.tag == "Bottom":
                                                new_snap_settings.offset[3] = int(element_offset.text)
                                    elif element_mode.tag == "PixelsInMM":
                                        new_snap_settings.pixels_in_mm = float(element_mode.text)
                                    elif element_mode.tag == "WorkHeightMM":
                                        new_snap_settings.work_height = float(element_mode.text)
                                    elif element_mode.tag == "Focus":
                                        pass
                                    elif element_mode.tag == "Zoom":
                                        pass
                                new_snap_settings.frame[0] = new_snap_settings.offset[0]
                                new_snap_settings.frame[1] = new_snap_settings.offset[1]
                                new_snap_settings.frame[2] = new_snap_settings.snap_width - new_snap_settings.offset[2]
                                new_snap_settings.frame[3] = new_snap_settings.snap_height - new_snap_settings.offset[3]
        pass


class SettingsDialog(QDialog):
    def __init__(self, program_settings: ProgramSettings):
        super().__init__()
        # self.all_micros_settings = list()
        self.program_settings = program_settings
        self.combo_micros = QComboBox()
        self.combo_modes = QComboBox()
        self.edt_res_width = QSpinBox()
        self.edt_res_height = QSpinBox()
        self.edt_offset_left = QSpinBox()
        self.edt_offset_right = QSpinBox()
        self.edt_offset_top = QSpinBox()
        self.edt_offset_bottom = QSpinBox()
        self.edt_pixels_in_mm = QDoubleSpinBox()
        self.edt_work_height = QDoubleSpinBox()
        self.edt_focus = QLineEdit()
        self.edt_zoom_ratio = QLineEdit()
        # self.btn_ok = QPushButton("OK")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.init_ui()

    # Создание элементов формы
    def init_ui(self):
        self.setMinimumWidth(480)
        layout_main = QVBoxLayout()

        lbl_micros = QLabel("Камера")
        # lbl_micros.setAlignment(Qt.AlignHCenter)
        font_title = lbl_micros.font()
        font_title.setBold(True)
        font_title.setPixelSize(16)
        lbl_micros.setFont(font_title)
        layout_main.addWidget(lbl_micros)
        layout_micros = QHBoxLayout()
        self.combo_micros.currentIndexChanged.connect(self.combo_micros_changed)
        layout_micros.addWidget(self.combo_micros)
        btn_micros_add = QPushButton("Добавить")
        btn_micros_add.setMaximumWidth(80)
        btn_micros_add.clicked.connect(self.btn_micros_add_click)
        layout_micros.addWidget(btn_micros_add)
        btn_micros_edt = QPushButton("Изменить")
        btn_micros_edt.setMaximumWidth(80)
        btn_micros_edt.clicked.connect(self.btn_micros_edt_click)
        layout_micros.addWidget(btn_micros_edt)
        btn_micros_del = QPushButton("Удалить")
        btn_micros_del.setMaximumWidth(80)
        btn_micros_del.clicked.connect(self.btn_micros_del_click)
        layout_micros.addWidget(btn_micros_del)
        layout_main.addLayout(layout_micros)

        for edt_px in [self.edt_res_width, self.edt_res_height, self.edt_offset_left, self.edt_offset_right,
                       self.edt_offset_top, self.edt_offset_bottom]:
            edt_px.setMinimum(0)
            edt_px.setMaximum(40000)
            edt_px.setSuffix(" px")
            edt_px.setButtonSymbols(QAbstractSpinBox.NoButtons)
            edt_px.setSingleStep(0)

        lbl_resolution = QLabel("Разрешение")
        lbl_resolution.setFont(font_title)
        layout_main.addWidget(lbl_resolution)
        layout_resolution = QHBoxLayout()
        layout_resolution.addWidget(QLabel("Ширина"))
        self.edt_res_width.setValue(1024)
        self.edt_res_width.setMinimum(20)

        layout_resolution.addWidget(self.edt_res_width)
        layout_resolution.addWidget(QLabel("Высота"))
        self.edt_res_height.setValue(768)
        self.edt_res_height.setMinimum(10)
        layout_resolution.addWidget(self.edt_res_height)
        layout_main.addLayout(layout_resolution)

        lbl_mode = QLabel("Режимы съемки")
        lbl_mode.setFont(font_title)
        layout_main.addWidget(lbl_mode)
        layout_modes_set = QHBoxLayout()
        self.combo_modes.currentIndexChanged.connect(self.combo_modes_changed)
        layout_modes_set.addWidget(self.combo_modes)
        btn_modes_set_add = QPushButton("Добавить")
        btn_modes_set_add.setMaximumWidth(80)
        btn_modes_set_add.clicked.connect(self.btn_modes_set_add_click)
        layout_modes_set.addWidget(btn_modes_set_add)
        btn_modes_set_edt = QPushButton("Изменить")
        btn_modes_set_edt.setMaximumWidth(80)
        btn_modes_set_edt.clicked.connect(self.btn_modes_set_edt_click)
        layout_modes_set.addWidget(btn_modes_set_edt)
        btn_modes_set_del = QPushButton("Удалить")
        btn_modes_set_del.setMaximumWidth(80)
        btn_modes_set_del.clicked.connect(self.btn_modes_set_del_click)
        layout_modes_set.addWidget(btn_modes_set_del)
        layout_main.addLayout(layout_modes_set)

        layout_offset = QFormLayout()
        layout_offset.addRow(QLabel("Размер отступа слева"), self.edt_offset_left)
        layout_offset.addRow(QLabel("Размер отступа справа"), self.edt_offset_right)
        layout_offset.addRow(QLabel("Размер отступа сверху"), self.edt_offset_top)
        layout_offset.addRow(QLabel("Размер отступа снизу"), self.edt_offset_bottom)

        self.edt_pixels_in_mm.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.edt_pixels_in_mm.setSingleStep(0)
        self.edt_pixels_in_mm.setMinimum(1.000)
        self.edt_pixels_in_mm.setMaximum(9999.999)
        self.edt_pixels_in_mm.setValue(1.0)
        self.edt_pixels_in_mm.setSingleStep(0.0)
        self.edt_pixels_in_mm.setDecimals(3)
        layout_offset.addRow(QLabel("Пикселей на мм"), self.edt_pixels_in_mm)
        self.edt_work_height.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.edt_work_height.setSingleStep(0)
        self.edt_work_height.setMinimum(1.000)
        self.edt_work_height.setMaximum(9999.999)
        self.edt_work_height.setValue(1.0)
        self.edt_work_height.setSingleStep(0.0)
        self.edt_work_height.setDecimals(3)
        layout_offset.addRow(QLabel("Высота работы камеры, мм"), self.edt_work_height)
        layout_offset.addRow(QLabel("Фокус"), self.edt_focus)
        layout_offset.addRow(QLabel("Увеличение"), self.edt_zoom_ratio)

        layout_main.addLayout(layout_offset)

        # layout_main.addWidget(self.btn_ok)
        # self.btn_ok.clicked.connect(self.btn_ok_clicked)
        self.button_box.button(QDialogButtonBox.Ok).setDefault(True)
        self.button_box.accepted.connect(self.accept_prop)
        layout_main.addWidget(self.button_box)
        self.button_box.rejected.connect(self.reject)
        self.setLayout(layout_main)

        self.load_all_micros_to_ui()

    # Загрука списка камер
    def load_all_micros_to_ui(self):
        for micros_settings in self.program_settings.all_micros_settings:
            self.combo_micros.addItem(micros_settings.name)
        for i in range(len(self.program_settings.all_micros_settings)):
            if self.program_settings.all_micros_settings[i] == self.program_settings.micros_settings:
                self.combo_micros.setCurrentIndex(i)
                self.load_all_modes_settings_to_ui(self.program_settings.micros_settings)

    # Загрузка настроек камеры
    def load_all_modes_settings_to_ui(self, micros_settings: MicrosSettings):
        self.edt_res_width.setValue(micros_settings.resolution.width())
        self.edt_res_height.setValue(micros_settings.resolution.height())
        self.combo_modes.clear()
        for mode in micros_settings.all_snap_settings:
            self.combo_modes.addItem(mode.name)
        for i in range(len(micros_settings.all_snap_settings)):
            if micros_settings.all_snap_settings[i] == self.program_settings.snap_settings:
                self.combo_modes.setCurrentIndex(i)
                self.load_mode_settings_to_ui(self.program_settings.snap_settings)

    def load_mode_settings_to_ui(self, mode_settings: SnapSettings):
        self.edt_offset_left.setValue(mode_settings.offset[0])
        self.edt_offset_top.setValue(mode_settings.offset[1])
        self.edt_offset_right.setValue(mode_settings.offset[2])
        self.edt_offset_bottom.setValue(mode_settings.offset[3])
        self.edt_pixels_in_mm.setValue(mode_settings.pixels_in_mm)
        self.edt_work_height.setValue(mode_settings.work_height)

    def accept_prop(self):
        # print("ok")
        super().accept()

    def combo_micros_changed(self):
        print(self.combo_micros.currentText())

    def combo_modes_changed(self):
        print(self.combo_modes.currentText())

    def btn_micros_add_click(self):
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self, "Добавление камеры", "Наименование", QLineEdit.Normal)

        if ok:
            self.combo_micros.addItem(text)
            self.combo_micros.setCurrentIndex(self.combo_micros.count() - 1)

    def btn_micros_edt_click(self):
        if self.combo_micros.count() == 0:
            return
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self,
                                        "Переименование камеры", "Наименование",
                                        QLineEdit.Normal, self.combo_micros.currentText())
        if ok and text:
            i = self.combo_micros.currentIndex()
            self.combo_micros.removeItem(self.combo_micros.currentIndex())
            self.combo_micros.insertItem(i, text)
            self.combo_micros.setCurrentIndex(i)

    def btn_micros_del_click(self):
        if self.combo_micros.count() == 0:
            return
        dlg_result = QMessageBox.question(self,
                                          "Confirm Dialog",
                                          "Вы действительно хотите удалить выбранную камеру со всеми настройками?",
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)
        if dlg_result == QMessageBox.Yes:
            input_dialog = QInputDialog()
            text, ok = input_dialog.getText(self, "Удаление камеры",
                                            "Для удаления напишите \"удалить\"", QLineEdit.Normal)
            if ok and str.lower(text) == "удалить":
                self.combo_micros.removeItem(self.combo_micros.currentIndex())

    def btn_modes_set_add_click(self):
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self, "Добавление настройки", "Наименование", QLineEdit.Normal)

        if ok:
            self.combo_set_micro.addItem(text)
            self.combo_set_micro.setCurrentIndex(self.combo_set_micro.count() - 1)

    def btn_modes_set_edt_click(self):
        if self.combo_set_micro.count() == 0:
            return
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self,
                                        "Переименование настройки", "Наименование",
                                        QLineEdit.Normal, self.combo_set_micro.currentText())
        if ok and text:
            i = self.combo_set_micro.currentIndex()
            self.combo_set_micro.removeItem(self.combo_set_micro.currentIndex())
            self.combo_set_micro.insertItem(i, text)
            self.combo_set_micro.setCurrentIndex(i)

    def btn_modes_set_del_click(self):
        if self.combo_set_micro.count() == 0:
            return
        dlg_result = QMessageBox.question(self,
                                          "Confirm Dialog",
                                          "Вы действительно хотите удалить выбранную настройку полностью?",
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)
        if dlg_result == QMessageBox.Yes:
            input_dialog = QInputDialog()
            text, ok = input_dialog.getText(self, "Удаление настройки",
                                            "Для удаления напишите \"удалить\"", QLineEdit.Normal)
            if ok and str.lower(text) == "удалить":
                self.combo_set_micro.removeItem(self.combo_set_micro.currentIndex())
