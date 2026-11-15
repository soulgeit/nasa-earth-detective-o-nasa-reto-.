# SI-assisted: hermes-2 (Claude Opus 5.5)
"""Titulos y frases de hallazgo por caso (Ronda 3, tarea 4).

Cada frase sale SOLO de los numeros de `analysis.json`: nada de causas ni de
historia (esa la decide el humano). Se escriben en ingles y espanol.

Uso: python scripts/write_case_copy.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "data", "cases")

COPY = {
    "lima-t2m": {
        "title_en": "Lima, Peru: air temperature 1981-2025",
        "title_es": "Lima, Perú: temperatura del aire 1981-2025",
        "finding_en": "Air temperature rose about 0.16 °C per decade (Theil-Sen, 1981-2025), "
                      "a total of 0.71 °C. Mann-Kendall finds the trend significant; the "
                      "least-squares test disagrees, so the verdict is SIGNIFICANT rather than strong.",
        "finding_es": "La temperatura del aire subió unos 0,16 °C por década (Theil-Sen, 1981-2025), "
                      "0,71 °C en total. Mann-Kendall encuentra la tendencia significativa; la prueba "
                      "de mínimos cuadrados discrepa, por eso el veredicto es SIGNIFICANT y no fuerte.",
    },
    "svalbard-t2m": {
        "title_en": "Svalbard, Norway: air temperature 1981-2025",
        "title_es": "Svalbard, Noruega: temperatura del aire 1981-2025",
        "finding_en": "Air temperature rose about 0.70 °C per decade (Theil-Sen), 3.14 °C in total, "
                      "and both tests agree: SIGNIFICANT_STRONG.",
        "finding_es": "La temperatura del aire subió unos 0,70 °C por década (Theil-Sen), 3,14 °C en "
                      "total, y ambas pruebas coinciden: SIGNIFICANT_STRONG.",
    },
    "piura-prectotcorr": {
        "title_en": "Piura, Peru: precipitation 1981-2025",
        "title_es": "Piura, Perú: precipitación 1981-2025",
        "finding_en": "Precipitation shows a slight decrease of about 0.011 mm/day per decade "
                      "(Theil-Sen); the tests disagree and Mann-Kendall gives p = 0.075, so the "
                      "verdict is SUGGESTIVE, not proven.",
        "finding_es": "La precipitación muestra un descenso leve de unos 0,011 mm/día por década "
                      "(Theil-Sen); las pruebas discrepan y Mann-Kendall da p = 0,075, así que el "
                      "veredicto es SUGGESTIVE, no demostrado.",
    },
    "arctic-seaice": {
        "title_en": "Arctic sea ice extent, 1978-2026",
        "title_es": "Extensión del hielo marino del Ártico, 1978-2026",
        "finding_en": "Arctic sea ice extent fell about 0.50 million km² per decade "
                      "(Theil-Sen, 1978-2026), 2.38 million km² in total (-4.4%). Both tests agree: "
                      "SIGNIFICANT_STRONG. Two months (1987-12 and 1988-01) are missing in the source "
                      "and are reported as missing, not as zero.",
        "finding_es": "La extensión del hielo marino del Ártico bajó unos 0,50 millones de km² por "
                      "década (Theil-Sen, 1978-2026), 2,38 millones de km² en total (-4,4%). Ambas "
                      "pruebas coinciden: SIGNIFICANT_STRONG. Faltan dos meses en la fuente "
                      "(1987-12 y 1988-01) y se informan como faltantes, no como cero.",
    },
    "antarctic-seaice": {
        "title_en": "Antarctic sea ice extent, 1978-2026",
        "title_es": "Extensión del hielo marino del Antártico, 1978-2026",
        "finding_en": "Antarctic sea ice extent fell about 0.05 million km² per decade (Theil-Sen), "
                      "0.23 million km² in total (-0.4%). The trend is NOT_SIGNIFICANT: with "
                      "autocorrelation corrected, p = 0.63, so no change can be stated. It would take "
                      "about 133 years of data to detect a trend this small.",
        "finding_es": "La extensión del hielo marino del Antártico bajó unos 0,05 millones de km² por "
                      "década (Theil-Sen), 0,23 millones de km² en total (-0,4%). La tendencia es "
                      "NOT_SIGNIFICANT: corregida la autocorrelación, p = 0,63, así que no se puede "
                      "afirmar un cambio. Harian falta unos 133 años de datos para detectar una "
                      "tendencia tan pequeña.",
    },
    "amazonia-t2m": {
        "title_en": "Amazon basin: air temperature 1980-2026 (user CSV)",
        "title_es": "Cuenca amazónica: temperatura del aire 1980-2026 (CSV del usuario)",
        "finding_en": "Air temperature rose about 0.19 °C per decade (Theil-Sen), 0.87 °C in total, "
                      "from an uploaded NASA Giovanni export; both tests agree: SIGNIFICANT_STRONG.",
        "finding_es": "La temperatura del aire subió unos 0,19 °C por década (Theil-Sen), 0,87 °C en "
                      "total, a partir de una exportación de NASA Giovanni subida por el usuario; "
                      "ambas pruebas coinciden: SIGNIFICANT_STRONG.",
    },
    "amazonia-prectotcorr": {
        "title_en": "Amazon basin: precipitation 1980-2026 (user CSV)",
        "title_es": "Cuenca amazónica: precipitación 1980-2026 (CSV del usuario)",
        "finding_en": "Precipitation trend is about -0.083 mm/day per decade (Theil-Sen); with "
                      "p = 0.34 neither test rejects 'no trend': NOT_SIGNIFICANT.",
        "finding_es": "La tendencia de la precipitación es de unos -0,083 mm/día por década "
                      "(Theil-Sen); con p = 0,34 ninguna prueba rechaza 'sin tendencia': "
                      "NOT_SIGNIFICANT.",
    },
}


def main() -> int:
    index_path = os.path.join(CASES, "index.json")
    with open(index_path, encoding="utf-8") as fh:
        index = json.load(fh)
    updated = 0
    for item in index["cases"]:
        copy = COPY.get(item["id"])
        if not copy:
            continue
        item["title"] = {"en": copy["title_en"], "es": copy["title_es"]}
        item["finding"] = {"en": copy["finding_en"], "es": copy["finding_es"]}
        case_path = os.path.join(ROOT, item["paths"]["case"])
        with open(case_path, encoding="utf-8") as fh:
            case = json.load(fh)
        case["titles"] = {"en": copy["title_en"], "es": copy["title_es"]}
        case["story"] = {
            "en": [copy["finding_en"], "TODO_HUMANO: the narrative is the human's decision."],
            "es": [copy["finding_es"], "TODO_HUMANO: la narrativa la decide el humano."],
        }
        with open(case_path, "w", encoding="utf-8") as fh:
            json.dump(case, fh, ensure_ascii=False, indent=1)
        updated += 1
    with open(index_path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
    print(f"copy written for {updated} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
