"""
系统功能测试脚本
"""

import asyncio
import json
from app.core.database import SessionLocal
from app.services.route_planner import RoutePlannerService
from app.services.llm_service import LLMService

async def test_llm_service():
    """测试LLM服务"""
    print("🧪 测试LLM服务...")
    
    llm_service = LLMService()
    
    # 测试路线规划
    user_input = {
        "destination": "北京",
        "start_date": "2024-01-01",
        "end_date": "2024-01-03",
        "travelers": 2,
        "budget": 5000,
        "interests": ["历史文化", "美食"],
        "special_requirements": "希望体验北京传统文化"
    }
    
    try:
        result = await llm_service.generate_route_plan(user_input)
        print("✅ LLM服务测试通过")
        print(f"📋 生成结果类型: {result.get('type', 'unknown')}")
        if 'content' in result:
            print(f"📝 内容预览: {result['content'][:100]}...")
    except Exception as e:
        print(f"❌ LLM服务测试失败: {e}")

async def test_route_planner():
    """测试路线规划服务"""
    print("🧪 测试路线规划服务...")
    
    db = SessionLocal()
    planner = RoutePlannerService()
    
    try:
        # 测试景点推荐
        recommendations = await planner.get_attraction_recommendations(
            city="北京",
            interests=["历史文化"],
            budget_range=(0, 100),
            db=db
        )
        print(f"✅ 景点推荐测试通过，找到 {len(recommendations)} 个景点")
        
        # 测试距离计算
        attractions = [
            {"name": "故宫", "latitude": 39.9163, "longitude": 116.3972},
            {"name": "天安门", "latitude": 39.9042, "longitude": 116.4074},
            {"name": "天坛", "latitude": 39.8823, "longitude": 116.4066}
        ]
        
        distance_result = await planner.calculate_route_distance(attractions)
        print(f"✅ 距离计算测试通过，总距离: {distance_result['total_distance']}km")
        
    except Exception as e:
        print(f"❌ 路线规划服务测试失败: {e}")
    finally:
        db.close()

def test_database_connection():
    """测试数据库连接"""
    print("🧪 测试数据库连接...")
    
    try:
        db = SessionLocal()
        # 简单查询测试
        result = db.execute("SELECT 1").fetchone()
        if result:
            print("✅ 数据库连接测试通过")
        else:
            print("❌ 数据库连接测试失败")
        db.close()
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 开始系统功能测试...\n")
    
    # 测试数据库连接
    test_database_connection()
    print()
    
    # 测试LLM服务（需要配置API密钥）
    try:
        await test_llm_service()
    except Exception as e:
        print(f"⚠️  LLM服务测试跳过（需要配置API密钥）: {e}")
    print()
    
    # 测试路线规划服务
    await test_route_planner()
    print()
    
    print("🎉 系统功能测试完成！")

if __name__ == "__main__":
    asyncio.run(main())