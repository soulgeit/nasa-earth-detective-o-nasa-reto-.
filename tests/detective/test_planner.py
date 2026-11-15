# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Planner: schema, hard validation, intent, and the extractive floor."""

from __future__ import annotations

import json

import pytest

from src.detective import plan
from src.detective.planner import validate_plan

PLAN_KEYS = {
    "intent", "variable_ids", "place", "place_b", "start_year", "end_year",
    "last_n_years", "hypothesis", "lang", "mode",
}


def test_plan_has_contract_shape():
    result = plan("¿está lloviendo menos en Piura?", lang="es")
    assert PLAN_KEYS <= set(result)
    assert result["intent"] in ("investigate", "compare", "define", "out_of_scope", "no_match")
    assert result["hypothesis"] in ("up", "down", "unknown")
    assert result["lang"] in ("es", "en")
    assert result["mode"] in ("rules", "llm", "lora")


def test_acceptance_case_from_the_prompt():
    """The prompt's acceptance test: rain variable, place Piura, mode reported."""
    result = plan("¿está lloviendo menos en Piura?", lang="es")
    assert result["variable_ids"] == ["PRECTOTCORR"]
    assert result["place"] == "Piura"
    assert result["hypothesis"] == "down"
    assert "mode" in result


def test_place_is_a_literal_substring_of_the_question():
    question = "¿por qué hace más calor en la Cordillera Blanca estos años?"
    result = plan(question, lang="es")
    if result["place"]:
        assert result["place"] in question


def test_off_topic_is_out_of_scope():
    result = plan("¿quién ganó el partido de fútbol?", lang="es")
    assert result["intent"] == "out_of_scope"
    assert result["variable_ids"] == []


def test_define_intent():
    assert plan("¿qué es el NDVI?", lang="es")["intent"] == "define"


def test_compare_needs_two_places():
    result = plan("compara la lluvia de Piura y Tumbes", lang="es")
    assert result["intent"] == "compare"
    assert result["place"] and result["place_b"]
    assert result["place"] != result["place_b"]


def test_years_are_extracted():
    result = plan("temperatura en Lima entre 1990 y 2020", lang="es")
    assert result["start_year"] == 1990
    assert result["end_year"] == 2020


def test_last_n_years():
    assert plan("lluvia en Iquitos en los últimos 20 años", lang="es")["last_n_years"] == 20


def test_requested_language_is_honoured():
    """`lang` is the caller's choice (contract §6: lang in es|en) — the UI owns it."""
    assert plan("is Lima getting hotter?", lang="en")["lang"] == "en"
    assert plan("¿hace más calor en Lima?", lang="es")["lang"] == "es"


def test_invalid_language_falls_back_to_detection():
    assert plan("is Lima getting hotter?", lang="fr")["lang"] == "en"
    assert plan("¿hace más calor en Lima?", lang="")["lang"] == "es"

CANDIDATES = {"T2M", "PRECTOTCORR", "GWETTOP"}
QUESTION = "¿está lloviendo menos en Piura?"


def _valid(**over):
    base = {
        "intent": "investigate", "variable_ids": ["PRECTOTCORR"], "place": "Piura",
        "place_b": None, "start_year": None, "end_year": None, "last_n_years": None,
        "hypothesis": "down", "lang": "es",
    }
    base.update(over)
    return base


def test_validate_accepts_a_clean_plan():
    result, reason = validate_plan(_valid(), question=QUESTION, candidates=CANDIDATES, lang="es")
    assert reason is None and result["variable_ids"] == ["PRECTOTCORR"]


def test_validate_accepts_json_text():
    result, reason = validate_plan(json.dumps(_valid()), question=QUESTION, candidates=CANDIDATES, lang="es")
    assert reason is None


@pytest.mark.parametrize("over,needle", [
    ({"variable_ids": ["SEAICE_EXTENT_N"]}, "not among candidates"),
    ({"variable_ids": ["NOT_A_VAR"]}, "not among candidates"),
    ({"place": "Lima"}, "not a substring"),
    ({"intent": "diagnose"}, "not allowed"),
    ({"hypothesis": "maybe"}, "not allowed"),
    ({"start_year": "1990"}, "bad year"),
    ({"variable_ids": []}, "need at least one variable"),
])
def test_validate_rejects(over, needle):
    result, reason = validate_plan(_valid(**over), question=QUESTION, candidates=CANDIDATES, lang="es")
    assert result is None and needle in reason, reason


