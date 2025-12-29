from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import jieba

from .summarizer import summarize


def _read_text(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="long-text-summarization",
        description="Generate an extractive summary for long Chinese text.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input text file path (UTF-8). Use '-' or omit to read stdin.",
    )
    p.add_argument("-k", "--max-sentences", type=int, default=3, help="Max sentences in summary.")
    p.add_argument("--max-chars", type=int, default=None, help="Soft cap for summary length (chars).")
    p.add_argument("--ratio", type=float, default=None, help="Keep top ratio of sentences, e.g. 0.1")
    p.add_argument(
        "--no-preserve-order",
        action="store_true",
        help="Do not preserve original sentence order.",
    )
    p.add_argument(
        "--sentence-limit",
        type=int,
        default=200,
        help="Max sentences considered (bounds runtime).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    jieba.setLogLevel(logging.WARN)
    text = _read_text(args.file)
    out = summarize(
        text,
        max_sentences=args.max_sentences,
        max_chars=args.max_chars,
        ratio=args.ratio,
        preserve_order=not args.no_preserve_order,
        sentence_limit=args.sentence_limit,
        language="zh",
    )
    sys.stdout.write(out)
    if out and not out.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
