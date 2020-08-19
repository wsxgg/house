from celery import Celery
from ihome.libs.yuntongxun.SendTemplateSMS import CCP


# 定义celery对象, 第一个参数为名称，broker为中间人（任务队列存放位置）
celery_app = Celery("ihome", broker="redis://192.168.152.156:6379/1")

# 定义任务
@celery_app.task
def send_sms(to, datas, temp_id):
    """发送短信的任务"""
    ccp = CCP()
    ccp.send_template_sms(to, datas, temp_id)



