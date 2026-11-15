# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""RONDA_4 rule 19: a `planned` variable is never a candidate.

Neither the rules nor the LoRA may return one in any plan that is not `no_match`.
This is the highest-value defect of the final round: it broke 2 pipeline tests and
15 of the LoRA's 19 misses on the reference questions.
"""

from __future__ import annotations

import json

import pytest

import src.detective as detective
from src.detective.corpus import load_catalog_cards
from src.detective.rag import retrieve_for_plan


def _planned_ids() -> set[str]:
    return {str(card["id"]) for card, available in load_catalog_cards() if not available}


def _available_ids() -> set[str]:
    return {str(card["id"]) for card, available in load_catalog_cards() if available}


def _golden_questions() -> list[dict]:
    from src.detective.config import SETTINGS

    path = SETTINGS.knowledge_dir / "golden_questions.jsonl"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_the_catalog_has_planned_products():
    """If the catalogue stopped publishing `planned`, this suite would pass vacuously."""
    planned = _planned_ids()
    assert planned, "no planned variables in the catalogue: the rule cannot be checked"
    assert planned.isdisjoint(_available_ids()), "a product cannot be both planned and available"


@pytest.mark.parametrize("question,lang", [
    ("¿la selva de Madre de Dios pierde vegetación?", "es"),
    ("is Amazon vegetation declining?", "en"),
    ("¿cuánta humedad hay en el suelo de Ica según GLDAS?", "es"),
    ("show me NO2 over Lima from OMI", "en"),
    ("¿qué lluvia muestra GPM IMERG en Piura?", "es"),
    ("temperatura de la superficie con MODIS en la costa", "es"),
])
def test_planned_never_appears_in_a_plan(question, lang):
    planned = _planned_ids()
    result = detective.plan(question, lang=lang)
    returned = set(result.get("variable_ids") or [])
    assert returned.isdisjoint(planned), f"planned variable returned: {returned & planned}"
    if returned:
        assert returned <= _available_ids(), f"unknown variable returned: {returned - _available_ids()}"


def test_planned_questions_become_no_match_with_a_note():
    result = detective.plan("¿la selva de Madre de Dios pierde vegetación?", lang="es")
    assert result["intent"] == "no_match"
    assert result["variable_ids"] == []
    assert result.get("missing_ids")
    assert result.get("how_to_load")


def test_planner_candidates_are_only_available_variables():
    """The candidate list itself is filtered, so the LoRA cannot pick a planned one."""
    available = _available_ids()
    for question in ("lluvia en Piura", "vegetación en la selva", "humedad del suelo"):
        for card in retrieve_for_plan(question, lang="es", k=6):
            for vid in card.get("variables") or []:
                assert vid in available, f"{vid} is not an available variable"
            assert card.get("available", True) is True


def test_all_golden_questions_never_return_a_planned_variable():
    planned = _planned_ids()
    for row in _golden_questions():
        result = detective.plan(row["question"], lang=row.get("lang", "es"))
        returned = set(result.get("variable_ids") or [])
        assert returned.isdisjoint(planned), f"{row['question']}: {returned & planned}"
