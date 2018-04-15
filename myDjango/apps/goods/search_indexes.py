# -*- coding:utf-8 -*-
from haystack import indexes
from goods.models import GoodsSKU

class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    """建立索引时被使用的类"""

    # text  是索引字段名 一般都叫text   use_template使用模板指定哪些字段需要添加
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """从哪个表中查询"""
        return GoodsSKU

    def index_queryset(self, using=None):
        """返回要建立索引的数据"""
        return self.get_model().objects.all()