# -*- coding: utf-8 -*-
# @Time    : 2018/8/24 18:12
# @Author  : FrankZ
# @Email   : FrankZ981210@gmail.com
# @File    : sava_list
# @Software: PyCharm

dict = {'3345':3}


def get_location_already_local(jobnum):
    return dict.get(jobnum, 0)


def save_dict(dict):
    f = open("data/dict.txt", 'w', encoding='utf-8')
    d_ls = dict.keys()
    for key in d_ls:
        value = dict.get(key)
        f.write(key+" "+str(value)+"\n")
    f.close()


def read_dict():
    f = open("data/dict.txt", 'r', encoding='utf-8')
    dict = {}
    while True:
        line = f.readline()
        if not line:
            break
        key_value = line.split(" ")
        dict.setdefault(key_value[0], int(key_value[1]))
    f.close()
    return dict


dict_1 = read_dict()
print(dict_1)

# locationid=get_location_already_local('3345345')
# if locationid > 0:
#     print("订单重复扫描！库位 【 "+str(locationid)+" 】")
# else:
#     print("进入分配")
#     dict.setdefault('3345345', 4)
#     print(str(dict))
#
# save_dict(dict)


