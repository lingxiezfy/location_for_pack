# -*- coding: utf-8 -*-
# @Time    : 2018/8/24 10:20
# @Author  : FrankZ
# @Email   : FrankZ981210@gmail.com
# @File    : import_data
# @Software: PyCharm

import xlrd
from sql_helper import SqlService
import pymysql
import time
import configparser

wb = xlrd.open_workbook("")

st = wb.sheet_by_index(0)
print(st.cell(2,1).value[:2])
print(st.cell(2,3))
print(st.cell(2,4))

# 当系统前时间
def now_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


sql_util = pymysql

config = configparser.ConfigParser()
config.read('config.conf')

dbms = config.get('Self', 'dbms')

host = config.get(dbms, 'host')
port = int(config.get(dbms, 'port'))
user = config.get(dbms, 'user')
pwd = config.get(dbms, 'pwd')
database = config.get(dbms, 'database')

createtime = now_time()
sql = ""
list=[]
db = SqlService(sql_util, host, port, user, pwd, database)
for i in range(2,173):
    order = st.cell(i, 1).value

    ordernum = st.cell(i, 2).value
    customerno = "0"+order[:2]
    opticianno = order[:5]
    locationid = int(st.cell(i, 3).value)
    quantity = int(st.cell(i, 4).value)

    if ordernum not in list:
        list.append(ordernum)
        sql = "UPDATE locationforpack SET ordernum='"+ordernum+"',customerno='"+customerno+"',opticianno='"+opticianno+"',quantity="+str(quantity)+",createtime='"+createtime+"',operator='AutoImport' WHERE locationid="+str(locationid)

        db.ExecNonQuery(sql)
        print(sql)

db.CloseDB()