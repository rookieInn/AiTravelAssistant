"""
Spark-based TopK job for massive short-video logs.

The job reads hourly partitions for a given biz_date, aggregates metrics in
small chunks, persists per-hour partial results to enable restart, and finally
produces the global TopK lists required by operations.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from pyspark.sql import Column, DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

LOG_SCHEMA = StructType(
    [
        StructField("userId", StringType(), nullable=False),
        StructField("videoId", StringType(), nullable=False),
        StructField("creatorId", StringType(), nullable=False),
        StructField("action", StringType(), nullable=False),
        StructField("duration", IntegerType(), nullable=True),
        StructField("ts", TimestampType(), nullable=False),
    ]
)


@dataclass
class MetricConfig:
    """Describes how to compute a single TopK metric."""

    name: str
    action: str
    dimension_col: str
    value_alias: str
    top_k: int
    agg_func: Callable[[Column], Column]
    value_col: Optional[str] = None
    extra_filters: List[Column] = field(default_factory=list)
    output_subdir: str = ""

    def metric_subdir(self, date_str: str) -> str:
        return os.path.join(self.output_subdir, f"dt={date_str}")


class ProgressTracker:
    """Keeps track of processed (metric, date, hour) tuples for restartability."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir) / "progress"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict[str, bool]] = {}

    def _state_path(self, metric: str, date_str: str) -> Path:
        return self.base_dir / f"{metric}_{date_str}.json"

    def _load(self, metric: str, date_str: str) -> Dict[str, bool]:
        cache_key = f"{metric}:{date_str}"
        if cache_key not in self._cache:
            path = self._state_path(metric, date_str)
            if path.exists():
                with path.open("r", encoding="utf-8") as fp:
                    self._cache[cache_key] = json.load(fp)
            else:
                self._cache[cache_key] = {}
        return self._cache[cache_key]

    def is_done(self, metric: str, date_str: str, hour: int) -> bool:
        state = self._load(metric, date_str)
        return state.get(f"{hour:02d}", False)

    def mark_done(self, metric: str, date_str: str, hour: int) -> None:
        state = self._load(metric, date_str)
        state[f"{hour:02d}"] = True
        path = self._state_path(metric, date_str)
        tmp_path = path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fp:
            json.dump(state, fp, ensure_ascii=False, sort_keys=True)
        tmp_path.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily TopK computation job")
    parser.add_argument("--input-base", required=True, help="Root path of hourly log partitions")
    parser.add_argument("--biz-date", required=True, help="Business date, e.g. 2025-11-27")
    parser.add_argument("--checkpoint-base", required=True, help="Directory to store partial aggregates")
    parser.add_argument("--output-base", required=True, help="Directory for final TopK results")
    parser.add_argument(
        "--enable-share-metric",
        action="store_true",
        help="Also compute share-count Top30 metric",
    )
    parser.add_argument(
        "--hours",
        type=str,
        default=",".join(f"{h:02d}" for h in range(24)),
        help="Comma separated hours (00-23) to process, default all day",
    )
    return parser.parse_args()


def build_metrics(output_base: str, enable_share: bool) -> List[MetricConfig]:
    metrics: List[MetricConfig] = [
        MetricConfig(
            name="video_watch_time",
            action="view",
            dimension_col="videoId",
            value_alias="total_duration",
            value_col="duration",
            agg_func=F.sum,
            top_k=100,
            output_subdir=os.path.join(output_base, "video_watch_time_daily"),
        ),
        MetricConfig(
            name="creator_like_count",
            action="like",
            dimension_col="creatorId",
            value_alias="like_count",
            value_col=None,
            agg_func=F.sum,
            top_k=50,
            output_subdir=os.path.join(output_base, "creator_like_daily"),
        ),
    ]
    if enable_share:
        metrics.append(
            MetricConfig(
                name="video_share_count",
                action="share",
                dimension_col="videoId",
                value_alias="share_count",
                value_col=None,
                agg_func=F.sum,
                top_k=30,
                output_subdir=os.path.join(output_base, "video_share_daily"),
            )
        )
    return metrics


