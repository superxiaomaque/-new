"""
认证路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta
from database import get_db, User
from auth import get_password_hash, verify_password, create_access_token
from config import settings

router = APIRouter(prefix="/auth", tags=["认证"])

class RegisterRequest(BaseModel):
    phone: str
    password: str

class LoginRequest(BaseModel):
    phone: str
    password: str

class TokenResponse(BaseModel):
    token: str
    user: dict

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="已关闭注册，请直接登录（首次登录会自动创建账号）"
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="已启用匿名模式，无需登录")

@router.get("/me")
async def get_me():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="已启用匿名模式，无需登录")

@router.post("/forgot-password")
async def forgot_password(request: dict, db: Session = Depends(get_db)):
    """忘记密码（简化版，实际应该发送验证码）"""
    phone = request.get("phone")
    new_password = request.get("new_password")
    
    if not phone or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="参数不完整"
        )
    if len(str(new_password)) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码长度至少6位")
    if len(str(new_password).encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码过长（请控制在 72 字节以内，建议不超过 24 个英文字符或 20 个左右中文字符）"
        )
    
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "密码重置成功"}

@router.post("/change-password")
async def change_password():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="已启用匿名模式，无需修改密码")
