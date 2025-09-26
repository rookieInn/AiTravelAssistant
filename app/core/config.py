"""
系统配置
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "AI智能旅游路线规划系统"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 数据库配置
    database_url: str = "sqlite:///./travel_planner.db"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # JWT配置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # LLM配置
    openai_api_key: Optional[str] = None
    llm_model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # 地图API配置
    map_api_key: Optional[str] = None
    
    # 缓存配置
    cache_ttl: int = 3600  # 1小时
    
    # 性能配置
    max_concurrent_requests: int = 200
    request_timeout: int = 60
    
    class Config:
        env_file = ".env"

# 全局设置实例
settings = Settings()