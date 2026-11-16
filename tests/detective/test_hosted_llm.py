# SI-assisted: cfable (Claude Sonnet 5.5)
"""Hosted OpenAI-compatible model (RONDA_7): off unless LLM_API_KEY is set, and safe when it is on.

A fake `requests.post` stands in for the provider: no network, no key, no cost.
"""

from __future__ import annotations

import json as jsonlib
import types

import pytest

from src.detective import about_facts, config as cfg, conversation, llm, narrative, planner

KEY = "sk-test-1234567890abcdef"
BASE = "https://api.example-llm.com/v1"


def ok(content):
    return {"choices": [{"message": {"content": content}}]}


def plan_json(variable, place, *, intent="investigate", place_b=None, hypothesis="unknown"):
    return jsonlib.dumps({
        "intent": intent, "variable_ids": [variable], "place": place, "place_b": place_b,
        "start_year": None, "end_year": None, "last_n_years": None, "hypothesis": hypothesis, "lang": "es",
    })


def make_settings(**override):
    values = dict(
        ai_mode="full", llm_base_url=BASE, planner_model="small-model", explain_model="small-model",
        embed_base_url="http://localhost:11434", embed_model="", data_dir=cfg.SETTINGS.data_dir,
        catalog_dir=cfg.SETTINGS.catalog_dir, knowledge_dir=cfg.SETTINGS.knowledge_dir,
        index_dir=cfg.SETTINGS.index_dir, request_timeout=60.0, llm_api_key=KEY, llm_daily_cap=0,
    )
    values.update(override)
    return cfg.Settings(**values)


class FakeProvider:
    def __init__(self):
        self.calls: list[dict] = []
        self.script: list[tuple[int, dict]] = []

    def post(self, url, json=None, timeout=None, headers=None):
        # A real provider receives a serialized snapshot: keep a copy, not a live reference.
        self.calls.append({"url": url, "json": jsonlib.loads(jsonlib.dumps(json)), "timeout": timeout,
                           "headers": dict(headers or {})})
        status, body = self.script.pop(0) if self.script else (200, ok("{}"))
        return types.SimpleNamespace(status_code=status, text=jsonlib.dumps(body), json=lambda: body)


@pytest.fixture()
def hosted(monkeypatch):
    provider = FakeProvider()
    llm.reset_state()
    for module in (llm, planner, narrative, about_facts):
        monkeypatch.setattr(module, "SETTINGS", make_settings(), raising=False)
    monkeypatch.setattr(llm.requests, "post", provider.post)
    about_facts.reset_cache()
    yield types.SimpleNamespace(api=provider, use=lambda **o: [monkeypatch.setattr(m, "SETTINGS", make_settings(**o), raising=False) for m in (llm, planner, narrative, about_facts)])
    llm.reset_state()


def test_a_hosted_call_sends_a_bearer_key_and_only_standard_fields(hosted):
    hosted.api.script = [(200, ok("hola"))]
    assert llm.chat([{"role": "user", "content": "x"}], model="small-model") == "hola"
    call = hosted.api.calls[0]
    assert call["url"] == f"{BASE}/chat/completions"
    assert call["headers"]["Authorization"] == f"Bearer {KEY}"
    assert set(call["json"]) == {"model", "messages", "temperature", "stream"}, "Ollama-only fields are rejected by hosted APIs"
    assert call["timeout"] <= llm.HOSTED_TIMEOUT_S


def test_a_local_server_keeps_its_ollama_fields_and_gets_no_key(hosted):
    hosted.use(llm_api_key="", llm_base_url="http://localhost:11434/v1")
    hosted.api.script = [(200, ok("hi"))]
    llm.chat([{"role": "user", "content": "x"}], model="qwen")
    call = hosted.api.calls[0]
    assert "Authorization" not in call["headers"]
    assert {"options", "keep_alive"} <= set(call["json"])


def test_a_model_that_refuses_temperature_is_asked_again_without_it(hosted):
    refusal = {"error": {"message": "Unsupported value: 'temperature' does not support 0 with this model."}}
    hosted.api.script = [(400, refusal), (200, ok("fine"))]
    assert llm.chat([{"role": "user", "content": "x"}], model="small-model") == "fine"
    assert "temperature" in hosted.api.calls[0]["json"] and "temperature" not in hosted.api.calls[1]["json"]


