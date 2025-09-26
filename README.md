# AI智能旅游路线规划系统

基于大语言模型的智能旅游路线规划智能体，为用户提供个性化的旅行建议和路线规划。

## 功能特性

### 🎯 核心功能
- **智能路线规划**: 基于用户需求生成个性化旅游路线
- **多轮对话支持**: 支持上下文记忆和连续对话
- **实时优化**: 根据用户反馈动态调整路线
- **景点推荐**: 智能推荐符合用户兴趣的景点
- **费用估算**: 提供详细的预算规划

### ⚡ 性能指标
- **响应时间**: 1分钟内提供初始路线规划
- **准确率**: 95%以上满足用户需求
- **灵活性**: 10-15分钟内根据反馈调整优化
- **并发支持**: 支持100-200个并发请求

### 🔧 技术特性
- **大语言模型集成**: 支持OpenAI GPT系列模型
- **智能缓存**: Redis缓存提升响应速度
- **RESTful API**: 完整的API接口设计
- **用户认证**: JWT令牌认证系统
- **权限管理**: 区分普通用户和管理员权限
- **数据持久化**: SQLAlchemy ORM + SQLite数据库

## 系统架构

```
AI智能旅游路线规划系统
├── 前端界面 (HTML/CSS/JavaScript)
├── API服务层 (FastAPI)
├── 业务逻辑层 (Services)
├── 数据访问层 (Models)
├── 大语言模型服务 (LLM Service)
├── 缓存层 (Redis)
└── 数据库层 (SQLite)
```

## 快速开始

### 环境要求
- Python 3.8+
- Redis 6.0+
- 现代浏览器

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-travel-planner
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的API密钥
```

4. **启动Redis服务**
```bash
redis-server
```

5. **运行应用**
```bash
python main.py
```

6. **访问应用**
- 主页: http://localhost:8000
- API文档: http://localhost:8000/api/docs
- 聊天界面: http://localhost:8000/static/chat.html

## API接口

### 用户管理
- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新用户信息

### 路线规划
- `POST /api/v1/routes/plan` - 创建路线规划
- `GET /api/v1/routes/{route_id}` - 获取路线详情
- `PUT /api/v1/routes/{route_id}/optimize` - 优化路线
- `GET /api/v1/routes/` - 获取路线列表
- `POST /api/v1/routes/recommendations/attractions` - 获取景点推荐

### 管理员功能
- `GET /api/v1/admin/stats` - 获取系统统计
- `POST /api/v1/admin/attractions` - 创建景点
- `PUT /api/v1/admin/attractions/{id}` - 更新景点
- `DELETE /api/v1/admin/attractions/{id}` - 删除景点

## 使用示例

### 1. 用户注册和登录
```bash
# 注册用户
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# 用户登录
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 2. 创建路线规划
```bash
curl -X POST "http://localhost:8000/api/v1/routes/plan" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "destination": "北京",
    "start_date": "2024-01-01",
    "end_date": "2024-01-03",
    "travelers": 2,
    "budget": 5000,
    "interests": ["历史文化", "美食"]
  }'
```

### 3. 获取景点推荐
```bash
curl -X POST "http://localhost:8000/api/v1/routes/recommendations/attractions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "city": "北京",
    "interests": ["历史文化"],
    "budget_range": [0, 200]
  }'
```

## 配置说明

### 环境变量
- `OPENAI_API_KEY`: OpenAI API密钥（必需）
- `SECRET_KEY`: JWT签名密钥
- `DATABASE_URL`: 数据库连接URL
- `REDIS_URL`: Redis连接URL
- `MAP_API_KEY`: 地图API密钥（可选）

### 数据库配置
系统使用SQLite作为默认数据库，支持以下数据模型：
- 用户信息 (User)
- 旅游景点 (Attraction)
- 酒店信息 (Hotel)
- 路线规划 (Route)
- 路线日程 (RouteDay)
- 路线活动 (RouteActivity)

## 部署指南

### Docker部署
```bash
# 构建镜像
docker build -t ai-travel-planner .

# 运行容器
docker run -p 8000:8000 ai-travel-planner
```

### 生产环境配置
1. 修改数据库为PostgreSQL或MySQL
2. 配置Redis集群
3. 设置反向代理（Nginx）
4. 配置SSL证书
5. 设置监控和日志

## 开发指南

### 项目结构
```
ai-travel-planner/
├── app/
│   ├── core/           # 核心配置
│   ├── models/         # 数据模型
│   ├── routes/         # API路由
│   └── services/       # 业务服务
├── static/             # 静态文件
├── main.py            # 应用入口
├── requirements.txt   # 依赖列表
└── README.md         # 项目说明
```

### 添加新功能
1. 在 `app/models/` 中定义数据模型
2. 在 `app/services/` 中实现业务逻辑
3. 在 `app/routes/` 中创建API接口
4. 更新前端界面（如需要）

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱: support@example.com
- 项目地址: https://github.com/example/ai-travel-planner

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础路线规划功能
- 用户认证系统
- 管理员后台
- 聊天界面