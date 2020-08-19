'''
@Author: your name
@Date: 2020-05-22 10:19:30
@LastEditTime: 2020-05-25 12:11:53
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: \ihome\ihome\constants.py
'''
"""保存常量的文件"""

# 图片验证码的redis有效期
IMAGE_CODE_REDIS_EXPIRES = 300


# 短信验证码的redis有效期
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码的间隔
SEND_SMS_CODE_INTERVAL = 60

# 登陆错误次数
LOGIN_ERROR_TIMES = 5

# 错误登陆数据的有效期
LOGIN_ERROR_FORBIN_TIME = 600

# 七牛的域名
QINIU_URL_DOMAIN = "HTTP://qav53q050.bkt.clouddn.com/"

# 区表的redis缓存有效时间
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 主页房屋显示数量
HOME_PAGE_MAX_HOUSES = 5

# 主页房屋显示的redis缓存有效期
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 各个房屋详情的redis缓存有效期
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 显示评论的数目
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 10

# 房屋搜索每页的显示数目
HOUSE_LIST_PAGE_CAPACITY = 8

# 房屋列表缓存有效期
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200