def test_a_rejected_key_is_reported_without_echoing_any_part_of_it(hosted):
    hosted.api.script = [(401, {"error": {"message": f"Incorrect API key provided: {KEY[:8]}****{KEY[-4:]}"}})]
    with pytest.raises(llm.AIUnavailable) as caught:
        llm.chat([{"role": "user", "content": "x"}], model="small-model")
    message = str(caught.value)
    assert "rejected" in message and KEY[:8] not in message and KEY[-4:] not in message


def test_a_provider_error_shows_the_visitor_only_host_and_status(hosted):
    """The error lands in a plan's note: no full URL, no provider text about quota or billing."""
    hosted.api.script = [(429, {"error": {"message": "You exceeded your current quota, check your billing details"}})]
    with pytest.raises(llm.AIUnavailable) as caught:
        llm.chat([{"role": "user", "content": "x"}], model="small-model")
    shown = str(caught.value)
    assert shown == "api.example-llm.com: HTTP 429"
    assert "quota" not in shown and "/v1" not in shown and "quota" in caught.value.detail


def test_the_daily_cap_stops_hosted_calls_and_resets_the_next_day(hosted, monkeypatch):
    hosted.use(llm_daily_cap=2)
    hosted.api.script = [(200, ok("1")), (200, ok("2")), (200, ok("3"))]
    llm.chat([{"role": "user", "content": "a"}], model="m")
    llm.chat([{"role": "user", "content": "b"}], model="m")
    with pytest.raises(llm.AIUnavailable, match="cap"):
        llm.chat([{"role": "user", "content": "c"}], model="m")
    assert len(hosted.api.calls) == 2, "a call over the cap must never reach the provider"
    tomorrow = types.SimpleNamespace(today=lambda: types.SimpleNamespace(isoformat=lambda: "2099-01-01"))
    monkeypatch.setattr(llm, "date", tomorrow)
    assert llm.chat([{"role": "user", "content": "d"}], model="m") == "3"


def test_a_burst_beyond_the_slots_is_told_busy_at_once_without_spending_the_cap(hosted):
    """At most MAX_HOSTED_INFLIGHT calls wait on the network; the rest degrade to the rules, not to a queue."""
    hosted.use(llm_daily_cap=5)
    taken = [llm._SLOTS.acquire() for _ in range(llm.MAX_HOSTED_INFLIGHT)]
    try:
        with pytest.raises(llm.AIUnavailable, match="busy"):
            llm.chat([{"role": "user", "content": "x"}], model="m")
    finally:
        for _ in taken:
            llm._SLOTS.release()
    assert hosted.api.calls == [], "a busy rejection must never reach the provider"
    assert llm.status()["calls_today"] == 0, "and must not spend the daily cap"
    assert llm.status()["last_error"] is None, "and is not a provider failure"
    hosted.api.script = [(200, ok("fine"))]
    assert llm.chat([{"role": "user", "content": "x"}], model="m") == "fine", "the slots are released afterwards"


def test_model_calls_run_off_the_event_loop():
    """The hang of 2026-11-15: a slow hosted call on the event loop freezes every visitor and the health check."""
    import inspect

    from src.api import main

    assert inspect.iscoroutinefunction(main.health_live), "the liveness probe must not wait for the worker pool"
    for route in (main.ai_chat, main.ai_explain):
        assert "run_in_threadpool" in inspect.getsource(route), f"{route.__name__} must call the model in a worker thread"


def test_a_key_means_a_cap_by_default():
    assert cfg._daily_cap.__doc__ and "2000" in cfg._daily_cap.__doc__


