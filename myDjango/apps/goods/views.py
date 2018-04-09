from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner, GoodsSKU


class IndexView(View):
    """首页"""

    def get(self, request):
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
            title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by('index')
            category.title_banners = title_banners

            image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by('index')
            category.image_banners = image_banners

        # 活动
        promotion_banners = IndexPromotionBanner.objects.all()

        context = {
            'categorys': categorys,
            'banners': banners,
            'promotion_banners': promotion_banners,
        }

        # 设置缓存数据：名字，内容，有效期
        cache.set('index_page_data', context, 3600)

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
            cart_dict = redis_conn.hget('cart_%s' % user_id)
            # 遍历购物车字典,累加到购物车
            for value in cart_dict.values():
                cart_num += int(value)

        # 补充购物车数据
        context.update(cart_num=cart_num)

        return render(request, 'index.html', context)


class DetailView(View):
    """商品详细信息页面"""

    def get(self, request, sku_id):
        # 传入的参数:skuid
        """
        需要获取的数据:
        sku,商品分类,同名其他规格商品,评论,新品推荐,购物车数量,浏览记录
        """
        # 尝试从缓存获取
        context = cache.get("detail_%s" % sku_id)
        if context:
            # 有数据就直接返回
            return render(request, 'detail.html', context)
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 商品分类
        categorys = GoodsCategory.objects.all()

        # 同名其他规格商品
        other_skus = sku.goods.goodssku_set.exclude(id=sku_id)

        # 先判断该商品是否有订单
        # 有则获取最新的30条评论信息
        sku_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]
        if sku_orders:
            for sku_order in sku_orders:
                sku_order.ctime = sku_order.create_time.strftime('%Y-%m-%d %H:%M:%S')
                # 订单所属的用户名
                sku_order.username = sku_order.order.user.username
        else:
            sku_orders = []

        # 新品推荐
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]

        # 设置缓存
        context = {
            "categorys": categorys,
            "sku": sku,
            "orders": sku_orders,
            "new_skus": new_skus,
            "other_skus": other_skus
        }

        cache.set("detail_%s" % sku_id, context)

        # 购物车数量
        cart_num = 0
        # 如果是登录的用户
        if request.user.is_authenticated():
            # 获取用户id
            user_id = request.user.id
            # 从redis中获取购物车信息
            redis_conn = get_redis_connection("default")
            # 如果redis中不存在，会返回None
            cart_dict = redis_conn.hgetall("cart_%s" % user_id)
            for val in cart_dict.values():
                cart_num += int(val)

            # 浏览记录: lpush history_userid sku_1 sku_2  (redis中以list形式存储)
            # 移除已经存在的本商品浏览记录
            # count > 0: 从头往尾移除
            # count < 0: 从尾往头移除
            # count = 0: 移除所有
            # lrem key count value
            redis_conn.lrem('history_%s' % user_id, 0, sku_id)
            # 添加新的浏览记录
            redis_conn.lpush('history_%s' % user_id, sku_id)
            # 最多保存5个数据
            # LTRIM KEY_NAME START STOP
            # 对一个列表进行修剪，让列表只保留指定区间内的元素，不在指定区间之内的元素都将被删除。
            redis_conn.ltrim("history_%s"%user_id, 0, 4)

        context['cart_num'] = cart_num

        return render(request, 'detail.html', context)