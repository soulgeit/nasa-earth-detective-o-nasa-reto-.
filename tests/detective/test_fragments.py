# SI-assisted: cfable (Claude Fable 5.2)
"""Knowledge fragments (RONDA_7): one file per lane, loaded defensively."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from src.detective import corpus, narrative

ROOT = Path(__file__).resolve().parents[2]


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_fragments", ROOT / "scripts" / "validate_fragments.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(doc_id: str, *, title: str, text: str | None = None, **extra) -> dict:
    text = text or (
        "Huancayo se ubica en el valle del Mantaro, a unos 3 250 m sobre el nivel del mar. "
        "La temporada de lluvias va de octubre a abril y las heladas son más frecuentes "
        "entre mayo y agosto, cuando el cielo está despejado y el aire es seco. " * 2
    )
    row = {
        "id": doc_id,
        "type": "region_note",
        "title": title,
        "url": "https://www.senamhi.gob.pe/?p=pronostico-detalle&dp=12",
        "publisher": "SENAMHI",
        "date": "2024",
        "lang": "es",
        "text": text,
        "variables": ["T2M"],
        "places": ["huancayo"],
        "license": "Gobierno del Perú (uso público con atribución)",
        "fetched_at": "2026-11-15T19:00:00Z",
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "is_quotation": False,
        "summary_by": "rag-huancayo",
    }
    row.update(extra)
    return row


@pytest.fixture()
def knowledge(tmp_path, monkeypatch):
    """A private knowledge folder with the real catalogue next to it."""
    folder = tmp_path / "knowledge"
    (folder / "regions").mkdir(parents=True)
    settings = dataclasses.replace(corpus.SETTINGS, knowledge_dir=folder)
    monkeypatch.setattr(corpus, "SETTINGS", settings)
    return folder


def _write(path: Path, rows: list) -> None:
    lines = [r if isinstance(r, str) else json.dumps(r, ensure_ascii=False) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_fragments_are_loaded_and_a_bad_row_never_breaks_the_corpus(knowledge):
    _write(
        knowledge / "regions" / "huancayo.jsonl",
        [
            _row("region-huancayo-clima-1", title="Clima de Huancayo"),
            "{this is not json",
            {"id": "region-huancayo-roto", "type": "region_note"},  # fields missing
            _row("region-huancayo-clima-2", title="Heladas en Huancayo", type="not_a_type"),
        ],
    )
    docs = {d.id: d for d in corpus.load_corpus()}

    assert "region-huancayo-clima-1" in docs
    assert docs["region-huancayo-clima-1"].places == ["huancayo"]
    assert "huancayo" in docs["region-huancayo-clima-1"].searchable()
    assert "region-huancayo-roto" not in docs and "region-huancayo-clima-2" not in docs
    assert len(corpus.FRAGMENT_ERRORS) == 3, corpus.FRAGMENT_ERRORS
    assert all(err.startswith("regions/huancayo.jsonl:") for err in corpus.FRAGMENT_ERRORS)


def test_a_fragment_can_supersede_an_older_document_without_editing_its_file(knowledge):
    _write(knowledge / "docs.jsonl", [_row("old-note", title="Nota antigua de Huancayo")])
    _write(
        knowledge / "regions" / "huancayo.jsonl",
        [_row("region-huancayo-mejor", title="Huancayo: nota con fuente oficial",
              supersedes=["old-note"], supersedes_reason="fuente primaria")],
    )
    ids = {d.id for d in corpus.load_corpus()}
    assert "region-huancayo-mejor" in ids
    assert "old-note" not in ids


def test_files_outside_the_three_lanes_are_not_loaded(knowledge):
    _write(knowledge / "golden_cities.jsonl", [_row("region-huancayo-x", title="Huancayo")])
    (knowledge / "borradores").mkdir()
    _write(knowledge / "borradores" / "huancayo.jsonl", [_row("region-huancayo-y", title="Huancayo")])
    _write(knowledge / "regions" / "_huancayo.tmp.jsonl", [_row("region-huancayo-z", title="Huancayo")])
    ids = {d.id for d in corpus.load_corpus()}
    assert not {"region-huancayo-x", "region-huancayo-y", "region-huancayo-z"} & ids


def test_the_gate_rejects_what_the_contract_forbids():
    gate = _load_validator()
    variables = gate.catalog_ids()

    def problems(row, folder="regions", stem="huancayo"):
        return gate.check_row(row, folder=folder, stem=stem, variables=variables)

    good = _row("region-huancayo-clima-1", title="Clima de Huancayo")
    assert problems(good) == []
    # another lane's prefix
    assert any("id must start" in p for p in problems(_row("region-lima-clima-1", title="Clima de Huancayo")))
    # the city must be named, so the explanation can match the place
    assert any("title must name the city" in p for p in problems(_row("region-huancayo-a", title="Clima del valle")))
    # a tampered text no longer matches its hash
    tampered = dict(good, text=good["text"] + " Dato añadido sin recalcular.")
    assert any("sha256" in p for p in problems(tampered))
    # a variable that the catalogue does not carry
    assert any("not in the catalogue" in p for p in problems(dict(good, variables=["INVENTADA"])))
    # a summary without an author
    assert any("summary_by" in p for p in problems(dict(good, summary_by=None)))
    # computed facts are never quotations and must say where they come from
    fact = _row("fact-huancayo-t2m", title="Tendencia de T2M en Huancayo", is_quotation=True)
    found = problems(fact, folder="facts")
    assert any("never quotations" in p for p in found) and any("generated_from" in p for p in found)


def test_the_fragments_in_the_repo_pass_the_gate(capsys):
    """Red here means a lane pushed a file that the app is silently skipping."""
    gate = _load_validator()
    code = gate.main([])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    corpus.load_corpus()
    assert corpus.FRAGMENT_ERRORS == []


def test_a_short_place_name_is_matched_as_a_word_not_as_a_substring(monkeypatch):
    """"Ica" must not cite an article about Africa (it used to: substring match)."""
    base = {"url": "https://example.org/", "type": "nasa_article", "lang": "es", "publisher": "NASA",
            "is_quotation": True, "variables": ["PRECTOTCORR"], "places": [], "text": "texto"}
    documents = [
        dict(base, id="africa", title="La lluvia cambia en África", url="https://example.org/africa"),
        dict(base, id="ica-1", title="Lluvias en Ica durante El Niño", url="https://example.org/ica"),
        dict(base, id="ica-otra", title="Polvo sobre Ica", url="https://example.org/polvo", variables=["AOD_55"]),
    ]

    def fake_retrieve(query, *, lang="es", k=6, types=None):
        if types and "method_note" in types:
            return []
        return [dict(d) for d in documents]

    monkeypatch.setattr(narrative, "retrieve", fake_retrieve)
    monkeypatch.setattr(narrative, "_documents_for_variable", lambda variable_id, lang: [])
    analysis = {"variable": {"id": "PRECTOTCORR"}, "region": {"name": "Ica, PE"}}

    cited = [p["id"] for p in narrative._passages_for(analysis, lang="es")]
    assert cited == ["ica-1"]
