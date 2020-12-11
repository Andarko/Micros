import cv2
import sys
import datetime
import random
import uuid
import shutil
from enum import Enum
import numpy as np
import os.path
import tempfile
import zipfile
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QTreeView, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QFileSystemModel, QMenuBar, QMenu, QMainWindow, QPushButton, QAction, qApp
from PyQt5.QtWidgets import QTextEdit, QSizePolicy, QGridLayout, QStyle, QFrame, QErrorMessage, QCheckBox
from PyQt5.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QMessageBox, QDockWidget
from PyQt5.QtGui import QIcon, QPixmap, QImage
import PyQt5.QtGui as QtGui
from PyQt5.QtCore import Qt, QSize, QEvent, QPoint, QPointF
from lxml import etree

from SettingsDialog import SettingsDialog, ProgramSettings
import xml.etree.ElementTree as Xml


class Point(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class PointF(object):
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y


class Size(object):
    def __init__(self, w=0, h=0):
        self.width = w
        self.height = h


class SizeF(object):
    def __init__(self, w=0.0, h=0.0):
        self.width = w
        self.height = h


class Rect(object):
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.width = w
        self.height = h


class RectF(object):
    def __init__(self, x=0.0, y=0.0, w=0.0, h=0.0):
        self.x = x
        self.y = y
        self.width = w
        self.height = h


# Данные сканирования
class SavedData(object):
    def __init__(self, folder):
        self.filePath = ""
        self.folder = folder
        self.rowCount = 0
        self.colCount = 0
        self.format = "jpg"
        # Размер исходника картинки
        self.imgSize = Size()
        # Размер обрезанного изображения
        self.connectionArea = Rect()
        # Коодридаты обрезанных изображений на склейке
        self.arrayImagesSize = []
        # Держать ли в памяти все изображение
        self.allImageInMemory = False
        # Изображения в памяти
        self.arrayLoadImages = []

    def set_all_image_in_memory(self, new_value):
        self.allImageInMemory = new_value
        if new_value:
            self.arrayLoadImages = []
            for k in range(3):
                layer = []
                prefix = "P"
                if k > 0:
                    prefix += str(k)
                prefix += "_"
                for i in range(self.rowCount):
                    row = []
                    for j in range(self.colCount):
                        row.append(cv2.imread(os.path.join(self.folder,
                                                           prefix + str(i+1) + "_" + str(j+1) + ".jpg"))[:, :, ::-1])
                    layer.append(row)
                self.arrayLoadImages.append(layer)
        else:
            self.arrayLoadImages = []

    # Подготовка обрезанных файлов изображения и уменьшенных файлов изображения
    def prepare_scans(self, replace=False):
        minimap = np.zeros(0)
        minimap_need_create = replace or not os.path.exists(os.path.join(self.folder, "mini.jpg"))
        modified = minimap_need_create
        for i in range(self.rowCount):
            # Вычисление размера частей картинок, нужных для склейки между собой
            y1 = self.connectionArea.y
            if i == 0:
                y1 = 0
            y2 = self.connectionArea.y + self.connectionArea.height
            if i == self.rowCount - 1:
                y2 = self.imgSize.height

            minimap_row = np.zeros(0)
            for j in range(self.colCount):
                img_p = np.zeros(0)
                # Подготовка основных (детализированных) изображений
                if (replace or not os.path.exists(os.path.join(self.folder,
                                                               "P_" + str(i+1) + "_" + str(j+1) + ".jpg"))) \
                        and os.path.exists(os.path.join(self.folder, "S_" + str(i+1) + "_" + str(j+1) + ".jpg")):
                    x1 = self.connectionArea.x
                    if j == 0:
                        x1 = 0
                    x2 = self.connectionArea.x + self.connectionArea.width
                    if j == self.colCount - 1:
                        x2 = self.imgSize.width
                    img_s = cv2.imread(os.path.join(self.folder, "S_" + str(i+1) + "_" + str(j+1) + ".jpg"))
                    img_p = np.copy(img_s[y1:y2, x1:x2, :])
                    cv2.imwrite(os.path.join(self.folder, "P_" + str(i+1) + "_" + str(j+1) + ".jpg"), img_p)
                    modified = True
                if img_p.shape[0] == 0:
                    img_p = cv2.imread(os.path.join(self.folder, "P_" + str(i+1) + "_" + str(j+1) + ".jpg"))
                if img_p.shape[0] == 0:
                    continue
                # Подготовка обрезанных изображений пониженного качества, в т.ч. миникарты
                img_p1 = np.zeros(0)
                img_p2 = np.zeros(0)
                if replace or not os.path.exists(os.path.join(self.folder,
                                                              "P1_" + str(i+1) + "_" + str(j+1) + ".jpg")) \
                        or not os.path.exists(os.path.join(self.folder, "P2_" + str(i+1) + "_" + str(j+1) + ".jpg")):
                    dim1 = (int(img_p.shape[1] / 2), int(img_p.shape[0] / 2))
                    img_p1 = cv2.resize(img_p, dim1, interpolation=cv2.INTER_AREA)
                    cv2.imwrite(os.path.join(self.folder, "P1_" + str(i+1) + "_" + str(j+1) + ".jpg"), img_p1)
                    dim2 = (int(img_p.shape[1] / 4), int(img_p.shape[0] / 4))
                    img_p2 = cv2.resize(img_p1, dim2, interpolation=cv2.INTER_AREA)
                    cv2.imwrite(os.path.join(self.folder, "P2_" + str(i+1) + "_" + str(j+1) + ".jpg"), img_p2)
                    modified = True

                if minimap_need_create:
                    if img_p2.size == 0:
                        img_p2 = cv2.imread(os.path.join(self.folder, "P2_" + str(i+1) + "_" + str(j+1) + ".jpg"))
                    if minimap_row.size == 0:
                        minimap_row = np.copy(img_p2)
                    else:
                        minimap_row = np.concatenate((minimap_row, img_p2), axis=1)
            if minimap_need_create:
                if minimap.size == 0:
                    minimap = np.copy(minimap_row)
                else:
                    minimap = np.concatenate((minimap, minimap_row), axis=0)

        if minimap_need_create:
            max_size = max(minimap.shape[0], minimap.shape[1])
            if max_size > 200:
                dim = (int(minimap.shape[1] * 200 / max_size), int(minimap.shape[0] * 200 / max_size))
                minimap = cv2.resize(minimap, dim, interpolation=cv2.INTER_AREA)
            cv2.imwrite(os.path.join(self.folder, "mini.jpg"), minimap)

        return modified
        """
        if not replace and (not os.path.exists(self.Folder + "P_" + str(i+1) + "_" + str(j+1) + ".jpg") or not os.path.exists(self.Folder + "P1_" + str(i+1) + "_" + str(j+1) + ".jpg") or not os.path.exists(self.Folder + "P2_" + str(i+1) + "_" + str(j+1) + ".jpg")):
            img_s = cv2.imread(self.Folder + "S_" + str(i+1) + "_" + str(j+1) + ".jpg")
            img_p = np.copy(img[y1:y2, x1:x2, :])
            if not os.path.exists(self.Folder + "P_" + str(i+1) + "_" + str(j+1) + ".jpg"):
                cv2.imwrite(self.Folder + "P_" + str(i+1) + "_" + str(j+1) + ".jpg", img_p)
            
        """

    # сохранение данных в XML
    def save_to_file_xml(self, xmlFile):
        try:
            root = Xml.Element("Root")
            appt_rc = Xml.Element("RowCount")
            appt_rc.text = str(self.rowCount)
            root.append(appt_rc)
            appt_cc = Xml.Element("ColCount")
            appt_cc.text = str(self.colCount)
            root.append(appt_cc)
            appt_i = Xml.Element("Image")
            root.append(appt_i)
            formatt = Xml.SubElement(appt_i, "Format")
            formatt.text = self.format
            # isAllImageInMemory = xml.SubElement(appt_i, "AllImageInMemory")
            # isAllImageInMemory.text = str(self.allImageInMemory)
            img_size = Xml.SubElement(appt_i, "ImgSize")
            is_width = Xml.SubElement(img_size, "Width")
            is_width.text = str(self.imgSize.width)
            is_height = Xml.SubElement(img_size, "Height")
            is_height.text = str(self.imgSize.height)
            con_area = Xml.SubElement(appt_i, "ConnectionArea")
            ca_x = Xml.SubElement(con_area, "X")
            ca_x.text = str(self.connectionArea.x)
            ca_y = Xml.SubElement(con_area, "Y")
            ca_y.text = str(self.connectionArea.y)
            ca_width = Xml.SubElement(con_area, "Width")
            ca_width.text = str(self.connectionArea.width)
            ca_height = Xml.SubElement(con_area, "Height")
            ca_height.text = str(self.connectionArea.height)

            tree = Xml.ElementTree(root)
            with open(xmlFile, "w") as fobj:
                tree.write(xmlFile)
            return True
        except Exception:
            return False

    # Загрузка данных из XML
    def load_from_file_xml(self, xml_file):
        try:
            with open(xml_file) as fobj:
                xml = fobj.read()
            root = etree.fromstring(xml)
            for appt in root.getchildren():
                if appt.tag == "RowCount":
                    self.rowCount = int(appt.text)
                elif appt.tag == "ColCount":
                    self.colCount = int(appt.text)
                elif appt.tag == "Image":
                    for elem in appt.getchildren():
                        if elem.tag == "Format":
                            self.format = appt.text
                        # elif elem.tag == "AllImageInMemory":
                        #    self.allImageInMemory = bool(appt.text)
                        elif elem.tag == "ImgSize":
                            for sub_elem in elem.getchildren():
                                if sub_elem.tag == "Width":
                                    self.imgSize.width = int(sub_elem.text)
                                elif sub_elem.tag == "Height":
                                    self.imgSize.height = int(sub_elem.text)
                        elif elem.tag == "ConnectionArea":
                            for sub_elem in elem.getchildren():
                                if sub_elem.tag == "Width":
                                    self.connectionArea.width = int(sub_elem.text)
                                elif sub_elem.tag == "Height":
                                    self.connectionArea.height = int(sub_elem.text)
                                elif sub_elem.tag == "X":
                                    self.connectionArea.x = int(sub_elem.text)
                                elif sub_elem.tag == "Y":
                                    self.connectionArea.y = int(sub_elem.text)
            self.filePath = xml_file
            self.arrayImagesSize = []
            koef = 1
            for k in range(3):
                array_area = []
                y = 0
                for i in range(self.rowCount + 1):
                    array_row = []
                    x = 0
                    if i == 0 or i == self.rowCount - 1:
                        dy = self.imgSize.height - self.connectionArea.y
                    elif i == self.rowCount:
                        dy = 0
                    else:
                        dy = self.connectionArea.height
                    if k > 0:
                        dy >>= k
                    for j in range(self.colCount + 1):
                        if j == 0 or j == self.colCount - 1:
                            dx = self.imgSize.width - self.connectionArea.x
                        elif j == self.colCount:
                            dx = 0
                        else:
                            dx = self.connectionArea.width
                        if k > 0:
                            dx >>= k
                        array_row.append(Rect(x, y, dx, dy))
                        x += dx
                    y += dy
                    array_area.append(array_row)
                self.arrayImagesSize.append(array_area)

            # self.reloadPrepareData()
            return True
        except Exception as err:
            print(err)
            return False


# Класс текущего отображения изображения
class ImageView(object):
    def __init__(self, saved_data=SavedData("")):
        # Данные изображения
        self.saved_data = saved_data
        # Загруженные куски изображения
        # self.imgData = np.empty(0)
        # Сшитое из кусков изображение фрагмента
        self.sumImg = np.empty(0)
        self.minimapBase = np.empty(0)
        self.curRect = Rect(-1, -1, 0, 0)
        # Параметры отображения
        self.scale = 1.0
        self.scaleIndex = 0
        self.offset = PointF()
        self.saved_data_clear()

    def saved_data_clear(self):
        # self.imgData = np.zerosro((self.savedData.rowCount, self.savedData.colCount))
        self.sumImg = np.empty(0)
        self.curRect = Rect(-1, -1, 0, 0)

    # Легкий вариант получения сшитого изображения простым сшитием всех кусков
    def easy_merge(self, new_scale_index=0, new_rect=Rect()):
        prefix = "P"
        if new_scale_index > 0:
            prefix += str(new_scale_index)
        prefix += "_"
        self.saved_data_clear()
        self.sumImg = np.zeros(0, dtype = np.uint8)
        for i in range(new_rect.y, new_rect.y + new_rect.height):
            row_img = np.zeros(0, dtype = np.uint8)
            for j in range(new_rect.x, new_rect.x + new_rect.width):
                if self.saved_data.allImageInMemory:
                    img = self.saved_data.arrayLoadImages[new_scale_index][i][j]
                else:
                    img = cv2.imread(os.path.join(self.saved_data.folder,
                                                  prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))[:, :, ::-1]
                if row_img.size == 0:
                    # row_img = np.copy(img)
                    row_img = img
                else:
                    row_img = np.concatenate((row_img, img), axis=1)

            if self.sumImg.size == 0:
                # self.sumImg = np.copy(row_img)
                self.sumImg = row_img
            else:
                self.sumImg = np.concatenate((self.sumImg, row_img), axis=0)

    # Получение сшитого изображения
    def get_new_preview(self, new_scale_index=0, new_rect=Rect()):
        prefix = "P"
        if new_scale_index > 0:
            prefix += str(new_scale_index)
        prefix += "_"
        if self.scaleIndex != new_scale_index:
            self.scaleIndex = new_scale_index
            self.saved_data_clear()

        intersect_rect = Rect()
        if self.sumImg.shape[0] > 0 and new_rect.width > 0 and new_rect.height > 0:
            intersect_rect.x = max(self.curRect.x, new_rect.x)
            intersect_rect.y = max(self.curRect.y, new_rect.y)
            intersect_rect.width = min(self.curRect.x + self.curRect.width, new_rect.x + new_rect.width) - intersect_rect.x
            intersect_rect.height = min(self.curRect.y + self.curRect.height, new_rect.y + new_rect.height) - intersect_rect.y

        if intersect_rect.width <= 0 or intersect_rect.height <= 0:
            # Отрисовываем соединенную картинку простым способом
            self.easy_merge(new_scale_index, new_rect)
        elif new_rect.width > 0 and new_rect.height > 0:
            # 1. Вырезаем видимую часть старого изображения
            first_area_of_intersect_rect = self.saved_data.arrayImagesSize[new_scale_index][intersect_rect.y][intersect_rect.x]
            last_area_of_intersect_rect = self.saved_data.arrayImagesSize[new_scale_index]
            [intersect_rect.y + intersect_rect.height - 1][intersect_rect.x + intersect_rect.width - 1]
            first_area_of_current_rect = self.saved_data.arrayImagesSize[new_scale_index][self.curRect.y][self.curRect.x]
            y1_inter_in_current = first_area_of_intersect_rect.y - first_area_of_current_rect.y
            x1_inter_in_current = first_area_of_intersect_rect.x - first_area_of_current_rect.x
            y2_inter_in_current = last_area_of_intersect_rect.y - first_area_of_current_rect.y
            y2_inter_in_current += last_area_of_intersect_rect.height
            x2_inter_in_current = last_area_of_intersect_rect.x - first_area_of_current_rect.x
            x2_inter_in_current += last_area_of_intersect_rect.width
            intersect_img = np.copy(self.sumImg[y1_inter_in_current:y2_inter_in_current,
                                    x1_inter_in_current:x2_inter_in_current, :])

            # 2. Слева и справа от этой области надо объединить кадры вертикально в столбцы
            # (высотой, равной высоте области)
            # 2.1 Слева
            full_row = np.zeros(0, dtype=np.uint8)
            for j in range(new_rect.x, intersect_rect.x):
                temp_column = np.zeros(0, dtype=np.uint8)
                for i in range(intersect_rect.y, intersect_rect.y + intersect_rect.height):
                    if self.saved_data.allImageInMemory:
                        img = self.saved_data.arrayLoadImages[new_scale_index][i][j]
                    else:
                        img = cv2.imread(os.path.join(self.saved_data.folder,
                                                      prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))[:, :, ::-1]
                    if temp_column.size == 0:
                        temp_column = img
                    else:
                        temp_column = np.concatenate((temp_column, img), axis=0)
                if full_row.size == 0:
                    full_row = temp_column
                else:
                    full_row = np.concatenate((full_row, temp_column), axis=1)
            # 2.2 Середину по горизонтали
            if full_row.size == 0:
                full_row = intersect_img
            else:
                full_row = np.concatenate((full_row, intersect_img), axis=1)
            # 2.3 Справа
            for j in range(intersect_rect.x + intersect_rect.width, new_rect.x + new_rect.width):
                temp_column = np.zeros(0, dtype=np.uint8)
                for i in range(intersect_rect.y, intersect_rect.y + intersect_rect.height):
                    if self.saved_data.allImageInMemory:
                        img = self.saved_data.arrayLoadImages[new_scale_index][i][j]
                    else:
                        img = cv2.imread(os.path.join(self.saved_data.folder,
                                                      prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))[:, :, ::-1]
                    if temp_column.size == 0:
                        temp_column = img
                    else:
                        temp_column = np.concatenate((temp_column, img), axis=0)
                if full_row.size == 0:
                    full_row = temp_column
                else:
                    full_row = np.concatenate((full_row, temp_column), axis=1)

            # 3. Объединяем части сверху, пришиваем наш full_row, потом части ниже
            # 3.1 Сверху
            self.sumImg = np.zeros(0, dtype=np.uint8)
            for i in range(new_rect.y, intersect_rect.y):
                temp_row = np.zeros(0, dtype=np.uint8)
                for j in range(new_rect.x, new_rect.x + new_rect.width):
                    if self.saved_data.allImageInMemory:
                        img = self.saved_data.arrayLoadImages[new_scale_index][i][j]
                    else:
                        img = cv2.imread(os.path.join(self.saved_data.folder,
                                                      prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))[:, :, ::-1]
                    if temp_row.size == 0:
                        temp_row = img
                    else:
                        temp_row = np.concatenate((temp_row, img), axis=1)
                if self.sumImg.size == 0:
                    self.sumImg = temp_row
                else:
                    self.sumImg = np.concatenate((self.sumImg, temp_row), axis=0)
            # 3.2 Середину по вертикали
            if self.sumImg.size == 0:
                self.sumImg = full_row
            else:
                self.sumImg = np.concatenate((self.sumImg, full_row), axis=0)
            # 3.3 Снизу
            for i in range(intersect_rect.y + intersect_rect.height, new_rect.y + new_rect.height):
                temp_row = np.zeros(0, dtype=np.uint8)
                for j in range(new_rect.x, new_rect.x + new_rect.width):
                    if self.saved_data.allImageInMemory:
                        img = self.saved_data.arrayLoadImages[new_scale_index][i][j]
                    else:
                        img = cv2.imread(os.path.join(self.saved_data.folder,
                                                      prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))[:, :, ::-1]
                    if temp_row.size == 0:
                        temp_row = img
                    else:
                        temp_row = np.concatenate((temp_row, img), axis=1)
                if self.sumImg.size == 0:
                    self.sumImg = temp_row
                else:
                    self.sumImg = np.concatenate((self.sumImg, temp_row), axis=0)

        self.curRect = new_rect

    def get_view(self, new_scale=1.0, new_visible_size=QSize()):
        if self.saved_data.rowCount == 0:
            return
        if new_scale < 0.001:
            new_scale = 0.001
        if new_scale > 20.0:
            new_scale = 20.0

        if self.offset.y + new_visible_size.height() / new_scale > self.saved_data.arrayImagesSize[0][-1][0].y:
            self.offset.y = self.saved_data.arrayImagesSize[0][-1][0].y - new_visible_size.height() / new_scale
        if self.offset.y < 0:
            self.offset.y = 0
        if self.offset.x + new_visible_size.width() / new_scale > self.saved_data.arrayImagesSize[0][0][-1].x:
            self.offset.x = self.saved_data.arrayImagesSize[0][0][-1].x - new_visible_size.width() / new_scale
        if self.offset.x < 0:
            self.offset.x = 0
        # Проверим сначала, как зименился масштаб, не надо ли загрузить изображения другого качества
        new_scale_index = 0
        if new_scale <= 0.125:
            new_scale_index = 2
        elif new_scale <= 0.25:
            new_scale_index = 1
        self.scale = new_scale
        y1_ind = 0
        x1_ind = 0
        y2_ind = 0
        x2_ind = 0
        y2_offset = self.offset.y + new_visible_size.height() / new_scale
        x2_offset = self.offset.x + new_visible_size.width() / new_scale
        for i in range(self.saved_data.rowCount - 1, -1, -1):
            if y2_offset >= self.saved_data.arrayImagesSize[0][i][0].y:
                y2_ind = i
                break
        for j in range(self.saved_data.colCount - 1, -1, -1):
            if x2_offset >= self.saved_data.arrayImagesSize[0][0][j].x:
                x2_ind = j
                break

        for i in range(y2_ind, -1, -1):
            if self.offset.y >= self.saved_data.arrayImagesSize[0][i][0].y:
                y1_ind = i
                break
        for j in range(x2_ind, -1, -1):
            if self.offset.x >= self.saved_data.arrayImagesSize[0][0][j].x:
                x1_ind = j
                break
        self.get_new_preview(new_scale_index, Rect(x1_ind, y1_ind, x2_ind - x1_ind + 1, y2_ind - y1_ind + 1))

        y1 = (int(self.offset.y) >> self.scaleIndex) - self.saved_data.arrayImagesSize[self.scaleIndex][y1_ind][x1_ind].y
        x1 = (int(self.offset.x) >> self.scaleIndex) - self.saved_data.arrayImagesSize[self.scaleIndex][y1_ind][x1_ind].x
        y2 = (int(y2_offset) >> self.scaleIndex) - self.saved_data.arrayImagesSize[self.scaleIndex][y1_ind][x1_ind].y
        x2 = (int(x2_offset) >> self.scaleIndex) - self.saved_data.arrayImagesSize[self.scaleIndex][y1_ind][x1_ind].x

        view = np.copy(self.sumImg[y1:y2, x1:x2, :])

        minimap = np.copy(self.minimapBase)

        # if self.savedData.rowCount > 0:
        #     self.imageView.offset.y = event.pos().y() * self.savedData.arrayImagesSize[0][-1][0].y
        #     / self.minimapLabel.size().height() - 0.5 * self.imLabel.size().height() / self.imageView.scale
        #     self.imageView.offset.x = event.pos().x() * self.savedData.arrayImagesSize[0][0][-1].x
        #     / self.minimapLabel.size().width() - 0.5 * self.imLabel.size().width() / self.imageView.scale
        # event.pos().y() * self.savedData.arrayImagesSize[0][-1][0].y / self.minimapLabel.size().height()
        # = self.imageView.offset.y + 0.5 * self.imLabel.size().height() / self.imageView.scale
        # event.pos().y() = self.minimapLabel.size().height() * (self.imageView.offset.y + 0.5
        # * self.imLabel.size().height() / self.imageView.scale) / self.savedData.arrayImagesSize[0][-1][0].y

        mini_koef = min(minimap.shape[0] / self.saved_data.arrayImagesSize[0][-1][0].y,
                       minimap.shape[1] / self.saved_data.arrayImagesSize[0][0][-1].x)
        cv2.rectangle(minimap,
                      (int(mini_koef * self.offset.x), int(mini_koef * self.offset.y)),
                      (int(mini_koef * x2_offset),
                       int(mini_koef * y2_offset)),
                      (255, 0, 0),
                      2)

        if self.scale != 1:
            return cv2.resize(view, (new_visible_size.width(), new_visible_size.height()), cv2.INTER_AREA), minimap

        return view, minimap


def numpy_q_image(image):
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
                    image.data, width, height, bytes_per_line, QImage.Format_RGB888
                )
            elif image.shape[2] == 4:
                height, width, channels = image.shape
                bytes_per_line = channels * width
                fmt = QImage.Format_ARGB32
                q_img = QImage(
                    image.data, width, height, bytes_per_line, QImage.Format_ARGB32
                )
    return q_img


