import sys
import traceback
import matplotlib.pyplot as plt

import cv2
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QToolBar, QGridLayout, QToolButton, QMenuBar, \
    QTextEdit, QMainWindow, QAction
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QFont, QScreen, QIcon
from os import listdir


class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('sk_icon.png'))
        self.painter = Painter()
        self.setCentralWidget(self.painter)

        layout = QGridLayout()
        tb = self.addToolBar("File")
        add = QAction(QIcon("res/addkp_icon.png"), "addkp", self)
        add.triggered.connect(self.painter.addKP)
        tb.addAction(add)
        stop = QAction(QIcon("res/stopkp_icon.png"), "stop", self)
        stop.triggered.connect(self.painter.stopKP)
        tb.addAction(stop)
        clear = QAction(QIcon("res/clear_icon.png"), "clear", self)
        clear.triggered.connect(self.painter.clear)
        tb.addAction(clear)
        mgnt = QAction(QIcon("res/magnet_icon.png"), "magnet", self)
        mgnt.triggered.connect(self.painter.magnet)
        tb.addAction(mgnt)
        self.savebutton = QAction(QIcon("res/save_icon.png"), "save", self)
        self.savebutton.triggered.connect(self.painter.save)
        # self.savebutton.setDisabled(True)
        tb.addAction(self.savebutton)
        self.setLayout(layout)
        self.setWindowTitle("Sketcher demo")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_enabled()


