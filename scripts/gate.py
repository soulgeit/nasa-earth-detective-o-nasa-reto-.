# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Puerta de calidad del repositorio en un solo comando.

Uso:
    python scripts/gate.py                # suite + smoke + validadores (sin red)
    python scripts/gate.py --base URL     # además, smoke contra una API viva
    python scripts/gate.py --offline      # solo suite y smoke local, sin validadores de red

Corre, en este orden:

1. ``pytest -q``               — la suite completa (regla 14: no solo tu carpeta).
2. ``smoke_api.py``            — contra una API viva, si se pasa ``--base``; si no,
                                 se levanta una instancia local en un puerto libre.
3. ``validate_datasets.py``    — los casos y el atlas congelados.
4. ``validate_knowledge.py``   — catálogo y corpus (con ``--offline`` por defecto,
                                 para que la puerta no dependa de internet).

Sale con código != 0 si cualquiera falla, y resume qué falló. Es lo que el
arquitecto ejecuta antes de cada ventana de integración.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def _run(name: str, cmd: list[str], *, timeout: int = 1800) -> tuple[str, int, str, float]:
    """Ejecuta un paso y devuelve (nombre, código, salida, segundos)."""
    started = time.perf_counter()
    print(f"\n=== {name} ===")
    print("$ " + " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        code = proc.returncode
    except subprocess.TimeoutExpired:
        out = f"tiempo agotado tras {timeout}s"
        code = 124
    elapsed = time.perf_counter() - started
    # Solo la cola: la salida completa de pytest son cientos de líneas.
    tail = "\n".join(out.strip().splitlines()[-25:])
    print(tail)
    print(f"-> exit {code} en {elapsed:.1f}s")
    return name, code, out, elapsed


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_health(base: str, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base}/api/health/live", timeout=3) as r:
                if r.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    return False


def _smoke(base: str) -> tuple[str, int, str, float]:
    """Arranca uvicorn en un puerto libre, corre el smoke y lo detiene."""
    started = time.perf_counter()
    port = _free_port()
    local = f"http://127.0.0.1:{port}"
    print(f"\n=== smoke_api (servidor propio en {local}) ===")
    server = subprocess.Popen(
        [PY, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", str(port), "--workers", "1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "ALLOW_FIXTURES": "0"},
    )
    try:
        if not _wait_health(local):
            return "smoke_api", 1, "el servidor no respondió en 60 s", time.perf_counter() - started
        proc = subprocess.run(
            [PY, "scripts/smoke_api.py", local],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        tail = "\n".join(out.strip().splitlines()[-25:])
        print(tail)
        elapsed = time.perf_counter() - started
        print(f"-> exit {proc.returncode} en {elapsed:.1f}s")
        return "smoke_api", proc.returncode, out, elapsed
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


def _frozen_files() -> list[str]:
    """Series congeladas (`timeseries/2`) de casos y atlas.

    `validate_datasets.py` solo entiende series: se filtran por `schema` para no
    pasarle `case.json`, `analysis.json` ni los `trendmap/2` del atlas, que
    fallarían por forma y no por contenido.
    """
    paths: list[Path] = []
    for folder in ("cases", "atlas"):
        base = ROOT / "data" / folder
        if not base.exists():
            continue
        paths.extend(sorted(base.rglob("*.json")))

    series: list[str] = []
    for path in paths:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            series.append(str(path))  # que el validador lo reporte como roto
            continue
        if isinstance(doc, dict) and doc.get("schema") == "timeseries/2":
            series.append(str(path))
    return series


def _http_json(url: str) -> tuple[int, object, int, str]:
    """GET que devuelve JSON tambien en los errores (4xx traen el contrato §7)."""
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), int((time.perf_counter() - started) * 1000), url
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            payload = {}
        return exc.code, payload, int((time.perf_counter() - started) * 1000), url


def _in_process_catalog() -> dict:
    """Catalogo sin levantar servidor, para que la puerta funcione offline."""
    sys.path.insert(0, str(ROOT))
    from src.api import catalog  # noqa: PLC0415

    available, planned = [], []
    for card in catalog.all_variables():
        item = catalog.with_availability(card)
        (planned if catalog.is_planned(card) else available).append(item)
    return {"variables": available, "planned": planned}


def _analyzable_probe(base: str | None, variable_id: str) -> tuple[int, str]:
    """Pide la variable y devuelve (status, codigo de error)."""
    if base:
        status, payload, _ms, _url = _http_json(f"{base}/api/analyze?variable_id={variable_id}")
    else:
        sys.path.insert(0, str(ROOT))
        from fastapi.testclient import TestClient  # noqa: PLC0415
        from src.api.main import app  # noqa: PLC0415

        r = TestClient(app).get("/api/analyze", params={"variable_id": variable_id})
        status, payload = r.status_code, r.json()
    code = ""
    if isinstance(payload, dict):
        code = (payload.get("error") or {}).get("code", "")
    return status, code


def _check_no_planned_analyzable(base: str | None) -> tuple[str, int, str, float]:
    """Regla 19: ninguna variable `planned` puede analizarse.

    Se comprueba donde importa: el catalogo las publica aparte y la API las
    rechaza con VARIABLE_PLANNED. Sin servidor vivo se hace en proceso.
    """
    started = time.perf_counter()
    print("\n=== planned no analizable (regla 19) ===")
    code = 0
    lines: list[str] = []
    try:
        if base:
            _st, payload, _ms, _url = _http_json(f"{base}/api/catalog/variables?lang=en")
            payload = payload if isinstance(payload, dict) else {}
        else:
            payload = _in_process_catalog()
        planned = payload.get("planned") or []
        available = {v.get("id") for v in (payload.get("variables") or [])}
        overlap = {v.get("id") for v in planned} & available
        if overlap:
            code = 1
            lines.append(f"FALLA: planned tambien publicadas como disponibles: {sorted(overlap)}")
        for item in planned:
            vid = item.get("id")
            if not vid:
                continue
            status, err = _analyzable_probe(base, vid)
            if err != "VARIABLE_PLANNED":
                code = 1
                lines.append(f"FALLA: {vid} es planned pero la API responde {status} {err}")
        lines.insert(0, f"planned={len(planned)} available={len(available)} solapamiento={bool(overlap)}")
        if not planned:
            lines.append("(el catalogo actual no declara planned: comprobacion vacia, no es un fallo)")
    except Exception as exc:  # noqa: BLE001
        code = 1
        lines.append(f"FALLA: no se pudo comprobar: {type(exc).__name__}: {exc}")
    for line in lines:
        print("  " + line)
    elapsed = time.perf_counter() - started
    print(f"-> exit {code} en {elapsed:.1f}s")
    return "planned_not_analyzable", code, "\n".join(lines), elapsed


def _check_case_ranges() -> tuple[str, int, str, float]:
    """Regla 12: ningun valor fuera del rango fisico dentro de data/cases/.

    Se apoya en `src/etl/validate.py`, que es la autoridad de los rangos. Un
    -9999 en el hielo marino cae aqui.
    """
    started = time.perf_counter()
    print("\n=== rangos fisicos en data/cases/ (regla 12) ===")
    sys.path.insert(0, str(ROOT))
    from src.etl.validate import PHYSICAL_RANGES, validate_file  # noqa: PLC0415

    cases_dir = ROOT / "data" / "cases"
    files = sorted(cases_dir.rglob("series.json")) if cases_dir.exists() else []
    code, problems, checked, values = 0, [], 0, 0
    for path in files:
        errors = validate_file(str(path))
        if errors:
            code = 1
            problems.append(f"FALLA: {path.relative_to(ROOT)}")
            problems.extend("   - " + e for e in errors[:5])
            continue
        checked += 1
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        var_id = doc.get("variable_id")
        bounds = PHYSICAL_RANGES.get(var_id)
        if not bounds:
            continue
        low, high = bounds
        for point in doc.get("data") or []:
            val = point.get("value")
            if val is None:
                continue
            values += 1
            if not (low <= float(val) <= high):
                code = 1
                problems.append(
                    f"FALLA: {path.relative_to(ROOT)} {point.get('date')}={val} "
                    f"fuera de {var_id} [{low}, {high}]"
                )
    summary = f"{checked}/{len(files)} series validas; {values} valores dentro de rango"
    if not files:
        summary = "no hay series en data/cases/ (nada que comprobar)"
    print("  " + summary)
    for line in problems[:20]:
        print("  " + line)
    elapsed = time.perf_counter() - started
    print(f"-> exit {code} en {elapsed:.1f}s")
    return "case_physical_ranges", code, summary + "\n" + "\n".join(problems), elapsed


#: Patrones de credencial (regla 23). Se busca la forma del secreto, no la
#: palabra «token»: un README puede explicar que no se pegue sin ser hallazgo.
_SECRET_PATTERNS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "token de GitHub"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "token fine-grained de GitHub"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "clave de API estilo OpenAI"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "access key de AWS"),
    (re.compile(r"hf_[A-Za-z0-9]{20,}"), "token de Hugging Face"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{30,}"), "clave de Google"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "clave privada"),
]

