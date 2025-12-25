from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .schemas import IngestResponse, SearchResponse, SearchResult
from .service import ImageSemanticService

app = FastAPI(title="Semantic Image Retrieval", version="0.1.0")
svc = ImageSemanticService()


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/v1/ingest", response_model=IngestResponse)
async def ingest(
    tenantId: str = Form(...),
    image: UploadFile = File(...),
    userTags: str | None = Form(None),
):
    try:
        b = await image.read()
        if not b:
            raise HTTPException(status_code=400, detail="empty image")
        r = svc.ingest_image_bytes(
            tenant_id=tenantId,
            image_bytes=b,
            filename=image.filename,
            user_tags_raw=userTags,
        )
        return IngestResponse(
            imageId=r.image_id,
            tenantId=r.tenant_id,
            caption=r.caption,
            tags=r.tags,
            userTags=r.user_tags,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/search", response_model=SearchResponse)
async def search(
    tenantId: str = Form(...),
    topN: int = Form(10),
    queryText: str | None = Form(None),
    queryImage: UploadFile | None = File(None),
):
    if (not queryText or not queryText.strip()) and queryImage is None:
        raise HTTPException(status_code=400, detail="queryText or queryImage required")

    qimg = await queryImage.read() if queryImage is not None else None

    try:
        query_type, ranked = svc.search(
            tenant_id=tenantId, top_n=topN, query_text=queryText, query_image_bytes=qimg
        )
        records = svc.db.get_images_by_ids([r.image_id for r in ranked])
        results: list[SearchResult] = []
        for r in ranked:
            rec = records.get(r.image_id)
            if not rec:
                continue
            results.append(
                SearchResult(
                    imageId=rec.image_id,
                    score=r.score,
                    caption=rec.caption,
                    tags=rec.tags,
                    userTags=rec.user_tags,
                    imagePath=rec.image_path,
                )
            )
        return SearchResponse(tenantId=tenantId, queryType=query_type, topN=topN, results=results)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

