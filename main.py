import sys
from os.path import exists

import cv2
from ast import literal_eval
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
        self.setWindowIcon(QtGui.QIcon('res/app_icon.png'))
        self.painter = Painter()
        self.setCentralWidget(self.painter)
        # Тулбар с кнопками
        layout = QGridLayout()
        tb = self.addToolBar("File")
        add = QAction(QIcon("res/aim_icon.png"), "Add keypoints", self)
        add.triggered.connect(self.painter.addKP)
        tb.addAction(add)
        stop = QAction(QIcon("res/draw_icon.png"), "Add sketch", self)
        stop.triggered.connect(self.painter.stopKP)
        tb.addAction(stop)
        clear = QAction(QIcon("res/clear_icon.png"), "Clear all", self)
        clear.triggered.connect(self.painter.clear)
        tb.addAction(clear)
        mgnt = QAction(QIcon("res/magnet_icon.png"), "Magnet", self)
        mgnt.triggered.connect(self.painter.magnet)
        tb.addAction(mgnt)
        self.savebutton = QAction(QIcon("res/save_icon.png"), "Save", self)
        self.savebutton.triggered.connect(self.painter.save)
        tb.addAction(self.savebutton)
        self.checkbutton = QAction(QIcon("res/check_icon.png"), "check", self)
        self.checkbutton.triggered.connect(self.painter.check)
        tb.addAction(self.checkbutton)
        self.setLayout(layout)
        self.setWindowTitle("Sketcher. Beta")


