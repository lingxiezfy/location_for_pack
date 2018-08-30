# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\PycharmProjects\MiniPythonPro\location_for_pack\login.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LoginForm(object):
    def setupUi(self, LoginForm):
        LoginForm.setObjectName("LoginForm")
        LoginForm.resize(385, 242)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Pack_24px.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        LoginForm.setWindowIcon(icon)
        self.login_line_edit = QtWidgets.QLineEdit(LoginForm)
        self.login_line_edit.setGeometry(QtCore.QRect(150, 40, 161, 31))
        self.login_line_edit.setObjectName("login_line_edit")
        self.login_lable = QtWidgets.QLabel(LoginForm)
        self.login_lable.setGeometry(QtCore.QRect(80, 40, 61, 31))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.login_lable.setFont(font)
        self.login_lable.setObjectName("login_lable")
        self.login_pwd_line_edit = QtWidgets.QLineEdit(LoginForm)
        self.login_pwd_line_edit.setGeometry(QtCore.QRect(150, 100, 161, 31))
        self.login_pwd_line_edit.setObjectName("login_pwd_line_edit")
        self.login_pwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login_pwd_lable = QtWidgets.QLabel(LoginForm)
        self.login_pwd_lable.setGeometry(QtCore.QRect(80, 100, 61, 31))
        font = QtGui.QFont()
        font.setFamily("Aharoni")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.login_pwd_lable.setFont(font)
        self.login_pwd_lable.setObjectName("login_pwd_lable")
        self.login_btn = QtWidgets.QPushButton(LoginForm)
        self.login_btn.setGeometry(QtCore.QRect(240, 180, 91, 31))
        self.login_btn.setObjectName("login_btn")
        self.login_msg_lable = QtWidgets.QLabel(LoginForm)
        self.login_msg_lable.setGeometry(QtCore.QRect(30, 150, 291, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setStrikeOut(False)
        self.login_msg_lable.setFont(font)
        self.login_msg_lable.setStyleSheet("color:rgb(255, 0, 0)")
        self.login_msg_lable.setText("")
        self.login_msg_lable.setObjectName("login_msg_lable")

        self.retranslateUi(LoginForm)
        QtCore.QMetaObject.connectSlotsByName(LoginForm)

    def retranslateUi(self, LoginForm):
        _translate = QtCore.QCoreApplication.translate
        LoginForm.setWindowTitle(_translate("LoginForm", "套装打包-员工登录"))
        LoginForm.setFixedSize(LoginForm.width(),LoginForm.height())
        self.login_lable.setText(_translate("LoginForm", "工  号"))
        self.login_pwd_lable.setText(_translate("LoginForm", "密    码"))
        self.login_btn.setText(_translate("LoginForm", "登   录"))

    def updateLoginMsg(self, msg_str):
        _translate = QtCore.QCoreApplication.translate
        self.login_msg_lable.setText(_translate("LoginForm", msg_str))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QWidget()
    ui = Ui_LoginForm()
    ui.setupUi(widget)
    widget.show()
    sys.exit(app.exec_())
