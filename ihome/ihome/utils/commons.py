
from werkzeug.routing import BaseConverter
import functools
from flask import jsonify, g, session
from ihome.utils.response_code import RET

# 制作万能转换器
class RegexConverter(BaseConverter):
    def __init__(self, url_map, regex):
        # 调用父类构造方法
        super().__init__(url_map)
        self.regex = regex
        

# 定义用户登录验证的装饰器
def login_required(view_func):
   
    @functools.wraps(view_func)
    # functools.wraps装饰器可以解决因为添加装饰器而造成的函数属性改变，如__name__,__doc__等
    def wrapper(*args, **kwargs):
        # 判断用户登录状态
        user_id = session.get("user_id")
        if user_id is not None:
            # 将user_id添加到全局对象，可以在试图函数中使用
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
        
    return wrapper
