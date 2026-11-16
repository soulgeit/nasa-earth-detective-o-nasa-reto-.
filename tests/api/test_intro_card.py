# SI-assisted: cfable (Claude Sonnet 5.5)
"""The initial card ("how Huiracocha AI works") describes the optional language-model API and says the
truth about THIS server: nothing is announced as active until it has really answered."""

from __future__ import annotations

import re
from pathlib import Path

UI = Path(__file__).resolve().parents[2] / "src" / "ui"
SOURCE = (UI / "chat.js").read_text(encoding="utf-8")
EN = SOURCE[SOURCE.index("const EN = {"): SOURCE.index("const ES = {")]
ES = SOURCE[SOURCE.index("const ES = {"): SOURCE.index("Object.assign(I18N.STRINGS.en")]
STATES = ("off", "configured", "ready", "failing")


def value(block: str, key: str) -> str:
    match = re.search(r"^  '" + re.escape(key) + r"': '(.*)',$", block, re.M)
    assert match, f"{key} is missing"
    return match.group(1)


def test_the_api_card_and_every_server_state_exist_in_both_languages():
    for block in (EN, ES):
        for key in ("intro.api.title", "intro.api.body", "intro.api.guard"):
            assert value(block, key)
        for state in STATES:
            assert value(block, f"intro.api.here.{state}")


def test_the_pipeline_names_the_api_next_to_the_lora():
    assert "LoRA" in value(EN, "intro.step.3") and "API" in value(EN, "intro.step.3")
    assert "LoRA" in value(ES, "intro.step.3") and "API" in value(ES, "intro.step.3")


def test_only_the_active_sentence_names_the_provider_and_the_inactive_one_claims_no_external_service():
    for block in (EN, ES):
        assert "{host}" in value(block, "intro.api.here.ready")
        for state in ("off", "configured", "failing"):
            assert "{host}" not in value(block, f"intro.api.here.{state}")
    assert "no external AI service" in value(EN, "intro.api.here.off")
    assert "ningún servicio externo de IA" in value(ES, "intro.api.here.off")


def test_the_active_sentence_discloses_everything_the_provider_receives():
    """The planner gets the question; the explanation gets the statistics and the cited passages."""
    assert "question" in value(EN, "intro.api.here.ready") and "statistics" in value(EN, "intro.api.here.ready")
    assert "pregunta" in value(ES, "intro.api.here.ready") and "estadísticas" in value(ES, "intro.api.here.ready")


def test_the_card_is_drawn_from_the_state_the_server_reports():
    assert "about.deployment.llm" in SOURCE
    assert "`intro.api.here.${apiState}`" in SOURCE
    assert "els.grid.append(flow, rag, lo, rs, ap)" in SOURCE
    assert "intro-card--wide" in (UI / "styles.css").read_text(encoding="utf-8")
