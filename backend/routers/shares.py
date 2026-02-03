"""
分享相关路由
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db, User, Analysis, ShareLink
from anonymous import get_default_user
from services.storage import StorageService

router = APIRouter(prefix="/shares", tags=["分享"])
storage_service = StorageService()

@router.post("/{analysis_id}")
async def create_share_link(
    analysis_id: int,
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db)
):
    """创建分享链接"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在"
        )
    
    # 生成分享token
    share_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    # 创建分享链接
    share_link = ShareLink(
        analysis_id=analysis_id,
        share_token=share_token,
        expires_at=expires_at
    )
    db.add(share_link)
    db.commit()
    db.refresh(share_link)
    
    return {
        "share_token": share_token,
        "share_url": f"/share/{share_token}",
        "expires_at": expires_at.isoformat()
    }

@router.get("/{share_token}")
async def get_share_analysis(
    share_token: str,
    db: Session = Depends(get_db)
):
    """获取分享的分析结果（免登录）"""
    share_link = db.query(ShareLink).filter(
        ShareLink.share_token == share_token
    ).first()
    
    if not share_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分享链接不存在"
        )
    
    # 检查是否过期
    if share_link.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="分享链接已过期"
        )
    
    # 更新访问次数
    share_link.view_count += 1
    db.commit()
    
    # 获取分析结果
    analysis = db.query(Analysis).filter(
        Analysis.id == share_link.analysis_id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在"
        )
    
    import json
    try:
        result_data = json.loads(analysis.result)
    except:
        result_data = {"raw_text": analysis.result}
    
    return {
        "id": analysis.id,
        "result": result_data,
        "view_count": share_link.view_count,
        "created_at": analysis.created_at.isoformat(),
        # tos 模式可用时可提供签名URL（前端目前不展示原图，仅预留）
        "images_signed": _signed_images_safe(analysis.images),
    }


def _signed_images_safe(images):
    try:
        if not images:
            return []
        if (storage_service.backend or "local") != "tos":
            return []
        return [storage_service.get_signed_url(k, expires=3600) for k in images]
    except Exception:
        return []
