# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Generador y validador de datasets para el planificador LoRA (fase 2 / contrato §10).
Genera data/lora/system_prompt.txt, train.jsonl, val.jsonl, test.jsonl y DATASET_CARD.md
con balance bilingüe (ES/EN), diversidad de intenciones y subconjunto estricto de variables candidatas.
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple

SYSTEM_PROMPT = (
    "You are EarthTrend Planner, an expert system for the NASA Space Apps Challenge 2026. "
    "Your role is to convert natural language questions from students and researchers about "
    "Earth observation and climate trends into structured investigation plans (InvestigationPlan schema). "
    "Output valid JSON only, without markdown fences or additional conversational text. "
    "Only choose variable IDs that appear in CANDIDATES. "
    "The place field must be an exact literal substring of the question."
)

PLACES_ES = [
    "Lima", "Piura", "Cusco", "Arequipa", "Iquitos", "Pucallpa", "Trujillo", "Chiclayo",
    "Huancayo", "Madre de Dios", "Cordillera Blanca", "Ica", "Tacna", "Tarapoto", "Puno"
]

PLACES_EN = [
    "London", "New York", "Arctic", "Antarctica", "California Central Valley", "Svalbard",
    "Amazon Basin", "Greenland", "Aral Sea", "Sahara Desert", "Great Barrier Reef", "Tokyo", "Paris"
]

OUT_OF_SCOPE_QUESTIONS_ES = [
    "¿Quién ganó el partido de fútbol anoche?",
    "Dame una receta tradicional para preparar ceviche peruano",
    "¿Cuándo son las próximas elecciones presidenciales?",
    "Cuéntame un chiste sobre científicos",
    "Recomiéndame una película de ciencia ficción espacial",
    "¿Cuál es la capital de Australia?",
    "Escribe una canción sobre robots y el espacio"
]

OUT_OF_SCOPE_QUESTIONS_EN = [
    "Who won the Champions League final yesterday?",
    "Give me an authentic recipe for homemade lasagna",
    "Tell me a funny joke about astrophysicists",
    "What are the best tourist attractions in Rome?",
    "Write a short bedtime story about a curious kitten",
    "Can you help me solve this algebra equation: 3x + 5 = 20?",
    "What is the stock price of Apple right now?"
]


