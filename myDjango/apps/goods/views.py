from django.core.cache import cache
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsCategory,IndexGoodsBanner,IndexPromotionBanner, IndexCategoryGoodsBanner


class IndexView(View):
    """首页"""

    def get(self,request):
        """查询首页需要的数据,返回"""

        # 从缓存中取数据,有数据直接返回
        context = cache.get('index_page_data')
        if context:
            return render(request, 'index.html', context)

        # 用户个人信息(request.user)
        # 商品分类信息
        categorys = GoodsCategory.objects.all()

        # 轮播图,按照index进行排序
        banners = IndexGoodsBanner.objects.all().order_by('index')

        # 分类商品详情
        for category in categorys:

            title_banners = IndexCategoryGoodsBanner.objects.filter(category=category,display_type=0).order_by('index')
            category.title_banners = title_banners

            image_banners = IndexCategoryGoodsBanner.objects.filter(category=category,display_type=1).order_by('index')
            category.image_banners = image_banners

        # 活动
        promotion_banners = IndexPromotionBanner.objects.all()

        context = {
            'categorys': categorys,
            'banners': banners,
            'promotion_banners': promotion_banners,
        }

        # 设置缓存数据：名字，内容，有效期
        cache.set('index_page_data',context,3600)

        # 购物车,经常变化,不能存在缓存里
        cart_num = 0

        # 如果用户登陆,获取购物车数据
        # 哈希类型存储：cart_userid sku_1 10 sku_2 20
        # 字典结构：cart_userid:{sku_1:10,sku_2:20}
        if request.user.is_authenticated():
            # 创建redis对象
            redis_conn = get_redis_connection()
            # 获取用户id
            user_id = request.user.id
            # 从redis中获取购物车数据，返回字典
            cart_dict = redis_conn.hget('cart_%s'%user_id)
            # 遍历购物车字典,累加到购物车
            for value in cart_dict.values():
                cart_num += int(value)

        # 补充购物车数据
        context.update(cart_num=cart_num)

        return render(request,'index.html',context)

