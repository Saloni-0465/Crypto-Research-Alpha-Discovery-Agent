from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Report
from app.services.vector_store import embed_text, vector_store_from_settings

router = APIRouter()


@router.get("/search")
async def search_similar(
    q: str = Query(..., min_length=3, max_length=800),
    k: int = Query(8, ge=1, le=50),
    latest_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> dict:
    vec, meta = await embed_text(q)
    if vec is None:
        return {"error": "embeddings_disabled", "detail": "Set GEMINI_API_KEY to enable semantic search.", "meta": meta}

    store = vector_store_from_settings(dim=len(vec))
    hits = store.search(vector=vec, k=200 if latest_only else k)
    latest_run_id = None
    if latest_only:
        latest_report = (
            await db.execute(select(Report).order_by(desc(Report.created_at)).limit(1))
        ).scalar_one_or_none()
        latest_run_id = (latest_report.payload or {}).get("run_id") if latest_report else None

    filtered_hits = []
    seen_symbols: set[str] = set()
    for hit in hits:
        symbol = str(hit.meta.get("coin_symbol") or "")
        if latest_run_id and hit.meta.get("run_id") != latest_run_id:
            continue
        if symbol and symbol in seen_symbols:
            continue
        if symbol:
            seen_symbols.add(symbol)
        filtered_hits.append(hit)
        if len(filtered_hits) >= k:
            break

    return {
        "query": q,
        "k": k,
        "meta": {**meta, "latest_only": latest_only, "run_id": latest_run_id},
        "hits": [{"embedding_id": h.embedding_id, "score": h.score, "meta": h.meta} for h in filtered_hits],
    }
