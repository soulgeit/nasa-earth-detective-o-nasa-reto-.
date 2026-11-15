# SI-assisted: cfable (Claude Fable 5.2)
"""Huiracocha IA talks (RONDA_7). Offline: no network, no model."""

from __future__ import annotations

import pytest

from src import detective
from src.detective import conversation
from src.detective.conversation import SUGGESTIONS


def say(message, lang=None, **context):
    return detective.chat(message, lang=lang, context=context or None)


@pytest.mark.parametrize("message,lang", [("hola", "es"), ("Hola!", "es"), ("buenas tardes", "es"), ("ola", "es"),
                                          ("hi", "en"), ("hello", "en"), ("Good morning", "en")])
def test_a_greeting_is_answered_with_a_greeting(message, lang):
    """The reported bug: "hola" came back as intent=no_match with no text."""
    reply = say(message)
    assert reply["kind"] == "greeting"
    assert reply["lang"] == lang
    assert "Huiracocha" in reply["reply"]
    assert reply["plan"] is None and reply["action"] is None
    assert len(reply["suggestions"]) >= 3


def test_a_two_letter_message_is_not_an_error():
    """"hi" was rejected by the API with INVALID_REQUEST (minimum 3 characters)."""
    assert say("hi")["kind"] == "greeting"


def test_how_are_you_is_small_talk_and_como_is_not_a_city_in_italy():
    reply = say("Hola, ¿cómo estás?")
    assert reply["kind"] == "greeting"
    assert "cómo" not in reply["reply"].split("Soy")[1]
    vegetation = say("¿cómo está la vegetación en Ica?")
    assert all("cómo" not in s for s in vegetation["suggestions"]), vegetation["suggestions"]


@pytest.mark.parametrize("message,kind", [
    ("¿quién eres?", "identity"), ("who are you?", "identity"),
    ("¿qué puedes hacer?", "help"), ("ayuda", "help"), ("what can you do", "help"),
    ("gracias", "thanks"), ("thanks", "thanks"), ("chau", "farewell"),
    ("¿qué variables tienes?", "variables"), ("which variables do you have?", "variables"),
    ("¿de dónde salen los datos?", "data_source"), ("is the data real?", "data_source"),
    ("¿qué ciudades conoces?", "places"),
    ("¿quién ganó el partido?", "out_of_scope"),
    ("asdf qwerty zxcv", "fallback"),
])
def test_small_talk_and_meta_questions(message, kind):
    reply = say(message)
    assert reply["kind"] == kind, reply["reply"]
    assert reply["reply"] and reply["plan"] is None


def test_the_variable_list_counts_what_the_catalogue_really_has():
    from src.detective.corpus import load_catalog_cards

    ready = sum(1 for _card, available in load_catalog_cards() if available)
    reply = say("¿qué variables tienes?")
    assert f"{ready} variables" in reply["reply"]
    assert ready >= 35


@pytest.mark.parametrize("lang", ["es", "en"])
def test_every_suggested_question_really_works(lang):
    """A chip that leads to "I did not understand" would be a broken promise."""
    for question in SUGGESTIONS[lang]:
        reply = say(question, lang)
        assert reply["kind"] in ("plan", "scan"), (question, reply["kind"], reply["reply"])
        assert reply["lang"] == lang, question
        assert reply["action"] in ("analyze", "compare", "scan")
        assert (reply["plan"] or {}).get("place"), question


def test_a_question_becomes_a_plan_that_says_what_will_happen():
    reply = say("¿Llueve menos en Ica?")
    assert reply["kind"] == "plan" and reply["action"] == "analyze"
    assert reply["plan"]["variable_ids"] == ["PRECTOTCORR"]
    assert reply["plan"]["place"] == "Ica"
    assert reply["plan"]["hypothesis"] == "down"
    assert "Ica" in reply["reply"] and "NASA POWER" in reply["reply"]
    assert reply["context"] == {"place": "Ica", "place_b": None, "variable_id": "PRECTOTCORR"}


