# SI-assisted: cfable (Claude Sonnet 5.5)
"""The LoRA planner can never hold a request (or the server) hostage.

Incident, 2026-11-15 17:50: the first chat message loaded SmolLM2-1.7B + the adapter on a
CPU inside the request and the public service stopped answering everybody. The adapter is
simulated here with a fake that stays slow until the test lets it go.
"""

from __future__ import annotations

import concurrent.futures
import sys
import threading
import time
import types

import pytest

QUESTION = "¿Llueve menos en Ica?"


@pytest.fixture()
def lora(monkeypatch):
    from src.detective import config as cfg
    from src.detective import planner

    def settings(mode="full"):
        return cfg.Settings(
            ai_mode=mode, llm_base_url="http://localhost:11434/v1", planner_model="local-lora",
            explain_model="", embed_base_url="http://localhost:11434", embed_model="",
            data_dir=cfg.SETTINGS.data_dir, catalog_dir=cfg.SETTINGS.catalog_dir,
            knowledge_dir=cfg.SETTINGS.knowledge_dir, index_dir=cfg.SETTINGS.index_dir,
            request_timeout=5.0,
        )

    monkeypatch.setattr(planner, "SETTINGS", settings(), raising=False)
    monkeypatch.setattr(planner, "_LORA_LOCK", threading.Lock())
    monkeypatch.setattr(planner, "_LORA_POOL", concurrent.futures.ThreadPoolExecutor(max_workers=1))
    monkeypatch.setattr(planner, "_LORA_STATE", {"state": "idle", "error": None})
    monkeypatch.setattr(planner, "LORA_TIMEOUT_S", 0.4)

    release = threading.Event()
    calls: list[str] = []
    loads: list[int] = []
    fake = types.ModuleType("src.ml.serve")

    box = types.SimpleNamespace(answer=None)

    def plan_with_lora(question, candidates=None, lang="es", **kwargs):
        calls.append(question)
        release.wait(timeout=8)  # a slow model, until the test lets it go
        if box.answer is not None:
            return box.answer(question, candidates, lang)
        return {
            "intent": "investigate", "variable_ids": [candidates[0]["variable_id"]], "place": "Ica",
            "place_b": None, "start_year": None, "end_year": None, "last_n_years": None,
            "hypothesis": "down", "lang": lang,
        }

    def load_lora_planner(*args, **kwargs):
        time.sleep(0.5)
        loads.append(1)

    fake.plan_with_lora = plan_with_lora
    fake.load_lora_planner = load_lora_planner
    import src.ml as ml_package

    monkeypatch.setitem(sys.modules, "src.ml.serve", fake)
    monkeypatch.setattr(ml_package, "serve", fake, raising=False)
    yield types.SimpleNamespace(planner=planner, release=release, calls=calls, loads=loads, settings=settings, box=box)
    release.set()


def _wait(condition, seconds=4.0):
    end = time.time() + seconds
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.05)
    return False


def test_a_slow_adapter_never_blocks_the_request(lora):
    started = time.time()
    plan = lora.planner.plan(QUESTION, lang="es")
    elapsed = time.time() - started
    assert elapsed < 3.0, f"the request waited {elapsed:.1f} s for the adapter"
    assert plan["mode"] == "rules" and plan["variable_ids"] == ["PRECTOTCORR"]
    assert "TimeoutError" in plan["note"]


def test_a_second_question_gets_the_rules_answer_at_once(lora):
    first = lora.planner.plan(QUESTION, lang="es")
    assert "TimeoutError" in first["note"]
    started = time.time()
    second = lora.planner.plan("¿Llueve menos en Lima?", lang="es")
    assert time.time() - started < 1.0, "a busy adapter must not queue a second question"
    assert second["mode"] == "rules" and "LoraBusy" in second["note"]
    assert len(lora.calls) == 1, "only one inference may run at a time"


def test_the_adapter_is_usable_again_once_the_slow_run_ends(lora):
    assert "TimeoutError" in lora.planner.plan(QUESTION, lang="es")["note"]
    lora.release.set()
    assert _wait(lambda: not lora.planner._LORA_LOCK.locked()), "the lock was never released"
    plan = lora.planner.plan(QUESTION, lang="es")
    assert plan["mode"] == "lora" and plan["planner"] == "lora"
    assert lora.planner.lora_status()["state"] == "ready"


