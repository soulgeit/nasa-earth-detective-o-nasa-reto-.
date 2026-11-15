# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Planner: schema, hard validation, intent, and the extractive floor."""

from __future__ import annotations

import json

import pytest

from src.detective import plan
from src.detective.planner import validate_plan

PLAN_KEYS = {
    "intent", "variable_ids", "place", "place_b", "start_year", "end_year",
    "last_n_years", "hypothesis", "lang", "mode",
}


def test_plan_has_contract_shape():
    result = plan("¿está lloviendo menos en Piura?", lang="es")
    assert PLAN_KEYS <= set(result)
    assert result["intent"] in ("investigate", "compare", "define", "out_of_scope", "no_match")
    assert result["hypothesis"] in ("up", "down", "unknown")
    assert result["lang"] in ("es", "en")
    assert result["mode"] in ("rules", "llm", "lora")


def test_acceptance_case_from_the_prompt():
    """The prompt's acceptance test: rain variable, place Piura, mode reported."""
    result = plan("¿está lloviendo menos en Piura?", lang="es")
    assert result["variable_ids"] == ["PRECTOTCORR"]
    assert result["place"] == "Piura"
    assert result["hypothesis"] == "down"
    assert "mode" in result


def test_place_is_a_literal_substring_of_the_question():
    question = "¿por qué hace más calor en la Cordillera Blanca estos años?"
    result = plan(question, lang="es")
    if result["place"]:
        assert result["place"] in question


def test_off_topic_is_out_of_scope():
    result = plan("¿quién ganó el partido de fútbol?", lang="es")
    assert result["intent"] == "out_of_scope"
    assert result["variable_ids"] == []


def test_define_intent():
    assert plan("¿qué es el NDVI?", lang="es")["intent"] == "define"


def test_compare_needs_two_places():
    result = plan("compara la lluvia de Piura y Tumbes", lang="es")
    assert result["intent"] == "compare"
    assert result["place"] and result["place_b"]
    assert result["place"] != result["place_b"]


def test_years_are_extracted():
    result = plan("temperatura en Lima entre 1990 y 2020", lang="es")
    assert result["start_year"] == 1990
    assert result["end_year"] == 2020


def test_last_n_years():
    assert plan("lluvia en Iquitos en los últimos 20 años", lang="es")["last_n_years"] == 20


def test_requested_language_is_honoured():
    """`lang` is the caller's choice (contract §6: lang in es|en) — the UI owns it."""
    assert plan("is Lima getting hotter?", lang="en")["lang"] == "en"
    assert plan("¿hace más calor en Lima?", lang="es")["lang"] == "es"


def test_invalid_language_falls_back_to_detection():
    assert plan("is Lima getting hotter?", lang="fr")["lang"] == "en"
    assert plan("¿hace más calor en Lima?", lang="")["lang"] == "es"

CANDIDATES = {"T2M", "PRECTOTCORR", "GWETTOP"}
QUESTION = "¿está lloviendo menos en Piura?"


def _valid(**over):
    base = {
        "intent": "investigate", "variable_ids": ["PRECTOTCORR"], "place": "Piura",
        "place_b": None, "start_year": None, "end_year": None, "last_n_years": None,
        "hypothesis": "down", "lang": "es",
    }
    base.update(over)
    return base


def test_validate_accepts_a_clean_plan():
    result, reason = validate_plan(_valid(), question=QUESTION, candidates=CANDIDATES, lang="es")
    assert reason is None and result["variable_ids"] == ["PRECTOTCORR"]


def test_validate_accepts_json_text():
    result, reason = validate_plan(json.dumps(_valid()), question=QUESTION, candidates=CANDIDATES, lang="es")
    assert reason is None


@pytest.mark.parametrize("over,needle", [
    ({"variable_ids": ["SEAICE_EXTENT_N"]}, "not among candidates"),
    ({"variable_ids": ["NOT_A_VAR"]}, "not among candidates"),
    ({"place": "Lima"}, "not a substring"),
    ({"intent": "diagnose"}, "not allowed"),
    ({"hypothesis": "maybe"}, "not allowed"),
    ({"start_year": "1990"}, "bad year"),
    ({"variable_ids": []}, "need at least one variable"),
])
def test_validate_rejects(over, needle):
    result, reason = validate_plan(_valid(**over), question=QUESTION, candidates=CANDIDATES, lang="es")
    assert result is None and needle in reason, reason


def test_validate_rejects_non_json_text():
    result, reason = validate_plan("not json at all", question=QUESTION, candidates=CANDIDATES, lang="es")
    assert result is None and "not JSON" in reason