def test_follow_ups_keep_the_thread():
    first = say("¿Llueve menos en Ica?")
    place_changed = say("¿y en Huancayo?", **first["context"])
    assert place_changed["plan"]["variable_ids"] == ["PRECTOTCORR"]
    assert place_changed["plan"]["place"] == "Huancayo"

    variable_changed = say("¿y la temperatura?", **place_changed["context"])
    assert variable_changed["plan"]["variable_ids"] == ["T2M"]
    assert variable_changed["plan"]["place"] == "Huancayo"

    compared = say("compáralo con Lima", **variable_changed["context"])
    assert compared["action"] == "compare"
    assert (compared["plan"]["place"], compared["plan"]["place_b"]) == ("Huancayo", "Lima")


def test_a_variable_without_a_place_asks_where_and_a_place_without_a_variable_asks_what():
    where = say("temperatura")
    assert where["kind"] == "ask_place" and where["context"]["variable_id"] == "T2M"
    assert any("Huancayo" in s for s in where["suggestions"])

    what = say("Andahuaylas")
    assert what["kind"] == "place_briefing" and what["context"]["place"] == "Andahuaylas"
    assert any("Andahuaylas" in s for s in what["suggestions"])
    # every offered follow-up is answerable
    for suggestion in what["suggestions"]:
        assert say(suggestion)["kind"] in ("plan", "scan"), suggestion


def test_a_global_series_needs_no_place():
    reply = say("¿Se derrite el hielo del Ártico?")
    assert reply["kind"] == "plan" and reply["plan"]["variable_ids"] == ["SEAICE_EXTENT_N"]


def test_definitions_come_from_the_catalogue_and_never_from_a_loose_match():
    rain = say("¿qué es la precipitación?")
    assert rain["kind"] == "define" and "PRECTOTCORR" in rain["reply"]
    assert rain["sources"] and rain["sources"][0]["url"].startswith("https://")
    # "El Niño" is listed among the drivers of surface pressure; that is not a definition.
    nino = say("¿qué es El Niño?")
    assert nino["kind"] in ("knowledge", "fallback")
    assert "PS" not in nino["reply"] and "kPa" not in nino["reply"]


def test_a_method_question_is_about_statistics_not_about_kendall_florida():
    reply = say("¿qué es Mann-Kendall?")
    assert reply["kind"] == "method"
    assert "Mann-Kendall" in reply["reply"]
    assert reply["plan"] is None


def test_a_product_that_is_not_loaded_is_named_not_replaced():
    reply = say("¿cómo está la vegetación en Ica?")
    assert reply["kind"] == "missing_variable"
    assert "NDVI" in reply["reply"]
    assert reply["plan"] is None


def test_what_is_changing_asks_for_a_scan_of_the_place():
    reply = say("¿Qué está cambiando en Huancayo?")
    assert reply["kind"] == "scan" and reply["action"] == "scan"
    assert reply["plan"]["place"] == "Huancayo"
    carried = say("¿qué está cambiando?", place="Lima")
    assert carried["action"] == "scan" and carried["plan"]["place"] == "Lima"


def test_local_knowledge_is_quoted_with_its_source(monkeypatch):
    """When a city lane has fed the corpus, the plan cites what is known locally."""
    note = {
        "id": "region-huancayo-heladas-01", "type": "region_note", "lang": "es",
        "title": "Heladas en Huancayo y el valle del Mantaro", "publisher": "SENAMHI",
        "url": "https://www.senamhi.gob.pe/heladas", "variables": ["FROST_DAYS"], "places": ["huancayo"],
        "is_quotation": False, "text": "En Huancayo las heladas se concentran entre mayo y agosto, con cielo despejado.",
    }
    from src.detective import rag

    monkeypatch.setattr(rag, "retrieve", lambda query, **kw: [dict(note)])
    reply = say("¿Hay menos heladas en Huancayo?")
    assert reply["kind"] == "plan"
    assert "SENAMHI" in reply["reply"] and "mayo y agosto" in reply["reply"]
    assert reply["sources"][0]["url"] == "https://www.senamhi.gob.pe/heladas"
    assert "«" not in reply["reply"].split("Contexto local")[1], "a summary is never shown as a quotation"


def test_a_bad_context_is_ignored_not_trusted():
    reply = say("¿y en Huancayo?", variable_id="NO_EXISTE", place="x" * 500)
    assert reply["kind"] == "place_briefing"
    assert conversation._clean_context("not a dict") == {}
