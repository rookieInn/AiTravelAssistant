from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("data")
    db_path: Path = data_dir / "metadata.sqlite3"
    index_dir: Path = data_dir / "faiss"
    images_dir: Path = data_dir / "images"

    # Models (HF identifiers)
    clip_model: str = "openai/clip-vit-base-patch32"
    blip_model: str = "Salesforce/blip-image-captioning-base"

    # Fusion weights
    w_image: float = 0.6
    w_text: float = 0.4

    # Ranking (custom tags)
    tag_bonus: float = 0.15  # added to similarity score when tags match query (bounded)


SETTINGS = Settings()

