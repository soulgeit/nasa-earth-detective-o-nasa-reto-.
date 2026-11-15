# SI-assisted: rag-datos (Huiracocha IA Ronda 7)
"""
Pruebas de integridad y veracidad para los hechos climáticos de las cinco ciudades.
Verifica que cada cifra, pendiente, valor p, periodo y observación del texto
esté estrictamente respaldada en el JSON congelado generado por el motor de la app.
Falla si un número del texto no está en el JSON congelado (§5).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CITIES_DIR = ROOT / "data" / "cities"
FACTS_DIR = ROOT / "data" / "knowledge" / "facts"

CITIES = ["lima", "huancayo", "andahuaylas", "ica", "ayacucho"]

# Expresión regular para extraer números: detecta números con signo solo si van precedidos de espacio o delimitador
NUMBER_TOKEN_RE = re.compile(r"(?:(?<=[\s(\[,:])|^)[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|\b\d+(?:\.\d+)?\b")


def _extract_numbers_from_text(text: str) -> list[str]:
    """Extrae todos los tokens numéricos del texto."""
    raw = NUMBER_TOKEN_RE.findall(text)
    cleaned = []
    for num in raw:
        clean = num.lstrip("+")
        if clean:
            cleaned.append(clean)
    return cleaned


def _collect_numbers_from_json(obj: Any) -> set[str]:
    """Extrae recursivamente todas las representaciones numéricas de un JSON."""
    found: set[str] = set()

    def recurse(item: Any):
        if isinstance(item, (int, float)):
            found.add(str(item))
            if isinstance(item, float):
                found.add(f"{item:.1f}")
                found.add(f"{item:.2f}")
                found.add(f"{item:.3f}")
                found.add(f"{item:.4f}")
                found.add(f"{item:.2e}")
                found.add(f"{item:+.3f}".lstrip("+"))
                found.add(f"{item:+.4f}".lstrip("+"))
        elif isinstance(item, str):
            for m in NUMBER_TOKEN_RE.findall(item):
                clean = m.lstrip("+")
                if clean:
                    found.add(clean)
        elif isinstance(item, dict):
            for k, v in item.items():
                for m in NUMBER_TOKEN_RE.findall(str(k)):
                    clean = m.lstrip("+")
                    if clean:
                        found.add(clean)
                recurse(v)
        elif isinstance(item, list):
            for v in item:
                recurse(v)

    recurse(obj)
    # 95% es el nivel de confianza estándar del intervalo ci95 declarado en el esquema
    found.add("95")
    return found


def _verify_numbers_in_frozen(text: str, frozen_json: dict[str, Any]) -> list[str]:
    """Devuelve la lista de números del texto que no se encontraron en el JSON congelado."""
    text_numbers = _extract_numbers_from_text(text)
    json_numbers = _collect_numbers_from_json(frozen_json)

    missing: list[str] = []
    for num_str in text_numbers:
        # 1. Comprobación exacta
        if num_str in json_numbers:
            continue

        # 2. Comprobación como float con tolerancia numérica
        try:
            val = float(num_str)
            match = False
            for j_str in json_numbers:
                try:
                    j_val = float(j_str)
                    if abs(val - j_val) < 1e-4:
                        match = True
                        break
                except ValueError:
                    continue
            if match:
                continue
        except ValueError:
            pass

        missing.append(num_str)

    return missing


def test_every_city_has_frozen_data_and_facts_files():
    """Comprueba que existen los directorios y archivos de las 5 ciudades."""
    assert CITIES_DIR.is_dir(), f"Directorio {CITIES_DIR} no existe"
    assert FACTS_DIR.is_dir(), f"Directorio {FACTS_DIR} no existe"

    for city in CITIES:
        facts_file = FACTS_DIR / f"{city}.jsonl"
        city_dir = CITIES_DIR / city
        assert facts_file.is_file(), f"Falta archivo de hechos: {facts_file}"
        assert city_dir.is_dir(), f"Falta directorio congelado: {city_dir}"
        frozen_files = list(city_dir.glob("*.analysis.json"))
        assert len(frozen_files) >= 15, f"{city} tiene solo {len(frozen_files)} variables congeladas"


def test_fact_numbers_strictly_match_frozen_analysis_json():
    """
    Regla 4 de §5: una prueba que falle si un número del texto no está en el JSON congelado.
    Recorre cada documento de hechos y verifica que todas sus cifras provengan del JSON.
    """
    errors: list[str] = []

    for city in CITIES:
        facts_file = FACTS_DIR / f"{city}.jsonl"
        if not facts_file.exists():
            continue

        city_dir = CITIES_DIR / city

        # Cargar todos los JSON congelados de la ciudad para el resumen
        all_city_jsons = []
        for p in city_dir.glob("*.analysis.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    all_city_jsons.append(json.load(f))
            except Exception:
                pass

        with open(facts_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                doc = json.loads(line)
                doc_id = doc.get("id", "")
                text = doc.get("text", "")
                variables = doc.get("variables", [])

                if "summary" in doc_id:
                    # Para el documento de resumen, las cifras deben estar en el conjunto de JSONs
                    combined_numbers: set[str] = set()
                    for cj in all_city_jsons:
                        combined_numbers |= _collect_numbers_from_json(cj)
                    # Añadir conteos globales de variables
                    combined_numbers.add(str(len(all_city_jsons)))

                    text_numbers = _extract_numbers_from_text(text)
                    for n in text_numbers:
                        if n not in combined_numbers:
                            try:
                                val = float(n)
                                if not any(abs(val - float(cj_n)) < 1e-4 for cj_n in combined_numbers if re.match(r"^[-+]?\d+(?:\.\d+)?$", cj_n)):
                                    errors.append(f"{city}:{line_no} [{doc_id}] resumen contiene número no respaldado: {n}")
                            except ValueError:
                                errors.append(f"{city}:{line_no} [{doc_id}] resumen contiene número no respaldado: {n}")
                else:
                    # Hecho individual de variable
                    var_id = variables[0] if variables else None
                    if not var_id:
                        errors.append(f"{city}:{line_no} [{doc_id}] sin variable asociada")
                        continue

                    json_path = city_dir / f"{var_id}.analysis.json"
                    if not json_path.exists():
                        errors.append(f"{city}:{line_no} [{doc_id}] falta JSON congelado: {json_path}")
                        continue

                    with open(json_path, "r", encoding="utf-8") as jf:
                        frozen_data = json.load(jf)

                    missing = _verify_numbers_in_frozen(text, frozen_data)
                    if missing:
                        errors.append(
                            f"{city}:{line_no} [{doc_id}] números en texto no hallados en {var_id}.analysis.json: {missing}"
                        )

    assert not errors, f"Se encontraron discrepancias numéricas:\n" + "\n".join(errors)


def test_verification_fails_if_number_is_invented():
    """Demuestra que la prueba detecta números inventados o manipulados."""
    dummy_frozen = {
        "period": {"start": "1981-01", "end": "2025-12", "years": 45.0, "n_obs": 540},
        "trend": {"sen_slope_per_decade": 0.1585, "sen_ci95_per_decade": [0.0313, 0.2808], "total_change": 0.7131},
        "tests": {"mann_kendall": {"tau": 0.23, "z": 7.9, "p_value_autocorr": 3.87e-05}},
        "significance": {"level": "p<0.05", "verdict_code": "SIGNIFICANT"},
        "answers": {"how_much": {"es": "Tasa estimada de +0.159 °C/década, con un cambio acumulado de +0.713 °C."}},
    }

    tampered_text = (
        "En Lima, el análisis arrojó una tasa de +0.159 °C/década, con un cambio de +0.713 °C, "
        "pero alguien inventó que la temperatura máxima subió 999.888 grados en 540 observaciones."
    )

    missing = _verify_numbers_in_frozen(tampered_text, dummy_frozen)
    assert "999.888" in missing, "El verificador debió capturar el número inventado 999.888"
