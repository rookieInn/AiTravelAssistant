"""
旅游景点数据模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Attraction(Base):
    """旅游景点模型"""
    __tablename__ = "attractions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), index=True)  # 自然景观、人文景观、主题公园等
    city = Column(String(100), index=True)
    province = Column(String(50), index=True)
    country = Column(String(50), default="中国")
    
    # 地理位置
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500))
    
    # 营业信息
    opening_hours = Column(Text)  # 营业时间，JSON格式
    ticket_price = Column(Float)  # 门票价格
    ticket_info = Column(Text)  # 门票信息
    
    # 评分和评价
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    
    # 标签和特色
    tags = Column(Text)  # 标签列表，JSON字符串
    features = Column(Text)  # 特色功能，JSON字符串
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    is_recommended = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Transportation(Base):
    """交通信息模型"""
    __tablename__ = "transportation"
    
    id = Column(Integer, primary_key=True, index=True)
    from_attraction_id = Column(Integer, nullable=False)
    to_attraction_id = Column(Integer, nullable=False)
    transport_type = Column(String(50), nullable=False)  # 步行、公交、地铁、出租车、自驾
    duration_minutes = Column(Integer, nullable=False)
    distance_km = Column(Float)
    cost = Column(Float)  # 费用
    route_info = Column(Text)  # 路线详情
    is_active = Column(Boolean, default=True)

class Hotel(Base):
    """酒店信息模型"""
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    city = Column(String(100), index=True)
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # 价格和评分
    price_per_night = Column(Float)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    
    # 设施和服务
    amenities = Column(Text)  # 设施列表，JSON字符串
    room_types = Column(Text)  # 房型信息，JSON字符串
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())