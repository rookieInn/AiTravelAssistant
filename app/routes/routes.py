"""
路线规划API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.core.security import verify_token
from app.services.route_planner import RoutePlannerService
from app.models.route import Route, RouteDay, RouteActivity
from app.models.attraction import Attraction

router = APIRouter()

# 请求模型
class RoutePlanRequest(BaseModel):
    """路线规划请求"""
    destination: str = Field(..., description="目的地")
    start_date: str = Field(..., description="出发日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")
    travelers: int = Field(1, description="旅行人数")
    budget: Optional[float] = Field(None, description="预算")
    travel_style: Optional[str] = Field(None, description="旅行风格")
    interests: List[str] = Field(default=[], description="兴趣标签")
    special_requirements: Optional[str] = Field(None, description="特殊要求")

class RouteOptimizationRequest(BaseModel):
    """路线优化请求"""
    feedback: str = Field(..., description="用户反馈")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")

class AttractionRecommendationRequest(BaseModel):
    """景点推荐请求"""
    city: str = Field(..., description="城市")
    interests: List[str] = Field(default=[], description="兴趣标签")
    budget_range: Optional[List[float]] = Field(None, description="预算范围 [最小值, 最大值]")

# 响应模型
class RoutePlanResponse(BaseModel):
    """路线规划响应"""
    success: bool
    route_id: Optional[int] = None
    route_data: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None

class RouteListResponse(BaseModel):
    """路线列表响应"""
    routes: List[Dict[str, Any]]
    total: int
    page: int
    size: int

@router.post("/plan", response_model=RoutePlanResponse)
async def create_route_plan(
    request: RoutePlanRequest,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """创建路线规划"""
    
    try:
        # 获取用户ID（简化实现，实际应该从token中解析）
        user_id = 1  # 这里应该从current_user中获取实际用户ID
        
        # 转换请求数据
        user_input = {
            "destination": request.destination,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "travelers": request.travelers,
            "budget": request.budget,
            "travel_style": request.travel_style,
            "interests": request.interests,
            "special_requirements": request.special_requirements
        }
        
        # 创建路线规划服务
        planner = RoutePlannerService()
        
        # 生成路线规划
        result = await planner.create_route_plan(user_id, user_input, db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return RoutePlanResponse(
            success=True,
            route_id=result.get("route_id"),
            route_data=result.get("route_data"),
            message=result.get("message", "路线规划创建成功")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建路线规划时出错: {str(e)}"
        )

@router.post("/{route_id}/optimize", response_model=RoutePlanResponse)
async def optimize_route(
    route_id: int,
    request: RouteOptimizationRequest,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """优化路线"""
    
    try:
        # 检查路线是否存在
        route = db.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="路线不存在"
            )
        
        # 创建路线规划服务
        planner = RoutePlannerService()
        
        # 优化路线
        result = await planner.optimize_route(
            route_id,
            request.feedback,
            request.constraints,
            db
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return RoutePlanResponse(
            success=True,
            message=result.get("message", "路线优化完成")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"优化路线时出错: {str(e)}"
        )

@router.get("/{route_id}")
async def get_route(
    route_id: int,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """获取路线详情"""
    
    try:
        route = db.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="路线不存在"
            )
        
        # 构建路线数据
        days_data = []
        for day in route.days:
            activities = []
            for activity in day.activities:
                activities.append({
                    "id": activity.id,
                    "name": activity.name,
                    "description": activity.description,
                    "type": activity.activity_type,
                    "start_time": activity.start_time.isoformat() if activity.start_time else None,
                    "end_time": activity.end_time.isoformat() if activity.end_time else None,
                    "cost": activity.cost,
                    "order_index": activity.order_index
                })
            
            days_data.append({
                "id": day.id,
                "day_number": day.day_number,
                "title": day.title,
                "description": day.description,
                "budget": day.budget,
                "activities": activities
            })
        
        return {
            "id": route.id,
            "title": route.title,
            "description": route.description,
            "start_date": route.start_date.isoformat(),
            "end_date": route.end_date.isoformat(),
            "duration_days": route.duration_days,
            "budget": route.budget,
            "travel_style": route.travel_style,
            "interests": route.interests,
            "status": route.status,
            "rating": route.user_rating,
            "created_at": route.created_at.isoformat(),
            "days": days_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取路线详情时出错: {str(e)}"
        )

@router.get("/", response_model=RouteListResponse)
async def list_routes(
    page: int = 1,
    size: int = 10,
    status: Optional[str] = None,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """获取路线列表"""
    
    try:
        # 获取用户ID（简化实现）
        user_id = 1
        
        # 构建查询
        query = db.query(Route).filter(Route.user_id == user_id)
        
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
                "description": route.description,
                "start_date": route.start_date.isoformat(),
                "end_date": route.end_date.isoformat(),
                "duration_days": route.duration_days,
                "budget": route.budget,
                "status": route.status,
                "rating": route.user_rating,
                "created_at": route.created_at.isoformat()
            })
        
        return RouteListResponse(
            routes=routes_data,
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取路线列表时出错: {str(e)}"
        )

@router.post("/recommendations/attractions")
async def get_attraction_recommendations(
    request: AttractionRecommendationRequest,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """获取景点推荐"""
    
    try:
        planner = RoutePlannerService()
        
        budget_range = None
        if request.budget_range and len(request.budget_range) == 2:
            budget_range = (request.budget_range[0], request.budget_range[1])
        
        recommendations = await planner.get_attraction_recommendations(
            request.city,
            request.interests,
            budget_range,
            db
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "total": len(recommendations)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取景点推荐时出错: {str(e)}"
        )

@router.post("/{route_id}/favorite")
async def toggle_favorite(
    route_id: int,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """切换收藏状态"""
    
    try:
        route = db.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="路线不存在"
            )
        
        route.is_favorite = not route.is_favorite
        db.commit()
        
        return {
            "success": True,
            "is_favorite": route.is_favorite,
            "message": "收藏状态已更新"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新收藏状态时出错: {str(e)}"
        )

@router.delete("/{route_id}")
async def delete_route(
    route_id: int,
    current_user: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """删除路线"""
    
    try:
        route = db.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="路线不存在"
            )
        
        db.delete(route)
        db.commit()
        
        return {
            "success": True,
            "message": "路线已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除路线时出错: {str(e)}"
        )