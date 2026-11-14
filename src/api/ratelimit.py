# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Límite de peticiones por IP para los endpoints que llaman a la NASA.

Objetivo (A4): no agotar la cuota de NASA POWER con un bucle de un cliente.
Ventana deslizante en memoria; suficiente para un único proceso de uvicorn.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from .config import RATE_LIMIT_PER_MIN
from .errors import ApiError


class SlidingWindowLimiter:
    def __init__(self, limit: int = RATE_LIMIT_PER_MIN, window_s: float = 60.0) -> None:
        self.limit = limit
        self.window_s = window_s
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        if self.limit <= 0:
            return
        now = time.monotonic()
        with self._lock:
            q = self._events[key]
            while q and now - q[0] > self.window_s:
                q.popleft()
            if len(q) >= self.limit:
                retry = max(1, int(self.window_s - (now - q[0])) + 1)
                raise ApiError(
                    "RATE_LIMITED",
                    hint=f"Retry after ~{retry}s. Limit: {self.limit} requests/minute.",
                )
            q.append(now)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


limiter = SlidingWindowLimiter()
