"""
路线规划数据模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Route(Base):
    """路线规划模型"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 路线基本信息
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    duration_days = Column(Integer, default=1)
    budget = Column(Float)
    
    # 路线参数
    travel_style = Column(String(50))  # 家庭游、蜜月游、独自旅行等
    interests = Column(Text)  # 兴趣标签，JSON字符串
    constraints = Column(Text)  # 约束条件，JSON字符串
    
    # 路线状态
    status = Column(String(20), default="draft")  # draft, active, completed, cancelled
    is_public = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    # 评分和反馈
    user_rating = Column(Float)
    user_feedback = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    days = relationship("RouteDay", back_populates="route", cascade="all, delete-orphan")

class RouteDay(Base):
    """路线日程模型"""
    __tablename__ = "route_days"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    day_number = Column(Integer, nullable=False)  # 第几天
    date = Column(DateTime(timezone=True))
    
    # 日程信息
    title = Column(String(200))
    description = Column(Text)
    budget = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    route = relationship("Route", back_populates="days")
    activities = relationship("RouteActivity", back_populates="day", cascade="all, delete-orphan")

class RouteActivity(Base):
    """路线活动模型"""
    __tablename__ = "route_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("route_days.id"), nullable=False)
    attraction_id = Column(Integer, ForeignKey("attractions.id"))
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    
    # 活动信息
    activity_type = Column(String(50), nullable=False)  # attraction, hotel, transport, meal, rest
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 时间安排
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    
    # 位置信息
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String(500))
    
    # 费用和评分
    cost = Column(Float)
    rating = Column(Float)
    notes = Column(Text)
    
    # 排序
    order_index = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    day = relationship("RouteDay", back_populates="activities")
    attraction = relationship("Attraction")
    hotel = relationship("Hotel")

class RouteFeedback(Base):
    """路线反馈模型"""
    __tablename__ = "route_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 反馈内容
    rating = Column(Float, nullable=False)  # 1-5分
    content = Column(Text)
    suggestions = Column(Text)
    
    # 具体评价
    attraction_ratings = Column(Text)  # 各景点评分，JSON字符串
    transportation_ratings = Column(Text)  # 交通评分，JSON字符串
    accommodation_ratings = Column(Text)  # 住宿评分，JSON字符串
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    route = relationship("Route")
    user = relationship("User")