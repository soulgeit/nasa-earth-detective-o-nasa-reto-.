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
    (root / "data" / "cases").mkdir(parents=True)
    (root / "data" / "cases" / "index.json").write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "lima_t2m",
                        "region_id": "lima_t2m",
                        "region_name": "Lima, Peru",
                        "variable_id": "T2M",
                        "lat": -12.05,
                        "lon": -77.03,
                        "analysis": analysis,
                    }
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
    assert (dist / "api" / "analyze__lima_t2m.json").exists()


def test_shim_is_injected_before_app_js(staged_repo: Path) -> None:
    assert _build(staged_repo).returncode == 0
    html = (staged_repo / "dist" / "index.html").read_text(encoding="utf-8")
    shim = html.index("static-api.js")
    app = html.index('<script src="app.js"')
    assert shim < app, "static-api.js must load before app.js"


def test_shim_contains_baked_index_with_position(staged_repo: Path) -> None:
    assert _build(staged_repo).returncode == 0
    shim = (staged_repo / "dist" / "static-api.js").read_text(encoding="utf-8")
    match = re.search(r"var INDEX = (\{.*?\});\s*/\*", shim, re.S)
    assert match, "INDEX literal not found"
    index = json.loads(match.group(1))
    entry = index["analyze__lima_t2m"]
    assert entry["variable_id"] == "T2M"
    assert entry["position"] == "-12.05,-77.03"
    assert entry["payload"]["schema"] == "analysis/2"


def test_shim_never_invents_data(staged_repo: Path) -> None:
    """Lo que no está horneado debe caer en `DATA_UNAVAILABLE`."""
    assert _build(staged_repo).returncode == 0
    shim = (staged_repo / "dist" / "static-api.js").read_text(encoding="utf-8")
    assert "DATA_UNAVAILABLE" in shim
    assert "return Promise.resolve(jsonResponse(errorPayload('DATA_UNAVAILABLE'" in shim


def test_missing_ui_file_fails_loudly(staged_repo: Path) -> None:
    (staged_repo / "src" / "ui" / "i18n.js").unlink()
    result = _build(staged_repo)
    assert result.returncode != 0
    assert "i18n.js" in (result.stdout + result.stderr)
