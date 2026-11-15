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
from .places import extract_places, resolve_place
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
        "planner": "rules",
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


def _resolved_places(question: str, *, limit: int = 2) -> list[str]:
    """Places the gazetteer or the regions file can actually resolve (RONDA_4 §4.2).

    A span that no verified source resolves is not a place, so it never reaches
    the plan. This is what stops ``place: "sea"`` and ``place_b: "the"``.
    """
    resolved: list[str] = []
    for span in extract_places(question, limit=limit + 2):
        if resolve_place(span):
            resolved.append(span)
        if len(resolved) >= limit:
            break
    return resolved


def _rules_plan(question: str, lang: str, cards: list[dict[str, Any]], *, mode: str = "rules") -> dict[str, Any]:
    """Deterministic fallback: first *available* retrieved variable + a resolvable place.

    RONDA_3 §4: a card for a planned product (available=false) may rank first, but it
    cannot be analysed. We never offer it as the variable to investigate; the first
    analysable card wins, and ``_coverage`` decides whether to answer ``no_match``.
    RONDA_4 §4.2: a span that no verified source resolves is not a place.
    """
    places = _resolved_places(question, limit=2)
    start, end, last_n = _years(question)
    chosen = next((c for c in cards if c.get("available", True)), cards[0] if cards else None)
    variables = (chosen.get("variables") or []) if chosen else []
    plan = {
        "intent": _intent(question),
        "variable_ids": [variables[0]] if variables else [],
        "place": places[0] if places else None,
        "place_b": places[1] if len(places) > 1 else None,
        "start_year": start,
        "end_year": end,
        "last_n_years": last_n,
        "hypothesis": _hypothesis(question),
        "lang": lang,
        "mode": mode,
        "planner": "lora" if mode == "lora" else "rules",
    }
    if chosen:
        plan["why"] = chosen.get("title")
    plan.update(_coverage(question, plan, lang))
    return _out_of_scope_guard(question, plan, lang)


# --- out of scope and unknown variables (RONDA_4 §4.2) ----------------------
# A question about the meaning of life is not a question about snow depth; and the
# catalogue has no wind variable, so "is the wind getting stronger?" must say so.
OUT_OF_SCOPE_RE = re.compile(
    r"(?<!\w)(?:"
    r"meaning of life|sentido de la vida|"
    r"qui[eé]n gan[oó]|who won|"
    r"f[uú]tbol|football|soccer|partido de|"
    r"elecciones|election|"
    r"receta de|recipe for|cocinar|cook\b|"
    r"chiste|joke|"
    r"canci[oó]n|cancion|song|"
    r"pel[ií]cula|movie|film\b|"
    r"precio del d[oó]lar|stock price|cu[aá]nto cuesta"
    r")(?!\w)",
    re.IGNORECASE,
)

# Physical processes the student may name that no catalogue variable covers.
UNKNOWN_TOPIC_RE = re.compile(
    r"(?<!\w)(?:viento|wind|vientos|winds|windy)(?!\w)", re.IGNORECASE
)


def _catalog_has_wind() -> bool:
    from .corpus import load_catalog_cards

    return any("WS2M" == str(card.get("id")) for card, _a in load_catalog_cards())


def _out_of_scope_guard(question: str, plan: dict[str, Any], lang: str) -> dict[str, Any]:
    """Last gate before a plan leaves the rules path."""
    folded = fold(question)
    if OUT_OF_SCOPE_RE.search(question) or OUT_OF_SCOPE_RE.search(folded):
        cleared = dict(plan)
        cleared.update({
            "intent": "out_of_scope",
            "variable_ids": [],
            "place": None,
            "place_b": None,
            "why": None,
        })
        return cleared

    if UNKNOWN_TOPIC_RE.search(question) and not _catalog_has_wind():
        cleared = dict(plan)
        cleared.update({
            "intent": "no_match",
            "variable_ids": [],
            "missing": ["viento / wind speed (WS2M)"] if lang == "es" else ["wind speed (WS2M)"],
            "missing_ids": ["WS2M"],
            "available": False,
            "note": "unknown_variable: WS2M is not in the catalogue",
        })
        return cleared

    return plan