class Painter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.drawing = False
        self.kpmode = False
        self.lastPoint = QPoint()
        self.setGeometry(100, 100, 500, 500)
        self.setFixedSize(self.width(), self.height())
        self.pixmap = QPixmap(self.width(), self.height())
        self.pixmap.fill(QColor("white"))
        self.setWindowTitle('Drawer')
        self.color = Qt.black
        self.kptext = 1
        self.savekptext = 1
        self.kplist = []
        self.redokplist = []
        self.undokplist = []
        self.sketch = None
        self.actionstype = []
        self.redoactionstype = []

        self.states = []
        self.redolist = []

        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self)
        shortcut.activated.connect(self.undo)

        shortcut2 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Z"), self)
        shortcut2.activated.connect(self.redo)

        ldir = sorted(listdir('out/'))
        print(ldir)
        imgdigits = []
        imgflag = False
        for fname in ldir:
            if 'img_' in fname:
                imgflag = True
                ff = '.'.join(fname.split('.')[:-1])
                imgdigit = ff.split('_')[-1]
                imgdigits.append(imgdigit)
        if imgflag:
            self.nimg = int(max(map(int, imgdigits))) + 1
        else:
            self.nimg = 1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.states.append(self.pixmap.copy())
            if len(self.states) > 3:
                del self.states[0]
            self.redoactionstype.clear()  # Как только внесли изменение в отмененное состояние,
            self.redolist.clear()  # Теряем возможность повторить действия
            self.drawing = True
            self.lastPoint = event.pos()
            if self.kpmode:
                painter = QPainter(self.pixmap)
                painter.setPen(QPen(self.color, 3, Qt.SolidLine))
                painter.drawEllipse(event.pos(), 6, 6)
                painter.setFont(QFont('Arial', 10))
                painter.drawText(event.x() + 5, event.y() + 20, str(self.kptext))
                self.kptext += 1
                self.kplist.append((event.x(), event.y()))
                self.actionstype.append('kp')
                self.update()
            else:
                self.actionstype.append('draw')

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawing and not self.kpmode:
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(self.color, 3, Qt.SolidLine))
            painter.drawLine(self.lastPoint, event.pos())
            self.lastPoint = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            self.drawing = False

    def addKP(self):
        if not self.actionstype:
            return
        self.color = Qt.blue
        if not self.sketch:
            print('R')
            self.sketch = self.pixmap.copy()
        self.kpmode = True

    def stopKP(self):  # Переключение на рисование
        if not self.actionstype:
            return
        self.color = Qt.black
        self.states.append(self.pixmap.copy())
        if len(self.states) > 3:
            del self.states[0]
        if self.sketch:
            self.pixmap = self.sketch
        self.undokplist = self.kplist.copy()
        self.redokplist.clear()
        self.kplist.clear()
        print(self.kplist)
        self.savekptext = self.kptext
        self.kptext = 1
        self.actionstype.append('stopkp')
        self.kpmode = False
        self.update()

    def save(self):
        if not self.kplist:
            return
        filename = f'out/img_{self.nimg}.png'
        self.save_img(filename)
        with open(filename.replace('png', 'txt'), 'w') as f:
            f.write(str(self.kplist))
        self.nimg += 1

    def clear(self):  # Нужно сохранять ключевые точки при очистке !!!
        if self.actionstype and self.actionstype[-1] == 'clear':
            return
        self.states.append(self.pixmap.copy())
        if len(self.states) > 3:
            del self.states[0]
        self.pixmap.fill(QColor("white"))
        self.savekptext = self.kptext  # Сохраняем нумерацию для отмены
        self.kptext = 1
        self.undokplist = self.kplist.copy()  # Сохраняем точки для отмены
        self.kplist.clear()
        self.redokplist.clear()
        self.sketch = None
        self.actionstype.append('clear')
        print(self.kplist, ' ||| ', self.redokplist, ' ||| ', self.undokplist, self.redolist)
        self.update()

    def redo(self):
        if self.actionstype and self.actionstype[-1] == 'clear':
            # Если мы вернулись к очищенному холсту,
            # дальше нет смысла нажимать на повтор
            self.redolist.clear()
            self.kptext = 1
        if self.redolist:
            self.states.append(self.pixmap)
            self.pixmap = self.redolist.pop()
            # Если крайний раз мы отменили добавление точки
            # Добавляем точку обратно в список
            if self.redokplist and self.redoactionstype:
                actype = self.redoactionstype.pop()
                print(actype, 'r')
                if actype == 'kp':
                    self.kplist.append(self.redokplist.pop())
                    self.kptext += 1
                if actype == 'clear' or actype == 'stopkp' or actype == 'magnet':  # Если последнее действие было "Clear"
                    self.undokplist = self.redokplist.copy()
                    self.kplist = []
                    self.redokplist = []
                    self.kptext = 1

                self.actionstype.append(actype)  # Тип последнего действия
            if len(self.states) > 3:
                del self.states[0]
            print(self.kplist, ' ||| ', self.redokplist, ' ||| ', self.undokplist)
            self.update()

    def undo(self):
        if self.states:
            self.redolist.append(self.pixmap)
            self.pixmap = self.states.pop()

            if self.actionstype:
                actype = self.actionstype.pop()
                print(actype, 'u')
                if actype == 'kp':  # Если последнее действие было "KP"
                    if self.kplist:
                        self.redokplist.append(self.kplist.pop())  # Убираем точку из списка точек
                        self.kptext -= 1
                if actype == 'clear' or actype == 'stopkp' or actype == 'magnet':  # Если последнее действие было "Clear"
                    if self.undokplist:
                        self.kptext = self.savekptext
                        self.redokplist = self.undokplist.copy()
                        self.kplist = self.undokplist.copy()
                        self.undokplist = []
                self.redoactionstype.append(actype)
            if len(self.redolist) > 3:
                del self.redolist[0]
            print(self.kplist, ' ||| ', self.redokplist, ' ||| ', self.undokplist)
            # print(self.pixmap)
            self.update()

    def save_img(self, filename):
        if self.sketch:
            self.sketch.save(filename, 'png')
        else:
            self.pixmap.save(filename, 'png')

    def magnet(self):  # Shift kp to borderlines
        if not self.kplist:
            return
        filename = 'tmp/magnet.png'
        self.save_img(filename)
        img = cv2.imread(filename)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.bitwise_not(img)
        ret, img = cv2.threshold(img, 200, 255, 0)
        nonzero = cv2.findNonZero(img)

        self.states.append(self.pixmap.copy())
        if len(self.states) > 3:
            del self.states[0]
        self.undokplist = self.kplist
        self.savekptext = self.kptext
        self.redokplist.clear()
        self.actionstype.append('magnet')
        self.pixmap = self.sketch.copy()

        fixed_kplist = []
        self.kptext = 1
        for kp in self.kplist:
            distances = np.sqrt((nonzero[:, :, 0] - kp[0]) ** 2 + (nonzero[:, :, 1] - kp[1]) ** 2)
            nearest_index = np.argmin(distances)
            fixed_kp = nonzero[nearest_index, 0]
            # print(*fixed_kp)
            # plt.scatter(*fixed_kp)
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(Qt.blue, 3, Qt.SolidLine))
            painter.drawEllipse(*fixed_kp, 6, 6)
            painter.setFont(QFont('Arial', 10))
            painter.drawText(fixed_kp[0] + 5, fixed_kp[1] + 20, str(self.kptext))
            painter = None  # Important !
            self.kptext += 1
            fixed_kplist.append(tuple(fixed_kp))
        self.update()
        self.kplist = fixed_kplist
        print(self.kplist)

        # plt.imshow(img, cmap='Greys')
        # plt.show()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = MyMainWindow()
    sys.excepthook = except_hook
    example.show()
    sys.exit(app.exec_())

#   Подписи к точкам при очистке холста
#   Зависание при включении KP
# Должна выбираться точка, где контур
# Если отменили и изменили, то не можем повторить
# Проверка точек из файла на холсте
# Повороты, аугментация
# Сохранение скетча после отмены, очистки, повторного добавления точек
# Disable кнопки
