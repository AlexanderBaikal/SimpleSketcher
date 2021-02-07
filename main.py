import sys
import cv2
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, \
    QMainWindow, QAction
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QIcon
from os import listdir


class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('sk_icon.png'))
        self.painter = Painter()
        self.setCentralWidget(self.painter)
        # Toolbar
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
        tb.addAction(self.savebutton)
        self.setLayout(layout)
        self.setWindowTitle("Sketcher. Beta")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_enabled()


class Painter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.drawing = False
        self.kp_mode = False
        self.last_point = QPoint()
        self.setGeometry(100, 100, 500, 500)
        self.setFixedSize(self.width(), self.height())
        self.pixmap = QPixmap(self.width(), self.height())
        self.pixmap.fill(QColor("white"))
        self.setWindowTitle('Drawer')
        self.color = Qt.black
        self.kp_text = 1
        self.undo_kp_text = 1
        self.kp_list = []
        self.redo_kp_list = []
        self.undo_kp_list = []
        self.extra_kp_list = []
        self.sketch = None
        self.undo_sketch = None
        self.undo_actions_type = []
        self.redo_actions_type = []
        self.undo_states = []
        self.redo_states = []
        undo_shcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self)
        undo_shcut.activated.connect(self.undo)
        redo_shcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Z"), self)
        redo_shcut.activated.connect(self.redo)
        img_digits = []
        img_flag = False
        for fname in sorted(listdir('out/')):  # Ищем номер последнего изображения
            if 'img_' in fname:
                img_flag = True
                ff = '.'.join(fname.split('.')[:-1])
                img_digit = ff.split('_')[-1]
                img_digits.append(img_digit)
        if img_flag:
            self.nimg = int(max(map(int, img_digits))) + 1
        else:
            self.nimg = 1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.undo_states.append(self.pixmap.copy())
            if len(self.undo_states) > 3:
                del self.undo_states[0]
            self.redo_actions_type.clear()  # Как только внесли изменение в отмененное состояние,
            self.redo_states.clear()  # Теряем возможность повторить действия
            self.drawing = True
            self.last_point = event.pos()
            if self.kp_mode:
                painter = QPainter(self.pixmap)
                painter.setPen(QPen(self.color, 3, Qt.SolidLine))
                painter.drawEllipse(event.pos(), 6, 6)
                painter.setFont(QFont('Arial', 10))
                painter.drawText(event.x() + 5, event.y() + 20, str(self.kp_text))
                self.kp_text += 1
                self.kp_list.append((event.x(), event.y()))
                self.undo_actions_type.append('kp')
                self.update()
            else:
                self.undo_actions_type.append('draw')

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawing and not self.kp_mode:
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(self.color, 3, Qt.SolidLine))
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            self.drawing = False

    def addKP(self):
        if not self.undo_actions_type or self.undo_actions_type[-1] == 'clear':
            return
        self.color = Qt.blue
        if not self.sketch:
            self.sketch = self.pixmap.copy()
        self.kp_mode = True

    def stopKP(self):  # Переключение на рисование
        if not self.undo_actions_type:
            return
        self.color = Qt.black
        self.undo_states.append(self.pixmap.copy())
        if len(self.undo_states) > 3:
            del self.undo_states[0]
        if self.sketch:
            self.pixmap = self.sketch
        self.undo_kp_list = self.kp_list.copy()
        self.redo_kp_list.clear()
        self.kp_list.clear()
        print(self.kp_list)
        self.undo_kp_text = self.kp_text
        self.kp_text = 1
        self.undo_actions_type.append('stopkp')
        self.kp_mode = False
        self.update()

    def save(self):
        if not self.kp_list:
            return
        filename = f'out/img_{self.nimg}.png'
        self.save_img(filename)
        with open(filename.replace('png', 'txt'), 'w') as f:
            f.write(str(self.kp_list))
        self.nimg += 1

    def clear(self):  # Нужно сохранять ключевые точки при очистке !!!
        if self.undo_actions_type and self.undo_actions_type[-1] == 'clear':
            return
        self.undo_states.append(self.pixmap.copy())
        if len(self.undo_states) > 3:
            del self.undo_states[0]
        self.pixmap.fill(QColor("white"))
        self.undo_kp_text = self.kp_text  # Сохраняем нумерацию для отмены
        self.kp_text = 1
        self.undo_kp_list = self.kp_list.copy()  # Сохраняем точки для отмены
        self.kp_list.clear()
        self.redo_kp_list.clear()
        self.undo_sketch = self.sketch.copy()
        self.sketch = None
        self.undo_actions_type.append('clear')
        print(self.kp_list, ' ||| ', self.redo_kp_list, ' ||| ', self.undo_kp_list)
        self.kp_mode = False
        self.color = Qt.black
        self.update()

    def redo(self):
        if self.undo_actions_type and self.undo_actions_type[-1] == 'clear':
            # Если мы вернулись к очищенному холсту,
            # дальше нет смысла нажимать на повтор
            self.redo_states.clear()
            self.kp_text = 1
        if self.redo_states:
            self.undo_states.append(self.pixmap)
            self.pixmap = self.redo_states.pop()
            # Если крайний раз мы отменили добавление точки
            # Добавляем точку обратно в список
            if self.redo_kp_list and self.redo_actions_type:
                actype = self.redo_actions_type.pop()
                print(actype, 'r')
                if actype == 'kp':
                    self.kp_list.append(self.redo_kp_list.pop())
                    self.kp_text += 1
                if actype == 'clear' or actype == 'stopkp':  # Если последнее действие было "Clear"
                    self.undo_kp_list = self.redo_kp_list.copy()
                    self.kp_list = []
                    self.redo_kp_list = []
                    self.kp_text = 1
                if actype == 'magnet':
                    self.kp_list = self.redo_kp_list.copy()
                    self.redo_kp_list = []
                    self.redo_states = []
                self.undo_actions_type.append(actype)  # Тип последнего действия
            if len(self.undo_states) > 3:
                del self.undo_states[0]
            print(self.kp_list, ' ||| ', self.redo_kp_list, ' ||| ', self.undo_kp_list)
            self.update()

    def undo(self):
        if self.undo_states:
            self.redo_states.append(self.pixmap)
            self.pixmap = self.undo_states.pop()
            if self.undo_actions_type:
                actype = self.undo_actions_type.pop()
                print(actype, 'u')
                if actype == 'kp':  # Если последнее действие было "KP"
                    if self.kp_list:
                        self.redo_kp_list.append(self.kp_list.pop())  # Убираем точку из списка точек
                        self.kp_text -= 1
                if actype == 'clear' or actype == 'stopkp':  # Если последнее действие было "Clear"
                    if self.undo_kp_list:
                        self.kp_text = self.undo_kp_text
                        self.redo_kp_list = self.undo_kp_list.copy()
                        self.kp_list = self.undo_kp_list.copy()
                        self.redo_kp_list = []
                        self.undo_kp_list = self.extra_kp_list.copy()
                        if self.undo_sketch:
                            self.sketch = self.undo_sketch.copy()
                if actype == 'magnet':
                    self.redo_kp_list = self.kp_list.copy()
                    self.kp_list = self.undo_kp_list.copy()
                self.redo_actions_type.append(actype)
            if len(self.redo_states) > 3:
                del self.redo_states[0]
            print(self.kp_list, ' ||| ', self.redo_kp_list, ' ||| ', self.undo_kp_list)
            self.update()

    def save_img(self, filename):
        if self.sketch:
            self.sketch.save(filename, 'png')
        else:
            self.pixmap.save(filename, 'png')

    def magnet(self):  # Shift kp to borderlines
        if not self.kp_list:
            return
        self.extra_kp_list = self.kp_list.copy()
        filename = 'tmp/magnet.png'
        self.save_img(filename)
        img = cv2.imread(filename)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.bitwise_not(img)
        ret, img = cv2.threshold(img, 200, 255, 0)
        nonzero = cv2.findNonZero(img)
        self.undo_states.append(self.pixmap.copy())
        if len(self.undo_states) > 3:
            del self.undo_states[0]
        self.undo_kp_list = self.kp_list
        self.undo_kp_text = self.kp_text
        self.redo_kp_list.clear()
        self.undo_actions_type.append('magnet')
        self.pixmap = self.sketch.copy()
        fixed_kplist = []
        self.kp_text = 1
        for kp in self.kp_list:
            distances = np.sqrt((nonzero[:, :, 0] - kp[0]) ** 2 + (nonzero[:, :, 1] - kp[1]) ** 2)
            nearest_index = np.argmin(distances)
            fixed_kp = nonzero[nearest_index, 0]
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(Qt.blue, 3, Qt.SolidLine))
            painter.drawEllipse(*fixed_kp, 6, 6)
            painter.setFont(QFont('Arial', 10))
            painter.drawText(fixed_kp[0] + 5, fixed_kp[1] + 20, str(self.kp_text))
            painter = None  # Important !
            self.kp_text += 1
            fixed_kplist.append(tuple(fixed_kp))
        self.update()
        self.kp_list = fixed_kplist
        print(self.kp_list, ' ||| ', self.redo_kp_list, ' ||| ', self.undo_kp_list)


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
#   Должна выбираться точка, где контур
#   Если отменили и изменили, то не можем повторить
# Проверка точек из файла на холсте
# Повороты, аугментация
# Сохранение скетча после отмены, очистки, повторного добавления точек
# Disable кнопки
