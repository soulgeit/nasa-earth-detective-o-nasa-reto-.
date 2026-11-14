# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""The planner (contract R3 + §10).

    retrieve(6 cards) ─► [full] model PLANNER_MODEL, JSON-constrained
                            └─ hard validation ─ retry once ─ fallback
                       [extractive] rules over the same retrieval
                                                ▼
                                        InvestigationPlan

Every plan says which path produced it: ``"mode": "lora" | "llm" | "rules"``.
The model never invents a variable_id: it may only pick from the candidates we
retrieved, and ``place`` must be a literal substring of the question.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from .config import SETTINGS
from .gazetteer import geocode
from .lexicon import expand, specificity_prior
from .llm import AIUnavailable, chat
from .places import extract_places
from .rag import retrieve_for_plan
from .text_norm import detect_language, fold

VALID_INTENTS = ("investigate", "compare", "define", "out_of_scope", "no_match")
VALID_HYPOTHESES = ("up", "down", "unknown")

PLAN_SCHEMA_HINT = (
    '{"intent":"investigate|compare|define|out_of_scope|no_match",'
    '"variable_ids":["<id from CANDIDATES>"],'
    '"place":"<substring of QUESTION or null>","place_b":null,'
    '"start_year":null,"end_year":null,"last_n_years":null,'
    '"hypothesis":"up|down|unknown","lang":"es|en"}'
)

# --- intent cues (linguistic, language-agnostic lists) -----------------------
COMPARE_CUES = (
    "comparar", "compara", "comparacion", "compare", "comparing", "versus", "vs",
    "frente a", "diferencia entre", "difference between", "más que", "mas que",
    "que en", "than in", "both", "ambos", "las dos", "las dos regiones",
)
DEFINE_CUES = (
    "qué es", "que es", "qué significa", "que significa", "definición", "definicion",
    "what is", "what does", "meaning of", "explica qué", "explain what", "how is it measured",
    "cómo se mide", "como se mide", "para qué sirve", "what does it mean",
)
OUT_OF_SCOPE_CUES = (
    "partido", "fútbol", "futbol", "football", "elecciones", "receta", "chiste", "joke",
    "cancion", "canción", "song", "película", "pelicula", "movie", "historia del perú",
)
DOWN_CUES = ("menos", "baja", "bajando", "disminuye", "desciende", "pierde", "pérdida", "perdida",
             "less", "decrease", "decreasing", "decline", "shrinking", "losing", "loss", "down", "fewer")
UP_CUES = ("más", "mas", "sube", "subiendo", "aumenta", "crece", "aumento", "incremento",
           "more", "increase", "increasing", "rise", "rising", "growing", "up", "warmer", "hotter")
YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")

INTENT_BY_MODE = {"lora": "lora", "llm": "llm", "rules": "rules"}


def _lang(question: str, lang: str | None) -> str:
    return lang if lang in ("es", "en") else detect_language(question)


def _empty_plan(intent: str, lang: str, mode: str, *, reason: str | None = None) -> dict[str, Any]:
    plan = {
        "intent": intent,
        "variable_ids": [],
        "place": None,
        "place_b": None,
        "start_year": None,
        "end_year": None,
        "last_n_years": None,
        "hypothesis": "unknown",
        "lang": lang,
        "mode": mode,
    }
    if reason:
        plan["note"] = reason
    return plan


def _cue_pattern(cues: tuple[str, ...]) -> re.Pattern[str]:
    """Whole-word/phrase matcher over the folded text.

    Whole-word matters: "vs" as a substring would fire inside other words, while
    "compara" must still match "comparar"/"comparando" (Spanish verb forms share
    the stem), so each cue is matched as a prefix of a word boundary.
    """
    parts = []
    for cue in cues:
        folded = fold(cue).strip()
        if not folded:
            continue
        parts.append(re.escape(folded) + r"\w*")
    return re.compile(r"(?<!\w)(?:" + "|".join(parts) + r")(?!\w)")


_COMPARE_RE = _cue_pattern(COMPARE_CUES)
_DEFINE_RE = _cue_pattern(DEFINE_CUES)
_OUT_OF_SCOPE_RE = _cue_pattern(OUT_OF_SCOPE_CUES)


