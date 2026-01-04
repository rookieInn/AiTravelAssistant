# 错误码规范（多服务统一）

本文定义跨服务统一的错误码格式与分配规则，目标是让错误**可检索、可聚合、可治理**，并能与《错误分类体系》联动实现自动归类与报表。

## 设计目标

- **全局唯一**：跨服务、跨模块不冲突
- **可读性**：看到错误码能快速定位服务与模块
- **可演进**：支持新增模块/新增错误而不破坏已有含义
- **可映射**：可映射到 HTTP/gRPC 状态码与分类（category）

## 错误码格式

推荐格式：

> `SVC-MOD-NNNN`

- **SVC**：服务短名（3–10 位大写字母/数字，例如 `ORDER`、`PAY`、`USER`）
- **MOD**：模块短名（2–12 位大写字母/数字，例如 `API`、`DB`、`AUTH`、`BILLING`）
- **NNNN**：4 位数字，按“类别段”划分（见下方分段规则）

示例：

- `ORDER-API-1001`：订单服务 API 层参数校验失败
- `PAY-GW-4002`：支付服务调用下游网关超时
- `USER-AUTH-2001`：用户服务鉴权失败（token 过期）

## 数字段分段规则（NNNN）

为了让错误码天然带“类别信息”，建议按千位段划分：

- **1xxx**：输入/协议类（`VALIDATION`、`BAD_REQUEST`、`SERIALIZATION`）
- **2xxx**：鉴权/权限类（`AUTHENTICATION`、`AUTHORIZATION`）
- **3xxx**：限流/配额类（`RATE_LIMIT`、`QUOTA_EXCEEDED`）
- **4xxx**：依赖/网络/超时类（`DEPENDENCY`、`NETWORK`、`TIMEOUT`）
- **5xxx**：存储/消息/IO 类（`DATABASE`、`CACHE`、`QUEUE`、`IO`）
- **6xxx**：资源/运行时/配置类（`RESOURCE_EXHAUSTED`、`CONFIG`、`RUNTIME`、`CONCURRENCY`）
- **7xxx**：业务规则与数据一致性（`BUSINESS_RULE`、`CONFLICT`、`NOT_FOUND`、`DATA_INTEGRITY`）
- **9xxx**：未知/兜底/兼容历史（慎用，建议尽快治理掉）

> 说明：HTTP 4xx 与这里的 4xxx **不是同一个概念**；这里的 4xxx 表示“依赖/网络/超时类别段”。

## 与错误分类（category）的映射

错误码应当在服务内维护一份注册表（建议以 JSON/表格形式），每个错误码至少绑定：

- **category**：错误类别（见《错误分类体系》）
- **severity**：P0–P4
- **retryable**：true/false/unknown
- **http_status / grpc_status**（可选）：对外协议状态码建议值

这样日志归集工具可以通过 `error_code` 直接归类，而不依赖脆弱的关键词匹配。

## 错误响应建议（对外接口）

建议统一错误响应 envelope（示例，字段可按语言/框架调整）：

```json
{
  "error": {
    "code": "ORDER-API-1001",
    "message": "invalid field: check_in_date",
    "category": "VALIDATION",
    "severity": "P4",
    "retryable": false,
    "trace_id": "b7b6c9d0..."
  }
}
```

## 分配与变更流程（建议）

- **新增错误码**：必须登记到服务内的错误码注册表（含 category/severity/retryable）
- **禁止复用**：历史错误码语义一旦发布，不可改变含义；如需变更，新增错误码并保留旧码兼容
- **治理 UNKNOWN**：出现 `UNKNOWN` 或 `9xxx` 的聚合项，应当补充错误码或完善注册表/规则

## 与日志字段的关系

日志中至少输出：

- `error_code`：如 `ORDER-API-1001`
- `message`：人类可读
- `trace_id`：链路追踪

结构化日志建议同时输出 `category/severity/retryable`，否则可由注册表/归类工具补齐。

