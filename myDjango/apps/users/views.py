import re

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends import db
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.utils.decorators import classonlymethod
from django.views.generic import View

from celery_tasks.tasks import send_active_email
from users.models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from utils.views import LoginRequired


class RegisterView(View):
    # 注册页面
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):

        # 获取注册请求参数
        user_name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 参数校验：缺少任意一个参数，就不要在继续执行
        if not all([user_name, pwd, email]):
            return redirect(reverse('users:register'))

        # 判断邮箱
        if not re.match(r"^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$", email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 判断是否勾选
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '未勾选协议'})

        # 保存到数据库
        try:
            # 用django提供的用户认证加密
            user = User.objects.create_user(username=user_name, password=pwd, email=email)
        except db.IntegrityError:
            return render(request, 'register.html', {'errmsg': '用户已注册'})

        # 手动的将用户认证系统默认的激活状态is_active设置成False,默认是True
        user.is_active = False

        # 生成token 包含user.id  这个过程叫签名
        token = user.generate_active_token()

        # 给用户发送激活邮件 send_mail()
        # recipient_list 是用户列表
        recipient_list = ['18226926930@163.com', ]
        # delay 通知woeker执行
        send_active_email.delay(recipient_list, user.username, token)

        # 保存到数据库
        user.save()
        return HttpResponse('登陆逻辑')


class ActiveView(View):
    """邮件激活"""

    def get(self, request, token):
        """处理激活请求"""
        # 解析token 获取用户id数据
        # 参1 混淆用的盐  参2 过期时间
        serializer = Serializer(settings.SECRET_KEY, 3600)
        result = serializer.loads(token)  # {"confirm": self.id}
        userid = result.get("confirm")

        # 通过userid获取用户,将用户转化为激活状态
        try:
            user = User.objects.get(id=userid)
        except User.DoesNotExist:
            return HttpResponse('用户不存在')

        if user.is_active:
            return HttpResponse('用户已激活')
        user.is_active = True
        user.save()

        return redirect(reverse('users:login'))


class LoginView(View):
    """登陆"""

    def get(self, request):
        """响应登陆请求"""
        return render(request, 'login.html')

    def post(self, request):
        """处理 登陆逻辑"""

        # 获取用户名,密码
        user_name = request.POST.get('username')
        pwd = request.POST.get('pwd')

        # 校验参数
        if not all([user_name, pwd]):
            return redirect(reverse('users:login'))

        # django用户认证系统判断是否登陆成功
        user = authenticate(username=user_name, password=pwd)

        # 验证失败
        if user is None:
            return render(request, 'login.html', {'errormsg': '用户名或密码错误'})
        # 验证成功,再验证是否激活
        if not user.is_active:
            return render(request, 'login.html', {'errormsg': '用户未激活'})
        # 使用django的用户认证系统，在session中保存用户的登陆状态
        login(request, user)

        # 判断用户是否勾选'记住用户'
        # request.session.set_expiry(value)
        # value 是一个整数，会话将在value秒后过期;为0 浏览器关闭时;
        # value 为None，那么会话则两个星期后过期
        if request.POST.get('remembered') != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)
        # 登陆成功，根据next决定访问的页面
        next = request.GET.get('next')
        if next is None:
            return HttpResponse('去主页')
        else:
            return redirect(next)


class LogoutView(View):
    """登出"""

    def get(self, request):
        # 由Django用户认证系统完成：需要清理cookie和session,request参数中有user对象
        logout(request)
        # 退出后跳转：由产品经理设计
        return redirect(reverse('users:login'))


class AddressView(LoginRequired,View):
    """用户地址"""

    def get(self, request):
        """提供用户地址"""
        # 判断用户是否登陆
        # if not request.user.is_authenticated():
        #     return redirect(reverse('users:login'))

        return render(request, 'user_center_site.html')

    # @classonlymethod
    # def as_view(cls, **initkwargs):
    #     view = super().as_view
    #     return login_required(view)