#: Solo lo que puede llevar un secreto versionado. `.git` guarda los mismos
#: objetos y multiplicaria los hallazgos por cada commit.
_SKIP_DIRS = {".git", ".venv", ".venv-ml", "node_modules", "__pycache__", "models", "dist", ".pytest_cache"}
_BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".mp4", ".safetensors", ".zip", ".nc", ".gz"}


def _check_no_secrets() -> tuple[str, int, str, float]:
    """Regla 23: ninguna credencial en el repositorio."""
    started = time.perf_counter()
    print("\n=== credenciales en el repositorio (regla 23) ===")
    hits: list[str] = []
    scanned = 0
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _BINARY_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        for pattern, label in _SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(f"FALLA: {path.relative_to(ROOT)} parece contener un {label}")
    code = 1 if hits else 0
    print(f"  {scanned} archivos revisados; {len(hits)} hallazgos")
    for hit in hits:
        print("  " + hit)
    elapsed = time.perf_counter() - started
    print(f"-> exit {code} en {elapsed:.1f}s")
    return "no_secrets", code, f"{scanned} archivos; {len(hits)} hallazgos\n" + "\n".join(hits), elapsed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Puerta de calidad de EarthTrend Detective")
    parser.add_argument("--base", default=None, help="API viva; si se omite se levanta una local")
    parser.add_argument("--offline", action="store_true", help="no comprobar URLs del corpus")
    parser.add_argument("--skip-suite", action="store_true", help="omite pytest (para iterar rápido)")
    parser.add_argument("--skip-validators", action="store_true", help="omite los validadores de datos")
    args = parser.parse_args(argv[1:])

    results: list[tuple[str, int, str, float]] = []

    if not args.skip_suite:
        results.append(_run("pytest", [PY, "-m", "pytest", "-q"]))

    if args.base:
        results.append(
            _run("smoke_api", [PY, "scripts/smoke_api.py", args.base], timeout=900)
        )
    else:
        results.append(_smoke(args.base or ""))

    if not args.skip_validators:
        frozen = _frozen_files()
        if frozen:
            results.append(_run("validate_datasets", [PY, "scripts/validate_datasets.py", *frozen], timeout=600))
        else:
            print("\n=== validate_datasets === (sin archivos congelados; se omite)")
            results.append(("validate_datasets", 0, "", 0.0))

        knowledge_cmd = [PY, "scripts/validate_knowledge.py"]
        if args.offline:
            knowledge_cmd.append("--offline")
        results.append(_run("validate_knowledge", knowledge_cmd, timeout=900))

    # RONDA_4 §4: las tres comprobaciones nuevas de la puerta.
    results.append(_check_no_planned_analyzable(args.base))
    results.append(_check_case_ranges())
    results.append(_check_no_secrets())

    print("\n" + "=" * 66)
    print("RESUMEN DE LA PUERTA")
    print("=" * 66)
    for name, code, _out, elapsed in results:
        mark = "OK  " if code == 0 else "FALLA"
        print(f"{mark}  {name:<20} exit={code:<3} {elapsed:6.1f}s")
    failed = [name for name, code, _o, _e in results if code != 0]
    if failed:
        print(f"\nPUERTA CERRADA: fallaron {', '.join(failed)}")
        return 1
    print("\nPUERTA ABIERTA: todo en verde")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
