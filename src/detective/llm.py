# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Thin client for a local, OpenAI-compatible model server (Ollama).

Design rules from the contracts:
  * every failure is explicit (``AIUnavailable``) and callers degrade gracefully;
  * we never download, start or stop models — if the service is down we say so;
  * no retries with hidden changes: the caller decides (one retry max, per §10/R3).
"""

from __future__ import annotations

import json
from typing import Any

import requests

from .config import SETTINGS


class AIUnavailable(RuntimeError):
    """The local model server did not answer; callers must use the fallback path."""


def _post(path: str, payload: dict[str, Any], *, base: str, timeout: float | None = None) -> dict[str, Any]:
    url = base.rstrip("/") + path
    try:
        resp = requests.post(url, json=payload, timeout=timeout or SETTINGS.request_timeout)
    except requests.RequestException as exc:
        raise AIUnavailable(f"{url}: {type(exc).__name__}") from exc
    if resp.status_code >= 400:
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
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise AIUnavailable(f"unexpected chat payload: {json.dumps(data)[:200]}") from exc


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
