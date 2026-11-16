# SI-assisted: cfable (Claude Sonnet 5.5)
"""Facts for the "how Huiracocha IA works" panel (RONDA_7).

Every number below is computed from the live corpus, the catalogue and the
settings of THIS process. Nothing about the deployment is typed by hand, so the
panel can never claim more than the server really has: when the LoRA planner is
not loaded it says so, and says what answers instead.

The only fixed figures are the LoRA training and evaluation numbers, copied from
``src/ml/MODEL_CARD.md`` and ``docs/EVAL_IA.md`` (measured by the lanes that
trained and evaluated the adapter) and pointed back to them.
"""

from __future__ import annotations

import importlib.util
from collections import Counter
from functools import lru_cache
from typing import Any

from .config import REPO_ROOT, SETTINGS

CITIES = (
    ("lima", "Lima"),
    ("huancayo", "Huancayo"),
    ("andahuaylas", "Andahuaylas"),
    ("ica", "Ica"),
    ("ayacucho", "Ayacucho"),
)

# src/ml/MODEL_CARD.md (training metadata recorded in reports/lora/train_meta.json)
# and docs/EVAL_IA.md. Rule 20: the adapter is always quoted with BOTH benchmarks.
LORA_FACTS: dict[str, Any] = {
    "base_model": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    "license": "Apache-2.0",
    "method": "QLoRA (4-bit NF4), rank 16, alpha 32",
    "trainable_params": 6_291_456,
    "train_examples": 4_323,
    "train_steps": 150,
    "train_seconds": 353.7,
    "hardware": "NVIDIA GeForce RTX 4070 SUPER (12 GB)",
    "adapter_bytes": 25_191_536,
    "sha256": "70314779040b656cc8ed5e4dac0f4285bd9efc7b392acfa870b003794327341c",
    "reference_questions": {"total": 50, "rules": 50, "lora_gpu": 40, "lora_cpu": 37},
    "synthetic_cases": {"total": 200, "exact_variable_pct": {"base": 4.5, "rules": 15.5, "lora": 84.5}},
    "sources": ["src/ml/MODEL_CARD.md", "docs/EVAL_IA.md"],
}


def engine_for(*, configured: bool, runtime: bool, adapter: bool, state: str) -> str:
    """"lora+rag" only once the adapter has really loaded or answered; never on a promise."""
    return "lora+rag" if (configured and runtime and adapter and state == "ready") else "rules+rag"


def _lora_runtime() -> dict[str, Any]:
    """Whether the LoRA planner can really answer in this process, and in which state."""
    from .planner import lora_status

    adapter = (REPO_ROOT / "models" / "etd-planner-lora" / "adapter_config.json").exists()
    runtime = all(importlib.util.find_spec(name) is not None for name in ("torch", "peft", "transformers"))
    configured = SETTINGS.ai_mode == "full" and (SETTINGS.planner_model or "").strip().lower() in (
        "local-lora", "local_lora", "lora",
    )
    status = lora_status()
    return {
        "adapter_present": adapter,
        "runtime_present": runtime,
        "configured": configured,
        "state": status["state"],  # idle | loading | ready | failed
        "active": engine_for(configured=configured, runtime=runtime, adapter=adapter, state=status["state"]) == "lora+rag",
    }


def _corpus_block(docs: list[Any]) -> dict[str, Any]:
    by_type = Counter(d.type for d in docs)
    publishers = {d.publisher for d in docs if d.publisher}
    urls = {d.url for d in docs if d.url}
    cities = []
    for city_id, name in CITIES:
        mine = [d for d in docs if city_id in (d.places or [])]
        cities.append({
            "id": city_id,
            "name": name,
            "docs": len(mine),
            "es": sum(1 for d in mine if d.lang == "es"),
            "en": sum(1 for d in mine if d.lang == "en"),
            "sources": len({d.url for d in mine if d.url}),
            "publishers": len({d.publisher for d in mine if d.publisher}),
            "computed_facts": sum(1 for d in mine if d.id.startswith("fact-")),
        })
    return {
        "documents": len(docs),
        "languages": dict(Counter(d.lang for d in docs)),
        "by_type": dict(by_type),
        "publishers": len(publishers),
        "sources": len(urls),
        "cities": cities,
    }


