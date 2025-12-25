from __future__ import annotations

import io
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .config import SETTINGS
from .db import MetadataDB
from .ml import caption_image, clip_dim, embed_image, embed_text, fuse_query_embeddings, tags_from_caption
from .vector_store import TenantFaissIndex


def _safe_tenant(tenant_id: str) -> str:
    # keep path-safe and deterministic
    return "".join(ch for ch in tenant_id if ch.isalnum() or ch in ("-", "_")).strip() or "default"


def _parse_user_tags(user_tags_raw: str | None) -> list[str]:
    if not user_tags_raw:
        return []
    s = user_tags_raw.strip()
    if not s:
        return []
    # allow JSON array or comma-separated
    if s.startswith("["):
        try:
            v = json.loads(s)
            if isinstance(v, list):
                return [str(x).strip() for x in v if str(x).strip()]
        except Exception:
            pass
    return [t.strip() for t in s.split(",") if t.strip()]


@dataclass
class IngestResult:
    image_id: str
    tenant_id: str
    caption: str
    tags: list[str]
    user_tags: list[str]


@dataclass
class RankedResult:
    image_id: str
    score: float


class ImageSemanticService:
    def __init__(self):
        SETTINGS.data_dir.mkdir(parents=True, exist_ok=True)
        SETTINGS.index_dir.mkdir(parents=True, exist_ok=True)
        SETTINGS.images_dir.mkdir(parents=True, exist_ok=True)
        self.db = MetadataDB(SETTINGS.db_path)
        self._indexes: dict[str, TenantFaissIndex] = {}

    def _tenant_index(self, tenant_id: str) -> TenantFaissIndex:
        t = _safe_tenant(tenant_id)
        if t in self._indexes:
            return self._indexes[t]
        idx_path = SETTINGS.index_dir / f"{t}.faiss"
        idx = TenantFaissIndex(idx_path, dim=clip_dim())
        self._indexes[t] = idx
        return idx

    def ingest_image_bytes(
        self,
        *,
        tenant_id: str,
        image_bytes: bytes,
        filename: str | None = None,
        user_tags_raw: str | None = None,
    ) -> IngestResult:
        image_id = str(uuid.uuid4())
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        caption = caption_image(img)
        tags = tags_from_caption(caption)
        user_tags = _parse_user_tags(user_tags_raw)

        emb = embed_image(img)  # normalized
        vector_id = self.db.get_or_create_vector_id(tenant_id=tenant_id, image_id=image_id)
        self._tenant_index(tenant_id).add(vector_id=vector_id, embedding=emb)
        self._tenant_index(tenant_id).save()

        # persist image file
        t = _safe_tenant(tenant_id)
        ext = (Path(filename).suffix.lower() if filename else "") or ".jpg"
        out_dir = SETTINGS.images_dir / t
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{image_id}{ext}"
        img.save(out_path)

        self.db.upsert_image(
            image_id=image_id,
            tenant_id=tenant_id,
            image_path=str(out_path),
            caption=caption,
            tags=tags,
            user_tags=user_tags,
        )

        return IngestResult(
            image_id=image_id,
            tenant_id=tenant_id,
            caption=caption,
            tags=tags,
            user_tags=user_tags,
        )

    def search(
        self,
        *,
        tenant_id: str,
        top_n: int,
        query_text: str | None = None,
        query_image_bytes: bytes | None = None,
    ) -> tuple[str, list[RankedResult]]:
        text_emb = None
        image_emb = None
        query_type = "text"

        if query_text and query_text.strip():
            text_emb = embed_text(query_text.strip())
            query_type = "text"
        if query_image_bytes:
            img = Image.open(io.BytesIO(query_image_bytes)).convert("RGB")
            image_emb = embed_image(img)
            query_type = "image" if text_emb is None else "multimodal"

        q = fuse_query_embeddings(text_emb=text_emb, image_emb=image_emb)
        hits = self._tenant_index(tenant_id).search(query_embedding=q, top_k=max(1, int(top_n)))

        # map vector_id -> image_id
        vid_to_iid = self.db.get_image_ids_by_vector_ids(
            tenant_id=tenant_id, vector_ids=[h.vector_id for h in hits]
        )

        # custom tag bonuses (simple substring match in user tags)
        bonuses: dict[str, float] = {}
        if query_text and query_text.strip():
            bonuses = self.db.search_user_tags(
                tenant_id=tenant_id, query_text_lower=query_text.strip().lower()
            )

        ranked: list[RankedResult] = []
        for h in hits:
            image_id = vid_to_iid.get(h.vector_id)
            if not image_id:
                continue
            bonus = bonuses.get(image_id, 0.0) * SETTINGS.tag_bonus
            ranked.append(RankedResult(image_id=image_id, score=float(h.score + bonus)))

        ranked.sort(key=lambda r: r.score, reverse=True)
        return query_type, ranked[: max(1, int(top_n))]

