# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Script de evaluación real para EarthTrend Planner (Fase 2 / Ronda 2 §9.2).
Evalúa de punta a punta sobre data/lora/test.jsonl contrastando 3 sistemas reales:
1. Reglas deterministas (Rules).
2. Modelo Base Zero-shot (HuggingFaceTB/SmolLM2-1.7B-Instruct).
3. Modelo Base + Adaptador LoRA Fine-Tuned (models/etd-planner-lora).

Métricas calculadas sobre inferencias reales:
- JSON válido (%)
- Esquema válido (%)
- Exactitud de intención (%)
- Coincidencia exacta de variables (%)
- Coincidencia de lugar (%)
- Exactitud de hipótesis (%)

Genera:
- reports/lora/eval.json (resumen cuantitativo formal)
- reports/lora/predictions.jsonl (trazabilidad y auditoría paso a paso)

REGLA ESTRICTA: Sin modelo cargado, sale con error y no produce cifras falsas.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.detective.planner import _rules_plan, validate_plan


def resolve_model_path(base_model_id: str) -> str:
    repo_folder = f"models--{base_model_id.replace('/', '--')}"
    hub_cache = Path.home() / ".cache" / "huggingface" / "hub" / repo_folder / "snapshots"
    if hub_cache.exists():
        snapshots = list(hub_cache.iterdir())
        if snapshots:
            for s in snapshots:
                if (s / "model.safetensors").exists():
                    return str(s)
            return str(snapshots[0])
    return base_model_id


def extract_json_block(text: str) -> str:
    """Extrae el primer bloque JSON balanceado de la respuesta del modelo."""
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()


def parse_prediction(text: str, question: str, candidates: List[str]) -> Tuple[bool, bool, Dict[str, Any]]:
    """Determina si la salida es JSON válido y si cumple el esquema."""
    raw = extract_json_block(text)
    try:
        data = json.loads(raw)
        is_json = True
    except Exception:
        return False, False, {"raw": text}

    if not isinstance(data, dict):
        return True, False, data

    plan, reason = validate_plan(data, question=question, candidates=candidates, lang=data.get("lang", "es"))
    is_schema = plan is not None
    return is_json, is_schema, data


