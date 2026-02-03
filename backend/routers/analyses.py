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
from database import get_db, User, Analysis
from anonymous import get_default_user
from services.doubao_api import DoubaoAPI
from services.storage import StorageService
from services.exporter import render_analysis_to_png, build_zip_of_pngs, PRESET_TAGS
from services.cost_monitor import extract_usage, estimate_cost, log_call, maybe_warn_cost
from config import settings

router = APIRouter(prefix="/analyses", tags=["分析"])

doubao_api = DoubaoAPI()
storage_service = StorageService()

@router.post("")
async def create_analysis(
    images: List[UploadFile] = File(...),
    supplementary_info: str = Form("{}"),
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db)
):
    """创建分析"""
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

        # 成本统计（如果响应中包含 usage）
        prompt_tokens, completion_tokens, total_tokens = extract_usage({"usage": usage})
        cost = estimate_cost(prompt_tokens, completion_tokens)
        try:
            log_call(
                db=db,
                user_id=current_user.id,
                call_type="analysis",
                model=settings.DOUBAO_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=cost,
            )
            warn = maybe_warn_cost(db, current_user.id)
        except Exception:
            warn = {"warnings": []}
        
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
            "created_at": new_analysis.created_at.isoformat(),
            "warnings": warn.get("warnings", []),
        }
        
    except Exception as e:
        # 如果分析失败，删除已上传的图片
        if 'image_urls' in locals():
            storage_service.delete_images(image_urls)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}"
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
        answer, usage = doubao_api.chat(
            analysis_id=analysis_id,
            question=question.get("question", ""),
            context=analysis.result
        )
        # 成本统计（如果响应中包含 usage）
        prompt_tokens, completion_tokens, total_tokens = extract_usage({"usage": usage})
        cost = estimate_cost(prompt_tokens, completion_tokens)
        try:
            log_call(
                db=db,
                user_id=current_user.id,
                call_type="chat",
                model=settings.DOUBAO_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=cost,
            )
            warn = maybe_warn_cost(db, current_user.id)
        except Exception:
            warn = {"warnings": []}
        
        return {
            "answer": answer,
            "warnings": warn.get("warnings", []),
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
    
    new_tag = (tag_data.get("tag") or "").strip()
    if new_tag and new_tag not in PRESET_TAGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的标签，可选：{', '.join(PRESET_TAGS)}"
        )
    analysis.tag = new_tag
    db.commit()
    
    return {"message": "标签更新成功"}


@router.get("/usage/summary")
async def get_usage_summary(
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db),
):
    """获取当日/当月成本与预警信息（如果启用）"""
    return maybe_warn_cost(db, current_user.id)


@router.get("/tags")
async def get_preset_tags():
    """获取系统预设标签"""
    return {"tags": PRESET_TAGS}


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


@router.post("/export.zip")
async def export_analyses_zip(
    payload: dict,
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db),
):
    """批量导出分析结果为ZIP（内含多张PNG）"""
    ids = payload.get("ids") or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ids不能为空")
    if len(ids) > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="单次最多导出50条")

    analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id,
        Analysis.id.in_(ids)
    ).order_by(Analysis.created_at.desc()).all()

    if not analyses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到可导出的记录")

    items: List[tuple] = []
    for a in analyses:
        try:
            result_data = json.loads(a.result)
        except Exception:
            result_data = {"raw_text": a.result, "summary": "结果解析错误"}
        items.append((a.id, result_data, a.tag or ""))

    zip_bytes, zip_name = build_zip_of_pngs(items)
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'}
    )
