from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ihome.constants import QINIU_URL_DOMAIN, HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS
from sqlalchemy import not_
from datetime import datetime


class BaseModel(object):
    # 模型基类，为每个模型补充创建时间和更新事件
    create_time = db.Column(db.DateTime, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# 用户表
class User(BaseModel, db.Model):
    __tablename__ = "ih_user"

    id = db.Column(db.Integer, primary_key=True)    # 用户编号
    name = db.Column(db.String(32), unique=True, nullable=False)    # 用户昵称
    password_hash = db.Column(db.String(128), nullable=False)   
    mobile = db.Column(db.String(11), unique=True, nullable=False)
    avatar_url = db.Column(db.String(128))      # 头像的url
    real_name = db.Column(db.String(32))        # 真实姓名
    id_card = db.Column(db.String(20))      # 身份证号
    houses = db.relationship("House", backref="user")       # 用户发布的房屋
    orders = db.relationship("Order", backref="user")       # 用户下的订单


    @property
    def password(self):
        """@property装饰器的函数将变成类的一个属性，属性名为函数名，属性值为函数返回值"""
        """@property装饰的函数会在读取属性值执行"""
        raise AttributeError("该属性只允许设置，不允许读取")

    @password.setter
    def password(self, value):
        """@xx.setter装饰器装饰的函数在设置/修改xx属性值的时候执行; 需要传递value值"""
        self.password_hash = generate_password_hash(value)
    
    @password.deleter
    def password(self):
        """@xx.deleter装饰器装饰的函数在xx属性删除时调用"""
        pass

    # # 对密码进行加密
    # def generate_password_hash(self, origin_password):
    #     self.password_hash = generate_password_hash(origin_password)

    # 密码校验
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)




# 城区表
class Area(BaseModel, db.Model):
    __tablename__ = "ih_area"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    houses = db.relationship("House", backref="area")       # 区域的房屋

    def to_dict(self):
        # 将对象转成字典
        d = {
            "aid": self.id,
            "aname": self.name
        }
        return d


# 建立房屋--设施表
house_facility = db.Table(
    "ih_house_facility",
    db.Column("house_id", db.Integer, db.ForeignKey("ih_house.id"), primary_key=True),       # 房屋编号
    db.Column("facility_id", db.Integer, db.ForeignKey("ih_facility.id"), primary_key=True),    # 设施编号
)


