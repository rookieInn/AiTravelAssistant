"""
简化的初始化示例数据
"""

import json
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.attraction import Attraction, Hotel
from app.models.user import User
from app.core.security import get_password_hash

def init_database():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)

def create_sample_attractions():
    """创建示例景点数据"""
    db = SessionLocal()
    
    attractions_data = [
        {
            "name": "故宫博物院",
            "description": "明清两朝的皇家宫殿，世界文化遗产",
            "category": "人文景观",
            "city": "北京",
            "province": "北京",
            "latitude": 39.9163,
            "longitude": 116.3972,
            "address": "北京市东城区景山前街4号",
            "opening_hours": json.dumps({"周一": "闭馆", "周二至周日": "08:30-17:00"}),
            "ticket_price": 60.0,
            "ticket_info": "成人票60元，学生票30元",
            "rating": 4.8,
            "review_count": 12580,
            "tags": json.dumps(["历史文化", "皇家建筑", "世界遗产"]),
            "features": json.dumps(["语音导览", "免费WiFi", "停车场"])
        },
        {
            "name": "天安门广场",
            "description": "世界上最大的城市广场，中华人民共和国的象征",
            "category": "人文景观",
            "city": "北京",
            "province": "北京",
            "latitude": 39.9042,
            "longitude": 116.4074,
            "address": "北京市东城区东长安街",
            "opening_hours": json.dumps({"全天": "24小时开放"}),
            "ticket_price": 0.0,
            "ticket_info": "免费参观",
            "rating": 4.7,
            "review_count": 8920,
            "tags": json.dumps(["历史文化", "政治地标", "免费景点"]),
            "features": json.dumps(["升旗仪式", "安检", "禁止携带危险品"])
        },
        {
            "name": "外滩",
            "description": "上海最著名的观光景点，万国建筑博览群",
            "category": "人文景观",
            "city": "上海",
            "province": "上海",
            "latitude": 31.2397,
            "longitude": 121.4998,
            "address": "上海市黄浦区中山东一路",
            "opening_hours": json.dumps({"全天": "24小时开放"}),
            "ticket_price": 0.0,
            "ticket_info": "免费参观",
            "rating": 4.6,
            "review_count": 23450,
            "tags": json.dumps(["历史建筑", "夜景", "免费景点"]),
            "features": json.dumps(["黄浦江游船", "观景台", "餐厅"])
        }
    ]
    
    for attr_data in attractions_data:
        # 检查景点是否已存在
        existing = db.query(Attraction).filter(
            Attraction.name == attr_data["name"],
            Attraction.city == attr_data["city"]
        ).first()
        
        if not existing:
            attraction = Attraction(**attr_data)
            db.add(attraction)
    
    db.commit()
    print("✅ 示例景点数据创建完成")
    db.close()

def create_sample_hotels():
    """创建示例酒店数据"""
    db = SessionLocal()
    
    hotels_data = [
        {
            "name": "北京饭店",
            "description": "历史悠久的豪华酒店，位于王府井商业区",
            "city": "北京",
            "address": "北京市东城区东长安街33号",
            "latitude": 39.9042,
            "longitude": 116.4074,
            "price_per_night": 800.0,
            "rating": 4.5,
            "review_count": 2340,
            "amenities": json.dumps(["免费WiFi", "健身房", "游泳池", "商务中心", "停车场"]),
            "room_types": json.dumps([
                {"type": "标准间", "price": 800, "size": "25平米"},
                {"type": "豪华间", "price": 1200, "size": "35平米"},
                {"type": "套房", "price": 2000, "size": "60平米"}
            ])
        }
    ]
    
    for hotel_data in hotels_data:
        # 检查酒店是否已存在
        existing = db.query(Hotel).filter(
            Hotel.name == hotel_data["name"],
            Hotel.city == hotel_data["city"]
        ).first()
        
        if not existing:
            hotel = Hotel(**hotel_data)
            db.add(hotel)
    
    db.commit()
    print("✅ 示例酒店数据创建完成")
    db.close()

def create_sample_users():
    """创建示例用户数据"""
    db = SessionLocal()
    
    users_data = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",
            "is_admin": True,
            "travel_style": "商务出行",
            "interests": json.dumps(["历史文化", "商务"])
        },
        {
            "username": "testuser",
            "email": "test@example.com",
            "password": "test123",
            "is_admin": False,
            "travel_style": "家庭游",
            "interests": json.dumps(["自然风光", "美食", "购物"])
        }
    ]
    
    for user_data in users_data:
        # 检查用户是否已存在
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        
        if not existing:
            password = user_data.pop("password")
            user_data["hashed_password"] = get_password_hash(password)
            user = User(**user_data)
            db.add(user)
    
    db.commit()
    print("✅ 示例用户数据创建完成")
    db.close()

def main():
    """主函数"""
    print("🚀 开始初始化AI智能旅游路线规划系统数据...")
    
    # 初始化数据库
    init_database()
    print("✅ 数据库初始化完成")
    
    # 创建示例数据
    create_sample_attractions()
    create_sample_hotels()
    create_sample_users()
    
    print("🎉 数据初始化完成！")
    print("📝 默认管理员账户: admin / admin123")
    print("👤 测试用户账户: testuser / test123")

if __name__ == "__main__":
    main()