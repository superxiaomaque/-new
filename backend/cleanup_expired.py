"""
清理到期数据（30天）：删除数据库记录 + 图片

建议部署后用 cron 每天跑一次，例如：
0 3 * * * cd /path/to/backend && /usr/bin/python3 cleanup_expired.py
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from database import SessionLocal, Analysis, ShareLink
from services.storage import StorageService


def main(days: int = 30):
    cutoff = datetime.utcnow() - timedelta(days=days)
    storage = StorageService()
    db: Session = SessionLocal()
    try:
        # 删除过期分享链接
        expired_shares = db.query(ShareLink).filter(ShareLink.expires_at < datetime.utcnow()).all()
        for s in expired_shares:
            db.delete(s)
        db.commit()

        # 删除过期分析记录（并删除图片）
        expired_analyses = db.query(Analysis).filter(Analysis.created_at < cutoff).all()
        for a in expired_analyses:
            try:
                if a.images:
                    storage.delete_images(a.images)
            except Exception:
                pass
            db.delete(a)
        db.commit()

        print(f"✅ 清理完成：删除分享 {len(expired_shares)} 条，删除分析 {len(expired_analyses)} 条（含图片）")
    finally:
        db.close()


if __name__ == "__main__":
    main()

