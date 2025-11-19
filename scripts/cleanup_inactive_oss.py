#!/usr/bin/env python3
"""
Remove images stored in Aliyun OSS for users who have been inactive for a configurable
number of days.

The script expects:
1. A relational database (PostgreSQL/MySQL/etc.) that stores user metadata containing:
   - `id`: primary key for logs
   - `oss_prefix`: the folder/key prefix in OSS where the user's images live
   - `last_login_at`: timestamp of the last successful login
2. An OSS bucket that keeps the user images.

Environment variables:
    DATABASE_URL                SQLAlchemy-compatible database URL.
    ALIYUN_OSS_ENDPOINT         Example: https://oss-cn-hangzhou.aliyuncs.com
    ALIYUN_OSS_ACCESS_KEY_ID
    ALIYUN_OSS_ACCESS_KEY_SECRET
    ALIYUN_OSS_BUCKET

Optional:
    USER_QUERY                  Custom SQL to fetch inactive users. Must include
                                `:cutoff` parameter and return `id`, `oss_prefix`.

Usage:
    python scripts/cleanup_inactive_oss.py --older-than-days 365 --apply --yes
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import oss2
from oss2.exceptions import OssError
from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None  # type: ignore


DEFAULT_USER_SQL = """
SELECT id, oss_prefix
FROM users
WHERE (last_login_at IS NULL OR last_login_at < :cutoff)
  AND oss_prefix IS NOT NULL
  AND oss_prefix <> ''
