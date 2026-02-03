"""
导出服务：将分析结果导出为图片（PNG），以及批量导出Zip
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont


SYSTEM_FONT_CANDIDATES = [
    # macOS 常见中文字体
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    # Windows 常见中文字体（如果未来迁移）
    "C:\\Windows\\Fonts\\msyh.ttc",
    "C:\\Windows\\Fonts\\simhei.ttf",
    # Linux 常见中文字体（如果未来部署）
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


PRESET_TAGS = ["重要", "已联系", "待跟进"]


def _load_font(size: int = 28) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in SYSTEM_FONT_CANDIDATES:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    # fallback
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    lines: List[str] = []
    for raw_line in (text or "").splitlines() or [""]:
        line = raw_line
        while line:
            # 逐步缩短，直到能放下
            lo, hi = 1, len(line)
            best = 1
            while lo <= hi:
                mid = (lo + hi) // 2
                w = draw.textlength(line[:mid], font=font)
                if w <= max_width:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            lines.append(line[:best])
            line = line[best:]
        if raw_line == "":
            lines.append("")
    return lines


def _draw_gradient_background(img: Image.Image, width: int, height: int):
    """绘制渐变背景"""
    draw = ImageDraw.Draw(img)
    # 从粉色到浅灰的渐变
    for y in range(height):
        ratio = y / height
        # 粉色 #ff9a9e -> 浅灰 #f5f5f5
        r = int(255 * (1 - ratio * 0.4))
        g = int(154 * (1 - ratio * 0.4) + 245 * ratio * 0.4)
        b = int(158 * (1 - ratio * 0.4) + 245 * ratio * 0.4)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def _draw_rounded_rectangle_simple(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, radius: int, fill: tuple):
    """绘制圆角矩形（简化版）"""
    # 绘制主体矩形
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    # 绘制四个圆角
    draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=fill)
    draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=fill)
    draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=fill)
    draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=fill)


def _draw_card_with_shadow(img: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int, radius: int = 20):
    """绘制带阴影的卡片（简化版，避免RGBA问题）"""
    # 绘制简单的阴影（深灰色矩形）
    shadow_offset = 4
    shadow_color = (200, 200, 200)
    _draw_rounded_rectangle_simple(draw, x + shadow_offset, y + shadow_offset, x + width + shadow_offset, y + height + shadow_offset, radius, shadow_color)
    
    # 绘制白色卡片
    _draw_rounded_rectangle_simple(draw, x, y, x + width, y + height, radius, (255, 255, 255))


def render_analysis_to_png(
    analysis_id: int,
    result: Dict[str, Any],
    tag: str = "",
    width: int = 1080,
) -> Tuple[bytes, str]:
    """
    将分析结果渲染为PNG，返回 (png_bytes, filename)
    样式与前端界面保持一致
    """
    # 字体设置
    title_font = _load_font(48)  # 标题字体
    score_font = _load_font(72)  # 评分大字体
    score_unit_font = _load_font(32)  # 评分单位字体
    heading_font = _load_font(32)  # 章节标题字体
    body_font = _load_font(28)  # 正文字体
    small_font = _load_font(24)  # 小字体

    padding = 40
    card_padding = 32
    card_spacing = 24
    content_width = width - padding * 2
    card_content_width = content_width - card_padding * 2

    # 准备数据
    match_score = result.get("match_score", 0)
    success_rate = result.get("success_rate", 0)

    def get_str(key: str) -> str:
        v = result.get(key, "")
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False, indent=2)
        return str(v or "暂无数据")

    comm = result.get("communication") or {}
    topics = comm.get("topics") or []
    opening_lines = comm.get("opening_lines") or []
    tips = comm.get("tips") or ""

    # 分析项配置（与前端一致）
    analysis_items = [
        ("性格分析", get_str("personality")),
        ("兴趣爱好", get_str("interests")),
        ("价值观倾向", get_str("values")),
        ("情感状态", get_str("emotion")),
        ("收入与消费能力", get_str("income_analysis")),
        ("沟通建议", _format_communication(topics, opening_lines, tips)),
        ("关系推进建议", get_str("relationship")),
        ("避雷指南", get_str("warnings")),
    ]

    # 计算高度
    dummy = Image.new("RGB", (width, 200), (255, 255, 255))
    dummy_draw = ImageDraw.Draw(dummy)
    
    y = padding
    y += 80  # 标题
    y += card_spacing
    y += 120  # 评分卡片
    y += card_spacing
    
    # 分析卡片
    for heading, body in analysis_items:
        y += 20  # 卡片间距
        y += 60  # 卡片标题
        wrapped = _wrap_text(dummy_draw, body, body_font, card_content_width)
        y += len(wrapped) * 36 + card_padding * 2 + 20
    
    height = max(2000, y + padding + 100)

    # 创建图片
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 绘制渐变背景
    _draw_gradient_background(img, width, height)

    y = padding

    # 标题区域
    title_text = "朋友圈分析助手"
    subtitle_text = "通过AI分析，助您找到心仪的另一半"
    title_width = dummy_draw.textlength(title_text, font=title_font)
    title_x = (width - title_width) // 2
    
    draw.text((title_x, y), title_text, fill=(255, 255, 255), font=title_font)
    y += 60
    
    subtitle_width = dummy_draw.textlength(subtitle_text, font=small_font)
    subtitle_x = (width - subtitle_width) // 2
    draw.text((subtitle_x, y), subtitle_text, fill=(240, 240, 240), font=small_font)
    y += padding + card_spacing

    # 评分卡片（渐变背景，与前端一致）
    score_card_height = 140
    score_card_y = y
    
    # 绘制评分卡片背景（渐变粉色）
    for i in range(score_card_height):
        ratio = i / score_card_height
        r = int(255 * (1 - ratio * 0.2) + 254 * ratio * 0.2)
        g = int(154 * (1 - ratio * 0.2) + 207 * ratio * 0.2)
        b = int(158 * (1 - ratio * 0.2) + 239 * ratio * 0.2)
        draw.line([(padding, score_card_y + i), (padding + content_width, score_card_y + i)], fill=(r, g, b))
    
    # 绘制圆角遮罩（用白色圆角矩形覆盖边缘）
    _draw_rounded_rectangle_simple(draw, padding, score_card_y, padding + content_width, score_card_y + score_card_height, 20, (255, 154, 158))
    
    # 绘制评分内容
    score_inner_y = score_card_y + score_card_height // 2
    score_left_x = padding + content_width // 4
    score_right_x = padding + content_width * 3 // 4
    
    # 左侧：匹配度
    match_text = str(match_score)
    match_width = dummy_draw.textlength(match_text, font=score_font)
    draw.text((score_left_x - match_width // 2, score_inner_y - 50), match_text, fill=(255, 255, 255), font=score_font)
    draw.text((score_left_x + match_width // 2 + 8, score_inner_y - 40), "分", fill=(250, 250, 250), font=score_unit_font)
    draw.text((score_left_x - 40, score_inner_y + 20), "匹配度", fill=(250, 250, 250), font=small_font)
    
    # 中间分隔线
    divider_x = padding + content_width // 2
    draw.line([(divider_x, score_card_y + 20), (divider_x, score_card_y + score_card_height - 20)], fill=(240, 240, 240), width=2)
    
    # 右侧：成功率
    rate_text = str(success_rate)
    rate_width = dummy_draw.textlength(rate_text, font=score_font)
    draw.text((score_right_x - rate_width // 2, score_inner_y - 50), rate_text, fill=(255, 255, 255), font=score_font)
    draw.text((score_right_x + rate_width // 2 + 8, score_inner_y - 40), "%", fill=(250, 250, 250), font=score_unit_font)
    draw.text((score_right_x - 60, score_inner_y + 20), "脱单成功率", fill=(250, 250, 250), font=small_font)
    
    y += score_card_height + card_spacing

    # 分析结果卡片
    for heading, body in analysis_items:
        # 计算卡片高度
        wrapped = _wrap_text(draw, body, body_font, card_content_width)
        card_height = 60 + len(wrapped) * 36 + card_padding * 2
        
        # 绘制卡片（带阴影）
        _draw_card_with_shadow(img, draw, padding, y, content_width, card_height, radius=16)
        
        # 卡片标题
        card_title_x = padding + card_padding
        card_title_y = y + card_padding
        draw.text((card_title_x, card_title_y), heading, fill=(51, 51, 51), font=heading_font)
        
        # 卡片内容
        content_y = card_title_y + 50
        for line in wrapped:
            if line.strip():
                draw.text((card_title_x, content_y), line, fill=(102, 102, 102), font=body_font)
            content_y += 36
        
        y += card_height + card_spacing

    # 保存
    out = io.BytesIO()
    img.save(out, format="PNG", quality=95)
    filename = f"analysis_{analysis_id}.png"
    return out.getvalue(), filename


def _format_communication(topics: List[str], opening_lines: List[str], tips: str) -> str:
    """格式化沟通建议"""
    parts = []
    if topics:
        parts.append("推荐话题：\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(topics)]))
    if opening_lines:
        parts.append("\n开场白建议：\n" + "\n".join([f"{i+1}. {l}" for i, l in enumerate(opening_lines)]))
    if tips:
        parts.append(f"\n聊天技巧：\n{tips}")
    return "\n".join(parts) if parts else "暂无数据"


def build_zip_of_pngs(items: List[Tuple[int, Dict[str, Any], str]]) -> Tuple[bytes, str]:
    """
    items: [(analysis_id, result_dict, tag)]
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for analysis_id, result, tag in items:
            png_bytes, filename = render_analysis_to_png(analysis_id, result, tag=tag)
            zf.writestr(filename, png_bytes)
    return buf.getvalue(), "analyses_export.zip"
