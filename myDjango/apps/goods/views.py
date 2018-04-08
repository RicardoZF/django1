from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from goods.models import GoodsCategory,IndexGoodsBanner,IndexPromotionBanner, IndexCategoryGoodsBanner


class IndexView(View):
    """首页"""

    def get(self,request):
        """查询首页需要的数据,返回"""
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

        return render(request,'index.html',context)

