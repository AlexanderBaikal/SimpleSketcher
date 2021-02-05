import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QFont, QScreen
from os import listdir


class Menu(QWidget):
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
        self.kplist = []

        self.states = []
        self.redolist = []

        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self)
        shortcut.activated.connect(self.undo)

        shortcut2 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Z"), self)
        shortcut2.activated.connect(self.redo)

        ldir = sorted(listdir())
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
        print(imgdigits)
        print(int(max(map(int, imgdigits))))
        self.btn = QPushButton('Add KeyPoints', self)
        self.btn.move(10, 10)
        self.btn.clicked.connect(self.addKP)

        self.btn2 = QPushButton('Stop adding', self)
        self.btn2.move((self.width()-20) // 4, 10)
        self.btn2.clicked.connect(self.stopKP)

        self.btn3 = QPushButton('Save', self)
        self.btn3.move(2*(self.width()-20) // 4, 10)
        self.btn3.clicked.connect(self.save)

        self.btn4 = QPushButton('Clear', self)
        self.btn4.move(3*(self.width()-20) // 4, 10)
        self.btn4.clicked.connect(self.clear)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)



    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.states.append(self.pixmap.copy())
            if len(self.states) > 3:
                del self.states[0]
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
                self.update()

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
        self.color = Qt.blue
        self.kpmode = True

    def stopKP(self):
        self.color = Qt.black
        self.kpmode = False

    def save(self):
        filename = f'img_{self.nimg}.jpg'
        self.pixmap.save(filename, 'jpg')
        with open(filename.replace('jpg', 'txt'), 'w') as f:
            f.write(str(self.kplist))
        self.nimg += 1

    def clear(self):
        self.states.append(self.pixmap.copy())
        if len(self.states) > 3:
            del self.states[0]
        self.pixmap.fill(QColor("white"))
        self.update()

    def redo(self):
        if self.redolist:
            self.states.append(self.pixmap)
            pm = self.redolist.pop()
            print('redo', pm)
            self.pixmap = pm
            if len(self.states) > 3:
                del self.states[0]
            print(len(self.states), len(self.redolist))
            self.update()

    def undo(self):
        if self.states:
            self.redolist.append(self.pixmap)
            pm = self.states.pop()
            print('undo', pm)
            self.pixmap = pm
            if len(self.redolist) > 3:
                del self.redolist[0]
            print(len(self.states), len(self.redolist))
            self.update()

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = Menu()
    sys.excepthook = except_hook
    example.show()
    sys.exit(app.exec_())

