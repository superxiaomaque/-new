"""
测试模式匿名用户依赖
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from test_database import get_db, User

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

