import sys
from ast import literal_eval
from itertools import combinations
from os import listdir, mkdir, walk
from os.path import exists, abspath
from shutil import copy2
from time import time

import cv2
import imagehash
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, \
    QMainWindow, QAction, QProgressBar, QLabel, QFileDialog, QAbstractItemView

from settings import Ui_Form


class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('res/aug_app_icon.png'))
        self.merge_dst_dir = 'merged'
        self.merge_src_dirs = ['others', 'out']
        self.check_dir = 'out'
        self.aug_dir = 'out'
        self.myprogressbar = MyProgressbar(self)
        self.setCentralWidget(self.myprogressbar)
        # Toolbar
        layout = QGridLayout()
        tb = self.addToolBar("File")
        self.augbutton = QAction(QIcon("res/aug_icon.png"), "Augmentation", self)
        self.augbutton.triggered.connect(self.myprogressbar.pre_launch_aug)
        tb.addAction(self.augbutton)
        self.checkbutton = QAction(QIcon("res/check_icon.png"), "Check", self)
        self.checkbutton.triggered.connect(self.myprogressbar.pre_launch_check)
        tb.addAction(self.checkbutton)
        self.mergebutton = QAction(QIcon("res/copy_icon.png"), "Merge", self)
        self.mergebutton.triggered.connect(self.myprogressbar.pre_launch_merge)
        tb.addAction(self.mergebutton)
        self.comparebutton = QAction(QIcon("res/compare_icon.png"), "Remove Duplicates", self)
        self.comparebutton.triggered.connect(self.myprogressbar.pre_launch_compare)
        tb.addAction(self.comparebutton)
        self.setbutton = QAction(QIcon("res/set_icon.png"), "Settings", self)
        self.setbutton.triggered.connect(self.settings)
        tb.addAction(self.setbutton)
        self.setLayout(layout)
        self.setWindowTitle("Aug. Beta")
        self.mysettings = []

    def settings(self):
        self.mysettings = MySettings(self)
        self.setDisabled(True)
        self.mysettings.show()

    def closeEvent(self, event):
        if self.mysettings:
            self.mysettings.close()


