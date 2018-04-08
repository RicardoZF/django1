# -*- coding:utf-8 -*-
from django.conf.urls import url
from goods import views

urlpatterns = [
    url(r'^index$', views.IndexView.as_view(), name='index')  # 商品主页
]
