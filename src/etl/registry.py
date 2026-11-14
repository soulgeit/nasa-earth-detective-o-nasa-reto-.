# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Registro de fuentes del ETL (contrato v2 §6).

Despacha por el campo `connector` de la tarjeta del catalogo y devuelve
siempre un TimeSeries v2. Si la fuente no esta implementada o no tiene el
dato, lanza `DataUnavailable` con su codigo: nunca sustituye por otra serie.
"""

from __future__ import annotations

from . import catalog, giovanni, gistemp, nsidc_seaice, power
from .errors import DataUnavailable

CONNECTORS = {
    "power": power,
    "gistemp": gistemp,
    "nsidc_seaice": nsidc_seaice,
}

__all__ = ["get_series", "get_grid", "parse_giovanni_csv", "DataUnavailable"]


def get_series(variable_id, *, lat=None, lon=None, bbox=None, start=None, end=None) -> dict:
    """TimeSeries v2 de la variable pedida en el lugar pedido."""
    card = catalog.get_variable(variable_id)
    connector = card.get("connector")
    if connector == "giovanni_csv":
        raise DataUnavailable(
            "VARIABLE_UNKNOWN",
            f"{variable_id} solo existe como CSV exportado de Giovanni: "
            "usa parse_giovanni_csv(text) con el fichero del usuario",
        )
    module = CONNECTORS.get(connector)
    if module is None:
        raise DataUnavailable("VARIABLE_UNKNOWN", f"conector {connector!r} no soportado")
    return module.series(variable_id, lat=lat, lon=lon, bbox=bbox, start=start, end=end)


def get_grid(variable_id, bbox, *, start=None, end=None) -> dict:
    """Rejilla [t][lat][lon] de la variable en la caja pedida."""
    card = catalog.get_variable(variable_id)
    connector = card.get("connector")
    module = CONNECTORS.get(connector)
    if module is None or not hasattr(module, "grid"):
        raise DataUnavailable("VARIABLE_UNKNOWN", f"conector {connector!r} sin rejilla")
    return module.grid(variable_id, bbox, start=start, end=end)


def parse_giovanni_csv(text: str, variable_id: str | None = None) -> dict:
    """CSV de Giovanni (subido por el usuario) -> TimeSeries v2, kind=user_upload."""
    return giovanni.parse_csv(text, variable_id=variable_id)
