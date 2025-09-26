"""
AI智能旅游路线规划系统
基于FastAPI和LLM的智能旅游路线规划智能体
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
from dotenv import load_dotenv

from app.routes import routes, users, admin
from app.core.config import settings
from app.core.database import engine, Base
from app.core.security import verify_token
from app.services.route_planner import RoutePlannerService
from app.services.llm_service import LLMService

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title="AI智能旅游路线规划系统",
    description="基于大语言模型的智能旅游路线规划智能体",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(routes.router, prefix="/api/v1/routes", tags=["路线规划"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理员"])

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 安全认证
security = HTTPBearer()

# 依赖注入
def get_route_planner():
    return RoutePlannerService()

def get_llm_service():
    return LLMService()

@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI智能旅游路线规划系统</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            .feature { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
            .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗺️ AI智能旅游路线规划系统</h1>
            <div class="feature">
                <h3>🎯 核心功能</h3>
                <p>基于大语言模型的智能旅游路线规划，为您提供个性化的旅行建议</p>
            </div>
            <div class="feature">
                <h3>⚡ 性能指标</h3>
                <p>• 响应时间：1分钟内提供初始路线规划<br>
                • 准确率：95%以上满足用户需求<br>
                • 灵活性：10-15分钟内根据反馈调整优化</p>
            </div>
            <div class="feature">
                <h3>🔧 技术特性</h3>
                <p>• 多轮对话支持<br>
                • 实时数据更新<br>
                • 智能缓存优化<br>
                • 地图可视化</p>
            </div>
            <div style="text-align: center;">
                <a href="/api/docs" class="btn">API文档</a>
                <a href="/static/chat.html" class="btn">开始规划</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "AI智能旅游路线规划系统运行正常"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )