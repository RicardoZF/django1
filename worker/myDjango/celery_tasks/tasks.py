import os
# 添加环境变量
os.environ["DJANGO_SETTINGS_MODULE"] = "myDjango.settings"
# 放到Celery服务器上时添加的代码
import django
django.setup()

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 实例化celery对象
# 参一:生成任务的文件路径  参二:broker的redis地址  redis://:密码@ip:端口号/数据库号
app = Celery('celery_tasks.tasks',broker='redis://192.168.44.129:6379/3')

# 装饰器  让方法成为celery任务
@app.task
def send_active_email(recipient_list,user_name,token):
    """发送邮件方法"""

    # 参一 邮件标题 参二 邮件内容,纯字符串格式  参三 发送人  参四 收件人
    html_message = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                  '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                  'http://127.0.0.1:8000/users/active/%s</a></p>' %(user_name, token, token)
    send_mail('天天生鲜激活','',settings.EMAIL_FROM, recipient_list,html_message=html_message,)