def test_validate_rejects_non_json_text():
    result, reason = validate_plan("not json at all", question=QUESTION, candidates=CANDIDATES, lang="es")
    assert result is None and "not JSON" in reason


def test_validate_rejects_place_b_outside_question():
    result, reason = validate_plan(_valid(intent="compare", place_b="Cusco"),
                                   question=QUESTION, candidates=CANDIDATES, lang="es")
    assert result is None and "place_b" in reason


# --- T4: training and inference must use the same message --------------------

def _dataset_system_prompt():
    import json as _json
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "data" / "lora" / "train.jsonl"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        return _json.loads(fh.readline())["messages"][0]["content"]


def test_system_prompt_is_identical_to_the_dataset():
    from src.detective.planner import _system_prompt

    expected = _dataset_system_prompt()
    if expected is None:
        pytest.skip("data/lora/train.jsonl not published")
    assert _system_prompt() == expected


def test_candidate_lines_match_the_dataset_shape():
    from src.detective.planner import _user_message, debug_candidates

    question = "¿qué es la temperatura?"
    message = _user_message(question, debug_candidates(question, lang="es", k=4), lang="es")
    lines = message.splitlines()
    assert lines[0] == f"QUESTION: {question}"
    assert lines[1] == "CANDIDATES:"
    for line in lines[2:]:
        # "- T2M: Temperatura del aire a 2 m (°C) - Cuánto calor hace..."
        assert line.startswith("- ")
        assert ": " in line
        assert " - " in line, f"missing the definition separator: {line}"


def _lora_settings(monkeypatch):
    """Switch the planner to `local-lora` for one test (regla 22: no disk state)."""
    from src.detective import config as cfg
    from src.detective import planner as planner_module

    monkeypatch.setattr(planner_module, "SETTINGS", cfg.Settings(
        ai_mode="full", llm_base_url="http://localhost:11434/v1",
        planner_model="local-lora", explain_model="",
        embed_base_url="http://localhost:11434", embed_model="",
        data_dir=cfg.SETTINGS.data_dir, catalog_dir=cfg.SETTINGS.catalog_dir,
        knowledge_dir=cfg.SETTINGS.knowledge_dir, index_dir=cfg.SETTINGS.index_dir,
        request_timeout=5.0,
    ), raising=False)
    return planner_module


# A module-scoped fixture is NOT possible here (each test needs a fresh fake); the
# global cleanup is applied only to the tests in this file that exercise the LoRA,
# by the `_clean_serve` fixture they request explicitly.


@pytest.fixture()
def _clean_serve(monkeypatch):
    """RONDA_4 rule 22: these tests must not depend on what is on disk or in memory.

    `src/ml/serve.py` keeps the loaded model in module globals, so a test elsewhere
    that loaded the real adapter would make `plan_with_lora` answer from it and the
    "adapter missing" case would silently succeed (that is the §2.4 defect of the
    ml lane, not ours to fix). We drop the module before and after each test here
    and undo the globals, so every test installs its own fake explicitly.
    """
    import sys

    saved = sys.modules.pop("src.ml.serve", None)
    parent = sys.modules.get("src.ml")
    if parent is not None and getattr(parent, "serve", None) is saved:
        try:
            delattr(parent, "serve")
        except AttributeError:
            pass
    yield
    sys.modules.pop("src.ml.serve", None)
    if parent is not None:
        current = getattr(parent, "serve", None)
        if current is not None:
            try:
                delattr(parent, "serve")
            except AttributeError:
                pass
    if saved is not None:
        for attr in ("_GLOBAL_MODEL", "_GLOBAL_TOKENIZER"):
            if hasattr(saved, attr):
                setattr(saved, attr, None)
        sys.modules["src.ml.serve"] = saved
        if parent is not None:
            parent.serve = saved


