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
