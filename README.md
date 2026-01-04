# AiTravelAssistant

本仓库当前包含一套“多服务错误日志/错误码归置与错误分类”的**可执行落地方案**：

- **统一分类体系**：见 `docs/error-taxonomy.md`
- **统一错误码规范**：见 `docs/error-code-spec.md`
- **日志归集与自动分类工具**：见 `tools/errorhub/`（无外部依赖，直接用 `python3` 运行）

## 快速开始（用示例日志跑通）

```bash
python3 -m tools.errorhub categorize \
  --config configs/errorhub.config.json \
  --input examples/logs/order-service.log \
  --input examples/logs/pay-service.ndjson \
  --out-dir out/errorhub \
  --write-events
```

生成结果：

- `out/errorhub/report.md`：人类可读的 Top groups 汇总
- `out/errorhub/report.csv`：可导入表格/BI 的聚合统计
- `out/errorhub/report.json`：机器可读的完整报告
- `out/errorhub/events.ndjson`：逐条事件的分类结果（仅当 `--write-events`）

## 如何接入你的多个服务

- **优先让服务输出结构化字段**：`service`、`error_code`、`trace_id`、`message`
- **维护错误码注册表**：把每个错误码绑定到 `category/severity/retryable`（工具会优先按错误码归类）
- **补充规则**：在 `configs/errorhub.config.json` 的 `rules` 里新增正则规则，覆盖暂时没有错误码的旧日志
