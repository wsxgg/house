
from . import api
from ihome.models import Area, House, Facility, HouseImage, Order
from flask import current_app, g, jsonify, json, request, session
from ihome.utils.commons import RET
from ihome.constants import AREA_INFO_REDIS_CACHE_EXPIRES, QINIU_URL_DOMAIN, HOME_PAGE_MAX_HOUSES, HOME_PAGE_MAX_HOUSES,\
    HOUSE_DETAIL_REDIS_EXPIRE_SECOND, HOME_PAGE_DATA_REDIS_EXPIRES, HOUSE_LIST_PAGE_CAPACITY, HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES
from ihome import redis_store, db
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage
from ihome.models import User
import json
from datetime import datetime


# 获取城区表信息
@api.route("/areas")
def get_area_info():
    # 尝试从redis读取缓存
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # 如果有缓存数据，直接返回
            return resp_json, 200, {"Content-Type": "application/json"}
    # 如果没有缓存，从数据库读取
    # 查询数据库，读取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.errror(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')
    
    # 将对象转成字典
    area_dict_li = []
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # 将数据转换成json字符串
    resp_dict = dict(errno=RET.OK, errmsg='OK', data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis数据库中作为缓存（字符串格式）
    try:
        redis_store.setex("area_info", AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    # 返回应答
    return resp_json, 200, {"Content-Type": "application/json"}
    
# 添加房屋信息
@api.route("/houses/info", methods=['POST'])
@login_required
def save_house_info():
    """添加房屋基本信息
    前端传递的json信息：
    {
        "title": "",
        "price": "",
        "area_id": "",
        "address": "",
        "room_count": "",       出租房间数
        "acreage: "",       房屋面积
        "unit": "",         户型
        "capacity": "",     适宜住宿人数
        "beds": "",         卧床配置
        "deposit":"",       押金
        "min_day": "",  
        "max_day": "",
        "facility": ["7", "8"]      配套设施
    }
    """

    # 1. 获取参数
    house_data = request.get_json()

    user_id = g.user_id
    house_id = house_data.get("house_id")
    title = house_data.get("title")
    price = house_data.get("price")
    area_id = house_data.get("area_id")     # 城区号
    address = house_data.get("address")     
    room_count = house_data.get("room_count")   # 出租房间数
    acreage = house_data.get("acreage")     # 房屋面积
    unit = house_data.get("unit")       # 户型
    capacity = house_data.get("capacity")       # 适宜居住人数   
    beds = house_data.get("beds")       # 卧床配置
    deposit = house_data.get("deposit")     # 押金
    min_days = house_data.get("min_days")
    max_days = house_data.get("max_days")

    # 2. 校验参数
    # 2.1 校验参数完整性
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 2.2 校验价格格式是否正确
    try:
        price = int(float(price) * 100)         # 因为数据库存储的是Integer
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 2.3 校验城区是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        login_required.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据异常')
    if area is None:
        return jsonify(errno=RET.NODATA, errmsg='城区信息有误')

    # 3. 业务逻辑
    # 3.1 处理房屋信息
    # 3.1.1 如果是新建房屋
    if not house_id:
        house = House(
            user_id=user_id,
            area_id=area_id,
            title=title,
            price=price,
            address=address,
            room_count=room_count,
            acreage=acreage,
            unit=unit,
            capacity=capacity,
            beds=beds,
            deposit=deposit,
            min_days=min_days,
            max_days=max_days
        )
    # 3.1.2 如果是修改房屋信息
    else:
        try:
            house = House.query.get(house_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库异常1')

        house.area_id = area_id
        house.title = title
        house.price = price
        house.address = address
        house.room_count = room_count
        house.acreage = acreage
        house.unit = unit
        house.capacity = capacity
        house.beds = beds
        house.deposit = deposit
        house.min_days = min_days
        house.max_days = max_days

        # 获取房屋图片信息
        images = HouseImage.query.filter_by(house_id = house_id).all() 
        image_list = []
        for image in images:
            image_url = QINIU_URL_DOMAIN + image.url
            image_list.append(image_url)
        

    # 3.2 处理房屋设施信息
    # 3.2.1 获取房屋设施列表
    facility_ids = house_data.get("facility")
    # 3.2.2 校验房屋设施（如果有数据，则保存数据）
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e) 
            return jsonify(errno=RET.DBERR, errmsg='数据库异常2')
        # 判断设施编号是否存在
        if facilities:
            # 如果是合法设施，保存到数据库
            house.facilities = facilities
    
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    # 4. 返回应答
    # 4.1 如果是新建按房屋信息
    if not house_id:
        return jsonify(errno=RET.OK, errmsg='创建成功', data={"house_id": house.id})
    # 4.2 如果是修改房屋信息
    else:
        return jsonify(errno=RET.OK, errmsg='创建成功', data={"house_id": house.id, "images": image_list})

# 保存房屋图片
@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """
    参数：图片，房屋id
    """
    # 1. 获取参数
    image_file = request.files.get("house_image")
    house_id = request.form.get("house_id")

    # 2. 校验参数
    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    
    # 3. 业务逻辑
    # 3.1 判断对应id的房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    if house is None:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')
    # 3.2 读取图片数据
    image_data = image_file.read()
    # 3.3 保存图片到七牛
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='保存图片失败')
    # 3.4 将图片信息保存到数据库
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)
    # 3.5 更新房屋表种的主图片（默认第一张）
    if not house.index_image_url: 
        house.index_image_url = file_name
        db.session.add(house)
    # 3.6 提交数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据库错误')

    # 4. 返回应答
    image_url = QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg='保存成功', data={"image_url": image_url})


