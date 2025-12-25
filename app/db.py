from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    tenant_id: str
    image_path: str
    caption: str
    tags: list[str]
    user_tags: list[str]
    created_at: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetadataDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS images (
                    image_id   TEXT PRIMARY KEY,
                    tenant_id  TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    caption    TEXT NOT NULL,
                    tags_json  TEXT NOT NULL,
                    user_tags_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_images_tenant ON images(tenant_id);"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vectors (
                    vector_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id  TEXT NOT NULL,
                    image_id   TEXT NOT NULL,
                    UNIQUE(tenant_id, image_id)
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_vectors_tenant ON vectors(tenant_id);"
            )

    def upsert_image(
        self,
        *,
        image_id: str,
        tenant_id: str,
        image_path: str,
        caption: str,
        tags: list[str],
        user_tags: list[str],
    ) -> None:
        created_at = _utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO images(image_id, tenant_id, image_path, caption, tags_json, user_tags_json, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(image_id) DO UPDATE SET
                    tenant_id=excluded.tenant_id,
                    image_path=excluded.image_path,
                    caption=excluded.caption,
                    tags_json=excluded.tags_json,
                    user_tags_json=excluded.user_tags_json;
                """,
                (
                    image_id,
                    tenant_id,
                    image_path,
                    caption,
                    json.dumps(tags, ensure_ascii=False),
                    json.dumps(user_tags, ensure_ascii=False),
                    created_at,
                ),
            )

    def get_images_by_ids(self, ids: Iterable[str]) -> dict[str, ImageRecord]:
        ids_list = list(ids)
        if not ids_list:
            return {}
        q = ",".join(["?"] * len(ids_list))
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM images WHERE image_id IN ({q});", ids_list
            ).fetchall()
        out: dict[str, ImageRecord] = {}
        for r in rows:
            out[r["image_id"]] = ImageRecord(
                image_id=r["image_id"],
                tenant_id=r["tenant_id"],
                image_path=r["image_path"],
                caption=r["caption"],
                tags=json.loads(r["tags_json"]),
                user_tags=json.loads(r["user_tags_json"]),
                created_at=r["created_at"],
            )
        return out

    def get_or_create_vector_id(self, *, tenant_id: str, image_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT vector_id FROM vectors WHERE tenant_id=? AND image_id=?;",
                (tenant_id, image_id),
            ).fetchone()
            if row:
                return int(row["vector_id"])
            cur = conn.execute(
                "INSERT INTO vectors(tenant_id, image_id) VALUES(?, ?);",
                (tenant_id, image_id),
            )
            return int(cur.lastrowid)

    def get_image_ids_by_vector_ids(
        self, *, tenant_id: str, vector_ids: Iterable[int]
    ) -> dict[int, str]:
        ids_list = [int(v) for v in vector_ids if v is not None]
        if not ids_list:
            return {}
        q = ",".join(["?"] * len(ids_list))
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT vector_id, image_id FROM vectors WHERE tenant_id=? AND vector_id IN ({q});",
                [tenant_id, *ids_list],
            ).fetchall()
        return {int(r["vector_id"]): str(r["image_id"]) for r in rows}

    def search_user_tags(
        self, *, tenant_id: str, query_text_lower: str
    ) -> dict[str, float]:
        """
        Returns: image_id -> bonus in [0, 1] based on substring match against user tags.
        (Simple + deterministic; can be replaced by tag-embedding similarity.)
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT image_id, user_tags_json FROM images WHERE tenant_id=?;",
                (tenant_id,),
            ).fetchall()
        bonuses: dict[str, float] = {}
        for r in rows:
            image_id = r["image_id"]
            try:
                tags: list[str] = json.loads(r["user_tags_json"])
            except Exception:
                tags = []
            if not tags or not query_text_lower:
                continue
            matched = 0
            for t in tags:
                if query_text_lower in (t or "").lower():
                    matched += 1
            if matched:
                bonuses[image_id] = min(1.0, matched / max(1, len(tags)))
        return bonuses