def test_while_the_adapter_loads_the_model_is_not_called(lora):
    lora.planner._LORA_STATE.update(state="loading")
    plan = lora.planner.plan(QUESTION, lang="es")
    assert plan["mode"] == "rules" and "LoraLoading" in plan["note"]
    assert lora.calls == []


def test_a_failed_load_is_reported_with_its_reason(lora):
    lora.planner._LORA_STATE.update(state="failed", error="OSError: out of memory")
    plan = lora.planner.plan(QUESTION, lang="es")
    assert plan["mode"] == "rules" and "out of memory" in plan["note"]
    assert lora.calls == []


def test_warmup_loads_in_the_background_and_questions_do_not_wait_for_it(lora):
    assert lora.planner.start_lora_warmup() is True
    assert lora.planner.lora_status()["state"] == "loading"
    assert lora.planner.start_lora_warmup() is False, "a second warm-up must not start another load"
    started = time.time()
    plan = lora.planner.plan(QUESTION, lang="es")
    assert time.time() - started < 0.4 and "LoraLoading" in plan["note"]
    assert _wait(lambda: lora.planner.lora_status()["state"] == "ready"), "the warm-up never finished"
    assert lora.loads == [1]


def test_warmup_only_runs_when_the_adapter_is_configured(lora, monkeypatch):
    monkeypatch.setattr(lora.planner, "SETTINGS", lora.settings(mode="extractive"), raising=False)
    assert lora.planner.start_lora_warmup() is False
    assert lora.planner.lora_status()["state"] == "idle"


def test_the_engine_is_reported_as_lora_only_once_the_adapter_is_ready():
    from src.detective.about_facts import engine_for

    ok = {"configured": True, "runtime": True, "adapter": True}
    assert engine_for(**ok, state="ready") == "lora+rag"
    for state in ("idle", "loading", "failed"):
        assert engine_for(**ok, state=state) == "rules+rag"
    assert engine_for(configured=False, runtime=True, adapter=True, state="ready") == "rules+rag"
    assert engine_for(configured=True, runtime=False, adapter=True, state="ready") == "rules+rag"
    assert engine_for(configured=True, runtime=True, adapter=False, state="ready") == "rules+rag"


# --- the adapter proposes, the verified rules decide ---------------------------

def _plan(question, candidates, lang, *, variable, place, place_b=None, intent="investigate"):
    return {
        "intent": intent, "variable_ids": [variable] if variable else [], "place": place, "place_b": place_b,
        "start_year": None, "end_year": None, "last_n_years": None, "hypothesis": "unknown", "lang": lang,
    }


def test_a_lora_plan_the_rules_support_is_kept_and_named(lora):
    from src.detective import chat

    lora.release.set()
    lora.box.answer = lambda q, c, lang: _plan(q, c, lang, variable="PRECTOTCORR", place="Ica")
    reply = chat("¿Llueve menos en Ica?", lang="es")
    assert reply["plan"]["mode"] == "lora" and reply["plan"]["variable_ids"] == ["PRECTOTCORR"]
    assert "LoRA" in reply["reply"] and "verificado por reglas" in reply["reply"]


def test_a_wrong_lora_variable_is_overruled_by_the_rules(lora):
    """Live test on the GPU machine: "heladas en Huancayo" came back as a place summary."""
    from src.detective import chat

    lora.release.set()

    def wrong(question, candidates, lang):
        other = next(c["variable_id"] for c in candidates if c["variable_id"] != "FROST_DAYS")
        return _plan(question, candidates, lang, variable=other, place="Huancayo")

    lora.box.answer = wrong
    reply = chat("heladas en Huancayo", lang="es")
    assert reply["kind"] == "plan", reply["reply"]
    assert reply["plan"]["variable_ids"] == ["FROST_DAYS"]
    assert reply["plan"]["mode"] == "rules"
    assert reply["plan"]["note"].startswith("lora_overruled")
    assert "LoRA" not in reply["reply"], "the answer must not credit the adapter for the rules' plan"


def test_a_comparison_the_lora_turns_into_a_single_place_is_restored_by_the_rules(lora):
    from src.detective import chat

    lora.release.set()
    lora.box.answer = lambda q, c, lang: _plan(q, c, lang, variable="PRECTOTCORR", place="Andahuaylas")
    reply = chat("Compara la lluvia de Andahuaylas y Lima", lang="es")
    assert reply["action"] == "compare"
    assert (reply["plan"]["place"], reply["plan"]["place_b"]) == ("Andahuaylas", "Lima")
    assert reply["plan"]["mode"] == "rules"
