"""
管理员API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import check_admin_permission
from app.models.attraction import Attraction, Hotel
from app.models.route import Route, RouteFeedback
from app.models.user import User

router = APIRouter()

# 请求模型
class AttractionCreateRequest(BaseModel):
    """创建景点请求"""
    name: str
    description: str
    category: str
    city: str
    province: str
    country: str = "中国"
    latitude: float
    longitude: float
    address: str
    opening_hours: Optional[dict] = None
    ticket_price: Optional[float] = None
    ticket_info: Optional[str] = None
    tags: Optional[List[str]] = None
    features: Optional[List[str]] = None

class HotelCreateRequest(BaseModel):
    """创建酒店请求"""
    name: str
    description: str
    city: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_per_night: Optional[float] = None
    amenities: Optional[List[str]] = None
    room_types: Optional[List[dict]] = None

class AttractionUpdateRequest(BaseModel):
    """更新景点请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    opening_hours: Optional[dict] = None
    ticket_price: Optional[float] = None
    ticket_info: Optional[str] = None
    tags: Optional[List[str]] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_recommended: Optional[bool] = None

# 响应模型
class AdminStatsResponse(BaseModel):
    """管理员统计响应"""
    total_users: int
    total_routes: int
    total_attractions: int
    total_hotels: int
    active_routes: int
    completed_routes: int

@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user: str = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """获取管理员统计信息"""
    
    try:
        total_users = db.query(User).count()
        total_routes = db.query(Route).count()
        total_attractions = db.query(Attraction).count()
        total_hotels = db.query(Hotel).count()
        active_routes = db.query(Route).filter(Route.status == "active").count()
        completed_routes = db.query(Route).filter(Route.status == "completed").count()
        
        return AdminStatsResponse(
            total_users=total_users,
            total_routes=total_routes,
            total_attractions=total_attractions,
            total_hotels=total_hotels,
            active_routes=active_routes,
            completed_routes=completed_routes
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息时出错: {str(e)}"
        )

@router.post("/attractions")
async def create_attraction(
    request: AttractionCreateRequest,
    current_user: str = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """创建景点"""
    
    try:
        # 检查景点是否已存在
        existing_attraction = db.query(Attraction).filter(
            Attraction.name == request.name,
            Attraction.city == request.city
        ).first()
        
        if existing_attraction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="景点已存在"
            )
        
        # 创建新景点
        attraction = Attraction(
            name=request.name,
            description=request.description,
            category=request.category,
            city=request.city,
            province=request.province,
            country=request.country,
            latitude=request.latitude,
            longitude=request.longitude,
            address=request.address,
            opening_hours=request.opening_hours,
            ticket_price=request.ticket_price,
            ticket_info=request.ticket_info,
            tags=request.tags,
            features=request.features
        )
        
        db.add(attraction)
        db.commit()
        db.refresh(attraction)
        
        return {
            "success": True,
            "attraction_id": attraction.id,
            "message": "景点创建成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建景点时出错: {str(e)}"
        )

@router.put("/attractions/{attraction_id}")
async def update_attraction(
    attraction_id: int,
    request: AttractionUpdateRequest,
    current_user: str = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """更新景点"""
    
    try:
        attraction = db.query(Attraction).filter(Attraction.id == attraction_id).first()
        if not attraction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="景点不存在"
            )
        
        # 更新景点信息
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(attraction, field, value)
        
        db.commit()
        db.refresh(attraction)
        
        return {
            "success": True,
            "message": "景点更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新景点时出错: {str(e)}"
        )

@router.delete("/attractions/{attraction_id}")
async def delete_attraction(
    attraction_id: int,
    current_user: str = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """删除景点"""
    
    try:
        attraction = db.query(Attraction).filter(Attraction.id == attraction_id).first()
        if not attraction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="景点不存在"
            )
        
        # 软删除
        attraction.is_active = False
        db.commit()
        
        return {
            "success": True,
            "message": "景点已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除景点时出错: {str(e)}"
        )

@router.post("/hotels")
async def create_hotel(
    request: HotelCreateRequest,
    current_user: str = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """创建酒店"""
    
    try:
        # 检查酒店是否已存在
        existing_hotel = db.query(Hotel).filter(
            Hotel.name == request.name,
            Hotel.city == request.city
        ).first()
        
        if existing_hotel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="酒店已存在"
            )
        
        # 创建新酒店
        hotel = Hotel(
            name=request.name,
            description=request.description,
            city=request.city,
            address=request.address,
            latitude=request.latitude,
            longitude=request.longitude,
            price_per_night=request.price_per_night,
            amenities=request.amenities,
            room_types=request.room_types
        )
        
        db.add(hotel)
        db.commit()
        db.refresh(hotel)
        
        return {
            "success": True,
            "hotel_id": hotel.id,
            "message": "酒店创建成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建酒店时出错: {str(e)}"
        )

@router.get("/routes")
async def get_all_routes(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    current_user: str = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """获取所有路线"""
    
    try:
        # 构建查询
        query = db.query(Route)
        
        if status:
            query = query.filter(Route.status == status)
        
        # 分页
        total = query.count()
        routes = query.offset((page - 1) * size).limit(size).all()
        
        # 构建响应数据
        routes_data = []
        for route in routes:
            routes_data.append({
                "id": route.id,
                "title": route.title,
                "user_id": route.user_id,
                "start_date": route.start_date.isoformat(),
                "end_date": route.end_date.isoformat(),
                "duration_days": route.duration_days,
                "budget": route.budget,
                "status": route.status,
                "rating": route.user_rating,
                "created_at": route.created_at.isoformat()
            })
        
        return {
            "success": True,
            "routes": routes_data,
            "total": total,
            "page": page,
            "size": size
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取路线列表时出错: {str(e)}"
        )

@router.get("/feedback")
async def get_route_feedback(
    page: int = 1,
    size: int = 20,
    current_user: str = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """获取路线反馈"""
    
    try:
        # 分页查询
        total = db.query(RouteFeedback).count()
        feedbacks = db.query(RouteFeedback).offset((page - 1) * size).limit(size).all()
        
        # 构建响应数据
        feedbacks_data = []
        for feedback in feedbacks:
            feedbacks_data.append({
                "id": feedback.id,
                "route_id": feedback.route_id,
                "user_id": feedback.user_id,
                "rating": feedback.rating,
                "content": feedback.content,
                "suggestions": feedback.suggestions,
                "created_at": feedback.created_at.isoformat()
            })
        
        return {
            "success": True,
            "feedbacks": feedbacks_data,
            "total": total,
            "page": page,
            "size": size
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取反馈列表时出错: {str(e)}"
        )

@router.get("/users")
async def get_all_users(
    page: int = 1,
    size: int = 20,
    current_user: str = Depends(check_admin_permission),
    db: Session = Depends(get_db)
):
    """获取所有用户"""
    
    try:
        # 分页查询
        total = db.query(User).count()
        users = db.query(User).offset((page - 1) * size).limit(size).all()
        
        # 构建响应数据
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "travel_style": user.travel_style,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat()
            })
        
        return {
            "success": True,
            "users": users_data,
            "total": total,
            "page": page,
            "size": size
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表时出错: {str(e)}"
        )