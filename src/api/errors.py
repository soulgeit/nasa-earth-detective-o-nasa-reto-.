# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
Errores de la API con el formato del contrato §7:

    {"error": {"code": "...", "message": {"es", "en"}, "hint": "..."}}

Regla de oro: **nunca se sustituye un dato en silencio**. Si no hay dato se
devuelve un error con código; el cliente decide qué hacer.
"""

from __future__ import annotations

from typing import Any, Mapping

from fastapi import Request
from fastapi.responses import JSONResponse

# Códigos válidos (contrato §6 y §7).
KNOWN_CODES: frozenset[str] = frozenset(
    {
        "VARIABLE_UNKNOWN",
        "OUT_OF_COVERAGE",
        "UPSTREAM_ERROR",
        "UPSTREAM_TIMEOUT",
        "BBOX_TOO_LARGE",
        "INSUFFICIENT_DATA",
        "AI_UNAVAILABLE",
        "INVALID_REQUEST",
        "DATA_UNAVAILABLE",
        "NOT_FOUND",
        "TOO_LARGE",
        "RATE_LIMITED",
        "INTERNAL_ERROR",
    }
)

# Mensajes por defecto bilingües. Cada código trae su par `{es, en}`.
DEFAULT_MESSAGES: dict[str, dict[str, str]] = {
    "VARIABLE_UNKNOWN": {
        "es": "La variable solicitada no existe en el catálogo.",
        "en": "The requested variable is not in the catalog.",
    },
    "OUT_OF_COVERAGE": {
        "es": "El punto o la caja están fuera de la cobertura de la fuente.",
        "en": "The point or bounding box is outside the source's coverage.",
    },
    "UPSTREAM_ERROR": {
        "es": "La fuente de datos de la NASA devolvió un error.",
        "en": "The NASA data source returned an error.",
    },
    "UPSTREAM_TIMEOUT": {
        "es": "La fuente de datos de la NASA no respondió a tiempo.",
        "en": "The NASA data source did not respond in time.",
    },
    "BBOX_TOO_LARGE": {
        "es": "La caja geográfica es demasiado grande para una sola consulta.",
        "en": "The bounding box is too large for a single request.",
    },
    "INSUFFICIENT_DATA": {
        "es": "No hay suficientes observaciones para calcular una tendencia.",
        "en": "There are not enough observations to compute a trend.",
    },
    "AI_UNAVAILABLE": {
        "es": "El módulo del detective con IA no está disponible; el resto de la app sigue funcionando.",
        "en": "The AI detective module is unavailable; the rest of the app keeps working.",
    },
    "INVALID_REQUEST": {
        "es": "La petición no es válida.",
        "en": "The request is not valid.",
    },
    "DATA_UNAVAILABLE": {
        "es": "El módulo de datos reales aún no está disponible.",
        "en": "The real-data module is not available yet.",
    },
    "NOT_FOUND": {
        "es": "El recurso no existe.",
        "en": "The resource does not exist.",
    },
    "TOO_LARGE": {
        "es": "La petición supera el tamaño permitido.",
        "en": "The request exceeds the allowed size.",
    },
    "RATE_LIMITED": {
        "es": "Demasiadas peticiones seguidas; espera unos segundos.",
        "en": "Too many requests in a row; wait a few seconds.",
    },
    "INTERNAL_ERROR": {
        "es": "Error interno inesperado.",
        "en": "Unexpected internal error.",
    },
}

#: Código -> estado HTTP. El contrato pide 400/404/422/502/504.
STATUS_BY_CODE: dict[str, int] = {
    "VARIABLE_UNKNOWN": 404,
    "OUT_OF_COVERAGE": 404,
    "BBOX_TOO_LARGE": 422,
    "UPSTREAM_ERROR": 502,
    "UPSTREAM_TIMEOUT": 504,
    "INSUFFICIENT_DATA": 422,
    "AI_UNAVAILABLE": 503,
    "DATA_UNAVAILABLE": 503,
    "INVALID_REQUEST": 400,
    "NOT_FOUND": 404,
    "TOO_LARGE": 413,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
}


class ApiError(Exception):
    """Error con contrato §7. Lo captura el manejador global de FastAPI."""

    def __init__(
        self,
        code: str,
        *,
        status_code: int | None = None,
        message: Mapping[str, str] | None = None,
        hint: str = "",
    ) -> None:
        if code not in KNOWN_CODES:
            # Un código fuera de contrato es un bug del servidor, no del cliente.
            code = "INTERNAL_ERROR"
        self.code = code
        self.status_code = status_code or STATUS_BY_CODE.get(code, 500)
        default = DEFAULT_MESSAGES.get(code, {"es": "Error.", "en": "Error."})
        self.message = {"es": default["es"], "en": default["en"]}
        if message:
            for lang in ("es", "en"):
                if message.get(lang):
                    self.message[lang] = str(message[lang])
        self.hint = hint
        super().__init__(self.code)

    def payload(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": dict(self.message),
                "hint": self.hint,
            }
        }


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.payload())


async def http_exception_handler(_request: Request, exc: Any) -> JSONResponse:
    """Convierte los `HTTPException` de FastAPI al formato §7."""
    code = {
        400: "INVALID_REQUEST",
        404: "NOT_FOUND",
        413: "TOO_LARGE",
        422: "INVALID_REQUEST",
        429: "RATE_LIMITED",
        502: "UPSTREAM_ERROR",
        503: "DATA_UNAVAILABLE",
        504: "UPSTREAM_TIMEOUT",
    }.get(int(getattr(exc, "status_code", 500)), "INTERNAL_ERROR")
    err = ApiError(
        code,
        status_code=int(getattr(exc, "status_code", 500)),
        hint=str(getattr(exc, "detail", "") or ""),
    )
    return JSONResponse(status_code=err.status_code, content=err.payload())