def test_the_planner_uses_the_hosted_model_and_labels_the_plan_as_llm(hosted):
    hosted.api.script = [(200, ok(plan_json("PRECTOTCORR", "Ica", hypothesis="down")))]
    plan = planner.plan("¿Llueve menos en Ica?", lang="es")
    assert plan["mode"] == "llm" and plan["planner"] == "llm" and plan["variable_ids"] == ["PRECTOTCORR"]
    sent = hosted.api.calls[0]["json"]["messages"]
    assert "planning module" in sent[0]["content"] and sent[1]["content"].startswith("QUESTION: ")


def test_the_hosted_prompt_is_the_one_the_lora_was_trained_with():
    packaged = (cfg.SETTINGS.data_dir / "lora" / "system_prompt.txt").read_text(encoding="utf-8").strip()
    assert planner.HOSTED_PLANNER_PROMPT == packaged


def test_when_the_provider_fails_the_rules_answer_and_say_why(hosted):
    hosted.api.script = [(500, {"error": {"message": "overloaded"}})]
    plan = planner.plan("¿Llueve menos en Ica?", lang="es")
    assert plan["mode"] == "rules" and plan["note"].startswith("ai_unavailable")
    assert plan["variable_ids"] == ["PRECTOTCORR"]
    assert KEY not in jsonlib.dumps(plan)


def test_a_hosted_plan_the_rules_do_not_support_is_overruled_in_the_conversation(hosted):
    """The model proposes, the verified rules decide: "heladas" is frost days, not whatever it guessed."""
    from src.detective import chat

    def wrong(question="heladas en Huancayo"):
        candidates = planner.retrieve_for_plan(question, lang="es", k=6)
        other = next(c["variables"][0] for c in candidates if c["variables"][0] != "FROST_DAYS")
        return plan_json(other, "Huancayo")

    hosted.api.script = [(200, ok(wrong()))]
    reply = chat("heladas en Huancayo", lang="es")
    assert reply["plan"]["variable_ids"] == ["FROST_DAYS"] and reply["plan"]["mode"] == "rules"
    assert reply["plan"]["note"].startswith("llm_overruled")


def test_a_supported_hosted_plan_is_kept_and_named(hosted):
    from src.detective import chat

    hosted.api.script = [(200, ok(plan_json("PRECTOTCORR", "Ica", hypothesis="down")))]
    reply = chat("¿Llueve menos en Ica?", lang="es")
    assert reply["plan"]["mode"] == "llm" and "modelo de lenguaje" in reply["reply"]


def test_an_explanation_with_an_invented_number_falls_back_to_the_extractive_text(hosted, analysis_result):
    hosted.api.script = [(200, ok("The trend is 42.7 degrees per decade [1].")), (200, ok("Still 42.7 degrees per decade [1]."))]
    result = narrative.explain(analysis_result, level="school", lang="en")
    assert result["mode"] == "extractive" and "42.7" not in result["text"]
    assert result["guard"].get("llm_attempts_rejected")


def test_the_panel_names_the_provider_only_after_a_real_success(hosted):
    before = about_facts.about(lang="en")["deployment"]
    assert before["llm"]["state"] == "configured" and before["engine"] == "rules+rag"
    assert before["generative_text"] is False
    hosted.api.script = [(200, ok("{}"))]
    llm.chat([{"role": "user", "content": "x"}], model="small-model")
    after = about_facts.about(lang="en")["deployment"]
    assert after["engine"] == "llm+rag" and after["llm"]["host"] == "api.example-llm.com"
    assert after["generative_text"] is True and after["planner"] == "llm"
    assert KEY not in jsonlib.dumps(about_facts.about(lang="en"))
    hosted.api.script = [(500, {"error": {"message": "down"}})]
    with pytest.raises(llm.AIUnavailable):
        llm.chat([{"role": "user", "content": "x"}], model="small-model")
    assert about_facts.about(lang="en")["deployment"]["engine"] == "rules+rag", "a failing provider must not be advertised"


def test_without_a_key_the_app_behaves_exactly_as_before(hosted):
    hosted.use(llm_api_key="", ai_mode="extractive", planner_model="", explain_model="")
    deployment = about_facts.about(lang="en")["deployment"]
    assert deployment["llm"]["state"] == "off" and deployment["engine"] == "rules+rag"
    assert deployment["generative_text"] is False and deployment["llm"]["host"] is None
