# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(761, 746)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.connect = QtWidgets.QToolButton(self.centralwidget)
        self.connect.setObjectName("connect")
        self.horizontalLayout_2.addWidget(self.connect)
        self.pause = QtWidgets.QToolButton(self.centralwidget)
        self.pause.setObjectName("pause")
        self.horizontalLayout_2.addWidget(self.pause)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout_2.addWidget(self.line)
        self.clear = QtWidgets.QToolButton(self.centralwidget)
        self.clear.setObjectName("clear")
        self.horizontalLayout_2.addWidget(self.clear)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.output = QtWidgets.QTextEdit(self.centralwidget)
        self.output.setReadOnly(True)
        self.output.setObjectName("output")
        self.verticalLayout.addWidget(self.output)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mode = QtWidgets.QToolButton(self.centralwidget)
        self.mode.setObjectName("mode")
        self.horizontalLayout.addWidget(self.mode)
        self.input = QtWidgets.QLineEdit(self.centralwidget)
        self.input.setFrame(True)
        self.input.setObjectName("input")
        self.horizontalLayout.addWidget(self.input)
        self.crc = QtWidgets.QCheckBox(self.centralwidget)
        self.crc.setChecked(True)
        self.crc.setObjectName("crc")
        self.horizontalLayout.addWidget(self.crc)
        self.txButton = QtWidgets.QPushButton(self.centralwidget)
        self.txButton.setObjectName("txButton")
        self.horizontalLayout.addWidget(self.txButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.connect.setText(_translate("MainWindow", "connect"))
        self.pause.setText(_translate("MainWindow", "pause"))
        self.clear.setText(_translate("MainWindow", "clear"))
        self.mode.setText(_translate("MainWindow", "M"))
        self.crc.setText(_translate("MainWindow", "CRC"))
        self.txButton.setText(_translate("MainWindow", "Send"))

