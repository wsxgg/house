
from qiniu import Auth, put_data, etag
import qiniu.config

#需要填写你的 Access Key 和 Secret Key
access_key = '5OzHXGWw8rCKnsmFO98VuLK6rstGhFA_9o9ok3qN'
secret_key = 'OCPoAr3BpvyFVAecNYlXquRJfqzwkE9lFzQHel_-'

# 定义上传文件的方法
def storage(file_data):
    #构建鉴权对象
    q = Auth(access_key, secret_key)

    #要上传的空间
    bucket_name = 'ihome-swx'

    #生成上传 Token，可以指定过期时间等, 参数： 上传的空间；上传后的文件名；token有效期
    token = q.upload_token(bucket_name, None, 3600)

    # 上传数据， 参数： token;上传后的文件名；文件数据
    ret, info = put_data(token, None, file_data)
    if info.status_code == 200:
        # 表示上传成功，返回文件名
        return ret.get("key")
    else:
        # 上传失败
        raise Exception("上传七牛失败")
