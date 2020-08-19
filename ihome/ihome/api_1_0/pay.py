from . import api
from ihome.utils.commons import login_required
from ihome.models import Order
from flask import g, current_app, jsonify, request, json
from ihome.utils.response_code import RET
from alipay import AliPay
import os
from ihome import db

@api.route("/orders/<int:order_id>/payment", methods=["POST"])
@login_required
def order_pay(order_id):
    """发起支付宝支付"""
    # 1. 获取参数
    user_id = g.user_id

    # 2. 校验参数（过）

    # 3. 业务逻辑
    # 3.1 判断订单状态
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    if not order:
        return jsonify(errno=RET.NODATA, errmsg="订单信息有误")


    # 3.2 创建支付宝sdk工具
    alipay = AliPay(
        appid="2016102400748506",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=open(os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read(),  # 自己的私钥，用于加密发送的信息
        alipay_public_key_string=open(os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read(),  # 支付宝的公钥，验证支付宝回传消息使用
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    # 3.3 发送手机网站支付请求
    # 手机网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
    order_string = alipay.api_alipay_trade_wap_pay(
        out_trade_no=order.id,
        total_amount=str(order.amount/100.0),
        subject="爱家租房 %s" % order.id,    # 订单标题
        return_url="http://127.0.0.1:5000/payComplete.html",        # 返回的连接地址
        notify_url=None         # 可选, 不填则使用默认notify url
    )

    # 3.4构建让用户跳转的支付宝支付的链接地址
    pay_url = "https://openapi.alipaydev.com/gateway.do?" + order_string

    # 4. 返回应答
    return jsonify(errno=RET.OK, errmsg='OK', data={"pay_url": pay_url})



# 保存订单支付结果
@api.route("/order/payment", methods=["PUT"])
def save_order_payment_result():
    """保存订单支付结果
    支付宝返回链接：
    http://127.0.0.1:5000/payComplete.html?charset=utf-8&out_trade_no=9&method=alipay.trade.wap.pay.return&total_amount=1999.00
    &sign=nt6TIpEINO6o%2Fxm1tpNlLxqI91rea2%2BK%2FXSJ%2FpYUuugQRErve0ngiuMTz%2F%2FNtN%2B802Ddq0fludUikCSOg22P5%2Br1NuC2ULI31WAGb
    4I%2BXO9WGYghj9o1N78PJHF%2BawWviB%2FeCSsTSyeqn0L0lA8v8n6VKJx2ZNL%2F%2BezzIk7%2FOGQHfvwhcrfh%2FP%2FcyUnVwJMzBINeg7DfyIRoGY4X
    aauUO9uOwItn2quRJruACotoEdyynczgyaWFnEoMU8nB5eIq59cAHDC%2FWYHZ3ytNn%2BJFLQErFdkabOcaItg6%2FQEytDy6Q%2FeJCiTsUlKC8LJJne1xziS
    3XWHPeoxDvKLcrh1eIQ%3D%3D&trade_no=2020060422001445090500530583&auth_app_id=2016102400748506&version=1.0&app_id=2016102400748506
    &sign_type=RSA2&seller_id=2088102180833264&timestamp=2020-06-04+15%3A58%3A08
    """
    # 1. 获取参数
    data = request.form.to_dict()

    # 2. 校验参数

    # 3.业务逻辑
    # 3.1 对支付宝传递的数据进行分离，提出支付宝的签名参数sign，和剩下的数据
    signature = data.pop("sign")

    # 3.2 创建支付宝sdk工具
    alipay = AliPay(
        appid="2016102400748506",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=open(os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read(),  # 自己的私钥，用于加密发送的信息
        alipay_public_key_string=open(os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read(),  # 支付宝的公钥，验证支付宝回传消息使用
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    # 3.3 借助verify验证参数的合法性，将data数据进行签名操作，再和signature对比. 成功返回true，否则false
    result = alipay.verify(data, signature)
    if result:
        # 修改数据库的订单数据
        order_id = data.get("out_trade_no")
        trade_no = data.get("trade_no")

        try:
            Order.query.filter_by(id=order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
    
    # 4. 返回应答
    return jsonify(errno=RET.OK, errmsg='OK')

