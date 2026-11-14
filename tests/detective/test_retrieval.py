# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Retrieval must return documents with score/title/url/type and never invent one."""

from __future__ import annotations

from src.detective import retrieve
from src.detective.rag import corpus_documents


def test_retrieve_contract_shape():
    results = retrieve("¿está lloviendo menos en Piura?", lang="es", k=3)
    assert results, "expected at least one document"
    for doc in results:
        assert {"id", "score", "title", "url", "type", "lang", "text"} <= set(doc)
        assert isinstance(doc["score"], float)
        assert doc["type"] in (
            "variable_card", "biome_profile", "region_note", "nasa_article",
            "paper_abstract", "method_note", "glossary",
        )


def test_retrieve_returns_nothing_for_empty_query():
    assert retrieve("", lang="es") == []
    assert retrieve("   ", lang="es") == []


def test_retrieve_only_returns_corpus_documents():
    known = {d.id for d in corpus_documents()}
    for doc in retrieve("temperatura del aire en Lima", lang="es", k=6):
        assert doc["id"] in known


def test_types_filter_is_respected():
    results = retrieve("lluvia", lang="es", k=5, types=["variable_card"])
    assert all(d["type"] == "variable_card" for d in results)


def test_spanish_question_finds_precipitation_card():
    top = retrieve("¿está lloviendo menos en Piura?", lang="es", k=1)[0]
    assert "PRECTOTCORR" in top["variables"]


def test_english_question_works_too():
    top = retrieve("is Arctic sea ice shrinking?", lang="en", k=1)[0]
    assert top["variables"][0].startswith("SEAICE_EXTENT")


def test_accents_and_case_do_not_matter():
    a = [d["id"] for d in retrieve("TEMPERATURA EN LIMA", lang="es", k=3)]
    b = [d["id"] for d in retrieve("temperatura en lima", lang="es", k=3)]
    assert a == b


def test_every_card_has_a_url():
    for doc in retrieve("agua suelo nieve ozono", lang="es", k=50, types=["variable_card"]):
        assert doc["url"], f"card {doc['id']} has no source URL"
