from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):
    """自定义Django存储系统的类"""

    def __init__(self,client_conf=None,server_ip=None):
        if client_conf is None:
            client_conf = settings.CLIENT_CONF
        self.client_conf = client_conf

        if server_ip is None:
            server_ip = settings.SERVER_IP
        self.server_ip = server_ip

    def _open(self):
        # 访问文件
        pass

    def _save(self,name,content):
        # 存储图片

        #　把图片存到fastdfs

        #　生成fastdfs客户端对象
        client = Fdfs_client(self.client_conf)

        # 读取图片二进制信息
        file_data = content.read()

        # 上传到fastdfs
        # Django借助client向FastDFS服务器上传文件
        try:
            ret = client.upload_by_buffer(file_data)
        except Exception as e:
            print(e)  # 自己调试临时打印
            raise

        # 根据返回数据，判断是否上传成功
        if ret.get('Status') == 'Upload successed.':
            # 读取file_id
            # 获取文件的真实路径和名字
            file_id = ret.get('Remote file_id')
            return file_id

        else:
            raise Exception('上传图片到fastdfs出现异常')

    def exists(self, name):
        """Django用来判断文件是否存在的"""

        # 由于Djnago不存储图片，所以永远返回Fasle，直接保存到FastFDS
        return False

    # 返回能够访问到图片的地址(nginx)
    def url(self,name):
        return self.server_ip + name


# class FastDFSStorage(Storage):

    # def __init__(self,client_conf = None,server_ip=None):
        # """配置信息"""
#         if client_conf is None:
#             # 没传 就用默认文件
#             client_conf = settings.CLIENT_CONF
#
#         self.client_conf = client_conf
#
#         if server_ip is None:
#             server_ip = settings.SERVER_IP
#         self.server_ip = server_ip
#
#     def _open(self):
#         """访问文件时"""
#         pass
#
#     # name 是图片原始名字 content是图片对象 对文件用content.read
#     def _save(self,name,content):
#         """存储图片会走"""
#         # 把图片存到fastdfs
#         # 生成客户端对象
#         client = Fdfs_client(self.client_conf)
#         file_data = content.read()
#         # 上传到dfs 连接远程服务器,可能上传失败
#         try:
#             ret = client.upload_by_buffer(file_data)
#         except Exception as e:
#             print(e)
#             # 抛出异常 让调用人员处理
#             raise
#         # {
#         #     'Group name': 'group1',
#         #     'Status': 'Upload successed.',  # 注意这有一个点
#         #     'Remote file_id': 'group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py',
#         #     'Uploaded size': '6.0KB',
#         #     'Local file name': 'test',
#         #     'Storage IP': '192.168.44.129'
#         # }
#         if ret.get('Status')== 'Upload successed.':
#             file_id = ret.get('Remote file_id')
#             return file_id
#         else:
#             # 让调用人员自己捕获异常
#             raise Exception('上传图片至fdfs失败')
#
#     # 由于Djnago不存储图片，所以永远返回Fasle，直接引导到FastFDS
#     def exists(self, name):
#         return False
#
#     # 返回能够访问到图片的地址(默认返回的是django地址,需要ngix地址)
#     def url(self, name):
#         # name = group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py
#         # http://192.168.44.128:8888/group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py
#         # < img src = {{sku.default_image.url}} >
#         return self.server_ip + name