# --- coverage: "we do not have that variable" -------------------------------
# RONDA_2 §6.2: before proposing the closest thing we happen to have, the planner
# must say that the data the student asked for is not in the catalogue.
MISSING_TOPICS: dict[str, dict[str, tuple[str, ...]]] = {
    "MODIS_NDVI": {
        # "selva"/"bosque" alone are places, not a request for vegetation data:
        # "¿Qué ha pasado con la lluvia en la selva de Madre de Dios?" is a rain
        # question. Only an explicit vegetation word makes it a NDVI question.
        "terms": ("ndvi", "vegetacion", "vegetation", "deforestacion", "deforestation",
                  "verdor", "greenness", "plantas", "plants", "biomasa", "biomass"),
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
    from .corpus import load_catalog_cards

    return {str(card["id"]) for card, available in load_catalog_cards() if available and card.get("id")}


def _planned_card(variable_id: str) -> dict[str, Any] | None:
    """The catalogue's `planned` entry for an id we know about but do not carry."""
    from .corpus import load_catalog_cards

    for card, available in load_catalog_cards():
        if not available and str(card.get("id")) == variable_id:
            return card
    return None


def _load_instructions(variable_id: str, lang: str) -> str | None:
    """Plain-language 'how do I get this variable', from the catalogue entry.

    RONDA_3 §4 (claude-omni-2, task 2): the answer must name the variable and say
    how to load it, not just "no match".
    """
    card = _planned_card(variable_id)
    if not card:
        return None
    definition = card.get("simple_definition") or {}
    if isinstance(definition, dict):
        text = definition.get(lang) or definition.get("en") or ""
        if text:
            return str(text)
    source = card.get("source") or {}
    url = source.get("url") if isinstance(source, dict) else None
    if url:
        return (
            f"Se carga subiendo el CSV de Giovanni ({url})."
            if lang == "es"
            else f"Load it by uploading the Giovanni CSV ({url})."
        )
    return None


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

    # Name it the way the catalogue names it, and say how to load it.
    missing_names: list[str] = []
    instructions: list[str] = []
    for variable_id in wanted:
        card = _planned_card(variable_id)
        names = (card or {}).get("names") or {}
        name = names.get(lang) or names.get("en") or MISSING_TOPICS[variable_id]["names"][lang]
        missing_names.append(str(name))
        how = _load_instructions(variable_id, lang)
        if how and how not in instructions:
            instructions.append(how)

    return {
        "intent": "no_match" if plan.get("intent") in ("investigate", "compare") else plan.get("intent"),
        "variable_ids": [],
        "missing": missing_names,
        "missing_ids": wanted,
        "available": False,
        "how_to_load": instructions or None,
        "alternatives": available_cards[:3],
        "note": (
            "missing_variable: " + ", ".join(wanted)
            + " — planned product, not loaded yet (Giovanni CSV pending)"
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



def _catalog_entry_text(variable_id: str, lang: str) -> str:
    """The CANDIDATES payload without the leading "- ID: ", as serve.py expects."""
    line = _catalog_line(variable_id, lang)
    prefix = f"- {variable_id}: "
    return line[len(prefix):] if line.startswith(prefix) else line


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

    # RONDA_4 §5.2: el modelo propone y las reglas comprueban. A place the gazetteer
    # or the regions file cannot resolve is dropped (it was hallucinated), and the
    # server-side scope rules still apply to what the model produced.
    for key in ("place", "place_b"):
        value = plan[key]
        if value is not None and not resolve_place(value):
            plan[key] = None
            note = f"dropped_unresolved_{key}"
            plan["why"] = f"{plan['why']}; {note}" if plan.get("why") else note
    return plan, None


def _local_lora(question: str, lang: str, cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Call the locally trained adapter through ``src/ml/serve.py`` (Antigravity 2).

    RONDA_2 §9.2.5 / RONDA_3 §4.3: ``PLANNER_MODEL=local-lora`` means "use the
    adapter this machine trained", not "use an Ollama tag called local-lora".
    The adapter is called through ``plan_with_lora(question, candidates, lang)``,
    which is the API Antigravity 2 published. If the module, the adapter or the
    GPU is missing we fall back to rules with an explicit note; we never fake it.
    """
    try:
        from src.ml import serve as serving  # type: ignore
    except Exception:
        return None
    if not hasattr(serving, "plan_with_lora"):
        return None
    # The serving module builds CANDIDATES itself from these entries, so give it
    # exactly the text the dataset used: "ID: nombre (unidad) - definición".
    candidates = [
        {"variable_id": vid, "title": _catalog_entry_text(vid, lang)}
        for vid in dict.fromkeys((c.get("variables") or [None])[0] for c in cards)
        if vid
    ]
    try:
        raw = serving.plan_with_lora(question, candidates=candidates, lang=lang)
    except Exception as exc:  # adapter missing, CUDA busy, no transformers
        return _rules_plan(question, lang, cards, mode="rules") | {
            "note": f"local_lora_unavailable: {type(exc).__name__}: {exc}"[:160]
        }
    allowed = {c["variable_id"] for c in candidates}
    plan, reason = validate_plan(raw, question=question, candidates=allowed, lang=lang)
    if plan is None:
        fallback = _rules_plan(question, lang, cards, mode="rules")
        fallback["note"] = f"lora_rejected: {reason}"[:160]
        return fallback
    plan["mode"] = "lora"
    plan["planner"] = "lora"
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
            plan["planner"] = "rules" if mode == "rules" else "lora"
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
    if _intent(question) == "out_of_scope" or OUT_OF_SCOPE_RE.search(question):
        return _empty_plan("out_of_scope", language, "rules")

    # A process the catalogue does not cover at all ("viento") is said out loud,
    # not answered with the closest thing we happen to have.
    if UNKNOWN_TOPIC_RE.search(question) and not _catalog_has_wind():
        result = _empty_plan("no_match", language, "rules", reason="unknown_variable: WS2M")
        result["missing"] = ["viento / wind speed (WS2M)"] if language == "es" else ["wind speed (WS2M)"]
        result["missing_ids"] = ["WS2M"]
        result["available"] = False
        return result

    cards = retrieve_for_plan(question, lang=language, k=6)
    if not cards:
        return _empty_plan("no_match", language, "rules", reason="no candidate variables retrieved")

    # RONDA_4 §5.2 — who plans:
    #   * the public server runs `AI_MODE=extractive`: rules plan, nothing is loaded;
    #   * locally, `PLANNER_MODEL=local-lora` opts in to the adapter explicitly.
    # The LoRA is therefore never the silent default: it wins only when the operator
    # asks for it, and its real numbers (200-case set + 50 reference questions) are
    # published together in docs/EVAL_IA.md (rule 20).
    if SETTINGS.ai_mode == "full" and SETTINGS.planner_model:
        if _planner_model_is_local_lora():
            result = _local_lora(question, language, cards)
            if result is not None:
                # §5.2: the model proposes, the rules verify. Whatever the adapter
                # produced still goes through the scope gate.
                return _out_of_scope_guard(question, result, language)
            fallback = _rules_plan(question, language, cards)
            fallback["note"] = "local_lora_unavailable: src/ml/serve.py or adapter not ready"
            return fallback
        return _out_of_scope_guard(question, _llm_plan(question, language, cards, mode="llm"), language)

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
