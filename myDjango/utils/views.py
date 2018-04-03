# -*- coding:utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.utils.decorators import classonlymethod


class LoginRequired(object):
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view
        return login_required(view)