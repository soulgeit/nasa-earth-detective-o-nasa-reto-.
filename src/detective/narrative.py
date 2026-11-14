# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Explanation with a guard (contract R6).

    AnalysisResult v2 + 3-5 retrieved passages
          ├─ [full]  EXPLAIN_MODEL -> 2 paragraphs, [n] citations
          │            └─ guard ─retry once─> rejected -> extractive fallback
          └─ [extractive] deterministic template from `analysis["answers"]`
                          + passages quoted verbatim

The extractive path is the contract's floor: with AI_MODE=extractive and no model
at all, the student still gets an honest, sourced answer with zero invented numbers.
"""

from __future__ import annotations

import json
from typing import Any

from .config import SETTINGS
from .guard import GuardResult, run_guard
from .llm import AIUnavailable, chat
from .rag import retrieve

VALID_LEVELS = ("school", "highschool", "university")
MAX_PASSAGES = 5

_LEVEL_HINT = {
    "school": "Explain for a 12-year-old: short sentences, no jargon.",
    "highschool": "Explain for a 16-year-old: introduce the technical words you use.",
    "university": "Explain for an undergraduate: be precise, name the method and its limits.",
}


def _facts(analysis: dict[str, Any]) -> dict[str, Any]:
    """The closed list of facts the model may use. Nothing else is allowed."""
    return {
        "variable": (analysis.get("variable") or {}).get("names") or (analysis.get("variable") or {}).get("id"),
        "region": (analysis.get("region") or {}).get("name"),
        "unit": (analysis.get("variable") or {}).get("unit"),
        "period": analysis.get("period"),
        "trend": analysis.get("trend"),
        "tests": analysis.get("tests"),
        "significance": analysis.get("significance"),
        "detectability": analysis.get("detectability"),
        "warnings": analysis.get("warnings"),
    }


def _is_significant(analysis: dict[str, Any]) -> bool | None:
    sig = analysis.get("significance") or {}
    value = sig.get("is_significant")
    return value if isinstance(value, bool) else None


def _passages_for(analysis: dict[str, Any], *, lang: str, k: int = MAX_PASSAGES) -> list[dict[str, Any]]:
    variable = analysis.get("variable") or {}
    region = analysis.get("region") or {}
    name = variable.get("names")
    if isinstance(name, dict):
        name = name.get(lang) or name.get("en")
    query = " ".join(str(x) for x in (name, variable.get("id"), region.get("name")) if x)
    docs = retrieve(query, lang=lang, k=k)
    return [
        {
            "n": i,
            "id": d["id"],
            "title": d["title"],
            "url": d["url"],
            "type": d["type"],
            "text": d["text"],
        }
        for i, d in enumerate(docs, start=1)
    ]


def _answer(analysis: dict[str, Any], key: str, lang: str) -> str:
    answers = analysis.get("answers") or {}
    block = answers.get(key) or {}
    if isinstance(block, str):
        return block
    return str(block.get(lang) or block.get("en") or "").strip()


def extractive_text(analysis: dict[str, Any], *, lang: str, passages: list[dict[str, Any]]) -> str:
    """Deterministic template: the app's own `answers` plus verbatim quotes."""
    parts = [p for p in (
        _answer(analysis, "what", lang),
        _answer(analysis, "where", lang),
        _answer(analysis, "how_much", lang),
        _answer(analysis, "significant", lang),
        _answer(analysis, "detectability", lang),
    ) if p]
    first = " ".join(parts) if parts else _fallback_summary(analysis, lang)

    second_lines: list[str] = []
    for p in passages:
        label = "Fragmento" if lang == "es" else "Passage"
        second_lines.append(f"[{p['n']}] {p['title']}: \"{_clip(p['text'], 220)}\"")
        _ = label
    second = "\n".join(second_lines) if second_lines else (
        "No hay fuentes recuperadas para este caso." if lang == "es" else "No sources were retrieved for this case."
    )
    return f"{first}\n\n{second}"


def _fallback_summary(analysis: dict[str, Any], lang: str) -> str:
    trend = analysis.get("trend") or {}
    period = analysis.get("period") or {}
    if lang == "es":
        return (
            f"El análisis cubre {period.get('start', '?')} a {period.get('end', '?')} con "
            f"{period.get('n_obs', '?')} observaciones."
        )
    return (
        f"The analysis covers {period.get('start', '?')} to {period.get('end', '?')} with "
        f"{period.get('n_obs', '?')} observations."
    )


