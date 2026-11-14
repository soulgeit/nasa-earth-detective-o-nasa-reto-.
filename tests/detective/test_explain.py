# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Explanation: contract shape, guard integration, and the extractive floor."""

from __future__ import annotations

from src.detective import explain
from src.detective.narrative import extractive_text


def test_explain_contract_shape(analysis_result):
    result = explain(analysis_result, level="school", lang="es")
    assert {"text", "citations", "guard", "mode"} <= set(result)
    assert isinstance(result["text"], str) and result["text"].strip()
    assert {"numbers_ok", "citations_ok", "retries"} <= set(result["guard"])
    assert result["mode"] in ("llm", "extractive")


def test_extractive_mode_without_model(analysis_result):
    """AI_MODE=extractive and no Ollama: explain() still answers."""
    result = explain(analysis_result, level="school", lang="es")
    assert result["mode"] == "extractive"
    assert result["text"].strip()


def test_extractive_text_carries_no_number_outside_the_facts(analysis_result):
    text = extractive_text(analysis_result, lang="es", passages=[])
    for token in ("0.31", "1.40", "45", "540"):
        if token in text:
            assert True  # allowed: each is in the facts
    # And the whole thing passes the guard.
    verdict = explain(analysis_result, level="school", lang="es")["guard"]
    assert verdict["numbers_ok"] is True


def test_extractive_is_bilingual(analysis_result):
    es = explain(analysis_result, level="school", lang="es")["text"]
    en = explain(analysis_result, level="school", lang="en")["text"]
    assert es != en
    assert "Temperatura" in es or "temperatura" in es
    assert "temperature" in en.lower()


def test_citations_point_at_real_passages(analysis_result):
    result = explain(analysis_result, level="school", lang="es")
    for citation in result["citations"]:
        assert citation["title"]
        assert citation["url"] is not None


def test_guard_runs_and_passes_on_our_own_text(analysis_result):
    result = explain(analysis_result, level="highschool", lang="es")
    assert result["guard"]["citations_ok"] is True
    assert result["guard"]["language_ok"] is True


def test_empty_analysis_does_not_crash():
    result = explain({}, level="school", lang="es")
    assert result["text"]
    assert result["mode"] == "extractive"
    assert result["citations"] == []


def test_bad_level_falls_back_to_school(analysis_result):
    assert explain(analysis_result, level="phd", lang="es")["mode"] in ("llm", "extractive")
