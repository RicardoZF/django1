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
        client = Fdfs_client('./client.conf')

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