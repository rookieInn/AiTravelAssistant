#!/bin/bash

# AI智能旅游路线规划系统启动脚本

echo "🚀 启动AI智能旅游路线规划系统..."

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $python_version == *"Python 3"* ]]; then
    echo "✅ Python版本检查通过: $python_version"
else
    echo "❌ 需要Python 3.8或更高版本"
    exit 1
fi

# 检查Redis服务
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis服务运行正常"
    else
        echo "⚠️  Redis服务未运行，正在启动..."
        redis-server --daemonize yes
        sleep 2
        if redis-cli ping &> /dev/null; then
            echo "✅ Redis服务启动成功"
        else
            echo "❌ Redis服务启动失败，请手动启动Redis"
            exit 1
        fi
    fi
else
    echo "❌ 未找到Redis，请先安装Redis"
    exit 1
fi

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 检查环境变量
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，创建默认配置..."
    cp .env.example .env 2>/dev/null || echo "请手动创建.env文件并配置必要的API密钥"
fi

# 初始化数据库
echo "🗄️  初始化数据库..."
python -c "
from app.core.database import engine, Base
Base.metadata.create_all(bind=engine)
print('✅ 数据库初始化完成')
"

# 启动应用
echo "🌟 启动AI智能旅游路线规划系统..."
echo "📍 访问地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/api/docs"
echo "💬 聊天界面: http://localhost:8000/static/chat.html"
echo ""
echo "按 Ctrl+C 停止服务"

python main.py