# AiTravelAssistant

## 合并“同一人在同一公司多个职位”的处理方式

你给的 JSON 里（如 `data.ENT_INFO.PERSON`），同一人可能在同一家公司同时担任多个职位（例如 `鲍涛` 同时是 `副董事长` 和 `经理`）。
常见做法是按 **(ENTNAME, PERNAME)** 分组，将同组的 `POSITION` 去重后用 **中文逗号 `，`** 连接。

### Java + Fastjson 示例

示例代码：`MergePositionsFastjson.java`

- 读取：`data.ENT_INFO.PERSON`
- 合并：按 `(ENTNAME, PERNAME)` 分组，把 `POSITION` 去重后用 `，` 拼接
- 回写：把合并后的 `PERSON` 写回原 JSON

说明：示例使用 `com.alibaba.fastjson`（Fastjson 1.x）API；如果你项目用的是 Fastjson2，可告诉我我再给对应版本。

### Python 示例

见脚本：`merge_positions.py`

```bash
python merge_positions.py
```