def test_validate_rejects_place_b_outside_question():
    result, reason = validate_plan(_valid(intent="compare", place_b="Cusco"),
                                   question=QUESTION, candidates=CANDIDATES, lang="es")
    assert result is None and "place_b" in reason


# --- T4: training and inference must use the same message --------------------

def _dataset_system_prompt():
    import json as _json
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "data" / "lora" / "train.jsonl"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return _json.loads(fh.readline())["messages"][0]["content"]


def test_system_prompt_is_identical_to_the_dataset():
    from src.detective.planner import _system_prompt

    expected = _dataset_system_prompt()
    if expected is None:
        pytest.skip("data/lora/train.jsonl not published")
    assert _system_prompt() == expected


def test_candidate_lines_match_the_dataset_shape():
    from src.detective.planner import _user_message, debug_candidates

    question = "¿qué es la temperatura?"
    message = _user_message(question, debug_candidates(question, lang="es", k=4), lang="es")
    lines = message.splitlines()
    assert lines[0] == f"QUESTION: {question}"
    assert lines[1] == "CANDIDATES:"
    for line in lines[2:]:
        # "- T2M: Temperatura del aire a 2 m (°C) - Cuánto calor hace..."
        assert line.startswith("- ")
        assert ": " in line
        assert " - " in line, f"missing the definition separator: {line}"


def test_local_lora_without_serving_falls_back_to_rules(monkeypatch):
    """PLANNER_MODEL=local-lora must not pretend if src/ml/serve.py is absent."""
    from src.detective import config as cfg
    from src.detective import planner as planner_module

    monkeypatch.setattr(planner_module, "SETTINGS", cfg.Settings(
        ai_mode="full", llm_base_url="http://localhost:11434/v1",
        planner_model="local-lora", explain_model="",
        embed_base_url="http://localhost:11434", embed_model="",
        data_dir=cfg.SETTINGS.data_dir, catalog_dir=cfg.SETTINGS.catalog_dir,
        knowledge_dir=cfg.SETTINGS.knowledge_dir, index_dir=cfg.SETTINGS.index_dir,
        request_timeout=5.0,
    ), raising=False)
    from src.detective.planner import plan as _plan

    result = _plan("¿está lloviendo menos en Piura?", lang="es")
    assert result["mode"] == "rules"
    assert "local_lora" in result.get("note", "") or "rejected" in result.get("note", "")


# --- RONDA_3 §4.2: planned variables from the catalogue ---------------------

def test_planned_variable_is_named_and_explained(monkeypatch, tmp_path):
    """A product in the catalogue's `planned` section must be named, not just refused."""
    import json as _json
    from src.detective import corpus as corpus_module

    catalog = {
        "schema": "catalog/2",
        "variables": [{"id": "T2M", "names": {"es": "Temperatura", "en": "Temperature"}, "unit": "°C"}],
        "planned": [{
            "id": "MODIS_NDVI",
            "available": False,
            "names": {"es": "NDVI (MODIS)", "en": "NDVI (MODIS)"},
            "simple_definition": {
                "es": "Se carga subiendo el CSV de NDVI exportado de Giovanni.",
                "en": "Load it by uploading the NDVI CSV exported from Giovanni.",
            },
            "source": {"via": "Giovanni (GES DISC)", "url": "https://giovanni.gsfc.nasa.gov/giovanni/"},
        }],
    }
    path = tmp_path / "variables.json"
    path.write_text(_json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(corpus_module.SETTINGS.__class__, "catalog_dir", property(lambda self: tmp_path), raising=False)
    monkeypatch.setattr(corpus_module, "SETTINGS", corpus_module.SETTINGS, raising=False)

    from src.detective import planner as planner_module

    monkeypatch.setattr(planner_module, "_catalog_variable_ids", lambda: {"T2M"})
    monkeypatch.setattr(
        planner_module,
        "_planned_card",
        lambda vid: next((c for c in catalog["planned"] if c["id"] == vid), None),
    )

    result = planner_module._coverage(
        "¿la selva pierde vegetación?", {"intent": "investigate", "mode": "rules", "variable_ids": []}, "es"
    )
    assert result["intent"] == "no_match"
    assert result["missing"] == ["NDVI (MODIS)"]
    assert result["how_to_load"] and "Giovanni" in result["how_to_load"][0]
    assert result["available"] is False


def test_planned_cards_are_read_from_the_catalog():
    from src.detective.corpus import load_catalog_cards

    cards = load_catalog_cards()
    planned = [c for c, available in cards if not available]
    for card in planned:
        assert card.get("available") is False, "a planned card must say so in its payload"
