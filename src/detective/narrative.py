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

VALID_LEVELS = ("school", "highschool", "university", "uni")
MAX_PASSAGES = 5

def normalize_level(level: str | None) -> str:
    lvl = str(level or "").lower().strip()
    if lvl == "uni":
        return "university"
    return lvl if lvl in ("school", "highschool", "university") else "school"

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


def _variable_terms(analysis: dict[str, Any], lang: str) -> list[str]:
    """Everything we know about the analysed variable, most specific first."""
    variable = analysis.get("variable") or {}
    terms: list[str] = []
    names = variable.get("names")
    if isinstance(names, dict):
        for key in (lang, "en", "es"):
            value = names.get(key)
            if value:
                terms.append(str(value))
    elif names:
        terms.append(str(names))
    for key in ("id", "connector_param", "power_longname"):
        if variable.get(key):
            terms.append(str(variable[key]))
    return [t for i, t in enumerate(dict.fromkeys(terms)) if t]


def _documents_for_variable(variable_id: str, lang: str) -> list[dict[str, Any]]:
    """The analysed variable's own cards, in the requested language first.

    This is a direct corpus lookup, not a ranked search: when we know the id we do
    not need BM25 to guess, and the explanation must never quote the English card
    of a variable while answering in Spanish (RONDA_3 §4.1).
    """
    from .rag import corpus_documents

    if not variable_id:
        return []
    docs = [d for d in corpus_documents() if variable_id in d.variables]
    docs.sort(key=lambda d: (0 if d.lang == lang else 1, d.type != "variable_card", d.id))
    return [d.to_public(1.0) for d in docs]


def _passages_for(analysis: dict[str, Any], *, lang: str, k: int = MAX_PASSAGES) -> list[dict[str, Any]]:
    """Sources that are actually about the variable that was analysed.

    RONDA_2 §6.1: the old query was one bag of words, so "T2M Lima" came back as
    aerosol depth cards. Now we look the variable up directly, keep only documents
    that really carry that variable id, and add at most one regional article.
    """
    variable = analysis.get("variable") or {}
    region = analysis.get("region") or {}
    variable_id = str(variable.get("id") or "").strip()
    region_name = str(region.get("name") or "").strip()

    chosen: list[tuple[Any, str]] = []
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()

    def _take(doc: dict[str, Any], role: str) -> bool:
        if doc["id"] in seen_ids:
            return False
        # The same page in two languages, or twice from two files, is one source.
        source_key = (doc.get("url") or "").split("?")[0].rstrip("/")
        if source_key and source_key in seen_sources:
            return False
        seen_ids.add(doc["id"])
        if source_key:
            seen_sources.add(source_key)
        chosen.append((doc, role))
        return True

    # 1) The variable's own cards, in the requested language (direct lookup).
    for doc in _documents_for_variable(variable_id, lang):
        if doc["type"] != "variable_card":
            continue
        _take(doc, "variable")
        if sum(1 for _d, r in chosen if r == "variable") >= 1:
            break

    # 2) A regional article, only from the requested language and the same region.
    if region_name:
        region_key = region_name.lower().split(",")[0].strip()
        for doc in retrieve(region_name, lang=lang, k=8, types=["nasa_article", "region_note"]):
            if region_key not in (doc.get("title") or "").lower():
                continue
            if variable_id and variable_id not in (doc.get("variables") or []):
                continue
            if _take(doc, "context"):
                break

    # 3) A method note in the requested language fits any variable.
    for doc in retrieve("trend significance Mann-Kendall", lang=lang, k=6, types=["method_note"]):
        if doc.get("lang") != lang:
            continue
        _take(doc, "method")
        break

    return [
        {
            "n": i,
            "id": doc["id"],
            "title": doc["title"],
            "url": doc["url"],
            "type": doc["type"],
            "lang": doc.get("lang"),
            "publisher": doc.get("publisher"),
            "role": role,
            "text": doc["text"],
        }
        for i, (doc, role) in enumerate(chosen[:k], start=1)
    ]


def _answer(analysis: dict[str, Any], key: str, lang: str) -> str:
    answers = analysis.get("answers") or {}
    block = answers.get(key) or {}
    if isinstance(block, str):
        return block
    return str(block.get(lang) or block.get("en") or "").strip()


def _school_first_paragraph(analysis: dict[str, Any], lang: str) -> str:
    parts = [p for p in (
        _answer(analysis, "what", lang),
        _answer(analysis, "where", lang),
        _answer(analysis, "how_much", lang),
        _answer(analysis, "significant", lang),
        _answer(analysis, "detectability", lang),
    ) if p]
    return " ".join(parts) if parts else _fallback_summary(analysis, lang)


