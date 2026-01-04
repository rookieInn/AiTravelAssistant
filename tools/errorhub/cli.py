from __future__ import annotations

import argparse
from pathlib import Path

from .categorize import categorize_logs


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="errorhub",
        description="Aggregate and categorize error logs across services.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("categorize", help="Categorize log files and output reports.")
    c.add_argument(
        "--config",
        type=Path,
        default=Path("configs/errorhub.config.json"),
        help="Path to config JSON (default: configs/errorhub.config.json)",
    )
    c.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input file/dir/glob (repeatable), e.g. examples/logs/*.log",
    )
    c.add_argument(
        "--out-dir",
        type=Path,
        default=Path("out/errorhub"),
        help="Output directory (default: out/errorhub)",
    )
    c.add_argument(
        "--write-events",
        action="store_true",
        help="Also write categorized events as NDJSON (events.ndjson).",
    )
    c.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="Max events to process (0 means no limit).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    p = _build_parser()
    args = p.parse_args(argv)

    if args.command == "categorize":
        categorize_logs(
            config_path=args.config,
            inputs=args.input,
            out_dir=args.out_dir,
            write_events=bool(args.write_events),
            max_events=int(args.max_events),
        )
        return 0

    p.error(f"unknown command: {args.command}")
    return 2

