"""
匿名模式：提供默认用户依赖（用于本地试用/无需登录）
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db, User


DEFAULT_ANON_PHONE = "00000000000"


def get_default_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.phone == DEFAULT_ANON_PHONE).first()
    if user:
        return user
    user = User(phone=DEFAULT_ANON_PHONE, password_hash="anonymous")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

