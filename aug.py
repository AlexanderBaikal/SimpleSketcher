import sys
import cv2
from ast import literal_eval
import numpy as np
from PIL import Image
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, \
    QMainWindow, QAction
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QIcon
from os import listdir, mkdir


class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('res/sk_icon.png'))
        self.painter = Painter()
        self.setCentralWidget(self.painter)
        # Toolbar
        layout = QGridLayout()
        tb = self.addToolBar("File")
        self.augbutton = QAction(QIcon("res/aug_icon.png"), "Augmentation", self)
        self.augbutton.triggered.connect(self.painter.aug)
        tb.addAction(self.augbutton)
        self.checkbutton = QAction(QIcon("res/check_icon.png"), "Check", self)
        self.checkbutton.triggered.connect(self.painter.check)
        tb.addAction(self.checkbutton)
        self.setLayout(layout)
        self.setWindowTitle("Aug. Beta")


class Painter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 500, 500)
        self.setFixedSize(self.width(), self.height())
        self.pixmap = QPixmap(self.width(), self.height())
        self.pixmap.fill(QColor("white"))
        self.color = Qt.black
        self.kp_text = 1
        self.kp_list = []

    def aug(self):
        if 'aug' not in listdir('out/'):
            mkdir('out/aug/')
        files = sorted(listdir('out/'))
        for i, fname in enumerate(files):  # Ищем изображения
            if 'img_' in fname and fname.endswith('.png'):
                fpath = "out/" + fname
                im = Image.open(fpath)
                txt = fpath.replace('.png', '.txt')
                with open(txt, 'r') as fread:
                    coords = fread.read()
                coords = literal_eval(coords)
                self.aug_rotate(im, coords, fpath)
                self.aug_flip(im, coords, fpath)
                percent = i / len(files) * 100
                print(str(round(percent, 2)) + '%')
        #         self.setWindowTitle(str(percent) + '%')
        # self.setWindowTitle("Aug. Beta")

    def aug_rotate(self, im, coords, fpath):
        for i in range(3):
            im = im.rotate(90)
            path = fpath.replace('out/', 'out/aug/').replace('.png', 'R_' + str(i) + '.png')
            im.save(path)
            if i > 0:
                coords = txt.copy()
            txt = []
            for coord in coords:
                size = im.size
                cp = (size[0] // 2, size[1] // 2)
                point_norm = (coord[0] - cp[0], coord[1] - cp[1])
                rotated_x = point_norm[1]  # x is old y
                rotated_y = -point_norm[0]  # y is negative of old x
                new_x = rotated_x + cp[0]
                new_y = rotated_y + cp[1]
                txt.append((new_x, new_y))
            with open(path.replace('.png', '.txt'), 'w') as f:
                f.write(str(txt))

    def aug_flip(self, im, coords, fpath):
        for i, mode in enumerate([Image.FLIP_LEFT_RIGHT, Image.FLIP_TOP_BOTTOM]):
            image = im.transpose(mode)
            path = fpath.replace('out/', 'out/aug/').replace('.png', 'F_' + str(i) + '.png')
            image.save(path)
            txt = []
            for coord in coords:
                size = im.size
                cp = (size[0] // 2, size[1] // 2)
                point_norm = (coord[0] - cp[0], coord[1] - cp[1])
                if mode == Image.FLIP_LEFT_RIGHT:
                    new_x = coord[0] - 2 * point_norm[0]
                    new_y = coord[1]
                if mode == Image.FLIP_TOP_BOTTOM:
                    new_x = coord[0]
                    new_y = coord[1] - 2 * point_norm[1]
                txt.append((new_x, new_y))
            with open(path.replace('.png', '.txt'), 'w') as f:
                f.write(str(txt))

    def check(self):
        if 'aug_test' not in listdir('out/aug/'):
            mkdir('out/aug/aug_test/')
        files = sorted(listdir("out/aug/"))
        for num, file in enumerate(files):
            if file.endswith(".png"):
                img = cv2.imread("out/aug/" + file)
                txt = file.replace('.png', '.txt')
                with open("out/aug/" + txt, 'r') as fread:
                    coords = fread.read()
                for i, coord in enumerate(literal_eval(coords)):
                    img = cv2.circle(img, coord, radius=3, color=(0, 0, 255), thickness=-1)
                    img = cv2.putText(img, str(i + 1), (coord[0] + 5, coord[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                      (0, 0, 255), 1)
                cv2.imwrite("out/aug/aug_test/" + file.replace('.png', '_test.png'), img)
            percent = num / len(files) * 100
            print(str(round(percent, 2)) + '%')
        #     self.setWindowTitle(str(percent) + '%')
        # self.setWindowTitle('Aug. Beta')


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = MyMainWindow()
    sys.excepthook = except_hook
    example.show()
    sys.exit(app.exec_())


# Повороты, аугментация
# 4eb0ff