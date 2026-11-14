# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
Genera `dist/`: la UI funcionando **sin API**, solo con los casos y el atlas
reales congelados (contrato A6). Es el seguro por si el servidor cae durante
las semanas de evaluación.

Cómo funciona:
1. Copia `src/ui/` (HTML, JS, CSS, i18n) tal cual.
2. Escribe `dist/api/*.json` con las respuestas reales que hoy sirve la API
   para los casos: `/api/health`, `/api/catalog/variables`, `/api/cases`,
   `/api/atlas/<id>` y un `/api/analyze` por caso.
3. Interpone `dist/static-api.js` **antes** de `app.js`: responde a `fetch`
   desde esos archivos y devuelve el mismo `{error:{code,message,hint}}` ante
   lo que no esté precalculado. Nunca inventa datos: lo que falta es un error.

Uso:
    python scripts/build_static.py              # intenta la API en localhost:8000
    python scripts/build_static.py --base URL   # usa una API ya desplegada
    python scripts/build_static.py --from-cases # solo data/cases + data/atlas
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
UI_DIR = REPO_ROOT / "src" / "ui"
DIST = REPO_ROOT / "dist"

HEALTH = {"status": "static", "version": "static-1", "ai_mode": "off", "sources_up": {"etl": False, "stats": False}}