class MySettings(QWidget, Ui_Form):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_widget = parent
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('res/set_icon.png'))
        self.setWindowTitle('Settings')
        self.setFixedSize(self.width(), self.height())
        self.pushButton.clicked.connect(self.open_dirs)
        self.pushButton_2.clicked.connect(self.open_merge_dir)
        self.pushButton_3.clicked.connect(self.save)
        self.pushButton_4.clicked.connect(self.reset)
        self.pushButton_5.clicked.connect(self.rm_selected)
        self.pushButton_6.clicked.connect(self.open_check_dir)
        self.pushButton_7.clicked.connect(self.open_aug_dir)
        self.listView.setSelectionMode(QAbstractItemView.MultiSelection)
        self.merge_src_dirs = self.parent_widget.merge_src_dirs.copy()
        self.merge_dst_dir = self.parent_widget.merge_dst_dir
        self.aug_dir = self.parent_widget.aug_dir
        self.check_dir = self.parent_widget.check_dir
        self.update_lw()

    def open_dirs(self):
        ap = len(abspath("")) + 1
        dir_name = QFileDialog.getExistingDirectory(self, 'Выберите папку')
        short_dir = dir_name[ap:]
        if any(short_dir in dst for dst in self.merge_src_dirs):
            print('duplicate')
            return
        self.merge_src_dirs.append(short_dir + '\t' + dir_name)
        self.update_lw()

    def open_check_dir(self):
        self.open_dir('check')

    def open_aug_dir(self):
        self.open_dir('aug')

    def open_merge_dir(self):
        self.open_dir('merge')

    def open_dir(self, arg):
        if arg == 'merge':
            cdir = self.merge_dst_dir
        elif arg == 'check':
            cdir = self.check_dir
        elif arg == 'aug':
            cdir = self.aug_dir
        ap = len(abspath("")) + 1

        dir_name = QFileDialog.getExistingDirectory(self, 'Выберите папку')
        if arg == 'aug' or arg == 'check':
            while not (sum(f.endswith('.png') for f in listdir(dir_name)) and
                       sum(f.endswith('.txt') for f in listdir(dir_name))):
                print('try again')
                dir_name = QFileDialog.getExistingDirectory(self, 'Выберите папку')

        short_dir = dir_name[ap:]
        if short_dir in cdir.split('\t')[0]:
            print('duplicate')
            return
        cdir = short_dir + '\t' + dir_name
        if arg == 'merge':
            self.merge_dst_dir = cdir
        elif arg == 'check':
            self.check_dir = cdir
        elif arg == 'aug':
            self.aug_dir = cdir
        self.update_lw()

    def rm_selected(self):
        if self.merge_src_dirs and self.listView.selectedItems():
            rm = [item.text() for item in self.listView.selectedItems()]
            for el in rm:
                self.merge_src_dirs.remove(el)
            print(rm, self.merge_src_dirs)
            self.update_lw()

    def update_lw(self):
        self.listView.clear()
        self.listView.addItems(self.merge_src_dirs)
        self.listView_2.clear()
        self.listView_2.addItem(self.merge_dst_dir)
        self.label_5.setText(self.check_dir.split('\t')[0])
        self.label_6.setText(self.aug_dir.split('\t')[0])

    def save(self):
        self.parent_widget.merge_src_dirs = list(map(lambda x: x.split('\t')[0], self.merge_src_dirs.copy()))
        self.parent_widget.merge_dst_dir = self.merge_dst_dir.split('\t')[0]
        self.parent_widget.aug_dir = self.aug_dir.split('\t')[0]
        print(self.parent_widget.aug_dir, self.aug_dir.split('\t')[0])
        self.parent_widget.check_dir = self.check_dir.split('\t')[0]
        self.myclose()

    def reset(self):
        self.merge_src_dirs = []
        self.parent_widget.setDisabled(False)
        self.parent_widget.mysettings = []

    def closeEvent(self, event):
        self.myclose()

    def myclose(self):
        self.parent_widget.setDisabled(False)
        self.parent_widget.mysettings = []


class ProgressbarThread(QThread):
    update_progressbar = pyqtSignal(int)
    update_label = pyqtSignal(str)

    def __init__(self, action_name, parent=None):
        super().__init__()
        self.action_name = action_name
        self.parent_widget = parent

    def run(self):
        self.myprogressbar = MyProgressbar(self.parent_widget)
        if self.action_name == 'compare':
            self.myprogressbar.compare(self)
        elif self.action_name == 'merge':
            self.myprogressbar.merge(self)
        elif self.action_name == 'check':
            self.myprogressbar.check(self)
        elif self.action_name == 'aug':
            self.myprogressbar.aug(self)
        self.parent_widget.myprogressbar.enable_buttons()