def _highschool_first_paragraph(analysis: dict[str, Any], lang: str) -> str:
    period = analysis.get("period") or {}
    trend = analysis.get("trend") or {}
    if not trend or "sen_slope_per_decade" not in trend:
        return _school_first_paragraph(analysis, lang)

    var = (analysis.get("variable") or {}).get("names") or {}
    var_name = var.get(lang) or var.get("es") or (analysis.get("variable") or {}).get("id") or "Variable"
    reg = (analysis.get("region") or {}).get("name") or "la región"
    unit = (analysis.get("variable") or {}).get("unit") or ""
    sig = analysis.get("significance") or {}
    det = analysis.get("detectability") or {}

    start_y = str(period.get("start", ""))[:4]
    end_y = str(period.get("end", ""))[:4]
    years = period.get("years")
    years_str = f"{int(years)}" if years and years == int(years) else f"{years}"
    slope = trend.get("sen_slope_per_decade")
    total_change = trend.get("total_change")
    is_sig = sig.get("is_significant", False)
    sig_level = sig.get("level") or ""
    years_needed = det.get("years_needed")
    years_needed_str = f"{int(years_needed)}" if years_needed and years_needed == int(years_needed) else f"{years_needed}"

    if lang == "es":
        sig_phrase = f"es estadísticamente significativa ({sig_level}), superando el ruido climático habitual" if is_sig else "no alcanza significancia estadística y puede deberse a variaciones naturales"
        det_phrase = f"con {years_str} años de registro que superan el mínimo necesario ({years_needed_str} años)" if not det.get("more_years_needed") else f"aunque se proyectan necesarios {years_needed_str} años para una confirmación definitiva"
        return (
            f"Nivel secundaria: En {reg}, el registro de {var_name} de {start_y} a {end_y} ({years_str} años) "
            f"indica un ritmo de cambio estimado en {slope} {unit} por década, acumulando una variación de {total_change} {unit}. "
            f"La tendencia {sig_phrase}, {det_phrase}."
        )
    else:
        sig_phrase = f"is statistically significant ({sig_level}), exceeding typical climate noise" if is_sig else "does not reach statistical significance and may reflect natural fluctuations"
        det_phrase = f"with {years_str} years of record exceeding the required threshold ({years_needed_str} years)" if not det.get("more_years_needed") else f"although an estimated {years_needed_str} years are projected for definitive confirmation"
        return (
            f"High school level: In {reg}, the {var_name} record from {start_y} to {end_y} ({years_str} years) "
            f"indicates an estimated rate of change of {slope} {unit} per decade, accumulating a variation of {total_change} {unit}. "
            f"The trend {sig_phrase}, {det_phrase}."
        )


def _university_first_paragraph(analysis: dict[str, Any], lang: str) -> str:
    period = analysis.get("period") or {}
    trend = analysis.get("trend") or {}
    if not trend or "sen_slope_per_decade" not in trend:
        return _school_first_paragraph(analysis, lang)

    var = (analysis.get("variable") or {}).get("names") or {}
    var_name = var.get(lang) or var.get("es") or (analysis.get("variable") or {}).get("id") or "Variable"
    reg = (analysis.get("region") or {}).get("name") or "la región"
    unit = (analysis.get("variable") or {}).get("unit") or ""
    tests = analysis.get("tests") or {}
    sig = analysis.get("significance") or {}
    det = analysis.get("detectability") or {}

    start_y = str(period.get("start", ""))[:4]
    end_y = str(period.get("end", ""))[:4]
    years = period.get("years")
    years_str = f"{int(years)}" if years and years == int(years) else f"{years}"
    n_obs = period.get("n_obs")

    slope = trend.get("sen_slope_per_decade")
    ci = trend.get("sen_ci95_per_decade")
    ci_str = f" (intervalo de confianza entre {ci[0]} y {ci[1]} {unit}/década)" if ci and len(ci) == 2 else ""
    ci_str_en = f" (confidence interval between {ci[0]} and {ci[1]} {unit}/decade)" if ci and len(ci) == 2 else ""
    total_change = trend.get("total_change")

    mk = tests.get("mann_kendall") or {}
    tau = mk.get("tau")
    tau_str = f" (tau = {tau})" if tau is not None else ""
    sig_level = sig.get("level") or ""
    is_sig = sig.get("is_significant", False)

    years_needed = det.get("years_needed")
    years_needed_str = f"{int(years_needed)}" if years_needed and years_needed == int(years_needed) else f"{years_needed}"

    if lang == "es":
        sig_phrase = f"un comportamiento estadísticamente significativo con nivel {sig_level}" if is_sig else "una variación que no es estadísticamente significativa"
        det_phrase = f"supera el umbral necesario de {years_needed_str} años" if not det.get("more_years_needed") else f"requiere {years_needed_str} años estimados"
        return (
            f"Evaluación universitaria y técnica: Para {var_name} en {reg} ({start_y} a {end_y}, {n_obs} observaciones), "
            f"la regresión robusta de Theil-Sen estima una pendiente de {slope} {unit}/década{ci_str}, "
            f"acumulando un cambio neto de {total_change} {unit} a lo largo de {years_str} años. "
            f"En la inferencia no paramétrica de Mann-Kendall con corrección por autocorrelación serial, el análisis determina "
            f"{sig_phrase}{tau_str}. "
            f"En el marco de detectabilidad climática de Weatherhead et al., la longitud del registro ({years_str} años) "
            f"{det_phrase} para emerger de la variabilidad natural."
        )
    else:
        sig_phrase = f"statistically significant behavior at level {sig_level}" if is_sig else "variation that is not statistically significant"
        det_phrase = f"exceeds the required threshold of {years_needed_str} years" if not det.get("more_years_needed") else f"requires an estimated {years_needed_str} years"
        return (
            f"University technical evaluation: For {var_name} in {reg} ({start_y} to {end_y}, {n_obs} observations), "
            f"the robust Theil-Sen estimator yields a slope of {slope} {unit}/decade{ci_str_en}, "
            f"with a net cumulative change of {total_change} {unit} across {years_str} years. "
            f"Under non-parametric Mann-Kendall inference adjusted for serial autocorrelation, the analysis identifies "
            f"{sig_phrase}{tau_str}. "
            f"In the Weatherhead et al. climate detectability framework, the record length ({years_str} years) "
            f"{det_phrase} to emerge from natural background noise."
        )


