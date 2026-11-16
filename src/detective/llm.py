# SI-assisted: claude-omni-2 (Claude Opus 5.5); hosted-API mode: cfable (Claude Sonnet 5.5)
"""Thin client for an OpenAI-compatible model server.

Two ways to run it, chosen only by environment variables:
  * local (default): Ollama at LLM_BASE_URL, no key, Ollama-only options in the payload;
  * hosted (RONDA_7): any OpenAI-compatible API (OpenAI, Together, Groq...) when LLM_API_KEY is set:
    a bearer key, standard fields only, a 20 s ceiling per call and a daily cap on calls, so a public
    site can never spend more than its owner decided.

Design rules from the contracts: every failure is explicit (``AIUnavailable``) and callers degrade
to the rules / extractive path; the key is never logged and never reaches a response.
"""

from __future__ import annotations

import json
import threading
from datetime import date
from typing import Any
from urllib.parse import urlparse

import requests

from .config import SETTINGS

HOSTED_TIMEOUT_S = 20.0
# At most this many hosted calls wait on the network at once. The rest are told "busy" at once and the
# caller answers with the verified rules: a burst degrades gracefully instead of queueing or hanging.
MAX_HOSTED_INFLIGHT = 8
SLOT_WAIT_S = 0.25


class AIUnavailable(RuntimeError):
    """The model server did not answer; callers must use the fallback path.

    ``str(exc)`` is safe to show (it ends up in a plan's ``note``); ``detail`` keeps the provider's own
    words for internal decisions only and is never shown.
    """

    def __init__(self, message: str, *, detail: str = "") -> None:
        super().__init__(message)
        self.detail = detail


_LOCK = threading.Lock()
_SLOTS = threading.BoundedSemaphore(MAX_HOSTED_INFLIGHT)
_STATE: dict[str, Any] = {"day": None, "calls": 0, "last_ok": None, "last_error": None}


def status() -> dict[str, Any]:
    """What the app may say about the hosted model: counts and the last outcome, never a key or a payload."""
    with _LOCK:
        today = date.today().isoformat()
        return {
            "calls_today": _STATE["calls"] if _STATE["day"] == today else 0,
            "last_ok": _STATE["last_ok"],
            "last_error": _STATE["last_error"],
        }


def reset_state() -> None:
    with _LOCK:
        _STATE.update(day=None, calls=0, last_ok=None, last_error=None)


def host() -> str | None:
    return urlparse(SETTINGS.llm_base_url).hostname


def _take_call() -> bool:
    """Count one hosted call against today's cap; False when the cap is spent."""
    cap = SETTINGS.llm_daily_cap
    today = date.today().isoformat()
    with _LOCK:
        if _STATE["day"] != today:
            _STATE.update(day=today, calls=0)
        if cap > 0 and _STATE["calls"] >= cap:
            return False
        _STATE["calls"] += 1
        return True


def _outcome(ok: bool, error: str | None = None) -> None:
    with _LOCK:
        _STATE.update(last_ok=ok, last_error=None if ok else (error or "")[:120])


def _post(
    path: str,
    payload: dict[str, Any],
    *,
    base: str,
    timeout: float | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    url = base.rstrip("/") + path
    # A hosted call (it carries a key) never puts the full URL or the provider's own words in an error:
    # those reach the visitor through the plan's note and can say things about quota or billing.
    where = urlparse(url).hostname if headers else url
    try:
        resp = requests.post(url, json=payload, timeout=timeout or SETTINGS.request_timeout, headers=headers or {})
    except requests.RequestException as exc:
        raise AIUnavailable(f"{where}: {type(exc).__name__}") from exc
    if resp.status_code >= 400:
        if headers and resp.status_code in (401, 403):
            # The provider echoes part of the key in this message: say only what matters.
            raise AIUnavailable(f"{where}: HTTP {resp.status_code} (the API key was rejected)")
        if headers:
            raise AIUnavailable(f"{where}: HTTP {resp.status_code}", detail=resp.text[:300])
        raise AIUnavailable(f"{url}: HTTP {resp.status_code} {resp.text[:200]}")
    try:
        return resp.json()
    except ValueError as exc:
        raise AIUnavailable(f"{url}: response is not JSON") from exc


def chat(
    messages: list[dict[str, str]],
    *,
    model: str,
    temperature: float = 0.0,
    num_ctx: int = 4096,
    keep_alive: str = "30m",
) -> str:
    """One chat completion. Returns the assistant message content."""
    if not model:
        raise AIUnavailable("no model configured (PLANNER_MODEL/EXPLAIN_MODEL is empty)")
    hosted = SETTINGS.llm_hosted
    if not hosted:
        data = _post(
            "/chat/completions",
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": False,
                # Ollama honours these two; other servers ignore them harmlessly.
                "options": {"num_ctx": num_ctx},
                "keep_alive": keep_alive,
            },
            base=SETTINGS.llm_base_url,
        )
    else:
        if not _SLOTS.acquire(timeout=SLOT_WAIT_S):
            # Busy is not a provider failure: no cap spent, no "failing" state; the rules answer now.
            raise AIUnavailable("hosted model busy")
        try:
            if not _take_call():
                _outcome(False, "daily call cap reached")
                raise AIUnavailable("daily call cap reached")
            payload: dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature, "stream": False}
            headers = {"Authorization": f"Bearer {SETTINGS.llm_api_key}"}
            timeout = min(SETTINGS.request_timeout, HOSTED_TIMEOUT_S)
            try:
                try:
                    data = _post("/chat/completions", payload, base=SETTINGS.llm_base_url, timeout=timeout, headers=headers)
                except AIUnavailable as exc:
                    # Some models only accept their default temperature: ask again without it, once.
                    if "temperature" not in f"{exc} {exc.detail}".lower():
                        raise
                    retry = {k: v for k, v in payload.items() if k != "temperature"}
                    data = _post("/chat/completions", retry, base=SETTINGS.llm_base_url, timeout=timeout, headers=headers)
            except AIUnavailable as exc:
                _outcome(False, str(exc))
                raise
        finally:
            _SLOTS.release()
    try:
        content = str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        if hosted:
            _outcome(False, "unexpected chat payload")
        raise AIUnavailable(f"unexpected chat payload: {json.dumps(data)[:200]}") from exc
    if hosted:
        _outcome(True)
    return content


def embed(texts: list[str], *, model: str) -> list[list[float]]:
    """Embeddings via Ollama's native endpoint (/api/embed). One vector per text."""
    if not model:
        raise AIUnavailable("no EMBED_MODEL configured")
    data = _post("/api/embed", {"model": model, "input": texts}, base=SETTINGS.embed_base_url)
    vectors = data.get("embeddings")
    if not isinstance(vectors, list) or len(vectors) != len(texts):
        raise AIUnavailable("embedding payload does not match the request")
    return [[float(x) for x in vec] for vec in vectors]


def list_models() -> list[str]:
    """Model names the server currently holds (never triggers a download)."""
    url = SETTINGS.embed_base_url.rstrip("/") + "/api/tags"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise AIUnavailable(f"{url}: {type(exc).__name__}") from exc
    return [str(m.get("name")) for m in resp.json().get("models", [])]
