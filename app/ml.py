from __future__ import annotations

import re
from functools import lru_cache

import numpy as np
import torch
from PIL import Image
from transformers import (
    BlipForConditionalGeneration,
    BlipProcessor,
    CLIPModel,
    CLIPProcessor,
)

from .config import SETTINGS


def _device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _normalize(v: np.ndarray) -> np.ndarray:
    v = v.astype(np.float32, copy=False)
    n = np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12
    return v / n


@lru_cache(maxsize=1)
def _clip():
    processor = CLIPProcessor.from_pretrained(SETTINGS.clip_model)
    model = CLIPModel.from_pretrained(SETTINGS.clip_model)
    model.eval()
    model.to(_device())
    return processor, model


def clip_dim() -> int:
    _, model = _clip()
    # CLIPModel uses a projection_dim for both text & image features.
    return int(getattr(model.config, "projection_dim", 512))


@lru_cache(maxsize=1)
def _blip():
    processor = BlipProcessor.from_pretrained(SETTINGS.blip_model)
    model = BlipForConditionalGeneration.from_pretrained(SETTINGS.blip_model)
    model.eval()
    model.to(_device())
    return processor, model


def embed_image(img: Image.Image) -> np.ndarray:
    processor, model = _clip()
    inputs = processor(images=img, return_tensors="pt")
    inputs = {k: v.to(_device()) for k, v in inputs.items()}
    with torch.no_grad():
        feats = model.get_image_features(**inputs)
    out = feats.detach().cpu().numpy()[0]
    return _normalize(out)


def embed_text(text: str) -> np.ndarray:
    processor, model = _clip()
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    inputs = {k: v.to(_device()) for k, v in inputs.items()}
    with torch.no_grad():
        feats = model.get_text_features(**inputs)
    out = feats.detach().cpu().numpy()[0]
    return _normalize(out)


def caption_image(img: Image.Image, *, max_new_tokens: int = 30) -> str:
    processor, model = _blip()
    inputs = processor(images=img, return_tensors="pt")
    inputs = {k: v.to(_device()) for k, v in inputs.items()}
    with torch.no_grad():
        out_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
    cap = processor.decode(out_ids[0], skip_special_tokens=True)
    return (cap or "").strip()


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}


def tags_from_caption(caption: str, *, k: int = 8) -> list[str]:
    """
    Deterministic, dependency-light tagger.
    Replace with KeyBERT/LLM/zero-shot classification if you want higher quality tags.
    """
    s = (caption or "").lower()
    tokens = re.findall(r"[a-z0-9]+", s)
    toks = [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]
    freq: dict[str, int] = {}
    for t in toks:
        freq[t] = freq.get(t, 0) + 1
    # sort by frequency then length
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))
    out: list[str] = []
    for t, _ in ranked:
        out.append(t)
        if len(out) >= k:
            break
    return out


def fuse_query_embeddings(
    *, text_emb: np.ndarray | None, image_emb: np.ndarray | None
) -> np.ndarray:
    if text_emb is None and image_emb is None:
        raise ValueError("text_emb and image_emb cannot both be None")
    if text_emb is not None and image_emb is not None:
        v = SETTINGS.w_text * text_emb + SETTINGS.w_image * image_emb
        return _normalize(v)
    return text_emb if text_emb is not None else image_emb  # already normalized

