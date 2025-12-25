from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import faiss  # type: ignore
import numpy as np


def _to_float32(x: np.ndarray) -> np.ndarray:
    if x.dtype != np.float32:
        x = x.astype(np.float32, copy=False)
    return x


@dataclass
class SearchHit:
    vector_id: int
    score: float


class TenantFaissIndex:
    """
    Cosine similarity via inner product over L2-normalized vectors.
    Uses IndexIDMap2 so we can retrieve integer IDs (vector_id).
    """

    def __init__(self, index_path: Path, dim: int):
        self.index_path = index_path
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.dim = dim
        self._lock = threading.Lock()
        self._index = self._load_or_create()

    def _load_or_create(self) -> faiss.Index:
        if self.index_path.exists():
            idx = faiss.read_index(str(self.index_path))
            return idx
        base = faiss.IndexFlatIP(self.dim)
        return faiss.IndexIDMap2(base)

    def save(self) -> None:
        with self._lock:
            faiss.write_index(self._index, str(self.index_path))

    def add(self, *, vector_id: int, embedding: np.ndarray) -> None:
        emb = _to_float32(embedding).reshape(1, -1)
        ids = np.array([int(vector_id)], dtype=np.int64)
        with self._lock:
            self._index.add_with_ids(emb, ids)

    def add_many(self, *, vector_ids: Iterable[int], embeddings: np.ndarray) -> None:
        ids = np.array([int(i) for i in vector_ids], dtype=np.int64)
        embs = _to_float32(embeddings)
        if embs.ndim != 2:
            raise ValueError("embeddings must be 2D")
        if embs.shape[0] != ids.shape[0]:
            raise ValueError("vector_ids and embeddings size mismatch")
        with self._lock:
            self._index.add_with_ids(embs, ids)

    def search(self, *, query_embedding: np.ndarray, top_k: int) -> list[SearchHit]:
        q = _to_float32(query_embedding).reshape(1, -1)
        with self._lock:
            scores, ids = self._index.search(q, top_k)
        out: list[SearchHit] = []
        for vid, s in zip(ids[0].tolist(), scores[0].tolist()):
            if vid == -1:
                continue
            out.append(SearchHit(vector_id=int(vid), score=float(s)))
        return out

