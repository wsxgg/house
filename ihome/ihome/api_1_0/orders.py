from ihome.api_1_0 import api
from ihome.utils.commons import login_required
from flask import jsonify, current_app, request, g
from ihome.utils.response_code import RET
from datetime import datetime
from ihome.models import House, Order
from ihome import db


# 用户添加订单（预约订单）
@api.route("/orders", methods=["POST"])
@login_required
def save_order():
    # 1.获取参数
    user_id = g.user_id
    
    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    house_id = order_data.get("house_id")
    start_date_str = order_data.get("start_date")
    end_date_str = order_data.get("end_date")    

    # 2.校验参数
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 3.业务逻辑
    # 3.1 判断日期格式，计算预定天数
    try:
        # 将时间str转成datetime类型
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        assert start_date <= end_date
        # 计算预定天数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='时间参数错误')
    # 3.2 判断房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取房屋信息失败')
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')
    # 3.3 判断预定的人是否是房东自己
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg='不能预定自己的房屋')
    # 3.4 判断预定时间内，房屋是否出租
    try:
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date, Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库检查错误')
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg='房屋已被预订')
    # 3.5 保存订单数据
    amount = days * house.price
    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存订单失败')
    
    # 4.返回应答
    return jsonify(errno=RET.OK, errmsg='OK', data={"order_id": order.id})


# 我的订单列表页面
# GET /api/v1.0/user/orders?role=customer    role=landlord
@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_orders():
    """查询用户订单列表"""
    # 1. 获取参数
    user_id = g.user_id
    role = request.args.get("role", "")

    # 2. 校验参数（过）

    # 3. 业务逻辑
    # 3.1 查询订单数据
    try:
        # 如果是房东访问
        if role == "landlord":
            # 先查询属于自己的房子
            houses = House.query.filter(House.user_id == user_id).all()
            houses_ids = [house.id for house in houses]
            # 再查询自己房子的订单
            orders = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc()).all()
        # 如果是普通用户
        else:
            # 查询自己的订单
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')
    
    # 4. 返回应答
    # 将订单对象转成自字典，添加到列表
    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())
    return jsonify(errno=RET.OK, errmsg='OK', data={"orders": orders_dict_list})


# 房东接单和拒单
@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def acceept_reject_order(order_id) :
    # 1. 获取参数 & 2. 校验参数
    user_id = g.user_id
    
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    
    action = req_data.get("action")     # 用于判断是接单还是拒单
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.DATAERR, errmsg='参数错误')

    # 3. 业务逻辑
    # 3.1 根据订单编号查询订单
    try:
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    # 3.2 确保房东只能更改自己发布的房源
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    # 3.3 接单和拒单实现
    if action == "accept":
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        # 如果是拒单，获取拒单缘由
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请填写拒单理由")
        order.status = "REJECTED"
        order.comment = reason
    
    # 3.4 保存数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    
    # 4. 返回应答
    return jsonify(errno=RET.OK, errmsg='OK')


# 用户评论
@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """保存订单评论"""
    # 1. 获取参数
    user_id = g.user_id
    
    req_data = request.get_json()
    comment = req_data.get("comment")

    # 2. 校验参数
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    
    # 3. 业务逻辑
    # 确保用户只能评论自己的订单且订单状态待评论
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == "WAIT_COMMENT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    if not order:
        return jsonify(error=RET.REQERR, errmsg='操作无效')
    
   
    try:
         # 设置订单状态
        order.status = "COMPLETE"
        # 保存评论
        order.comment = comment
        # 将房屋的完成订单+1
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')
    
    # 4. 返回应答
    # 4.1 修改过house，删除之前对应的redis数据库，待重新获取时重新设置
    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)
    # 4.2 返回应答
    return jsonify(errno=RET.OK, errmsg='')

