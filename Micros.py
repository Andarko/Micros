import cv2
import sys
import datetime
import time
import uuid
import shutil
from enum import Enum
import numpy as np
import os.path
import tempfile
import zipfile
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction
from PyQt5.QtWidgets import QTextEdit, QSizePolicy, QGridLayout, QErrorMessage, QCheckBox
from PyQt5.QtWidgets import QDoubleSpinBox, QMessageBox, QDockWidget
from PyQt5.QtGui import QImage
import PyQt5.QtGui as QtGui
from PyQt5.QtCore import Qt, QSize, QEvent, QPoint
from lxml import etree

from SettingsDialog import SettingsDialog, ProgramSettings
import xml.etree.ElementTree as XmlET
import scan
import random


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
                                                           prefix + str(i+1) + "_" + str(j+1) + ".jpg")))
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
            # if i == 0:
            #     y1 = 0
            y2 = self.connectionArea.y + self.connectionArea.height
            # if i == self.rowCount - 1:
            #     y2 = self.imgSize.height

            minimap_row = np.zeros(0)
            for j in range(self.colCount):
                img_p = np.zeros(0)
                # Подготовка основных (детализированных) изображений
                if (replace or not os.path.exists(os.path.join(self.folder,
                                                               "P_" + str(i+1) + "_" + str(j+1) + ".jpg"))) \
                        and os.path.exists(os.path.join(self.folder, "S_" + str(i+1) + "_" + str(j+1) + ".jpg")):
                    x1 = self.connectionArea.x
                    # if j == 0:
                    #     x1 = 0
                    x2 = self.connectionArea.x + self.connectionArea.width
                    # if j == self.colCount - 1:
                    #     x2 = self.imgSize.width
                    img_s = cv2.imread(os.path.join(self.folder, "S_" + str(i+1) + "_" + str(j+1) + ".jpg"))
                    img_p = np.copy(img_s[y1:y2, x1:x2, :])
                    cv2.imwrite(os.path.join(self.folder, "P_" + str(i+1) + "_" + str(j+1) + ".jpg"), img_p)
                    modified = True
                if img_p.shape[0] == 0:
                    img_p = cv2.imread(os.path.join(self.folder, "P_" + str(i+1) + "_" + str(j+1) + ".jpg"))
                if img_p.shape[0] == 0:
                    continue
                # Подготовка обрезанных изображений пониженного качества, в т.ч. миникарты
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

    # сохранение данных в XML
    def save_to_file_xml(self, xml_file):
        # noinspection PyBroadException
        try:
            root = XmlET.Element("Root")
            app_rc = XmlET.Element("RowCount")
            app_rc.text = str(self.rowCount)
            root.append(app_rc)
            app_cc = XmlET.Element("ColCount")
            app_cc.text = str(self.colCount)
            root.append(app_cc)
            app_i = XmlET.Element("Image")
            root.append(app_i)
            form = XmlET.SubElement(app_i, "Format")
            form.text = self.format
            # isAllImageInMemory = xml.SubElement(app_i, "AllImageInMemory")
            # isAllImageInMemory.text = str(self.allImageInMemory)
            img_size = XmlET.SubElement(app_i, "ImgSize")
            is_width = XmlET.SubElement(img_size, "Width")
            is_width.text = str(self.imgSize.width)
            is_height = XmlET.SubElement(img_size, "Height")
            is_height.text = str(self.imgSize.height)
            con_area = XmlET.SubElement(app_i, "ConnectionArea")
            ca_x = XmlET.SubElement(con_area, "X")
            ca_x.text = str(self.connectionArea.x)
            ca_y = XmlET.SubElement(con_area, "Y")
            ca_y.text = str(self.connectionArea.y)
            ca_width = XmlET.SubElement(con_area, "Width")
            ca_width.text = str(self.connectionArea.width)
            ca_height = XmlET.SubElement(con_area, "Height")
            ca_height.text = str(self.connectionArea.height)
            tree = XmlET.ElementTree(root)
            # with open(xml_file, "w") as f_obj:
            with open(xml_file, "w"):
                tree.write(xml_file)
            return True
        except Exception:
            return False

    # Загрузка данных из XML
    def load_from_file_xml(self, xml_file):
        try:
            with open(xml_file) as f_obj:
                xml = f_obj.read()
            root = etree.fromstring(xml)
            for section in root.getchildren():
                if section.tag == "RowCount":
                    self.rowCount = int(section.text)
                elif section.tag == "ColCount":
                    self.colCount = int(section.text)
                elif section.tag == "Image":
                    for elem in section.getchildren():
                        if elem.tag == "Format":
                            self.format = section.text
                        # elif elem.tag == "AllImageInMemory":
                        #    self.allImageInMemory = bool(section.text)
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
            for k in range(3):
                array_area = []
                y = 0
                for i in range(self.rowCount + 1):
                    array_row = []
                    x = 0
                    # if i == 0 or i == self.rowCount - 1:
                    #     dy = self.imgSize.height - self.connectionArea.y
                    if i == self.rowCount:
                        dy = 0
                    else:
                        dy = self.connectionArea.height
                    if k > 0:
                        dy >>= k
                    for j in range(self.colCount + 1):
                        # if j == 0 or j == self.colCount - 1:
                        #     dx = self.imgSize.width - self.connectionArea.x
                        if j == self.colCount:
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
        # self.imgData = np.zero((self.savedData.rowCount, self.savedData.colCount))
        self.sumImg = np.empty(0)
        self.curRect = Rect(-1, -1, 0, 0)

    # Легкий вариант получения сшитого изображения простым сшитием всех кусков
    def easy_merge(self, new_scale_index=0, new_rect=Rect()):
        prefix = "P"
        if new_scale_index > 0:
            prefix += str(new_scale_index)
        prefix += "_"
        self.saved_data_clear()
        self.sumImg = np.zeros(0, dtype=np.uint8)
        for i in range(new_rect.y, new_rect.y + new_rect.height):
            row_img = np.zeros(0, dtype=np.uint8)
            for j in range(new_rect.x, new_rect.x + new_rect.width):
                if self.saved_data.allImageInMemory:
                    img = self.saved_data.arrayLoadImages[new_scale_index][i][j]
                else:
                    img = cv2.imread(os.path.join(self.saved_data.folder,
                                                  prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))
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
            intersect_rect.width = min(self.curRect.x + self.curRect.width, new_rect.x
                                       + new_rect.width) - intersect_rect.x
            intersect_rect.height = min(self.curRect.y + self.curRect.height, new_rect.y
                                        + new_rect.height) - intersect_rect.y

        if intersect_rect.width <= 0 or intersect_rect.height <= 0:
            # Отрисовываем соединенную картинку простым способом
            self.easy_merge(new_scale_index, new_rect)
        elif new_rect.width > 0 and new_rect.height > 0:
            # 1. Вырезаем видимую часть старого изображения
            first_area_of_intersect_rect = \
                self.saved_data.arrayImagesSize[new_scale_index][intersect_rect.y][intersect_rect.x]
            last_area_of_intersect_rect = \
                self.saved_data.arrayImagesSize[new_scale_index][intersect_rect.y + intersect_rect.height
                                                                 - 1][intersect_rect.x + intersect_rect.width - 1]
            first_area_of_current_rect = \
                self.saved_data.arrayImagesSize[new_scale_index][self.curRect.y][self.curRect.x]
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
                                                      prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))
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
                                                      prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))
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
                                                      prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))
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
                                                      prefix + str(i + 1) + "_" + str(j + 1) + ".jpg"))
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

        # Если видимая область сшитого изображения выходит за его пределы - возвращаем видимую область в пределы
        if self.offset.y + new_visible_size.height() / new_scale > self.saved_data.arrayImagesSize[0][-1][0].y:
            self.offset.y = self.saved_data.arrayImagesSize[0][-1][0].y - new_visible_size.height() / new_scale
        if self.offset.y < 0:
            self.offset.y = 0
        if self.offset.x + new_visible_size.width() / new_scale > self.saved_data.arrayImagesSize[0][0][-1].x:
            self.offset.x = self.saved_data.arrayImagesSize[0][0][-1].x - new_visible_size.width() / new_scale
        if self.offset.x < 0:
            self.offset.x = 0
        # Проверим сначала, как изменился масштаб, не надо ли загрузить изображения другого качества
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
        # Получение первых и последних индексов изображений, из которых нужно сшивать итоговое изображение
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

        y1 = ((int(self.offset.y) >> self.scaleIndex)
              - self.saved_data.arrayImagesSize[self.scaleIndex][y1_ind][x1_ind].y)
        x1 = ((int(self.offset.x) >> self.scaleIndex)
              - self.saved_data.arrayImagesSize[self.scaleIndex][y1_ind][x1_ind].x)
        y2 = ((int(y2_offset) >> self.scaleIndex)
              - self.saved_data.arrayImagesSize[self.scaleIndex][y1_ind][x1_ind].y)
        x2 = ((int(x2_offset) >> self.scaleIndex)
              - self.saved_data.arrayImagesSize[self.scaleIndex][y1_ind][x1_ind].x)

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

        mini_rate = min(minimap.shape[0] / self.saved_data.arrayImagesSize[0][-1][0].y,
                        minimap.shape[1] / self.saved_data.arrayImagesSize[0][0][-1].x)
        cv2.rectangle(minimap,
                      (int(mini_rate * self.offset.x), int(mini_rate * self.offset.y)),
                      (int(mini_rate * x2_offset),
                       int(mini_rate * y2_offset)),
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
                    # image.data, width, height, bytes_per_line, QImage.Format_RGB888
                    image.data, width, height, bytes_per_line, QImage.Format_BGR888
                )
            elif image.shape[2] == 4:
                height, width, channels = image.shape
                bytes_per_line = channels * width
                q_img = QImage(
                    # image.data, width, height, bytes_per_line, QImage.Format_ARGB32
                    image.data, width, height, bytes_per_line, QImage.Format_BGR888
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


# Окно нового сканирования
# class ScanWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.initUI()
#
#     def open_file(self):
#         return


class ImageStatus(Enum):
    Idle = 0
    Move = 1
    MinimapMove = 2


# Главное окно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scan_window: scan.ScanWindow = None
        # self.scan_window.setAttribute(Qt.WA_DeleteOnClose)
        self.savedData = SavedData("")

        self.view_menu_main_panel = QAction()
        self.services_menu_all_in_memory = QAction()
        self.services_menu_settings = QAction()

        self.scale_edit = QDoubleSpinBox()
        self.im_label = QLabel()
        self.minimap_label = QLabel()
        self.right_doc_widget = QDockWidget("Инструменты", self)

        self.init_ui()

        self.EXTRACT_TEMP_FOLDER = os.path.join(tempfile.gettempdir(), "Micros")
        self.EXTRACT_TEMP_SUB_FOLDER = ""
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
        self.file_name = ""
        self.modified = False
        self.minScale = 0.001
        self.maxScale = 10.0
        self.programSettings = ProgramSettings()

        self.configFilePath = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "Config.xml")
        self.load_config()
        # self.dist_task()

    def dist_task(self):
        a = []
        k = 4
        N = 1000000
        for i in range(N):
            a.append((i, random.randint(-N, N)))
        t1 = datetime.datetime.now()
        # print(a)
        a.sort(key=lambda x: x[1])
        # print(a)
        # b = []
        # prev = 0
        # for aa in a:
        #     b.append(aa[1] - prev)
        #     prev = aa[1]
        # print(b)
        c = []
        # Основной цикл для обхода всех элементов
        for i in range(N):
            if i == 0:
                l_ind = -1
            else:
                l_ind = i
                # l_dist = b[l_ind]
                l_dist = a[l_ind][1] - a[l_ind - 1][1]

            if i >= N - 1:
                r_ind = -1
            else:
                r_ind = i + 1
                # r_dist = b[r_ind]
                r_dist = a[l_ind][1] - a[l_ind - 1][1]
            metric = 0
            for j in range(k):
                if (l_ind > 0 and l_dist <= r_dist) or r_ind < 0:
                    metric += l_dist
                    l_ind -= 1
                    # l_dist += b[l_ind]
                    l_dist += a[l_ind][1] - a[l_ind - 1][1]
                else:
                    metric += r_dist
                    r_ind += 1
                    if r_ind < N:
                        # r_dist += b[r_ind]
                        r_dist += a[l_ind][1] - a[l_ind - 1][1]
                    else:
                        r_ind = -1

            c.append(metric)
        # print(c)

        d = []
        for i in range(N):
            d.append(0)
        for i in range(N):
            d[a[i][0]] = c[i]


        # print(d)
        t2 = datetime.datetime.now()
        print(t2 - t1)
        self.close()

    def init_ui(self):
        self.setWindowTitle('Micros')
        # Основное меню
        menu_bar = self.menuBar()
        # Меню "Файл"
        file_menu = menu_bar.addMenu("&Файл")
        file_menu_a_new = QAction("&Новый", self)
        file_menu_a_new.setShortcut("Ctrl+N")
        file_menu_a_new.setStatusTip("Новое сканирование")
        file_menu_a_new.triggered.connect(self.new_scan)
        file_menu.addAction(file_menu_a_new)
        file_menu.addSeparator()
        file_menu_a_open = QAction("&Открыть", self)
        file_menu_a_open.setShortcut("Ctrl+O")
        file_menu_a_open.setStatusTip("Открыть существующее изображение")
        file_menu_a_open.triggered.connect(self.open_file)
        file_menu.addAction(file_menu_a_open)
        file_menu.addSeparator()
        file_menu_a_save = file_menu.addAction("&Сохранить")
        file_menu_a_save.setShortcut("Ctrl+S")
        file_menu_a_save.setStatusTip("Сохранить изменения")
        file_menu_a_save.triggered.connect(self.save_file)
        file_menu_a_save_ass = file_menu.addAction("Сохранить как...")
        file_menu_a_save_ass.setShortcut("Ctrl+Shift+S")
        file_menu_a_save_ass.setStatusTip("Сохранить текущее изображение в другом файле...")
        file_menu_a_save_ass.triggered.connect(self.save_file_ass)
        file_menu.addSeparator()
        file_menu_a_exit = QAction("&Выйти", self)
        file_menu_a_exit.setShortcut("Ctrl+Q")
        file_menu_a_exit.setStatusTip("Закрыть приложение")
        file_menu_a_exit.triggered.connect(self.close)
        file_menu.addAction(file_menu_a_exit)
        menu_bar.addMenu(file_menu)
        # Меню "Вид"
        view_menu = menu_bar.addMenu("&Вид")

        self.view_menu_main_panel.setText("Основная &панель")
        self.view_menu_main_panel.setShortcut("Ctrl+T")
        self.view_menu_main_panel.setStatusTip("Отображать основную панель")
        self.view_menu_main_panel.triggered.connect(self.view_menu_main_panel_click)
        self.view_menu_main_panel.setCheckable(True)
        self.view_menu_main_panel.setChecked(True)
        view_menu.addAction(self.view_menu_main_panel)
        menu_bar.addMenu(view_menu)
        # Меню "Настройки"
        services_menu = menu_bar.addMenu("&Сервис")
        self.services_menu_all_in_memory.setText("&Буферизировать изображение")
        self.services_menu_all_in_memory.setShortcut("Ctrl+M")
        self.services_menu_all_in_memory.setStatusTip("Разместить все части изображения в" +
                                                      " памяти для увеличения скорость навигации по нему")
        self.services_menu_all_in_memory.triggered.connect(self.services_menu_all_in_memory_click)
        self.services_menu_all_in_memory.setCheckable(True)
        self.services_menu_all_in_memory.setChecked(False)
        services_menu.addAction(self.services_menu_all_in_memory)
        services_menu.addSeparator()

        self.services_menu_settings.setText("Настройки")
        self.services_menu_settings.setStatusTip("Изменить основные настройки программы")
        self.services_menu_settings.triggered.connect(self.services_menu_settings_click)
        services_menu.addAction(self.services_menu_settings)
        menu_bar.addMenu(services_menu)

        # Центральные элементы, включая изображение
        main_widget = QWidget(self)
        central_layout = QVBoxLayout()
        main_widget.setLayout(central_layout)

        self.im_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.im_label.setStyleSheet("border: 1px solid red")
        self.im_label.installEventFilter(self)

        central_layout.addWidget(self.im_label)

        minimap_layout = QGridLayout()
        self.im_label.setLayout(minimap_layout)

        self.minimap_label.installEventFilter(self)

        minimap_layout.setRowStretch(0, 1)
        minimap_layout.setColumnStretch(0, 1)
        minimap_layout.addWidget(self.minimap_label, 1, 1)

        message_edit = QTextEdit(self)
        message_edit.setEnabled(False)

        message_edit.setText("Hello, world!")

        message_edit.setFixedHeight(100)
        message_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        central_layout.addWidget(message_edit)

        # Правые элементы
        self.right_doc_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        right_layout = QVBoxLayout(self)

        btn_export_img = QPushButton("Экспорт изображения", self)
        btn_export_img.clicked.connect(self.btn_export_img_click)
        right_layout.addWidget(btn_export_img)

        minimap_check_box = QCheckBox("Мини-изображение", self)
        minimap_check_box.stateChanged.connect(self.minimap_check_box_changed)
        minimap_check_box.setCheckState(Qt.Checked)
        right_layout.addWidget(minimap_check_box)

        grid_check_box = QCheckBox("Сетка", self)
        grid_check_box.stateChanged.connect(self.grid_check_box_changed)
        grid_check_box.setCheckState(Qt.Checked)
        right_layout.addWidget(grid_check_box)

        right_layout.addSpacing(50)

        lab_scale = QLabel("Увеличение")
        self.scale_edit.setMinimum(0.001)
        self.scale_edit.setMaximum(10.0)
        self.scale_edit.setValue(1.0)
        self.scale_edit.setSingleStep(0.01)
        self.scale_edit.setDecimals(3)
        self.scale_edit.valueChanged.connect(self.scale_edit_change)
        right_layout.addWidget(lab_scale)
        right_layout.addWidget(self.scale_edit)

        right_layout.addStretch(0)

        right_dock_widget_contents = QWidget()
        right_dock_widget_contents.setLayout(right_layout)
        # self.rightDocWidget.setLayout(right_layout)
        self.right_doc_widget.setWidget(right_dock_widget_contents)
        self.right_doc_widget.installEventFilter(self)

        self.setCentralWidget(main_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_doc_widget)

        self.statusBar().setStatusTip("Ready")

        self.resize(1280, 720)
        self.move(300, 300)
        self.setMinimumSize(800, 600)

        self.showMaximized()

    def save_config(self):
        root = XmlET.Element("Root")
        elem_full_load_img = XmlET.Element("FullLoadImageMemoryLimit")
        elem_full_load_img.text = "1024*1024*1024"
        root.append(elem_full_load_img)
        tree = XmlET.ElementTree(root)
        with open(self.configFilePath, "w"):
            tree.write(self.configFilePath)

    def load_config(self):
        if os.path.exists(self.configFilePath):
            with open(self.configFilePath) as f_obj:
                xml = f_obj.read()
                root = etree.fromstring(xml)
                for elem in root.getchildren():
                    if elem.tag == "FullLoadImageMemoryLimit":
                        mem_limit_text = elem.text
                        for ch in "xXхХ":
                            mem_limit_text = mem_limit_text.replace(ch, "*")
                        self.programSettings.fullLoadImageMemoryLimit = eval(mem_limit_text)
        else:
            self.save_config()
        return

    def image_move(self, pos=QPoint()):
        if self.status == ImageStatus.Move:
            self.imageView.offset.x = self.startMousePos.x - pos.x() / self.imageView.scale
            self.imageView.offset.y = self.startMousePos.y - pos.y() / self.imageView.scale
            self.set_new_view()

    # Обработчики событий формы и ее компонентов
    def eventFilter(self, obj, event):
        if obj is self.im_label:
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
                    new_scale = self.scale_edit.value() * (1000 + event.angleDelta().y()) / 1000
                elif event.modifiers() & Qt.ShiftModifier:
                    new_scale = self.scale_edit.value() * (6000 + event.angleDelta().y()) / 6000
                else:
                    new_scale = self.scale_edit.value() * (2500 + event.angleDelta().y()) / 2500
                if new_scale > self.maxScale:
                    new_scale = self.maxScale
                    self.imageView.scale = new_scale
                if new_scale < self.minScale:
                    new_scale = self.minScale
                    self.imageView.scale = new_scale

                self.imageView.offset.x += event.pos().x() * ((new_scale - self.imageView.scale)
                                                              / (new_scale * self.imageView.scale))
                self.imageView.offset.y += event.pos().y() * ((new_scale - self.imageView.scale)
                                                              / (new_scale * self.imageView.scale))
                self.scale_edit.setValue(new_scale)
                self.set_new_view()
            elif event.type() == QEvent.Resize:
                self.resized()
        elif obj is self.minimap_label:
            if event.type() == QEvent.MouseButtonPress:
                # print('mouse press event = ', event.pos())
                self.status = ImageStatus.MinimapMove
                if self.savedData.rowCount > 0:
                    self.imageView.offset.y = event.pos().y() * self.savedData.arrayImagesSize[0][-1][0].y
                    self.imageView.offset.y /= self.minimap_label.size().height()
                    self.imageView.offset.y -= 0.5 * self.im_label.size().height() / self.imageView.scale
                    self.imageView.offset.x = event.pos().x() * self.savedData.arrayImagesSize[0][0][-1].x
                    self.imageView.offset.x /= self.minimap_label.size().width()
                    self.imageView.offset.x -= 0.5 * self.im_label.size().width() / self.imageView.scale
                    self.set_new_view()
            elif event.type() == QEvent.MouseButtonRelease:
                self.status = ImageStatus.Idle
            elif event.type() == QEvent.MouseMove:
                # self.setWindowTitle(str(event.pos()))
                self.status = ImageStatus.MinimapMove
                if self.savedData.rowCount > 0:
                    self.imageView.offset.y = event.pos().y() * self.savedData.arrayImagesSize[0][-1][0].y
                    self.imageView.offset.y /= self.minimap_label.size().height()
                    self.imageView.offset.y -= 0.5 * self.im_label.size().height() / self.imageView.scale
                    self.imageView.offset.x = event.pos().x() * self.savedData.arrayImagesSize[0][0][-1].x
                    self.imageView.offset.x /= self.minimap_label.size().width()
                    self.imageView.offset.x -= 0.5 * self.im_label.size().width() / self.imageView.scale
                    self.set_new_view()
        elif obj is self.right_doc_widget:
            if event.type() == QEvent.Hide:
                self.view_menu_main_panel.setChecked(False)
        return QMainWindow.eventFilter(self, obj, event)

    def resized(self):
        if self.savedData and self.savedData.rowCount > 0:
            self.minScale = max(self.im_label.size().height() / self.savedData.arrayImagesSize[0][-1][0].y,
                                self.im_label.size().width() / self.savedData.arrayImagesSize[0][0][-1].x)
            if self.scale_edit.value() < self.minScale:
                self.scale_edit.setValue(self.minScale)
        self.set_new_view()

    def closeEvent(self, event):
        if self.file_name and self.modified:
            dlg_result = QMessageBox.question(self,
                                              "Confirm Dialog",
                                              "Есть несохраненные изменения. Хотите их сохранить перед закрытием?",
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                              QMessageBox.Yes)
            if dlg_result == QMessageBox.Yes:
                self.save_file()
            elif dlg_result == QMessageBox.Cancel:
                event.ignore()
                return
        if self.scan_window and not self.scan_window.test:
            # self.scan_window.thread_continuous.join()
            if self.scan_window.vidik.isRunning():
                self.scan_window.vidik.work = False
                self.scan_window.vidik.terminate()
            # self.scan_window.table_controller.thread_server.join()

            # if not self.scan_window.table_controller.thread_server.isRunning():
            print("thread_server terminate start")
            # self.scan_window.table_controller.thread_server.terminate()
            if not self.scan_window.test_only_camera:
                self.scan_window.table_controller.thread_server.work = False
                try_count = 0
                while not self.scan_window.table_controller.thread_server.stopped:
                    time.sleep(0.2)
                    try_count += 1
                    if try_count > 15:
                        break
            print("thread_server terminate end")

        if self.scan_window.timer_continuous.isActive():
            self.scan_window.timer_continuous.stop()
        if os.path.exists(self.EXTRACT_TEMP_SUB_FOLDER):
            shutil.rmtree(self.EXTRACT_TEMP_SUB_FOLDER)

    def prepare_to_close_file(self):
        if self.file_name and self.modified:
            dlg_result = QMessageBox.question(self,
                                              "Confirm Dialog",
                                              "Есть несохраненные изменения в текущем файле." +
                                              " Хотите сперва их сохранить?",
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                              QMessageBox.Yes)
            if dlg_result == QMessageBox.Yes:
                self.save_file()
            elif dlg_result == QMessageBox.Cancel:
                return False
        return True

    def new_scan(self):
        if self.prepare_to_close_file():
            if not self.scan_window:
                self.scan_window = scan.ScanWindow(self)
            self.scan_window.showMaximized()
            self.hide()

    def save_file_ass(self):
        self.save_file(True)

    def save_file(self, save_dlg=False):
        if not self.EXTRACT_TEMP_SUB_FOLDER:
            return
        if self.savedData.rowCount < 1 or self.savedData.colCount < 1:
            return
        if save_dlg or not self.file_name:
            a = QFileDialog.getSaveFileName(self, "Выберите место сохранения файла", "/",
                                            "All files (*.*);;Microscope scans (*.misc)", "Microscope scans (*.misc)")
            if len(a[0]) > 0:
                ext = os.path.splitext(a[0])
                if ext[1] == ".misc":
                    self.file_name = a[0]
                else:
                    self.file_name = ext[0] + ".misc"
                if os.path.exists(self.file_name):
                    dlg_result = QMessageBox.question(self, "Confirm Dialog",
                                                      "Файл уже существует. Хотите его перезаписать? " +
                                                      "Это удалит данные в нем",
                                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if dlg_result == QMessageBox.No:
                        return

            else:
                return

        if self.savedData.save_to_file_xml(os.path.join(self.EXTRACT_TEMP_SUB_FOLDER, "settings.xml")):
            self.savedData.folder = self.EXTRACT_TEMP_SUB_FOLDER
        else:
            err_dlg = QErrorMessage()
            err_dlg.setWindowTitle("Ошибка")
            err_dlg.showMessage("Произошла непредвиденная ошибка записи файла!")
            return

        z = zipfile.ZipFile(self.file_name, 'w')
        for root, dirs, files in os.walk(self.EXTRACT_TEMP_SUB_FOLDER):
            for file in files:
                if file:
                    z.write(os.path.join(self.EXTRACT_TEMP_SUB_FOLDER, file), file, compress_type=zipfile.ZIP_DEFLATED)
        self.modified = False
        self.setWindowTitle("Micros - " + self.file_name)
        QMessageBox.question(self, "Info Dialog", "Файл сохранен", QMessageBox.Ok, QMessageBox.Ok)

    def open_file(self, file_name=""):
        # sel_filter = "Microscope scans (*.misc)"
        # if self.file_name and self.modified:
        #     dlg_result = QMessageBox.question(self,
        #                                       "Confirm Dialog",
        #                                       "Есть несохраненные изменения в текущем файле." +
        #                                       " Хотите сперва их сохранить?",
        #                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
        #                                       QMessageBox.Yes)
        #     if dlg_result == QMessageBox.Yes:
        #         self.save_file()
        #     elif dlg_result == QMessageBox.Cancel:
        #         return
        if not file_name:
            if not self.prepare_to_close_file():
                return

            a = QFileDialog.getOpenFileName(self,
                                            "Выберите файл изображения",
                                            "/",
                                            "All files (*.*);;Microscope scans (*.misc)",
                                            "Microscope scans (*.misc)")
            file_name = a[0]
        if len(file_name) > 0:
            print(file_name)
            self.EXTRACT_TEMP_SUB_FOLDER = os.path.join(self.EXTRACT_TEMP_FOLDER, str(uuid.uuid4()))
            os.mkdir(self.EXTRACT_TEMP_SUB_FOLDER)
            z = zipfile.PyZipFile(file_name)
            z.extractall(self.EXTRACT_TEMP_SUB_FOLDER)
            sum_size = 0
            for f in os.listdir(self.EXTRACT_TEMP_SUB_FOLDER):
                if os.path.isfile(os.path.join(self.EXTRACT_TEMP_SUB_FOLDER, f)):
                    sum_size += os.path.getsize(os.path.join(self.EXTRACT_TEMP_SUB_FOLDER, f))

            if self.savedData.load_from_file_xml(os.path.join(self.EXTRACT_TEMP_SUB_FOLDER, "settings.xml")):
                self.savedData.folder = self.EXTRACT_TEMP_SUB_FOLDER
                self.savedData.prepare_scans()
                path_to_minimap = os.path.join(self.EXTRACT_TEMP_SUB_FOLDER, "mini.jpg")
                if os.path.exists(path_to_minimap):
                    self.imageView.minimapBase = cv2.imread(path_to_minimap, cv2.IMREAD_COLOR)
                self.file_name = file_name
                self.modified = False
                self.savedData.set_all_image_in_memory(sum_size <= self.programSettings.fullLoadImageMemoryLimit)
                self.services_menu_all_in_memory.setChecked(sum_size <= self.programSettings.fullLoadImageMemoryLimit)
                self.imageView.sumImg = np.empty(0)
                self.resized()
                self.setWindowTitle("Micros - " + self.file_name)
            else:
                err_dlg = QErrorMessage()
                err_dlg.setWindowTitle("Ошибка")
                err_dlg.showMessage("Произошла непредвиденная ошибка чтения файла. Возможно открываемый файл имеет " +
                                    "неподходячщий формат или поврежден!")

    def minimap_check_box_changed(self, state):
        if state == Qt.Checked:
            self.minimap_label.show()
        else:
            self.minimap_label.hide()

    def grid_check_box_changed(self, state):
        if state == Qt.Checked:
            self.minimap_label.show()
        else:
            self.minimap_label.hide()

    def prepare_scans(self):
        self.modified = self.savedData.prepare_scans(True)

    def btn_export_img_click(self):
        if not self.EXTRACT_TEMP_SUB_FOLDER:
            return
        if self.savedData.rowCount < 1 or self.savedData.colCount < 1:
            return

        a = QFileDialog.getSaveFileName(self, "Выберите место сохранения изображения", "/",
                                        "All files (*.*);;JPEG (*.jpg)", "JPEG (*.jpg)")
        if len(a[0]) > 0:
            ext = os.path.splitext(a[0])
            if ext[1] == ".jpg":
                image_file_name = a[0]
            else:
                image_file_name = ext[0] + ".jpg"
            if os.path.exists(image_file_name):
                dlg_result = QMessageBox.question(self, "Confirm Dialog",
                                                  "Файл уже существует. Хотите его перезаписать? " +
                                                  "Это удалит данные в нем",
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if dlg_result == QMessageBox.No:
                    return
            self.imageView.easy_merge(0, Rect(0, 0, self.savedData.colCount, self.savedData.rowCount))
            cv2.imwrite(image_file_name, self.imageView.sumImg)
            self.set_new_view()
        else:
            return

    def set_new_view(self):
        if not self.savedData or self.savedData.rowCount == 0:
            return
        main_img, mini_img = self.imageView.get_view(self.scale_edit.value(), self.im_label.size())
        q_img = numpy_q_image(main_img)
        pixmap = QtGui.QPixmap.fromImage(q_img)
        self.im_label.setPixmap(pixmap)
        q_mini_img = numpy_q_image(mini_img)
        pixmap_mini = QtGui.QPixmap.fromImage(q_mini_img)
        self.minimap_label.setPixmap(pixmap_mini)

    def scale_edit_change(self):
        self.set_new_view()

    def view_menu_main_panel_click(self):
        if self.view_menu_main_panel.isChecked():
            self.right_doc_widget.show()
        else:
            self.right_doc_widget.hide()

    @staticmethod
    def services_menu_settings_click():
        settings_dialog = SettingsDialog()
        settings_dialog.setAttribute(Qt.WA_DeleteOnClose)
        settings_dialog.exec()

    def services_menu_all_in_memory_click(self):
        self.savedData.set_all_image_in_memory(self.services_menu_all_in_memory.isChecked())
        self.resized()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
