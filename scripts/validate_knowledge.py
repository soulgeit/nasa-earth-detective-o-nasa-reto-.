#!/usr/bin/env python3
"""Validador del catálogo y corpus de conocimiento (Hermes 1 — Tarea C4)."""
import json
import os
import sys
import hashlib

CWD = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(CWD, "..")

errors = []
warnings = []

# === C4a: Catálogo de variables ===
print("=== Validando catálogo de variables ===")
cat_path = os.path.join(BASE, "data", "catalog", "variables.json")
if not os.path.exists(cat_path):
    errors.append(f"Catálogo no encontrado: {cat_path}")
    sys.exit(1)

with open(cat_path, "r", encoding="utf-8") as f:
    catalog = json.load(f)

required_fields = [
    "id", "names", "simple_definition", "unit", "ratio_scale",
    "sphere", "source", "what_up_means", "what_down_means",
    "typical_drivers", "caveats", "keywords", "verified"
]

vars_seen = set()
for v in catalog.get("variables", []):
    vid = v.get("id", "<sin_id>")
    vars_seen.add(vid)
    
    for field in required_fields:
        if field not in v:
            errors.append(f"  {vid} falta campo '{field}'")
    
    # Check bilingual names
    names = v.get("names", {})
    if "es" not in names or "en" not in names:
        errors.append(f"  {vid} nombres no bilingües")
    
    # Check definitions not empty
    sd = v.get("simple_definition", {})
    if not sd.get("es") or not sd.get("en"):
        errors.append(f"  {vid} definición vacía")
    
    # Check source has at least via and challenge_named_source
    src = v.get("source", {})
    if not src.get("via"):
        errors.append(f"  {vid} fuente sin 'via'")
    if not src.get("challenge_named_source"):
        errors.append(f"  {vid} fuente sin 'challenge_named_source'")
    
    # Check verified exists
    ver = v.get("verified")
    if not ver or not ver.get("by"):
        errors.append(f"  {vid} sin verificación")

print(f"  Variables en catálogo: {len(vars_seen)}")
print(f"  Campos requeridos: {len(required_fields)}")

# === C4b: Regiones ===
print("
=== Validando regiones ===")
regions_path = os.path.join(BASE, "data", "catalog", "regions.json")
if os.path.exists(regions_path):
    with open(regions_path, "r", encoding="utf-8") as f:
        regions_data = json.load(f)
    n_regions = len(regions_data.get("regions", []))
    print(f"  Regiones: {n_regions}")
    if n_regions < 20:
        warnings.append(f"  Pocas regiones (<20): {n_regions}")
else:
    warnings.append("  data/catalog/regions.json no encontrado (pendiente C2)")

# === C4c: Corpus docs.jsonl ===
print("
=== Validando corpus de conocimiento ===")
docs_path = os.path.join(BASE, "data", "knowledge", "docs.jsonl")
if os.path.exists(docs_path):
    doc_types = {}
    with open(docs_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                doc = json.loads(line)
                t = doc.get("type", "unknown")
                doc_types[t] = doc_types.get(t, 0) + 1
                
                # Check required fields
                for rf in ["id", "type", "title", "url", "text", "sha256"]:
                    if rf not in doc:
                        errors.append(f"  docs.jsonl#{i} falta '{rf}'")
            except json.JSONDecodeError:
                errors.append(f"  docs.jsonl#{i} JSON inválido")
    
    print(f"  Documentos: {sum(doc_types.values())}")
    for t, n in doc_types.items():
        print(f"    {t}: {n}")
else:
    warnings.append("  data/knowledge/docs.jsonl no encontrado (pendiente C3)")

# === C4d: URLs de documentos ===
print("
=== Validando URLs de documentos ===")
if os.path.exists(docs_path):
    import urllib.request
    checked = set()
    broken = []
    with open(docs_path, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            url = doc.get("url", "")
            if not url or "http" not in url:
                continue
            # Only check docs with text (not variable_cards/glossary)
            if doc.get("type") in ("glossary", "variable_card", "method_note"):
                continue
            if url in checked:
                continue
            checked.add(url)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "validator/1.0"})
                resp = urllib.request.urlopen(req, timeout=10)
                if resp.status != 200 and resp.status != 301 and resp.status != 302:
                    broken.append((url, resp.status))
            except Exception as e:
                broken.append((url, str(e)[:80]))
    
    if broken:
        print(f"  URLs rotas (muestra):")
        for u, s in broken[:5]:
            print(f"    {u} -> {s}")
    else:
        print("  Todas las URLs verificadas ✓")

# === C4e: Duplicados en corpus ===
print("
=== Buscando duplicados en corpus ===")
if os.path.exists(docs_path):
    ids_seen = set()
    dupes = []
    with open(docs_path, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            did = doc.get("id", "")
            if did in ids_seen:
                dupes.append(did)
            ids_seen.add(did)
    if dupes:
        warnings.append(f"  Duplicados en corpus: {set(dupes)}")
    else:
        print("  Sin duplicados ✓")

# === RESULTADO FINAL ===
print("
" + "=" * 60)
if errors:
    print(f"ERRORES ({len(errors)}):")
    for e in errors:
        print(f"  ✗ {e}")
else:
    print("✓ Sin errores de validación")

if warnings:
    print(f"
ADVERTENCIAS ({len(warnings)}):")
    for w in warnings:
        print(f"  ⚠ {w}")

exit_code = 1 if errors else 0
print(f"
Resultado: {'FALLÓ' if exit_code else 'APROBADO'} (código {exit_code})")
sys.exit(exit_code)