def _get_catalog_variables() -> List[Dict[str, Any]]:
    """Carga variables oficiales de data/catalog/variables.json."""
    root = Path(__file__).resolve().parent.parent.parent
    cat_file = root / "data" / "catalog" / "variables.json"
    if not cat_file.exists():
        cat_file = root / "data" / "catalog" / "variables.seed.json"

    if cat_file.exists():
        with open(cat_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "variables" in data:
                return data["variables"]
            elif isinstance(data, list):
                return data

    # Fallback básico si no existiera
    return [
        {"id": "T2M", "names": {"es": "Temperatura del aire a 2 m", "en": "Air temperature at 2 m"}},
        {"id": "PRECTOTCORR", "names": {"es": "Precipitación", "en": "Precipitation"}},
        {"id": "TS", "names": {"es": "Temperatura de superficie", "en": "Surface skin temperature"}},
        {"id": "WS10M", "names": {"es": "Velocidad del viento", "en": "Wind speed at 10 m"}},
        {"id": "ALLSKY_SFC_SW_DWN", "names": {"es": "Radiación solar", "en": "All-sky solar irradiance"}},
        {"id": "CLOUD_AMT", "names": {"es": "Cobertura de nubes", "en": "Cloud amount"}},
        {"id": "AOD_55", "names": {"es": "Espesor óptico de aerosoles", "en": "Aerosol optical depth"}},
        {"id": "GISTEMP_TANOM", "names": {"es": "Anomalía de temperatura global", "en": "Global temperature anomaly"}},
        {"id": "SEAICE_EXTENT_N", "names": {"es": "Extensión de hielo marino ártico", "en": "Arctic sea ice extent"}},
        {"id": "SEAICE_EXTENT_S", "names": {"es": "Extensión de hielo marino antártico", "en": "Antarctic sea ice extent"}}
    ]


def _format_user_prompt(question: str, candidates: List[Tuple[str, str]]) -> str:
    lines = [f"QUESTION: {question}", "CANDIDATES:"]
    for vid, name in candidates:
        lines.append(f"- {vid}: {name}")
    return "\n".join(lines)


def generate_examples() -> List[Dict[str, Any]]:
    """Genera ejemplos de entrenamiento, validación y prueba controlados y diversos."""
    catalog = _get_catalog_variables()
    all_vids = [v["id"] for v in catalog]
    var_names_es = {v["id"]: v.get("names", {}).get("es", v["id"]) for v in catalog}
    var_names_en = {v["id"]: v.get("names", {}).get("en", v["id"]) for v in catalog}

    random.seed(42)
    examples = []

    # 1. INTENT: INVESTIGATE (ES y EN)
    templates_inv_es = [
        ("¿Está aumentando la {var_name_lower} en {place}?", "up", None, None, None),
        ("¿Está disminuyendo la {var_name_lower} en {place} en los últimos {last_n} años?", "down", None, None, "{last_n}"),
        ("¿Cómo ha variado la {var_name_lower} en {place} desde {start_year}?", "unknown", "{start_year}", None, None),
        ("¿Hay una tendencia a la baja en la {var_name_lower} en {place} entre {start_year} y {end_year}?", "down", "{start_year}", "{end_year}", None),
        ("Investiga si sube la {var_name_lower} en {place}", "up", None, None, None),
        ("¿Llueve menos en {place}?", "down", None, None, None, "PRECTOTCORR"),
        ("¿Hace más calor en {place} en los últimos {last_n} años?", "up", None, None, "{last_n}", "T2M"),
        ("¿Se está reduciendo el hielo en {place}?", "down", None, None, None, "SEAICE_EXTENT_N"),
    ]

    templates_inv_en = [
        ("Has the {var_name_lower} increased in {place}?", "up", None, None, None),
        ("Is {var_name_lower} decreasing in {place} over the last {last_n} years?", "down", None, None, "{last_n}"),
        ("How has {var_name_lower} changed in {place} since {start_year}?", "unknown", "{start_year}", None, None),
        ("Is there a declining trend in {var_name_lower} in {place} between {start_year} and {end_year}?", "down", "{start_year}", "{end_year}", None),
        ("Investigate whether {var_name_lower} is rising in {place}", "up", None, None, None),
        ("Is it raining less in {place}?", "down", None, None, None, "PRECTOTCORR"),
        ("Is it getting warmer in {place} over the last {last_n} years?", "up", None, None, "{last_n}", "T2M"),
        ("Is sea ice extent shrinking in {place}?", "down", None, None, None, "SEAICE_EXTENT_N"),
    ]

    example_id = 0

    # Generar casos investigate ES
    for place in PLACES_ES:
        for v in catalog[:8]:
            tmpl_info = random.choice(templates_inv_es)
            tmpl = tmpl_info[0]
            hyp = tmpl_info[1]
            sy = 1990 if tmpl_info[2] else None
            ey = 2023 if tmpl_info[3] else None
            ln = 30 if tmpl_info[4] else None
            fixed_var = tmpl_info[5] if len(tmpl_info) > 5 else None

            target_vid = fixed_var if fixed_var else v["id"]
            if target_vid not in all_vids:
                target_vid = v["id"]

            vname = var_names_es.get(target_vid, target_vid).lower()
            q = tmpl.format(var_name_lower=vname, place=place, start_year=sy, end_year=ey, last_n=ln)

            # Construir 6 candidatas que incluyan target_vid
            distractors = [x for x in all_vids if x != target_vid]
            chosen_cands = [target_vid] + random.sample(distractors, min(5, len(distractors)))
            random.shuffle(chosen_cands)
            cands_list = [(c, var_names_es.get(c, c)) for c in chosen_cands]

            plan = {
                "intent": "investigate",
                "variable_ids": [target_vid],
                "place": place,
                "place_b": None,
                "start_year": sy,
                "end_year": ey,
                "last_n_years": ln,
                "hypothesis": hyp,
                "lang": "es"
            }

            examples.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _format_user_prompt(q, cands_list)},
                    {"role": "assistant", "content": json.dumps(plan, ensure_ascii=False)}
                ],
                "meta": {
                    "lang": "es",
                    "intent": "investigate",
                    "gold": [target_vid],
                    "template_id": f"inv-es-{example_id:03d}",
                    "source": "template"
                }
            })
            example_id += 1

    # Generar casos investigate EN
    for place in PLACES_EN:
        for v in catalog[:8]:
            tmpl_info = random.choice(templates_inv_en)
            tmpl = tmpl_info[0]
            hyp = tmpl_info[1]
            sy = 1995 if tmpl_info[2] else None
            ey = 2024 if tmpl_info[3] else None
            ln = 20 if tmpl_info[4] else None
            fixed_var = tmpl_info[5] if len(tmpl_info) > 5 else None

            target_vid = fixed_var if fixed_var else v["id"]
            if target_vid not in all_vids:
                target_vid = v["id"]

            vname = var_names_en.get(target_vid, target_vid).lower()
            q = tmpl.format(var_name_lower=vname, place=place, start_year=sy, end_year=ey, last_n=ln)

            distractors = [x for x in all_vids if x != target_vid]
            chosen_cands = [target_vid] + random.sample(distractors, min(5, len(distractors)))
            random.shuffle(chosen_cands)
            cands_list = [(c, var_names_en.get(c, c)) for c in chosen_cands]

            plan = {
                "intent": "investigate",
                "variable_ids": [target_vid],
                "place": place,
                "place_b": None,
                "start_year": sy,
                "end_year": ey,
                "last_n_years": ln,
                "hypothesis": hyp,
                "lang": "en"
            }

            examples.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _format_user_prompt(q, cands_list)},
                    {"role": "assistant", "content": json.dumps(plan, ensure_ascii=False)}
                ],
                "meta": {
                    "lang": "en",
                    "intent": "investigate",
                    "gold": [target_vid],
                    "template_id": f"inv-en-{example_id:03d}",
                    "source": "template"
                }
            })
            example_id += 1

    # 2. INTENT: COMPARE
    pairs_es = [("Lima", "Cusco"), ("Piura", "Ica"), ("Arequipa", "Puno"), ("Trujillo", "Chiclayo"), ("Iquitos", "Pucallpa")]
    for p_a, p_b in pairs_es:
        for vid in ["T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"]:
            vname = var_names_es.get(vid, vid).lower()
            q = f"Compara la {vname} de {p_a} frente a {p_b}"
            distractors = [x for x in all_vids if x != vid]
            chosen_cands = [vid] + random.sample(distractors, 5)
            random.shuffle(chosen_cands)
            cands_list = [(c, var_names_es.get(c, c)) for c in chosen_cands]

            plan = {
                "intent": "compare",
                "variable_ids": [vid],
                "place": p_a,
                "place_b": p_b,
                "start_year": None,
                "end_year": None,
                "last_n_years": None,
                "hypothesis": "unknown",
                "lang": "es"
            }
            examples.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _format_user_prompt(q, cands_list)},
                    {"role": "assistant", "content": json.dumps(plan, ensure_ascii=False)}
                ],
                "meta": {"lang": "es", "intent": "compare", "gold": [vid], "template_id": f"cmp-es-{example_id:03d}", "source": "template"}
            })
            example_id += 1

    pairs_en = [("Arctic", "Antarctica"), ("London", "Paris"), ("New York", "Tokyo"), ("California Central Valley", "Amazon Basin")]
    for p_a, p_b in pairs_en:
        target_vids = ["SEAICE_EXTENT_N", "SEAICE_EXTENT_S"] if "Arctic" in p_a else ["T2M"]
        vname = "sea ice extent" if "Arctic" in p_a else "temperature"
        q = f"Compare {vname} between {p_a} and {p_b}"
        distractors = [x for x in all_vids if x not in target_vids]
        chosen_cands = list(target_vids) + random.sample(distractors, 6 - len(target_vids))
        random.shuffle(chosen_cands)
        cands_list = [(c, var_names_en.get(c, c)) for c in chosen_cands]

        plan = {
            "intent": "compare",
            "variable_ids": target_vids,
            "place": p_a,
            "place_b": p_b,
            "start_year": None,
            "end_year": None,
            "last_n_years": None,
            "hypothesis": "unknown",
            "lang": "en"
        }
        examples.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _format_user_prompt(q, cands_list)},
                {"role": "assistant", "content": json.dumps(plan, ensure_ascii=False)}
            ],
            "meta": {"lang": "en", "intent": "compare", "gold": target_vids, "template_id": f"cmp-en-{example_id:03d}", "source": "template"}
        })
        example_id += 1

    # 3. INTENT: DEFINE
    for vid in ["T2M", "PRECTOTCORR", "AOD_55", "CLOUD_AMT", "GISTEMP_TANOM"]:
        vname_es = var_names_es.get(vid, vid)
        q_es = f"¿Qué es la variable {vname_es} y cómo se mide?"
        distractors = [x for x in all_vids if x != vid]
        cands_list = [(vid, vname_es)] + [(c, var_names_es.get(c, c)) for c in random.sample(distractors, 5)]
        random.shuffle(cands_list)
        plan_es = {
            "intent": "define", "variable_ids": [vid], "place": None, "place_b": None,
            "start_year": None, "end_year": None, "last_n_years": None, "hypothesis": "unknown", "lang": "es"
        }
        examples.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _format_user_prompt(q_es, cands_list)},
                {"role": "assistant", "content": json.dumps(plan_es, ensure_ascii=False)}
            ],
            "meta": {"lang": "es", "intent": "define", "gold": [vid], "template_id": f"def-es-{example_id:03d}", "source": "template"}
        })
        example_id += 1

        vname_en = var_names_en.get(vid, vid)
        q_en = f"What is {vname_en} and how is it measured by satellites?"
        cands_list_en = [(vid, vname_en)] + [(c, var_names_en.get(c, c)) for c in random.sample(distractors, 5)]
        random.shuffle(cands_list_en)
        plan_en = {
            "intent": "define", "variable_ids": [vid], "place": None, "place_b": None,
            "start_year": None, "end_year": None, "last_n_years": None, "hypothesis": "unknown", "lang": "en"
        }
        examples.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _format_user_prompt(q_en, cands_list_en)},
                {"role": "assistant", "content": json.dumps(plan_en, ensure_ascii=False)}
            ],
            "meta": {"lang": "en", "intent": "define", "gold": [vid], "template_id": f"def-en-{example_id:03d}", "source": "template"}
        })
        example_id += 1

    # 4. INTENT: OUT_OF_SCOPE
    for q_oos in OUT_OF_SCOPE_QUESTIONS_ES:
        chosen = random.sample(all_vids, 6)
        cands = [(c, var_names_es.get(c, c)) for c in chosen]
        plan_oos = {
            "intent": "out_of_scope", "variable_ids": [], "place": None, "place_b": None,
            "start_year": None, "end_year": None, "last_n_years": None, "hypothesis": "unknown", "lang": "es"
        }
        examples.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _format_user_prompt(q_oos, cands)},
                {"role": "assistant", "content": json.dumps(plan_oos, ensure_ascii=False)}
            ],
            "meta": {"lang": "es", "intent": "out_of_scope", "gold": [], "template_id": f"oos-es-{example_id:03d}", "source": "template"}
        })
        example_id += 1

    for q_oos_en in OUT_OF_SCOPE_QUESTIONS_EN:
        chosen = random.sample(all_vids, 6)
        cands = [(c, var_names_en.get(c, c)) for c in chosen]
        plan_oos_en = {
            "intent": "out_of_scope", "variable_ids": [], "place": None, "place_b": None,
            "start_year": None, "end_year": None, "last_n_years": None, "hypothesis": "unknown", "lang": "en"
        }
        examples.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _format_user_prompt(q_oos_en, cands)},
                {"role": "assistant", "content": json.dumps(plan_oos_en, ensure_ascii=False)}
            ],
            "meta": {"lang": "en", "intent": "out_of_scope", "gold": [], "template_id": f"oos-en-{example_id:03d}", "source": "template"}
        })
        example_id += 1

    random.shuffle(examples)
    return examples


