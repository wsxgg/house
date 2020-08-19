'''
@Author: your name
@Date: 2020-05-21 09:27:17
@LastEditTime: 2020-05-25 10:11:46
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: \ihome\ihome\api_1_0\__init__.py
'''

from flask import Blueprint

"""定义蓝图"""
# 1.创建蓝图对象
api = Blueprint("api_1_0", __name__)

# 导入蓝图的视图
from . import verify_code, passport, profile, house, orders, pay