class MyProgressbar(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_widget = parent
        self.initUI()

    def initUI(self):
        self.progressbar = QProgressBar(self)
        self.progressbar.setStyleSheet("QProgressBar{border: none;"
                                       "background: transparent;"
                                       "border-radius: 7px;}"
                                       "QProgressBar::chunk{"
                                       "background: #4eb0ff;"
                                       "border-radius: 7px;}"
                                       )

        self.progressbar.setAlignment(Qt.AlignCenter)
        self.setGeometry(100, 100, 500, 100)
        self.progressbar.setGeometry(5, self.height() - 20, self.width() - 10, 15)

        self.setFixedSize(self.width(), self.height())
        self.i_progress = 0
        self.lbl = QLabel(self)
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setGeometry(20, 10, self.width() - 40, 30)
        self.merge_src_dirs = self.parent_widget.merge_src_dirs
        self.merge_dst_dir = self.parent_widget.merge_dst_dir
        self.check_dir = self.parent_widget.check_dir
        self.aug_dir = self.parent_widget.aug_dir

    def pre_launch_check(self):
        self.launch_progress_bar('check')

    def pre_launch_compare(self):
        self.launch_progress_bar('compare')

    def pre_launch_merge(self):
        self.launch_progress_bar('merge')

    def pre_launch_aug(self):
        self.launch_progress_bar('aug')

    def launch_progress_bar(self, action_name):
        self.disable_buttons()
        self.ProgressbarThread_intance = ProgressbarThread(action_name, self.parent_widget)
        self.ProgressbarThread_intance.update_progressbar.connect(self.updateProgressbar)
        self.ProgressbarThread_intance.update_label.connect(self.updateLabel)
        self.ProgressbarThread_intance.start()

    def updateProgressbar(self, value):
        self.progressbar.setValue(value)

    def updateLabel(self, string):
        self.lbl.setText(string)

    def enable_buttons(self):
        self.parent_widget
        if self.parent_widget:
            self.parent_widget.checkbutton.setDisabled(False)
            self.parent_widget.comparebutton.setDisabled(False)
            self.parent_widget.mergebutton.setDisabled(False)
            self.parent_widget.augbutton.setDisabled(False)
            self.parent_widget.setbutton.setDisabled(False)

    def disable_buttons(self):
        if self.parent_widget:
            self.parent_widget.checkbutton.setDisabled(True)
            self.parent_widget.comparebutton.setDisabled(True)
            self.parent_widget.mergebutton.setDisabled(True)
            self.parent_widget.augbutton.setDisabled(True)
            self.parent_widget.setbutton.setDisabled(True)

    def aug(self, cls=None):
        if cls:
            cls.update_label.emit('Augmentation...')
        if 'aug' not in listdir(self.aug_dir):
            mkdir(self.aug_dir + '/aug/')
        files = sorted(listdir(self.aug_dir))
        for i, fname in enumerate(files):  # Ищем изображения
            if 'img_' in fname and fname.endswith('.png'):
                fpath = self.aug_dir + "/" + fname
                im = Image.open(fpath)
                txt = fpath.replace('.png', '.txt')
                if not exists(txt) or not exists(fpath):
                    continue
                with open(txt, 'r') as fread:
                    coords = fread.read()
                coords = literal_eval(coords)
                self.aug_rotate(im, coords, fpath)
                self.aug_flip(im, coords, fpath)
                percent = int(i / len(files) * 100)
                cls.update_progressbar.emit(percent)
        if cls:
            cls.update_progressbar.emit(100)
            self.enable_buttons()
            cls.update_label.emit('Augmentation done')

    def aug_rotate(self, im, coords, fpath):
        for i in range(3):
            im = im.rotate(90)
            path = fpath.replace(self.aug_dir + '/', self.aug_dir +
                                 '/aug/').replace('.png', 'R_' + str(i) + '.png')
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
            path = fpath.replace(self.aug_dir + '/', self.aug_dir +
                                 '/aug/').replace('.png', 'F_' + str(i) + '.png')
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

    def merge(self, cls=None):
        if cls:
            cls.update_label.emit('Merging folders...')
        print(self.parent_widget.merge_src_dirs.copy())
        print(self.parent_widget.merge_dst_dir)
        self.i_progress = 0
        inpaths = self.parent_widget.merge_src_dirs.copy()
        inpaths = list(map(lambda x: x + '/', inpaths))
        print(inpaths)
        outpath = self.parent_widget.merge_dst_dir + '/'
        ncopy = 0  # Might be changed to num of last el + 1
        old_percent = 0
        nb_files = sum([len(files) for inpath in inpaths for r, d, files in walk(inpath) if 'test' not in d])

        # if outpath not in listdir():
        #     mkdir(outpath)
        for inpath in inpaths:
            print(inpath)
            for dirname, subdirs, fnames in walk(inpath):
                print(dirname, fnames)
                if 'test' in dirname:
                    continue
                for fname in fnames:
                    self.i_progress += 1
                    if fname.endswith('.png'):
                        src_png = dirname + '\\' + fname
                        src_txt = dirname + '\\' + fname.replace('.png', '.txt')
                        # print(src_png, src_txt)
                        if not exists(src_png) or not exists(src_txt):
                            # print("doesn't exist")
                            continue
                        copy2(src_png, outpath + 'img_' + str(ncopy) + '.png')
                        copy2(src_txt, outpath + 'img_' + str(ncopy) + '.txt')
                        ncopy += 1
                        percent = int(self.i_progress / nb_files * 100)
                        if cls and percent != old_percent:
                            cls.update_progressbar.emit(percent)
                            old_percent = percent
        if cls:
            cls.update_progressbar.emit(100)
            self.enable_buttons()
            cls.update_label.emit('Merging folders done')
            print(outpath)

    def check(self, cls=None):
        if cls:
            cls.update_label.emit('Checking files...')
        print(self.check_dir)
        print(listdir(self.check_dir + '/aug/'))
        if 'aug_test' not in listdir(self.check_dir + '/aug/'):
            mkdir(self.check_dir + '/aug/aug_test/')
        files = sorted(listdir(self.check_dir + "/aug/"))
        print(files)
        for num, file in enumerate(files):
            if file.endswith(".png"):
                img = cv2.imread(self.check_dir + "/aug/" + file)
                txt = file.replace('.png', '.txt')
                with open(self.check_dir + "/aug/" + txt, "r") as fread:
                    coords = fread.read()
                for i, coord in enumerate(literal_eval(coords)):
                    img = cv2.circle(img, coord, radius=3, color=(0, 0, 255), thickness=-1)
                    img = cv2.putText(img, str(i + 1), (coord[0] + 5, coord[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                      (0, 0, 255), 1)
                cv2.imwrite(self.check_dir + "/aug/aug_test/" + file.replace('.png', '_test.png'), img)
                # print(self.check_dir + "/aug/aug_test/" + file.replace('.png', '_test.png'))
            percent = int(num / len(files) * 100)

            if cls:
                cls.update_progressbar.emit(percent)
        if cls:
            cls.update_progressbar.emit(100)
            self.enable_buttons()
            cls.update_label.emit('Checking files done')

    def difference_images(self, h1, h2, f1, f2, path=''):
        if (h1 == h2):
            self.rm_images.append((path + f1, path + f2, str(h1)))
        return

    def make_hash(self, array, path='', cls=None):
        cls.update_label.emit('Extracting hashes...')
        hashes = []
        for i, el in enumerate(array):
            img = Image.open(path + el)
            hash = imagehash.phash(img)
            hashes.append(hash)
            if cls:
                percent = int(i / len(array) * 100)
                cls.update_progressbar.emit(percent)
        return hashes

    def compare(self, cls=None):
        start = time()
        self.i_progress = 0
        self.rm_images = []
        if cls:
            cls.update_progressbar.emit(0)

        path = self.parent_widget.merge_dst_dir + '/'
        imgs = sorted(filter(lambda x: x.endswith('.png'), listdir(path)),
                      key=lambda x: int(x.replace('img_', '').replace('.png', '')))
        print(imgs)
        nb_images = len(list(combinations(imgs, 2)))  # Should be replaced with formula

        hashes = self.make_hash(imgs, path, cls)

        check_file = 0  # Проверяемый файл
        current_file = 0  # Текущий файл
        old_percent = 0  # percent

        while check_file < len(hashes) and current_file < len(hashes):
            cls.update_label.emit('Comparison hashes...')
            self.i_progress += 1
            percent = int(self.i_progress / nb_images * 100)
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
        self.enable_buttons()
        cls.update_label.emit('Comparison done')
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

# Добавить настройки папок для check и др...
# 4eb0ff
# pyinstaller --onefile --noconsole --icon=aug_icon.ico aug.py
# Повторяющиеся хэши ???