def test_local_lora_without_serving_falls_back_to_rules(monkeypatch, _clean_serve):
    """RONDA_4 rule 22: the test simulates ABSENCE, it does not depend on the disk.

    `src.ml.serve.plan_with_lora` raises, which is what happens on a machine with
    no adapter or no GPU. The planner must fall back to rules and say why.
    """
    import sys
    import types

    sys.modules.pop("src.ml.serve", None)
    import src.ml as _ml_parent
    if hasattr(_ml_parent, "serve"):
        try:
            delattr(_ml_parent, "serve")
        except AttributeError:
            pass
    fake = types.ModuleType("src.ml.serve")

    def plan_with_lora(*args, **kwargs):
        raise FileNotFoundError("no adapter on this machine (simulated)")

    fake.plan_with_lora = plan_with_lora
    monkeypatch.setitem(sys.modules, "src.ml.serve", fake)
    planner_module = _lora_settings(monkeypatch)

    result = planner_module.plan("¿está lloviendo menos en Piura?", lang="es")
    assert result["mode"] == "rules"
    assert result["planner"] == "rules"
    assert "local_lora" in result.get("note", "")


def test_local_lora_with_a_valid_plan_says_lora(monkeypatch, _clean_serve):
    """RONDA_4 rule 22 (opposite case): a simulated adapter wins and is reported."""
    import json as _json
    import sys
    import types

    sys.modules.pop("src.ml.serve", None)
    import src.ml as _ml_parent
    if hasattr(_ml_parent, "serve"):
        try:
            delattr(_ml_parent, "serve")
        except AttributeError:
            pass
    fake = types.ModuleType("src.ml.serve")
    fake.plan_with_lora = lambda question, candidates=None, lang="es": {
        "intent": "investigate",
        "variable_ids": ["PRECTOTCORR"],
        "place": "Piura",
        "place_b": None,
        "start_year": None,
        "end_year": None,
        "last_n_years": None,
        "hypothesis": "down",
        "lang": "es",
    }
    monkeypatch.setitem(sys.modules, "src.ml.serve", fake)
    planner_module = _lora_settings(monkeypatch)

    result = planner_module.plan("¿está lloviendo menos en Piura?", lang="es")
    assert result["mode"] == "lora"
    assert result["planner"] == "lora"
    assert result["variable_ids"] == ["PRECTOTCORR"]


def test_local_lora_returning_a_planned_variable_is_rejected(monkeypatch, _clean_serve):
    """RONDA_4 rule 19 + §5.2: the model proposes, the rules verify."""
    import sys
    import types

    sys.modules.pop("src.ml.serve", None)
    import src.ml as _ml_parent
    if hasattr(_ml_parent, "serve"):
        try:
            delattr(_ml_parent, "serve")
        except AttributeError:
            pass
    fake = types.ModuleType("src.ml.serve")
    fake.plan_with_lora = lambda question, candidates=None, lang="es": {
        "intent": "investigate",
        "variable_ids": ["MODIS_NDVI"],
        "place": "Madre de Dios",
        "place_b": None,
        "start_year": None, "end_year": None, "last_n_years": None,
        "hypothesis": "down", "lang": "es",
    }
    monkeypatch.setitem(sys.modules, "src.ml.serve", fake)
    planner_module = _lora_settings(monkeypatch)

    result = planner_module.plan("¿la selva de Madre de Dios pierde vegetación?", lang="es")
    assert result["planner"] == "rules", "a planned variable must not come out of the model path"
    assert "MODIS_NDVI" not in (result.get("variable_ids") or [])
    assert result.get("note", "").startswith("lora_rejected")


def test_local_lora_inventing_a_place_drops_it(monkeypatch, _clean_serve):
    """§5.2: a place the gazetteer cannot resolve is removed, not shown.

    (Not "Atlantis": there is a real town called Atlantis in South Africa, so it
    resolves. "Xanaduprobe" does not exist in the gazetteer.)
    """
    import sys
    import types

    sys.modules.pop("src.ml.serve", None)
    import src.ml as _ml_parent
    if hasattr(_ml_parent, "serve"):
        try:
            delattr(_ml_parent, "serve")
        except AttributeError:
            pass
    fake = types.ModuleType("src.ml.serve")
    fake.plan_with_lora = lambda question, candidates=None, lang="es": {
        "intent": "investigate",
        "variable_ids": ["T2M"],
        "place": "Xanaduprobe",
        "place_b": None,
        "start_year": None, "end_year": None, "last_n_years": None,
        "hypothesis": "unknown", "lang": "es",
    }
    monkeypatch.setitem(sys.modules, "src.ml.serve", fake)
    planner_module = _lora_settings(monkeypatch)

    # The invented name must appear in the question for validation to reach it.
    result = planner_module.plan("temperatura en Xanaduprobe", lang="es")
    assert result["place"] is None
    assert "dropped_unresolved_place" in (result.get("why") or "")