def extractive_text(analysis: dict[str, Any], *, level: str = "school", lang: str = "es", passages: list[dict[str, Any]]) -> str:
    """Deterministic template: the app's own `answers` plus short, attributed quotes."""
    norm_level = normalize_level(level)
    if norm_level == "university":
        first = _university_first_paragraph(analysis, lang)
    elif norm_level == "highschool":
        first = _highschool_first_paragraph(analysis, lang)
    else:
        first = _school_first_paragraph(analysis, lang)

    second_lines: list[str] = []
    for p in passages:
        # A short quoted sentence, then the source it came from with its real URL.
        quote = _first_sentence(p["text"], limit=180)
        source = p.get("publisher") or p.get("type") or ""
        attrib = f" — {source}" if source else ""
        second_lines.append(f"[{p['n']}] {p['title']}{attrib}: \"{quote}\"\n     {p['url'] or ''}".rstrip())
    second = "\n".join(second_lines) if second_lines else (
        "No hay fuentes recuperadas para este caso." if lang == "es" else "No sources were retrieved for this case."
    )
    return f"{first}\n\n{second}"


def _first_sentence(text: str, *, limit: int) -> str:
    """A complete sentence from the document, trimmed to ``limit`` characters."""
    clean = " ".join(str(text).split())
    if not clean:
        return ""
    for end in (". ", "! ", "? "):
        idx = clean.find(end)
        if 0 < idx <= limit:
            return clean[: idx + 1]
    return _clip(clean, limit)


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


def _public_citation(p: dict[str, Any]) -> dict[str, Any]:
    """A human-readable citation: real title, real URL, real publisher — no internal ids.

    RONDA_2 §6.1: the UI was showing ``[var-aod_55-es]`` and labelling every source
    "NASA Earth Observatory". The id stays in the payload for tracing, but the
    title/url/publisher now come from the document that was actually quoted.
    """
    return {
        "n": p["n"],
        "title": p["title"],
        "url": p["url"],
        "publisher": p.get("publisher") or "",
        "source_id": p["id"],
    }


def _citations(text: str, passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from .guard import CITATION_RE

    used = sorted({int(n) for n in CITATION_RE.findall(text)})
    by_n = {p["n"]: p for p in passages}
    return [_public_citation(by_n[n]) for n in used if n in by_n]


def _all_citations(passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_public_citation(p) for p in passages]


def explain(analysis: dict, *, level: str = "school", lang: str = "es") -> dict[str, Any]:
    """Two paragraphs the student can quote, with the guard's verdict attached."""
    level = normalize_level(level)
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
        text = extractive_text(analysis, level=level, lang=lang, passages=passages)
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

    text = extractive_text(analysis, level=level, lang=lang, passages=passages)
    verdict = run_guard(text, facts=facts, passages=passages, lang=lang, is_significant=significant)
    return {
        "text": text,
        "citations": _all_citations(passages),
        "guard": verdict.to_public(),
        "mode": "extractive",
    }