def _has(pattern: re.Pattern[str], folded: str) -> bool:
    return bool(pattern.search(folded))


def _hypothesis(question: str) -> str:
    q = " " + fold(question) + " "
    tokens = set(fold(question).split())
    down = sum(1 for cue in DOWN_CUES if f" {fold(cue)} " in q or fold(cue) in tokens)
    up = sum(1 for cue in UP_CUES if f" {fold(cue)} " in q or fold(cue) in tokens)
    if down > up:
        return "down"
    if up > down:
        return "up"
    return "unknown"


def _intent(question: str) -> str:
    folded = fold(question)
    if _has(_OUT_OF_SCOPE_RE, folded):
        return "out_of_scope"
    if _has(_COMPARE_RE, folded):
        return "compare"
    if _has(_DEFINE_RE, folded):
        return "define"
    return "investigate"


def _years(question: str) -> tuple[int | None, int | None, int | None]:
    years = sorted({int(y) for y in YEAR_RE.findall(question)})
    last_n = None
    match = re.search(r"(?:últimos|ultimos|last)\s+(\d{1,2})\s*(?:años|anos|years)", fold(question))
    if match:
        last_n = int(match.group(1))
    if len(years) >= 2:
        return years[0], years[-1], last_n
    return None, None, last_n


def _rules_plan(question: str, lang: str, cards: list[dict[str, Any]], *, mode: str = "rules") -> dict[str, Any]:
    """Deterministic fallback: first retrieved variable + gazetteer/grammar place."""
    places = extract_places(question, limit=2)
    start, end, last_n = _years(question)
    plan = {
        "intent": _intent(question),
        "variable_ids": [cards[0]["variables"][0]] if cards and cards[0].get("variables") else [],
        "place": places[0] if places else None,
        "place_b": places[1] if len(places) > 1 else None,
        "start_year": start,
        "end_year": end,
        "last_n_years": last_n,
        "hypothesis": _hypothesis(question),
        "lang": lang,
        "mode": mode,
    }
    if cards:
        plan["why"] = cards[0].get("title")
    plan.update(_coverage(question, plan, lang))
    return plan


# --- coverage: "we do not have that variable" -------------------------------
# RONDA_2 §6.2: before proposing the closest thing we happen to have, the planner
# must say that the data the student asked for is not in the catalogue.
MISSING_TOPICS: dict[str, dict[str, tuple[str, ...]]] = {
    "MODIS_NDVI": {
        "terms": ("ndvi", "vegetacion", "vegetation", "deforestacion", "deforestation",
                  "selva", "bosque", "forest", "verdor", "greenness", "plantas", "plants",
                  "cultivos", "crops", "biomasa", "biomass"),
        "names": {"es": "NDVI / vegetación (MODIS)", "en": "NDVI / vegetation (MODIS)"},
        # Physically related variables we do carry: water/energy balance of the land
        # surface is what MODIS NDVI would have shown the greenness of.
        "related": ("GWETTOP", "EVLAND", "TS", "ALLSKY_SFC_SW_DWN"),
    },
    "GPM_IMERG_PRECIP": {
        "terms": ("gpm", "imerg", "lluvia satelital", "satellite rain"),
        "names": {"es": "precipitación GPM IMERG", "en": "GPM IMERG precipitation"},
        "related": ("PRECTOTCORR", "TQV", "RH2M"),
    },
    "GLDAS_SOILM_0_10": {
        "terms": ("gldas", "humedad satelital", "satellite soil moisture"),
        "names": {"es": "humedad del suelo GLDAS", "en": "GLDAS soil moisture"},
        "related": ("GWETTOP", "EVLAND", "PRECTOTCORR"),
    },
    "AIRS_SURF_AIR_TEMP": {
        "terms": ("airs", "temperatura satelital"),
        "names": {"es": "temperatura del aire AIRS", "en": "AIRS air temperature"},
        "related": ("T2M", "TS"),
    },
    "OMI_NO2_TROP": {
        "terms": ("no2", "dioxido de nitrogeno", "nitrogen dioxide"),
        "names": {"es": "NO₂ troposférico (OMI)", "en": "tropospheric NO₂ (OMI)"},
        "related": ("AOD_55", "CLOUD_AMT"),
    },
    "OMI_O3_TOTAL": {
        "terms": ("omi",),
        "names": {"es": "ozono total OMI", "en": "OMI total ozone"},
        "related": ("TO3",),
    },
}


