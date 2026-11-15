# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""20 peticiones simultáneas a /api/analyze: mide caché y concurrencia.

Uso:
    python scripts/load_test.py [http://127.0.0.1:8000]

Cada petición lleva un `X-Forwarded-For` distinto: el límite de 120/min es por
cliente, y con una sola IP se mediría el cupo en vez de la concurrencia del
servidor. Dos tandas: la misma clave (caché) y 20 claves distintas (motor).
"""

from __future__ import annotations

import concurrent.futures as cf
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
N = 20


def _get(url: str, client: str, timeout: float = 180.0) -> tuple[int, float]:
    req = urllib.request.Request(url, headers={"X-Forwarded-For": client})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
        return resp.status, time.perf_counter() - started
    except urllib.error.HTTPError as exc:
        exc.read()
        return exc.code, time.perf_counter() - started
    except Exception:  # noqa: BLE001
        return 0, time.perf_counter() - started


def _report(label: str, results: list[tuple[int, float]], total: float) -> None:
    codes: dict[int, int] = {}
    for code, _ in results:
        codes[code] = codes.get(code, 0) + 1
    latencies = sorted(dt for _, dt in results)
    print(label)
    print(f"  peticiones          : {len(results)}")
    print(f"  codigos             : {codes}")
    print(f"  total (pared)       : {total * 1000:.0f} ms")
    print(
        f"  latencia min/med/max: {latencies[0] * 1000:.0f} / "
        f"{latencies[len(latencies) // 2] * 1000:.0f} / {latencies[-1] * 1000:.0f} ms"
    )
    print(f"  throughput          : {len(results) / total:.1f} req/s")


def main() -> int:
    same = f"{BASE}/api/analyze?variable_id=T2M&lat=-12.05&lon=-77.03"
    _get(same, "10.9.9.9")  # calienta la caché

    print("=== 20 simultaneas, misma clave (cache) ===")
    started = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=N) as ex:
        results = list(ex.map(lambda i: _get(same, f"10.0.{i}.1"), range(N)))
    _report("cache hit x20", results, time.perf_counter() - started)

    print("\n=== 20 simultaneas, 20 claves distintas (motor sin cache) ===")
    started = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=N) as ex:
        results = list(
            ex.map(
                lambda i: _get(
                    f"{BASE}/api/analyze?variable_id=T2M&lat={-12.05 - i * 0.01:.2f}&lon=-77.03",
                    f"10.1.{i}.1",
                ),
                range(N),
            )
        )
    _report("engine x20", results, time.perf_counter() - started)

    return 0 if all(code == 200 for code, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
