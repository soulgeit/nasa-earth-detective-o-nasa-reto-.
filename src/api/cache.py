# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Caché de respuestas de análisis en memoria con caducidad y exclusión mutua.

- Una entrada por clave (parámetros normalizados + variable).
- Exclusión mutua por clave: dos peticiones simultáneas de lo mismo esperan al
  mismo cálculo en vez de duplicar la descarga a la NASA (A4).
- Límite de tamaño para no crecer sin control en un contenedor pequeño.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Hashable

from .config import ANALYSIS_CACHE_TTL


class TTLCache:
    def __init__(self, ttl: float = ANALYSIS_CACHE_TTL, max_entries: int = 256) -> None:
        self.ttl = ttl
        self.max_entries = max_entries
        self._data: OrderedDict[Hashable, tuple[float, Any]] = OrderedDict()
        self._locks: dict[Hashable, threading.Lock] = {}
        self._guard = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: Hashable) -> Any | None:
        now = time.monotonic()
        with self._guard:
            item = self._data.get(key)
            if item is None:
                self.misses += 1
                return None
            stored, value = item
            if now - stored > self.ttl:
                self._data.pop(key, None)
                self.misses += 1
                return None
            self._data.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key: Hashable, value: Any) -> None:
        now = time.monotonic()
        with self._guard:
            self._data[key] = (now, value)
            self._data.move_to_end(key)
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)

    def _lock_for(self, key: Hashable) -> threading.Lock:
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock
            return lock

    def get_or_compute(self, key: Hashable, producer: Callable[[], Any]) -> Any:
        """Devuelve el valor cacheado o lo calcula una sola vez por clave."""
        cached = self.get(key)
        if cached is not None:
            return cached
        lock = self._lock_for(key)
        with lock:
            # Otro hilo pudo calcularlo mientras esperábamos el lock.
            cached = self.get(key)
            if cached is not None:
                return cached
            value = producer()
            if value is not None:
                self.set(key, value)
            return value

    def clear(self) -> None:
        with self._guard:
            self._data.clear()
            self._locks.clear()

    def stats(self) -> dict[str, int]:
        with self._guard:
            return {"entries": len(self._data), "hits": self.hits, "misses": self.misses, "ttl": int(self.ttl)}


analysis_cache = TTLCache()
