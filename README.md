# 日志 TopK 统计系统

本仓库提供一套针对短视频 App 的海量日志统计方案，满足以下目标：

- 每日统计观看时长 Top100 视频、点赞数 Top50 创作者，支持未来扩展分享数 Top30。
- 处理规模：10 亿条日志（≈100 GB）在 2 小时内完成，单机内存 ≤16 GB。
- 具备断点续跑能力，宕机后无需重跑全部数据。

## 目录结构

```
docs/design.md      # 架构与容量规划说明
src/topk_job.py     # Spark 作业实现，支持分小时增量 + TopK 计算
requirements.txt    # 开发依赖
```

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 准备数据：按照 `dt=YYYY-MM-DD/hour=HH` 的分区结构，将原始日志（Parquet 格式、字段见设计文档）写入对象存储或本地文件系统。
3. 运行 TopK 作业（示例使用本地模式，实际部署可通过 `spark-submit` 提交到集群）：
   ```bash
   spark-submit \
     --master local[4] \
     src/topk_job.py \
     --input-base s3://video-logs/raw \
     --biz-date 2025-11-27 \
     --checkpoint-base s3://video-logs/checkpoints/topk \
     --output-base s3://video-logs/metrics \
     --enable-share-metric
   ```

任务会依次读取尚未处理的 `hour` 分区，生成局部聚合结果并持久化；全部小时完成后再合并得出最终 TopK 列表。若运行中断，重跑会自动跳过已处理的小时。

> 更详细的架构、容量及容错设计请参阅 `docs/design.md`。

## 结果消费

作业会在 `output-base` 下生成以下目录：

- `video_watch_time_daily/dt=YYYY-MM-DD`：字段 `videoId,total_duration,rank,biz_date`
- `creator_like_daily/dt=YYYY-MM-DD`：字段 `creatorId,like_count,rank,biz_date`
- `video_share_daily/dt=YYYY-MM-DD`（启用分享指标时）

这些结果可继续导入 ClickHouse/StarRocks/Doris 供运营分析或 Dashboard 展示。