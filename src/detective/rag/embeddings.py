# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Vector side of the retrieval: embeddings cached in a .npz, cosine with numpy.

Contract R1: "Vectores con el modelo de EMBED_MODEL vía Ollama, guardados en un
.npz que se reconstruye con ``python -m src.detective.rag.build_index``. Similitud
coseno con numpy; sin base de datos vectorial."

If there is no embedding service the whole vector side disappears and retrieval
runs on BM25 alone — without failing (contract §11).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import SETTINGS
from ..corpus import Document, corpus_fingerprint
from ..llm import AIUnavailable, embed


@dataclass
class VectorIndex:
    doc_ids: list[str]
    matrix: np.ndarray  # (n_docs, dim), L2-normalised
    model: str
    fingerprint: str

    def search(self, query_vec: np.ndarray, *, limit: int) -> list[tuple[int, float]]:
        if self.matrix.size == 0:
            return []
        q = _l2(query_vec.reshape(1, -1))[0]
        sims = self.matrix @ q
        order = np.argsort(-sims)[:limit]
        return [(int(i), float(sims[i])) for i in order]


def _l2(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def index_path(model: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in model)
    return SETTINGS.index_dir / f"docs-{safe}.npz"


def build(docs: list[Document], *, model: str, batch_size: int = 16) -> VectorIndex:
    """Embed every document and persist the matrix. Raises AIUnavailable on failure."""
    if not docs:
        raise ValueError("cannot build a vector index from an empty corpus")
    vectors: list[list[float]] = []
    for start in range(0, len(docs), batch_size):
        chunk = docs[start : start + batch_size]
        vectors.extend(embed([d.searchable() for d in chunk], model=model))
    matrix = _l2(np.asarray(vectors, dtype=np.float32))
    fp = corpus_fingerprint(docs)
    path = index_path(model)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        matrix=matrix,
        doc_ids=np.asarray([d.id for d in docs]),
        meta=np.asarray([json.dumps({"model": model, "fingerprint": fp})]),
    )
    return VectorIndex(doc_ids=[d.id for d in docs], matrix=matrix, model=model, fingerprint=fp)


def load(docs: list[Document], *, model: str) -> VectorIndex | None:
    """Load the cached index if it matches this corpus; otherwise None (rebuild)."""
    path = index_path(model)
    if not path.exists():
        return None
    try:
        with np.load(path, allow_pickle=False) as blob:
            matrix = blob["matrix"].astype(np.float32)
            doc_ids = [str(x) for x in blob["doc_ids"].tolist()]
            meta = json.loads(str(blob["meta"][0]))
    except (OSError, ValueError, KeyError):
        return None
    if meta.get("fingerprint") != corpus_fingerprint(docs):
        return None  # corpus changed: a stale index is worse than no index
    by_id = {d.id: i for i, d in enumerate(docs)}
    if set(by_id) != set(doc_ids):
        return None
    order = [by_id[i] for i in doc_ids]
    # Re-align rows with the in-memory document order.
    inverse = np.argsort(order)
    return VectorIndex(doc_ids=[docs[i].id for i in order], matrix=matrix[inverse], model=model, fingerprint=meta["fingerprint"])


def query_vector(text: str, *, model: str) -> np.ndarray:
    vecs = embed([text], model=model)
    return np.asarray(vecs[0], dtype=np.float32)


def try_load_or_build(docs: list[Document], *, model: str) -> VectorIndex | None:
    """Best effort: never raises. Returns None when embeddings are unavailable."""
    if not model:
        return None
    cached = load(docs, model=model)
    if cached is not None:
        return cached
    try:
        return build(docs, model=model)
    except (AIUnavailable, ValueError):
        return None
