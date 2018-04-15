from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
import json
from goods.models import GoodsSKU


class AddCartView(View):
    """添加到购物车"""

    # def get(self,request):
    #     return HttpResponse('呵呵呵')

    def post(self, request):

        # 接收数据:user_id sku 数量
        user_id = request.user.id
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 2, 'msg': '参数不完整'})

        # 判断是否有此商品
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 3, 'msg': '无此商品'})

        # 判断count是否是整数
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 5, 'msg': '数量参数格式有误'})

        # 判断库存是否足够
        if count > sku.stock:
            return JsonResponse({'code': 4, 'msg': '库存不足'})
            # 判断用户是否登陆

        if request.user.is_authenticated():

            # 存入redis
            # hash类型  cart_userid: {skuid1:value1  skuid2:value2}
            # 创建redis对象
            redis_conn = get_redis_connection('default')

            # 需要先获取要添加到购物车的商品是否存在
            origin_count = redis_conn.hget('cart_%s' % user_id, sku_id)
            if origin_count:
                # redis取出的是string 要强转
                count += int(origin_count)

            redis_conn.hset(name='cart_%s' % user_id, key=sku_id, value=count)

            # 为了配合模板中js交互并展示购物车的数量，在这里需要查询一下购物车的总数
            cart_num = 0
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)
            for val in cart_dict.values():
                # 强转
                cart_num += int(val)
            return JsonResponse({'code': 0, 'msg': '添加购物车成功', 'cart_num': cart_num})
        else:
            # 未登录
            cart_num = 0
            # 从cookie中取数据  cart:'{sku1:value1,sku2:value2}'
            cart_json = request.COOKIES.get('cart')
            # 判断购物车cookie数据是否存在，有可能用户从来没有操作过购物车
            if cart_json:
                # json数据 转为字典
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                # 如果cookie中有这个商品记录，则直接进行求和；如果cookie中没有这个商品记录，则将记录设置到购物车cookie中
                origin_count = cart_dict[sku_id]
                count += int(origin_count)

            # 设置最终的商品数量到购物车
            cart_dict[sku_id] = count
            for val in cart_dict.values():
                # 强转
                cart_num += int(val)

            print(cart_num)
            response = JsonResponse({'code': 0, 'msg': '添加购物车成功', 'cart_num': cart_num})

            # 将字典转为json存入cookie
            cart_json = json.dumps(cart_dict)
            response.set_cookie('cart', cart_json)
            # 返回数据
            return response


class CartInfoView(View):
    """购物车详情页面"""
    def get(self,request):
        """
        需要返回: sku 单个sku商品金额及数量 所有sku商品总金额和总数量
        """

        # 查询购物车数据
        if request.user.is_authenticated():
            # 登陆,从redis取
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s'%user_id)
        else:
            # 未登陆,从cookie取
            cart_json = request.COOKIES.get('cart')

            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

        # 保存遍历出来的sku
        skus = []
        # 总金额
        total_amount = 0
        # 总数量
        total_count = 0
        for sku_id,count in cart_dict.items():
            try:
                # 获取商品sku
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                # 商品不存在，跳过这个商品，继续遍历
                continue

            # redis取出的是string,所以将count转为int
            count = int(count)

            # 总金额
            amount = sku.price * count

            # 将需要展示的数据保存到对象中
            sku.amount = amount
            sku.count = count

            # 生成模型列表
            skus.append(sku)

            # 计算总金额 总数量
            total_amount += amount
            total_count +=count

        context = {
            'skus':skus,
            'total_amount':total_amount,
            'total_count':total_count,
        }

        return render(request,'cart.html',context)