# 海量日志 TopK 统计系统设计

## 1. 背景与目标
- 日志量：10 亿条/天，约 100 GB（单条 100 B）。
- 统计指标：
  1. 当日观看时长总和 Top100 `videoId`。
  2. 当日被点赞次数 Top50 `creatorId`。
  3. 未来扩展：分享数 Top30 `videoId`。
- 时效性：次日 02:00 前出数，整体计算延迟 ≤ 2 小时。
- 约束：单机内存 ≤ 16 GB，需要断点续跑且扩展灵活。

## 2. 数据流与总体架构
```
客户端埋点 → Kafka (实时缓冲) → Flink Sink/Batch Writer → Data Lake (S3/HDFS, Parquet, 按小时分区)
                                                                      ↓
                                                        Airflow 调度的 Spark 任务（Structured Streaming micro-batch）
                                                                      ↓
                                        Delta 表 (video_watch_time, creator_likes, video_shares) + Hive Metastore
                                                                      ↓
                                        指标快照导入 ClickHouse/StarRocks → BI/运营分析
```
- **接入层**：Kafka 集群按业务线划分 Topic，写入三副本保证可靠性。
- **落盘层**：Flink Sink or Kafka Connect 将日志滚动写入对象存储（S3/HDFS）按 `dt=YYYY-MM-DD/hour=HH` 分区，存储格式 Parquet + Snappy，便于向量化读取。
- **计算层**：Spark Structured Streaming（微批 5 分钟）或 Spark Batch（每日定时）读取当日分区，执行 MapReduce 式聚合 + TopK 合并。
- **调度层**：Airflow 每天 00:30 触发，依赖前一日 24 个分区完成；失败自动重试并支持从 checkpoint 恢复。
- **结果层**：Delta 表用于保存历史，平台可通过 JDBC 或 Presto 查询。

## 3. 关键设计
### 3.1 TopK 双阶段聚合
1. **分桶聚合**：Spark 分区内先按 `groupByKey` 聚合（视频/创作者级别），使用 map-side combine 降低 shuffle。
2. **局部 TopK**：每个 Executor 用小顶堆维护本分区 TopK，序列化后写入临时 Delta 表。
3. **全局 TopK**：Driver/单节点读取所有局部 TopK（最多 `executor_num × K` 条），再次堆合并得最终 TopK，数据量小可直接内存处理。
4. **可拓展性**：TopK 指标配置化描述（过滤条件、聚合字段、K 值、输出目的表），新增 “分享数 Top30” 仅新增配置。

### 3.2 断点续跑
- Structured Streaming 自带 checkpoint（存储于 `s3://.../checkpoints/topk_job/`），记录偏移、state store。
- Batch 模式仍保留粒度为“小时分区”的落地结果，例如 `metrics/day=2025-11-28/hour=13`。当任务重跑，只处理未写成功的小时，已完成分区通过小文件元数据跳过。
- Airflow Operator 在写入成功后向 `processing_log` Delta 表插入 `day-hour` 状态，重试时读取该表确定需要补跑的分区。

### 3.3 资源规划（示例）
- 计算目标：100 GB 输入，2 小时完成 ⇒ 50 GB/h。
- Spark 集群：20 台 r6i.2xlarge（8 vCPU/64 GB），每 Executor 分配 6 GB 内存 + 2 核，保证 map-side 聚合不 OOM 且满足“单机 ≤16 GB”。
- 读取吞吐：Parquet + 列式压缩约 2.5× 压缩比，IO 压力 < 1 GB/s，总体可行。
- Checkpoint/State Store 需要约 50 GB SSD/HDFS，用 RocksDB state store（可自动 spill 到磁盘）。

### 3.4 容错
- Kafka → S3/HDFS：ACK=all、幂等生产者；落盘保证至少一次。
- Spark：失败自动重试，依赖 checkpoint 重放上游分区，输出使用 Delta 的 UPSERT（MERGE）避免重复。
- Airflow：定义 SLA（01:45），若未出数则报警；任务支持 `on_failure_callback` 触发 PagerDuty。

### 3.5 数据模型
#### 原始日志
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `userId` | STRING | 用户 |
| `videoId` | STRING | 视频 |
| `creatorId` | STRING | 创作者 |
| `action` | ENUM(view/like/share) | 行为类型 |
| `duration` | INT | view 时长（秒，其他行为为 0） |
| `ts` | TIMESTAMP | 行为时间 |

#### 指标结果表（示例）
| 表 | 主键 | 字段 |
| --- | --- | --- |
| `video_watch_time_daily` | `biz_date, rank` | `videoId, total_duration, rank, generated_at` |
| `creator_like_daily` | 同上 | `creatorId, like_count` |
| `video_share_daily` | 同上 | `videoId, share_count` |

## 4. 可扩展性方案
- 指标计算以 **配置驱动**：`metric_id`, `source`, `filters`, `group_keys`, `agg_expr`, `top_k`.
- 新指标仅新增一条配置，Spark 作业遍历配置表并为每条配置生成同构的 DataFrame 聚合逻辑。
- 数据 schema 固定，新增指标无需改动 ingestion。
- 结果存储/导出统一走 Delta + ClickHouse sink，保证一致的访问方式。

## 5. 运维与监控
- **指标监控**：接入 Prometheus，采集每个微批耗时、处理记录数、state store 大小。
- **数据质量**：对比 Kafka offset / S3 分区条数，发现丢数及时报警；TopK 结果设置区间校验（如 Top1 watch time 不应低于 30 分钟）。
- **调优策略**：观察 skew 视频（爆款），必要时对热点 `videoId` 做两级 key（hash 前缀）或开启 Adaptive Query Execution。

## 6. 输出与消费
- 结果写入 Delta 同时触发 ClickHouse Materialized View，供运营侧秒级查询。
- 任务完成后通过钉钉/Slack 发送 TopK 摘要，携带数据生成时间与数据量核对信息。

---
该设计满足性能、内存、容错及可扩展要求，并为后续新增指标提供低成本路径。