# 房屋表
class House(BaseModel, db.Model):
    __tablename__ = "ih_house"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user.id"), nullable=False)        # 房屋的所属
    title = db.Column(db.String(64), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey("ih_area.id"), nullable=False)         # 所属城区
    address = db.Column(db.String(128), nullable=False)        # 房屋地址
    price = db.Column(db.Integer, default=0)        # 单价，单位：分
    room_count = db.Column(db.Integer, default=1)       # 房间数目
    acreage = db.Column(db.Integer, default=0)      # 房屋面积
    unit = db.Column(db.String(32), default="")     # 房屋的规格
    capacity = db.Column(db.Integer, default=1)         # 房屋容纳人数
    beds = db.Column(db.String(64), default="")         # 房屋床铺配置
    deposit = db.Column(db.Integer, default=0)          # 房屋押金
    min_days = db.Column(db.Integer, default=1)         # 至少入住天数
    max_days = db.Column(db.Integer, default=0)         # 最多入住天数，0标识不限制
    order_count = db.Column(db.Integer, default=0)          # 订单数
    index_image_url = db.Column(db.String(256), default="")     # 主页图片
    images = db.relationship("HouseImage", cascade='all')          # 房屋的图片
    facilities = db.relationship("Facility", secondary=house_facility)      # 房屋的设置，secondary指定多对多
    orders = db.relationship("Order", backref="house")      # 房屋的订单

    def to_basic_dict(self):
        """将房屋的基本信息转成字典的函数"""
        house_dict = {
            "house_id": self.id,
            "title": self.title,
            "price": self.price,
            "area_name": self.area.name,
            "img_url": QINIU_URL_DOMAIN + self.index_image_url if self.index_image_url else "",
            "room_count": self.room_count,
            "order_count": self.order_count,
            "address": self.address,
            "user_avatar": QINIU_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "ctime": self.create_time.strftime("%Y-%m-%d")
        }
        return house_dict

    def to_full_dict(self):
        """将详细信息转换为字典数据"""
        house_dict = {
            "hid": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name,
            "user_avatar": QINIU_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "room_count": self.room_count,
            "acreage": self.acreage,
            "unit": self.unit,
            "capacity": self.capacity,
            "beds": self.beds,
            "deposit": self.deposit,
            "min_days": self.min_days,
            "max_days": self.max_days,
            "area_id": self.area_id,
        }

        # 房屋图片
        img_urls = []
        for image in self.images:
            img_urls.append(QINIU_URL_DOMAIN + image.url)
        house_dict["img_urls"] = img_urls

        # 房屋设施
        facilities = []
        for facility in self.facilities:
            facilities.append(facility.id)
        house_dict["facilities"] = facilities

        # 评论信息
        # comments = []
        # orders = Order.query.filter(Order.house_id == self.id, Order.status == "COMPLETE", Order.comment != None).order_by(Order.update_time.desc()).limit(HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS)
        # for order in orders:
        #     comment = {
        #         "comment": order.comment,  # 评论的内容
        #         "user_name": order.user.name if order.user.name != order.user.mobile else "匿名用户",  # 发表评论的用户
        #         "ctime": order.update_time.strftime("%Y-%m-%d %H:%M:%S")  # 评价的时间
        #     }
        #     comments.append(comment)
        # house_dict["comments"] = comments
        return house_dict


# 设施表
class Facility(BaseModel, db.Model):
    __tablename__ = "ih_facility"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)     # 设施名称


# 房屋图片
class HouseImage(BaseModel, db.Model):
    __tablename__ = "ih_house_image"

    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey("ih_house.id"), nullable=True, )      # 图片对应房屋id
    url = db.Column(db.String(256), nullable=False)         # 图片对应url


# 订单
class Order(BaseModel, db.Model):
    __tablename__ = "ih_order"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user.id"), nullable=False)        # 订单用户
    house_id = db.Column(db.Integer, db.ForeignKey("ih_house.id"), nullable=True)      # 订单房屋
    begin_date = db.Column(db.DateTime, nullable=False)     # 起始入住时间
    end_date = db.Column(db.DateTime, nullable=False)       # 结束入住时间
    days = db.Column(db.Integer, nullable=False)        # 入住天数
    house_price = db.Column(db.Integer, nullable=False)        # 房屋单价
    amount = db.Column(db.Integer, nullable=False)      # 订单总价
    status = db.Column(
        db.Enum(
            "WAIT_ACCEPT",      # 等待接单
            "WAIT_PAYMENT",     # 待支付
            "PAID",         # 已支付
            "WAIT_COMMENT",     # 待评价
            "COMPLETE",        # 已完成
            "CANCELED" ,        # 已取消
            "REJECTED",        # 已拒单
        ),
        default="WAIT_ACCEPT", index=True)
    comment = db.Column(db.Text)        # 订单评论或拒单原因
    trade_no = db.Column(db.String(80))     # 支付宝交易流水号

    def to_dict(self): 
        order_dict = {
            "order_id": self.id,
            "user_id": self.user_id,
            "house_id": self.house_id,
            "start_date": datetime.strftime(self.begin_date, "%Y-%m-%d"),
            "end_date": datetime.strftime(self.end_date, "%Y-%m-%d"),
            "days": self.days,
            "house_price": self.house_price,
            "amount": self.amount,
            "status": self.status,
            "comment": self.comment
        }

        if self.house:
            order_dict['img_url'] = QINIU_URL_DOMAIN + self.house.index_image_url
        else:
            order_dict['img_url'] = " "

        return order_dict

