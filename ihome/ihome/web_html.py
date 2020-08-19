from flask import Blueprint, current_app, make_response
from flask_wtf import csrf

# 创建提供静态文件的蓝图对象
html = Blueprint("web_html", __name__)

@html.route("/<re(r'.*'):file_name>")
def get_html(file_name):
    # 专门提供html静态文件 
    if file_name == '':
        file_name = "index.html"
    if file_name != 'favicon.ico':
        file_name = "html/"+file_name

    # 创建一个csrf_token的值
    csrf_token = csrf.generate_csrf()

    # 组织返回信息
    resp = make_response(current_app.send_static_file(file_name))
    # 添加csrf_token的cookies, 不设置有效期默认关闭浏览器失效
    resp.set_cookie("csrf_token", csrf_token)
    return resp




