"""
路线规划核心服务
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from geopy.distance import geodesic
import redis
from app.core.config import settings
from app.core.database import get_db
from app.models.attraction import Attraction, Transportation, Hotel
from app.models.route import Route, RouteDay, RouteActivity
from app.models.user import User
from app.services.llm_service import LLMService

class RoutePlannerService:
    """路线规划服务"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    
    async def create_route_plan(
        self,
        user_id: int,
        user_input: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """创建路线规划"""
        
        # 验证输入参数
        validation_result = self._validate_user_input(user_input)
        if not validation_result["valid"]:
            return validation_result
        
        # 获取用户上下文
        context = await self._get_user_context(user_id, db)
        
        # 检查缓存
        cache_key = self._generate_cache_key(user_input)
        cached_result = await self._get_cached_route(cache_key)
        if cached_result:
            return cached_result
        
        # 使用LLM生成路线规划
        llm_result = await self.llm_service.generate_route_plan(user_input, context)
        
        if "error" in llm_result:
            return llm_result
        
        # 处理LLM结果
        if llm_result.get("type") == "text":
            # 文本格式，需要进一步处理
            return await self._process_text_route(llm_result, user_input, db)
        else:
            # JSON格式，直接处理
            return await self._process_json_route(llm_result, user_id, user_input, db)
    
    async def optimize_route(
        self,
        route_id: int,
        feedback: str,
        constraints: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """优化路线"""
        
        # 获取当前路线
        route = db.query(Route).filter(Route.id == route_id).first()
        if not route:
            return {"error": "路线不存在"}
        
        # 构建路线数据
        route_data = self._build_route_data(route, db)
        
        # 使用LLM优化路线
        optimization_result = await self.llm_service.optimize_route(
            route_data, feedback, constraints
        )
        
        if "error" in optimization_result:
            return optimization_result
        
        # 更新路线
        await self._update_route_from_optimization(route, optimization_result, db)
        
        return {
            "success": True,
            "message": "路线优化完成",
            "optimization": optimization_result
        }
    
    async def get_attraction_recommendations(
        self,
        city: str,
        interests: List[str],
        budget_range: Optional[Tuple[float, float]] = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """获取景点推荐"""
        
        query = db.query(Attraction).filter(
            Attraction.city == city,
            Attraction.is_active == True
        )
        
        # 根据兴趣标签过滤
        if interests:
            # 使用LIKE查询匹配JSON字符串中的标签
            for interest in interests:
                query = query.filter(Attraction.tags.like(f'%{interest}%'))
        
        # 根据预算过滤
        if budget_range:
            min_budget, max_budget = budget_range
            query = query.filter(
                Attraction.ticket_price >= min_budget,
                Attraction.ticket_price <= max_budget
            )
        
        attractions = query.order_by(Attraction.rating.desc()).limit(20).all()
        
        return [
            {
                "id": attr.id,
                "name": attr.name,
                "description": attr.description,
                "category": attr.category,
                "rating": attr.rating,
                "ticket_price": attr.ticket_price,
                "latitude": attr.latitude,
                "longitude": attr.longitude,
                "tags": attr.tags or []
            }
            for attr in attractions
        ]
    
    async def calculate_route_distance(
        self,
        attractions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算路线距离和时间"""
        
        if len(attractions) < 2:
            return {"total_distance": 0, "total_time": 0, "segments": []}
        
        total_distance = 0
        total_time = 0
        segments = []
        
        for i in range(len(attractions) - 1):
            current = attractions[i]
            next_attr = attractions[i + 1]
            
            # 计算距离
            distance = geodesic(
                (current["latitude"], current["longitude"]),
                (next_attr["latitude"], next_attr["longitude"])
            ).kilometers
            
            # 估算时间（假设平均速度30km/h）
            time_minutes = int(distance / 30 * 60)
            
            total_distance += distance
            total_time += time_minutes
            
            segments.append({
                "from": current["name"],
                "to": next_attr["name"],
                "distance_km": round(distance, 2),
                "time_minutes": time_minutes
            })
        
        return {
            "total_distance": round(total_distance, 2),
            "total_time": total_time,
            "segments": segments
        }
    
    def _validate_user_input(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """验证用户输入"""
        
        required_fields = ["destination", "start_date", "end_date"]
        missing_fields = [field for field in required_fields if not user_input.get(field)]
        
        if missing_fields:
            return {
                "valid": False,
                "error": f"缺少必要字段: {', '.join(missing_fields)}"
            }
        
        # 验证日期格式
        try:
            start_date = datetime.fromisoformat(user_input["start_date"])
            end_date = datetime.fromisoformat(user_input["end_date"])
            
            if start_date >= end_date:
                return {
                    "valid": False,
                    "error": "出发时间必须早于结束时间"
                }
            
            # 检查旅行天数是否合理
            days = (end_date - start_date).days
            if days > 30:
                return {
                    "valid": False,
                    "error": "旅行天数不能超过30天"
                }
            
        except ValueError:
            return {
                "valid": False,
                "error": "日期格式不正确，请使用YYYY-MM-DD格式"
            }
        
        return {"valid": True}
    
    async def _get_user_context(self, user_id: int, db: Session) -> Dict[str, Any]:
        """获取用户上下文"""
        
        # 获取用户历史路线
        recent_routes = db.query(Route).filter(
            Route.user_id == user_id,
            Route.status == "completed"
        ).order_by(Route.created_at.desc()).limit(5).all()
        
        # 获取用户偏好
        user = db.query(User).filter(User.id == user_id).first()
        preferences = {
            "travel_style": user.travel_style if user else None,
            "interests": json.loads(user.interests) if user and user.interests else [],
            "budget_range": user.budget_range if user else None
        }
        
        return {
            "preferences": preferences,
            "history": [self._build_route_summary(route) for route in recent_routes],
            "feedback": []  # 这里应该从反馈表中获取
        }
    
    def _build_route_summary(self, route: Route) -> Dict[str, Any]:
        """构建路线摘要"""
        return {
            "id": route.id,
            "title": route.title,
            "destination": route.description,
            "duration_days": route.duration_days,
            "budget": route.budget,
            "rating": route.user_rating,
            "created_at": route.created_at.isoformat()
        }
    
    def _generate_cache_key(self, user_input: Dict[str, Any]) -> str:
        """生成缓存键"""
        key_data = {
            "destination": user_input.get("destination"),
            "start_date": user_input.get("start_date"),
            "end_date": user_input.get("end_date"),
            "travelers": user_input.get("travelers"),
            "interests": sorted(user_input.get("interests", []))
        }
        return f"route_plan:{hash(json.dumps(key_data, sort_keys=True))}"
    
    async def _get_cached_route(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的路线"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            pass
        return None
    
    async def _cache_route(self, cache_key: str, route_data: Dict[str, Any]) -> None:
        """缓存路线数据"""
        try:
            self.redis_client.setex(
                cache_key,
                settings.cache_ttl,
                json.dumps(route_data, ensure_ascii=False)
            )
        except Exception:
            pass
    
    async def _process_text_route(
        self,
        llm_result: Dict[str, Any],
        user_input: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """处理文本格式的路线结果"""
        
        # 这里可以添加文本解析逻辑，将文本转换为结构化数据
        # 简化实现，直接返回文本结果
        return {
            "type": "text",
            "content": llm_result["content"],
            "suggestions": llm_result.get("suggestions", []),
            "raw_input": user_input
        }
    
    async def _process_json_route(
        self,
        llm_result: Dict[str, Any],
        user_id: int,
        user_input: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """处理JSON格式的路线结果"""
        
        # 创建路线记录
        route = Route(
            user_id=user_id,
            title=llm_result.get("title", "智能路线规划"),
            description=llm_result.get("description", ""),
            start_date=datetime.fromisoformat(user_input["start_date"]),
            end_date=datetime.fromisoformat(user_input["end_date"]),
            duration_days=(datetime.fromisoformat(user_input["end_date"]) - 
                          datetime.fromisoformat(user_input["start_date"])).days,
            budget=user_input.get("budget"),
            travel_style=user_input.get("travel_style"),
            interests=user_input.get("interests", []),
            status="draft"
        )
        
        db.add(route)
        db.commit()
        db.refresh(route)
        
        # 创建日程安排
        days_data = llm_result.get("days", [])
        for i, day_data in enumerate(days_data):
            route_day = RouteDay(
                route_id=route.id,
                day_number=i + 1,
                date=route.start_date + timedelta(days=i),
                title=day_data.get("title", f"第{i+1}天"),
                description=day_data.get("description", ""),
                budget=day_data.get("budget")
            )
            
            db.add(route_day)
            db.commit()
            db.refresh(route_day)
            
            # 创建活动安排
            activities = day_data.get("activities", [])
            for j, activity_data in enumerate(activities):
                activity = RouteActivity(
                    day_id=route_day.id,
                    activity_type=activity_data.get("type", "attraction"),
                    name=activity_data.get("name", ""),
                    description=activity_data.get("description", ""),
                    start_time=datetime.fromisoformat(activity_data["start_time"]) if activity_data.get("start_time") else None,
                    end_time=datetime.fromisoformat(activity_data["end_time"]) if activity_data.get("end_time") else None,
                    cost=activity_data.get("cost"),
                    order_index=j
                )
                
                db.add(activity)
        
        db.commit()
        
        # 缓存结果
        cache_key = self._generate_cache_key(user_input)
        await self._cache_route(cache_key, llm_result)
        
        return {
            "success": True,
            "route_id": route.id,
            "route_data": llm_result,
            "message": "路线规划创建成功"
        }
    
    def _build_route_data(self, route: Route, db: Session) -> Dict[str, Any]:
        """构建路线数据"""
        
        days_data = []
        for day in route.days:
            activities = []
            for activity in day.activities:
                activities.append({
                    "name": activity.name,
                    "description": activity.description,
                    "type": activity.activity_type,
                    "start_time": activity.start_time.isoformat() if activity.start_time else None,
                    "end_time": activity.end_time.isoformat() if activity.end_time else None,
                    "cost": activity.cost
                })
            
            days_data.append({
                "day_number": day.day_number,
                "title": day.title,
                "description": day.description,
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
            "days": days_data
        }
    
    async def _update_route_from_optimization(
        self,
        route: Route,
        optimization_result: Dict[str, Any],
        db: Session
    ) -> None:
        """根据优化结果更新路线"""
        
        # 这里应该实现具体的路线更新逻辑
        # 简化实现，只更新描述
        if "content" in optimization_result:
            route.description = optimization_result["content"]
            db.commit()