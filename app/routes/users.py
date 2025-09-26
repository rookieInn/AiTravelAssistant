"""
用户管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token
from app.models.user import User, UserSession
from app.core.config import settings

router = APIRouter()

# 请求模型
class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str
    email: EmailStr
    password: str
    travel_style: Optional[str] = None
    interests: Optional[list] = None

class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str
    password: str

class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    email: Optional[EmailStr] = None
    travel_style: Optional[str] = None
    interests: Optional[list] = None
    budget_range: Optional[str] = None

class UserSessionRequest(BaseModel):
    """用户会话请求"""
    context_data: Optional[dict] = None

# 响应模型
class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    travel_style: Optional[str]
    interests: Optional[list]
    budget_range: Optional[str]
    is_active: bool
    created_at: datetime

class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str
    user: UserResponse

@router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = db.query(User).filter(User.email == request.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 创建新用户
        hashed_password = get_password_hash(request.password)
        user = User(
            username=request.username,
            email=request.email,
            hashed_password=hashed_password,
            travel_style=request.travel_style,
            interests=request.interests
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            travel_style=user.travel_style,
            interests=user.interests,
            budget_range=user.budget_range,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册用户时出错: {str(e)}"
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    
    try:
        # 验证用户凭据
        user = db.query(User).filter(User.username == request.username).first()
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用"
            )
        
        # 创建访问令牌
        access_token = create_access_token(data={"sub": user.username})
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                travel_style=user.travel_style,
                interests=user.interests,
                budget_range=user.budget_range,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户登录时出错: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    
    try:
        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            travel_style=user.travel_style,
            interests=user.interests,
            budget_range=user.budget_range,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息时出错: {str(e)}"
        )

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: UserUpdateRequest,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    
    try:
        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新用户信息
        if request.email is not None:
            # 检查邮箱是否已被其他用户使用
            existing_email = db.query(User).filter(
                User.email == request.email,
                User.id != user.id
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被其他用户使用"
                )
            user.email = request.email
        
        if request.travel_style is not None:
            user.travel_style = request.travel_style
        
        if request.interests is not None:
            user.interests = request.interests
        
        if request.budget_range is not None:
            user.budget_range = request.budget_range
        
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            travel_style=user.travel_style,
            interests=user.interests,
            budget_range=user.budget_range,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息时出错: {str(e)}"
        )

@router.post("/sessions")
async def create_user_session(
    request: UserSessionRequest,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """创建用户会话"""
    
    try:
        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 创建新会话
        import uuid
        session_id = str(uuid.uuid4())
        
        session = UserSession(
            user_id=user.id,
            session_id=session_id,
            context_data=request.context_data
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "会话创建成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户会话时出错: {str(e)}"
        )

@router.get("/sessions")
async def get_user_sessions(
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """获取用户会话列表"""
    
    try:
        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).order_by(UserSession.last_activity.desc()).all()
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                "id": session.id,
                "session_id": session.session_id,
                "context_data": session.context_data,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat()
            })
        
        return {
            "success": True,
            "sessions": sessions_data,
            "total": len(sessions_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户会话时出错: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_user_session(
    session_id: str,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """删除用户会话"""
    
    try:
        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        session.is_active = False
        db.commit()
        
        return {
            "success": True,
            "message": "会话已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户会话时出错: {str(e)}"
        )