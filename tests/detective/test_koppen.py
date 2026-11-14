# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Köppen-Geiger: the thresholds of Peel et al. (2007), Table 1.

The inputs here are *test* fixtures (constant or textbook monthly values). They are
not data shown to users; rule 1 allows hand-written numbers inside tests/ only.
"""

from __future__ import annotations

import pytest

from src.detective.koppen import InsufficientClimatology, from_monthly_series


def constant(temp: float, precip: float) -> dict:
    return from_monthly_series({m: temp for m in range(1, 13)}, {m: precip for m in range(1, 13)})


def test_polar_group_comes_before_aridity():
    """E is a temperature test; Peel's order puts B first, and a cold desert is B."""
    assert constant(2, 30)["code"] == "ET"
    assert constant(-15, 10)["code"] == "EF"


def test_b_is_identified_before_a():
    """Hot and dry: CW/BS, not A (Peel: 'the B climates must be identified first')."""
    assert constant(30, 5)["code"] == "BWh"
    assert constant(10, 25)["code"] == "BSk"


def test_tropical_rainforest():
    assert constant(26, 250)["code"] == "Af"


def test_mediterranean(self=None):
    csa = from_monthly_series(
        {1: 9, 2: 10, 3: 12, 4: 15, 5: 19, 6: 24, 7: 27, 8: 27, 9: 23, 10: 18, 11: 13, 12: 10},
        {1: 80, 2: 70, 3: 55, 4: 40, 5: 25, 6: 10, 7: 2, 8: 3, 9: 20, 10: 50, 11: 80, 12: 90},
    )
    assert csa["code"] == "Csa"


def test_temperate_humid():
    assert constant(15, 100)["code"] == "Cfb"


def test_cold_continental():
    # Hot summer, freezing winter -> D. Very cold winter -> 'd'.
    dfa = from_monthly_series(
        {1: -5, 2: -3, 3: 3, 4: 10, 5: 17, 6: 22, 7: 25, 8: 24, 9: 19, 10: 12, 11: 5, 12: -2},
        {m: 60 for m in range(1, 13)},
    )
    assert dfa["code"].startswith("D")


def test_unusual_cold_winter_uses_d_letter():
    """'d': Not(a or b) and Tcold < -38 °C, i.e. fewer than 4 months above 10 °C."""
    dfd = from_monthly_series(
        {1: -45, 2: -40, 3: -25, 4: -5, 5: 4, 6: 12, 7: 13, 8: 12, 9: 9, 10: -2, 11: -25, 12: -40},
        {m: 25 for m in range(1, 13)},
    )
    assert dfd["code"] == "Dfd", dfd["code"]


def test_hot_summer_wins_over_cold_winter():
    """'a' is checked first: Thot >= 22 gives Dfa even with a -45 °C winter."""
    dfa = from_monthly_series(
        {1: -45, 2: -40, 3: -25, 4: 0, 5: 10, 6: 20, 7: 25, 8: 23, 9: 15, 10: 2, 11: -25, 12: -40},
        {m: 25 for m in range(1, 13)},
    )
    assert dfa["code"].endswith("a"), dfa["code"]


def test_missing_month_is_an_error_not_a_guess():
    with pytest.raises(InsufficientClimatology):
        from_monthly_series(
            {m: 20 for m in range(1, 13)},
            {m: (100 if m != 7 else None) for m in range(1, 13)},
        )


def test_result_carries_its_criteria_and_citation():
    result = constant(30, 5)
    assert result["diagnostics"]["mat_c"] == pytest.approx(30.0)
    assert "Peel" in result["method"]["citation"]
    assert result["method"]["url"].startswith("https://hess.copernicus.org/")
    assert result["names"]["es"] and result["names"]["en"]


def test_language_names_differ():
    result = constant(30, 5)
    assert result["names"]["es"] != result["names"]["en"]
