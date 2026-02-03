"""
成本统计与预警
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple

from sqlalchemy.orm import Session

from config import settings
from database import ModelCallLog


def extract_usage(resp_json: Dict[str, Any]) -> Tuple[int, int, int]:
    """
    从火山方舟 Chat Completions 响应中提取 usage（如果有）
    """
    usage = resp_json.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
    return prompt_tokens, completion_tokens, total_tokens


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """
    简单按 1K tokens 单价估算成本（未配置则为0）
    """
    in_cost = (prompt_tokens / 1000.0) * float(settings.COST_INPUT_PER_1K_TOKENS or 0.0)
    out_cost = (completion_tokens / 1000.0) * float(settings.COST_OUTPUT_PER_1K_TOKENS or 0.0)
    return round(in_cost + out_cost, 6)


def log_call(
    db: Session,
    user_id: int,
    call_type: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    estimated_cost: float,
):
    db.add(
        ModelCallLog(
            user_id=user_id,
            call_type=call_type,
            model=model or "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
        )
    )
    db.commit()


def get_today_month_cost(db: Session, user_id: int) -> Tuple[float, float]:
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    today_cost = (
        db.query(ModelCallLog)
        .filter(ModelCallLog.user_id == user_id, ModelCallLog.created_at >= today_start)
        .with_entities(ModelCallLog.estimated_cost)
        .all()
    )
    month_cost = (
        db.query(ModelCallLog)
        .filter(ModelCallLog.user_id == user_id, ModelCallLog.created_at >= month_start)
        .with_entities(ModelCallLog.estimated_cost)
        .all()
    )

    return (
        float(sum(x[0] or 0.0 for x in today_cost)),
        float(sum(x[0] or 0.0 for x in month_cost)),
    )


def maybe_warn_cost(db: Session, user_id: int) -> Dict[str, Any]:
    """
    返回预警信息（如果启用阈值）
    """
    today, month = get_today_month_cost(db, user_id)
    warnings = []

    if settings.DAILY_COST_WARN_THRESHOLD and today >= float(settings.DAILY_COST_WARN_THRESHOLD):
        warnings.append(f"今日成本已达到预警阈值：{today:.4f} 元")
    if settings.MONTHLY_COST_WARN_THRESHOLD and month >= float(settings.MONTHLY_COST_WARN_THRESHOLD):
        warnings.append(f"本月成本已达到预警阈值：{month:.4f} 元")

    return {"today_cost": today, "month_cost": month, "warnings": warnings}

