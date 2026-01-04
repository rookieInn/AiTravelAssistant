# 错误分类体系（多服务统一）

本文定义一套跨服务通用的**错误分类（Error Taxonomy）**，用于把来自多个服务的错误日志、错误码统一归置与汇总，并支持后续告警、SLO 统计、问题归因与治理。

## 目标与原则

- **统一口径**：同类问题在不同服务中输出一致的分类与字段。
- **可落地**：允许服务渐进式接入（先有分类与错误码，再逐步补齐字段）。
- **可治理**：分类可映射到“可重试/是否告警/责任归属/处理建议”。
- **可扩展**：类别尽量稳定，新问题优先归入既有类别，必要时再新增。

## 核心对象

- **错误事件（Error Event）**：一条日志或一次请求中的错误记录。
- **错误组（Error Group）**：按“错误码/类别/关键特征”聚合后的集合，用于统计与治理。

## 最小字段（建议所有服务逐步统一）

每个错误事件建议至少具备以下字段（结构化日志更佳，纯文本也可由采集工具抽取）：

- **service**：服务名（例如 `order-service`）
- **env**：环境（`prod`/`staging`/`dev`）
- **timestamp**：时间戳
- **level**：日志级别（`ERROR`/`WARN`/`INFO`）
- **error_code**：错误码（见《错误码规范》）
- **category**：错误类别（见下方“类别枚举”）
- **severity**：严重度（P0–P4，见下方定义）
- **retryable**：是否可重试（`true`/`false`/`unknown`）
- **message**：人类可读的错误描述
- **trace_id / request_id**：链路标识
- **dependency**（可选）：依赖方（如 `mysql`/`redis`/`payment-gateway`）

## 类别枚举（Category）

建议使用下列稳定枚举（括号内为常见归类线索）：

### 输入与协议

- **VALIDATION**：输入参数/请求体/字段格式不合法（`ValidationError`、`invalid argument`）
- **BAD_REQUEST**：语义不正确但不一定是字段校验（缺少必需资源标识、非法状态转换请求）
- **SERIALIZATION**：序列化/反序列化失败（JSON parse、protobuf decode）

### 鉴权与访问控制

- **AUTHENTICATION**：未登录/凭证无效（`401`、token invalid/expired）
- **AUTHORIZATION**：无权限访问（`403`、permission denied）

### 限流与配额

- **RATE_LIMIT**：触发限流（`429`、`rate limit exceeded`）
- **QUOTA_EXCEEDED**：配额/容量到达上限（每日额度、账户上限）

### 依赖与网络

- **NETWORK**：网络不可达/连接失败（`ECONNREFUSED`、`No route to host`）
- **TIMEOUT**：超时（`deadline exceeded`、`context deadline exceeded`、`ReadTimeout`）
- **DEPENDENCY**：第三方/下游返回错误但不属于网络/超时（支付网关返回 `5xx`、外部 API 业务错误）

### 存储与消息

- **DATABASE**：数据库错误（连接、SQL、锁等待、主从延迟导致的读不到）
- **CACHE**：缓存错误（Redis down、序列化、keyspace 配置）
- **QUEUE**：消息队列/流处理错误（Kafka offset、ack、broker unavailable）
- **IO**：文件系统/对象存储 IO 错误（S3 put/get 失败、磁盘写入失败）

### 资源与运行时

- **RESOURCE_EXHAUSTED**：资源耗尽（内存、CPU、线程池、连接池、FD）
- **CONCURRENCY**：并发冲突（乐观锁失败、重复提交、幂等冲突）
- **CONFIG**：配置缺失/不合法（缺少环境变量、证书路径错误）
- **RUNTIME**：运行时异常/崩溃（panic、segfault、NPE），且无法归入更具体类别

### 数据与业务

- **NOT_FOUND**：资源不存在（`404`、entity not found）
- **CONFLICT**：资源冲突（`409`、重复创建、版本冲突）
- **DATA_INTEGRITY**：数据一致性/约束错误（唯一键冲突可归入 CONFLICT，外键/约束/校验可归入此类）
- **BUSINESS_RULE**：业务规则不满足（余额不足、状态不允许、风控拒绝）

### 未分类兜底

- **UNKNOWN**：暂未识别，需补充规则或完善错误码/日志字段

## 严重度（Severity, P0–P4）

用严重度驱动告警与响应：

- **P0**：核心链路大面积不可用/数据损坏风险，需立刻响应
- **P1**：核心功能部分不可用或持续错误率升高，需尽快响应
- **P2**：非核心功能受影响或有明确降级路径，工作时间内响应
- **P3**：边缘场景/可忽略错误，对用户影响低，按需跟进
- **P4**：可预期的用户输入/业务拒绝（如参数校验失败、余额不足），通常不告警

## 可重试（Retryable）

- **true**：短暂性问题，通常重试可恢复（网络抖动、超时、依赖 5xx、连接池瞬时耗尽）
- **false**：重试无意义（参数校验失败、无权限、业务规则拒绝）
- **unknown**：无法判断，优先补充错误码与规则

## 归因与治理建议（可选扩展字段）

建议在错误组层面维护以下信息，用于治理闭环：

- **owner_team**：责任团队
- **runbook**：处理手册/链接
- **alert_policy**：是否告警、告警阈值（例如 5 分钟内错误率 > 2%）
- **slo_impact**：是否计入可用性/SLO

## 分类优先级建议

当同一事件命中多个特征时，建议优先级：

1. **明确的 error_code 映射**
2. **结构化字段**（例如 `http_status`、`grpc_status`、`exception_type`）
3. **规则匹配**（正则/关键词）
4. **UNKNOWN 兜底**