#  для размещения картинок
"""class ClickedLabel(QLabel):
    def __init__(self):
        super().__init__()
    mouseReleased = pyqtSignal()
    resized = pyqtSignal()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.mouseReleased().emit()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.resized.emit()"""


#Окно нового сканирования
class ScanWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def open_file(self):
        return


class ImageStatus(Enum):
    Idle = 0
    Move = 1
    MinimapMove = 2


#Главное окно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.savedData = SavedData("")
        self.initUI()
        self.EXTRACT_TEMP_FOLDER = os.path.join(tempfile.gettempdir(), "Micros")
        self.EXTRACT_TEMP_SUBFOLDER = ""
        self.imageView = ImageView(self.savedData)
        if not os.path.exists(self.EXTRACT_TEMP_FOLDER):
            os.mkdir(self.EXTRACT_TEMP_FOLDER)
        for folder in os.listdir(self.EXTRACT_TEMP_FOLDER):
            if os.path.isdir(os.path.join(self.EXTRACT_TEMP_FOLDER, folder)):
                sett_file = os.path.join(self.EXTRACT_TEMP_FOLDER, folder, "settings.xml")
                if os.path.exists(sett_file):
                    create_dt = datetime.datetime.fromtimestamp(os.path.getctime(sett_file))
                    if (datetime.datetime.now() - create_dt).total_seconds() > 120.0:
                        shutil.rmtree(os.path.join(self.EXTRACT_TEMP_FOLDER, folder))
        self.startMousePos = Point()
        self.status = ImageStatus.Idle
        self.fileName = ""
        self.modified = False
        self.minScale = 0.001
        self.maxScale = 10.0
        self.programSettings = ProgramSettings()

        self.configFilePath = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "Config.xml")
        self.loadConfig()

    def save_config(self):
        root = Xml.Element("Root")
        apptRC = Xml.Element("FullLoadImageMemoryLimit")
        apptRC.text = "1024*1024*1024"
        root.append(apptRC)
        tree = Xml.ElementTree(root)
        with open(self.configFilePath, "w") as fobj:
            tree.write(self.configFilePath)

    def loadConfig(self):
        if os.path.exists(self.configFilePath):
            with open(self.configFilePath) as fobj:
                xml = fobj.read()
                root = etree.fromstring(xml)
                for appt in root.getchildren():
                    if appt.tag == "FullLoadImageMemoryLimit":
                        mem_limit_text = appt.text
                        for ch in "xXхХ":
                            mem_limit_text = mem_limit_text.replace(ch, "*")
                        self.programSettings.fullLoadImageMemoryLimit = eval(mem_limit_text)
        else:
            self.save_config()
        return

    def image_move(self, pos = QPoint()):
        if self.status == ImageStatus.Move:
            self.imageView.offset.x = self.startMousePos.x - pos.x() / self.imageView.scale
            self.imageView.offset.y = self.startMousePos.y - pos.y() / self.imageView.scale
            self.setNewView()

    # Обработчики событий формы и ее компонентов
    def eventFilter(self, obj, event):
        if obj is self.imLabel:
            if event.type() == QEvent.MouseButtonPress:
                # print('mouse press event = ', event.pos())
                if self.status == ImageStatus.Idle:
                    self.status = ImageStatus.Move
                    self.startMousePos.x = self.imageView.offset.x + event.pos().x() / self.imageView.scale
                    self.startMousePos.y = self.imageView.offset.y + event.pos().y() / self.imageView.scale
            elif event.type() == QEvent.MouseButtonRelease:
                # print('mouse release event = ', event.pos())
                if self.status == ImageStatus.Move:
                    self.image_move(event.pos())
                self.status = ImageStatus.Idle
            elif event.type() == QEvent.MouseMove:
                # self.setWindowTitle(str(event.pos()))
                if self.status == ImageStatus.Move:
                    self.image_move(event.pos())
            elif event.type() == QEvent.Wheel:
                # self.setWindowTitle(str(event.angleDelta().y()) + "; pos: " + str(event.pos()))
                if event.modifiers() & Qt.ControlModifier:
                    new_scale = self.scaleEdit.value() * (1000 + event.angleDelta().y()) / 1000
                elif event.modifiers() & Qt.ShiftModifier:
                    new_scale = self.scaleEdit.value() * (6000 + event.angleDelta().y()) / 6000
                else:
                    new_scale = self.scaleEdit.value() * (2500 + event.angleDelta().y()) / 2500
                if new_scale > self.maxScale:
                    new_scale = self.maxScale
                    self.imageView.scale = new_scale
                if new_scale < self.minScale:
                    new_scale = self.minScale
                    self.imageView.scale = new_scale

                self.imageView.offset.x += event.pos().x() * (new_scale - self.imageView.scale) / (new_scale * self.imageView.scale)
                self.imageView.offset.y += event.pos().y() * (new_scale - self.imageView.scale) / (new_scale * self.imageView.scale)
                self.scaleEdit.setValue(new_scale)
                self.setNewView()
            elif event.type() == QEvent.Resize:
                self.resized()
        elif obj is self.minimapLabel:
            if event.type() == QEvent.MouseButtonPress:
                # print('mouse press event = ', event.pos())
                self.status = ImageStatus.MinimapMove
                if self.savedData.rowCount > 0:
                    self.imageView.offset.y = event.pos().y() * self.savedData.arrayImagesSize[0][-1][0].y / self.minimapLabel.size().height() - 0.5 * self.imLabel.size().height() / self.imageView.scale
                    self.imageView.offset.x = event.pos().x() * self.savedData.arrayImagesSize[0][0][-1].x / self.minimapLabel.size().width() - 0.5 * self.imLabel.size().width() / self.imageView.scale
                    self.setNewView()
            elif event.type() == QEvent.MouseButtonRelease:
                self.status = ImageStatus.Idle
            elif event.type() == QEvent.MouseMove:
                # self.setWindowTitle(str(event.pos()))
                self.status = ImageStatus.MinimapMove
                if self.savedData.rowCount > 0:
                    self.imageView.offset.y = event.pos().y() * self.savedData.arrayImagesSize[0][-1][0].y / self.minimapLabel.size().height() - 0.5 * self.imLabel.size().height() / self.imageView.scale
                    self.imageView.offset.x = event.pos().x() * self.savedData.arrayImagesSize[0][0][-1].x / self.minimapLabel.size().width() - 0.5 * self.imLabel.size().width() / self.imageView.scale
                    self.setNewView()
        elif obj is self.rightDocWidget:
            if event.type() == QEvent.Hide:
                self.viewMenuMainPanel.setChecked(False)
        return QMainWindow.eventFilter(self, obj, event)

    def resized(self):
        if self.savedData and self.savedData.rowCount > 0:
            self.minScale = max(self.imLabel.size().height() / self.savedData.arrayImagesSize[0][-1][0].y, self.imLabel.size().width() / self.savedData.arrayImagesSize[0][0][-1].x)
            if self.scaleEdit.value() < self.minScale:
                self.scaleEdit.setValue(self.minScale)
        self.setNewView()

    def closeEvent(self, event):
        if self.fileName and self.modified:
            dlgResult = QMessageBox.question(self, "Confirm Dialog", "Есть несохраненные изменения. Хотите их сохранить перед закрытием?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if dlgResult == QMessageBox.Yes:
                self.saveFile()
            elif dlgResult == QMessageBox.Cancel:
                event.ignore()
                return
        if os.path.exists(self.EXTRACT_TEMP_SUBFOLDER):
            shutil.rmtree(self.EXTRACT_TEMP_SUBFOLDER)

    def saveFileAss(self):
        self.saveFile(True)

    def saveFile(self, saveDlg = False):
        if not self.EXTRACT_TEMP_SUBFOLDER:
            return
        if self.savedData.rowCount < 1 or self.savedData.colCount < 1:
            return
        if saveDlg or not self.fileName:
            sel_filter = "Microscope scans (*.misc)"
            a = QFileDialog.getSaveFileName(self, "Выберите место сохранения файла", "/", "All files (*.*);;Microscope scans (*.misc)", sel_filter)
            if len(a[0]) > 0:
                ext = os.path.splitext(a[0])
                if ext[1] == ".misc":
                    self.fileName = a[0]
                else:
                    self.fileName = ext[0] + ".misc"
                if os.path.exists(self.fileName):
                    dlgResult = QMessageBox.question(self, "Confirm Dialog", "Файл уже существует. Хотите его перезаписать? Это удалит данные в нем", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if dlgResult == QMessageBox.No:
                        return

            else:
                return

        if self.savedData.save_to_file_xml(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, "settings.xml")):
            self.savedData.folder = self.EXTRACT_TEMP_SUBFOLDER
        else:
            err_dlg = QErrorMessage()
            err_dlg.setWindowTitle("Ошибка")
            err_dlg.showMessage("Произошла непредвиденная ошибка записи файла!")
            return

        z = zipfile.ZipFile(self.fileName, 'w')
        for root, dirs, files in os.walk(self.EXTRACT_TEMP_SUBFOLDER):
            for file in files:
                if file:
                    z.write(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, file), file, compress_type=zipfile.ZIP_DEFLATED)
        self.modified = False
        self.setWindowTitle("Micros - " + self.fileName)
        dlgResult = QMessageBox.question(self, "Info Dialog", "Файл сохранен", QMessageBox.Ok, QMessageBox.Ok)

    def openFile(self):
        sel_filter = "Microscope scans (*.misc)"
        if self.fileName and self.modified:
            dlg_result = QMessageBox.question(self,
                                             "Confirm Dialog",
                                             "Есть несохраненные изменения в текущем файле. Хотите сперва их сохранить?",
                                             QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                             QMessageBox.Yes)
            if dlg_result == QMessageBox.Yes:
                self.saveFile()
            elif dlg_result == QMessageBox.Cancel:
                return

        a = QFileDialog.getOpenFileName(self,
                                        "Выберите файл изображения",
                                        "/",
                                        "All files (*.*);;Microscope scans (*.misc)",
                                        sel_filter)
        if len(a[0]) > 0:
            self.EXTRACT_TEMP_SUBFOLDER = os.path.join(self.EXTRACT_TEMP_FOLDER, str(uuid.uuid4()))
            os.mkdir(self.EXTRACT_TEMP_SUBFOLDER)
            z = zipfile.PyZipFile(a[0])
            z.extractall(self.EXTRACT_TEMP_SUBFOLDER)
            sum_size = 0
            for f in os.listdir(self.EXTRACT_TEMP_SUBFOLDER):
                if os.path.isfile(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, f)):
                    sum_size += os.path.getsize(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, f))

            if self.savedData.load_from_file_xml(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, "settings.xml")):
                self.savedData.folder = self.EXTRACT_TEMP_SUBFOLDER
                self.savedData.prepare_scans()
                path_to_minimap = os.path.join(self.EXTRACT_TEMP_SUBFOLDER, "mini.jpg")
                if os.path.exists(path_to_minimap):
                    self.imageView.minimapBase = cv2.imread(path_to_minimap, cv2.IMREAD_COLOR)[:, :, ::-1]
                self.fileName = a[0]
                self.modified = False
                self.savedData.set_all_image_in_memory(sum_size <= self.programSettings.fullLoadImageMemoryLimit)
                self.servicesMenuAllInMemory.setChecked(sum_size <= self.programSettings.fullLoadImageMemoryLimit)
                self.resized()
                self.setWindowTitle("Micros - " + self.fileName)
            else:
                err_dlg = QErrorMessage()
                err_dlg.setWindowTitle("Ошибка")
                err_dlg.showMessage("Произошла непредвиденная ошибка чтения файла. Возможно открываемый файл имеет неподходячщий формат или поврежден!")

    def minimap_check_box_changed(self, state):
        if state == Qt.Checked:
            self.minimapLabel.show()
        else:
            self.minimapLabel.hide()

    def grid_check_box_changed(self, state):
        if state == Qt.Checked:
            self.minimapLabel.show()
        else:
            self.minimapLabel.hide()

    def prepareScans(self):
        self.modified = self.savedData.prepare_scans(True)

    def btn31_Click(self):
        koefSize = 0.30
        imgSize = Size()
        imgSize.width = 3000
        imgSize.height = 4000
        conArea = Rect()
        conArea.x = 1050
        conArea.y = 1400
        conArea.width = 900
        conArea.height = 1200

        sumImg = np.arange(0)
        for i in range (5):
            y1 = conArea.y
            if i == 0:
                y1 = 0
            y2 = conArea.y + conArea.height
            if i == 4:
                y2 = imgSize.height
            rowImg = np.arange(0)
            for j in range (11):
                x1 = conArea.x
                if j == 0:
                    x1 = 0
                x2 = conArea.x + conArea.width
                if j == 10:
                    x2 = imgSize.width
                fileName = "/home/krasnov/IRZProjects/python_micro/data/38fb1a73-5005-4eda-9fe7-7975fa31e11e/S_" + str(i+1) + "_" + str(j+1) + ".jpg";
                img = cv2.imread(fileName)
                img2 = np.copy(img[y1:y2, x1:x2, :])
                if rowImg.size == 0:
                    rowImg = np.copy(img2)
                else:
                    rowImg = np.concatenate((rowImg, img2), axis=1)

            if sumImg.size == 0:
                sumImg = np.copy(rowImg)
            else:
                sumImg = np.concatenate((sumImg, rowImg), axis=0)

        cv2.imwrite("/home/krasnov/IRZProjects/python_micro/data/38fb1a73-5005-4eda-9fe7-7975fa31e11e/sumImg.jpg", sumImg)

    def setNewView(self):
        if not self.savedData or self.savedData.rowCount == 0:
            return
        mainImg, miniImg = self.imageView.get_view(self.scaleEdit.value(), self.imLabel.size())
        qImg = numpy_q_image(mainImg)
        pixmap = QtGui.QPixmap.fromImage(qImg)
        self.imLabel.setPixmap(pixmap)
        qMiniImg = numpy_q_image(miniImg)
        pixmapMini = QtGui.QPixmap.fromImage(qMiniImg)
        self.minimapLabel.setPixmap(pixmapMini)

    def scaleEdit_Change(self):
        self.setNewView()

    def viewMenuMainPanel_Click(self):
        if self.viewMenuMainPanel.isChecked():
            self.rightDocWidget.show()
        else:
            self.rightDocWidget.hide()

    def servicesMenuSettings_Click(self):
        settingsDialog = SettingsDialog()
        settingsDialog.setAttribute(Qt.WA_DeleteOnClose)
        settingsDialog.exec()

    def servicesMenuAllInMemory_Click(self):
        self.savedData.set_all_image_in_memory(self.servicesMenuAllInMemory.isChecked())
        self.resized()


    def initUI(self):
        self.setWindowTitle('Micros')
        # Основное меню
        menuBar = self.menuBar()
        # Меню "Файл"
        fileMenu = menuBar.addMenu("&Файл")
        fileMenuANew = QAction("&Новый", self)
        fileMenuANew.setShortcut("Ctrl+N")
        fileMenuANew.setStatusTip("Новое сканирование")
        #fileMenuANew.triggered.connect(self.close)
        fileMenu.addAction(fileMenuANew)
        fileMenu.addSeparator()
        fileMenuAOpen = QAction("&Открыть", self)
        fileMenuAOpen.setShortcut("Ctrl+O")
        fileMenuAOpen.setStatusTip("Открыть существующее изображение")
        fileMenuAOpen.triggered.connect(self.openFile)
        fileMenu.addAction(fileMenuAOpen)
        fileMenu.addSeparator()
        fileMenuASave = fileMenu.addAction("&Сохранить")
        fileMenuASave.setShortcut("Ctrl+S")
        fileMenuASave.setStatusTip("Сохранить изменения")
        fileMenuASave.triggered.connect(self.saveFile)
        fileMenuASaveAss = fileMenu.addAction("Сохранить как...")
        fileMenuASaveAss.setShortcut("Ctrl+Shift+S")
        fileMenuASaveAss.setStatusTip("Сохранить текущее изображение в другом файле...")
        fileMenuASaveAss.triggered.connect(self.saveFileAss)
        fileMenu.addSeparator()
        fileMenuAExit = QAction("&Выйти", self)
        fileMenuAExit.setShortcut("Ctrl+Q")
        fileMenuAExit.setStatusTip("Закрыть приложение")
        fileMenuAExit.triggered.connect(self.close)
        fileMenu.addAction(fileMenuAExit)
        menuBar.addMenu(fileMenu)
        # Меню "Вид"
        viewMenu = menuBar.addMenu("&Вид")
        self.viewMenuMainPanel = QAction("Основная &панель", self)
        self.viewMenuMainPanel.setShortcut("Ctrl+T")
        self.viewMenuMainPanel.setStatusTip("Отображать основную панель")
        self.viewMenuMainPanel.triggered.connect(self.viewMenuMainPanel_Click)
        self.viewMenuMainPanel.setCheckable(True)
        self.viewMenuMainPanel.setChecked(True)
        viewMenu.addAction(self.viewMenuMainPanel)
        menuBar.addMenu(viewMenu)
         # Меню "Настройки"
        servicesMenu = menuBar.addMenu("&Сервис")
        self.servicesMenuAllInMemory = QAction("&Буферизировать изображение", self)
        self.servicesMenuAllInMemory.setShortcut("Ctrl+M")
        self.servicesMenuAllInMemory.setStatusTip("Разместить все части изображения в памяти, что увеличит скорость навигации по нему")
        self.servicesMenuAllInMemory.triggered.connect(self.servicesMenuAllInMemory_Click)
        self.servicesMenuAllInMemory.setCheckable(True)
        self.servicesMenuAllInMemory.setChecked(False)
        servicesMenu.addAction(self.servicesMenuAllInMemory)
        servicesMenu.addSeparator()
        self.servicesMenuSettings = QAction("Настройки", self)
        self.servicesMenuSettings.setStatusTip("Изменить основные настройки программы")
        self.servicesMenuSettings.triggered.connect(self.servicesMenuSettings_Click)
        servicesMenu.addAction(self.servicesMenuSettings)
        menuBar.addMenu(servicesMenu)
        #self.viewMenuMainPanel = QAction("Основная &панель", self)
        #self.viewMenuMainPanel.setShortcut("Ctrl+T")
        #self.viewMenuMainPanel.setStatusTip("Отображать основную панель")
        #self.viewMenuMainPanel.triggered.connect(self.viewMenuMainPanel_Click)
        #self.viewMenuMainPanel.setCheckable(True)
        #self.viewMenuMainPanel.setChecked(True)
        #viewMenu.addAction(self.viewMenuMainPanel)



        # Элементы формы

        # Левые элементы
        """leftLayout = QVBoxLayout()
        btn1 = QPushButton("Load")
        btn1.setMaximumWidth(150)
        leftLayout.addWidget(btn1)
        leftLayout.addStretch(0)
        mainLayout.addLayout(leftLayout)"""

        # Центральные элементы, включая изображение
        mainLayout = QHBoxLayout(self)
        mainWidget = QWidget(self)
        #mainWidget.setLayout(mainLayout)
        centralLayout = QVBoxLayout()
        mainWidget.setLayout(centralLayout)
        #self.imLabel = ClickedLabel()
        self.imLabel = QLabel()

        #img2 = cv2.imread("/home/krasnov/Pictures/схема_Уберподробно/beforeRotate/2_7.jpg", cv2.IMREAD_COLOR)[:, :, ::-1]
        #height, width = img.shape[:2]
        #start_row, strt_col = int(height * 0.00), int(width * 0.00)
        #end_row, end_col = int(height * 1.00), int(width * 1.00)
        #croped = img[start_row:end_row, strt_col:end_col].copy()
        """img = cv2.imread("/home/krasnov/IRZProjects/python_micro/data/38fb1a73-5005-4eda-9fe7-7975fa31e11e/S_3_7.jpg", cv2.IMREAD_COLOR)[:, :, ::-1]
        croped = img.copy()
        qImg = numpyQImage(croped)
        pixmap = QtGui.QPixmap.fromImage(qImg)
        self.imLabel.setPixmap(pixmap)"""
        #pixmap = pixmap.scaled(self.imLabel.size(), Qt.KeepAspectRatio)
        #imQ = QImage(img.data,img.cols,img.cols,QImage.Format_Grayscale16)
        #pixmap = QPixmap("/home/krasnov/Pictures/P_20191028_093917.jpg")
        #pixmap = QPixmap.fromImage(imQ)


        #self.imLabel.setMaximumSize(1200, 800)
        #self.imLabel.setFixedSize(1200, 800)
        #self.imLabel.setAlignment(Qt.AlignCenter)
        self.imLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.imLabel.setStyleSheet("border: 1px solid red")
        #self.imLabel.mouseReleased.connect(self.imLabel_MouseReleased)
        #self.imLabel.resized.connect(self.imLabel_Resize)
        self.imLabel.installEventFilter(self)

        #self.setWindowTitle(str(self.imLabel.size().width()) + "x" + str(self.imLabel.size().height()))
        #self.setWindowTitle(str(random.randint(1,44)))

        centralLayout.addWidget(self.imLabel)

        minimapLayout = QGridLayout()
        self.imLabel.setLayout(minimapLayout)

        self.minimapLabel = QLabel()
        #imgMini = cv2.imread("/home/krasnov/IRZProjects/python_micro/data/38fb1a73-5005-4eda-9fe7-7975fa31e11e/mini.jpg", cv2.IMREAD_COLOR)[:, :, ::-1]
        #cropedMini = imgMini.copy()
        #qImgMini = numpyQImage(cropedMini)
        #pixmapMini = QtGui.QPixmap.fromImage(qImgMini)
        #pixmapMini = pixmapMini.scaled(self.minimapLabel.size(), Qt.KeepAspectRatio)

        #self.minimapLabel.setPixmap(pixmapMini)
        #self.minimapLabel.setFixedSize(pixmapMini.size())
        self.minimapLabel.installEventFilter(self)

        minimapLayout.setRowStretch(0,1)
        minimapLayout.setColumnStretch(0,1)
        minimapLayout.addWidget(self.minimapLabel, 1, 1)

        messageEdit = QTextEdit(self)
        messageEdit.setEnabled(False)

        messageEdit.setText("Hello, world!")

        messageEdit.setFixedHeight(100)
        messageEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        centralLayout.addWidget(messageEdit)
        #mainLayout.addLayout(centralLayout)
        # Правые элементы
        self.rightDocWidget = QDockWidget("Dock Widget", self)
        self.rightDocWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        rightLayout = QVBoxLayout(self)

        btn31 = QPushButton("MegaImg", self)
        btn31.clicked.connect(self.btn31_Click)
        btn32 = QPushButton("Prepare", self)
        btn32.clicked.connect(self.prepareScans)
        btn33 = QPushButton("View", self)
        rightLayout.addWidget(btn31)
        rightLayout.addWidget(btn32)
        rightLayout.addWidget(btn33)

        minimap_check_box = QCheckBox("Мини-изображение", self)
        minimap_check_box.stateChanged.connect(self.minimap_check_box_changed)
        minimap_check_box.setCheckState(Qt.Checked)
        rightLayout.addWidget(minimap_check_box)

        grid_check_box = QCheckBox("Сетка", self)
        grid_check_box.stateChanged.connect(self.grid_check_box_changed)
        grid_check_box.setCheckState(Qt.Checked)
        rightLayout.addWidget(grid_check_box)

        rightLayout.addSpacing(50)

        labScale = QLabel("Увеличение")
        self.scaleEdit = QDoubleSpinBox()
        self.scaleEdit.setMinimum(0.001)
        self.scaleEdit.setMaximum(10.0)
        self.scaleEdit.setValue(1.0)
        self.scaleEdit.setSingleStep(0.01)
        self.scaleEdit.setDecimals(3)
        self.scaleEdit.valueChanged.connect(self.scaleEdit_Change)
        rightLayout.addWidget(labScale)
        rightLayout.addWidget(self.scaleEdit)

        rightLayout.addStretch(0)

        rightDockWidgetContents = QWidget()
        rightDockWidgetContents.setLayout(rightLayout)
        #self.rightDocWidget.setLayout(rightLayout)
        self.rightDocWidget.setWidget(rightDockWidgetContents)
        self.rightDocWidget.installEventFilter(self)

        #mainLayout.addLayout(rightLayout)


        self.setCentralWidget(mainWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.rightDocWidget)

        self.statusBar().setStatusTip("Ready")

        self.resize(1280, 720)
        self.move(300, 300)
        self.setMinimumSize(800, 600)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
