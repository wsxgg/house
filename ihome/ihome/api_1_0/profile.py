'''
@Author: your name
@Date: 2020-05-25 10:10:35
@LastEditTime: 2020-05-25 12:15:00
@LastEditors: Please set LastEditors
@Description: 关于用户资料的视图
@FilePath: \ihome\ihome\api_1_0\profile.py
'''
from flask import g, current_app, jsonify, request, session
from . import api
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome import db
from ihome.models import User
from ihome.constants import QINIU_URL_DOMAIN
import re


# 我的页面，显示用户名和手机号
@api.route("/myinfo")
@login_required
def show_my_info():
    # 1. 获取参数
    user_id = g.user_id
    # 2. 校验参数（过）
    # 3. 业务逻辑
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库获取失败')
    # 4. 返回应答
    name = user.name
    mobile = user.mobile
    if user.avatar_url:
        avatar = QINIU_URL_DOMAIN + user.avatar_url
    else:
        avatar = ""
    return jsonify(errno=RET.OK, errmsg='访问成功', data={"name": name, "mobile": mobile, "avatar": avatar})

# 修改头像页面，显示原头像和用户名
@api.route("/users")
@login_required
def show():
    # 1. 获取参数
    user_id = g.user_id

    # 2. 校验参数（无）
    # 3. 业务逻辑
    # 3.1   获取用户头像和用户名
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')
    avatar_url = user.avatar_url
    avatar_url = QINIU_URL_DOMAIN + avatar_url
    name = user.name
    # 4. 返回应答
    return jsonify(errno=RET.OK, errmsg='获取成功', data={"avatar_url":avatar_url, "name":name})


# 用户设置头像的的视图
@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """
    参数： 图片(多媒体表单格式)  用户id(装饰器的g对象中)
    """
    # 1. 获取参数
    user_id = g.user_id
    image_file = request.files.get("avatar")
    
    # 2. 校验参数
    if image_file is None:
        return jsonify(error=RET.PARAMERR, errmsg='未上传图片')

    # 3. 业务逻辑
    # 3.1   获取图片数据
    image_data = image_file.read()
    # 3.2   调用七牛上传图片
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')
    # 3.3   获取该数据库对象，修改头像
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    # 4. 返回应答
    # 拼接头像url
    avatar_url = QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})

# 保存用户名
@api.route("/users/name", methods=["POST"])
@login_required
def set_user_name():
    '''参数：用户名; 格式：json'''
    # 1. 获取参数
    user_id = g.user_id
    req_dict = request.get_json()
    print(req_dict)
    user_name = req_dict.get("user_name")

    # 2. 校验参数
    # 2 校验是否为空输入
    if user_name == "":
        return jsonify(errno=RET.PARAMERR, errmsg='请输入用户名')
    # 2.2 校验是否重复
    try:
        old_user = User.query.filter_by(name=user_name).first()
        print(old_user)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库错误")
    if old_user is not None:
        return jsonify(errno=RET.PARAMERR, errmsg='用户名已存在')

    # 3. 逻辑处理
    try:
        User.query.filter_by(id=user_id).update({"name": user_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据库错误')
    # 4. 返回应答
    session["name"] = user_name
    return jsonify(errno=RET.OK, errmsg="用户名修改成功", data={"user_name": user_name})


# 实名认证
@api.route("/users/auth", methods=["POST", "GET"])
@login_required
def set_auth():
    # 如果是提交表单
    if request.method == "POST":
        '''添加实名认证
        参数：姓名，身份证
        格式：json'''
        # 1. 获取参数
        user_id = g.user_id
        req_dict = request.get_json()
        real_name = req_dict.get("real_name")
        id_card = req_dict.get("id_card")
        # 2. 校验参数
        if not all([real_name, id_card]):
            return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
        if not re.match(r'\d{13}[0-9X]', id_card):
            return jsonify(errno=RET.DATAERR, errmsg='身份证输入错误')
        # 3. 业务逻辑
        try:
            user = User.query.filter_by(id=user_id).first()
            user.real_name = real_name
            user.id_card = id_card
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg='数据库获取失败')
        # 4. 返回应答
        return jsonify(errno=RET.OK, errmsg="修改成功", data={"real_name":real_name, "id_card":id_card})
    
    # 如果是获取页面
    else:
        # 1. 获取参数
        user_id = g.user_id
        # 2. 校验参数（过）
        # 3. 业务逻辑
        try:
            user = User.query.filter_by(id=user_id).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='连接数据库失败')          
        # 4. 返回应答 
        real_name = user.real_name
        id_card = user.id_card
        return jsonify(errno=RET.OK, errmsg='查看成功', data={"real_name":real_name, "id_card": id_card})

