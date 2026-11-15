# SI-assisted: hermes-2 (Claude Opus 5.5)
"""Comprueba que los textos espanoles de los casos llevan sus tildes (Ronda 5).

Regla: en `data/cases/index.json` y en cada `case.json`, los textos en espanol no
pueden contener las palabras de la lista sin tilde; y los textos en INGLES no
deben llevar tildes espanolas (el ingles escribe "Peru", no "Peru" con tilde).

Uso: python -X utf8 -I scripts/check_case_accents.py
Sale con codigo 1 si encuentra alguno.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "data", "cases")

# Palabras que en espanol llevan tilde (o enie) y que aparecieron sin ella.
UNACCENTED = [
    "Peru", "precipitacion", "Extension", "extension", "Artico", "Antartico",
    "amazonica", "subio", "bajo", "decada", "minimos", "exportacion",
    "autocorrelacion", "asi", "anos", "km2", "mm/dia", "pequena",
]
ACCENTED = re.compile(r"[áéíóúñÁÉÍÓÚÑ]")


def spanish_texts(case: dict) -> list[str]:
    out = []
    for key in ("title", "finding"):
        if isinstance(case.get(key), dict):
            out.append(case[key].get("es") or "")
    for key in ("titles", "story", "names", "variable_name"):
        value = case.get(key)
        if isinstance(value, dict):
            es = value.get("es")
            if isinstance(es, str):
                out.append(es)
            elif isinstance(es, list):
                out.extend(str(v) for v in es)
    return [t for t in out if t]


def english_texts(case: dict) -> list[str]:
    out = []
    for key in ("title", "finding"):
        if isinstance(case.get(key), dict):
            out.append(case[key].get("en") or "")
    for key in ("titles", "story", "names", "variable_name"):
        value = case.get(key)
        if isinstance(value, dict):
            en = value.get("en")
            if isinstance(en, str):
                out.append(en)
            elif isinstance(en, list):
                out.extend(str(v) for v in en)
    return [t for t in out if t]


def scan(path: str) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    cases = doc["cases"] if "cases" in doc else [doc]
    problems = []
    for case in cases:
        cid = case.get("id", os.path.basename(os.path.dirname(path)))
        for text in spanish_texts(case):
            for word in UNACCENTED:
                if re.search(rf"\b{re.escape(word)}\b", text):
                    problems.append(f"{cid}: '{word}' sin tilde en texto espanol")
        for text in english_texts(case):
            if ACCENTED.search(text):
                problems.append(f"{cid}: tilde espanola en texto ingles: {text[:60]!r}")
    return problems


def main() -> int:
    paths = [os.path.join(CASES, "index.json")]
    for name in sorted(os.listdir(CASES)):
        p = os.path.join(CASES, name, "case.json")
        if os.path.exists(p):
            paths.append(p)
    total = 0
    for path in paths:
        problems = scan(path)
        total += len(problems)
        for p in problems:
            print("FALLA", p)
    print(f"{total} problemas en {len(paths)} archivos")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
