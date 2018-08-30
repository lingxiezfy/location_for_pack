# -*- coding: utf-8 -*-
# @Time    : 2018/8/17 9:59
# @Author  : FrankZ
# @Email   : FrankZ981210@gmail.com
# @File    : Main
# @Software: PyCharm

from login_ui import Ui_LoginForm
from pack_ui import Ui_PackForm
from sql_helper import SqlService
# import psycopg2
import pymysql
from rpc_helper import RPCProxy
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QObject,QDate
from PyQt5.QtWidgets import QFileDialog,QDialog
from PyQt5.Qt import QColor,QFont
import re
import os
import time
import logging
import traceback
import xlwt
import configparser
from xmlrpc.client import ServerProxy


# 关闭信号
class CloseSignal(QObject):
    closeApp = pyqtSignal()


class LoginUI(QtWidgets.QWidget):
    def __init__(self):
        super(LoginUI, self).__init__()
        self.LoginForm = Ui_LoginForm()
        self.LoginForm.setupUi(self)

        self.operator = ""
        # 绑定点击事件处理器
        self.LoginForm.login_btn.clicked.connect(self.login_action)

    # 登录rpc检测
    def login(self, username, password):

        odoologinurl = ("http://%s:%s/xmlrpc/2/common" % (rpc_host, rpc_port))
        common = ServerProxy(odoologinurl)
        try:
            uid = common.authenticate(rpc_db, username, password, {})
        except ConnectionRefusedError as cre:
            logger.info("登录失败 - rpc连接失败-%s-%s - %s" % (rpc_host, rpc_port, cre.__repr__()))
            self.LoginForm.updateLoginMsg("连接数据失败！请检查网络")
            return False
        if uid:
            rpc = RPCProxy(uid, password, host=rpc_host, port=rpc_port, dbname=rpc_db)
            return_msg = rpc('res.users', 'search_read', [('id', '=', uid)], ['name'])
            self.operator = return_msg[0].get('name')
            logger.info("登录成功 - 用户-"+self.operator)
            return True
        else:
            logger.info("登录失败 - 工号或密码错误-%s-%s" % (username,password))
            self.LoginForm.updateLoginMsg("登录失败！工号或密码错误")
            return False

    # 回车登录
    def keyPressEvent(self, e):
        if str(e.key()) == "16777220":
            self.login_action()
        else:
            pass

    # 登录按钮事件响应
    def login_action(self):
        login = self.LoginForm.login_line_edit.text()
        pwd = self.LoginForm.login_pwd_line_edit.text()
        if login == '' or pwd == '':
            self.LoginForm.updateLoginMsg("工号和密码不能为空！")
        else:

            if self.login(login, pwd):
                # 创建信号，并连接到关闭自身插槽
                self.c = CloseSignal()
                self.c.closeApp.connect(self.close)
                # 触发信号关闭自身
                self.c.closeApp.emit()
                # 创建并打开PackForm
                self.PackForm = PackUI(self.operator)
                self.PackForm.show()


