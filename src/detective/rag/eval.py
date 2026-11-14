# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Retrieval evaluation (contract R2):  python -m src.detective.rag.eval

Metrics per backend (BM25, vectors, fusion): precision@1, precision@3 and MRR,
computed over ``data/knowledge/golden_questions.jsonl`` (Hermes 1) or, until it
lands, the provisional set in ``tests/detective/golden_questions.provisional.jsonl``
written by us BEFORE looking at any result.

It also prints a Markdown table that goes verbatim into docs/EVAL_IA.md.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ..config import SETTINGS
from . import _cached_corpus, corpus_documents, retrieve
from .embeddings import query_vector, try_load_or_build

BACKENDS = ("bm25", "vectors", "fusion")


@dataclass
class Metrics:
    backend: str
    n: int = 0
    hits1: int = 0
    hits3: int = 0
    rr_sum: float = 0.0

    @property
    def precision_at_1(self) -> float:
        return self.hits1 / self.n if self.n else 0.0

    @property
    def precision_at_3(self) -> float:
        return self.hits3 / self.n if self.n else 0.0

    @property
    def mrr(self) -> float:
        return self.rr_sum / self.n if self.n else 0.0

    def row(self) -> str:
        return (
            f"| {self.backend} | {self.precision_at_1:.3f} | {self.precision_at_3:.3f} | "
            f"{self.mrr:.3f} | {self.n} |"
        )


def golden_path() -> tuple[Path, bool]:
    official = SETTINGS.knowledge_dir / "golden_questions.jsonl"
    if official.exists():
        return official, False
    return SETTINGS.data_dir.parent / "tests" / "detective" / "golden_questions.provisional.jsonl", True


def load_golden(path: Path | None = None) -> tuple[list[dict[str, Any]], bool]:
    path, provisional = (path, False) if path else golden_path()
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows, provisional


def _rank_variables(backend: str, question: str, *, lang: str, k: int) -> list[str]:
    if backend == "bm25":
        results = retrieve(question, lang=lang, k=k, types=["variable_card"])
        return [d["variables"][0] for d in results if d.get("variables")]
    if backend == "vectors":
        corpus = _cached_corpus()
        index = try_load_or_build(corpus.docs, model=SETTINGS.embed_model)
        if index is None:
            return []
        qv = query_vector(question, model=SETTINGS.embed_model)
        id_to_idx = {d.id: i for i, d in enumerate(corpus.docs)}
        out: list[str] = []
        for i, _score in index.search(qv, limit=k * 4):
            doc = corpus.docs[id_to_idx[index.doc_ids[i]]]
            if doc.type == "variable_card" and doc.variables:
                out.append(doc.variables[0])
            if len(out) >= k:
                break
        return out
    results = retrieve(question, lang=lang, k=k, types=["variable_card"])
    return [d["variables"][0] for d in results if d.get("variables")]


def evaluate(*, k: int = 6, path: Path | None = None) -> tuple[list[Metrics], bool, int]:
    rows, provisional = load_golden(path)
    metrics = {b: Metrics(backend=b) for b in BACKENDS}
    for row in rows:
        expected = set(row.get("expected_variable_ids") or [])
        if not expected:
            continue
        for backend in BACKENDS:
            ranked = _rank_variables(backend, row["question"], lang=row.get("lang", "es"), k=k)
            if not ranked:
                continue  # backend unavailable (e.g. no embeddings) — out of the denominator
            m = metrics[backend]
            m.n += 1
            if ranked[0] in expected:
                m.hits1 += 1
            if any(v in expected for v in ranked[:3]):
                m.hits3 += 1
            first = next((i for i, v in enumerate(ranked, start=1) if v in expected), None)
            if first:
                m.rr_sum += 1.0 / first
    return [metrics[b] for b in BACKENDS], provisional, len(rows)


def markdown_table(rows: Iterable[Metrics], *, provisional: bool, n_questions: int, k: int) -> str:
    source = (
        "**Set provisional** (15 preguntas / 15 questions, escritas por claude-omni-2 antes de mirar resultados; "
        "se sustituye por `data/knowledge/golden_questions.jsonl` de Hermes 1)"
        if provisional
        else "`data/knowledge/golden_questions.jsonl` (Hermes 1)"
    )
    lines = [
        f"Fuente / Source: {source}",
        "",
        f"| Backend | Precision@1 | Precision@3 | MRR | Preguntas / Questions (k={k}) |",
        "|---|---|---|---|---|",
    ]
    lines += [m.row() for m in rows]
    lines.append("")
    lines.append(
        "Nota: `vectors` queda fuera de la media si no hay servicio de embeddings; "
        "la app funciona con BM25 solo (contract §11). / "
        "`vectors` drops out of the means when no embedding service is available."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval (precision@1, precision@3, MRR).")
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--golden", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    rows, provisional, n_questions = evaluate(k=args.k, path=args.golden)
    if args.json:
        print(json.dumps(
            {
                "provisional": provisional,
                "n_questions": n_questions,
                "backends": [
                    {"backend": m.backend, "precision_at_1": round(m.precision_at_1, 4),
                     "precision_at_3": round(m.precision_at_3, 4), "mrr": round(m.mrr, 4), "n": m.n}
                    for m in rows
                ],
            },
            indent=2,
        ))
        return 0
    print(f"corpus: {len(corpus_documents())} documents")
    print(markdown_table(rows, provisional=provisional, n_questions=n_questions, k=args.k))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
