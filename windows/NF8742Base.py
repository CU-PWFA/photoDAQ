# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NF8742.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DriverWindow(object):
    def setupUi(self, DriverWindow):
        DriverWindow.setObjectName("DriverWindow")
        DriverWindow.resize(252, 635)
        self.centralwidget = QtWidgets.QWidget(DriverWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.abortButton = QtWidgets.QPushButton(self.centralwidget)
        self.abortButton.setGeometry(QtCore.QRect(60, 260, 131, 27))
        self.abortButton.setStyleSheet("QPushButton{ background-color: rgb(255, 0, 0); }\n"
"QPushButton{color:white;}\n"
"")
        self.abortButton.setObjectName("abortButton")
        self.setAccelButton = QtWidgets.QPushButton(self.centralwidget)
        self.setAccelButton.setGeometry(QtCore.QRect(0, 490, 141, 31))
        self.setAccelButton.setObjectName("setAccelButton")
        self.setVelocityButton = QtWidgets.QPushButton(self.centralwidget)
        self.setVelocityButton.setGeometry(QtCore.QRect(0, 460, 141, 31))
        self.setVelocityButton.setObjectName("setVelocityButton")
        self.outputText = QtWidgets.QTextBrowser(self.centralwidget)
        self.outputText.setGeometry(QtCore.QRect(0, 520, 251, 61))
        self.outputText.setObjectName("outputText")
        self.homeButton = QtWidgets.QPushButton(self.centralwidget)
        self.homeButton.setGeometry(QtCore.QRect(80, 140, 91, 71))
        self.homeButton.setObjectName("homeButton")
        self.setVelocityText = QtWidgets.QTextEdit(self.centralwidget)
        self.setVelocityText.setGeometry(QtCore.QRect(140, 460, 111, 31))
        self.setVelocityText.setObjectName("setVelocityText")
        self.setAccelerationText = QtWidgets.QTextEdit(self.centralwidget)
        self.setAccelerationText.setGeometry(QtCore.QRect(140, 490, 111, 31))
        self.setAccelerationText.setObjectName("setAccelerationText")
        self.positionLabel = QtWidgets.QLabel(self.centralwidget)
        self.positionLabel.setGeometry(QtCore.QRect(60, 70, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.positionLabel.setFont(font)
        self.positionLabel.setObjectName("positionLabel")
        self.setHomeButton = QtWidgets.QPushButton(self.centralwidget)
        self.setHomeButton.setGeometry(QtCore.QRect(0, 430, 141, 31))
        self.setHomeButton.setObjectName("setHomeButton")
        self.setHomeText = QtWidgets.QTextEdit(self.centralwidget)
        self.setHomeText.setGeometry(QtCore.QRect(140, 430, 111, 31))
        self.setHomeText.setObjectName("setHomeText")
        self.upButton = QtWidgets.QPushButton(self.centralwidget)
        self.upButton.setGeometry(QtCore.QRect(80, 100, 91, 41))
        self.upButton.setObjectName("upButton")
        self.downButton = QtWidgets.QPushButton(self.centralwidget)
        self.downButton.setGeometry(QtCore.QRect(80, 210, 91, 41))
        self.downButton.setObjectName("downButton")
        self.rightButton = QtWidgets.QPushButton(self.centralwidget)
        self.rightButton.setGeometry(QtCore.QRect(170, 140, 51, 71))
        self.rightButton.setObjectName("rightButton")
        self.leftButton = QtWidgets.QPushButton(self.centralwidget)
        self.leftButton.setGeometry(QtCore.QRect(30, 140, 51, 71))
        self.leftButton.setObjectName("leftButton")
        self.absoluteCheck = QtWidgets.QCheckBox(self.centralwidget)
        self.absoluteCheck.setGeometry(QtCore.QRect(10, 310, 221, 22))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.absoluteCheck.setFont(font)
        self.absoluteCheck.setObjectName("absoluteCheck")
        self.relativeCheck = QtWidgets.QCheckBox(self.centralwidget)
        self.relativeCheck.setGeometry(QtCore.QRect(10, 330, 211, 22))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.relativeCheck.setFont(font)
        self.relativeCheck.setObjectName("relativeCheck")
        self.moveToButton = QtWidgets.QPushButton(self.centralwidget)
        self.moveToButton.setGeometry(QtCore.QRect(0, 370, 141, 31))
        self.moveToButton.setObjectName("moveToButton")
        self.setStepText = QtWidgets.QTextEdit(self.centralwidget)
        self.setStepText.setGeometry(QtCore.QRect(140, 400, 111, 31))
        self.setStepText.setObjectName("setStepText")
        self.setStepButton = QtWidgets.QPushButton(self.centralwidget)
        self.setStepButton.setGeometry(QtCore.QRect(0, 400, 141, 31))
        self.setStepButton.setObjectName("setStepButton")
        self.moveToText = QtWidgets.QTextEdit(self.centralwidget)
        self.moveToText.setGeometry(QtCore.QRect(140, 370, 111, 31))
        self.moveToText.setObjectName("moveToText")
        self.indMoveCheck = QtWidgets.QCheckBox(self.centralwidget)
        self.indMoveCheck.setGeometry(QtCore.QRect(10, 290, 221, 22))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.indMoveCheck.setFont(font)
        self.indMoveCheck.setObjectName("indMoveCheck")
        self.mirrorSelectionCombo = QtWidgets.QComboBox(self.centralwidget)
        self.mirrorSelectionCombo.setGeometry(QtCore.QRect(80, 40, 85, 27))
        self.mirrorSelectionCombo.setObjectName("mirrorSelectionCombo")
        self.driverSerialText = QtWidgets.QLabel(self.centralwidget)
        self.driverSerialText.setGeometry(QtCore.QRect(30, 0, 191, 31))
        font = QtGui.QFont()
        font.setPointSize(22)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.driverSerialText.setFont(font)
        self.driverSerialText.setObjectName("driverSerialText")
        DriverWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(DriverWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 252, 25))
        self.menubar.setObjectName("menubar")
        DriverWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(DriverWindow)
        self.statusbar.setObjectName("statusbar")
        DriverWindow.setStatusBar(self.statusbar)

        self.retranslateUi(DriverWindow)
        QtCore.QMetaObject.connectSlotsByName(DriverWindow)

    def retranslateUi(self, DriverWindow):
        _translate = QtCore.QCoreApplication.translate
        DriverWindow.setWindowTitle(_translate("DriverWindow", "MainWindow"))
        self.abortButton.setText(_translate("DriverWindow", "ABORT MOTION"))
        self.setAccelButton.setText(_translate("DriverWindow", "SET ACCELERATION"))
        self.setVelocityButton.setText(_translate("DriverWindow", "SET VELOCITY"))
        self.outputText.setHtml(_translate("DriverWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">OUTPUT:</p></body></html>"))
        self.homeButton.setText(_translate("DriverWindow", "HOME"))
        self.setVelocityText.setHtml(_translate("DriverWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">2000</p></body></html>"))
        self.setAccelerationText.setHtml(_translate("DriverWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">100000</p></body></html>"))
        self.positionLabel.setText(_translate("DriverWindow", "Position: (0,0)"))
        self.setHomeButton.setText(_translate("DriverWindow", "SET HOME (X,Y)"))
        self.setHomeText.setHtml(_translate("DriverWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">0,0</p></body></html>"))
        self.upButton.setText(_translate("DriverWindow", "UP"))
        self.downButton.setText(_translate("DriverWindow", "DOWN"))
        self.rightButton.setText(_translate("DriverWindow", "RIGHT"))
        self.leftButton.setText(_translate("DriverWindow", "LEFT"))
        self.absoluteCheck.setText(_translate("DriverWindow", "ABSOLUTE MOTION"))
        self.relativeCheck.setText(_translate("DriverWindow", "RELATIVE MOTION"))
        self.moveToButton.setText(_translate("DriverWindow", "MOVE TO (X,Y)"))
        self.setStepText.setHtml(_translate("DriverWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">10</p></body></html>"))
        self.setStepButton.setText(_translate("DriverWindow", "SET STEP"))
        self.moveToText.setHtml(_translate("DriverWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">0,0</p></body></html>"))
        self.indMoveCheck.setText(_translate("DriverWindow", "INDEFINTE MOTION"))
        self.driverSerialText.setText(_translate("DriverWindow", "Driver #0000"))

