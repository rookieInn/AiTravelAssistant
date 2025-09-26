"""
初始化示例数据
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
            "opening_hours": {"全天": "24小时开放"},
            "ticket_price": 0.0,
            "ticket_info": "免费参观",
            "rating": 4.7,
            "review_count": 8920,
            "tags": ["历史文化", "政治地标", "免费景点"],
            "features": ["升旗仪式", "安检", "禁止携带危险品"]
        },
        {
            "name": "长城（八达岭）",
            "description": "万里长城最著名的一段，世界文化遗产",
            "category": "人文景观",
            "city": "北京",
            "province": "北京",
            "latitude": 40.3584,
            "longitude": 116.0144,
            "address": "北京市延庆区八达岭镇",
            "opening_hours": {"夏季": "06:30-19:00", "冬季": "07:00-18:00"},
            "ticket_price": 40.0,
            "ticket_info": "成人票40元，缆车往返100元",
            "rating": 4.6,
            "review_count": 15620,
            "tags": ["历史文化", "世界遗产", "登山"],
            "features": ["缆车", "索道", "停车场", "餐厅"]
        },
        {
            "name": "颐和园",
            "description": "中国古典园林之首，皇家园林博物馆",
            "category": "人文景观",
            "city": "北京",
            "province": "北京",
            "latitude": 39.9999,
            "longitude": 116.2755,
            "address": "北京市海淀区新建宫门路19号",
            "opening_hours": {"夏季": "06:30-18:00", "冬季": "07:00-17:00"},
            "ticket_price": 30.0,
            "ticket_info": "成人票30元，联票60元",
            "rating": 4.5,
            "review_count": 9870,
            "tags": ["古典园林", "皇家建筑", "湖泊"],
            "features": ["游船", "导游服务", "停车场"]
        },
        {
            "name": "天坛公园",
            "description": "明清皇帝祭天的场所，世界文化遗产",
            "category": "人文景观",
            "city": "北京",
            "province": "北京",
            "latitude": 39.8823,
            "longitude": 116.4066,
            "address": "北京市东城区天坛路甲1号",
            "opening_hours": {"夏季": "06:00-22:00", "冬季": "06:30-21:30"},
            "ticket_price": 15.0,
            "ticket_info": "成人票15元，联票35元",
            "rating": 4.4,
            "review_count": 6540,
            "tags": ["历史文化", "世界遗产", "古建筑"],
            "features": ["晨练", "免费WiFi", "停车场"]
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
            "opening_hours": {"全天": "24小时开放"},
            "ticket_price": 0.0,
            "ticket_info": "免费参观",
            "rating": 4.6,
            "review_count": 23450,
            "tags": ["历史建筑", "夜景", "免费景点"],
            "features": ["黄浦江游船", "观景台", "餐厅"]
        },
        {
            "name": "东方明珠",
            "description": "上海标志性建筑，亚洲第四高塔",
            "category": "现代建筑",
            "city": "上海",
            "province": "上海",
            "latitude": 31.2397,
            "longitude": 121.4998,
            "address": "上海市浦东新区世纪大道1号",
            "opening_hours": {"全天": "08:00-21:30"},
            "ticket_price": 160.0,
            "ticket_info": "成人票160元，儿童票80元",
            "rating": 4.3,
            "review_count": 18760,
            "tags": ["现代建筑", "观景台", "夜景"],
            "features": ["旋转餐厅", "玻璃栈道", "纪念品商店"]
        },
        {
            "name": "西湖",
            "description": "中国著名的风景名胜区，世界文化遗产",
            "category": "自然景观",
            "city": "杭州",
            "province": "浙江",
            "latitude": 30.2741,
            "longitude": 120.1551,
            "address": "浙江省杭州市西湖区龙井路1号",
            "opening_hours": {"全天": "24小时开放"},
            "ticket_price": 0.0,
            "ticket_info": "免费参观，部分景点收费",
            "rating": 4.7,
            "review_count": 45680,
            "tags": ["自然风光", "湖泊", "免费景点"],
            "features": ["游船", "自行车租赁", "步行道"]
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
            "amenities": ["免费WiFi", "健身房", "游泳池", "商务中心", "停车场"],
            "room_types": [
                {"type": "标准间", "price": 800, "size": "25平米"},
                {"type": "豪华间", "price": 1200, "size": "35平米"},
                {"type": "套房", "price": 2000, "size": "60平米"}
            ]
        },
        {
            "name": "上海和平饭店",
            "description": "外滩标志性建筑，豪华历史酒店",
            "city": "上海",
            "address": "上海市黄浦区南京东路20号",
            "latitude": 31.2397,
            "longitude": 121.4998,
            "price_per_night": 1200.0,
            "rating": 4.7,
            "review_count": 1890,
            "amenities": ["免费WiFi", "健身房", "水疗中心", "商务中心", "代客泊车"],
            "room_types": [
                {"type": "江景房", "price": 1200, "size": "30平米"},
                {"type": "豪华江景房", "price": 1800, "size": "45平米"},
                {"type": "总统套房", "price": 5000, "size": "120平米"}
            ]
        },
        {
            "name": "杭州西湖国宾馆",
            "description": "西湖边的豪华度假酒店",
            "city": "杭州",
            "address": "浙江省杭州市西湖区杨公堤18号",
            "latitude": 30.2741,
            "longitude": 120.1551,
            "price_per_night": 600.0,
            "rating": 4.4,
            "review_count": 1560,
            "amenities": ["免费WiFi", "健身房", "游泳池", "花园", "停车场"],
            "room_types": [
                {"type": "湖景房", "price": 600, "size": "28平米"},
                {"type": "豪华湖景房", "price": 900, "size": "40平米"},
                {"type": "别墅", "price": 2000, "size": "80平米"}
            ]
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
            "interests": ["历史文化", "商务"]
        },
        {
            "username": "testuser",
            "email": "test@example.com",
            "password": "test123",
            "is_admin": False,
            "travel_style": "家庭游",
            "interests": ["自然风光", "美食", "购物"]
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