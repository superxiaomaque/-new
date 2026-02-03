"""
文件服务路由
"""
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/files", tags=["文件"])

@router.get("/{filepath:path}")
async def get_file(filepath: str):
    """获取文件"""
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
