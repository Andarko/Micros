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
from PyQt5.QtCore import Qt, QSize, QEvent, QPoint
from lxml import etree

from SettingsDialog import SettingsDialog, ProgramSettings
import xml.etree.ElementTree as xml


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
        #Изображения в памяти
        self.arrayLoadImages = []

    def setAllImageInMemory(self, newValue):
        self.allImageInMemory = newValue
        if newValue:
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
                        row.append(cv2.imread(os.path.join(self.folder, prefix + str(i+1) + "_" + str(j+1) + ".jpg"))[:, :, ::-1])
                    layer.append(row)
                self.arrayLoadImages.append(layer)
        else:
            self.arrayLoadImages = []

    # Подготовка обрезанных файлов изображения и уменьшенных файлов изображения
    def prepareScans(self, replace=False):
        minimap = np.zeros(0)
        minimapNeedCreate = replace or not os.path.exists(os.path.join(self.folder, "mini.jpg"))
        modiefed = minimapNeedCreate
        for i in range(self.rowCount):
            # Вычисление размера частей картинок, нужных для склейки между собой
            y1 = self.connectionArea.y
            if i == 0:
                y1 = 0
            y2 = self.connectionArea.y + self.connectionArea.height
            if i == self.rowCount - 1:
                y2 = self.imgSize.height

            minimapRow = np.zeros(0)
            for j in range(self.colCount):
                imgP = np.zeros(0)
                #Подготовка основных (детализированных) изображений
                if (replace or not os.path.exists(os.path.join(self.folder, "P_" + str(i+1) + "_" + str(j+1) + ".jpg"))) and os.path.exists(os.path.join(self.folder, "S_" + str(i+1) + "_" + str(j+1) + ".jpg")):
                    x1 = self.connectionArea.x
                    if j == 0:
                        x1 = 0
                    x2 = self.connectionArea.x + self.connectionArea.width
                    if j == self.colCount - 1:
                        x2 = self.imgSize.width
                    imgS = cv2.imread(os.path.join(self.folder, "S_" + str(i+1) + "_" + str(j+1) + ".jpg"))
                    imgP = np.copy(imgS[y1:y2, x1:x2, :])
                    cv2.imwrite(os.path.join(self.folder, "P_" + str(i+1) + "_" + str(j+1) + ".jpg"), imgP)
                    modiefed = True
                if imgP.shape[0] == 0:
                    imgP = cv2.imread(os.path.join(self.folder, "P_" + str(i+1) + "_" + str(j+1) + ".jpg"))
                if imgP.shape[0] == 0:
                    continue
                #Подготовка обрезанных изображений пониженного качества, в т.ч. миникарты
                imgP1 = np.zeros(0)
                imgP2 = np.zeros(0)
                if replace or not os.path.exists(os.path.join(self.folder, "P1_" + str(i+1) + "_" + str(j+1) + ".jpg")) or not os.path.exists(os.path.join(self.folder, "P2_" + str(i+1) + "_" + str(j+1) + ".jpg")):
                    dim1 = (int(imgP.shape[1] / 2), int(imgP.shape[0] / 2))
                    imgP1 = cv2.resize(imgP, dim1, interpolation=cv2.INTER_AREA)
                    cv2.imwrite(os.path.join(self.folder, "P1_" + str(i+1) + "_" + str(j+1) + ".jpg"), imgP1)
                    dim2 = (int(imgP.shape[1] / 4), int(imgP.shape[0] / 4))
                    imgP2 = cv2.resize(imgP1, dim2, interpolation=cv2.INTER_AREA)
                    cv2.imwrite(os.path.join(self.folder, "P2_" + str(i+1) + "_" + str(j+1) + ".jpg"), imgP2)
                    modiefed = True

                if minimapNeedCreate:
                    if imgP2.size == 0:
                        imgP2 = cv2.imread(os.path.join(self.folder, "P2_" + str(i+1) + "_" + str(j+1) + ".jpg"))
                    if minimapRow.size == 0:
                        minimapRow = np.copy(imgP2)
                    else:
                        minimapRow = np.concatenate((minimapRow, imgP2), axis=1)
            if minimapNeedCreate:
                if minimap.size == 0:
                    minimap = np.copy(minimapRow)
                else:
                    minimap = np.concatenate((minimap, minimapRow), axis=0)

        if minimapNeedCreate:
            cv2.imwrite(os.path.join(self.folder, "mini.jpg"), minimap)

        return modiefed
        """
        if not replace and (not os.path.exists(self.Folder + "P_" + str(i+1) + "_" + str(j+1) + ".jpg") or not os.path.exists(self.Folder + "P1_" + str(i+1) + "_" + str(j+1) + ".jpg") or not os.path.exists(self.Folder + "P2_" + str(i+1) + "_" + str(j+1) + ".jpg")):
            imgS = cv2.imread(self.Folder + "S_" + str(i+1) + "_" + str(j+1) + ".jpg")
            imgP = np.copy(img[y1:y2, x1:x2, :])
            if not os.path.exists(self.Folder + "P_" + str(i+1) + "_" + str(j+1) + ".jpg"):
                cv2.imwrite(self.Folder + "P_" + str(i+1) + "_" + str(j+1) + ".jpg", imgP)
            
        """
    #сохранение данных в XML
    def saveToFileXML(self, xmlFile):
        try:
            root = xml.Element("Root")
            apptRC = xml.Element("RowCount")
            apptRC.text = str(self.rowCount)
            root.append(apptRC)
            apptCC = xml.Element("ColCount")
            apptCC.text = str(self.colCount)
            root.append(apptCC)
            apptI = xml.Element("Image")
            root.append(apptI)
            formatt = xml.SubElement(apptI, "Format")
            formatt.text = self.format
            #isAllImageInMemory = xml.SubElement(apptI, "AllImageInMemory")
            #isAllImageInMemory.text = str(self.allImageInMemory)
            imgSize = xml.SubElement(apptI, "ImgSize")
            isWidth = xml.SubElement(imgSize, "Width")
            isWidth.text = str(self.imgSize.width)
            isHeight = xml.SubElement(imgSize, "Height")
            isHeight.text = str(self.imgSize.height)
            conArea = xml.SubElement(apptI, "ConnectionArea")
            caX = xml.SubElement(conArea, "X")
            caX.text = str(self.connectionArea.x)
            caY = xml.SubElement(conArea, "Y")
            caY.text = str(self.connectionArea.y)
            caWidth = xml.SubElement(conArea, "Width")
            caWidth.text = str(self.connectionArea.width)
            caHeight = xml.SubElement(conArea, "Height")
            caHeight.text = str(self.connectionArea.height)

            tree = xml.ElementTree(root)
            with open(xmlFile, "w") as fobj:
                tree.write(xmlFile)
            return True
        except Exception:
            return False

    #Загрузка данных из XML
    def loadFromFileXML(self, xmlFile):
        try:
            with open(xmlFile) as fobj:
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
                        #elif elem.tag == "AllImageInMemory":
                        #    self.allImageInMemory = bool(appt.text)
                        elif elem.tag == "ImgSize":
                            for subelem in elem.getchildren():
                                if subelem.tag == "Width":
                                    self.imgSize.width = int(subelem.text)
                                elif subelem.tag == "Height":
                                    self.imgSize.height = int(subelem.text)
                        elif elem.tag == "ConnectionArea":
                            for subelem in elem.getchildren():
                                if subelem.tag == "Width":
                                    self.connectionArea.width = int(subelem.text)
                                elif subelem.tag == "Height":
                                    self.connectionArea.height = int(subelem.text)
                                elif subelem.tag == "X":
                                    self.connectionArea.x = int(subelem.text)
                                elif subelem.tag == "Y":
                                    self.connectionArea.y = int(subelem.text)
            self.filePath = xmlFile
            self.arrayImagesSize = []
            koef = 1
            for k in range(3):
                arrayArea = []
                y = 0
                for i in range(self.rowCount + 1):
                    arrayRow = []
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
                        arrayRow.append(Rect(x, y, dx, dy))
                        x += dx
                    y += dy
                    arrayArea.append(arrayRow)
                self.arrayImagesSize.append(arrayArea)


            #self.reloadPrepareData()
            return True
        except Exception as err:
            print(err)
            return False