def _resources(docs: list[Any], lang: str) -> list[dict[str, Any]]:
    """The platforms of the challenge brief that the corpus documents (one per URL)."""
    wanted = [d for d in docs if d.id.startswith("res-platforms-") or d.id.startswith("res-csa-")]
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for doc in sorted(wanted, key=lambda d: (0 if d.lang == lang else 1, d.id)):
        key = (doc.url or doc.id).split("?")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append({"id": doc.id, "title": doc.title, "url": doc.url, "publisher": doc.publisher})
    return out


def _catalog_block() -> dict[str, Any]:
    from .corpus import load_catalog_cards

    cards = load_catalog_cards()
    available = [c for c, ok in cards if ok]
    return {
        "available": len(available),
        "planned": sum(1 for _c, ok in cards if not ok),
        "spheres": dict(Counter(str(c.get("sphere") or "atmosphere") for c in available)),
    }


@lru_cache(maxsize=4)
def _static_block(lang: str) -> dict[str, Any]:
    """The parts that only change when the corpus does (cached per language)."""
    from .corpus import FRAGMENT_ERRORS
    from .rag import corpus_documents

    docs = corpus_documents()
    return {
        "corpus": _corpus_block(docs) | {"skipped_rows": len(FRAGMENT_ERRORS)},
        "catalog": _catalog_block(),
        "resources": _resources(docs, lang),
    }


def _llm_block() -> dict[str, Any]:
    """The hosted model, if any: configured, and only "ready" after a call really succeeded."""
    from . import llm as llm_client

    local_lora = (SETTINGS.planner_model or "").strip().lower() in ("local-lora", "local_lora", "lora")
    plans = bool(SETTINGS.planner_model) and not local_lora
    explains = bool(SETTINGS.explain_model)
    configured = bool(SETTINGS.ai_mode == "full" and SETTINGS.llm_hosted and (plans or explains))
    last_ok = llm_client.status()["last_ok"]
    if not configured:
        state = "off"
    elif last_ok is True:
        state = "ready"
    elif last_ok is False:
        state = "failing"
    else:
        state = "configured"
    return {
        "configured": configured,
        "state": state,  # off | configured | ready | failing
        "host": llm_client.host() if configured else None,
        "plans": configured and plans,
        "explains": configured and explains,
    }


def about(*, lang: str = "es") -> dict[str, Any]:
    static = _static_block(lang)
    lora = _lora_runtime()
    llm = _llm_block()
    if lora["active"]:
        engine = "lora+rag"
    elif llm["state"] == "ready":
        engine = "llm+rag"
    else:
        engine = "rules+rag"
    return {
        "schema": "about/1",
        "assistant": {"name": "Huiracocha IA", "named_after": "Wiracocha"},
        "deployment": {
            "ai_mode": SETTINGS.ai_mode,
            "engine": engine,
            "planner": "lora" if lora["active"] else ("llm" if engine == "llm+rag" and llm["plans"] else "rules"),
            "lora": lora,
            "llm": llm,
            "generative_text": bool(engine == "llm+rag" and llm["explains"]),
            "embeddings": bool(SETTINGS.embeddings_enabled),
        },
        "pipeline": ["question", "retrieval", "plan", "nasa_data", "statistics", "explanation"],
        "retrieval": {"method": "BM25 + colloquial lexicon" + (" + embeddings (RRF)" if SETTINGS.embeddings_enabled else "")},
        "corpus": static["corpus"],
        "catalog": static["catalog"],
        "lora": LORA_FACTS,
        "resources": static["resources"],
    }


def reset_cache() -> None:
    _static_block.cache_clear()
