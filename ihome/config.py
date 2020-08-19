import redis

# 配置类
class Config(object):

    SECRET_KEY = "IAKBAKGFALFKEHEEHFLK32503HL1L"
    # mysql数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root: @192.168.152.156:3306/ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # redis数据库
    REDIS_HOST = "192.168.152.156"
    REDIS_PORT = 6379
    # session_type,设置为redis存储(线上一般不同于redis缓存数据库)
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True       # 对cookie中的session_id加密隐藏
    PERMANENT_SESSION_LIFETIME = 86400      #session数据的有效期，单位s


# 开发模式的配置信息
class DevelopmentConfig(Config):
    DEBUG = True

# 生产环境的配置信息
class ProductionConfig(Config):
    pass

# 创建配置类映射
config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}