def _catalog_variable_ids() -> set[str]:
    """Variables the app can actually fetch today (the live catalogue)."""
    from .rag import corpus_documents

    return {v for doc in corpus_documents() for v in doc.variables if v}


def _coverage(question: str, plan: dict[str, Any], lang: str) -> dict[str, Any]:
    """Mark `no_match` when the student named a product we do not carry.

    A question about vegetation is not a question about soil evaporation. Instead of
    returning the nearest available variable, we say which data are missing and
    which catalogue variables are closest, so the UI can offer an honest alternative.
    """
    folded = fold(question)
    available = _catalog_variable_ids()
    wanted: list[str] = []
    for variable_id, spec in MISSING_TOPICS.items():
        if variable_id in available:
            continue  # we do carry it: nothing missing
        if any(re.search(rf"(?<!\w){re.escape(fold(t))}(?!\w)", folded) for t in spec["terms"]):
            wanted.append(variable_id)
    if not wanted:
        return {}

    # What we *can* offer instead: retrieved candidates that really exist.
    from .rag import retrieve_for_plan

    cards = retrieve_for_plan(question, lang=lang, k=6)
    related = MISSING_TOPICS[wanted[0]].get("related", ())
    seen: set[str] = set()
    ranked: list[tuple[int, dict[str, Any]]] = []
    for c in cards:
        vids = c.get("variables") or []
        if not vids or vids[0] not in available or vids[0] in seen:
            continue
        seen.add(vids[0])
        # A sensible substitute shares the sphere or the physical process; a
        # bare "nearest neighbour" can be nonsense (soil evaporation as a stand-in
        # for vegetation). Related variables rank first, the rest keep retrieval order.
        ranked.append((0 if vids[0] in related else 1, {"variable_id": vids[0], "title": c.get("title")}))
    ranked.sort(key=lambda pair: pair[0])
    available_cards = [item for _rank, item in ranked[:3]]
    if plan.get("mode") in ("lora", "llm"):
        # The model answered from candidates we do have; do not override its choice
        # unless it silently swapped the topic.
        if plan.get("variable_ids") and set(plan["variable_ids"]) <= available:
            return {"missing": [MISSING_TOPICS[v]["names"][lang] for v in wanted]}
    return {
        "intent": "no_match" if plan.get("intent") in ("investigate", "compare") else plan.get("intent"),
        "variable_ids": [],
        "missing": [MISSING_TOPICS[v]["names"][lang] for v in wanted],
        "missing_ids": wanted,
        "alternatives": available_cards[:3],
        "note": (
            "missing_variable: " + ", ".join(wanted)
            + " — the catalogue does not carry it yet (Giovanni CSV pending)"
        ),
    }


def _system_prompt() -> str | None:
    """The SAME system prompt the LoRA dataset uses (contract §10, Hermes 2)."""
    for candidate in (
        SETTINGS.data_dir / "lora" / "system_prompt.txt",
        SETTINGS.data_dir / "lora" / "SYSTEM_PROMPT.txt",
    ):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()
    return None


def _catalog_line(variable_id: str, lang: str) -> str:
    """One CANDIDATES line in the exact shape the LoRA dataset was built with.

    ``data/lora/train.jsonl`` writes ``- T2M: Temperatura del aire a 2 m (°C) -
    Cuánto calor hace...``. Training and inference must match, so the planner
    rebuilds that line from the published catalogue instead of the short corpus title.
    """
    card = _catalog_card(variable_id)
    if not card:
        return f"- {variable_id}: {variable_id}"
    names = card.get("names") or {}
    name = names.get(lang) or names.get("en") or names.get("es") or variable_id
    unit = card.get("unit") or ""
    definition = (card.get("simple_definition") or {})
    definition = definition.get(lang) or definition.get("en") or ""
    head = f"- {variable_id}: {name}" + (f" ({unit})" if unit else "")
    return f"{head} - {definition}" if definition else head


