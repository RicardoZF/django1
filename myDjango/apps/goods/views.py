from django.core.cache import cache
from django.core.paginator import Paginator, InvalidPage
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic import View
from django_redis import get_redis_connection
import json
from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner, GoodsSKU

class BaseCartView(View):
    """提供购物车数据统计功能"""
    def get_cart_num(self, request):

        cart_num = 0
        if request.user.is_authenticated():
            # 登陆,从redis获取
            # 获取用户id
            user_id = request.user.id
            # 创建redis连接对象
            redis_conn = get_redis_connection('default')
            # 从redis中获取购物车数据，返回字典,如果没有数据，返回None,所以不需要异常判断
            cart_dict = redis_conn.hgetall('cart_%s'%user_id)
        else:
            # 未登录,从cookie获取
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                # 将json数据转为字典
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
        # 遍历购物车字典，计算商品数量
        for val in cart_dict.values():
            cart_num += int(val)

        return cart_num


class IndexView(View):
    """首页"""

    def get(self, request):
        """查询首页需要的数据,返回"""

        # 从缓存中取数据,有数据直接返回
        context = cache.get('index_page_data')
        if context is None:

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
        else:
            print('使用的缓存的数据')

        cart_num = BaseCartView().get_cart_num(request)

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
        if context is None:

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
        cart_num = BaseCartView().get_cart_num(request)

        # 如果是登录的用户
        if request.user.is_authenticated():
            # 获取用户id
            user_id = request.user.id
            # 创建redis连接对象
            redis_conn = get_redis_connection('default')
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
            redis_conn.ltrim("history_%s" % user_id, 0, 4)

        context['cart_num'] = cart_num

        return render(request, 'detail.html', context)


class ListView(View):
    """商品列表页"""

    def get(self, request, category_id, page):
        """
         /list/category_id/page_num/?sort='默认，价格，人气'
        参数: category_id page_num
        需要获取的数据:
        sort 当前分类 所有分类 当前分类所有sku 购物车 新品推荐
        """
        # sort
        sort = request.GET.get('sort')

        # 当前分类
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 查询商品所有类别
        categorys = GoodsCategory.objects.all()

        # 购物车数量
        cart_num = BaseCartView().get_cart_num(request)

        # 新品推荐
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[:2]

        # 按sort查询商品 'price' 'hot' 'default'
        if sort == 'price':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')
        else:
            skus = GoodsSKU.objects.filter(category=category)
            # 无论用户是否传入或者传入其他的排序规则，我在这里都重置成'default'
            sort = 'default'

        # 分页 参一 所有商品对象 参二 每页的数量
        paginator = Paginator(skus, 2)
        # paginator.num_pages 页面总数。
        # paginator.page_range 页码的范围列表，从1开始，例如[1, 2, 3, 4]。
        # [1,2,3,4,5,6,7,8]
        # 总页数 <= 5 显示所有页
        # page <= 3 显示前5页
        # page 是最后3页 显示最后5页
        # 其他
        if paginator.num_pages <= 5:
            page_list = paginator.page_range
        elif page <= 3:
            page_list = range(1, 6)
        elif paginator.num_pages - page <= 2:
            page_list = range(paginator.num_pages - 4, paginator.num_pages + 1)
        else:
            page_list = range(page - 2, page + 3)

        # 获取当前页数据
        try:
            page_skus = paginator.page(page)
        except InvalidPage:
            # 如果page_num不正确，默认给用户第一页数据
            page_skus = paginator.page(1)

        context = {
            'sort':sort,
            'category': category,
            'categorys': categorys,
            'page_skus': page_skus,
            'new_skus': new_skus,
            'cart_num': cart_num,
            'page_list':page_list,
        }

        return render(request, 'list.html', context)