#Класс текущего отображения изображения
class ImageView(object):
    def __init__(self, savedData=SavedData("")):
        # Данные изображения
        self.savedData = savedData
        # Загруженные куски изображения
        #self.imgData = np.empty(0)
        # Сшитое из кусков изображение фрагмента
        self.sumImg = np.empty(0)
        self.minimapBase = np.empty(0)
        self.curRect = Rect(-1, -1, 0, 0)
        # Параметры отображения
        self.scale = 1.0
        self.scaleIndex = 0
        self.offset = PointF()
        self.savedDataClear()

    def savedDataClear(self):
        #self.imgData = np.zerosro((self.savedData.rowCount, self.savedData.colCount))
        self.sumImg = np.empty(0)
        self.curRect = Rect(-1, -1, 0, 0)

    # Легкий вариант получения сшитого изображения простым сшитием всех кусков
    def easyMerge(self, newScaleIndex = 0, newRect = Rect()):
        prefix = "P"
        if newScaleIndex > 0:
            prefix += str(newScaleIndex)
        prefix += "_"
        self.savedDataClear()
        self.sumImg = np.zeros((0), dtype = np.uint8)
        for i in range (newRect.y, newRect.y + newRect.height):
            rowImg = np.zeros((0), dtype = np.uint8)
            for j in range (newRect.x, newRect.x + newRect.width):
                if self.savedData.allImageInMemory:
                    img = self.savedData.arrayLoadImages[newScaleIndex][i][j]
                else:
                    img = cv2.imread(os.path.join(self.savedData.folder, prefix + str(i+1) + "_" + str(j+1) + ".jpg"))[:, :, ::-1]
                if rowImg.size == 0:
                    #rowImg = np.copy(img)
                    rowImg = img
                else:
                    rowImg = np.concatenate((rowImg, img), axis=1)

            if self.sumImg.size == 0:
                #self.sumImg = np.copy(rowImg)
                self.sumImg = rowImg
            else:
                self.sumImg = np.concatenate((self.sumImg, rowImg), axis=0)

    # Получение сшитого изображения
    def getNewPreView(self, newScaleIndex = 0, newRect = Rect()):
        prefix = "P"
        if newScaleIndex > 0:
            prefix += str(newScaleIndex)
        prefix += "_"
        if self.scaleIndex != newScaleIndex:
            self.scaleIndex = newScaleIndex
            self.savedDataClear()

        intersectRect = Rect()
        if self.sumImg.shape[0] > 0 and newRect.width > 0 and newRect.height > 0:
            intersectRect.x = max(self.curRect.x, newRect.x)
            intersectRect.y = max(self.curRect.y, newRect.y)
            intersectRect.width = min(self.curRect.x + self.curRect.width, newRect.x + newRect.width) - intersectRect.x
            intersectRect.height = min(self.curRect.y + self.curRect.height, newRect.y + newRect.height) - intersectRect.y

        if intersectRect.width <= 0 or intersectRect.height <= 0:
            # Отрисовываем соединенную картинку простым способом
            self.easyMerge(newScaleIndex, newRect)
        elif newRect.width > 0 and newRect.height > 0:
            # 1. Вырезаем видимую часть старого изображения
            firstAreaOfIntersectRect = self.savedData.arrayImagesSize[newScaleIndex][intersectRect.y][intersectRect.x]
            lastAreaOfIntersectRect = self.savedData.arrayImagesSize[newScaleIndex][intersectRect.y + intersectRect.height - 1][intersectRect.x + intersectRect.width - 1]
            firstAreaOfCurrentRect = self.savedData.arrayImagesSize[newScaleIndex][self.curRect.y][self.curRect.x]
            y1InterInCurrent = firstAreaOfIntersectRect.y - firstAreaOfCurrentRect.y
            x1InterInCurrent = firstAreaOfIntersectRect.x - firstAreaOfCurrentRect.x
            y2InterInCurrent = lastAreaOfIntersectRect.y - firstAreaOfCurrentRect.y + lastAreaOfIntersectRect.height
            x2InterInCurrent = lastAreaOfIntersectRect.x - firstAreaOfCurrentRect.x + lastAreaOfIntersectRect.width
            intersectImg = np.copy(self.sumImg[y1InterInCurrent:y2InterInCurrent, x1InterInCurrent:x2InterInCurrent, :])
            # 2. Слева и справа от этой области надо объединить кадры вертикально в столбцы (высотой, равной высоте области)
            # 2.1 Слева
            fullRow = np.zeros(0, dtype=np.uint8)
            for j in range(newRect.x, intersectRect.x):
                tempColumn = np.zeros(0, dtype=np.uint8)
                for i in range(intersectRect.y, intersectRect.y + intersectRect.height):
                    if self.savedData.allImageInMemory:
                        img = self.savedData.arrayLoadImages[newScaleIndex][i][j]
                    else:
                        img = cv2.imread(os.path.join(self.savedData.folder, prefix + str(i+1) + "_" + str(j+1) + ".jpg"))[:, :, ::-1]
                    if tempColumn.size == 0:
                        tempColumn = img
                    else:
                        tempColumn = np.concatenate((tempColumn, img), axis=0)
                if fullRow.size == 0:
                    fullRow = tempColumn
                else:
                    fullRow = np.concatenate((fullRow, tempColumn), axis=1)
            # 2.2 Середину по горизонтали
            if fullRow.size == 0:
                fullRow = intersectImg
            else:
                fullRow = np.concatenate((fullRow, intersectImg), axis=1)
            # 2.3 Справа
            for j in range(intersectRect.x + intersectRect.width, newRect.x + newRect.width):
                tempColumn = np.zeros(0, dtype=np.uint8)
                for i in range(intersectRect.y, intersectRect.y + intersectRect.height):
                    if self.savedData.allImageInMemory:
                        img = self.savedData.arrayLoadImages[newScaleIndex][i][j]
                    else:
                        img = cv2.imread(os.path.join(self.savedData.folder, prefix + str(i+1) + "_" + str(j+1) + ".jpg"))[:, :, ::-1]
                    if tempColumn.size == 0:
                        tempColumn = img
                    else:
                        tempColumn = np.concatenate((tempColumn, img), axis=0)
                if fullRow.size == 0:
                    fullRow = tempColumn
                else:
                    fullRow = np.concatenate((fullRow, tempColumn), axis=1)

            # 3. Объединяем части сверху, пришиваем наш fullRow, потом части ниже
            # 3.1 Сверху
            self.sumImg = np.zeros(0, dtype=np.uint8)
            for i in range(newRect.y, intersectRect.y):
                tempRow = np.zeros(0, dtype=np.uint8)
                for j in range(newRect.x, newRect.x + newRect.width):
                    if self.savedData.allImageInMemory:
                        img = self.savedData.arrayLoadImages[newScaleIndex][i][j]
                    else:
                        img = cv2.imread(os.path.join(self.savedData.folder, prefix + str(i+1) + "_" + str(j+1) + ".jpg"))[:, :, ::-1]
                    if tempRow.size == 0:
                        tempRow = img
                    else:
                        tempRow = np.concatenate((tempRow, img), axis=1)
                if self.sumImg.size == 0:
                    self.sumImg = tempRow
                else:
                    self.sumImg = np.concatenate((self.sumImg, tempRow), axis=0)
            # 3.2 Середину по вертикали
            if self.sumImg.size == 0:
                self.sumImg = fullRow
            else:
                self.sumImg = np.concatenate((self.sumImg, fullRow), axis=0)
            # 3.3 Снизу
            for i in range(intersectRect.y + intersectRect.height, newRect.y + newRect.height):
                tempRow = np.zeros(0, dtype=np.uint8)
                for j in range(newRect.x, newRect.x + newRect.width):
                    if self.savedData.allImageInMemory:
                        img = self.savedData.arrayLoadImages[newScaleIndex][i][j]
                    else:
                        img = cv2.imread(os.path.join(self.savedData.folder, prefix + str(i+1) + "_" + str(j+1) + ".jpg"))[:, :, ::-1]
                    if tempRow.size == 0:
                        tempRow = img
                    else:
                        tempRow = np.concatenate((tempRow, img), axis=1)
                if self.sumImg.size == 0:
                    self.sumImg = tempRow
                else:
                    self.sumImg = np.concatenate((self.sumImg, tempRow), axis=0)

        self.curRect = newRect

    def getView(self, newScale=1.0, newVisibleSize = QSize()):
        if self.savedData.rowCount == 0:
            return
        if newScale < 0.001:
            newScale = 0.001
        if newScale > 20.0:
            newScale = 20.0

        if self.offset.y + newVisibleSize.height() / newScale > self.savedData.arrayImagesSize[0][-1][0].y:
            self.offset.y = self.savedData.arrayImagesSize[0][-1][0].y - newVisibleSize.height() / newScale
        if self.offset.y < 0:
            self.offset.y = 0
        if self.offset.x + newVisibleSize.width() / newScale > self.savedData.arrayImagesSize[0][0][-1].x:
            self.offset.x = self.savedData.arrayImagesSize[0][0][-1].x - newVisibleSize.width() / newScale
        if self.offset.x < 0:
            self.offset.x = 0
        #Проверим сначала, как зименился масштаб, не надо ли загрузить изображения другого качества
        newScaleIndex = 0
        if newScale <= 0.125:
            newScaleIndex = 2
        elif newScale <= 0.25:
            newScaleIndex = 1
        self.scale = newScale
        y1Ind = 0
        x1Ind = 0
        y2Ind = 0
        x2Ind = 0
        y2Offset = self.offset.y + newVisibleSize.height() / newScale
        x2Offset = self.offset.x + newVisibleSize.width() / newScale
        for i in range(self.savedData.rowCount - 1, -1, -1):
            if y2Offset >= self.savedData.arrayImagesSize[0][i][0].y:
                y2Ind = i
                break
        for j in range(self.savedData.colCount - 1, -1, -1):
            if x2Offset >= self.savedData.arrayImagesSize[0][0][j].x:
                x2Ind = j
                break

        for i in range(y2Ind, -1, -1):
            if self.offset.y >= self.savedData.arrayImagesSize[0][i][0].y:
                y1Ind = i
                break
        for j in range(x2Ind, -1, -1):
            if self.offset.x >= self.savedData.arrayImagesSize[0][0][j].x:
                x1Ind = j
                break
        self.getNewPreView(newScaleIndex, Rect(x1Ind, y1Ind, x2Ind - x1Ind + 1, y2Ind - y1Ind + 1))

        y1 = (int(self.offset.y) >> self.scaleIndex) - self.savedData.arrayImagesSize[self.scaleIndex][y1Ind][x1Ind].y
        x1 = (int(self.offset.x) >> self.scaleIndex) - self.savedData.arrayImagesSize[self.scaleIndex][y1Ind][x1Ind].x
        y2 = (int(y2Offset) >> self.scaleIndex) - self.savedData.arrayImagesSize[self.scaleIndex][y1Ind][x1Ind].y
        x2 = (int(x2Offset) >> self.scaleIndex) - self.savedData.arrayImagesSize[self.scaleIndex][y1Ind][x1Ind].x

        view = np.copy(self.sumImg[y1:y2, x1:x2, :])

        miniKoef = 200 / self.savedData.arrayImagesSize[0][-1][0].y
        minimap = np.copy(self.minimapBase)
        cv2.rectangle(minimap, (int(miniKoef * self.offset.x), int(miniKoef * self.offset.y)), (int(miniKoef * x2Offset), int(miniKoef * y2Offset)), (255, 0, 0), 2)

        if self.scale != 1:
            return cv2.resize(view, (newVisibleSize.width(), newVisibleSize.height()), cv2.INTER_AREA), minimap


        return view, minimap


