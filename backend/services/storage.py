"""
云存储服务（火山引擎TOS）
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import List

def _get_settings():
    """动态获取settings，支持测试模式"""
    try:
        from config import settings
        return settings
    except ImportError:
        import sys
        if 'config' in sys.modules:
            from config import settings
            return settings
        else:
            from test_config import settings
            return settings

class StorageService:
    """
    存储服务封装：
    - 默认 local：本地 uploads/
    - 可切换 tos：火山引擎TOS（需要安装TOS SDK并配置环境变量）
    """

    def __init__(self):
        settings = _get_settings()
        self.backend = (settings.STORAGE_BACKEND or "local").lower()
        self.storage_path = "uploads"
        os.makedirs(self.storage_path, exist_ok=True)
        self._tos_client = None
        if self.backend == "tos":
            self._init_tos()

    def _init_tos(self):
        """
        延迟初始化TOS。当前仓库未内置SDK依赖，避免阻塞本地运行；
        你后续接入时只需：
        - pip 安装火山引擎TOS SDK
        - 配置 TOS_ACCESS_KEY/TOS_SECRET_KEY/TOS_ENDPOINT/TOS_BUCKET
        - 设置 STORAGE_BACKEND=tos
        """
        try:
            import tos  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "当前未安装TOS SDK，无法启用 STORAGE_BACKEND=tos。"
                "请先安装火山引擎TOS SDK（或保持 STORAGE_BACKEND=local）。"
            ) from e

        if not (settings.TOS_ACCESS_KEY and settings.TOS_SECRET_KEY and settings.TOS_ENDPOINT and settings.TOS_BUCKET):
            raise RuntimeError("启用TOS需要配置 TOS_ACCESS_KEY/TOS_SECRET_KEY/TOS_ENDPOINT/TOS_BUCKET")

        auth = tos.CredentialProvider(settings.TOS_ACCESS_KEY, settings.TOS_SECRET_KEY)
        self._tos_client = tos.TosClientV2(settings.TOS_ENDPOINT, auth, enable_crc=True)
    
    def upload_images(self, images: List, user_id: int) -> List[str]:
        """
        上传图片到云存储
        
        Args:
            images: 图片文件列表
            user_id: 用户ID
        
        Returns:
            图片URL列表
        """
        image_urls = []

        if self.backend == "tos":
            # 存储为 object key，并返回 key（由 files 路由/或 CDN 域名拼 URL）
            for image in images:
                file_ext = os.path.splitext(image.filename)[1]
                key = f"{user_id}/{uuid.uuid4()}{file_ext}"
                body = image.file.read()
                self._tos_client.put_object(settings.TOS_BUCKET, key, body=body)
                image_urls.append(key)
            return image_urls

        # local backend
        user_dir = os.path.join(self.storage_path, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        for image in images:
            file_ext = os.path.splitext(image.filename)[1]
            filename = f"{uuid.uuid4()}{file_ext}"
            filepath = os.path.join(user_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image.file.read())
            image_urls.append(filepath)

        return image_urls
    
    def get_image_url(self, filepath: str) -> str:
        """获取图片访问URL"""
        # 对外统一通过 /files/ 访问（tos模式下 filepath 是 object key）
        return f"/files/{filepath}"

    def get_signed_url(self, key: str, expires: int = 3600) -> str:
        """
        获取 TOS 签名URL（仅 tos 模式可用）
        """
        if self.backend != "tos":
            raise RuntimeError("get_signed_url 仅在 STORAGE_BACKEND=tos 时可用")
        # tos sdk 签名URL（不同版本SDK方法名可能不同，这里做 best-effort）
        try:
            return self._tos_client.pre_signed_url(
                "GET",
                settings.TOS_BUCKET,
                key,
                expires=expires
            ).signed_url
        except Exception as e:
            raise RuntimeError(f"生成签名URL失败: {e}") from e
    
    def delete_images(self, image_urls: List[str]):
        """删除图片"""
        if self.backend == "tos":
            for key in image_urls:
                try:
                    self._tos_client.delete_object(settings.TOS_BUCKET, key)
                except Exception as e:
                    print(f"删除TOS对象失败 {key}: {e}")
            return

        for url in image_urls:
            try:
                if os.path.exists(url):
                    os.remove(url)
            except Exception as e:
                print(f"删除图片失败 {url}: {e}")
    
    def cleanup_expired_files(self, days: int = 30):
        """清理过期文件"""
        cutoff_date = datetime.now() - timedelta(days=days)
        for root, dirs, files in os.walk(self.storage_path):
            for file in files:
                filepath = os.path.join(root, file)
                if os.path.getmtime(filepath) < cutoff_date.timestamp():
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        print(f"清理文件失败 {filepath}: {e}")
