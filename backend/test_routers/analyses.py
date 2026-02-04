"""
分析相关路由
"""
import os
import json
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from test_database import get_db, User, Analysis
from test_anonymous import get_default_user
from services.doubao_api import DoubaoAPI
from services.storage import StorageService
from services.exporter import render_analysis_to_png, build_zip_of_pngs, PRESET_TAGS
from test_config import settings

router = APIRouter(prefix="/analyses", tags=["分析"])

# 安全初始化服务
try:
    doubao_api = DoubaoAPI()
    storage_service = StorageService()
except Exception as e:
    print(f"[FATAL] 服务初始化失败: {e}")
    import traceback
    traceback.print_exc()
    # 设置为None，在请求时再尝试初始化
    doubao_api = None
    storage_service = None

@router.post("")
async def create_analysis(
    images: List[UploadFile] = File(...),
    supplementary_info: str = Form("{}"),
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db)
):
    """创建分析"""
    # 确保服务已初始化
    global doubao_api, storage_service
    if doubao_api is None or storage_service is None:
        try:
            if doubao_api is None:
                doubao_api = DoubaoAPI()
            if storage_service is None:
                storage_service = StorageService()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"服务初始化失败: {str(e)}"
            )
    
    # 检查图片数量
    if len(images) < settings.MIN_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"至少需要上传{settings.MIN_IMAGES}张图片"
        )
    
    if len(images) > settings.MAX_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"最多只能上传{settings.MAX_IMAGES}张图片"
        )
    
    # 检查文件大小和格式
    for image in images:
        # 检查文件大小
        image.file.seek(0, 2)  # 移动到文件末尾
        file_size = image.file.tell()
        image.file.seek(0)  # 重置到开头
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"图片 {image.filename} 超过大小限制（{settings.MAX_FILE_SIZE / 1024 / 1024}MB）"
            )
        
        # 检查文件格式
        file_ext = os.path.splitext(image.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的图片格式: {file_ext}"
            )
    
    try:
        # 上传图片
        image_urls = storage_service.upload_images(images, current_user.id)
        
        # 解析补充信息
        try:
            supplementary_data = json.loads(supplementary_info) if supplementary_info else {}
        except:
            supplementary_data = {}
        
        # 调用豆包API进行分析
        analysis_result, usage = doubao_api.analyze_friend_circle(
            image_urls=image_urls,
            supplementary_info=supplementary_data
        )
        
        # 保存分析结果（确保是字典格式，不是数组）
        if isinstance(analysis_result, list) and len(analysis_result) > 0:
            analysis_result = analysis_result[0]
        elif not isinstance(analysis_result, dict):
            analysis_result = {"raw_text": str(analysis_result)}
        
        new_analysis = Analysis(
            user_id=current_user.id,
            images=image_urls,
            supplementary_info=supplementary_data,
            result=json.dumps(analysis_result, ensure_ascii=False)
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        
        return {
            "id": new_analysis.id,
            "result": analysis_result,
            "created_at": new_analysis.created_at.isoformat()
        }
        
    except Exception as e:
        # 打印详细错误信息到后端日志
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] 分析失败: {str(e)}")
        print(f"[ERROR] 错误堆栈:\n{error_trace}")
        
        # 如果分析失败，删除已上传的图片
        if 'image_urls' in locals():
            try:
                storage_service.delete_images(image_urls)
            except Exception as cleanup_error:
                print(f"[WARN] 清理图片失败: {cleanup_error}")
        
        # 返回详细错误信息
        error_detail = str(e)
        # 如果是HTTP错误，提取更详细的信息
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            try:
                error_detail = f"{error_detail}\nAPI响应: {e.response.text[:200]}"
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {error_detail}"
        )

@router.get("")
async def get_analyses(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db)
):
    """获取分析列表"""
    skip = (page - 1) * page_size
    analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(Analysis.created_at.desc()).offset(skip).limit(page_size).all()
    
    total = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).count()
    
    items = []
    for analysis in analyses:
        try:
            result_data = json.loads(analysis.result)
            summary = result_data.get('summary', '')[:100]
        except:
            summary = '查看详情'
        
        items.append({
            "id": analysis.id,
            "summary": summary,
            "tag": analysis.tag,
            "created_at": analysis.created_at.isoformat()
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db)
):
    """获取分析详情"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在"
        )
    
    try:
        result_data = json.loads(analysis.result)
        # 如果 result 是数组，取第一个元素
        if isinstance(result_data, list) and len(result_data) > 0:
            result_data = result_data[0]
    except:
        result_data = {"raw_text": analysis.result}
    
    return {
        "id": analysis.id,
        "result": result_data,
        "images": analysis.images,
        "supplementary_info": analysis.supplementary_info,
        "tag": analysis.tag,
        "created_at": analysis.created_at.isoformat()
    }

@router.post("/{analysis_id}/chat")
async def chat_with_analysis(
    analysis_id: int,
    question: dict,
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db)
):
    """多轮对话"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在"
        )
    
    try:
        answer, _usage = doubao_api.chat(
            analysis_id=analysis_id,
            question=question.get("question", ""),
            context=analysis.result
        )
        
        return {
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话失败: {str(e)}"
        )

@router.patch("/{analysis_id}/tag")
async def update_tag(
    analysis_id: int,
    tag_data: dict,
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db)
):
    """更新标签"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在"
        )
    
    analysis.tag = tag_data.get("tag", "")
    db.commit()
    
    return {"message": "标签更新成功"}


@router.get("/{analysis_id}/export.png")
async def export_analysis_png(
    analysis_id: int,
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db),
):
    """导出单条分析结果为PNG（不包含原图）"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在"
        )

    try:
        result_data: Dict[str, Any] = json.loads(analysis.result)
        # 如果 result 是数组，取第一个元素
        if isinstance(result_data, list) and len(result_data) > 0:
            result_data = result_data[0]
    except Exception:
        result_data = {"raw_text": analysis.result, "summary": "导出失败：结果解析错误"}

    png_bytes, filename = render_analysis_to_png(analysis_id, result_data, tag=analysis.tag or "")
    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
