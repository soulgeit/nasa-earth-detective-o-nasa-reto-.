"""
SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
Validador de integridad para el corpus de conocimiento data/knowledge/docs.jsonl.
Cumple con las reglas de aceptación de CONTRATOS.md §9.
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_FILE = os.path.join(BASE_DIR, "data", "knowledge", "docs.jsonl")

REQUIRED_FIELDS = [
    "id", "type", "title", "url", "publisher", "date",
    "lang", "text", "variables", "biomes", "license",
    "fetched_at", "sha256"
]

VALID_TYPES = [
    "variable_card", "biome_profile", "region_note",
    "nasa_article", "paper_abstract", "method_note", "glossary"
]

def validate():
    if not os.path.exists(DOCS_FILE):
        print(f"FAIL: Corpus file {DOCS_FILE} does not exist.")
        sys.exit(1)

    seen_ids = set()
    errors = []
    types_count = {}
    langs_count = {}

    with open(DOCS_FILE, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except Exception as e:
                errors.append(f"Line {line_num}: invalid JSON -> {e}")
                continue

            doc_id = doc.get("id")
            if not doc_id:
                errors.append(f"Line {line_num}: missing 'id'")
            elif doc_id in seen_ids:
                errors.append(f"Line {line_num}: duplicate id '{doc_id}'")
            else:
                seen_ids.add(doc_id)

            for req in REQUIRED_FIELDS:
                if req not in doc:
                    errors.append(f"Doc '{doc_id}': missing required field '{req}'")

            dtype = doc.get("type")
            if dtype not in VALID_TYPES:
                errors.append(f"Doc '{doc_id}': invalid type '{dtype}'")
            else:
                types_count[dtype] = types_count.get(dtype, 0) + 1

            lang = doc.get("lang")
            if lang not in ["es", "en"]:
                errors.append(f"Doc '{doc_id}': invalid lang '{lang}'")
            else:
                langs_count[lang] = langs_count.get(lang, 0) + 1

            text = doc.get("text", "")
            if len(text) < 100 and dtype != "glossary":
                errors.append(f"Doc '{doc_id}': text too short ({len(text)} chars)")
            if len(text) > 2000:
                errors.append(f"Doc '{doc_id}': text too long ({len(text)} chars)")

            sha = doc.get("sha256", "")
            if len(sha) != 64:
                errors.append(f"Doc '{doc_id}': invalid sha256 hash length ({len(sha)})")

    if errors:
        print(f"FAILED with {len(errors)} errors:")
        for err in errors[:15]:
            print(f"  - {err}")
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more errors.")
        sys.exit(1)

    print("VALIDATION SUCCESS: data/knowledge/docs.jsonl is 100% compliant.")
    print(f"Total documents: {len(seen_ids)}")
    print("Breakdown by type:")
    for t, c in sorted(types_count.items()):
        print(f"  - {t}: {c}")
    print("Breakdown by language:")
    for l, c in sorted(langs_count.items()):
        print(f"  - {l}: {c}")
    sys.exit(0)

if __name__ == "__main__":
    validate()
