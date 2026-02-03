"""
文件服务路由
"""
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os
from config import settings

router = APIRouter(prefix="/files", tags=["文件"])

@router.get("/{filepath:path}")
async def get_file(filepath: str):
    """获取文件"""
    # TOS 模式：这里仅做占位（建议通过 TOS 公网域名/签名URL 直接访问）
    if (settings.STORAGE_BACKEND or "local").lower() == "tos":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="TOS模式下建议使用TOS公开URL/签名URL访问文件；当前 /files 仅支持本地存储。"
        )

    # 安全检查：防止路径遍历攻击
    if ".." in filepath or filepath.startswith("/"):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文件路径"
        )
    
    full_path = os.path.join("uploads", filepath)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)
    else:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