def _get(base: str, path: str, params: dict[str, Any] | None = None) -> tuple[int, bytes]:
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "etd-build-static"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _write(dist_api: Path, name: str, payload: Any) -> None:
    (dist_api / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def build_from_api(base: str) -> dict[str, int]:
    """Hornea las respuestas de una API viva (local o desplegada)."""
    dist_api = DIST / "api"
    dist_api.mkdir(parents=True, exist_ok=True)

    counts = {"cases": 0, "analyses": 0, "atlas": 0, "errors": 0}

    status, body = _get(base, "/api/health")
    _write(dist_api, "health", json.loads(body) if status == 200 else HEALTH)

    status, body = _get(base, "/api/catalog/variables", {"lang": "es"})
    if status != 200:
        raise SystemExit(f"catalog unavailable ({status}); cannot build a static copy")
    catalog = json.loads(body)
    _write(dist_api, "catalog_variables", catalog)

    status, body = _get(base, "/api/cases")
    cases = json.loads(body).get("cases", []) if status == 200 else []
    _write(dist_api, "cases", {"cases": cases})

    for case in cases:
        case_id = case.get("id") or case.get("region_id") or case.get("variable_id")
        params = {"variable_id": case.get("variable_id")}
        if case.get("bbox"):
            params["bbox"] = ",".join(str(v) for v in case["bbox"])
        else:
            params["lat"] = case.get("lat")
            params["lon"] = case.get("lon")
        status, body = _get(base, "/api/analyze", params)
        if status == 200:
            _write(dist_api, f"analyze__{case_id}", json.loads(body))
            counts["analyses"] += 1
        else:
            counts["errors"] += 1

    for card in catalog.get("variables", []):
        vid = card.get("id")
        status, body = _get(base, f"/api/atlas/{urllib.parse.quote(vid)}")
        if status == 200:
            _write(dist_api, f"atlas__{vid}", json.loads(body))
            counts["atlas"] += 1

    counts["cases"] = len(cases)
    return counts


def build_from_cases() -> dict[str, int]:
    """Sin API: usa solo los archivos congelados de `data/cases` y `data/atlas`."""
    dist_api = DIST / "api"
    dist_api.mkdir(parents=True, exist_ok=True)
    counts = {"cases": 0, "analyses": 0, "atlas": 0, "errors": 0}

    _write(dist_api, "health", HEALTH)

    cases_index = REPO_ROOT / "data" / "cases" / "index.json"
    if not cases_index.exists():
        raise SystemExit("data/cases/index.json not found (Hermes 2 lane); nothing to freeze")
    cases = json.loads(cases_index.read_text(encoding="utf-8"))
    cases = cases.get("cases", cases) if isinstance(cases, dict) else cases
    _write(dist_api, "cases", {"cases": cases})
    for case in cases:
        if case.get("analysis"):
            case_id = case.get("id") or case.get("region_id")
            _write(dist_api, f"analyze__{case_id}", case["analysis"])
            counts["analyses"] += 1
    counts["cases"] = len(cases)

    atlas_dir = REPO_ROOT / "data" / "atlas"
    if atlas_dir.exists():
        for path in atlas_dir.glob("*.json"):
            if path.name == "index.json":
                continue
            _write(dist_api, f"atlas__{path.stem}", json.loads(path.read_text(encoding="utf-8")))
            counts["atlas"] += 1

    catalog = REPO_ROOT / "data" / "catalog" / "variables.json"
    if catalog.exists():
        _write(dist_api, "catalog_variables", json.loads(catalog.read_text(encoding="utf-8")))
    else:
        # La semilla sirve: el respaldo estático necesita el selector de variables
        # aunque Hermes 1 no haya publicado el catálogo completo. Se normaliza
        # aquí, sin importar `src.api`, para que el script sea autónomo.
        seed = REPO_ROOT / "data" / "catalog" / "variables.seed.json"
        if seed.exists():
            raw = json.loads(seed.read_text(encoding="utf-8"))
            cards = [_seed_card(e) for e in raw.get("live", [])]
            cards += [_seed_card(e) for e in raw.get("planned_giovanni", [])]
            _write(
                dist_api,
                "catalog_variables",
                {
                    "catalog": {
                        "source": "seed",
                        "loaded_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                        "is_complete": False,
                        "n_variables": len(cards),
                    },
                    "variables": cards,
                },
            )
    return counts


def _seed_card(entry: dict[str, Any]) -> dict[str, Any]:
    """Entrada de la semilla -> tarjeta mínima §8, sin inventar campos."""
    longname = entry.get("power_longname") or entry["id"]
    text = {"es": longname, "en": longname}
    return {
        "id": entry["id"],
        "connector": entry.get("connector"),
        "names": text,
        "simple_definition": dict(text),
        "unit": entry.get("unit", ""),
        "ratio_scale": bool(entry.get("ratio_scale", False)),
        "sphere": entry.get("sphere"),
        "source": {
            "model_or_mission": entry.get("challenge_named_source"),
            "via": "NASA POWER" if entry.get("connector") == "power" else entry.get("connector"),
            "challenge_named_source": entry.get("challenge_named_source"),
            "start": entry.get("start"),
            "homogeneous_since": entry.get("homogeneous_since"),
        },
        "_catalog_source": "seed",
    }


STATIC_API_JS = r"""/* SI-assisted: claude-omni-3 (Claude Opus 5.5)
 * Static API shim for the offline backup build.
 *
 * Intercepts fetch() calls to /api/* and answers them from ./api/*.json,
 * which scripts/build_static.py baked from real, frozen case files.
 * If something was not precomputed it returns the same contract error the
 * real API would: this build never invents a number.
 */
(function () {
  'use strict';
  if (window.__etdStaticApi) return;
  window.__etdStaticApi = true;

  var INDEX = __INDEX__;   /* {path: file} baked by the build script */

  function errorPayload(code, hint) {
    return {
      error: {
        code: code,
        message: {
          es: 'Este respaldo estático solo incluye los casos congelados.',
          en: 'This static backup only includes the frozen cases.'
        },
        hint: hint || ''
      }
    };
  }

  function jsonResponse(body, status) {
    return new Response(JSON.stringify(body), {
      status: status || 200,
      headers: { 'Content-Type': 'application/json', 'X-ETD-Static': '1' }
    });
  }

  function samePosition(baked, params) {
    var want = params.get('bbox');
    if (want) return baked === want.replace(/\s+/g, '');
    var lat = parseFloat(params.get('lat'));
    var lon = parseFloat(params.get('lon'));
    if (baked.indexOf(',') < 0 || isNaN(lat) || isNaN(lon)) return false;
    var parts = baked.split(',');
    return Math.abs(parseFloat(parts[0]) - lat) < 5e-4 && Math.abs(parseFloat(parts[1]) - lon) < 5e-4;
  }

  function slug(path, params) {
    if (path === '/api/health' || path === '/health') return 'health';
    if (path === '/api/catalog/variables') return 'catalog_variables';
    if (path === '/api/cases') return 'cases';
    if (path.indexOf('/api/atlas/') === 0) return 'atlas__' + decodeURIComponent(path.slice('/api/atlas/'.length));
    if (path === '/api/analyze' || path === '/api/series') {
      var vid = params.get('variable_id');
      for (var key in INDEX) {
        if (key.indexOf('analyze__') !== 0) continue;
        var baked = INDEX[key];
        if (baked.variable_id === vid && samePosition(baked.position, params)) return key;
      }
    }
    return null;
  }

  var realFetch = window.fetch ? window.fetch.bind(window) : null;

  window.fetch = function (input, init) {
    var url;
    try { url = new URL(typeof input === 'string' ? input : input.url, location.href); }
    catch (_) { return realFetch ? realFetch(input, init) : Promise.reject(new Error('bad url')); }

    if (url.origin !== location.origin || url.pathname.indexOf('/api/') !== 0) {
      return realFetch ? realFetch(input, init) : Promise.reject(new Error('offline'));
    }

    var key = slug(url.pathname, url.searchParams);
    if (key && INDEX[key]) {
      var entry = INDEX[key];
      var body = entry.payload;
      if (key.indexOf('analyze__') === 0) body = entry.payload;
      return Promise.resolve(jsonResponse(body, 200));
    }
    return Promise.resolve(jsonResponse(errorPayload('DATA_UNAVAILABLE',
      'Only the frozen demonstration cases are available offline.'), 503));
  };
})();
"""


def _bake_index(dist_api: Path) -> dict[str, Any]:
    """Construye el índice de rutas con la posición que las produjo."""
    index: dict[str, Any] = {}
    for path in sorted(dist_api.glob("*.json")):
        stem = path.stem
        payload = json.loads(path.read_text(encoding="utf-8"))
        entry: dict[str, Any] = {"payload": payload}
        if stem.startswith("analyze__"):
            region = payload.get("region") or {}
            if region.get("bbox"):
                entry["position"] = ",".join(str(v) for v in region["bbox"])
            else:
                entry["position"] = f"{region.get('lat')},{region.get('lon')}"
            entry["variable_id"] = (payload.get("variable") or {}).get("id")
        index[stem] = entry
    return index


def write_shim(dist_api: Path) -> None:
    index = _bake_index(dist_api)
    js = STATIC_API_JS.replace("__INDEX__", json.dumps(index, ensure_ascii=False))
    (DIST / "static-api.js").write_text(js, encoding="utf-8")


def patch_index_html() -> None:
    index = DIST / "index.html"
    if not index.exists():
        raise SystemExit("dist/index.html missing (UI copy failed)")
    html = index.read_text(encoding="utf-8")
    if "static-api.js" in html:
        return
    marker = '<script src="app.js"></script>'
    if marker not in html:
        # Insert before </body> as a last resort.
        html = html.replace("</body>", "  <script src=\"static-api.js\"></script>\n</body>")
    else:
        html = html.replace(marker, '<script src="static-api.js"></script>\n  ' + marker)
    index.write_text(html, encoding="utf-8")


def copy_ui() -> None:
    if not UI_DIR.exists():
        raise SystemExit(f"UI directory missing: {UI_DIR}")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    missing = []
    for item in UI_DIR.iterdir():
        if item.is_file():
            shutil.copy2(item, DIST / item.name)
    # `index.html` referencia estos archivos; si falta uno el respaldo no carga.
    for name in ("index.html", "app.js", "styles.css", "i18n.js"):
        if not (DIST / name).exists():
            missing.append(name)
    if missing:
        raise SystemExit(
            f"UI is missing {', '.join(missing)}. Merge feature/ui into this branch first, "
            "or run this script from a worktree that has it."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the offline static backup in dist/")
    parser.add_argument("--base", default="http://127.0.0.1:8000", help="API base URL to bake from")
    parser.add_argument("--from-cases", action="store_true", help="use data/cases/*.json instead of a live API")
    parser.add_argument("--no-patch", action="store_true", help="do not inject static-api.js into index.html")
    args = parser.parse_args()

    copy_ui()
    if args.from_cases:
        counts = build_from_cases()
    else:
        counts = build_from_api(args.base)
    write_shim(DIST / "api")
    if not args.no_patch:
        patch_index_html()

    print("dist/ built")
    print(json.dumps(counts, indent=1))
    print("open dist/index.html over a local web server (file:// blocks fetch)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