def hour_partition_path(base: str, date_str: str, hour: str) -> str:
    return os.path.join(base, f"dt={date_str}", f"hour={hour}")


def path_exists(spark: SparkSession, target: str) -> bool:
    hadoop_conf = spark._jsc.hadoopConfiguration()
    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_conf)
    hadoop_path = spark._jvm.org.apache.hadoop.fs.Path(target)
    try:
        return fs.exists(hadoop_path)
    except Exception:  # pylint: disable=broad-except
        return Path(target).exists()


def compute_hourly_metric(df: DataFrame, metric: MetricConfig, date_str: str, hour: str) -> DataFrame:
    filtered = df.filter(F.col("action") == metric.action)
    for extra_filter in metric.extra_filters:
        filtered = filtered.filter(extra_filter)
    if metric.value_col:
        value_col = F.col(metric.value_col)
    else:
        value_col = F.lit(1)
    aggregated = (
        filtered.groupBy(F.col(metric.dimension_col).alias(metric.dimension_col))
        .agg(metric.agg_func(value_col).alias(metric.value_alias))
        .withColumn("biz_date", F.lit(date_str))
        .withColumn("hour", F.lit(hour))
    )
    return aggregated


def write_partial(df: DataFrame, path: str) -> None:
    if df.rdd.isEmpty():
        return
    df.write.mode("overwrite").parquet(path)


def load_partials(spark: SparkSession, root_path: str) -> Optional[DataFrame]:
    if not path_exists(spark, root_path):
        return None
    hourly_glob = os.path.join(root_path, "hour=*")
    try:
        return spark.read.parquet(hourly_glob)
    except Exception:  # pylint: disable=broad-except
        logging.warning("Failed to read partials under %s", hourly_glob)
        return None


def merge_partials_and_emit(df: DataFrame, metric: MetricConfig, biz_date: str, output_path: str) -> None:
    if df is None:
        logging.warning("No partials found for metric %s on %s", metric.name, biz_date)
        return
    aggregated = (
        df.groupBy(metric.dimension_col)
        .agg(F.sum(metric.value_alias).alias(metric.value_alias))
    )
    window = Window.orderBy(F.col(metric.value_alias).desc(), F.col(metric.dimension_col))
    ranked = (
        aggregated.withColumn("rank", F.row_number().over(window))
        .filter(F.col("rank") <= metric.top_k)
        .withColumn("biz_date", F.lit(biz_date))
    )
    ranked.write.mode("overwrite").parquet(output_path)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    spark = SparkSession.builder.appName("DailyTopKJob").getOrCreate()
    metrics = build_metrics(args.output_base, args.enable_share_metric)
    tracker = ProgressTracker(args.checkpoint_base)

    hours: Iterable[str] = [h.strip() for h in args.hours.split(",") if h.strip()]
    for hour in hours:
        hour_path = hour_partition_path(args.input_base, args.biz_date, hour)
        try:
            if not path_exists(spark, hour_path):
                logging.warning("Skip missing partition %s", hour_path)
                continue
        except Exception as err:  # pylint: disable=broad-except
            logging.error("Failed to check path %s: %s", hour_path, err)
            continue

        df_hour = spark.read.schema(LOG_SCHEMA).parquet(hour_path)
        for metric in metrics:
            if tracker.is_done(metric.name, args.biz_date, int(hour)):
                logging.info("Metric %s already processed for hour %s", metric.name, hour)
                continue
            partial_path = os.path.join(
                args.checkpoint_base,
                "partials",
                metric.name,
                f"dt={args.biz_date}",
                f"hour={hour}",
            )
            partial_df = compute_hourly_metric(df_hour, metric, args.biz_date, hour)
            write_partial(partial_df, partial_path)
            tracker.mark_done(metric.name, args.biz_date, int(hour))

    for metric in metrics:
        partial_root = os.path.join(
            args.checkpoint_base, "partials", metric.name, f"dt={args.biz_date}"
        )
        merged = load_partials(spark, partial_root)
        output_path = os.path.join(metric.output_subdir, f"dt={args.biz_date}")
        merge_partials_and_emit(merged, metric, args.biz_date, output_path)

    spark.stop()


if __name__ == "__main__":
    main()
