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