ORDER BY last_login_at ASC, id ASC
"""


@dataclass
class InactiveUser:
    user_id: int
    oss_prefix: str


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete Aliyun OSS objects belonging to users inactive for N days."
    )
    parser.add_argument(
        "--older-than-days",
        type=int,
        default=365,
        help="Users whose last_login_at is older than this many days will be selected.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional limit for number of inactive users to process (useful for batching).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="How many OSS objects to delete per batch request.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete the objects. Without this flag the script runs in dry-run mode.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation when --apply is used.",
    )
    parser.add_argument(
        "--user-query-file",
        type=Path,
        help="Optional path to a SQL file that replaces the default inactive-user query.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def maybe_load_dotenv() -> None:
    if load_dotenv is not None:
        load_dotenv()


def get_db_engine() -> Engine:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logging.error("DATABASE_URL is not set.")
        raise SystemExit(2)
    return create_engine(db_url)


def get_bucket() -> oss2.Bucket:
    endpoint = os.getenv("ALIYUN_OSS_ENDPOINT")
    ak = os.getenv("ALIYUN_OSS_ACCESS_KEY_ID")
    sk = os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET")
    bucket_name = os.getenv("ALIYUN_OSS_BUCKET")

    missing = [name for name, value in [
        ("ALIYUN_OSS_ENDPOINT", endpoint),
        ("ALIYUN_OSS_ACCESS_KEY_ID", ak),
        ("ALIYUN_OSS_ACCESS_KEY_SECRET", sk),
        ("ALIYUN_OSS_BUCKET", bucket_name),
    ] if not value]
    if missing:
        logging.error("Missing required OSS env variables: %s", ", ".join(missing))
        raise SystemExit(2)

    auth = oss2.Auth(ak, sk)
    return oss2.Bucket(auth, endpoint, bucket_name)


def load_user_query(custom_file: Optional[Path]) -> str:
    if custom_file:
        if not custom_file.exists():
            logging.error("Custom query file %s not found.", custom_file)
            raise SystemExit(2)
        return custom_file.read_text(encoding="utf-8")

    env_query = os.getenv("USER_QUERY")
    if env_query:
        return env_query
    return DEFAULT_USER_SQL


def fetch_inactive_users(engine: Engine, query: str, cutoff: dt.datetime, limit: Optional[int]) -> List[InactiveUser]:
    query_to_run = query.strip()
    params = {"cutoff": cutoff}

    if limit is not None and ":limit" in query_to_run:
        params["limit"] = limit
    elif limit is not None and ":limit" not in query_to_run:
        query_to_run = f"{query_to_run}\nLIMIT :limit"
        params["limit"] = limit

    if ":cutoff" not in query_to_run:
        logging.error("The user query must contain the ':cutoff' parameter.")
        raise SystemExit(2)

    try:
        with engine.begin() as conn:
            rows = conn.execute(text(query_to_run), params)
            return [
                InactiveUser(user_id=row["id"], oss_prefix=row["oss_prefix"])
                for row in rows
                if row["oss_prefix"]
            ]
    except SQLAlchemyError as exc:
        logging.error("Failed to execute inactive-user query: %s", exc)
        raise SystemExit(1)


def validate_prefix(prefix: str) -> bool:
    cleaned = prefix.strip()
    if not cleaned or cleaned in ("/", "."):
        logging.warning("Skipping suspicious prefix '%s'.", prefix)
        return False
    return True


def delete_objects(bucket: oss2.Bucket, keys: Sequence[str], dry_run: bool) -> int:
    if not keys:
        return 0
    if dry_run:
        logging.debug("[dry-run] Would delete keys: %s", keys)
        return len(keys)

    try:
        result = bucket.batch_delete_objects(keys, quiet=True)
        if result.delete_keys:
            logging.debug("Deleted %d objects.", len(result.delete_keys))
            return len(result.delete_keys)
        return len(keys)
    except OssError as exc:
        logging.error("OSS deletion failed for keys %s: %s", keys, exc)
        return 0


def delete_prefix(bucket: oss2.Bucket, prefix: str, batch_size: int, dry_run: bool) -> int:
    total_deleted = 0
    batch: List[str] = []
    iterator = oss2.ObjectIteratorV2(bucket, prefix=prefix, max_keys=batch_size)

    for obj in iterator:
        batch.append(obj.key)
        if len(batch) >= batch_size:
            total_deleted += delete_objects(bucket, batch, dry_run)
            batch = []

    if batch:
        total_deleted += delete_objects(bucket, batch, dry_run)

    return total_deleted


def confirm_execution(dry_run: bool) -> bool:
    if dry_run:
        logging.info("Running in dry-run mode. No data will be deleted.")
        return True

    answer = input("This will permanently delete OSS objects. Type 'delete' to proceed: ").strip()
    if answer.lower() != "delete":
        logging.info("Aborted by user.")
        return False
    return True


def cleanup_users(users: Iterable[InactiveUser], bucket: oss2.Bucket, batch_size: int, dry_run: bool) -> None:
    total_users = 0
    total_objects = 0

    for user in users:
        if not validate_prefix(user.oss_prefix):
            continue
        total_users += 1
        deleted = delete_prefix(bucket, user.oss_prefix, batch_size, dry_run)
        total_objects += deleted
        logging.info(
            "User %s | prefix='%s' | objects_deleted=%d",
            user.user_id,
            user.oss_prefix,
            deleted,
        )

    logging.info(
        "Completed cleanup. Users processed=%d, objects_deleted=%d%s",
        total_users,
        total_objects,
        " (dry-run)" if dry_run else "",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.log_level)
    maybe_load_dotenv()

    cutoff = dt.datetime.utcnow() - dt.timedelta(days=args.older_than_days)
    logging.info("Cutoff timestamp: %s", cutoff.isoformat())

    dry_run = not args.apply
    if args.apply and not args.yes and sys.stdin.isatty():
        if not confirm_execution(dry_run=False):
            return 0
    elif args.apply and not args.yes and not sys.stdin.isatty():
        logging.error("Refusing to delete without --yes in non-interactive mode.")
        return 2
    elif dry_run:
        logging.info("Dry-run mode is active. Use --apply --yes to delete objects.")

    engine = get_db_engine()
    bucket = get_bucket()
    query = load_user_query(args.user_query_file)
    users = fetch_inactive_users(engine, query, cutoff, args.limit)

    if not users:
        logging.info("No inactive users matched the query.")
        return 0

    cleanup_users(users, bucket, args.batch_size, dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
