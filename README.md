# 会议/通话纪要系统（说话人分离 + 行动项可追溯）

目标：在**音频转写**（已包含时间戳与说话人）之后，自动生成结构化会议纪要：

- **输入**：`transcript`（带时间戳/说话人）、会议元信息（会议时间、参会人、主题等）
- **输出**：`summary`、`actionItems`、`risks`、`decisions`
- **约束**：每条 **action item 必须可追溯**到原文（引用时间戳/utterance）
- **加分能力**：自动写入工单系统；到期提醒

> 说明：说话人分离（diarization）属于上游能力；本项目默认输入已经包含 `speaker` 字段。

## 快速开始

### 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) 运行示例

```bash
python -m meeting_minutes.cli \
  --transcript examples/sample_transcript.json \
  --metadata examples/sample_metadata.json \
  --out examples/out.json
```

输出文件 `examples/out.json` 将包含：

- `summary`: 列表形式要点
- `actionItems`: 每条包含 `sourceQuotes`（带时间戳与 utteranceId）
- `risks`, `decisions`

## 输入格式（JSON）

### transcript

`transcript` 是一个 utterance 列表：

- `id`: 句子/片段唯一 id
- `speaker`: 说话人标识（如 “Alice” / “SPEAKER_01”）
- `start`: 开始时间戳（`HH:MM:SS.mmm`）
- `end`: 结束时间戳（`HH:MM:SS.mmm`）
- `text`: 转写文本

### metadata

最少字段：

- `meetingTitle`
- `meetingDate`（ISO 8601，例如 `2025-12-24T10:00:00+08:00`）
- `participants`（数组）

## 工单写入（可选）

当前提供一个 **GitHub Issues** 适配器（可选）：

```bash
export GITHUB_TOKEN="..."
python -m meeting_minutes.cli \
  --transcript examples/sample_transcript.json \
  --metadata examples/sample_metadata.json \
  --create-github-issues \
  --github-repo owner/repo \
  --out examples/out_with_issues.json
```

## 到期提醒（可选）

CLI 支持输出提醒计划（JSON），用于接入你们内部的定时任务/消息推送系统：

```bash
python -m meeting_minutes.cli \
  --transcript examples/sample_transcript.json \
  --metadata examples/sample_metadata.json \
  --reminders examples/reminders.json \
  --out examples/out.json
```

## 设计原则

- **可追溯**：action item 必须引用原句（时间戳/utteranceId），否则会校验失败
- **可扩展**：抽取器（启发式/LLM）与工单/提醒是可插拔模块
- **可落地**：默认启发式抽取可离线运行；如接入 LLM 可替换抽取器