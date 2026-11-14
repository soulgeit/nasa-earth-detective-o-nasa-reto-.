# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""The guard must reject hallucinated numbers and citations (contract R7)."""

from __future__ import annotations

import pytest

from src.detective.guard import check_citations, check_numbers, check_no_overclaim, run_guard

FACTS = {
    "trend": {"sen_slope_per_decade": 0.31, "sen_ci95_per_decade": [0.22, 0.40], "total_change": 1.40},
    "period": {"start": "1981-01", "end": "2025-12", "n_obs": 540, "years": 45.0},
    "significance": {"level": "p<0.01"},
}
PASSAGES = [{"n": 1, "title": "A"}, {"n": 2, "title": "B"}, {"n": 3, "title": "C"}]

# Ten trap texts. Each one MUST be rejected by the guard as a whole; the third
# element says which check is expected to catch it.
TRAPS = [
    ("La temperatura subió 0.87 °C por década.", "numbers", "number 0.87 not in facts"),
    ("La subida fue de 2.50 °C en total.", "numbers", "number 2.50 not in facts"),
    ("Hay 1200 observaciones en la serie.", "numbers", "number 1200 not in facts"),
    ("La cobertura fue del 87 por ciento.", "numbers", "number 87 not in facts"),
    ("El p-valor fue 0.0001.", "numbers", "number 0.0001 not in facts"),
    ("En 1999 empezó el cambio.", "numbers", "year 1999 not in facts"),
    ("La pendiente es 0.31 y también 0.99 °C.", "numbers", "0.99 not in facts"),
    ("Esto demuestra que la causa es el CO2.", "overclaim", "causal overclaim"),
    ("Proves that emissions are the only driver.", "overclaim", "causal overclaim"),
    ("El hielo bajó 3.14 millones de km².", "numbers", "number 3.14 not in facts"),
]


@pytest.mark.parametrize("text,kind,why", TRAPS)
def test_guard_rejects_hallucinations(text, kind, why):
    """Every trap is rejected by run_guard; the specific check is pinned too.

    The trap text may be Spanish or English; ``lang`` here is what the *user*
    asked for, and an overclaim in the other language must still be caught.
    """
    result = run_guard(text, facts=FACTS, passages=PASSAGES, lang="en", is_significant=False)
    assert not result.ok, f"guard accepted a hallucination ({why}): {text!r}"
    if kind == "numbers":
        assert not check_numbers(text, FACTS)[0], f"{why}: {text!r}"
    else:
        assert not check_no_overclaim(text, lang="en", is_significant=False)[0], f"{why}: {text!r}"


def test_guard_accepts_the_real_numbers():
    text = (
        "La temperatura subió 0.31 °C por década (intervalo 0.22 a 0.40), "
        "con un cambio total de 1.40 °C entre 1981 y 2025 y 540 observaciones."
    )
    ok, bad = check_numbers(text, FACTS)
    assert ok, f"guard rejected real facts: {bad}"


def test_guard_tolerates_rounding():
    text = "Subió 0.3 °C por década y 1.4 °C en total, con 540 datos."
    ok, bad = check_numbers(text, FACTS)
    assert ok, f"rounding tolerance too tight: {bad}"


def test_citations_must_exist():
    ok, bad = check_citations("Los datos [1] lo muestran y [2] lo confirma.", PASSAGES)
    assert ok
    ok, bad = check_citations("Según [4], esto pasa.", PASSAGES)
    assert not ok and "[4]" in bad[0]


def test_overclaim_only_rejected_when_not_significant():
    text = "Esto demuestra que la temperatura subió."
    assert not check_no_overclaim(text, lang="es", is_significant=False)[0]
    assert check_no_overclaim(text, lang="es", is_significant=True)[0]


def test_run_guard_reports_every_check():
    result = run_guard(
        "Subió 0.31 °C por década [1] y 0.99 °C más tarde.",
        facts=FACTS,
        passages=PASSAGES,
        lang="es",
        is_significant=True,
    )
    payload = result.to_public()
    assert payload["numbers_ok"] is False
    assert payload["citations_ok"] is True
    assert payload["language_ok"] is True
    assert payload["retries"] == 0
    assert payload["reasons"]


# --- false positives found in RONDA_2 §6.1 -------------------------------
# The guard rejected our own correct extractive text because it counted the
# digits of a URL and of a reference line ("Hermes 1 summary") as invented figures.

def test_urls_are_not_numbers():
    text = "Según la fuente, la serie está en https://science.nasa.gov/earth/peru-89931/ desde 1981."
    ok, bad = check_numbers(text, {"period": {"start": "1981-01"}})
    assert ok, f"a URL's digits were read as a claim: {bad}"


def test_dois_are_not_numbers():
    ok, bad = check_numbers("Método: https://doi.org/10.1016/S0022-1694(97)00125-X", {"x": 1})
    assert ok, f"a DOI was read as a claim: {bad}"


def test_reference_lines_are_metadata():
    text = (
        "La tendencia es significativa [1].\n"
        "[1] What the Mann-Kendall test is — Hermes 1 summary of cited sources: \"Non-parametric test.\"\n"
        "     https://doi.org/10.1016/S0022-1694(97)00125-X"
    )
    ok, bad = check_numbers(text, {"significance": {"is_significant": True}}, passages=[
        {"n": 1, "title": "What the Mann-Kendall test is",
         "publisher": "Hermes 1 summary of cited sources",
         "text": "The Mann-Kendall test is a non-parametric test for monotonic trend."}
    ])
    assert ok, f"reference metadata was read as a claim: {bad}"


def test_real_invented_number_still_caught_in_prose():
    """Regression guard: relaxing metadata must not open a door."""
    text = "La temperatura subió 7.5 °C por década."
    ok, _bad = check_numbers(text, {"trend": {"sen_slope_per_decade": 0.31}})
    assert not ok
