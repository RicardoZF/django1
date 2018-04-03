from django.conf.urls import url

from users import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # 注册
    url(r'^register$',views.RegisterView.as_view(),name='register'),
    url(r'^active/(?P<token>.+)$',views.ActiveView.as_view(),name='register'), # 邮件激活
    url(r'^login$',views.LoginView.as_view(),name='login'), # 登陆
    url(r'^logout$',views.LogoutView.as_view(),name='logout'), # 登陆
    # url(r'^address$',login_required(views.AddressView.as_view()) ,name='address'), # 收货地址
    url(r'^address$',views.AddressView.as_view() ,name='address'), # 收货地址
]