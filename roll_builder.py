import os
import sys
import builder
from builder import Roll
from functools import partial

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

arr_roll = [1000, 1500, 1260, 1200]
arr_roll.sort()
roller = Roll()


class RollerBuilder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.desktop = QApplication.desktop()
        self.central_widget = QWidget()
        self.central_layout = QHBoxLayout()
        # self.central_widget.layout = self.central_layout
        self.central_widget.setLayout(self.central_layout)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)
        self.statusBar = self.statusBar()
        self.toolBar = self.addToolBar('TopToolbar')
        self.toolBarButton = [('Open', self.open_file),
                              ('Build roll', self.build),
                              ('Close', self.close_)]
        for but in self.toolBarButton:
            pushBut = QPushButton(but[0])
            pushBut.clicked.connect(but[1])
            self.toolBar.addWidget(pushBut)


        self.Max_w = False
        self.min_roll = 0

    def open_file(self):
        self.selected_width = []
        self.openFolder = QFileDialog().getExistingDirectory(self, 'Open file', 'D:/LayOutQC/') + '/'
        if self.openFolder != '/':
            for i in reversed(range(self.central_layout.count())):
                self.central_layout.itemAt(i).widget().deleteLater()
            dir_print = os.listdir(self.openFolder)
            # Checking open folder if empty
            if len(dir_print) < 1:
                self.popup(name_pop="Folder is empty")
                self.layoutPop_old.insertWidget(0, QLabel("Folder is empty"),
                                                alignment=Qt.AlignCenter)
                self.add_butClose()
                self.popUpModal.show()
                self.clear_toolbar()
            else:
                roller.read_files(dir_print, self.openFolder)
                roller.min_width_piece()
                self.min_roll = 0
                if roller.maxWidth_unit + 20 < max(arr_roll):
                    for widthRoll in arr_roll:
                        if widthRoll >= roller.maxWidth_unit + 20:
                            if self.min_roll == 0:
                                self.min_roll = widthRoll
                            self.selected_width.append(widthRoll)
                            roller.clear_DB()
                            roller.roll_constructor(widthRoll - 20, self.openFolder)
                            roller.count_efficiency(widthRoll - 20)
                            efficiency_str = QLabel('When width film  _________'
                                                    + str(widthRoll) + '\n' + roller.eff_str)
                            self.central_layout. addWidget(efficiency_str)
                else:
                    self.popup(name_pop="Too large layouts")
                    qq = QLabel('Too large layouts, no suitable film width! \n' + str(roller.maxWidth_unit))
                    qq.setAlignment(Qt.AlignCenter)
                    self.layoutPop_old.insertWidget(0, qq, alignment=Qt.AlignCenter)
                    self.add_butClose()
                    self.popUpModal.show()
                if self.min_roll != 0:
                    self.clear_toolbar()
                    self.Max_w = QLabel('     MAX width of layouts - ' + str(round(roller.maxWidth_unit)) + 'mm')
                    self.toolBar.addWidget(self.Max_w)
                    self.toolBar.addWidget(QLabel('     MIN width roll - '
                                                  + str(self.min_roll) + 'mm'))

    def clear_toolbar(self):
        if self.Max_w:
            self.toolBar.clear()
            for but in self.toolBarButton:
                pushBut = QPushButton(but[0])
                pushBut.clicked.connect(but[1])
                self.toolBar.addWidget(pushBut)

    def popup(self, x_w=300, y_h=100, name_pop='Massage'):
        self.popUpModal = QWidget(window, Qt.Tool)
        self.popUpModal.setWindowTitle(name_pop)
        self.popUpModal.setGeometry(self.desktop.width() / 2 - x_w / 2, self.desktop.height() / 2 - y_h / 2, x_w, y_h)
        self.popUpModal.setWindowModality(Qt.WindowModal)
        self.popUpModal.setAttribute(Qt.WA_DeleteOnClose, True)
        self.layoutPop_old = QVBoxLayout()
        self.layout_but = QHBoxLayout()
        self.layoutPop_old.addLayout(self.layout_but)
        self.popUpModal.setLayout(self.layoutPop_old)

    def add_butClose(self):
        self.butClose = QPushButton('Close')
        self.butClose.clicked.connect(self.popUpModal.close)
        self.layout_but.addWidget(self.butClose, alignment=Qt.AlignHCenter)

    def add_butOK(self, connect=None, text='OK'):
        self.butOK = QPushButton(text)
        if connect:
            self.butOK.clicked.connect(connect)
        self.butOK.clicked.connect(self.popUpModal.close)
        self.layout_but.addWidget(self.butOK)

    def build(self):
        if self.min_roll != 0:
            self.popup(name_pop="Build roll", x_w=200, y_h=200)
            self.add_butClose()
            n=0
            for w in self.selected_width:
                w_but = QPushButton(str(w))
                w_but.clicked.connect(partial(self.build_layout, w))
                self.layoutPop_old.insertWidget(n, w_but, alignment=Qt.AlignHCenter)
                n +=1
            self.popUpModal.show()

    def build_layout(self, w):
        self.popUpModal.close()
        roller.clear_DB()
        roller.roll_constructor(w - 20, self.openFolder)
        roller.layout_builder(w - 20, self.openFolder)
        self.popup(name_pop="Done")
        self.add_butClose()
        self.layoutPop_old.insertWidget(0, QLabel('Done!!!!'), alignment=Qt.AlignHCenter)
        self.popUpModal.show()
        print('--------DONE---------')

    def close_(self):
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RollerBuilder()
    window.setWindowTitle('Roller builder')
    window.resize(900, 300)
    window.show()
    sys.exit(app.exec_())

