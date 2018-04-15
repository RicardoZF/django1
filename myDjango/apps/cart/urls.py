# -*- coding:utf-8 -*-
from django.conf.urls import url
from cart import views

urlpatterns = [
    url(r'^add$',views.AddCartView.as_view(),name='add'),
    url(r'^info$',views.CartInfoView.as_view(),name='info'),
]

