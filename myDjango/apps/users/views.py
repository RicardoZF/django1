import re

from django.contrib.sessions.backends import db
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View


# def register(request):
#     # 注册页面
#     return render(request,'register.html')
from users.models import User


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

        # 保存到数据库
        user.save()

        return HttpResponse('登陆逻辑')