# --- RONDA_3 §4.2: planned variables from the catalogue ---------------------

def test_planned_variable_is_named_and_explained(monkeypatch, tmp_path):
    """A product in the catalogue's `planned` section must be named, not just refused."""
    import json as _json
    from src.detective import corpus as corpus_module

    catalog = {
        "schema": "catalog/2",
        "variables": [{"id": "T2M", "names": {"es": "Temperatura", "en": "Temperature"}, "unit": "°C"}],
        "planned": [{
            "id": "MODIS_NDVI",
            "available": False,
            "names": {"es": "NDVI (MODIS)", "en": "NDVI (MODIS)"},
            "simple_definition": {
                "es": "Se carga subiendo el CSV de NDVI exportado de Giovanni.",
                "en": "Load it by uploading the NDVI CSV exported from Giovanni.",
            },
            "source": {"via": "Giovanni (GES DISC)", "url": "https://giovanni.gsfc.nasa.gov/giovanni/"},
        }],
    }
    path = tmp_path / "variables.json"
    path.write_text(_json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(corpus_module.SETTINGS.__class__, "catalog_dir", property(lambda self: tmp_path), raising=False)
    monkeypatch.setattr(corpus_module, "SETTINGS", corpus_module.SETTINGS, raising=False)

    from src.detective import planner as planner_module

    monkeypatch.setattr(planner_module, "_catalog_variable_ids", lambda: {"T2M"})
    monkeypatch.setattr(
        planner_module,
        "_planned_card",
        lambda vid: next((c for c in catalog["planned"] if c["id"] == vid), None),
    )

    result = planner_module._coverage(
        "¿la selva pierde vegetación?", {"intent": "investigate", "mode": "rules", "variable_ids": []}, "es"
    )
    assert result["intent"] == "no_match"
    assert result["missing"] == ["NDVI (MODIS)"]
    assert result["how_to_load"] and "Giovanni" in result["how_to_load"][0]
    assert result["available"] is False


def test_planned_cards_are_read_from_the_catalog():
    from src.detective.corpus import load_catalog_cards

    cards = load_catalog_cards()
    planned = [c for c, available in cards if not available]
    for card in planned:
        assert card.get("available") is False, "a planned card must say so in its payload"


# --- RONDA_5 §4.5: the lexicon must not confuse a place with a process --------

@pytest.mark.parametrize("question,lang,expected", [
    # "Desert" here is part of a place name, not a request for soil moisture.
    ("Is dust from the Sechura Desert travelling farther now?", "en", "AOD_55"),
    # The same word inside "turning into desert" IS a desertification question.
    ("Which variable tells me if Piura is turning into desert?", "en", "GWETTOP"),
    # Reverse direction: a phrase split across the sentence must still match.
    ("Is the soil in Ica drying out?", "en", "GWETTOP"),
    ("¿El aire de Lima está más sucio que hace veinte años?", "es", "AOD_55"),
])
def test_desert_and_drying_are_not_confused(question, lang, expected):
    result = plan(question, lang=lang)
    assert expected in result["variable_ids"], result["variable_ids"]


def test_all_reference_questions_are_answered_by_rules():
    """RONDA_5: the rules must answer 50/50 on the golden set (was 49/50)."""
    from src.detective.config import SETTINGS

    path = SETTINGS.knowledge_dir / "golden_questions.jsonl"
    if not path.exists():
        pytest.skip("golden_questions.jsonl not published")
    import json as _json

    failures = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = _json.loads(line)
        result = plan(row["question"], lang=row.get("lang", "es"))
        expected = set(row.get("expected_variable_ids") or [])
        got = set(result.get("variable_ids") or [])
        if not (expected & got) or result["intent"] not in ("investigate", "compare", "define"):
            failures.append((row["question"], sorted(got), sorted(expected)))
    assert not failures, f"{len(failures)} reference questions still fail: {failures}"
