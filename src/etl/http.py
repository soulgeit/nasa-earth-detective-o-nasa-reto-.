# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Cliente HTTP del ETL: User-Agent identificable, timeouts, reintentos y un
limite de concurrencia de 2 peticiones (verificado 2026-11-14: POWER no
publica cuota numerica, pero responde 429 si se le aprieta; ver reporte).
"""

from __future__ import annotations

import threading
import time

import requests

USER_AGENT = "EarthTrendDetective/0.2"
CONNECT_TIMEOUT = 10.0
READ_TIMEOUT = 60.0
MAX_CONCURRENT = 2
RETRIES = 2
BACKOFF_SECONDS = (1.0, 3.0)

_local = threading.local()
_semaphore = threading.BoundedSemaphore(MAX_CONCURRENT)


class UpstreamTimeout(Exception):
    pass


class UpstreamError(Exception):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body[:200]}")


def _session() -> requests.Session:
    sess = getattr(_local, "session", None)
    if sess is None:
        sess = requests.Session()
        sess.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        _local.session = sess
    return sess


def get(url: str) -> requests.Response:
    """GET con reintentos (2, espera creciente) y como maximo 2 en paralelo."""
    last_exc: Exception | None = None
    with _semaphore:
        for attempt in range(RETRIES + 1):
            try:
                resp = _session().get(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
            except requests.Timeout as exc:
                last_exc = UpstreamTimeout(str(exc))
                time.sleep(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])
                continue
            except requests.RequestException as exc:
                last_exc = UpstreamError(0, str(exc))
                time.sleep(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])
                continue
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                last_exc = UpstreamError(resp.status_code, resp.text)
                if attempt < RETRIES:
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        pause = float(retry_after) if retry_after else BACKOFF_SECONDS[attempt]
                    except ValueError:
                        pause = BACKOFF_SECONDS[attempt]
                    time.sleep(min(pause, 10.0))
                    continue
            return resp
    if isinstance(last_exc, UpstreamTimeout):
        raise last_exc
    raise last_exc if last_exc is not None else UpstreamError(0, "sin respuesta")
