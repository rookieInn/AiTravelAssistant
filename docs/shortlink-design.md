 # 短链接服务设计
 
 ## 1. 目标与范围
 - **目标**：输入长链接，输出短链接；提供跳转与常用统计功能。
 - **范围**：API、数据模型、短码生成、跳转流程、统计与监控、可用性与安全。
 - **非目标**：不涵盖广告投放平台、复杂反作弊模型训练、BI可视化前端实现细节。
 
 ## 2. 核心功能
 1. **短链创建**
    - 输入长链接，返回短链。
    - 支持自定义短码（可选）。
    - 支持过期时间、备注、标签、归因参数（UTM）等。
 2. **短链跳转**
    - 访问短链时 301/302 重定向到长链接。
    - 支持禁用或过期提示页。
 3. **统计功能（常用）**
    - 总点击量、日/小时趋势（PV/UV）。
    - 独立访客（基于 cookie/IP+UA 的近似去重）。
    - 来源（Referrer/UTM）、地域、设备、系统、浏览器、语言。
    - 访问路径与响应码分布。
 4. **管理功能**
    - 查询、编辑、禁用、删除短链。
    - 批量创建/导出。
 5. **安全与风控**
    - 黑名单/白名单、恶意链接扫描、速率限制。
    - 访问频控与异常流量报警。
 
 ## 3. 关键约束与指标
 - **可用性**：99.9%+。
 - **重定向延迟**：P99 < 50ms（缓存命中场景）。
 - **写入吞吐**：可扩展，创建链路 QPS 与跳转 QPS 解耦。
 - **一致性**：短链映射强一致（创建后立即可用）。
 
 ## 4. API 设计（示例）
 ### 4.1 创建短链
 - **POST** `/api/v1/links`
 - Request：
   ```json
   {
     "long_url": "https://example.com/a/b?x=1",
     "custom_code": "promo2026",
     "expire_at": "2026-12-31T23:59:59Z",
     "tags": ["campaign", "spring"],
     "utm": {
       "source": "newsletter",
       "medium": "email",
       "campaign": "spring_sale"
     }
   }
   ```
 - Response：
   ```json
   {
     "id": "lnk_01HZY...",
     "short_code": "aZ4f9",
     "short_url": "https://s.example.com/aZ4f9",
     "long_url": "https://example.com/a/b?x=1",
     "expire_at": "2026-12-31T23:59:59Z",
     "created_at": "2026-01-21T08:00:00Z"
   }
   ```
 
 ### 4.2 访问跳转
 - **GET** `/{short_code}`
 - 行为：根据短码查找长链接并重定向（默认 302，可配置 301）。
 
 ### 4.3 统计查询
 - **GET** `/api/v1/links/{id}/stats?from=2026-01-01&to=2026-01-21`
 - Response（示例）：
   ```json
   {
     "total_clicks": 123456,
     "unique_visitors": 54321,
     "series": [
       {"date": "2026-01-20", "pv": 345, "uv": 210},
       {"date": "2026-01-21", "pv": 567, "uv": 300}
     ],
     "top_referrers": [
       {"referrer": "https://google.com", "pv": 123}
     ],
     "top_countries": [
       {"country": "CN", "pv": 890}
     ],
     "devices": [
       {"device": "Mobile", "pv": 650}
     ]
   }
   ```
 
 ## 5. 数据模型（示例）
 ### 5.1 关系型存储（元数据）
 ```sql
 CREATE TABLE short_links (
   id            BIGINT PRIMARY KEY,
   short_code    VARCHAR(16) UNIQUE NOT NULL,
   long_url      TEXT NOT NULL,
   owner_id      BIGINT NULL,
   status        SMALLINT NOT NULL DEFAULT 1, -- 1=active,2=disabled,3=expired
   expire_at     TIMESTAMP NULL,
   created_at    TIMESTAMP NOT NULL,
   updated_at    TIMESTAMP NOT NULL,
   meta_json     JSONB NULL
 );
 
 CREATE INDEX idx_short_links_status_expire
   ON short_links (status, expire_at);
 ```
 
 ### 5.2 统计存储
 - **实时计数**：Redis/KeyDB 计数器（PV/UV/地域/设备等）按小时/天维度累加。
 - **离线分析**：ClickHouse/BigQuery/Parquet 记录明细事件，用于大盘、回溯分析。
 
 ## 6. 短码生成策略
 1. **顺序 ID + Base62**
    - 生成全局递增 ID（Snowflake/数据库序列）。
    - 将 ID 进行 Base62 编码得到短码。
    - 优点：短、无碰撞；缺点：可枚举（可加扰或加盐）。
 2. **随机码（6-8 位）**
    - 生成随机短码，写入时校验冲突，冲突重试。
    - 优点：难枚举；缺点：需要冲突检测。
 
 **推荐方案**：Snowflake ID + Base62 + 可选掩码（XOR salt），兼顾长度与不可预测性。
 
 ## 7. 跳转与统计流程
 1. 用户访问短链 `/{short_code}`。
 2. **缓存查询**（Redis）：命中直接返回长链接。
 3. 未命中：访问 DB 读取短链映射，写回缓存（设置 TTL）。
 4. 异步上报统计事件（消息队列或日志）。
 5. 返回 302/301 重定向。
 
 ## 8. 统计埋点设计
 - 事件字段：`short_code`, `timestamp`, `ip`, `user_agent`, `referrer`,
   `device`, `os`, `browser`, `country`, `city`, `status_code`。
 - **UV 计算**：`cookie_id` 优先；无 cookie 时使用 `hash(ip + ua + day)`。
 - **聚合策略**：流式聚合到 Redis，定时落地到 OLAP。
 
 ## 9. 可用性与扩展
 - **缓存**：短码映射高频访问，使用 Redis + CDN Cache。
 - **分库分表**：按短码或 ID 分片。
 - **多地域部署**：就近访问，减少跳转延迟。
 - **降级策略**：统计落库失败不影响跳转。
 
 ## 10. 安全与风控
 - URL 合法性校验（scheme/长度/白名单）。
 - 反钓鱼/恶意链接扫描（异步扫描 + 人工审核）。
 - 速率限制（IP/账号维度）。
 - 管理端鉴权（JWT/OAuth2），审计日志。
 
 ## 11. 监控与告警
 - 指标：QPS、P99 延迟、缓存命中率、跳转失败率、队列积压。
 - 告警：异常峰值、黑名单命中率突增、DB/缓存故障。
 
 ## 12. 测试建议
 - 单元测试：短码生成、URL 校验、过期逻辑。
 - 压测：跳转接口、缓存命中/未命中路径。
 - 容灾演练：缓存/数据库故障模拟。
 
 ---
 如需落地实现，可基于上述设计补充技术选型与具体部署方案。
