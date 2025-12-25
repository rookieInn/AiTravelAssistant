from __future__ import annotations

import argparse
from pathlib import Path

from app.service import ImageSemanticService


def iter_images(root: Path):
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def main():
    ap = argparse.ArgumentParser(description="Offline batch ingest images into local FAISS+SQLite store")
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--dir", required=True, help="Directory containing images")
    ap.add_argument("--user-tags", default=None, help='Comma-separated or JSON array, e.g. "cat,pet" or ["cat","pet"]')
    args = ap.parse_args()

    svc = ImageSemanticService()
    root = Path(args.dir)
    if not root.exists():
        raise SystemExit(f"dir not found: {root}")

    n = 0
    for p in iter_images(root):
        b = p.read_bytes()
        r = svc.ingest_image_bytes(
            tenant_id=args.tenant, image_bytes=b, filename=p.name, user_tags_raw=args.user_tags
        )
        n += 1
        print(f"[{n}] {p} -> {r.image_id} | caption={r.caption!r} | tags={r.tags} | userTags={r.user_tags}")


if __name__ == "__main__":
    main()

