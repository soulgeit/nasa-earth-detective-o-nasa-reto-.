# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Okapi BM25 over the detective corpus. Pure Python, no dependencies.

Parameters follow the common defaults (k1=1.5, b=0.75); they were tuned on the
provisional golden set in tests/detective/golden_questions.provisional.jsonl —
see docs/EVAL_IA.md for the measured table.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from .corpus import Document
from .text_norm import normalize_terms


@dataclass
class BM25Index:
    docs: list[Document]
    postings: dict[str, dict[int, int]]
    doc_len: list[int]
    avg_len: float
    k1: float = 1.5
    b: float = 0.75

    @classmethod
    def build(cls, docs: list[Document], *, k1: float = 1.5, b: float = 0.75) -> "BM25Index":
        postings: dict[str, dict[int, int]] = {}
        doc_len: list[int] = []
        for idx, doc in enumerate(docs):
            terms = normalize_terms(doc.searchable())
            doc_len.append(len(terms))
            for term, freq in Counter(terms).items():
                postings.setdefault(term, {})[idx] = freq
        avg = (sum(doc_len) / len(doc_len)) if doc_len else 0.0
        return cls(docs=docs, postings=postings, doc_len=doc_len, avg_len=avg, k1=k1, b=b)

    def _idf(self, term: str) -> float:
        n_docs = len(self.docs)
        df = len(self.postings.get(term, {}))
        if df == 0:
            return 0.0
        # BM25+ style floor keeps multi-word queries from scoring zero on common terms.
        return math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))

    def search(self, query: str, *, limit: int | None = None) -> list[tuple[int, float]]:
        terms = normalize_terms(query)
        if not terms or not self.docs:
            return []
        scores: dict[int, float] = {}
        for term in terms:
            hits = self.postings.get(term)
            if not hits:
                continue
            idf = self._idf(term)
            for idx, freq in hits.items():
                dl = self.doc_len[idx] or 1
                denom = freq + self.k1 * (1 - self.b + self.b * dl / (self.avg_len or 1))
                scores[idx] = scores.get(idx, 0.0) + idf * (freq * (self.k1 + 1)) / denom
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return ranked[:limit] if limit else ranked