# Центральный виджет
class Painter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.drawing = False  # Режим рисования
        self.kp_mode = False  # Режим ключевых точек
        self.last_point = QPoint()  # Последняя точка рисунка
        self.setGeometry(100, 100, 500, 500)
        self.setFixedSize(self.width(), self.height())
        self.pixmap = QPixmap(self.width(), self.height())  # Холст
        self.pixmap.fill(QColor("white"))
        self.setWindowTitle('Drawer')
        self.color = Qt.black
        self.kp_text = 1  # Нумерация ключевых точек
        self.undo_kp_text = 1  # Сохранение нумерации ключевых точек для отмены
        self.kp_list = []  # Список координат ключевых точек
        self.redo_kp_list = []  # Список координат ключевых точек для повтора
        self.undo_kp_list = []  # Список координат ключевых точек для отмены
        self.extra_kp_list = []
        self.sketch = None  # Непосредственно рисунок без ключевых точек
        self.undo_sketch = None  # Для отмены
        self.undo_actions_type = []  # Для отмены
        self.redo_actions_type = []  # Для повтора
        self.undo_states = []  # Для отмены. Предыдущие действия
        self.redo_states = []  # Для повтора
        undo_shcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self)
        undo_shcut.activated.connect(self.undo)
        redo_shcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Z"), self)
        redo_shcut.activated.connect(self.redo)
        img_digits = []  # Список чисел после имен файлов (img_"33")
        img_flag = False  # Есть ли хоть один файл-изображение?
        for fname in sorted(listdir('out/')):  # Ищем номер последнего изображения
            if 'img_' in fname:
                img_flag = True
                ff = '.'.join(fname.split('.')[:-1])
                img_digit = ff.split('_')[-1]
                img_digits.append(img_digit)
        if img_flag:  # Номер последнего изображения + 1
            self.nimg = int(max(map(int, img_digits))) + 1
        else:
            self.nimg = 1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.undo_states.append(self.pixmap.copy())
            if len(self.undo_states) > 3:  # Сохраняем не больше 3х последних действий
                del self.undo_states[0]
            self.redo_actions_type.clear()  # Как только внесли изменение в отмененное состояние,
            self.redo_states.clear()  # Теряем возможность повторить действия
            self.drawing = True
            self.last_point = event.pos()
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(self.color, 3, Qt.SolidLine))
            if self.kp_mode:  # Режим ключевых точек
                painter.drawEllipse(event.pos(), 6, 6)
                painter.setFont(QFont('Arial', 10))
                painter.drawText(event.x() + 5, event.y() + 20, str(self.kp_text))
                self.kp_text += 1
                self.kp_list.append((event.x(), event.y()))
                self.undo_actions_type.append('kp')
            else:  # Рисуем обычную точку
                painter.drawPoint(event.pos())
                self.undo_actions_type.append('draw')
            self.update()

    def mouseMoveEvent(self, event):  # Рисуем набросок
        if event.buttons() and Qt.LeftButton and self.drawing and not self.kp_mode:
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(self.color, 3, Qt.SolidLine))
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):  # Отпускаем мышь
        if event.button == Qt.LeftButton:
            self.drawing = False

    def addKP(self):  # Добавляем ключевую точку
        if not self.undo_actions_type or self.undo_actions_type[-1] == 'clear':
            # Если нет действий для отмены
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
        if len(self.undo_states) > 3:  # Храним не больше 3х действий для отмены
            del self.undo_states[0]
        if self.sketch:  # Сохраняем набросок без точек
            self.pixmap = self.sketch
        self.undo_kp_list = self.kp_list.copy()  # Сохраняем точки для отмены
        self.redo_kp_list.clear()  # Очищаем точки для ctrl+sh+z
        self.kp_list.clear()  # Очищаем текущий список точек
        # print(self.kp_list) For debug
        self.undo_kp_text = self.kp_text
        self.kp_text = 1
        self.undo_actions_type.append('stopkp')  # Добавляем тип действия в список для отмены
        self.kp_mode = False  # Вышли из режима ключевых точек
        self.update()

    def save(self):  # Сохраняем результат
        if not self.kp_list:
            return
        filename = f'out/img_{self.nimg}.png'
        self.save_img(filename)  # Сохраняем набросок
        with open(filename.replace('png', 'txt'), 'w') as f:
            f.write(str(self.kp_list))  # И текстовый файл с координатами
        self.nimg += 1

    def clear(self):  # Нужно сохранять ключевые точки при очистке
        if self.undo_actions_type and self.undo_actions_type[-1] == 'clear':
            return  # Если нет действий для отмены
        self.undo_states.append(self.pixmap.copy())  # Копируем холст
        if len(self.undo_states) > 3:  # Отмена действий - не больше 3х
            del self.undo_states[0]
        self.pixmap.fill(QColor("white"))
        self.undo_kp_text = self.kp_text  # Сохраняем нумерацию для отмены
        self.kp_text = 1  # Сбрасываем нумерацию при очистке
        self.undo_kp_list = self.kp_list.copy()  # Сохраняем точки для отмены
        self.kp_list.clear()  # Очищаем текущий
        self.redo_kp_list.clear()  # для повтора
        if self.sketch:  # Скетч для отмены
            self.undo_sketch = self.sketch.copy()
        self.sketch = None
        self.undo_actions_type.append('clear')  # Добавляем в список тип действия
        self.kp_mode = False
        self.color = Qt.black
        self.update()

    def redo(self):  # Повтор действия, возврат к предыдущему состоянию
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
                actype = self.redo_actions_type.pop()  # Извлекаем последнее действие из
                # списка для повтора
                # print(actype, 'r') for debug
                if actype == 'kp':  # Если действие = добавление ключевой точки
                    self.kp_list.append(self.redo_kp_list.pop())
                    self.kp_text += 1
                if actype == 'clear' or actype == 'stopkp':  # Если последнее действие было "Clear"
                    self.undo_kp_list = self.redo_kp_list.copy()
                    self.kp_list = []
                    self.redo_kp_list = []
                    self.kp_text = 1
                if actype == 'magnet':  # Если действие = магнит
                    self.kp_list = self.redo_kp_list.copy()
                    self.redo_kp_list = []
                    self.redo_states = []
                self.undo_actions_type.append(actype)  # Тип последнего действия
            if len(self.undo_states) > 3:
                del self.undo_states[0]
            # print(self.kp_list, ' ||| ', self.redo_kp_list, ' ||| ', self.undo_kp_list) for debug
            self.update()

    def undo(self):  # Отмена действия, возврат к предыдущему состоянию
        if self.undo_states:
            self.redo_states.append(self.pixmap)
            self.pixmap = self.undo_states.pop()
            if self.undo_actions_type:
                actype = self.undo_actions_type.pop()
                print(actype, 'u')
                if actype == 'kp':  # Если последнее действие было "KP" - добавление ключевой точки
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
            # print(self.kp_list, ' ||| ', self.redo_kp_list, ' ||| ', self.undo_kp_list)
            self.update()

    def save_img(self, filename):  # Сохранение изображения наброска (!) без ключевых точек
        if self.sketch:
            self.sketch.save(filename, 'png')
        else:
            self.pixmap.save(filename, 'png')

    def magnet(self):  # Сдвинуть ключевые точки к границам контура
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
        for kp in self.kp_list:  # Собственно сдвиг для каждой точки
            # Ищем ближайший контур по окружности
            distances = np.sqrt((nonzero[:, :, 0] - kp[0]) ** 2 + (nonzero[:, :, 1] - kp[1]) ** 2)
            nearest_index = np.argmin(distances)
            fixed_kp = nonzero[nearest_index, 0]  # Обновляем координаты точки
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(Qt.blue, 3, Qt.SolidLine))
            painter.drawEllipse(*fixed_kp, 6, 6)
            painter.setFont(QFont('Arial', 10))
            painter.drawText(fixed_kp[0] + 5, fixed_kp[1] + 20,
                             str(self.kp_text))  # Перерисовываем надпись ключевой точки
            painter = None  # Important !
            self.kp_text += 1
            fixed_kplist.append(tuple(fixed_kp))
        self.update()
        self.kp_list = fixed_kplist
        # print(self.kp_list, ' ||| ', self.redo_kp_list, ' ||| ', self.undo_kp_list) for debug

    def check(self):  # Инструмент Check накладывает координаты на готовые изображения набросков
        for file in sorted(listdir("out/")):  # Папка исходников
            if file.endswith(".png"):  # Изображения
                img = cv2.imread("out/" + file)
                txt = file.replace('.png', '.txt')
                if not exists("out/" + file) or not exists("out/" + txt):
                    continue  # Если не нашлось файла с координатами
                    # для текущего изображения - идем далее
                with open("out/" + txt, 'r') as fread:
                    coords = fread.read()
                for i, coord in enumerate(literal_eval(coords)):
                    img = cv2.circle(img, coord, radius=3, color=(0, 0, 255), thickness=-1)
                    img = cv2.putText(img, str(i + 1), (coord[0] + 5, coord[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                      (0, 0, 255), 1)  # Рисуем-рисуем
                cv2.imwrite("out/test/" + file.replace('.png', '_test.png'), img)  # Сохраняем в папку res


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
# 4eb0ff
