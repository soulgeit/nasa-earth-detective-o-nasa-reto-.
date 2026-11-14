# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Köppen-Geiger climate classification from monthly climatology (contract R5).

Rules transcribed from Peel, Finlayson & McMahon (2007), *Updated world map of the
Köppen-Geiger climate classification*, Hydrol. Earth Syst. Sci. 11, 1633-1644,
Table 1 — verified by reading the PDF at
https://hess.copernicus.org/articles/11/1633/2007/hess-11-1633-2007.pdf on
2026-11-14. That paper follows Köppen (1936) except for one documented change:

    the temperate/cold boundary (C/D) uses Tcold > 0 °C, not the classic -3 °C
    ("We have followed Russell (1931) and used the temperature of the coldest
    month >0 °C, rather than >-3 °C").

Symbols used below, all in °C and mm:
    Tcold, Thot   temperature of the coldest / hottest month
    Tmon10        number of months with T > 10 °C
    MAP           mean annual precipitation
    MAT           mean annual temperature
    Pdry          precipitation of the driest month
    Psdry/Pswet   driest / wettest month of summer
    Pwdry/Pwwet   driest / wettest month of winter
    Pthreshold    2*MAT if 70% of MAP falls in winter; 2*MAT+28 if 70% in summer;
                  otherwise 2*MAT+14
    Summer/winter = the warmer/cooler six-month period of ONDJFM and AMJJAS.

This module only classifies. It never fetches, and it never fills a missing month
with a guess: fewer than 12 monthly values -> insufficient data, explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

MONTHS = tuple(range(1, 13))
ONDJFM = (10, 11, 12, 1, 2, 3)
AMJJAS = (4, 5, 6, 7, 8, 9)

# Plain-language names, both languages. These are translations of the standard
# Köppen group names, not new science.
GROUP_NAMES = {
    "A": {"es": "tropical", "en": "tropical"},
    "B": {"es": "árido o semiárido", "en": "arid or semi-arid"},
    "C": {"es": "templado", "en": "temperate"},
    "D": {"es": "frío (continental)", "en": "cold (continental)"},
    "E": {"es": "polar", "en": "polar"},
}

SUBGROUP_NAMES = {
    "Af": {"es": "selva tropical, llueve todo el año", "en": "tropical rainforest, rain all year"},
    "Am": {"es": "monzón tropical", "en": "tropical monsoon"},
    "Aw": {"es": "sabana tropical, invierno seco", "en": "tropical savanna, dry winter"},
    "BW": {"es": "desierto", "en": "desert"},
    "BS": {"es": "estepa", "en": "steppe"},
    "Cs": {"es": "templado con verano seco", "en": "temperate with dry summer"},
    "Cw": {"es": "templado con invierno seco", "en": "temperate with dry winter"},
    "Cf": {"es": "templado sin estación seca", "en": "temperate without dry season"},
    "Ds": {"es": "frío con verano seco", "en": "cold with dry summer"},
    "Dw": {"es": "frío con invierno seco", "en": "cold with dry winter"},
    "Df": {"es": "frío sin estación seca", "en": "cold without dry season"},
    "ET": {"es": "tundra", "en": "tundra"},
    "EF": {"es": "hielo permanente", "en": "frost / ice cap"},
}

THIRD_LETTER = {
    "h": {"es": "caliente", "en": "hot"},
    "k": {"es": "frío", "en": "cold"},
    "a": {"es": "verano caluroso", "en": "hot summer"},
    "b": {"es": "verano templado", "en": "warm summer"},
    "c": {"es": "verano frío", "en": "cold summer"},
    "d": {"es": "invierno muy frío", "en": "very cold winter"},
}


class InsufficientClimatology(ValueError):
    """Fewer than 12 monthly values in temperature or precipitation."""


@dataclass(frozen=True)
class Climatology:
    temp_c: dict[int, float]   # month -> mean temperature °C
    precip_mm: dict[int, float]  # month -> mean monthly precipitation total, mm

    def diagnostics(self) -> dict[str, Any]:
        return {
            "t_cold": min(self.temp_c[m] for m in MONTHS),
            "t_hot": max(self.temp_c[m] for m in MONTHS),
            "t_months_above_10": sum(1 for m in MONTHS if self.temp_c[m] > 10),
            "map_mm": round(sum(self.precip_mm[m] for m in MONTHS), 1),
            "mat_c": round(sum(self.temp_c[m] for m in MONTHS) / 12.0, 2),
            "p_dry_mm": round(min(self.precip_mm[m] for m in MONTHS), 1),
            "p_wet_mm": round(max(self.precip_mm[m] for m in MONTHS), 1),
        }


def build_climatology(
    temp_by_month: dict[int, float | None],
    precip_by_month: dict[int, float | None],
) -> Climatology:
    """Require 12 valid months for both series; raise instead of interpolating."""
    temp: dict[int, float] = {}
    precip: dict[int, float] = {}
    missing_t = [m for m in MONTHS if temp_by_month.get(m) is None]
    missing_p = [m for m in MONTHS if precip_by_month.get(m) is None]
    if missing_t or missing_p:
        raise InsufficientClimatology(
            f"missing months — temperature: {missing_t or 'none'}, precipitation: {missing_p or 'none'}"
        )
    for m in MONTHS:
        temp[m] = float(temp_by_month[m])  # type: ignore[arg-type]
        precip[m] = float(precip_by_month[m])  # type: ignore[arg-type]
    return Climatology(temp_c=temp, precip_mm=precip)


def _season_sums(precip: dict[int, float], months: Sequence[int]) -> dict[int, float]:
    return {m: precip[m] for m in months}


def classify(clim: Climatology) -> dict[str, Any]:
    """Return the Köppen-Geiger code plus the numbers that produced it."""
    diag = clim.diagnostics()
    tcold, thot = diag["t_cold"], diag["t_hot"]
    tmon10 = diag["t_months_above_10"]
    precip = clim.precip_mm
    map_mm = diag["map_mm"]
    mat = diag["mat_c"]

    summer = ONDJFM if sum(clim.temp_c[m] for m in ONDJFM) > sum(clim.temp_c[m] for m in AMJJAS) else AMJJAS
    winter = AMJJAS if summer is ONDJFM else ONDJFM

    psdry = min(_season_sums(precip, summer).values())
    pswet = max(_season_sums(precip, summer).values())
    pwdry = min(_season_sums(precip, winter).values())
    pwwet = max(_season_sums(precip, winter).values())
    pdry = min(precip.values())

    summer_share = sum(precip[m] for m in summer) / map_mm if map_mm > 0 else 0.0
    winter_share = sum(precip[m] for m in winter) / map_mm if map_mm > 0 else 0.0
    if winter_share > 0.70:
        pthreshold = 2.0 * mat
    elif summer_share > 0.70:
        pthreshold = 2.0 * mat + 28.0
    else:
        pthreshold = 2.0 * mat + 14.0

    notes: list[str] = []

    # ---- E: polar ----------------------------------------------------------
    # Peel et al. 2007, §3: "Since all locations that satisfy the B climate criteria
    # will also satisfy one of the other (A, C, D or E) climate criteria, the B
    # climates must be identified first." So the B test comes before A/C/D/E.
    if map_mm < 10.0 * pthreshold:
        group = "BW" if map_mm < 5.0 * pthreshold else "BS"
        code = group + ("h" if mat >= 18 else "k")
        return _result(
            code,
            diag,
            {"p_threshold": round(pthreshold, 2), "season_summer_share": round(summer_share, 3),
             "season_winter_share": round(winter_share, 3)},
            notes,
        )

    if thot < 10:
        code = "ET" if thot > 0 else "EF"
        return _result(code, diag, {"psdry": psdry, "pwdry": pwdry, "summer_months": list(summer)}, notes)

    # ---- A: tropical -------------------------------------------------------
    if tcold >= 18:
        if pdry >= 60:
            code = "Af"
        elif pdry >= 100.0 - map_mm / 25.0:
            code = "Am"
        else:
            code = "Aw"
        return _result(code, diag, {"p_dry": pdry, "p_threshold_am": round(100 - map_mm / 25, 1)}, notes)

    # ---- C / D: temperate vs cold (Peel: 0 °C boundary) --------------------
    if thot > 10 and tcold > 0:
        group = "C"
    elif thot > 10 and tcold <= 0:
        group = "D"
    else:
        # Falls outside every table row: report it instead of forcing a label.
        return _result("UNKNOWN", diag, {"p_threshold": round(pthreshold, 2)}, ["no Köppen row matched"])

    if psdry < 40 and psdry < pswet / 3.0:
        second = "s"
    elif pwdry < pswet / 10.0:
        second = "w"
    else:
        second = "f"

    # Peel's Table 1 order for the third letter is a -> b -> (d for D) -> c:
    #   a: Thot >= 22
    #   b: Not(a) & Tmon10 >= 4
    #   d: Not(a or b) & Tcold < -38   (D only)
    #   c: everything else
    if thot >= 22:
        third = "a"
    elif tmon10 >= 4:
        third = "b"
    elif group == "D" and tcold < -38:
        third = "d"
    else:
        third = "c"

    code = group + second + third
    return _result(
        code,
        diag,
        {"psdry": round(psdry, 1), "pswet": round(pswet, 1), "pwdry": round(pwdry, 1),
         "pwwet": round(pwwet, 1), "summer_months": list(summer)},
        notes,
    )


def _result(code: str, diag: dict[str, Any], extra: dict[str, Any], notes: list[str]) -> dict[str, Any]:
    return {
        "code": code,
        "group": code[0] if code and code[0] in GROUP_NAMES else None,
        "subgroup": code[:2] if len(code) >= 2 else code,
        "names": {
            "es": _name_es(code),
            "en": _name_en(code),
        },
        "diagnostics": diag,
        "criteria_values": extra,
        "notes": notes,
        "method": {
            "citation": "Peel, Finlayson & McMahon (2007), HESS 11:1633-1644, Table 1",
            "url": "https://hess.copernicus.org/articles/11/1633/2007/",
            "deviation": "C/D boundary at Tcold > 0 °C (Russell 1931), as in Peel et al. 2007",
        },
    }


def _name_es(code: str) -> str:
    group = GROUP_NAMES.get(code[0], {}).get("es") if code else None
    sub = SUBGROUP_NAMES.get(code[:2], {}).get("es")
    third = THIRD_LETTER.get(code[2], {}).get("es") if len(code) > 2 else None
    bits = [b for b in (group, sub, third) if b]
    return ", ".join(bits) if bits else code


def _name_en(code: str) -> str:
    group = GROUP_NAMES.get(code[0], {}).get("en") if code else None
    sub = SUBGROUP_NAMES.get(code[:2], {}).get("en")
    third = THIRD_LETTER.get(code[2], {}).get("en") if len(code) > 2 else None
    bits = [b for b in (group, sub, third) if b]
    return ", ".join(bits) if bits else code


def from_monthly_series(
    temp_c_by_month: dict[int, float | None],
    precip_mm_by_month: dict[int, float | None],
) -> dict[str, Any]:
    clim = build_climatology(temp_c_by_month, precip_mm_by_month)
    return classify(clim)