def _clip(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _prompt(analysis: dict[str, Any], passages: list[dict[str, Any]], *, lang: str, level: str) -> str:
    facts = json.dumps(_facts(analysis), ensure_ascii=False, sort_keys=True)
    passage_block = "\n".join(
        f"[{p['n']}] {p['title']} ({p['url']})\n{p['text']}" for p in passages
    )
    if lang == "es":
        return (
            "Eres un asistente científico. Escribe EXACTAMENTE dos párrafos en español.\n"
            "Párrafo 1: qué dicen los datos, usando SOLO las cifras de HECHOS (cópialas tal cual).\n"
            "Párrafo 2: posibles causas como HIPÓTESIS; cada frase que use un fragmento lleva su cita [n].\n"
            "Prohibido: cifras nuevas, coordenadas, fuentes que no estén abajo, palabras como "
            "'demuestra' o 'sin duda' si el veredicto no es significativo.\n"
            f"Nivel: {level}. {_LEVEL_HINT.get(level, '')}\n\n"
            f"HECHOS (JSON, cerrado):\n{facts}\n\nFRAGMENTOS:\n{passage_block}"
        )
    return (
        "You are a science assistant. Write EXACTLY two paragraphs in English.\n"
        "Paragraph 1: what the data says, using ONLY the numbers in FACTS (copy them as given).\n"
        "Paragraph 2: possible causes as HYPOTHESES; every sentence using a passage carries its [n] citation.\n"
        "Forbidden: new numbers, coordinates, sources not listed below, and 'proves'/'confirms' "
        "when the verdict is not significant.\n"
        f"Level: {level}. {_LEVEL_HINT.get(level, '')}\n\n"
        f"FACTS (closed JSON):\n{facts}\n\nPASSAGES:\n{passage_block}"
    )


def _citations(text: str, passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from .guard import CITATION_RE

    used = sorted({int(n) for n in CITATION_RE.findall(text)})
    by_n = {p["n"]: p for p in passages}
    return [
        {"n": n, "title": by_n[n]["title"], "url": by_n[n]["url"], "id": by_n[n]["id"]}
        for n in used
        if n in by_n
    ]


def _all_citations(passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"n": p["n"], "title": p["title"], "url": p["url"], "id": p["id"]} for p in passages]


def explain(analysis: dict, *, level: str = "school", lang: str = "es") -> dict[str, Any]:
    """Two paragraphs the student can quote, with the guard's verdict attached."""
    level = level if level in VALID_LEVELS else "school"
    lang = lang if lang in ("es", "en") else "es"
    if not isinstance(analysis, dict) or not analysis:
        return {
            "text": "No hay análisis que explicar." if lang == "es" else "There is no analysis to explain.",
            "citations": [],
            "guard": {"numbers_ok": True, "citations_ok": True, "language_ok": True,
                      "no_overclaim": True, "retries": 0, "reasons": []},
            "mode": "extractive",
        }

    passages = _passages_for(analysis, lang=lang)
    significant = _is_significant(analysis)
    facts = _facts(analysis)

    if SETTINGS.ai_mode == "full" and SETTINGS.explain_model:
        messages = [
            {"role": "system", "content": _LEVEL_HINT.get(level, "")},
            {"role": "user", "content": _prompt(analysis, passages, lang=lang, level=level)},
        ]
        last: GuardResult | None = None
        for attempt in range(2):
            try:
                text = chat(messages, model=SETTINGS.explain_model, temperature=0.2).strip()
            except AIUnavailable as exc:
                break
            verdict = run_guard(text, facts=facts, passages=passages, lang=lang,
                               is_significant=significant, retries=attempt)
            if verdict.ok:
                return {
                    "text": text,
                    "citations": _citations(text, passages),
                    "guard": verdict.to_public(),
                    "mode": "llm",
                }
            last = verdict
            messages = messages[:2] + [
                {
                    "role": "user",
                    "content": (
                        f"Rejected: {'; '.join(verdict.reasons)}. Rewrite the two paragraphs obeying every rule."
                        if lang == "en"
                        else f"Rechazado: {'; '.join(verdict.reasons)}. Reescribe los dos párrafos cumpliendo las reglas."
                    ),
                }
            ]
        text = extractive_text(analysis, lang=lang, passages=passages)
        verdict = run_guard(text, facts=facts, passages=passages, lang=lang,
                            is_significant=significant, retries=2)
        payload_guard = verdict.to_public()
        if last is not None:
            payload_guard["llm_attempts_rejected"] = last.to_public()
        return {
            "text": text,
            "citations": _all_citations(passages),
            "guard": payload_guard,
            "mode": "extractive",
        }

    text = extractive_text(analysis, lang=lang, passages=passages)
    verdict = run_guard(text, facts=facts, passages=passages, lang=lang, is_significant=significant)
    return {
        "text": text,
        "citations": _all_citations(passages),
        "guard": verdict.to_public(),
        "mode": "extractive",
    }
