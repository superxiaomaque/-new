"""
认证路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta
from test_database import get_db, User
from test_auth import get_password_hash, verify_password, create_access_token
from test_anonymous import get_default_user
from test_config import settings

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
    """用户登录（若用户不存在则自动创建）"""
    if len((request.password or "").encode("utf-8")) > 72:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码过长（请控制在72字节以内）")
    user = db.query(User).filter(User.phone == request.phone).first()

    # 不存在则自动创建
    if not user:
        if not request.phone or len(request.phone) < 11:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手机号格式不正确")
        if len(request.password) < 6:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码长度至少6位")
        user = User(phone=request.phone, password_hash=get_password_hash(request.password))
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    # 生成token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "token": access_token,
        "user": {
            "id": user.id,
            "phone": user.phone
        }
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_default_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "phone": current_user.phone
    }

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
async def change_password(
    request: dict,
    current_user: User = Depends(get_default_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    old_password = request.get("old_password")
    new_password = request.get("new_password")
    
    if not old_password or not new_password:
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
    
    # 验证旧密码
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "密码修改成功"}
