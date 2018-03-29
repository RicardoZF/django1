from django.conf.urls import url

from users import views

urlpatterns = [
    # 注册
    url(r'^register$',views.RegisterView.as_view(),name='register'),
    url(r'^active/(?P<token>.+)$',views.ActiveView.as_view(),name='register'), # 邮件激活
    url(r'^login$',views.LoginView.as_view(),name='login'), # 登陆
    url(r'^logout$',views.LogoutView.as_view(),name='logout'), # 登陆
]