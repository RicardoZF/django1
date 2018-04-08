import os
# # 添加环境变量
os.environ["DJANGO_SETTINGS_MODULE"] = "myDjango.settings"
# 放到Celery服务器上时添加的代码
import django
django.setup()

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 实例化celery对象
# 参一:生成任务的文件路径  参二:broker的redis地址  redis://:密码@ip:端口号/数据库号
from django.template import loader

from goods.models import GoodsCategory, IndexCategoryGoodsBanner, IndexPromotionBanner
from goods.models import IndexGoodsBanner

app = Celery('celery_tasks.tasks',broker='redis://192.168.44.129:6379/3')

# 装饰器  让方法成为celery任务
@app.task
def send_active_email(recipient_list,user_name,token):
    """发送邮件方法"""

    # 参一 邮件标题 参二 邮件内容,纯字符串格式  参三 发送人  参四 收件人
    html_message = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                  '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                  'http://127.0.0.1:8000/users/active/%s</a></p>' %(user_name, token, token)
    send_mail('天天生鲜激活','',settings.EMAIL_FROM, recipient_list,html_message=html_message,)

@app.task
def generate_static_index_html():
    """查询首页需要的数据,返回"""
    # 用户个人信息(request.user)
    # 商品分类信息
    categorys = GoodsCategory.objects.all()

    # 轮播图,按照index进行排序
    banners = IndexGoodsBanner.objects.all().order_by('index')

    # 分类商品详情
    for category in categorys:
        title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by('index')
        category.title_banners = title_banners

        image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by('index')
        category.image_banners = image_banners

    # 购物车
    cart_num = 0
    # 活动
    promotion_banners = IndexPromotionBanner.objects.all()

    context = {
        'categorys': categorys,
        'banners': banners,
        'promotion_banners': promotion_banners,
        'cart_num': cart_num
    }

    # content是渲染好的模板的最终html代码
    content = loader.render_to_string('static_index.html',context)

    # 把content保存成一个静态文件
    # 获取要写入的文件路径 放在static文件夹下
    file_path =os.path.join(settings.STATICFILES_DIRS[0],'index.html')
    # 写入数据
    with open(file_path,'w') as f:
        f.write(content)
