from flask import current_app, jsonify, make_response, request
from . import api
from ihome.utils.captcha.captcha import captcha 
from ihome import redis_store, db
from ihome.constants import IMAGE_CODE_REDIS_EXPIRES, SMS_CODE_REDIS_EXPIRES, SEND_SMS_CODE_INTERVAL
from ihome.utils.response_code import RET
from ihome.models import User
import random
from ihome.libs.yuntongxun.SendTemplateSMS import CCP
from ihome.tasks.task_sms import send_sms

# 获取图片验证码
# GET 127.0.0.1:5000/api/V1.0/image_code/<image_code_id>
@api.route("/image_code/<image_code_id>")
def get_image_code(image_code_id):
    """获取图片验证码， 返回验证码图片"""
    # 1. 获取参数  url中已经获取 

    # 2. 校验参数   参数存在，无其他校验

    # 3. 业务逻辑   
    # 3.1 生成验证码图片
    # 名字  真实文本  图片数据
    name, text, image_data = captcha.generate_captcha()
    # 3.2 将图片和编号存储到redis
    # redis_store.set("image_code_%s" % image_code_id, text)
    # redis_store.expire("image_code_%s" % image_code_id, IMAGE_CODE_REDIS_EXPIRES)
    try:        # 防止redis连接中断
        redis_store.setex("image_code_%s" % image_code_id, IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="save image_code _id failed")

    # 4. 返回图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp

# 获取手机验证码
# GET 127.0.0.1:5000/api/V1.0/sms_code/<mobile>?image_code=xxxxxx&image_code_id=xxxxxx
@api.route("/sms_code/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    # 1. 获取参数
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")

    # 2. 校验参数
    if not all([image_code, image_code_id]):
        # 参数不完整
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 3. 业务逻辑
    # 3.1 对比图片验证码
    try:
        real_image_code = redis_store.get(image_code_id).decode('utf-8')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis获取图片验证码失败")
    if real_image_code is None:
        # 如果图片验证码过期
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

    # 图片验证码仅可使用一次，删除图片验证码
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
    
    if real_image_code.upper() != image_code.upper():
        # 填写错误
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误") 

    # 判断该手机号是否在60s内操作过
    try:
        send_flag = redis_store.get("send_sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag == 1:
            # 操作频繁
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60s后重试")
    # 3.2 判断手机号是否已注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 手机号已经注册
            return jsonify(errno=RET.DATAEXIST, errmsg="用户已存在")
    # 3.3 如果未注册，生成短信验证码并保存，发送短信验证码
    sms_code = "%06d" % random.randint(0, 999999)
    try:
        redis_store.setex("sms_code_%s" % mobile, SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给这个号码的记录，防止用户在60s内再次重复发送
        redis_store.setex("send_sms_code_%s" % mobile, SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码异常")
    # ccp = CCP()
    # try:
    #     result = ccp.send_template_sms(mobile, [sms_code, int(SMS_CODE_REDIS_EXPIRES/60)], 1)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.THIRDERR, errmsg="第三方发送短信异常")
    # if result == 0:
    #     # 发送成功
    #     return jsonify(errno=RET.OK, errmsg="发送成功")
    # else:
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送失败")
    
    # 异步发送短信
    send_sms.delay(mobile, [sms_code, int(SMS_CODE_REDIS_EXPIRES/60)], 1)

    # 4. 返回值
    return jsonify(errno=RET.OK, errmsg="发送成功")
