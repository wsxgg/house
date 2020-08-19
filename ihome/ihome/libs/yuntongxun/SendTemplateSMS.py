'''
@Author: your name
@Date: 2020-05-22 15:30:50
@LastEditTime: 2020-05-22 19:35:21
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: \ihome\ihome\libs\yuntongxun\SendTemplateSMS.py
'''
#coding=gbk

#coding=utf-8

#-*- coding: UTF-8 -*-

from .CCPRestSDK import REST
import configparser

#主账号
accountSid = '8a216da871f37b2f01723ae3bde2022a'

#主账号Token
accountToken = 'f7cb9680216a47a69c654b370d778c0b'

#应用Id
appId = '8a216da871f37b2f01723ae3be650231'

#请求地址，不需要写http://
serverIP = 'app.cloopen.com'

#请求端口
serverPort = 8883

#REST版本号
softVersion = '2013-12-26'

# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如['12','34'] 如不需要替换填''
# @param $tempId 模板Id


class CCP():
    """自己封装的发短信的辅助类"""
    # 单例
    instance = None

    def __new__(cls):
        # 判断CCP有没有实例，如果有直接返回，如果没有创建实例
        if cls.instance is None:
            obj = super().__new__(cls)
            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)
            cls.instance = obj
            return obj

        return cls.instance

    def send_template_sms(self, to, datas, tempId):
        result = self.rest.sendTemplateSMS(to, datas, tempId)
        # for k, v in result.items():
        #     if k == 'templateSMS':
        #         for k, s in v.items():
        #             print ('%s:%s' % (k, s))
        #     else:
        #         print ('%s:%s' % (k, v))
        # 返回值：
        # statusCode:000000       000000表示成功
        # smsMessageSid:9c9629fad5e045e6ab09b562b2cb303a
        # dateCreated:20200522164622
        # 判断是否发送成功
        status_code = result.get("statusCode")
        if status_code == "000000":
            return 0
        else:
            return -1


if __name__ == "__main__":
    ccp = CCP()
    ret = ccp.send_template_sms("15720606667", ["1234", '5'], 1)
    print(ret)
    


# sendTemplateSMS(手机号, 内容数据, 模板Id)