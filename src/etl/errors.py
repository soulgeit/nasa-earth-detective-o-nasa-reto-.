# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Errores de datos del ETL (contrato v2 §6).

`DataUnavailable` es el unico error que el ETL lanza al resto del sistema:
si falta un dato, falla con un codigo explicito; nunca devuelve otra serie.
"""

CODES = (
    "VARIABLE_UNKNOWN",
    "OUT_OF_COVERAGE",
    "UPSTREAM_ERROR",
    "UPSTREAM_TIMEOUT",
    "BBOX_TOO_LARGE",
)


class DataUnavailable(Exception):
    """Dato no disponible en la fuente. `code` es uno de CODES."""

    def __init__(self, code: str, detail: str | None = None):
        if code not in CODES:
            raise ValueError(f"codigo de error desconocido: {code!r}")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)
