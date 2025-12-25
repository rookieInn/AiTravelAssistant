from __future__ import annotations

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    imageId: str
    tenantId: str
    caption: str
    tags: list[str]
    userTags: list[str]


class SearchResult(BaseModel):
    imageId: str
    score: float
    caption: str
    tags: list[str]
    userTags: list[str]
    imagePath: str


class SearchResponse(BaseModel):
    tenantId: str
    queryType: str = Field(..., description="text|image|multimodal")
    topN: int
    results: list[SearchResult]

