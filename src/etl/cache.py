# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Cache en disco de respuestas crudas de servicios NASA (contrato v2 §3).

- Clave: sha256 de la URL exacta.
- Se guarda la respuesta cruda tal cual (bytes) + un sidecar con la metadata.
- Validez: 30 dias por defecto (TTL). Pasado ese plazo se vuelve a pedir.
- La procedencia siempre se refiere a la descarga original, no a la lectura de cache.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

DEFAULT_TTL_DAYS = 30.0


def cache_dir() -> str:
    return os.environ.get("DATA_CACHE_DIR") or os.path.join("data", "cache")


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _paths(url: str, directory: str | None = None) -> tuple[str, str]:
    key = cache_key(url)
    base = directory or cache_dir()
    return os.path.join(base, key + ".body"), os.path.join(base, key + ".meta.json")


def load(
    url: str,
    *,
    directory: str | None = None,
    ttl_days: float = DEFAULT_TTL_DAYS,
    now: float | None = None,
) -> dict | None:
    """Devuelve {'body': bytes, 'meta': {...}} si la entrada existe y no ha caducado."""
    body_path, meta_path = _paths(url, directory)
    if not (os.path.exists(body_path) and os.path.exists(meta_path)):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        with open(body_path, "rb") as fh:
            body = fh.read()
    except (OSError, ValueError):
        return None
    if meta.get("url") != url:
        return None
    age_days = ((now if now is not None else time.time()) - float(meta.get("fetched_at_epoch", 0))) / 86400.0
    if age_days > ttl_days:
        return None
    return {"body": body, "meta": meta}


def store(
    url: str,
    body: bytes,
    *,
    status: int,
    directory: str | None = None,
    fetched_at_epoch: float | None = None,
    extra: dict | None = None,
) -> dict:
    """Guarda respuesta cruda + metadata. Devuelve la metadata escrita."""
    directory = directory or cache_dir()
    os.makedirs(directory, exist_ok=True)
    body_path, meta_path = _paths(url, directory)
    now = fetched_at_epoch if fetched_at_epoch is not None else time.time()
    meta = {
        "url": url,
        "status": status,
        "fetched_at_epoch": now,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    }
    if extra:
        meta.update(extra)
    # Escritura atomica: primero el cuerpo, luego el sidecar (indica entrada completa).
    tmp_body = body_path + ".tmp"
    with open(tmp_body, "wb") as fh:
        fh.write(body)
    os.replace(tmp_body, body_path)
    tmp_meta = meta_path + ".tmp"
    with open(tmp_meta, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    os.replace(tmp_meta, meta_path)
    return meta