@lru_cache(maxsize=1)
def _catalog_cards_by_id() -> dict[str, dict[str, Any]]:
    from .corpus import load_catalog_cards

    return {str(card["id"]): card for card, _available in load_catalog_cards() if card.get("id")}


def _catalog_card(variable_id: str) -> dict[str, Any] | None:
    return _catalog_cards_by_id().get(variable_id)


def _user_message(question: str, cards: list[dict[str, Any]], *, lang: str = "es") -> str:
    """Exactly the shape data/lora/*.jsonl uses (§10)."""
    lines = [f"QUESTION: {question}", "CANDIDATES:"]
    seen: set[str] = set()
    for card in cards:
        vid = (card.get("variables") or [""])[0]
        if not vid or vid in seen:
            continue
        seen.add(vid)
        lines.append(_catalog_line(vid, lang))
    return "\n".join(lines)


def validate_plan(raw: Any, *, question: str, candidates: set[str], lang: str) -> tuple[dict[str, Any] | None, str | None]:
    """Hard validation (§R3.3). Returns (plan, None) or (None, reason)."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return None, "not JSON"
    if not isinstance(raw, dict):
        return None, "not an object"

    intent = raw.get("intent")
    if intent not in VALID_INTENTS:
        return None, f"intent {intent!r} not allowed"
    ids = raw.get("variable_ids") or []
    if not isinstance(ids, list) or not all(isinstance(v, str) for v in ids):
        return None, "variable_ids must be a list of strings"
    bad = [v for v in ids if v not in candidates]
    if bad:
        return None, f"variable_ids not among candidates: {bad}"
    if intent in ("investigate", "compare") and not ids:
        return None, "investigate/compare need at least one variable"

    place = raw.get("place")
    if place is not None:
        if not isinstance(place, str) or not place.strip():
            return None, "place must be a non-empty string or null"
        if fold(place.strip()) not in fold(question):
            return None, f"place {place!r} is not a substring of the question"
    place_b = raw.get("place_b")
    if place_b is not None:
        if not isinstance(place_b, str) or fold(place_b.strip()) not in fold(question):
            return None, "place_b is not a substring of the question"

    hypothesis = raw.get("hypothesis", "unknown")
    if hypothesis not in VALID_HYPOTHESES:
        return None, f"hypothesis {hypothesis!r} not allowed"

    def _year(key: str) -> int | None:
        value = raw.get(key)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or not (1880 <= value <= 2100):
            raise ValueError(key)
        return value

    try:
        start_year, end_year = _year("start_year"), _year("end_year")
        last_n = raw.get("last_n_years")
        if last_n is not None and (not isinstance(last_n, int) or not (1 <= last_n <= 100)):
            raise ValueError("last_n_years")
    except ValueError as exc:
        return None, f"bad year field {exc}"

    plan = {
        "intent": intent,
        "variable_ids": list(dict.fromkeys(ids)),
        "place": place.strip() if isinstance(place, str) else None,
        "place_b": place_b.strip() if isinstance(place_b, str) else None,
        "start_year": start_year,
        "end_year": end_year,
        "last_n_years": last_n,
        "hypothesis": hypothesis,
        "lang": raw.get("lang") if raw.get("lang") in ("es", "en") else lang,
    }
    return plan, None


def _local_lora(question: str, lang: str, cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Call the locally trained adapter through ``src/ml/serve.py`` (Antigravity 2).

    RONDA_2 §9.2.5: ``PLANNER_MODEL=local-lora`` means "use the adapter this
    machine trained", not "use an Ollama tag called local-lora". If the serving
    module or the adapter is not there yet we return None and the caller falls
    back to rules with a note; we never fake a lora answer.
    """
    system = _system_prompt()
    if system is None:
        return None
    try:
        from src.ml.serve import generate  # type: ignore
    except Exception:
        return None
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": _user_message(question, cards, lang=lang)},
    ]
    try:
        raw = generate(messages)
    except Exception as exc:  # model not loaded, CUDA busy, adapter missing
        return _rules_plan(question, lang, cards, mode="rules") | {
            "note": f"local_lora_unavailable: {type(exc).__name__}: {exc}"[:160]
        }
    candidates = {(c.get("variables") or [None])[0] for c in cards}
    candidates = {c for c in candidates if c}
    plan, reason = validate_plan(raw, question=question, candidates=candidates, lang=lang)
    if plan is None:
        fallback = _rules_plan(question, lang, cards, mode="rules")
        fallback["note"] = f"lora_rejected: {reason}"[:160]
        return fallback
    plan["mode"] = "lora"
    return plan


