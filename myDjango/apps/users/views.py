import json
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
from users.models import User, Address
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from utils.views import LoginRequired
from django_redis import get_redis_connection
from goods.models import GoodsSKU
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

        # 在页面跳转之前，将cookie中和redis中的购物车数据合并
        # 1.取出cookie里购物车数据
        cart_json = request.COOKIES.get('cart')
        if cart_json:
            cart_dict_cookie = json.loads(cart_json)
        else:
            cart_dict_cookie = {}

        # 2.取出redis里购物车数据
        # 创建redis对象
        redis_conn = get_redis_connection('default')
        # 获取数据
        cart_dict_redis = redis_conn.hgetall('cart_%s'%user.id)

        # 3.进行购物车商品数量合并:将cookie中购物车数量合并到redis中
        # 注意 :redis取出的 cart_dict  {b'3': b'1'} ,而 从cookie取出的是 cart_json '{"5": 2, "1": 2, "4": 1}'
        for sku_id,count in cart_dict_cookie.items():
            # 将cookie里取出的数据转码
            sku_id = sku_id.encode()

            # redis里有cookie里的skuid则累加数量
            if sku_id in cart_dict_redis:
                count += int(cart_dict_redis[sku_id])

            # 没有,则直接赋值
            cart_dict_redis[sku_id] = count

        # 4.将合并后的redis数据，设置到redis中:redis_conn.hmset()不能传入空字典
        if cart_dict_redis:
            # hmset不能存空
            # hmset 一次存多条数据 类似命令行 cart_user.id skuid1 5 skuid2 6
            redis_conn.hmset('cart_%s' % user.id, cart_dict_redis)

        # 根据next决定访问的页面
        next = request.GET.get('next')
        if next is None:
            # 跳转到首页
            response = redirect(reverse('goods:index'))
        else:
            # 从哪来，回哪去
           response = redirect(next)

        # 清除cookie
        response.delete_cookie('cart')

        return response

class LogoutView(View):
    """登出"""

    def get(self, request):
        # 由Django用户认证系统完成：需要清理cookie和session,request参数中有user对象
        logout(request)
        # 退出后跳转：由产品经理设计
        return redirect(reverse('users:login'))


class AddressView(LoginRequired, View):
    """用户地址"""

    def get(self, request):
        """提供用户地址"""
        # 判断用户是否登陆
        # if not request.user.is_authenticated():
        #     return redirect(reverse('users:login'))

        user = request.user
        # 获取最新的地址
        # address = user.address_set.order_by('-create_time')[0]
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            # 地址不存在
            address = None
        context = {
            # 'user':user,  # 不用传,request中有
            'adderss': address,
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        """修改用户地址"""

        # 接收地址表单数据
        user = request.user

        recv_name = request.POST.get('receiver_name')  # 收件人
        recv_mobile = request.POST.get('receiver_mobile')  # 联系电话
        addr = request.POST.get('detail_addr')  # 详细地址
        zip_code = request.POST.get('zip_code')  # 邮政编码

        # 校验参数
        if all([recv_name,recv_mobile,addr,zip_code]):

            # address = Address(
            #     user=user,
            #     receiver_name=recv_name,
            #     detail_addr=addr,
            #     zip_code=zip_code,
            #     receiver_mobile=recv_mobile
            # )
            # address.save()

            # 保存到数据库
            Address.objects.create(
                user=user,
                receiver_name=recv_name,
                detail_addr=addr,
                zip_code=zip_code,
                receiver_mobile=recv_mobile
            )

        return redirect(reverse('users:address'))


class UserInfoView(View):
    """用户中心"""

    def get(self,request):
        """查询用户信息和地址信息"""

        user = request.user

        # 获取最新的地址信息
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            # 地址不存在
            address = None

        # 获取最新的5个浏览记录

        # 存在redis  string 列表 集合 有序集合 hash
        # 存的是  列表形式  'history_userid':[sku1.id,sku2.id,sku3.id,sku4.id,sku5.id,]

        # 创建redis连接对象
        redis_conn = get_redis_connection('default')

        # 从redis中取商品浏览列表数据 没有数据,返回的是空列表[]
        sku_ids = redis_conn.lrange('history_%s'%user.id,0,4)
        # 从数据库中查询商品sku信息,范围在sku_ids中
        # sku_list = GoodsSKU.objects.filter(id_in=sku_ids)
        # 问题：经过数据库查询后得到的skuList，就不再是redis中维护的顺序了,而是[2,5,8]
        # 需求：保证经过数据库查询后，依然是[8,2,5]
        # 循环遍历,加入列表
        skus = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            skus.append(sku)

        context = {
            'adderss': address,
            'skus':skus
        }
        return render(request,'user_center_info.html',context)
