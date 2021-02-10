import sys
import threading
from itertools import combinations
from os.path import exists
from queue import Queue
from time import time, sleep

import cv2
from ast import literal_eval
import numpy as np
from PIL import Image, ImageChops
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, \
    QMainWindow, QAction, QMessageBox, QProgressBar, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QIcon
from os import listdir, mkdir, remove
import imagehash


class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('res/aug_icon.png'))
        self.myprogressbar = MyProgressbar()
        self.setCentralWidget(self.myprogressbar)
        # Toolbar
        layout = QGridLayout()
        tb = self.addToolBar("File")
        self.augbutton = QAction(QIcon("res/aug_icon.png"), "Augmentation", self)
        self.augbutton.triggered.connect(self.myprogressbar.aug)
        tb.addAction(self.augbutton)
        self.checkbutton = QAction(QIcon("res/check_icon.png"), "Check", self)
        self.checkbutton.triggered.connect(self.myprogressbar.check)
        tb.addAction(self.checkbutton)
        self.comparebutton = QAction(QIcon("res/compare_icon.png"), "Remove Duplicates", self)
        self.comparebutton.triggered.connect(self.myprogressbar.launch_progress_bar)
        tb.addAction(self.comparebutton)
        self.setLayout(layout)
        self.setWindowTitle("Aug. Beta")


class ProgressbarThread(QThread):
    update_progressbar = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__()

    def run(self):
        self.myprogressbar = MyProgressbar()
        self.myprogressbar.compare(self)


class MyProgressbar(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.progressbar = QProgressBar(self)
        self.progressbar.setAlignment(Qt.AlignCenter)
        self.progressbar.setGeometry(100, 50, 300, 50)
        self.setGeometry(100, 100, 500, 200)
        self.setFixedSize(self.width(), self.height())
        self.i_compare = 0

    def launch_progress_bar(self):
        self.ProgressbarThread_intance = ProgressbarThread()
        self.ProgressbarThread_intance.update_progressbar.connect(self.updateProgressbar)
        self.ProgressbarThread_intance.start()

    def updateProgressbar(self, value):
        self.progressbar.setValue(value)

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
                percent = str(round(percent, 2)) + '%'
                print(percent)

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
            percent = str(round(percent, 2)) + '%'
            print(percent)

    def difference_images(self, h1, h2, f1, f2, path=''):
        if (h1 == h2):
            self.rm_images.append((path + f1, path + f2, str(h1)))
        return

    def make_hash(self, array, path=''):
        hashes = []
        for el in array:
            img = Image.open(path + el)
            hash = imagehash.phash(img)
            hashes.append(hash)
        return hashes

    def compare(self, cls=None):
        start = time()
        self.i_compare = 0
        self.rm_images = []

        path = 'out/'
        imgs = sorted(filter(lambda x: x.endswith('.png'), listdir(path)),
                      key=lambda x: int(x.replace('img_', '').replace('.png', '')))

        print(imgs)
        nb_images = len(list(combinations(imgs, 2)))
        # print(nb_images)

        hashes = self.make_hash(imgs, path)

        check_file = 0  # Проверяемый файл
        current_file = 0  # Текущий файл
        old_percent = 0  # percent

        while check_file < len(hashes) and current_file < len(hashes):
            self.i_compare += 1
            percent = int(self.i_compare / nb_images * 100)
            # print(percent)
            # self.progressbar.setValue(percent)
            if cls and percent != old_percent:
                cls.update_progressbar.emit(percent)
                old_percent = percent
            if current_file == check_file:
                current_file += 1
                continue
            self.difference_images(hashes[current_file], hashes[check_file],
                                   imgs[current_file], imgs[check_file], path)
            current_file += 1
            if current_file == len(imgs):
                check_file += 1
                current_file = check_file

        if self.rm_images:
            # print(self.rm_images)
            duplicates = self.drop_duplicates()
            for k, v in duplicates.items():
                v = sorted(filter(lambda x: x.endswith('.png'), v),
                           key=lambda x: int(x.replace(path + 'img_', '').replace('.png', '')))
                orig = v[0]
                dropped = v[1:]
                print(orig, dropped)

        end = time()
        self.progressbar.setValue(100)
        print('Done', str(end - start))

    def drop_duplicates(self):
        hash_dict = dict()
        if self.rm_images:
            for group in self.rm_images:
                if group[2] in hash_dict.keys():
                    if group[0] not in hash_dict[group[2]]:
                        hash_dict[group[2]].append(group[0])
                    if group[1] not in hash_dict[group[2]]:
                        hash_dict[group[2]].append(group[1])
                else:
                    hash_dict[group[2]] = [group[0], group[1]]
        return hash_dict


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
# pyinstaller --onefile --noconsole --icon=aug_icon.ico aug.py
# Увеличить скорость для остальных кнопок
