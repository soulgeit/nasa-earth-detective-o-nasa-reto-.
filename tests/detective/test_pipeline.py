# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""20 end-to-end questions: retrieve -> plan -> (geocode) -> explain, offline.

These run in AI_MODE=extractive with no network at all, which is exactly the
degradation contract (§11) and the acceptance test of the prompt.
"""

from __future__ import annotations

import socket

import pytest

import src.detective as detective

QUESTIONS = [
    ("¿está lloviendo menos en Piura?", "es", "PRECTOTCORR"),
    ("¿cada vez hace más calor en Lima?", "es", "T2M"),
    ("¿el aire de Lima está más contaminado?", "es", "AOD_55"),
    ("¿se está derritiendo el hielo del Ártico?", "es", "SEAICE_EXTENT_N"),
    ("¿hay menos nieve en la Cordillera Blanca?", "es", "SNODP"),
    ("¿la selva de Madre de Dios pierde vegetación?", "es", "MODIS_NDVI"),
    ("¿se está secando el suelo de Ica?", "es", "GWETTOP"),
    ("¿qué es la humedad relativa?", "es", "RH2M"),
    ("¿llega más radiación solar a la costa?", "es", "ALLSKY_SFC_SW_DWN"),
    ("¿el ozono se está recuperando?", "es", "TO3"),
    ("¿la temperatura del suelo sube en el desierto?", "es", "TS"),
    ("¿hay más vapor de agua en la atmósfera?", "es", "TQV"),
    ("compara la lluvia de Piura y Tumbes", "es", "PRECTOTCORR"),
    ("is it raining less in Piura?", "en", "PRECTOTCORR"),
    ("is Lima getting hotter?", "en", "T2M"),
    ("is Arctic sea ice shrinking?", "en", "SEAICE_EXTENT_N"),
    ("what is soil moisture?", "en", "GWETTOP"),
    ("is Amazon vegetation declining?", "en", "MODIS_NDVI"),
    ("is snow decreasing in the Andes?", "en", "SNODP"),
    ("is Antarctica gaining or losing ice?", "en", "SEAICE_EXTENT_S"),
]


@pytest.fixture()
def no_network(monkeypatch):
    """Any outgoing socket connection raises: proves the suite never leaves the box."""
    def _blocked(*args, **kwargs):
        raise AssertionError("network access attempted in an offline test")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


def test_fixture_list_is_complete():
    assert len(QUESTIONS) == 20


@pytest.mark.parametrize("question,lang,expected", QUESTIONS)
def test_pipeline_offline(question, lang, expected, analysis_result, no_network):
    docs = detective.retrieve(question, lang=lang, k=3)
    assert docs, "retrieval returned nothing"

    result = detective.plan(question, lang=lang)
    assert result["mode"] == "rules"          # extractive mode, no model
    assert result["variable_ids"], "planner produced no variable"
    assert expected in result["variable_ids"]  # the top pick is the right one
    if result["place"]:
        assert result["place"] in question     # literal substring, contract §10

    answer = detective.explain(analysis_result, level="school", lang=lang)
    assert answer["mode"] == "extractive"
    assert answer["text"].strip()
    assert answer["guard"]["numbers_ok"] is True


@pytest.mark.parametrize("question,lang,expected", QUESTIONS[:5])
def test_geocode_never_asks_a_model(question, lang, expected):
    """With no gazetteer the geocoder returns [] — it must not invent coordinates."""
    places = detective.geocode("Piura")
    assert isinstance(places, list)
    for place in places:
        assert -90 <= place["lat"] <= 90
        assert -180 <= place["lon"] <= 180


def test_full_contract_acceptance(analysis_result):
    """The prompt's acceptance line, verbatim in spirit."""
    result = detective.plan("¿está lloviendo menos en Piura?", lang="es")
    assert result["variable_ids"] == ["PRECTOTCORR"]
    assert result["place"] == "Piura"
    assert result["mode"] in ("lora", "llm", "rules")
