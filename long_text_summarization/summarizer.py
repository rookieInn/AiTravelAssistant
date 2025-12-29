from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Optional, Sequence

import jieba
import numpy as np


_ZH_SENT_BOUNDARY_RE = re.compile(r"(?<=[。！？；!?;])")
_SPACE_RE = re.compile(r"[ \t\f\v]+")
_PUNCT_RE = re.compile(r"^[\W_]+$", re.UNICODE)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Keep newlines (helps sentence splitting); only collapse spaces/tabs.
    text = _SPACE_RE.sub(" ", text)
    return text.strip()


def _split_sentences_zh(text: str) -> List[str]:
    # Keep punctuation; split on end punctuation or newlines.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # First, split by newlines, then by end punctuation boundaries.
    parts: List[str] = []
    for block in re.split(r"\n+", text):
        block = block.strip()
        if not block:
            continue
        parts.extend([p.strip() for p in _ZH_SENT_BOUNDARY_RE.split(block) if p.strip()])
    # If punctuation-based split didn't work (e.g. no punctuation), fall back to rough chunks.
    if len(parts) <= 1 and len(text) > 200:
        chunk_size = 80
        parts = [text[i : i + chunk_size].strip() for i in range(0, len(text), chunk_size)]
        parts = [p for p in parts if p]
    return parts


def _tokenize_zh(sentence: str) -> List[str]:
    toks = [t.strip() for t in jieba.lcut(sentence, cut_all=False)]
    toks = [t for t in toks if t and not _PUNCT_RE.match(t)]
    return toks


@dataclass(frozen=True)
class _Vec:
    weights: dict[str, float]
    norm: float


def _tfidf_vectors(tokenized: Sequence[Sequence[str]]) -> List[_Vec]:
    n = len(tokenized)
    if n == 0:
        return []

    df: dict[str, int] = {}
    for toks in tokenized:
        seen = set(toks)
        for t in seen:
            df[t] = df.get(t, 0) + 1

    idf: dict[str, float] = {}
    for t, d in df.items():
        # Smooth IDF.
        idf[t] = math.log((n + 1) / (d + 1)) + 1.0

    vecs: List[_Vec] = []
    for toks in tokenized:
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        weights: dict[str, float] = {}
        for t, c in tf.items():
            w = (c / max(1, len(toks))) * idf.get(t, 0.0)
            if w:
                weights[t] = w
        norm = math.sqrt(sum(w * w for w in weights.values())) or 1.0
        vecs.append(_Vec(weights=weights, norm=norm))
    return vecs


def _cosine(a: _Vec, b: _Vec) -> float:
    # Iterate smaller dict for speed.
    if len(a.weights) > len(b.weights):
        a, b = b, a
    dot = 0.0
    for t, wa in a.weights.items():
        wb = b.weights.get(t)
        if wb is not None:
            dot += wa * wb
    return dot / (a.norm * b.norm)


def _pagerank(sim: np.ndarray, damping: float = 0.85, max_iter: int = 200, tol: float = 1e-6) -> np.ndarray:
    n = sim.shape[0]
    if n == 0:
        return np.array([], dtype=float)
    if n == 1:
        return np.array([1.0], dtype=float)

    # Row-normalize outgoing weights.
    out = sim.sum(axis=1)
    out = np.where(out == 0.0, 1.0, out)
    m = (sim.T / out).astype(float)  # column-stochastic-ish

    pr = np.full(n, 1.0 / n, dtype=float)
    teleport = (1.0 - damping) / n
    for _ in range(max_iter):
        prev = pr
        pr = teleport + damping * (m @ prev)
        if float(np.abs(pr - prev).sum()) < tol:
            break
    return pr


def summarize(
    text: str,
    *,
    max_sentences: int = 3,
    max_chars: Optional[int] = None,
    ratio: Optional[float] = None,
    language: str = "zh",
    preserve_order: bool = True,
    sentence_limit: int = 200,
) -> str:
    """
    Extractive summarization for long text (TextRank-like on TF-IDF sentence similarity).

    Args:
        text: Input long text.
        max_sentences: Maximum sentences to return (ignored if ratio is provided).
        max_chars: Optional soft cap for returned summary length (characters).
        ratio: Optional ratio in (0,1], e.g. 0.1 means keep top 10% sentences.
        language: Currently supports "zh" (Chinese-ish sentence splitting + jieba tokenization).
        preserve_order: If True, keep selected sentences in original order.
        sentence_limit: Max sentences considered (to keep O(n^2) bounded).
    """
    text_n = _normalize_text(text)
    if not text_n:
        return ""

    if language != "zh":
        # Fallback: treat as "zh" splitting but without jieba benefit is limited.
        language = "zh"

    sents = _split_sentences_zh(text_n)
    # Filter very short/empty lines.
    sents = [s.strip() for s in sents if s and len(s.strip()) >= 2]
    if not sents:
        return text_n[: max_chars] if max_chars else text_n

    if len(sents) > sentence_limit:
        sents = sents[:sentence_limit]

    if ratio is not None:
        if not (0.0 < ratio <= 1.0):
            raise ValueError("ratio must be in (0, 1].")
        k = max(1, int(round(len(sents) * ratio)))
    else:
        k = max(1, int(max_sentences))
    k = min(k, len(sents))

    if len(sents) <= k:
        out = " ".join(sents)
        return out[:max_chars] if max_chars else out

    tokenized = [_tokenize_zh(s) for s in sents]
    vecs = _tfidf_vectors(tokenized)

    n = len(vecs)
    sim = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            c = _cosine(vecs[i], vecs[j])
            if c > 0:
                sim[i, j] = c
                sim[j, i] = c

    scores = _pagerank(sim)
    ranked = sorted(range(n), key=lambda i: float(scores[i]), reverse=True)

    chosen: List[int] = []
    if max_chars is None:
        chosen = ranked[:k]
    else:
        total = 0
        for idx in ranked:
            if len(chosen) >= k:
                break
            add_len = len(sents[idx]) + (1 if chosen else 0)  # space
            if total + add_len <= max_chars or not chosen:
                chosen.append(idx)
                total += add_len
        if not chosen:
            chosen = [ranked[0]]

    if preserve_order:
        chosen.sort()

    summary = " ".join(sents[i] for i in chosen).strip()
    if max_chars is not None and len(summary) > max_chars:
        summary = summary[:max_chars].rstrip()
    return summary
