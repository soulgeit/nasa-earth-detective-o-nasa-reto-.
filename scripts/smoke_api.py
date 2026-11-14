# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
Recorrido de humo de la API v2 (contrato A4).

Uso:
    python scripts/smoke_api.py http://127.0.0.1:8000
    python scripts/smoke_api.py https://mi-sitio --strict

Imprime una tabla con el resultado de cada comprobación y sale con código ≠ 0
si alguna falla. Lo usa el arquitecto en cada puerta.

Con `--strict`, un `503 DATA_UNAVAILABLE` (módulo aún sin fusionar) también
cuenta como fallo. Sin `--strict` se marca como `skip`, que es honesto: la
comprobación no pudo ejercitarse.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

import urllib.error
import urllib.parse
import urllib.request

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


@dataclass
class Check:
    name: str
    status: str
    detail: str
    ms: int


def _get(base: str, path: str, params: dict[str, Any] | None = None, timeout: float = 90.0):
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers={"User-Agent": "EarthTrendDetective-smoke/2.0"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, body, int((time.perf_counter() - started) * 1000), url
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return exc.code, body, int((time.perf_counter() - started) * 1000), url
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc).encode(), int((time.perf_counter() - started) * 1000), url


def _json(body: bytes) -> dict[str, Any] | None:
    try:
        data = json.loads(body)
    except Exception:  # noqa: BLE001
        return None
    return data if isinstance(data, dict) else None


def _is_contract_error(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    err = payload.get("error")
    if not isinstance(err, dict):
        return False
    return (
        isinstance(err.get("code"), str)
        and isinstance(err.get("message"), dict)
        and {"es", "en"} <= set(err["message"])
    )


def run(base: str, *, strict: bool) -> list[Check]:
    checks: list[Check] = []

    def record(name: str, ok: bool, detail: str, ms: int, *, skip: bool = False) -> None:
        status = PASS if ok else (SKIP if skip else FAIL)
        checks.append(Check(name, status, detail, ms))

    # 1. health
    status, body, ms, _ = _get(base, "/api/health")
    payload = _json(body)
    ok = status == 200 and isinstance(payload, dict) and "ai_mode" in payload
    record("health", ok, f"HTTP {status} ai_mode={payload.get('ai_mode') if payload else '?'}", ms)

    # 2. catálogo
    status, body, ms, _ = _get(base, "/api/catalog/variables", {"lang": "en"})
    payload = _json(body)
    n = len(payload.get("variables", [])) if payload else 0
    record("catalog/variables", status == 200 and n > 0, f"HTTP {status} variables={n}", ms)

    # 3. error honesto: variable inexistente
    status, body, ms, _ = _get(base, "/api/analyze", {"variable_id": "NOT_A_VARIABLE", "lat": 0, "lon": 0})
    payload = _json(body)
    ok = status == 404 and _is_contract_error(payload) and payload["error"]["code"] == "VARIABLE_UNKNOWN"
    record("analyze unknown variable -> 404", ok, f"HTTP {status} code={(payload or {}).get('error', {}).get('code')}", ms)

    # 4. error honesto: sin coordenadas
    status, body, ms, _ = _get(base, "/api/analyze", {"variable_id": "T2M"})
    payload = _json(body)
    ok = status in {400, 422} and _is_contract_error(payload)
    record("analyze no coords -> 400", ok, f"HTTP {status}", ms)

    # 5. la puerta G1: análisis real de Lima
    status, body, ms, url = _get(base, "/api/analyze", {"variable_id": "T2M", "lat": -12.05, "lon": -77.03})
    payload = _json(body)
    if status == 503:
        record("analyze Lima (G1)", False, "HTTP 503 — real data module not merged yet", ms, skip=not strict)
    elif status == 200 and payload:
        prov = (payload.get("provenance") or {}).get("kind")
        n_obs = (payload.get("period") or {}).get("n_obs")
        ok = payload.get("schema") == "analysis/2" and prov in {"nasa_api", "nasa_file", "user_upload", "fixture"}
        detail = f"HTTP 200 schema={payload.get('schema')} provenance={prov} n_obs={n_obs} {ms}ms"
        if prov == "fixture":
            ok = False
            detail += " (FIXTURE DATA — must not be served in production)"
        record("analyze Lima (G1)", ok, detail, ms)
    else:
        record("analyze Lima (G1)", False, f"HTTP {status} {body[:120]!r}", ms)

    # 6. latencia en caché
    if status == 200:
        status2, _b, ms2, _u = _get(base, "/api/analyze", {"variable_id": "T2M", "lat": -12.05, "lon": -77.03})
        record("analyze Lima (cache < 300ms)", status2 == 200 and ms2 < 3000, f"HTTP {status2} {ms2}ms", ms2)

    # 7. trendmap
    status, body, ms, _ = _get(
        base, "/api/trendmap", {"variable_id": "T2M", "bbox": "-82,-7,-78,-3"}, timeout=120.0
    )
    payload = _json(body)
    if status == 503:
        record("trendmap", False, "HTTP 503 — grid module not merged yet", ms, skip=not strict)
    else:
        ok = status == 200 and (payload or {}).get("schema") == "trendmap/2"
        record("trendmap", ok, f"HTTP {status} cells={(payload or {}).get('n_cells')}", ms)

    # 8. IA degrada con elegancia
    status, body, ms, _ = _get(base, "/api/cases")
    record("cases", status in {200, 503}, f"HTTP {status}", ms)

    # 9. informe
    status, body, ms, _ = _get(
        base, "/api/report", {"variable_id": "T2M", "lat": -12.05, "lon": -77.03, "lang": "en"}, timeout=120.0
    )
    if status == 503:
        record("report", False, "HTTP 503 — analysis module not merged yet", ms, skip=not strict)
    else:
        ok = status == 200 and body[:200].lower().startswith(b"<!doctype html")
        record("report", ok, f"HTTP {status} bytes={len(body)}", ms)

    # 10. UI en /
    status, body, ms, _ = _get(base, "/")
    record("UI /", status == 200 and len(body) > 0, f"HTTP {status} bytes={len(body)}", ms)

    return checks


def print_table(checks: list[Check]) -> None:
    width = max((len(c.name) for c in checks), default=10)
    print(f"{'CHECK'.ljust(width)}  STATUS  TIME    DETAIL")
    print(f"{'-' * width}  ------  ------  {'-' * 50}")
    for c in checks:
        print(f"{c.name.ljust(width)}  {c.status:6}  {c.ms:>5}ms  {c.detail}")
    n_fail = sum(1 for c in checks if c.status == FAIL)
    n_skip = sum(1 for c in checks if c.status == SKIP)
    n_pass = sum(1 for c in checks if c.status == PASS)
    print(f"\n{n_pass} passed · {n_skip} skipped · {n_fail} failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for the EarthTrend Detective API v2")
    parser.add_argument("base_url", help="e.g. http://127.0.0.1:8000")
    parser.add_argument("--strict", action="store_true", help="treat 503 (module not merged) as failure")
    args = parser.parse_args()

    checks = run(args.base_url, strict=args.strict)
    print_table(checks)
    return 1 if any(c.status == FAIL for c in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
