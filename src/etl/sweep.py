# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Recorrido global reanudable para el atlas (apoyo a Hermes 2, "después de G1").

Este modulo SOLO trae datos: genera las cajas, pide cada una a NASA POWER en
**serie** (una peticion a la vez; POWER no publica cuota numerica y responde 429
si se le aprieta) y deja un JSON por caja en disco. La estadistica y el ensamblado
del atlas son del carril de Antigravity 2 y Hermes 2.

Propiedades que exige el prompt:
- **Reanudable**: cada caja terminada se escribe una vez y no se repite; si el
  proceso muere o se agota el tiempo, la siguiente llamada continua donde iba.
- **Respetuoso con la fuente**: secuencial, con pausa configurable entre cajas,
  y sin pedir dos veces lo que ya esta en la cache de 30 dias.
- **Presupuesto de tiempo**: `--deadline` corta limpiamente antes de que el
  orquestador mate el proceso; lo hecho queda guardado.

Uso:
    python -m src.etl.sweep --variable T2M --out data/cache/sweep --max-tiles 20
    python -m src.etl.sweep --variable T2M --out data/cache/sweep --deadline 100
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from . import catalog, power
from .errors import DataUnavailable

# POWER exige cajas de 2 a 10 grados. Se usa el minimo (2x2) para tener mas
# celdas en el mapa sin trocear, y se deja 0,5 grados de solape negativo evitado
# generando cajas contiguas exactas.
TILE_DEGREES = 2.0


def tiles_global(step: float = TILE_DEGREES) -> list[tuple[float, float, float, float]]:
    """Cajas contiguas que cubren el planeta ([-180,180] x [-90,90])."""
    if step <= 0 or 180.0 % step or 360.0 % step:
        raise ValueError("el paso debe dividir exacto 180 y 360")
    tiles = []
    lat = -90.0
    while lat < 90.0:
        lon = -180.0
        while lon < 180.0:
            tiles.append((lon, lat, lon + step, lat + step))
            lon += step
        lat += step
    return tiles


def _tile_path(out_dir: str, tile) -> str:
    west, south, east, north = tile
    return os.path.join(out_dir, f"tile_s{south:+06.1f}_n{north:+06.1f}_w{west:+07.1f}_e{east:+07.1f}.json")


def _load_tile(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    return doc if doc.get("status") in ("ok", "empty") else None


def _save(path: str, doc: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    os.replace(tmp, path)


def run(
    variable_id: str,
    out_dir: str,
    *,
    step: float = TILE_DEGREES,
    max_tiles: int | None = None,
    deadline_seconds: float | None = None,
    pause_seconds: float = 0.25,
    start=None,
    end=None,
    log=print,
) -> dict:
    """Recorre las cajas pendientes. Devuelve un resumen del progreso."""
    card = catalog.get_variable(variable_id)
    if card.get("connector") != "power":
        raise DataUnavailable("VARIABLE_UNKNOWN", f"{variable_id} no es del conector power")
    default_start, default_end = power.default_period(card)
    start = str(start or default_start)
    end = str(end or default_end)

    os.makedirs(out_dir, exist_ok=True)
    tiles = tiles_global(step)
    pending = []
    done = 0
    for tile in tiles:
        if _load_tile(_tile_path(out_dir, tile)) is not None:
            done += 1
        else:
            pending.append(tile)
    log(f"{variable_id}: {done}/{len(tiles)} cajas ya hechas, {len(pending)} pendientes")

    t0 = time.perf_counter()
    processed = 0
    failures = 0
    stopped_by: str | None = None
    tile_cost = 0.0  # media observada por caja en esta ejecucion (segundos)
    for tile in pending:
        elapsed = time.perf_counter() - t0
        # Se reserva lo que cuesta una caja mas: asi el proceso sale ANTES del
        # limite y no una peticion despues. `perf_counter` es necesario aqui:
        # `time.monotonic()` en Windows solo avanza cada ~15,6 ms.
        if deadline_seconds is not None and elapsed + tile_cost >= deadline_seconds:
            stopped_by = "deadline"
            break
        if max_tiles is not None and processed >= max_tiles:
            stopped_by = "max_tiles"
            break
        path = _tile_path(out_dir, tile)
        tile_started = time.perf_counter()
        try:
            grid = power.grid(variable_id, tile, start=start, end=end)
            doc = {
                "status": "ok",
                "variable_id": variable_id,
                "bbox": list(tile),
                "unit": grid["unit"],
                "lats": grid["lats"],
                "lons": grid["lons"],
                "dates": grid["dates"],
                "values": grid["values"],
                "provenance": grid["provenance"],
            }
        except DataUnavailable as exc:
            # Una caja sin datos (p. ej. oceano para una variable terrestre) no
            # es un fallo del recorrido: se anota y se sigue.
            doc = {
                "status": "empty",
                "variable_id": variable_id,
                "bbox": list(tile),
                "error": {"code": exc.code, "detail": exc.detail},
            }
            failures += 1
            log(f"  {tile}: {exc.code}")
        _save(path, doc)
        processed += 1
        spent = time.perf_counter() - tile_started
        tile_cost = spent if processed == 1 else (tile_cost * (processed - 1) + spent) / processed
        if processed % 10 == 0:
            log(f"  {processed} cajas en {time.perf_counter() - t0:.1f}s")
        if pause_seconds:
            tile_cost += pause_seconds
            time.sleep(pause_seconds)

    total_done = done + processed
    summary = {
        "variable_id": variable_id,
        "out_dir": out_dir,
        "tiles_total": len(tiles),
        "tiles_done": total_done,
        "tiles_remaining": len(tiles) - total_done,
        "processed_this_run": processed,
        "empty_this_run": failures,
        "stopped_by": stopped_by,
        "elapsed_seconds": round(time.perf_counter() - t0, 1),
        "start": start,
        "end": end,
    }
    log(json.dumps(summary, ensure_ascii=False))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recorrido global reanudable de NASA POWER")
    parser.add_argument("--variable", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--step", type=float, default=TILE_DEGREES)
    parser.add_argument("--max-tiles", type=int, default=None)
    parser.add_argument("--deadline", type=float, default=None)
    parser.add_argument("--pause", type=float, default=0.25)
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    args = parser.parse_args(argv)
    try:
        summary = run(
            args.variable,
            args.out,
            step=args.step,
            max_tiles=args.max_tiles,
            deadline_seconds=args.deadline,
            pause_seconds=args.pause,
            start=args.start,
            end=args.end,
        )
    except DataUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0 if summary["tiles_remaining"] == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
