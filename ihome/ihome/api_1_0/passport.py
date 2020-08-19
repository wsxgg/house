'''
@Author: your name
@Date: 2020-05-23 11:23:15
@LastEditTime: 2020-05-24 16:50:33
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: \ihome\ihome\api_1_0\passport.py
'''
from . import api
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
import re
from ihome import redis_store, db
from ihome.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from ihome.constants import LOGIN_ERROR_TIMES, LOGIN_ERROR_FORBIN_TIME


# 注册
# 127.0.0.1:5000/api/v1.0/users
@api.route("/users", methods=["POST"])
def register():
    """"注册
    参数：手机号，短信验证码，密码，二次密码
    参数格式：json"""
    # 1. 获取请求参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 2. 校验参数
    # 2.1 参数完整性
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    
    # 2.2 校验手机号格式, re.match匹配成功返回匹配字符串，失败返回None；
    if not re.match(r"1[34578]\d{9}", mobile):
        # 手机号匹配失败
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")
    
    # 2.3 密码校验
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")
    
    # 2.4 校验短信验证码
    # 2.4.1 获取redis中的短信验证码的值（能否获取，是否过期）
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile).decode('utf-8')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="redis获取短信验证码失败")
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码已过期")
    # 2.4.2 校验短信验证码（如果成功，删除短信验证码）
    if sms_code != real_sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg="短信验证码错误")
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 3. 业务处理
    # 3.1 判断用户手机号是否以及注册
    # 为了减少数据库的读取，合并在添加账户
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DATAERR, errmsg="数据库异常")
    # else:
    #     if user is not None:
    #         return jsonify(errno=RET.DATAERR, errmsg="手机号已存在")

    # 3.2 添加账户进数据库
    user = User(name=mobile, mobile=mobile)
    user.password = password       # 设置属性值，对应的加密在类中执行
    try:
        db.session.add(user)
        db.session.commit()
    except InterityError as e:
        # Interity手机号出现重复值是的异常，表示手机号已注册
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(serrno=RET.DATAERR, errmsg="数据已存在")
    except Exception as e:
        # 其他数据库错误
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库查询异常")

    # 3.3 保存登录状态到session中
    session['name'] = mobile
    session['mobile'] = mobile
    session['user_id'] = user.id

    # 4. 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


# 登陆
# 127.0.0.1:5000/api/v1.0/sessions
@api.route("/sessions", methods=["POST"])
def login():
    """"登陆参数：手机号，密码"""
    # 1. 获取参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    # 2. 校验参数
    # 2.1   参数完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='请输入用户名和密码')
    # 2.2   手机号格式是否正确,re.match成功返回字符串，失败返回None
    if not re.match(r'1[34578]\d{9}', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号格式错误')
    # 2.3   判断用户操作是否超过限制
    # redis记录："access_nums_%s" % user_ip: nums
    user_ip = request.remote_addr   # 获取用户的IP地址 
    try:
        access_nums = redis_store.get("access_nums_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= LOGIN_ERROR_TIMES:
            return jsonify(errno=RET.REQERR, errmsg='登陆次数过多，请稍后重试')
    
    # 3. 业务处理
    # 3.1   获取用户对象
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="用户名或密码错误")
    # 3.2   如果获取的为空 / 密码校验错误
    if user is None or not user.check_password(password):
        # 记录错误次数
        try:
            redis_store.incr("access_nums_%s" % user_ip)
            redis_store.expire("access_nums_%s" % LOGIN_ERROR_FORBIN_TIME)      # 设置数据有效期
        except Exception as e:
            current_app.logger.error(e)
        
        return jsonify(errno=RET.PARAMERR, errmsg='用户名或密码错误')

    # 4. 返回应答
    # 4.1   保存登录状态
    session['name'] = user.name
    session['mobile'] = user.mobile
    session['user_id'] = user.id
    # 4.2 消除错误登陆次数
    redis_store.delete("access_nums_%s" % user_ip)
    # 4.3   返回应答
    return jsonify(errno=RET.OK, errmsg='登陆成功')

# 检查登录状态
# 127.0.0.1:5000/api/v1.o/sessions
@api.route("/sessions", methods=["GET"])
def check_login():
    # 尝试从session中获取登陆的用户名
    name = session.get("name")
    # 如果name存在，则为已经登陆返货用户名，否则未登录
    if name is not None:
        return jsonify(errno=RET.OK, errmsg='true', data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg='false')

# 登出
# 127.0.0.1:5000/api/v1.o/sessions
@api.route("/sessions", methods=["DELETE"])
def logout():
    # 清除session数据
    csrf_token = session.get("csrf_token")
    session.clear()
    session["csrf_token"] = csrf_token
    return jsonify(errno=RET.OK, errmsg='OK')