# 当系统前时间
def now_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class PackUI(QtWidgets.QWidget):
    def __init__(self, operator=None):
        super(PackUI, self).__init__()
        self.PackForm = Ui_PackForm()
        self.PackForm.setupUi(self)
        # 设置操作员显示
        self.PackForm.updateLoginLoginStatus(operator)
        self.operator = operator
        # 将库位号输入框设置成只接受数字
        self.PackForm.clear_single_le.setValidator(QtGui.QIntValidator(self))
        # 将数量输入框设置成只接受数字,上限100
        self.PackForm.add_number_le.setValidator(QtGui.QIntValidator(0, 100, self))
        # 将焦点定位至扫描枪输入位置
        self.PackForm.scan_jobnum_le.setFocus()
        # 录入按钮绑定事件
        self.PackForm.scan_btn.clicked.connect(self.scan_action)
        # 加载扫描历史
        self.scan_history_list = self.load_scan_history()
        # 一键清空满3副库位按钮绑定事件
        self.PackForm.clear_all_3_btn.clicked.connect(self.clear_all_full_action)
        # 单次清除按钮事件绑定
        self.PackForm.clear_single_btn.clicked.connect(self.clear_single_action)
        # 增加库位事件绑定
        self.PackForm.add_btn.clicked.connect(self.add_location_action)
        # 数据导出按钮事件绑定
        self.PackForm.export_btn.clicked.connect(self.export_action)

        # 控制选择
        self.PackForm.export_history_rb.clicked.connect(self.export_history_rb_click)
        self.PackForm.export_location_rb.clicked.connect(self.export_location_rb_click)
        # 设置显示当天日期
        self.PackForm.export_history_select_de.setDate(QDate.currentDate())
        self.show_location_sum()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, '警告', '你确认要退出吗？', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            logger.info("程序退出 - 用户-"+self.operator)
            event.accept()
        else:
            event.ignore()

    # 导出历史单选框选中事件响应
    def export_history_rb_click(self):
        self.PackForm.export_location_select_cb.setEnabled(False)
        self.PackForm.export_history_select_de.setEnabled(True)

    # 导出库位信息单选框选中事件响应
    def export_location_rb_click(self):
        self.PackForm.export_location_select_cb.setEnabled(True)
        self.PackForm.export_history_select_de.setEnabled(False)

    # 导出数据事件响应
    def export_action(self):
        export_dir = QFileDialog.getExistingDirectory(self, "选择文件夹", "/")
        if export_dir == "":
            pass
        else:
            try:
                if self.PackForm.export_location_rb.isChecked():
                    option = self.PackForm.export_location_select_cb.currentIndex()
                    self.export_location(option, export_dir)
                if self.PackForm.export_history_rb.isChecked():
                    option = self.PackForm.export_history_select_de.date()
                    self.export_history(option, export_dir)
            except Exception as e:
                print(traceback.format_exc())
                self.inset_list_front("导出失败（数据库连接失败，请检查网络）",now_time())
                logger.info("导出数据 - 导出失败 - %s", e.__repr__())
        # 使焦点回到扫描输入框
        self.PackForm.scan_jobnum_le.setFocus()

    # 导出历史数据
    def export_history(self,option,export_dir):

        sql='SELECT customerno as "客户号",opticianno "店号",ordernum "订单",locationid "库位号",quantity "商品数量",originalcreatetime "录入时间",originaloperator "扫描员",createtime "删除时间",operator "删除操作员" ' \
            ' FROM locationforpackhistory where originalcreatetime >= \''+option.toString("yyyy-MM-dd 00:00:00")+\
            '\' and originalcreatetime < \''+option.addDays(1).toString("yyyy-MM-dd 00:00:00")+\
            '\' ORDER BY locationid,createtime,originalcreatetime'
        db = SqlService(sql_util, host, port, user, pwd, database)
        cur = db.ExecForCursor(sql)
        db.CloseDB()
        export_excel(export_dir, "历史数据", cur)

    # 导出库位信息
    def export_location(self, option, export_dir):
        if option == 0:
            con = "quantity >= 1"
            name_str = "库位信息_全部"
        elif option == 3:
            con = "quantity >= 3"
            name_str = "库位信息_满3副"
        elif option == 1:
            name_str = "库位信息_1副"
            con = "quantity = " + str(option)
        else:
            name_str = "库位信息_2副"
            con = "quantity = " + str(option)
        sql = 'SELECT customerno as "客户号",opticianno "店号",ordernum "订单号",locationid "库位号",quantity "商品数量", createtime "完成时间",operator "扫描员" ' \
              'FROM locationforpack where ' + con + ' ORDER BY locationid'
        db = SqlService(sql_util, host, port, user, pwd, database)
        cur = db.ExecForCursor(sql)
        export_excel(export_dir, name_str, cur)
        db.CloseDB()

    # 回车监听
    def keyPressEvent(self, e):
        if str(e.key()) == "16777220":
            # 扫描输入过滤
            if self.PackForm.scan_jobnum_le.hasFocus():
                self.scan_action()
            else:
                pass
        else:
            pass

    # 单次清除按钮事件响应
    def clear_single_action(self):
        locationid = self.PackForm.clear_single_le.text()
        if locationid != "":
            reply = QtWidgets.QMessageBox.question(self, '警告', '确认清空库位 ' + locationid + ' ?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                logger.info("清空单个库位 - %s - 开始执行" % locationid)
                try:
                    result = self.clear_location(locationid)
                    if result == -1:
                        self.inset_list_front("库位 " + locationid + " 不存在！", now_time())
                    elif result == 0:
                        self.inset_list_front("库位 " + locationid + " 还未使用，无需清空！", now_time())
                    else:
                        self.inset_list_front("已清空库位 " + locationid, now_time())
                        logger.info("清空单个库位 - %s - 清空成功" % locationid)
                except Exception as e:
                    self.inset_list_front("清空库位 "+locationid+" 失败！(数据库连接失败，请检查网络)", now_time())
                    logger.info("清空单个库位 - %s - 清空失败-%s" % (locationid, e.__repr__()))

                logger.info("清空单个库位 - %s - 执行完成" % locationid)
        self.PackForm.clear_single_le.setText("")
        # 使焦点回到扫描输入框
        self.PackForm.scan_jobnum_le.setFocus()

    # 一键清空满3副库位按钮绑定事件响应
    def clear_all_full_action(self):
        reply = QtWidgets.QMessageBox.question(self, '警告', '确认清空所有满3副库位?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            logger.info("清空满3副库位 - 开始执行")
            try:
                result = self.clear_all_full_location()
                if len(result) > 0:
                    self.inset_list_front("已清空所有满3副库位", now_time())
                    logger.info("清空满3副库位 - 清空成功 - %s" % result.__repr__())
                else:
                    self.inset_list_front("暂无满3副库位", now_time())
                    logger.info("清空满3副库位 - 无需清空 - 无满3副库位")
            except Exception as e:
                self.inset_list_front("清空满3副库位失败！(数据库连接失败，请检查网络)",now_time())
                logger.info("清空满3副库位 - 清空失败-%s" % e.__repr__())
            logger.info("清空满3副库位 - 执行完成")
        # 使焦点回到扫描输入框
        self.PackForm.scan_jobnum_le.setFocus()

    # 清空单个库位
    def clear_location(self, locationid):
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql_data = "select quantity from locationforpack where locationid=" + locationid
        rows = db.ExecQuery(sql_data)
        if len(rows) == 0:
            return -1
        elif rows[0][0] == 0:
            return 0
        else:
            sql_history = "insert into locationforpackhistory SELECT locationforpack.*,'" + now_time() + "','" + self.operator + "' FROM locationforpack WHERE locationforpack.locationid=" + locationid
            db.ExecNonQuery(sql_history)

            sql = "UPDATE locationforpack set quantity=0 WHERE locationid=" + locationid
            db.ExecNonQuery(sql)
        db.CloseDB()
        return rows[0][0]

    # 清空所有满3套库位
    def clear_all_full_location(self):
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql_data = "select locationid from locationforpack where quantity >=3"
        rows = db.ExecQuery(sql_data)
        if len(rows) > 0:
            sql_history = "insert into locationforpackhistory SELECT locationforpack.*,'" + now_time() + "','" + self.operator + "' FROM locationforpack WHERE locationforpack.quantity>=3"
            db.ExecNonQuery(sql_history)
            sql = "UPDATE locationforpack set quantity=0 WHERE quantity>=3"
            db.ExecNonQuery(sql)
        db.CloseDB()
        return rows

    # 增加库位事件响应
    def add_location_action(self):
        num_str = self.PackForm.add_number_le.text()
        if num_str != "" and int(num_str) > 0:
            reply = QtWidgets.QMessageBox.question(self, '警告', '确认增加 ' + num_str + ' 个库位 ?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                logger.info("增加库位 -数量:%s- 开始执行" % num_str)
                try:
                    self.add_location(num_str)
                    self.inset_list_front("已增加 " + num_str + " 个库位 ", now_time())
                    logger.info("增加库位 -数量:%s- 增加成功" % num_str)
                except Exception as e:
                    print(traceback.format_exc())
                    self.inset_list_front("增加库位失败！(数据库连接失败，请检查网络)",now_time())
                    logger.info("增加库位 -数量:%s- 增加失败 - %s" % (num_str, e.__repr__()))
                logger.info("增加库位 -数量:%s- 执行完成" % num_str)
        self.PackForm.add_number_le.setText("")
        # 使焦点回到扫描输入框
        self.PackForm.scan_jobnum_le.setFocus()

    # 增加库位
    def add_location(self, num):
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql_data = 'SELECT max(locationid) from locationforpack'
        rows = db.ExecQuery(sql_data)
        if rows[0][0] is None:
            max_location = 0
        else:
            max_location = rows[0][0]
        temp_num = max_location + 1
        sql = "INSERT INTO locationforpack(locationid,ordernum,customerno,opticianno,createtime,operator)" \
              " VALUES("+str(temp_num)+",NULL,NULL,NULL,NULL,NULL)"
        temp_num = temp_num+1
        while temp_num <= max_location+int(num):
            sql += ",("+str(temp_num)+",NULL,NULL,NULL,NULL,NULL)"
            temp_num = temp_num + 1
        else:
            db.ExecNonQuery(sql)
        db.CloseDB()
        self.show_location_sum()

    # 显示库位总数
    def show_location_sum(self):
        logger.info("获取库位总数 - 开始执行")
        try:
            location_sum = self.get_location_sum()
            logger.info("获取库位总数 - 获取成功 - "+str(location_sum))
            self.PackForm.location_num_lable.setText(str(location_sum))
        except Exception as e:
            self.PackForm.location_num_lable.setText("未连接")
            logger.info("获取库位总数 - 获取失败 - "+e.__repr__())
            self.inset_list_front("数据库连接失败，请检查网络", now_time())
        logger.info("获取库位总数 - 执行完成")

    # 获取库位总数
    def get_location_sum(self):
        location_sum = 0
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql = "select count(*) from locationforpack"
        rows = db.ExecQuery(sql)
        location_sum = rows[0][0]
        db.CloseDB()
        return location_sum


    # 录入事件响应
    def scan_action(self):
        jobnum = self.PackForm.scan_jobnum_le.text()
        # 防止其他操作使扫描框失去焦点
        self.PackForm.scan_jobnum_le.setFocus()
        # 非空过滤
        if jobnum == "":
            return False
        logger.info("%s - 生产单号输入" % jobnum)
        self.PackForm.scan_jobnum_le.setText("")
        if self.is_job_num(jobnum):
            if self.is_scan_alreadly(jobnum):
                logger.info("%s - 生产单号重复扫描" % jobnum)
                self.inset_list_front("订单重复扫描！", now_time())
            else:
                logger.info("%s - 分配库位 - 开始执行" % jobnum)
                self.scan(jobnum)
                logger.info("%s - 分配库位 - 执行完成" % jobnum)
        else:
            logger.info("%s - 生产单号非法" % jobnum)
            self.inset_list_front("生产单号有误！(正确的为10位数字)", now_time())

    # 非jobnum过滤
    def is_job_num(self, jobnum):
        pattern = re.compile(r'^\d{10}$')
        if re.match(pattern, jobnum):
            return True
        return False

    # 录入并分配库位
    def scan(self, jobnum):
        createtime = now_time()
        try:
            order_info = self.get_order_info_lwr(jobnum)
            if order_info:
                order_num = order_info[0]
                opticianno = order_info[1]
                customerno = order_info[2]
                logger.info("%s - 分配库位 - 获取订单信息 - 获取成功 - %s" % (jobnum, order_info))
            else:
                logger.info("%s - 分配库位 - 获取订单信息 - 获取失败 - 未找到订单信息" % jobnum)
                self.inset_list_front("未找到订单信息！", createtime)
                return False
            logger.info("%s - 分配库位 - %s - 开始分配" % (jobnum, order_num))
            if self.is_location_full():
                logger.info("%s - 分配库位 - %s - 分配失败 - 所有库位均已满3副" % (jobnum, order_num))
                self.inset_list_front("所有库位均已满！请清理满3副库位", createtime)
            else:
                if self.is_pack_order(order_num):
                    order_num_s = self.split_order_num(order_num)
                    ordernum = order_num_s[0]
                    locationid = self.get_location(ordernum)
                    if locationid > 0:
                        # 更新数量+1
                        self.add_location_quantity(locationid)
                        logger.info("%s - 分配库位 - %s - 分配成功 - %s - 已有同一套订单" % (jobnum, order_num, locationid))
                        self.inset_list_front("分配成功！", createtime, ordernum=jobnum, locationid=locationid)
                        # 保存本次扫描历史
                        self.save_scan_history(jobnum)
                    else:
                        locationid = self.get_min_useful_location()
                        if locationid > 0:
                            # 记录数据库
                            self.insert_db_row(locationid, ordernum, customerno, opticianno, 1, createtime, self.operator)
                            logger.info("%s - 分配库位 - %s - 分配成功 - %s - 新订单" % (jobnum, order_num, locationid))
                            self.inset_list_front("分配成功！", createtime, ordernum=jobnum, locationid=locationid)
                            # 保存本次扫描历史
                            self.save_scan_history(jobnum)
                        else:
                            logger.info("%s - 分配库位 - %s - 分配失败 - 库位均被占用" % (jobnum, order_num))
                            self.inset_list_front("库位已满！请清理满3副库位", createtime)
                else:
                    logger.info("%s - 分配库位 - %s - 分配失败 - 非套装订单" % (jobnum, order_num))
                    self.inset_list_front("非套装订单！请检查", createtime)
        except Exception as e:
            logger.info("%s - 分配库位 - 分配失败 - %s" % (jobnum, e.__repr__()))
            self.inset_list_front("数据库连接失败！请检查网络", createtime)

    # 加载扫描历史
    def load_scan_history(self):
        return []

    # 保存本次扫描历史
    def save_scan_history(self, jobnum):
        self.scan_history_list.append(jobnum)



    # 单独更新数量
    def add_location_quantity(self, locationid):
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql = "UPDATE locationforpack set quantity=quantity+1 WHERE locationid=" + str(locationid)
        db.ExecNonQuery(sql)
        db.CloseDB()

    # 记录数据
    def insert_db_row(self, locationid, ordernum, customerno, opticianno, quantity, createtime, operator):
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql = "UPDATE locationforpack set ordernum='" + ordernum + "',customerno='" + customerno + "',opticianno='" \
              + opticianno + "',quantity=" + str(quantity) + ",createtime='" \
              + createtime + "',operator='" + operator + "' where locationid=" + str(locationid)
        db.ExecNonQuery(sql)
        db.CloseDB()

    # 获取最小可用库位,无可用库位返回-1
    def get_min_useful_location(self):
        locationid = 0
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql = "SELECT locationid from locationforpack where quantity = 0 ORDER BY locationid"
        rows = db.ExecQuery(sql)
        if len(rows) >= 1:
            locationid = rows[0][0]
        db.CloseDB()
        return locationid

    # 根据订单号获取库位，失败返回-1
    def get_location(self, ordernum):
        locationid = 0
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql = "SELECT locationid  from locationforpack WHERE ordernum = '" + ordernum + "' and quantity > 0"
        rows = db.ExecQuery(sql)
        db.CloseDB()
        if len(rows) >= 1:
            locationid = rows[0][0]
        return locationid

    # 非套装订单 过滤
    def is_pack_order(self, order_num):
        if order_num.count("-3-") == 1:
            return True
        return False

    # 库位是否满
    def is_location_full(self):
        db = SqlService(sql_util, host, port, user, pwd, database)
        sql = 'SELECT count(*) from locationforpack WHERE locationforpack.quantity < 3'
        rows = db.ExecQuery(sql)
        db.CloseDB()
        if rows[0][0] == 0:
            return True
        return False

    # 是否已经扫描
    def is_scan_alreadly(self, jobnum):
        if jobnum in self.scan_history_list:
            return True
        return False

    # 列表第一行插入提示消息
    def inset_list_front(self, message, now_time, **keywords):
        msg = now_time+" "
        if 'ordernum' in keywords:
            pass
            msg += "订单 " + str(keywords.get('ordernum')) + "  "
        if 'locationid' in keywords:
            pass
            msg += "库位【 " + str(keywords.get('locationid')) + " 】 "
        msg += message
        self.PackForm.scan_info_lv.insertItem(0, msg)
        font = QFont()
        font.setPointSize(13)
        self.PackForm.scan_info_lv.item(0).setBackground(QColor('yellow'))
        self.PackForm.scan_info_lv.item(0).setFont(font)
        if self.PackForm.scan_info_lv.count() > 1:
            self.PackForm.scan_info_lv.item(1).setBackground(QColor('white'))
        # 清除界面累计数据
        if self.PackForm.scan_info_lv.count() > 50:
            self.PackForm.scan_info_lv.takeItem(50)

    # 截取订单号
    def split_order_num(self, order_num):
        return order_num.split("-", 2)

    # 使用该函数需要替换 line：364 处，并修改sql_util参数为psycopg2 (line:578),并修改配置文件的dbms选项为PgSql
    # 根据jobnum获取订单信息
    def get_order_info(self, jobnum):
        order_info = None
        db = SqlService(sql_util, host, port, user, pwd, source_database)
        sql = "select order_num,optician_no,customer_id from sale_order_origin where job_num='" + jobnum + "'"
        rows = db.ExecQuery(sql)
        db.CloseDB()
        if len(rows) >= 1:
            order_info = rows[0]
        return order_info

    # 使用该函数需要替换 line：364 处，并修改sql_util参数为pymysql (line:577),并修改配置文件的dbms选项为Mysql
    # 根据jobnum获取lwr订单信息
    def get_order_info_lwr(self,jobnum):
        order_info = None
        db = SqlService(sql_util, host, port, user, pwd, source_database)
        sql = "SELECT Reference,CustNumb from order_header WHERE OrdNumbH ='          " + jobnum + "'"
        rows = db.ExecQuery(sql)
        db.CloseDB()
        if len(rows) >= 1:
            order_info = []
            temp_s = rows[0][0].split(" - ", 1)
            order_num = temp_s[1]
            opticianno = temp_s[0]
            customerno = rows[0][1].lstrip()
            order_info.append(order_num)
            order_info.append(opticianno)
            order_info.append(customerno)
        return order_info


# 导出excel
def export_excel(export_dir, file_name, cur):
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet(file_name, cell_overwrite_ok=True)
    results = cur.fetchall()
    fields = cur.description

    for field in range(0, len(fields)):
        sheet.write(0, field, fields[field][0])
        sheet.col(field).width = 0x0d00 + 1500

    location_style = xlwt.easyxf('font: bold on, name 宋体, height 300, color red; align: vert centre, horiz centre')

    for row in range(1, len(results) + 1):
        for col in range(0, len(fields)):
            if col == 3:
                sheet.write(row, col, u'%s' % results[row - 1][col], location_style)
            else:
                sheet.write(row, col, u'%s' % results[row - 1][col])
    time_str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
    out_path = export_dir+"/"+file_name+"_"+time_str+".xls"
    workbook.save(out_path)
    logger.info("导出数据 - 导出成功 - %s", out_path)
    open_dir = "\\".join(export_dir.split("/"))
    os.startfile(open_dir)


logger = logging.getLogger('Status')
logger.setLevel(logging.DEBUG)
fn = os.path.split(os.path.realpath(__file__))[0] + '/log/' + str(
    time.strftime('%Y-%m-%d', time.localtime(time.time()))) + '.log'
fh = logging.FileHandler(fn, encoding='utf-8')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

config = configparser.ConfigParser()
config.read('config.conf')

sql_util = pymysql
# sql_util = psycopg2

dbms = config.get('Self', 'dbms')

host = config.get(dbms, 'host')
port = int(config.get(dbms, 'port'))
user = config.get(dbms, 'user')
pwd = config.get(dbms, 'pwd')
database = config.get(dbms, 'database')
source_database = config.get(dbms, 'source_database')

rpc_host = config.get('Odoo', 'rpc_host')
rpc_port = config.get('Odoo', 'rpc_port')
rpc_db = config.get('Odoo', 'rpc_db')


if __name__ == "__main__":
    import sys
    logger.info("启动程序")
    app = QtWidgets.QApplication(sys.argv)
    main = LoginUI()
    main.show()
    sys.exit(app.exec_())

