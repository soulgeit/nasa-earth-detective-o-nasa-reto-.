# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
Configuración de la API leída del entorno (nunca de valores secretos en el repo).

Todas las variables son opcionales; los valores por defecto son los de
`.env.example` y solo afectan al comportamiento, no a los datos servidos.
"""

from __future__ import annotations

import os
from pathlib import Path

# Raíz del repositorio: src/api/config.py -> src/api -> src -> <repo>
REPO_ROOT = Path(__file__).resolve().parents[2]

UI_DIR = REPO_ROOT / "src" / "ui"
DATA_DIR = REPO_ROOT / "data"
CATALOG_DIR = DATA_DIR / "catalog"
CASES_DIR = DATA_DIR / "cases"
ATLAS_DIR = DATA_DIR / "atlas"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "real"


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def allow_fixtures() -> bool:
    """Leído en cada uso: los tests y el arranque pueden cambiarlo sin recargar."""
    return _bool("ALLOW_FIXTURES", False)


ALLOW_FIXTURES = allow_fixtures()

#: Modo de IA declarado por el entorno. La API no lo ejecuta: solo lo informa.
AI_MODE = os.environ.get("AI_MODE", "extractive").strip().lower() or "extractive"

#: Directorio de caché del ETL (lo usa src/etl; aquí solo se informa).
DATA_CACHE_DIR = os.environ.get("DATA_CACHE_DIR", "data/cache")

#: Vida de la caché de análisis en memoria, en segundos.
ANALYSIS_CACHE_TTL = _int("ANALYSIS_CACHE_TTL", 3600)

#: Peticiones por minuto y por IP a los endpoints que llaman a la NASA.
RATE_LIMIT_PER_MIN = _int("RATE_LIMIT_PER_MIN", 120)

#: Tamaño máximo de un CSV subido (5 MB, contrato A2).
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

#: Extensión máxima de una caja en grados por lado (red de seguridad; el ETL
#: trocea cajas mayores por su cuenta). Evita consultas absurdas.
MAX_BBOX_SPAN_DEG = 60.0

#: Límite de observaciones que la API acepta analizar en una petición.
MAX_ANALYSIS_OBS = 5000

API_TITLE = "EarthTrend Detective API"
API_VERSION = "2.0.0"
