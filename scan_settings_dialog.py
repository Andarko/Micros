from PyQt5.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QInputDialog, \
    QLineEdit, QMessageBox, QFormLayout, QDoubleSpinBox, QSpinBox, QAbstractSpinBox, QDialogButtonBox
from PyQt5.QtCore import Qt, QSize, QRect
import xml.etree.ElementTree as Xml


# Класс для хранения всех настроек камер. Он может загружаться из файла и сохраняться в файл
from lxml import etree


# Классы для хранения текущих выбранных настроек
# Выбранные настройки микроскопа
class MicrosSettings(object):
    def __init__(self, name=""):
        self.name = name
        self.resolution = QSize(1024, 768)
        self.all_snap_settings = list()
        self.default = False


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
        self.focus = ""
        self.zoom = ":"
        self.default = False


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
        self.micros_settings: MicrosSettings = None
        self.snap_settings: SnapSettings = None
        self.table_settings = TableSettings()
        self.test = test
        # if not test:
        self.load_settings_from_xml("scan_settings.xml")

    def set_default_micros(self, micros_settings: MicrosSettings = None):
        for settings in self.all_micros_settings:
            settings.default = False
        if micros_settings:
            micros_settings.default = True
        else:
            self.micros_settings.default = True

    def set_default_snap(self, snap_settings: SnapSettings = None):
        for settings in self.micros_settings.all_snap_settings:
            settings.default = False
        if snap_settings:
            snap_settings.default = True
        else:
            self.snap_settings.default = True

    # Загрузка настроек из файла
    def load_settings_from_xml(self, file_name, test=False):
        with open(file_name) as fileObj:
            xml = fileObj.read()
        root = etree.fromstring(xml)

        for element_main in root.getchildren():
            # Загрузка параметров стола
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

            # Загрузка списка микроскопов
            elif element_main.tag == "AllMicros":
                for element_all in element_main.getchildren():
                    # Данные микроскопа
                    if element_all.tag == "Micros":
                        new_micros_settings = MicrosSettings(element_all.get('name'))
                        self.all_micros_settings.append(new_micros_settings)
                        for element_micros in element_all.getchildren():
                            # Микроскоп, выбранный по умолчанию
                            if element_micros.tag == "Default":
                                if (not self.test and element_micros.text == "True") \
                                        or (self.test and new_micros_settings.name == "Микроскоп_тест 20к"):
                                    new_micros_settings.default = True
                                    self.micros_settings = new_micros_settings

                            elif element_micros.tag == "Resolution":
                                for element_resolution in element_micros.getchildren():
                                    if element_resolution.tag == "Width":
                                        new_micros_settings.resolution.setWidth(int(element_resolution.text))
                                    elif element_resolution.tag == "Height":
                                        new_micros_settings.resolution.setHeight(int(element_resolution.text))
                            # Чтеник списка модов микроскопа
                            elif element_micros.tag == "Mode":
                                new_snap_settings = SnapSettings(element_micros.get('name'))
                                new_micros_settings.all_snap_settings.append(new_snap_settings)
                                new_snap_settings.snap_width = new_micros_settings.resolution.width()
                                new_snap_settings.snap_height = new_micros_settings.resolution.height()
                                for element_mode in element_micros.getchildren():
                                    if element_mode.tag == "Default" and element_mode.text == "True":
                                        new_snap_settings.default = True
                                        # self.snap_settings = new_snap_settings
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
                                        new_snap_settings.focus = element_mode.text
                                    elif element_mode.tag == "Zoom":
                                        new_snap_settings.zoom = element_mode.text
                                new_snap_settings.frame[0] = new_snap_settings.offset[0]
                                new_snap_settings.frame[1] = new_snap_settings.offset[1]
                                new_snap_settings.frame[2] = new_snap_settings.snap_width - new_snap_settings.offset[2]
                                new_snap_settings.frame[3] = new_snap_settings.snap_height - new_snap_settings.offset[3]
        if self.all_micros_settings and not self.micros_settings:
            self.micros_settings = self.all_micros_settings[0]
        if self.micros_settings.all_snap_settings and not self.snap_settings:
            self.snap_settings = self.micros_settings.all_snap_settings[0]


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
        self.edt_zoom = QLineEdit()
        # self.btn_ok = QPushButton("OK")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.edits_res_unsaved = False
        self.edits_mode_unsaved = False

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
        # self.combo_micros.currentIndexChanged.connect(self.combo_micros_changed)
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
        self.edt_res_width.editingFinished.connect(self.edits_res_changed)

        layout_resolution.addWidget(self.edt_res_width)
        layout_resolution.addWidget(QLabel("Высота"))
        self.edt_res_height.setValue(768)
        self.edt_res_height.setMinimum(10)
        self.edt_res_height.editingFinished.connect(self.edits_res_changed)
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
        self.edt_offset_left.valueChanged.connect(self.edits_mode_changed)
        layout_offset.addRow(QLabel("Размер отступа справа"), self.edt_offset_right)
        self.edt_offset_right.valueChanged.connect(self.edits_mode_changed)
        layout_offset.addRow(QLabel("Размер отступа сверху"), self.edt_offset_top)
        self.edt_offset_top.valueChanged.connect(self.edits_mode_changed)
        layout_offset.addRow(QLabel("Размер отступа снизу"), self.edt_offset_bottom)
        self.edt_offset_bottom.valueChanged.connect(self.edits_mode_changed)

        self.edt_pixels_in_mm.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.edt_pixels_in_mm.setSingleStep(0)
        self.edt_pixels_in_mm.setMinimum(1.000)
        self.edt_pixels_in_mm.setMaximum(9999.999)
        self.edt_pixels_in_mm.setValue(1.0)
        self.edt_pixels_in_mm.setSingleStep(0.0)
        self.edt_pixels_in_mm.setDecimals(3)
        self.edt_pixels_in_mm.valueChanged.connect(self.edits_mode_changed)
        layout_offset.addRow(QLabel("Пикселей на мм"), self.edt_pixels_in_mm)
        self.edt_work_height.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.edt_work_height.setSingleStep(0)
        self.edt_work_height.setMinimum(1.000)
        self.edt_work_height.setMaximum(9999.999)
        self.edt_work_height.setValue(1.0)
        self.edt_work_height.setSingleStep(0.0)
        self.edt_work_height.setDecimals(3)
        self.edt_work_height.valueChanged.connect(self.edits_mode_changed)
        layout_offset.addRow(QLabel("Высота работы камеры, мм"), self.edt_work_height)
        layout_offset.addRow(QLabel("Фокус"), self.edt_focus)
        self.edt_focus.textChanged.connect(self.edits_mode_changed)
        layout_offset.addRow(QLabel("Увеличение"), self.edt_zoom)
        self.edt_zoom.textChanged.connect(self.edits_mode_changed)

        layout_main.addLayout(layout_offset)

        # layout_main.addWidget(self.btn_ok)
        # self.btn_ok.clicked.connect(self.btn_ok_clicked)
        self.button_box.button(QDialogButtonBox.Ok).setDefault(True)
        self.button_box.accepted.connect(self.accept_prop)
        layout_main.addWidget(self.button_box)
        self.button_box.rejected.connect(self.reject)
        self.setLayout(layout_main)

        self.load_all_micros_to_ui()

        self.combo_micros.currentIndexChanged.connect(self.combo_micros_changed)

    def closeEvent(self, event):
        self.edits_res_save()
        self.edits_mode_save()

    def edits_res_changed(self):
        self.edits_res_unsaved = True

    def edits_mode_changed(self):
        self.edits_mode_unsaved = True

    def edits_res_save(self):
        if self.edits_res_unsaved:
            self.program_settings.micros_settings.resolution.setWidth(self.edt_res_width.value())
            self.program_settings.micros_settings.resolution.setHeight(self.edt_res_height.value())

    def edits_mode_save(self):
        if self.edits_mode_unsaved:
            self.program_settings.snap_settings.offset[0] = self.edt_offset_left.value()
            self.program_settings.snap_settings.offset[1] = self.edt_offset_top.value()
            self.program_settings.snap_settings.offset[2] = self.edt_offset_right.value()
            self.program_settings.snap_settings.offset[3] = self.edt_offset_bottom.value()
            self.program_settings.snap_settings.pixels_in_mm = self.edt_pixels_in_mm.value()
            self.program_settings.snap_settings.work_height = self.edt_work_height.value()
            self.program_settings.snap_settings.focus = self.edt_focus.text()
            self.program_settings.snap_settings.zoom = self.edt_zoom.text()

    # Загрука списка камер
    def load_all_micros_to_ui(self):
        if self.program_settings.all_micros_settings:
            for micros_settings in self.program_settings.all_micros_settings:
                self.combo_micros.addItem(micros_settings.name)
            i = -1
            for micros_settings in self.program_settings.all_micros_settings:
                i += 1
                if micros_settings.default:
                    self.combo_micros.setCurrentIndex(i)
                    self.load_all_modes_to_ui(self.program_settings.micros_settings)
                    return
            self.combo_micros.setCurrentIndex(0)
            self.load_all_modes_to_ui(self.program_settings.micros_settings)

    # Загрузка настроек камеры
    def load_all_modes_to_ui(self, micros_settings: MicrosSettings):
        if self.program_settings.micros_settings:
            # Запись измененных настроек предыдущего микроскопа
            self.edits_res_save()
            # self.program_settings.micros_settings.default = False
            self.program_settings.micros_settings = micros_settings
            # self.program_settings.micros_settings.default = True
            self.program_settings.set_default_micros()

        self.edt_res_width.setValue(micros_settings.resolution.width())
        self.edt_res_height.setValue(micros_settings.resolution.height())
        self.combo_modes.clear()
        for mode in micros_settings.all_snap_settings:
            self.combo_modes.addItem(mode.name)
        i = -1
        for mode in micros_settings.all_snap_settings:
            i += 1
            if mode.default:
                self.combo_modes.setCurrentIndex(i)
                self.load_mode_settings_to_ui(self.program_settings.snap_settings)
        self.edits_res_unsaved = False

    def load_mode_settings_to_ui(self, snap_settings: SnapSettings):
        if not snap_settings:
            snap_settings = SnapSettings()
        # change_default = \
        #     snap_settings in self.program_settings.micros_settings.all_snap_settings and \
        #     self.program_settings.snap_settings in self.program_settings.micros_settings.all_snap_settings
        #
        # if change_default:
        #     self.program_settings.snap_settings.default = False
        # snap_settings.default = True
        # Запись данных по настройке
        if self.program_settings.snap_settings:
            self.edits_mode_save()
        self.edt_offset_left.setValue(snap_settings.offset[0])
        self.edt_offset_top.setValue(snap_settings.offset[1])
        self.edt_offset_right.setValue(snap_settings.offset[2])
        self.edt_offset_bottom.setValue(snap_settings.offset[3])
        self.edt_pixels_in_mm.setValue(snap_settings.pixels_in_mm)
        self.edt_work_height.setValue(snap_settings.work_height)
        self.edt_focus.setText(snap_settings.focus)
        self.edt_zoom.setText(snap_settings.zoom)

        self.program_settings.snap_settings = snap_settings
        self.program_settings.set_default_snap()
        self.edits_mode_unsaved = False

    def accept_prop(self):
        # print("ok")
        super().accept()

    def combo_micros_changed(self):
        print("micros: " + self.combo_micros.currentText())
        if self.combo_micros.currentIndex() > -1:
            self.load_all_modes_to_ui(self.program_settings.all_micros_settings[self.combo_micros.currentIndex()])

    def combo_modes_changed(self):
        if self.program_settings.micros_settings and self.program_settings.micros_settings.all_snap_settings \
                and self.combo_modes.currentIndex() > -1:
            self.load_mode_settings_to_ui(self.program_settings.micros_settings.all_snap_settings[
                                              self.combo_modes.currentIndex()])
        else:
            self.load_mode_settings_to_ui(None)
        print("mode: " + self.combo_modes.currentText())

    def btn_micros_add_click(self, default_text=""):
        if not default_text:
            default_text = ""
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self, "Добавление камеры", "Наименование", QLineEdit.Normal, default_text)

        if ok and text:
            for micros_settings in self.program_settings.all_micros_settings:
                if micros_settings.name == text:
                    QMessageBox.warning(self, "Warning!", "Данное имя уже используется", QMessageBox.Ok, QMessageBox.Ok)
                    self.btn_micros_add_click(text)
                    return
            self.program_settings.all_micros_settings.append(MicrosSettings(text))
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
            self.program_settings.micros_settings.name = text
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
                index = self.combo_micros.currentIndex()
                self.program_settings.all_micros_settings.pop(index)
                if index == len(self.program_settings.all_micros_settings):
                    index -= 1
                if index > -1:
                    self.program_settings.micros_settings = self.program_settings.all_micros_settings[index]
                else:
                    self.program_settings.micros_settings = MicrosSettings()
                self.combo_micros.removeItem(self.combo_micros.currentIndex())

    def btn_modes_set_add_click(self, default_text=""):
        if not default_text:
            default_text = ""
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self, "Добавление настройки", "Наименование", QLineEdit.Normal, default_text)

        if ok and text:
            for snap_settings in self.program_settings.micros_settings.all_snap_settings:
                if snap_settings.name == text:
                    QMessageBox.warning(self, "Warning!", "Данное имя уже используется", QMessageBox.Ok, QMessageBox.Ok)
                    self.btn_modes_set_add_click(text)
                    return
            self.program_settings.micros_settings.all_snap_settings.append(SnapSettings(text))
            self.combo_modes.addItem(text)
            self.combo_modes.setCurrentIndex(self.combo_modes.count() - 1)

    def btn_modes_set_edt_click(self):
        if self.combo_modes.count() == 0:
            return
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self,
                                        "Переименование настройки", "Наименование",
                                        QLineEdit.Normal, self.combo_modes.currentText())
        if ok and text:
            self.program_settings.snap_settings.name = text
            i = self.combo_modes.currentIndex()
            self.combo_modes.removeItem(self.combo_modes.currentIndex())
            self.combo_modes.insertItem(i, text)
            self.combo_modes.setCurrentIndex(i)

    def btn_modes_set_del_click(self):
        if self.combo_modes.count() == 0:
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
                index = self.combo_modes.currentIndex()
                self.program_settings.micros_settings.all_snap_settings.pop(index)
                if index == len(self.program_settings.micros_settings.all_snap_settings):
                    index -= 1
                if index > -1:
                    self.program_settings.snap_settings = self.program_settings.micros_settings.all_snap_settings[index]
                else:
                    self.program_settings.snap_settings = SnapSettings()
                self.combo_modes.removeItem(self.combo_modes.currentIndex())