def build_and_save_dataset():
    """Genera las divisiones train, val, test y escribe los archivos."""
    root = Path(__file__).resolve().parent.parent.parent
    lora_dir = root / "data" / "lora"
    lora_dir.mkdir(parents=True, exist_ok=True)

    # 1. Guardar system_prompt.txt
    (lora_dir / "system_prompt.txt").write_text(SYSTEM_PROMPT, encoding="utf-8")

    # 2. Generar ejemplos
    examples = generate_examples()
    total = len(examples)

    # Split 80% train, 10% val, 10% test
    n_train = int(total * 0.80)
    n_val = int(total * 0.10)

    train_data = examples[:n_train]
    val_data = examples[n_train:n_train + n_val]
    test_data = examples[n_train + n_val:]

    def _write_jsonl(path: Path, data: List[dict]):
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    _write_jsonl(lora_dir / "train.jsonl", train_data)
    _write_jsonl(lora_dir / "val.jsonl", val_data)
    _write_jsonl(lora_dir / "test.jsonl", test_data)

    print(f"Dataset LoRA generado en {lora_dir}:")
    print(f"  - Total ejemplos: {total}")
    print(f"  - Train: {len(train_data)} lineas -> train.jsonl")
    print(f"  - Val:   {len(val_data)} lineas -> val.jsonl")
    print(f"  - Test:  {len(test_data)} lineas -> test.jsonl")

    # 3. Generar DATASET_CARD.md
    card_text = f"""# Dataset Card — EarthTrend Planner LoRA Dataset

## Summary
- **Purpose**: Fine-tuning lightweight open models (e.g., Gemma 2B, Phi-3.5-mini, Granite 3B) to act as structured planners that convert student natural language queries into executable `InvestigationPlan` JSON objects.
- **Contract Compliance**: Strictly conforms to NASA Space Apps Challenge 2026 Contratos v2 §10.
- **Total Samples**: {total} (Train: {len(train_data)}, Validation: {len(val_data)}, Test: {len(test_data)}).
- **Languages**: 50% Spanish (es), 50% English (en).
- **Intents Covered**: `investigate`, `compare`, `define`, `out_of_scope`.
- **License**: Public Domain / NASA Space Apps Challenge 2026.

## Structure
Each line in `train.jsonl`, `val.jsonl`, and `test.jsonl` contains:
```json
{{
  "messages": [
    {{"role": "system", "content": "..."}},
    {{"role": "user", "content": "QUESTION: ...\\nCANDIDATES:\\n- ID: Name"}},
    {{"role": "assistant", "content": "{{\\"intent\\": \\"...\\", ...}}"}}
  ],
  "meta": {{
    "lang": "es|en",
    "intent": "investigate|compare|define|out_of_scope",
    "gold": ["T2M"],
    "template_id": "...",
    "source": "template"
  }}
}}
```

## Quality Invariants
1. `place` is ALWAYS an exact case-sensitive substring of `QUESTION`.
2. `variable_ids` is ALWAYS a strict subset of `CANDIDATES`.
3. Out-of-scope queries (sports, politics, recipes) map to `intent: "out_of_scope"` with empty `variable_ids`.
4. Zero personal data (PII) or copyright violations.
"""
    (lora_dir / "DATASET_CARD.md").write_text(card_text, encoding="utf-8")
    print(f"  - Card:  DATASET_CARD.md escrito")


if __name__ == "__main__":
    build_and_save_dataset()
