#!/usr/bin/env python3
"""
简化的系统测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        from app.core.config import settings
        print("✅ 配置模块导入成功")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False
    
    try:
        from app.core.database import engine, Base
        print("✅ 数据库模块导入成功")
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        return False
    
    try:
        from app.models.user import User
        from app.models.attraction import Attraction
        from app.models.route import Route
        print("✅ 数据模型导入成功")
    except Exception as e:
        print(f"❌ 数据模型导入失败: {e}")
        return False
    
    try:
        from app.services.llm_service import LLMService
        from app.services.route_planner import RoutePlannerService
        print("✅ 服务模块导入成功")
    except Exception as e:
        print(f"❌ 服务模块导入失败: {e}")
        return False
    
    return True

def test_database():
    """测试数据库连接"""
    print("\n🧪 测试数据库连接...")
    
    try:
        from app.core.database import SessionLocal, engine
        from app.models.user import User
        
        # 创建数据库表
        from app.core.database import Base
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")
        
        # 测试数据库连接
        db = SessionLocal()
        user_count = db.query(User).count()
        print(f"✅ 数据库连接成功，用户数量: {user_count}")
        db.close()
        
        return True
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_llm_service():
    """测试LLM服务"""
    print("\n🧪 测试LLM服务...")
    
    try:
        from app.services.llm_service import LLMService
        
        llm_service = LLMService()
        print("✅ LLM服务初始化成功")
        
        # 注意：这里不实际调用API，因为需要配置API密钥
        print("⚠️  LLM服务需要配置API密钥才能完全测试")
        
        return True
    except Exception as e:
        print(f"❌ LLM服务测试失败: {e}")
        return False

async def test_route_planner():
    """测试路线规划服务"""
    print("\n🧪 测试路线规划服务...")
    
    try:
        from app.services.route_planner import RoutePlannerService
        from app.core.database import SessionLocal
        
        planner = RoutePlannerService()
        print("✅ 路线规划服务初始化成功")
        
        # 测试景点推荐
        db = SessionLocal()
        recommendations = await planner.get_attraction_recommendations(
            city="北京",
            interests=["历史文化"],
            budget_range=(0, 100),
            db=db
        )
        print(f"✅ 景点推荐测试成功，找到 {len(recommendations)} 个景点")
        db.close()
        
        return True
    except Exception as e:
        print(f"❌ 路线规划服务测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始AI智能旅游路线规划系统测试...\n")
    
    # 测试模块导入
    if not test_imports():
        print("\n❌ 模块导入测试失败，请检查依赖安装")
        return False
    
    # 测试数据库
    if not test_database():
        print("\n❌ 数据库测试失败，请检查数据库配置")
        return False
    
    # 测试LLM服务
    if not test_llm_service():
        print("\n❌ LLM服务测试失败，请检查LLM配置")
        return False
    
    # 测试路线规划服务
    try:
        import asyncio
        if not asyncio.run(test_route_planner()):
            print("\n❌ 路线规划服务测试失败")
            return False
    except Exception as e:
        print(f"\n❌ 路线规划服务测试失败: {e}")
        return False
    
    print("\n🎉 所有测试通过！系统可以正常运行")
    print("\n📝 使用说明:")
    print("1. 配置 .env 文件中的 OPENAI_API_KEY")
    print("2. 运行 python3 main.py 启动服务")
    print("3. 访问 http://localhost:8000 查看主页")
    print("4. 访问 http://localhost:8000/static/chat.html 使用聊天界面")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)