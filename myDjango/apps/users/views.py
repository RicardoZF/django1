import re

from django.conf import settings
from django.contrib.sessions.backends import db
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View
from users.models import User


# def register(request):
#     # 注册页面
#     return render(request,'register.html')

class RegisterView(View):
    # 注册页面
    def get(self,request):
        return render(request, 'register.html')

    def post(self,request):

        # 获取注册请求参数
        user_name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 参数校验：缺少任意一个参数，就不要在继续执行
        if not all([user_name,pwd,email]):
            return redirect(reverse('users:register'))

        # 判断邮箱
        if not re.match(r"^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$", email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 判断是否勾选
        if allow != 'on':
            return render(request,'register.html',{'errmsg':'未勾选协议'})

        # 保存到数据库
        try:
            # 用django提供的用户认证加密
            user = User.objects.create_user(username=user_name,password=pwd,email=email)
        except db.IntegrityError:
            return render(request,'register.html',{'errmsg':'用户已注册'})

        # 手动的将用户认证系统默认的激活状态is_active设置成False,默认是True
        user.is_active =False


        # 生成token 包含user.id  这个过程叫签名
        token = user.generate_active_token()

        # 给用户发送激活邮件 send_mail()
        # recipient_list 是用户列表
        recipient_list = ['18226926930@163.com',]
        send_active_email(recipient_list,user.username,token)

        user.is_active = True
        # 保存到数据库
        user.save()
        return HttpResponse('登陆逻辑')


class ActiveView(View):
    """邮件激活"""

    def get(self, request, token):
        """处理激活请求"""
        pass


def send_active_email(recipient_list,user_name,token):
    """发送邮件方法"""

    # 参一 邮件标题 参二 邮件内容,纯字符串格式  参三 发送人  参四 收件人
    html_message = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                  '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                  'http://127.0.0.1:8000/users/active/%s</a></p>' %(user_name, token, token)
    send_mail('天天生鲜激活','',settings.EMAIL_FROM, recipient_list,html_message=html_message,)