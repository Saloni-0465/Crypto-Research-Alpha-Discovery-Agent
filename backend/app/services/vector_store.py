from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from google.genai import types

from app.settings import settings
from app.services.gemini import gemini_client


@dataclass
class VectorHit:
    embedding_id: int
    score: float
    meta: dict[str, Any]


class FaissVectorStore:
    def __init__(self, *, dim: int, dir_path: str):
        self.dim = dim
        self.dir = Path(dir_path)
        self.dir.mkdir(parents=True, exist_ok=True)

        self._index_path = self.dir / "index.faiss"
        self._meta_path = self.dir / "meta.json"
        self._reset_meta = False

        self.index = self._load_or_create()
        self.meta = self._load_meta()

    def _load_or_create(self):
        if self._index_path.exists():
            index = faiss.read_index(str(self._index_path))
            if index.d == self.dim:
                return index
            self._reset_meta = True
        # cosine similarity via inner product on normalized vectors
        return faiss.IndexFlatIP(self.dim)

    def _load_meta(self) -> dict[str, Any]:
        if self._meta_path.exists() and not self._reset_meta:
            return json.loads(self._meta_path.read_text())
        return {"next_id": 1, "items": {}}

    def _persist(self) -> None:
        faiss.write_index(self.index, str(self._index_path))
        self._meta_path.write_text(json.dumps(self.meta, indent=2, sort_keys=True))

    def add(self, *, vector: np.ndarray, meta: dict[str, Any]) -> int:
        v = vector.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        embedding_id = int(self.meta["next_id"])
        self.meta["next_id"] = embedding_id + 1

        self.index.add(v)
        self.meta["items"][str(embedding_id)] = meta
        self._persist()
        return embedding_id

    def search(self, *, vector: np.ndarray, k: int = 5) -> list[VectorHit]:
        if self.index.ntotal == 0:
            return []
        v = vector.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        scores, ids = self.index.search(v, k)

        hits: list[VectorHit] = []
        for score, idx in zip(scores[0].tolist(), ids[0].tolist(), strict=False):
            if idx < 0:
                continue
            # IndexFlat doesn't preserve our embedding_id; we store sequentially and map by position+1
            embedding_id = idx + 1
            meta = self.meta["items"].get(str(embedding_id), {})
            hits.append(VectorHit(embedding_id=embedding_id, score=float(score), meta=meta))
        return hits

async def embed_text(text: str) -> tuple[np.ndarray | None, dict[str, Any]]:
    if not settings.gemini_api_key:
        return None, {"mode": "disabled"}
    try:
        client = gemini_client()
        resp = client.models.embed_content(
            model=settings.gemini_embeddings_model,
            contents=text[:8000],
            config=types.EmbedContentConfig(output_dimensionality=settings.gemini_embeddings_dim),
        )
        values = resp.embeddings[0].values  # type: ignore[attr-defined]
        vec = np.array(values, dtype="float32")
        return vec, {"mode": "gemini", "model": settings.gemini_embeddings_model, "dim": settings.gemini_embeddings_dim}
    except Exception as exc:  # noqa: BLE001
        return None, {"mode": "disabled", "reason": type(exc).__name__}


def vector_store_from_settings(*, dim: int) -> FaissVectorStore:
    dir_path = settings.faiss_dir
    # allow relative paths under backend/
    if not os.path.isabs(dir_path):
        dir_path = str(Path(__file__).resolve().parents[2] / dir_path)
    return FaissVectorStore(dim=dim, dir_path=dir_path)
