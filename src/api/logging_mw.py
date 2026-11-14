# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Registro estructurado sin datos personales (A4).

Una línea JSON por petición: método, ruta, estado, duración y el código de error
si lo hubo. No se registra la IP, ni el `User-Agent`, ni cabeceras, ni cuerpos:
nada que identifique a una persona. Sirve para diagnosticar caídas (¿falla POWER?
¿qué endpoint tarda?) sin convertirse en un fichero de datos personales.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

log = logging.getLogger("etd.api.access")


class StructuredAccessLog(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any):
        started = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            record = {
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "ms": round((time.perf_counter() - started) * 1000),
            }
            log.info(json.dumps(record, ensure_ascii=False))