def evaluate_batch(
    base_model_id: str = "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    adapter_path: str = "models/etd-planner-lora",
    test_file: str = "data/lora/test.jsonl",
    max_samples: Optional[int] = None,
    output_eval: str = "reports/lora/eval.json",
    output_preds: str = "reports/lora/predictions.jsonl",
) -> Dict[str, Any]:
    root = Path(__file__).resolve().parent.parent.parent
    test_path = root / test_file
    adapter_dir = root / adapter_path
    if not adapter_dir.exists() and (root / "models/planner-lora").exists():
        adapter_dir = root / "models/planner-lora"
    eval_path = root / output_eval
    preds_path = root / output_preds

    eval_path.parent.mkdir(parents=True, exist_ok=True)
    preds_path.parent.mkdir(parents=True, exist_ok=True)

    if not test_path.exists():
        raise FileNotFoundError(f"No se encontró dataset de prueba: {test_path}")

    if not adapter_dir.exists() or not (adapter_dir / "adapter_config.json").exists():
        raise FileNotFoundError(
            f"Adaptador LoRA no encontrado en {adapter_dir}. "
            "No se pueden simular resultados. Entrene el adaptador con src/ml/train_lora.py."
        )

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    base_path = resolve_model_path(base_model_id)

    print(f"[LoRA Eval] Cargando dataset de prueba {test_path}...")
    test_cases = []
    with open(test_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if max_samples and idx >= max_samples:
                break
            line = line.strip()
            if line:
                test_cases.append(json.loads(line))

    n_cases = len(test_cases)
    print(f"[LoRA Eval] Casos a evaluar: {n_cases}")

    print(f"[LoRA Eval] Cargando Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[LoRA Eval] Cargando Modelo Base 4-bit...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    ) if torch.cuda.is_available() else None

    base_model = AutoModelForCausalLM.from_pretrained(
        base_path,
        quantization_config=bnb_config,
        device_map="auto" if torch.cuda.is_available() else "cpu",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True,
    )
    base_model.eval()

    # Contenedores de métricas
    modes = ["rules", "base_model", "lora"]
    stats = {m: {"json": 0, "schema": 0, "intent": 0, "variables_em": 0, "place": 0, "hypothesis": 0} for m in modes}
    predictions_log = []

    print("[LoRA Eval] Fase 1: Evaluación de Reglas y Modelo Base...")
    base_outputs = []
    for idx, case in enumerate(test_cases):
        msgs = case["messages"]
        prompt_msgs = msgs[:2]
        gold_plan = json.loads(msgs[2]["content"])
        meta = case.get("meta", {})
        question = meta.get("question") or ""
        if not question:
            # Extraer de msgs[1]["content"]
            lines = msgs[1]["content"].splitlines()
            for l in lines:
                if l.startswith("QUESTION:"):
                    question = l.replace("QUESTION:", "").strip()

        # Extraer candidatos del user prompt
        candidates = []
        for l in msgs[1]["content"].splitlines():
            if l.startswith("- ") and ":" in l:
                c_id = l[2:].split(":")[0].strip()
                title = l[2:].split(":")[1].strip()
                candidates.append({"variable_id": c_id, "title": title, "variables": [c_id]})

        cand_ids = [c["variable_id"] for c in candidates]
        lang = gold_plan.get("lang", "es")

        # 1. Reglas
        r_plan = _rules_plan(question, lang, candidates)
        is_j_r, is_s_r, pred_r = parse_prediction(json.dumps(r_plan), question, cand_ids)

        # 2. Base Model
        prompt_str = tokenizer.apply_chat_template(prompt_msgs, tokenize=False, add_generation_prompt=True)
        inp = tokenizer.encode(prompt_str, return_tensors="pt").to(base_model.device)
        with torch.no_grad():
            out_ids = base_model.generate(
                inp,
                max_new_tokens=150,
                do_sample=False,
                temperature=0.0,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        gen_tokens = out_ids[0][inp.shape[1] :]
        gen_base_text = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
        is_j_b, is_s_b, pred_b = parse_prediction(gen_base_text, question, cand_ids)

        base_outputs.append({
            "idx": idx,
            "question": question,
            "candidates": cand_ids,
            "gold": gold_plan,
            "rules": {"text": json.dumps(r_plan), "plan": pred_r, "is_json": is_j_r, "is_schema": is_s_r},
            "base": {"text": gen_base_text, "plan": pred_b, "is_json": is_j_b, "is_schema": is_s_b},
        })
        if (idx + 1) % 25 == 0 or (idx + 1) == n_cases:
            print(f"[LoRA Eval] Fase 1 (Base): {idx + 1}/{n_cases} casos evaluados...")

    # Cargar LoRA sobre el modelo
    print(f"[LoRA Eval] Fase 2: Cargando adaptador LoRA {adapter_dir}...")
    lora_model = PeftModel.from_pretrained(base_model, str(adapter_dir))
    lora_model.eval()

    print("[LoRA Eval] Fase 3: Evaluación de Modelo LoRA Fine-Tuned...")
    for i_lora, item in enumerate(base_outputs):
        idx = item["idx"]
        case = test_cases[idx]
        gold_plan = item["gold"]
        question = item["question"]
        cand_ids = item["candidates"]

        prompt_str = tokenizer.apply_chat_template(case["messages"][:2], tokenize=False, add_generation_prompt=True)
        inp = tokenizer.encode(prompt_str, return_tensors="pt").to(lora_model.device)
        with torch.no_grad():
            out_ids = lora_model.generate(
                inp,
                max_new_tokens=150,
                do_sample=False,
                temperature=0.0,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        gen_tokens = out_ids[0][inp.shape[1] :]
        gen_lora_text = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
        is_j_l, is_s_l, pred_l = parse_prediction(gen_lora_text, question, cand_ids)

        preds_record = {
            "id": idx,
            "question": question,
            "gold": gold_plan,
            "rules": item["rules"]["plan"],
            "base_model": item["base"]["plan"],
            "lora": pred_l,
            "raw_text": {
                "base": item["base"]["text"],
                "lora": gen_lora_text,
            },
        }
        predictions_log.append(preds_record)

        # Actualizar contadores
        eval_triplet = [
            ("rules", item["rules"]["is_json"], item["rules"]["is_schema"], item["rules"]["plan"]),
            ("base_model", item["base"]["is_json"], item["base"]["is_schema"], item["base"]["plan"]),
            ("lora", is_j_l, is_s_l, pred_l),
        ]

        for m_name, is_j, is_s, p in eval_triplet:
            if is_j:
                stats[m_name]["json"] += 1
            if is_s:
                stats[m_name]["schema"] += 1
            if p.get("intent") == gold_plan.get("intent"):
                stats[m_name]["intent"] += 1
            if sorted(p.get("variable_ids") or []) == sorted(gold_plan.get("variable_ids") or []):
                stats[m_name]["variables_em"] += 1
            p_place = (p.get("place") or "").strip().lower()
            g_place = (gold_plan.get("place") or "").strip().lower()
            if p_place == g_place:
                stats[m_name]["place"] += 1
            if p.get("hypothesis") == gold_plan.get("hypothesis"):
                stats[m_name]["hypothesis"] += 1

        if (i_lora + 1) % 25 == 0 or (i_lora + 1) == len(base_outputs):
            print(f"[LoRA Eval] Fase 3 (LoRA): {i_lora + 1}/{len(base_outputs)} casos evaluados...")

    # Guardar predictions.jsonl
    with open(preds_path, "w", encoding="utf-8") as f:
        for p in predictions_log:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # Calcular porcentajes
    metrics = {}
    for m in modes:
        metrics[m] = {
            "valid_json_pct": round(100.0 * stats[m]["json"] / n_cases, 1),
            "valid_schema_pct": round(100.0 * stats[m]["schema"] / n_cases, 1),
            "intent_accuracy_pct": round(100.0 * stats[m]["intent"] / n_cases, 1),
            "variable_exact_match_pct": round(100.0 * stats[m]["variables_em"] / n_cases, 1),
            "place_match_pct": round(100.0 * stats[m]["place"] / n_cases, 1),
            "hypothesis_accuracy_pct": round(100.0 * stats[m]["hypothesis"] / n_cases, 1),
        }

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_dataset": test_file,
        "test_samples_evaluated": n_cases,
        "base_model": base_model_id,
        "adapter_path": adapter_path,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "metrics": metrics,
    }

    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("RESULTADOS DE EVALUACIÓN REAL (EARTH TREND PLANNER)")
    print("=" * 70)
    for m in modes:
        met = metrics[m]
        print(f"[{m.upper()}]")
        print(f"  JSON Válido:       {met['valid_json_pct']}%")
        print(f"  Esquema Válido:    {met['valid_schema_pct']}%")
        print(f"  Intención Exacta:  {met['intent_accuracy_pct']}%")
        print(f"  Variables Exactas: {met['variable_exact_match_pct']}%")
        print(f"  Lugar Exacto:      {met['place_match_pct']}%")
        print(f"  Hipótesis:         {met['hypothesis_accuracy_pct']}%\n")

    print(f"Informe guardado en: {eval_path}")
    print(f"Predicciones guardadas en: {preds_path}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Evaluación comparativa real LoRA vs Base vs Reglas")
    parser.add_argument("--base-model", type=str, default="HuggingFaceTB/SmolLM2-1.7B-Instruct")
    parser.add_argument("--adapter", type=str, default="models/etd-planner-lora")
    parser.add_argument("--test-file", type=str, default="data/lora/test.jsonl")
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--output-eval", type=str, default="reports/lora/eval.json")
    parser.add_argument("--output-preds", type=str, default="reports/lora/predictions.jsonl")
    args = parser.parse_args()

    evaluate_batch(
        base_model_id=args.base_model,
        adapter_path=args.adapter,
        test_file=args.test_file,
        max_samples=args.max_samples,
        output_eval=args.output_eval,
        output_preds=args.output_preds,
    )


if __name__ == "__main__":
    main()
