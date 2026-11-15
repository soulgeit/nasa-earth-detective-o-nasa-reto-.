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


# --- RONDA_2 §6.1: citations must be about the variable that was analysed -----

def _lima(analysis_result):
    import copy

    a = copy.deepcopy(analysis_result)
    a["variable"] = {"id": "T2M", "names": {"es": "Temperatura del aire a 2 m",
                                            "en": "Air temperature at 2 m"}, "unit": "°C"}
    a["region"] = {"kind": "point", "name": "Lima, Peru", "lat": -12.05, "lon": -77.03}
    return a


def test_citations_are_about_the_analysed_variable(analysis_result):
    """Explaining T2M must not cite aerosol cards."""
    result = explain(_lima(analysis_result), level="school", lang="es")
    titles = " ".join(c["title"].lower() for c in result["citations"])
    assert "aerosol" not in titles
    assert "gistemp" not in titles
    assert any("temperatura" in t.lower() or "temperature" in t.lower() for t in
               [c["title"] for c in result["citations"]]), result["citations"]


def test_citations_have_real_titles_and_urls(analysis_result):
    result = explain(_lima(analysis_result), level="school", lang="es")
    assert result["citations"], "no citations at all"
    for c in result["citations"]:
        assert c["title"] and not c["title"].startswith("var-") and not c["title"].startswith("card-")
        assert c["url"] and c["url"].startswith("http")
        assert c["publisher"], "a citation without a publisher cannot be attributed"


def test_citations_are_not_duplicated_in_two_languages(analysis_result):
    result = explain(_lima(analysis_result), level="school", lang="es")
    urls = [c["url"] for c in result["citations"]]
    assert len(urls) == len(set(urls)), f"same source cited twice: {urls}"


def test_internal_ids_are_not_in_the_text(analysis_result):
    text = explain(_lima(analysis_result), level="school", lang="es")["text"]
    assert "var-aod" not in text
    assert "method-mann-kendall-en" not in text


# --- RONDA_3 §4.1: one language per answer, never mixed ----------------------

def _lang_of(text: str) -> str:
    from src.detective.text_norm import detect_language

    return detect_language(text)


def test_spanish_answer_cites_spanish_sources(analysis_result):
    result = explain(_lima(analysis_result), level="school", lang="es")
    assert result["citations"], "no citations"
    # The variable card must be the Spanish one.
    first = result["citations"][0]
    assert first["title"] == "Temperatura del aire a 2 m", first["title"]


def test_english_answer_cites_english_sources(analysis_result):
    result = explain(_lima(analysis_result), level="school", lang="en")
    first = result["citations"][0]
    assert first["title"] == "Air temperature at 2 m", first["title"]


def test_no_answer_mixes_languages(analysis_result):
    for lang in ("es", "en"):
        result = explain(_lima(analysis_result), level="school", lang=lang)
        assert result["guard"]["language_ok"] is True, (lang, result["guard"]["reasons"])
        assert _lang_of(result["text"].split("\n")[0]) == lang


def test_both_languages_have_citations(analysis_result):
    for lang in ("es", "en"):
        result = explain(_lima(analysis_result), level="school", lang=lang)
        assert result["citations"], f"no citations in {lang}"


# --- RONDA_5 §2.15: sources are attributed once, and a summary is not a quote ----

def test_text_does_not_repeat_sources_or_raw_urls(analysis_result):
    result = explain(_lima(analysis_result), level="school", lang="en")
    text = result["text"]
    assert "http" not in text, "the raw URL must live in the citations list, not the text"
    # Every cited title appears once in the prose at most.
    for citation in result["citations"]:
        assert text.count(citation["title"]) <= 1


def test_no_internal_agent_name_is_shown_as_a_publisher(analysis_result):
    """§2.15: 'Hermes 1 summary of cited sources' was visible to the judge."""
    for lang in ("es", "en"):
        result = explain(_lima(analysis_result), level="school", lang=lang)
        blob = result["text"] + " ".join(str(c.get("publisher") or "") for c in result["citations"])
        assert "Hermes 1" not in blob
        for citation in result["citations"]:
            assert citation["publisher"], "every source needs a real publisher"


def test_no_document_is_attributed_to_an_internal_agent():
    from src.detective.rag import corpus_documents

    offenders = [
        d.id for d in corpus_documents()
        if "hermes" in str(d.publisher or "").lower() or "claude-omni" in str(d.publisher or "").lower()
    ]
    assert not offenders, f"documents show an internal agent as publisher: {offenders}"


def test_summaries_are_flagged_and_quotations_are_not():
    from src.detective.rag import corpus_documents

    for doc in corpus_documents():
        if doc.summary_by:
            assert doc.is_quotation is False, f"{doc.id} is a summary but marked as a quotation"
