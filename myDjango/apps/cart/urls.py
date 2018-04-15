# -*- coding:utf-8 -*-
from django.conf.urls import url
from cart import views

urlpatterns = [
    url(r'^add$',views.AddCartView.as_view(),name='add'),  # 添加
    url(r'^info$',views.CartInfoView.as_view(),name='info'),  # 详情
    url(r'^update$',views.UpdateCartView.as_view(),name='delete'),  # 更新
    url(r'^delete$',views.DeletelCartView.as_view(),name='delete'),  # 删除
]

