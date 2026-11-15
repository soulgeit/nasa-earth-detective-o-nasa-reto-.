# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Pruebas del respaldo estático (A6) y del shim sin API.

No levantan red: ejercitan `scripts/build_static.py` sobre casos congelados
temporales y comprueban que el shim responde con datos horneados o con el
error de contrato, nunca con cifras inventadas.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build_static.py"


@pytest.fixture()
def staged_repo(tmp_path: Path) -> Path:
    """Copia mínima del repo: UI, catálogo y un caso congelado real."""
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPT, root / "scripts" / "build_static.py")

    for item in (REPO_ROOT / "src" / "ui").iterdir():
        if item.is_file():
            (root / "src" / "ui").mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, root / "src" / "ui" / item.name)

    # `i18n.js` belongs to the UI lane; this branch only needs *a* file with that
    # name to prove the build refuses to ship an incomplete page.
    i18n = root / "src" / "ui" / "i18n.js"
    if not i18n.exists():
        (root / "src" / "ui").mkdir(parents=True, exist_ok=True)
        i18n.write_text("window.__etdI18n = { t: (k) => k, applyTranslations() {} };", encoding="utf-8")

    (root / "data" / "catalog").mkdir(parents=True)
    shutil.copy2(
        REPO_ROOT / "data" / "catalog" / "variables.seed.json",
        root / "data" / "catalog" / "variables.seed.json",
    )

    analysis = {
        "schema": "analysis/2",
        "region": {"kind": "point", "name": "Lima, Peru", "lat": -12.05, "lon": -77.03, "bbox": None},
        "period": {"start": "1981-01", "end": "2025-12", "n_obs": 540},
        "variable": {"id": "T2M", "names": {"es": "Temperatura", "en": "Temperature"}, "unit": "°C"},
        "trend": {"sen_slope_per_decade": 0.31},
        "provenance": {"kind": "nasa_api", "source": "NASA POWER", "request_url": "https://example"},
    }
    # El caso global no trae posición: la variable sin lugar cambia tierra por área.
    global_analysis = {
        "schema": "analysis/2",
        "region": {"kind": "named", "name": None, "lat": None, "lon": None, "bbox": None},
        "period": {"start": "1979-01", "end": "2025-12", "n_obs": 576},
        "trend": {"sen_slope_per_decade": -0.5},
        "provenance": {"kind": "nasa_file", "source": "NSIDC"},
    }
    (root / "data" / "cases").mkdir(parents=True)
    # `data/cases/index.json` real publica RUTAS (`paths`), no el análisis inline.
    # Esta es la forma que el build debe saber leer (regresión: horneaba 0 análisis).
    (root / "data" / "cases" / "lima-t2m").mkdir()
    (root / "data" / "cases" / "lima-t2m" / "analysis.json").write_text(
        json.dumps(analysis), encoding="utf-8"
    )
    (root / "data" / "cases" / "arctic-seaice").mkdir()
    (root / "data" / "cases" / "arctic-seaice" / "analysis.json").write_text(
        json.dumps(global_analysis), encoding="utf-8"
    )
    (root / "data" / "cases" / "index.json").write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "lima-t2m",
                        "variable_id": "T2M",
                        "names": {"es": "Lima, Perú", "en": "Lima, Peru"},
                        "region": {"kind": "point", "lat": -12.05, "lon": -77.03, "bbox": None},
                        "paths": {"analysis": "data/cases/lima-t2m/analysis.json"},
                    },
                    {
                        "id": "arctic-seaice",
                        "variable_id": "SEAICE_EXTENT_N",
                        "region": {"kind": "named", "lat": None, "lon": None, "bbox": None},
                        "paths": {"analysis": "data/cases/arctic-seaice/analysis.json"},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return root


def _build(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "build_static.py"), "--from-cases"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_build_creates_complete_dist(staged_repo: Path) -> None:
    result = _build(staged_repo)
    assert result.returncode == 0, result.stderr
    dist = staged_repo / "dist"
    for name in ("index.html", "app.js", "i18n.js", "styles.css", "static-api.js"):
        assert (dist / name).exists(), f"{name} missing from dist/"
    assert (dist / "api" / "cases.json").exists()
    assert (dist / "api" / "catalog_variables.json").exists()
    assert (dist / "api" / "analyze__lima-t2m.json").exists()
    # Regresión: con el formato real (`paths`) el build horneaba 0 análisis.
    assert (dist / "api" / "analyze__arctic-seaice.json").exists()
    # GitHub Pages ejecuta Jekyll salvo que exista `.nojekyll`.
    assert (dist / ".nojekyll").exists()


def test_nojekyll_is_empty(staged_repo: Path) -> None:
    assert _build(staged_repo).returncode == 0
    assert (staged_repo / "dist" / ".nojekyll").read_text(encoding="utf-8") == ""


def test_case_endpoint_is_baked(staged_repo: Path) -> None:
    """La interfaz abre un caso con GET /api/cases/<id>; el shim debe tenerlo."""
    assert _build(staged_repo).returncode == 0
    shim = (staged_repo / "dist" / "static-api.js").read_text(encoding="utf-8")
    assert "'/api/cases/'" in shim
    assert "case__" in shim


def test_shim_is_injected_before_app_js(staged_repo: Path) -> None:
    assert _build(staged_repo).returncode == 0
    html = (staged_repo / "dist" / "index.html").read_text(encoding="utf-8")
    shim = html.index("static-api.js")
    app = html.index('<script src="app.js')  # with or without the ?v= cache-busting query
    assert shim < app, "static-api.js must load before app.js"


def test_shim_contains_baked_index_with_position(staged_repo: Path) -> None:
    assert _build(staged_repo).returncode == 0
    shim = (staged_repo / "dist" / "static-api.js").read_text(encoding="utf-8")
    match = re.search(r"var INDEX = (\{.*?\});\s*/\*", shim, re.S)
    assert match, "INDEX literal not found"
    index = json.loads(match.group(1))
    entry = index["analyze__lima-t2m"]
    assert entry["variable_id"] == "T2M"
    assert entry["position"] == "-12.05,-77.03"
    assert entry["payload"]["schema"] == "analysis/2"
    # El caso global no tiene posición y aun así debe llevar su variable.
    global_entry = index["analyze__arctic-seaice"]
    assert global_entry["variable_id"] == "SEAICE_EXTENT_N"
    assert global_entry["position"] is None


def test_global_case_matches_without_position(staged_repo: Path) -> None:
    """Hielo marino y GISTEMP no llevan lat/lon: la variable basta para servirlos."""
    assert _build(staged_repo).returncode == 0
    shim = (staged_repo / "dist" / "static-api.js").read_text(encoding="utf-8")
    assert "if (!baked || baked === 'null,null'" in shim


def test_shim_never_invents_data(staged_repo: Path) -> None:
    """Lo que no está horneado debe caer en `DATA_UNAVAILABLE`."""
    assert _build(staged_repo).returncode == 0
    shim = (staged_repo / "dist" / "static-api.js").read_text(encoding="utf-8")
    assert "DATA_UNAVAILABLE" in shim
    assert "return Promise.resolve(jsonResponse(errorPayload('DATA_UNAVAILABLE'" in shim


def test_cases_are_flattened_for_the_ui(staged_repo: Path) -> None:
    """`openCase()` lee c.lat/c.lon en la raíz; el índice los trae en `region`."""
    assert _build(staged_repo).returncode == 0
    cases = json.loads((staged_repo / "dist" / "api" / "cases.json").read_text(encoding="utf-8"))["cases"]
    lima = next(c for c in cases if c["id"] == "lima-t2m")
    assert lima["lat"] == -12.05 and lima["lon"] == -77.03
    assert lima["region_name"]


def test_missing_ui_file_fails_loudly(staged_repo: Path) -> None:
    (staged_repo / "src" / "ui" / "i18n.js").unlink()
    result = _build(staged_repo)
    assert result.returncode != 0
    assert "i18n.js" in (result.stdout + result.stderr)


# --- arquitecto, Ronda 5 -----------------------------------------------------

def test_shim_serves_the_frozen_case_route(staged_repo: Path) -> None:
    """La interfaz abre un caso con GET /api/cases/<id>; el respaldo debe responderlo."""
    assert _build(staged_repo).returncode == 0
    shim = (staged_repo / "dist" / "static-api.js").read_text(encoding="utf-8")
    assert "path.indexOf('/api/cases/') === 0" in shim
    assert "analysis: INDEX['analyze__' + caseId].payload" in shim


def test_bbox_is_compared_as_numbers(staged_repo: Path) -> None:
    """'-71' (JavaScript) y '-71.0' (Python) son la misma caja."""
    assert _build(staged_repo).returncode == 0
    shim = (staged_repo / "dist" / "static-api.js").read_text(encoding="utf-8")
    assert "parseFloat(a[k]) - parseFloat(b[k])" in shim
    assert "baked === want" not in shim