def _llm_plan(question: str, lang: str, cards: list[dict[str, Any]], *, mode: str) -> dict[str, Any]:
    """Ask PLANNER_MODEL, validate, retry once, then fall back to rules."""
    candidates = {(c.get("variables") or [None])[0] for c in cards}
    candidates = {c for c in candidates if c}
    system = _system_prompt()
    if system is None:
        # Without Hermes 2's system prompt the training/use contract can't be met,
        # so we do not pretend: rules answer, and the plan says why.
        plan = _rules_plan(question, lang, cards, mode="rules")
        plan["note"] = "lora_system_prompt_missing"
        return plan

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": _user_message(question, cards, lang=lang)},
    ]
    last_reason = None
    for attempt in range(2):
        try:
            raw = chat(messages, model=SETTINGS.planner_model, temperature=0.0)
        except AIUnavailable as exc:
            plan = _rules_plan(question, lang, cards, mode="rules")
            plan["note"] = f"ai_unavailable: {exc}"[:160]
            return plan
        plan, reason = validate_plan(raw, question=question, candidates=candidates, lang=lang)
        if plan is not None:
            plan["mode"] = mode
            return plan
        last_reason = reason
        messages = messages[:2] + [
            {"role": "user", "content": f"Your previous answer was rejected ({reason}). Reply with valid JSON only: {PLAN_SCHEMA_HINT}"}
        ]
    plan = _rules_plan(question, lang, cards, mode="rules")
    plan["note"] = f"planner_rejected: {last_reason}"[:160]
    return plan


def _planner_model_is_local_lora() -> bool:
    """`PLANNER_MODEL=local-lora` selects the adapter, not an Ollama tag."""
    return (SETTINGS.planner_model or "").strip().lower() in ("local-lora", "local_lora", "lora")


def plan(question: str, *, lang: str = "es") -> dict[str, Any]:
    """Turn a student's question into an InvestigationPlan (contract §10)."""
    language = _lang(question, lang)
    if not question or not question.strip():
        return _empty_plan("no_match", language, "rules", reason="empty question")

    # Off-topic questions are answered before retrieval: a football question must
    # not come back with a climate variable because one word collided.
    if _intent(question) == "out_of_scope":
        return _empty_plan("out_of_scope", language, "rules")

    cards = retrieve_for_plan(question, lang=language, k=6)
    if not cards:
        return _empty_plan("no_match", language, "rules", reason="no candidate variables retrieved")

    if SETTINGS.ai_mode == "full" and SETTINGS.planner_model:
        if _planner_model_is_local_lora():
            result = _local_lora(question, language, cards)
            if result is not None:
                return result
            fallback = _rules_plan(question, language, cards)
            fallback["note"] = "local_lora_unavailable: src/ml/serve.py or adapter not ready"
            return fallback
        return _llm_plan(question, language, cards, mode="llm")

    return _rules_plan(question, language, cards)


def resolve(plan_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """Attach coordinates to a plan through the gazetteer only (never a model)."""
    out = []
    for key in ("place", "place_b"):
        name = plan_dict.get(key)
        out.append({"field": key, "name": name, "places": geocode(name) if name else []})
    return out


def debug_candidates(question: str, *, lang: str = "es", k: int = 6) -> list[dict[str, Any]]:
    return retrieve_for_plan(question, lang=lang, k=k)


def explain_choice(question: str, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Why each candidate appeared: which of the student's words hit the lexicon."""
    hits = expand(question)
    prior = specificity_prior(question)
    rows = []
    for card in cards:
        vid = (card.get("variables") or [None])[0]
        rows.append(
            {
                "variable_id": vid,
                "title": card.get("title"),
                "score": card.get("score"),
                "matched_terms": hits.get(vid, []) if vid else [],
                "specificity": round(prior.get(vid, 0.0), 3) if vid else 0.0,
                "url": card.get("url"),
            }
        )
    return rows
