"""
Django settings for myDjango project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import sys

# 添加导包路径
sys.path.insert(1, os.path.join(BASE_DIR, 'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')-k0p3*bm34kzpbz1530=o#itliid#0el(_l&*j!md0f+*8bdk'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'goods',
    'orders',
    'cart',
    # 富文本编辑器
    'tinymce',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'myDjango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myDjango.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ttsx',
        'HOST': '192.168.44.129',
        'PORT': '3306',
        'USER': 'root',
        'PASSWORD': 'mysql',
    },
    # 'slave': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': 'dailyfresh',
    #     'HOST': '192.168.47.70',
    #     'PORT': '3306',
    #     'USER': 'root',
    #     'PASSWORD': 'mysql',
    # },
}
# 配置读写分离
# DATABASE_ROUTERS = ['utils.db_router.MasterSlaveDBRouter']

# 缓存
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.44.129:6379/5",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Session
# http://django-redis-chs.readthedocs.io/zh_CN/latest/#session-backend

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# 应用.用户模型类
AUTH_USER_MODEL = 'users.User'
# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
# 配置静态文件加载路径
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# 配置邮箱
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 导入邮件模块
EMAIL_HOST = 'smtp.163.com'  # 发邮件主机
EMAIL_PORT = 25  # 发邮件端口
EMAIL_HOST_USER = '18226926930@163.com'  # 授权的邮箱
EMAIL_HOST_PASSWORD = 'xiaoxin369'  # 邮箱授权时获得的密码，非注册登录密码
EMAIL_FROM = '18226926930@163.com'  # 发件人抬头

# 指定装饰器@login_required验证失败后跳转到的路径
LOGIN_URL = '/users/login'

# 配置Django自定义的存储系统
DEFAULT_FILE_STORAGE = 'utils.fastdfs.storage.FastDFSStorage'

# FastFDS使用的配置信息
CLIENT_CONF = os.path.join(BASE_DIR, 'utils/fastdfs/client.conf')
SERVER_IP = 'http://192.168.44.129:8888/'

# 富文本编辑器配置
TINYMCE_DEFAULT_CONFIG = {
  'theme': 'advanced', # 丰富样式
  'width': 600,
  'height': 400,
}
