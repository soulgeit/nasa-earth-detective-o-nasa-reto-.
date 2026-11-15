# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""RONDA_4 §4.2 / §2.6: the rules path must not invent places.

The four phrases below are exactly the ones the architect found broken:
    «Has Arctic sea ice shrunk since 1980?»      -> place "sea", place_b "Has"
    «Is the wind getting stronger in Punta Arenas?» -> place_b "the", RH2M
    «…que en los años 80?»                       -> place_b "los"
    «What is the meaning of life?»               -> define, SNODP, place "the"
"""

from __future__ import annotations

import pytest

import src.detective as detective
from src.detective.places import resolve_place


@pytest.mark.parametrize("question,lang", [
    ("Has Arctic sea ice shrunk since 1980?", "en"),
    ("Is the wind getting stronger in Punta Arenas?", "en"),
    ("¿qué pasó con la temperatura en Lima en los años 80?", "es"),
    ("What is the meaning of life?", "en"),
])
def test_no_invented_places(question, lang):
    result = detective.plan(question, lang=lang)
    for key in ("place", "place_b"):
        value = result.get(key)
        if value is None:
            continue
        assert resolve_place(value), f"{key}={value!r} is not a resolvable place"
        assert value in question, "a place must be copied verbatim from the question"


def test_ice_question_has_a_variable_and_no_place():
    result = detective.plan("Has Arctic sea ice shrunk since 1980?", lang="en")
    assert result["variable_ids"] == ["SEAICE_EXTENT_N"]
    assert result["place"] is None


def test_wind_is_a_real_variable_since_round_7():
    """RONDA_7 added WS2M to the catalogue: a wind question is now investigated.

    Until then the honest answer was "no_match, WS2M is missing" (never RH2M).
    """
    result = detective.plan("Is the wind getting stronger in Punta Arenas?", lang="en")
    assert result["intent"] == "investigate"
    assert result["variable_ids"] == ["WS2M"]
    assert result["place"] == "Punta Arenas"
    assert not result.get("missing_ids")


def test_a_city_question_never_gets_a_global_only_series():
    """"temperatura en Huancayo" used to return the GISTEMP *global* anomaly."""
    for question in ("temperatura en Huancayo", "temperature in Ayacucho"):
        result = detective.plan(question, lang="es")
        assert result["variable_ids"] == ["T2M"], result
    # a named region keeps its hemispheric series
    arctic = detective.plan("Is Arctic sea ice shrinking?", lang="en")
    assert arctic["variable_ids"] == ["SEAICE_EXTENT_N"], arctic


def test_a_name_inside_a_longer_name_is_not_a_second_place():
    result = detective.plan("calor en San Juan de Lurigancho", lang="es")
    assert result["place_b"] is None, result


def test_meaning_of_life_is_out_of_scope():
    result = detective.plan("What is the meaning of life?", lang="en")
    assert result["intent"] == "out_of_scope"
    assert result["variable_ids"] == []


def test_years_as_text_are_not_places():
    result = detective.plan("¿qué pasó con la temperatura en Lima en los años 80?", lang="es")
    assert result["place"] == "Lima"
    assert result["place_b"] is None


def test_real_places_still_resolve():
    for question in ("¿está lloviendo menos en Piura?", "nieve en Arequipa", "temperatura en Madre de Dios"):
        result = detective.plan(question, lang="es")
        assert result["place"], f"lost a real place in {question!r}"


def test_coordination_keeps_the_order_of_the_question():
    result = detective.plan("compara la lluvia de Piura y Tumbes", lang="es")
    assert result["place"] == "Piura"
    assert result["place_b"] == "Tumbes"


def test_generous_geocoder_does_not_leak_into_plans():
    """`geocode` is generous (alt_names, fuzzy); a plan place must be canonical.

    GeoNames' alt_names map "Sea" to Seattle and "Los" to Lagos, which is why the
    plan uses `resolve_place` (exact canonical name) and not `geocode`.
    """
    from src.detective.gazetteer import geocode

    assert geocode("sea"), "precondition: the user-facing geocoder is generous"
    assert not resolve_place("sea")
    assert not resolve_place("los")
    assert not resolve_place("the")