# 我的房源页面
@api.route("/user/houses")
@login_required
def get_user_houses():
    """获取房东发布的房源"""
    # 1. 获取参数
    user_id = g.user_id

    # 2. 校验参数(过)

    # 3. 业务逻辑
    # 3.1   获取用户房源对象
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')
    
    # 3.2   将查询到的房源信息转成字典存放到列表
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
        houses_list.reverse()

    # 4. 返回应答
    return jsonify(errno=RET.OK, errmsg='OK', data={"houses": houses_list})


# 主页房屋资源
@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋"""
    # 首先尝试从缓存中获取数据
    try:
        ret = redis_store.get("home_page_data").encode("utf-8")
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    # 如果存在，直接返回
    if ret:
        return '{"errno":"0", "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type":"application/json"}
    # 如果不存在，添加查询数据库，并添加缓存
    else:
        try:
            houses = House.query.order_by(House.order_count.desc()).limit(HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')
        # 如果查询数据为空
        if not houses:
            return jsonify(errno=RET.NODATA, errmsg='查询无数据')
        
        houses_list = []
        for house in houses:
            # 遍历房屋信息
            # 如果房屋未设置主图片，则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())
        
        # 将房屋数据转成字符串，存入缓存
        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data", HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)
        
        # 返回应答
        return '{"errno":"0", "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


# 房屋详情页信息
@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情页"""
    # 前端在访问房屋详情页的时候，如果用户不是该房屋的房东，则显示预定按钮
    # 需要后端返回登陆用户的user_id,如果没有登陆返回“-1”，方便前端操作
    # 1. 获取参数
    user_id = session.get('user_id', '-1') 

    # 2. 校验参数(过)

    # 3. 业务逻辑
    # 3.1 尝试从redis获取缓存
    try:
        ret = redis_store.get("house_info_%s" % house_id).encode('utf-8')
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    # 如果获取到缓存，直接返回
    if ret:
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id": %s, "house": %s}}' % (user_id, ret), 200, {"Content-Type": "application/json"}
    # 如果没有缓存，查找数据库，添加缓存
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.errno(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")
    
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='数据不存在')
    
    # 将数据转为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据出错')
    
    # 存到redis缓存
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    # 4. 返回应答
    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), 200, {"Content-Type": "application/json"}
    return resp 