def numpyQImage(image):
    qImg = QImage()
    if image.dtype == np.uint8:
        if len(image.shape) == 2:
            channels = 1
            height, width = image.shape
            bytesPerLine = channels * width
            qImg = QImage(
                image.data, width, height, bytesPerLine, QImage.Format_Indexed8
            )
            qImg.setColorTable([QtGui.qRgb(i, i, i) for i in range(256)])
        elif len(image.shape) == 3:
            if image.shape[2] == 3:
                height, width, channels = image.shape
                bytesPerLine = channels * width
                qImg = QImage(
                    image.data, width, height, bytesPerLine, QImage.Format_RGB888
                )
            elif image.shape[2] == 4:
                height, width, channels = image.shape
                bytesPerLine = channels * width
                fmt = QImage.Format_ARGB32
                qImg = QImage(
                    image.data, width, height, bytesPerLine, QImage.Format_ARGB32
                )
    return qImg

#Label для размещения картинок
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

    def openFile(self):
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
                settFile = os.path.join(self.EXTRACT_TEMP_FOLDER, folder, "settings.xml")
                if os.path.exists(settFile):
                    createDT = datetime.datetime.fromtimestamp(os.path.getctime(settFile))
                    if (datetime.datetime.now() - createDT).total_seconds() > 120.0:
                        shutil.rmtree(os.path.join(self.EXTRACT_TEMP_FOLDER, folder))
        self.startMousePos = Point()
        self.status = ImageStatus.Idle
        self.fileName = ""
        self.modiefed = False
        self.minScale = 0.001
        self.maxScale = 10.0
        self.programSettings = ProgramSettings()

        self.configFilePath = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "Config.xml")
        self.loadConfig()


    def saveConfig(self):
        root = xml.Element("Root")
        apptRC = xml.Element("FullLoadImageMemoryLimit")
        apptRC.text = "1024*1024*1024"
        root.append(apptRC)
        tree = xml.ElementTree(root)
        with open(self.configFilePath, "w") as fobj:
            tree.write(self.configFilePath)


    def loadConfig(self):
        if os.path.exists(self.configFilePath):
            with open(self.configFilePath) as fobj:
                xml = fobj.read()
                root = etree.fromstring(xml)
                for appt in root.getchildren():
                    if appt.tag == "FullLoadImageMemoryLimit":
                        memLimitText = appt.text
                        for ch in "xXхХ":
                            memLimitText = memLimitText.replace(ch, "*")
                        self.programSettings.fullLoadImageMemoryLimit = eval(memLimitText)
        else:
            self.saveConfig()
        return

    def imageMove(self, pos = QPoint()):
        if self.status == ImageStatus.Move:
            self.imageView.offset.x = self.startMousePos.x - pos.x() / self.imageView.scale
            self.imageView.offset.y = self.startMousePos.y - pos.y() / self.imageView.scale
            self.setNewView()


    # Обработчики событий формы и ее компонентов
    def eventFilter(self, obj, event):
        if obj is self.imLabel:
            if event.type() == QEvent.MouseButtonPress:
                #print('mouse press event = ', event.pos())
                if self.status == ImageStatus.Idle:
                    self.status = ImageStatus.Move
                    self.startMousePos.x = self.imageView.offset.x + event.pos().x() / self.imageView.scale
                    self.startMousePos.y = self.imageView.offset.y + event.pos().y() / self.imageView.scale
            elif event.type() == QEvent.MouseButtonRelease:
                #print('mouse release event = ', event.pos())
                if self.status == ImageStatus.Move:
                    self.imageMove(event.pos())
                self.status = ImageStatus.Idle
            elif event.type() == QEvent.MouseMove:
                #self.setWindowTitle(str(event.pos()))
                if self.status == ImageStatus.Move:
                    self.imageMove(event.pos())
            elif event.type() == QEvent.Wheel:
                #self.setWindowTitle(str(event.angleDelta().y()) + "; pos: " + str(event.pos()))
                if event.modifiers() & Qt.ControlModifier:
                    newScale = self.scaleEdit.value() * (1000 + event.angleDelta().y()) / 1000
                elif event.modifiers() & Qt.ShiftModifier:
                    newScale = self.scaleEdit.value() * (6000 + event.angleDelta().y()) / 6000
                else:
                    newScale = self.scaleEdit.value() * (2500 + event.angleDelta().y()) / 2500
                if newScale > self.maxScale:
                    newScale = self.maxScale
                    self.imageView.scale = newScale
                if newScale < self.minScale:
                    newScale = self.minScale
                    self.imageView.scale = newScale

                self.imageView.offset.x += event.pos().x() * (newScale - self.imageView.scale) / (newScale * self.imageView.scale)
                self.imageView.offset.y += event.pos().y() * (newScale - self.imageView.scale) / (newScale * self.imageView.scale)
                self.scaleEdit.setValue(newScale)
                self.setNewView()
            elif event.type() == QEvent.Resize:
                self.resized()
        elif obj is self.minimapLabel:
            if event.type() == QEvent.MouseButtonPress:
                #print('mouse press event = ', event.pos())
                self.status = ImageStatus.MinimapMove
                if self.savedData.rowCount > 0:
                    self.imageView.offset.y = event.pos().y() * self.savedData.arrayImagesSize[0][-1][0].y / self.minimapLabel.size().height() - 0.5 * self.imLabel.size().height() / self.imageView.scale
                    self.imageView.offset.x = event.pos().x() * self.savedData.arrayImagesSize[0][0][-1].x / self.minimapLabel.size().width() - 0.5 * self.imLabel.size().width() / self.imageView.scale
                    self.setNewView()
            elif event.type() == QEvent.MouseButtonRelease:
                self.status = ImageStatus.Idle
            elif event.type() == QEvent.MouseMove:
                #self.setWindowTitle(str(event.pos()))
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
        if self.fileName and self.modiefed:
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
            selfilter = "Microscope scans (*.misc)"
            a = QFileDialog.getSaveFileName(self, "Выберите место сохранения файла", "/", "All files (*.*);;Microscope scans (*.misc)", selfilter)
            if len(a[0]) > 0:
                ext = os.path.splitext(a[0])
                if ext[1] == ".misc":
                    self.fileName = a[0]
                else:
                    self.fileName = ext[0] + ".misc"
                if os._exists(self.fileName):
                    dlgResult = QMessageBox.question(self, "Confirm Dialog", "Файл уже существует. Хотите его перезаписать? Это удалит данные в нем", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if dlgResult == QMessageBox.No:
                        return

            else:
                return

        if self.savedData.saveToFileXML(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, "settings.xml")):
            self.savedData.folder = self.EXTRACT_TEMP_SUBFOLDER
        else:
            self.errDlg = QErrorMessage()
            self.errDlg.setWindowTitle("Ошибка")
            self.errDlg.showMessage("Произошла непредвиденная ошибка записи файла!")
            return

        z = zipfile.ZipFile(self.fileName, 'w')
        for root, dirs, files in os.walk(self.EXTRACT_TEMP_SUBFOLDER):
            for file in files:
                if file:
                    z.write(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, file), file, compress_type = zipfile.ZIP_DEFLATED)
        self.modiefed = False
        self.setWindowTitle("Micros - " + self.fileName)
        dlgResult = QMessageBox.question(self, "Info Dialog", "Файл сохранен", QMessageBox.Ok, QMessageBox.Ok)

    def openFile(self):
        selfilter = "Microscope scans (*.misc)"
        if self.fileName and self.modiefed:
            dlgResult = QMessageBox.question(self,
                                             "Confirm Dialog",
                                             "Есть несохраненные изменения в текущем файле. Хотите сперва их сохранить?",
                                             QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                             QMessageBox.Yes)
            if dlgResult == QMessageBox.Yes:
                self.saveFile()
            elif dlgResult == QMessageBox.Cancel:
                return

        a = QFileDialog.getOpenFileName(self,
                                        "Выберите файл изображения",
                                        "/",
                                        "All files (*.*);;Microscope scans (*.misc)",
                                        selfilter)
        if len(a[0]) > 0:
            self.EXTRACT_TEMP_SUBFOLDER = os.path.join(self.EXTRACT_TEMP_FOLDER, str(uuid.uuid4()))
            os.mkdir(self.EXTRACT_TEMP_SUBFOLDER)
            z = zipfile.PyZipFile(a[0])
            z.extractall(self.EXTRACT_TEMP_SUBFOLDER)
            sumSize = 0
            for f in os.listdir(self.EXTRACT_TEMP_SUBFOLDER):
                if os.path.isfile(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, f)):
                    sumSize += os.path.getsize(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, f))

            if self.savedData.loadFromFileXML(os.path.join(self.EXTRACT_TEMP_SUBFOLDER, "settings.xml")):
                self.savedData.folder = self.EXTRACT_TEMP_SUBFOLDER
                self.savedData.prepareScans()
                path_to_minimap = os.path.join(self.EXTRACT_TEMP_SUBFOLDER, "mini.jpg")
                if os.path.exists(path_to_minimap):
                    self.imageView.minimapBase = cv2.imread(path_to_minimap, cv2.IMREAD_COLOR)[:, :, ::-1]
                self.fileName = a[0]
                self.modiefed = False
                self.savedData.setAllImageInMemory(sumSize <= self.programSettings.fullLoadImageMemoryLimit)
                self.servicesMenuAllInMemory.setChecked(sumSize <= self.programSettings.fullLoadImageMemoryLimit)
                self.resized()
                self.setWindowTitle("Micros - " + self.fileName)
            else:
                self.errDlg = QErrorMessage()
                self.errDlg.setWindowTitle("Ошибка")
                self.errDlg.showMessage("Произошла непредвиденная ошибка чтения файла. Возможно открываемый файл имеет неподходячщий формат или поврежден!")

    def minimapCheckBox_Changed(self, state):
        if state == Qt.Checked:
            self.minimapLabel.show()
        else:
            self.minimapLabel.hide()

    def prepareScans(self):
        self.modiefed = self.savedData.prepareScans(True)

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
        mainImg, miniImg = self.imageView.getView(self.scaleEdit.value(), self.imLabel.size())
        qImg = numpyQImage(mainImg)
        pixmap = QtGui.QPixmap.fromImage(qImg)
        self.imLabel.setPixmap(pixmap)
        qMiniImg = numpyQImage(miniImg)
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
        self.savedData.setAllImageInMemory(self.servicesMenuAllInMemory.isChecked())
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

        minimapCheckBox = QCheckBox("Мини-изображение", self)
        minimapCheckBox.stateChanged.connect(self.minimapCheckBox_Changed)
        minimapCheckBox.setCheckState(Qt.Checked)
        rightLayout.addWidget(minimapCheckBox)

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
