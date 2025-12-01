# 退款审核系统

该示例项目实现了一个退款审核与自动退费服务，覆盖“用户自助申请 + 后台审核 + 自动远端退费 + 失败后人工重试”完整闭环。项目基于 FastAPI，以内存仓库演示业务流程，方便本地快速验证。

## 核心流程

1. **用户自助申请**：用户提交订单号、退款金额、原因，生成 `PENDING_REVIEW` 状态的退款单。
2. **后台审核**：运营人员审批用户单据，审批通过后系统立即调用支付网关自动退费；审批拒绝则结束流程。
3. **后台直接发起**：后台也可绕过审核直接创建退款单，并立即触发自动退费，用于客服或财务手工场景。
4. **自动退费**：`PaymentGateway` 封装远端退费接口。退费成功进入 `REFUNDED`，失败进入 `REFUND_FAILED` 并记录失败原因。
5. **失败后重试**：若自动退费失败，后台可在上限内多次重试，系统统计 `manual_retry_count` 与 `remote_attempt_count`，方便追踪。

状态机：`PENDING_REVIEW → (APPROVE) → REMOTE_PROCESSING → REFUNDED / REFUND_FAILED`，`REFUND_FAILED` 状态可通过重新发起进入新的 `REMOTE_PROCESSING`，直至成功或超过重试次数。

## 目录结构

```
app/
  ├── main.py            # FastAPI 入口 & 路由
  ├── models.py          # 领域模型与状态枚举
  ├── schemas.py         # Pydantic 请求/响应模型
  ├── services.py        # 退款领域服务，封装审核、退费逻辑
  ├── storage.py         # 线程安全内存仓库
  └── payment_gateway.py # 示例支付网关适配层
requirements.txt         # 运行依赖
README.md                # 使用说明
```

tests 中包含三条端到端测试（用户审核成功、失败后重试、后台直退）。

## 运行与调试

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000
```

启动后可通过 `http://localhost:8000/docs` 访问自动生成的 Swagger UI，覆盖以下接口：

- `POST /refunds/user/apply`：用户发起退款
- `POST /refunds/backoffice/create`：后台直接发起退款并自动退费
- `POST /refunds/{id}/review`：后台审核，审核通过会触发远端退费
- `POST /refunds/{id}/retry`：后台在失败后重新发起退费
- `GET /refunds/{id}` / `GET /refunds?status=...`：查询单条或按状态筛选

## 测试

```bash
pytest
```

测试使用 FastAPI `TestClient` 覆盖成功、失败/重试、后台直退三种关键场景，模拟网关失败后再次成功的路径，确保业务分支正确。