# GET /api/v1.0/houses?sd=20171201&ed=20171211&aid=1&sk=new&page=1
# 房屋列表信息
@api.route("/houses")
def get_house_list():
    # 1. 获取参数
    start_date = request.args.get("sd", "")
    end_date = request.args.get("ed", "")
    area_id = request.args.get("aid", "")
    sort_key = request.args.get("sk", "new")
    page = request.args.get("page", "")
    # 2. 校验参数
    # 2.1 校验时间
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期参数有误')
    # 2.2 校验区域ID
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='区域参数有误')
    # 2.3 校验页码
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 尝试获取redis缓存
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        ret_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if ret_json:
            return ret_json, 200, {"Content-Type": "application/json"} 

    # 3. 业务逻辑
    # 3.1 创建一个用于查询数据库的过滤条件容器
    filter_params = []
    # 3.2 填充过滤参数
    # 3.2.1 时间条件
    conflict_order = None       # 防止没有冲突订单带来的查询错误
    try:
        if start_date and end_date:
            # 如果有起始和结束时间的冲突订单
            conflict_order = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            # 如果只规定开始时间时的冲突订单
            conflict_order = Order.query.filter(Order.end_date >= start_data).all()
        elif end_date:
            #  如果只规定结束时间时的冲突订单
            conflict_order = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询失败")

    if conflict_order:          # 如果存在冲突订单
        # 获取冲突订单的房屋id
        conflict_house_ids = [ order.house_id for order in conflict_order ]

        # 如果冲突的房屋id不为空，则添加过滤条件
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))    
    # 3.2.2 区域条件
    if area_id:
        filter_params.append(House.area_id==area_id)

    # 3.3 补充排序条件（此时还没有开始查询数据库）
    if  sort_key == "booking":
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_params).order_by(House.price)
    elif sort_key == "price-des":
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 3.4 处理分页
    # paginate()的参数： page：当前页码， per_page:每页数目， error_out:自动的错误输出
    try:
        page_obj = house_query.paginate(page=page, per_page=HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')
    # page_obj.items : 表示当前页的数据
    # page_obj.pages : 表示总页数
    total_page = page_obj.pages
    # 获取对应页面数据，转成字典存放到一个列表中
    houses_li = []
    for house in page_obj.items:
        houses_li.append(house.to_basic_dict())

    # 4. 返回应答
    # 4.1 添加redis缓存，缓存格式为hash， house_起始_终止_区域id_排序  { 页码1  ： 数据1 ， 页码2 ： 数据2 ......}
    # 先把数据转成字典，在转成字符串
    ret_dict = dict(errno=RET.OK, errmsg='OK', data={"total_page": total_page, "houses": houses_li, "current_page": page})
    ret_json = json.dumps(ret_dict)
    # 设置redis缓存
    if page <= total_page:
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
        try:
            # redis_store.hset(redis_key, page, ret_json)
            # redis_store.expire(redis_key, HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)
            # 创建管道对象，可以一次执行多个语句，可以解决多语句中的不完全成功的问题
            pipeline = redis_store.pipeline()
            # 开启多语句记录
            pipeline.multi()
            pipeline.hset(redis_key, page, ret_json)
            pipeline.expire(redis_key, HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)
            # 执行语句
            pipeline.execute()

        except Exception as e:
            current_app.logger.error(e)
    # 4.2 返回应答
    return ret_json, 200, {"Content-Type": "application/json"}


# 房东修改房屋配置
@api.route("/houses/<int:house_id>/change", methods=["GET"])
@login_required
def change_house_info(house_id):
    # 1.获取参数
    user_id = g.user_id

    # 2.校验参数

    # 3.业务逻辑
    # 3.1 获取房屋对象
    try:
        house = House.query.filter(House.id == house_id, House.user_id == user_id).first()
    except  Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg='数据库异常')
    if not house:
        return jsonify(error=RET.DATAERR, errmsg='无效的数据')
    
    # 4.返回应答
    house_data = house.to_full_dict()
    house_data['price'] = int(float(house_data['price'])/100)
    house_data['deposit'] = int(float(house_data['deposit'])/100)
    return jsonify(errno=RET.OK, errmsg='OK', data={"house": house_data})


# 房东删除房源
@api.route("/houses/<int:house_id>/delete", methods=["PUT"])
@login_required
def delete_house(house_id):
    print("delete begin")
    # 1. 获取参数
    user_id = g.user_id

    # 2. 校验参数

    # 3. 业务逻辑
    # 3.1 获取该房屋对象
    try:
        house = House.query.filter_by(id=house_id, user_id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    if not house:
        return jsonify(errno=RET.DATAEXIST, errmsg='房源不存在')
    # 3.2 删除房屋数据
    try:
        db.session.delete(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        print(e)
        return jsonify(errno=RET.DBERR, errmsg="删除失败")
    return jsonify(errno=RET.OK, errmsg='删除成功')

