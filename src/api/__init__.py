# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""EarthTrend Detective API v2.

El paquete no construye la app al importarse: `src.api.main:app` es el punto de
entrada de uvicorn, y las pruebas importan `src.api.cache`, `src.api.modules`, etc.
sin desplegar una aplicación entera.
"""

from typing import Any

__all__ = ["app"]


def __getattr__(name: str) -> Any:  # pragma: no cover - azúcar de importación
    if name == "app":
        from .main import app as _app

        return _app
    raise AttributeError(name)
