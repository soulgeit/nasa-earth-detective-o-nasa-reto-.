# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Retrieval (contract R1).

    question ─► BM25 ─┐
                 ────┴─► reciprocal rank fusion ─► documents with score, title, url, type
    question ─► embeddings ─┘

Design notes
------------
* Fusion is Reciprocal Rank Fusion (Cormack et al. 2009, *Reciprocal Rank Fusion
  outperforms Condorcet and individual rank learning methods*), the standard way to
  merge two rankers without calibrating their scales.
* Anything that fails on the vector side is dropped; BM25 alone remains. The
  response says which backends actually ran in ``meta``.
* No document is ever invented: every result comes from ``corpus.load_corpus()``.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, Sequence

from ..bm25 import BM25Index
from ..config import SETTINGS
from ..corpus import Document, corpus_fingerprint, load_corpus
from ..lexicon import expansion_terms, specificity_prior
from ..llm import AIUnavailable
from ..text_norm import detect_language
from .embeddings import VectorIndex, query_vector, try_load_or_build

RRF_K = 60  # standard damping constant
# Cards for products that still need a manual Giovanni export rank below the
# ones the app can fetch live, but they are not hidden: they are real candidates.
TIER_PLANNED_FACTOR = 0.75


@dataclass
class _Corpus:
    docs: list[Document]
    bm25: BM25Index
    fingerprint: str


@lru_cache(maxsize=1)
def _cached_corpus() -> _Corpus:
    docs = load_corpus()
    return _Corpus(docs=docs, bm25=BM25Index.build(docs), fingerprint=corpus_fingerprint(docs))


def reset_cache() -> None:
    """Drop the in-process corpus cache (tests, or after Hermes 1 rewrites data/)."""
    _cached_corpus.cache_clear()


def corpus_documents() -> list[Document]:
    return _cached_corpus().docs


def _vector_index() -> VectorIndex | None:
    corpus = _cached_corpus()
    if not SETTINGS.embeddings_enabled:
        return None
    return try_load_or_build(corpus.docs, model=SETTINGS.embed_model)


def _rrf(*rankings: Sequence[tuple[int, float]], k: int = RRF_K) -> dict[int, float]:
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, (idx, _score) in enumerate(ranking, start=1):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank)
    return fused


def _order(fused: dict[int, float]) -> list[tuple[int, float]]:
    return sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))


def retrieve(
    query: str,
    *,
    lang: str = "es",
    k: int = 6,
    types: Iterable[str] | None = None,
    explain_scores: bool = False,
) -> list[dict[str, Any]]:
    """Search the corpus. Returns documents with ``score``, ``title``, ``url``, ``type``.

    ``lang`` only influences the tie-break (documents in the asked language win
    when the fused score is equal); it never filters the corpus out.
    """
    corpus = _cached_corpus()
    if not query or not query.strip() or k <= 0:
        return []
    wanted = {t for t in (types or []) if t}

    def keep(idx: int) -> bool:
        return not wanted or corpus.docs[idx].type in wanted

    # Query expansion: a student's "llueve" must reach the card named
    # "Precipitation Corrected". The lexicon only adds the seed's own long names
    # and ids to the query text; it never creates a document.
    expanded_query = query
    extra_terms = expansion_terms(query)
    if extra_terms:
        expanded_query = f"{query} {extra_terms}"

    bm25_rank = [(i, s) for i, s in corpus.bm25.search(expanded_query, limit=max(k * 8, 60)) if keep(i)]

    vec_rank: list[tuple[int, float]] = []
    backend = "bm25"
    vector_index = _vector_index()
    if vector_index is not None:
        try:
            qv = query_vector(query, model=SETTINGS.embed_model)
            id_to_idx = {d.id: i for i, d in enumerate(corpus.docs)}
            vec_rank = [
                (id_to_idx[vector_index.doc_ids[i]], s)
                for i, s in vector_index.search(qv, limit=max(k * 8, 60))
                if vector_index.doc_ids[i] in id_to_idx and keep(id_to_idx[vector_index.doc_ids[i]])
            ]
            backend = "rrf" if vec_rank else "bm25"
        except AIUnavailable:
            backend = "bm25"

    fused = _rrf(bm25_rank, vec_rank) if vec_rank else dict(
        (i, 1.0 / (RRF_K + r)) for r, (i, _s) in enumerate(bm25_rank, start=1)
    )

    # Lexical specificity: when a colloquial word maps cleanly onto one variable,
    # that card breaks ties (air temperature over skin temperature, etc.).
    # It can never lift a document that BM25 did not retrieve.
    prior = specificity_prior(query)
    weighted = {
        idx: score
        * (1.0 + 0.5 * max((prior.get(v, 0.0) for v in corpus.docs[idx].variables), default=0.0))
        * (1.0 if corpus.docs[idx].available else TIER_PLANNED_FACTOR)
        for idx, score in fused.items()
    }

    # Language and type are only healthy tie-breakers; the ranking above decides.
    ordered = sorted(
        weighted.items(),
        key=lambda kv: (-kv[1], 0 if corpus.docs[kv[0]].lang == lang else 1, corpus.docs[kv[0]].id),
    )

    results: list[dict[str, Any]] = []
    for idx, score in ordered[:k]:
        doc = corpus.docs[idx]
        payload = doc.to_public(score)
        if explain_scores:
            payload["backends"] = {
                "bm25_rank": next((r for r, (i, _s) in enumerate(bm25_rank, 1) if i == idx), None),
                "vector_rank": next((r for r, (i, _s) in enumerate(vec_rank, 1) if i == idx), None),
            }
        results.append(payload)

    if explain_scores:
        for item in results:
            item["meta"] = {"backend": backend, "fingerprint": corpus.fingerprint[:16]}
    return results


def retrieve_for_plan(question: str, *, lang: str = "es", k: int = 6) -> list[dict[str, Any]]:
    """What the planner sees as candidate variables (contract R3: 6 cards)."""
    cards = retrieve(question, lang=lang, k=k, types=["variable_card"])
    if len(cards) < k:
        extra = retrieve(question, lang=lang, k=k, types=["biome_profile", "region_note", "nasa_article"])
        seen = {c["id"] for c in cards}
        cards.extend(d for d in extra if d["id"] not in seen)
    return cards[:k]


def best_language(query: str) -> str:
    return detect_language(query)
