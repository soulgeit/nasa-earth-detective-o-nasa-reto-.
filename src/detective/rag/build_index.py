# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Rebuild the vector index:  python -m src.detective.rag.build_index"""

from __future__ import annotations

import argparse
import sys

from ..config import SETTINGS
from ..corpus import corpus_fingerprint, load_corpus
from ..llm import AIUnavailable
from .embeddings import build, index_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the detective vector index (.npz).")
    parser.add_argument("--model", default=SETTINGS.embed_model, help="embedding model served by EMBED_BASE_URL")
    parser.add_argument("--force", action="store_true", help="rebuild even if the cached index matches")
    args = parser.parse_args(argv)

    docs = load_corpus()
    print(f"corpus: {len(docs)} documents, fingerprint {corpus_fingerprint(docs)[:16]}")
    by_type: dict[str, int] = {}
    for d in docs:
        by_type[d.type] = by_type.get(d.type, 0) + 1
    print("by type:", dict(sorted(by_type.items())))
    print("by lang:", {lg: sum(1 for d in docs if d.lang == lg) for lg in ("es", "en")})

    if not docs:
        print("ERROR: empty corpus — nothing to index", file=sys.stderr)
        return 2
    if not args.model:
        print("EMBED_MODEL is empty: BM25 alone is a supported configuration (contract §11).", file=sys.stderr)
        return 3
    if index_path(args.model).exists() and not args.force:
        print(f"index already present at {index_path(args.model)} (use --force to rebuild)")
        return 0
    try:
        index = build(docs, model=args.model)
    except AIUnavailable as exc:
        print(f"ERROR: embedding service unavailable: {exc}", file=sys.stderr)
        print("The detective keeps working with BM25 only; retry once Ollama serves the model.", file=sys.stderr)
        return 4
    print(f"built {index.matrix.shape[0]}x{index.matrix.shape[1]} index -> {index_path(args.model)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
