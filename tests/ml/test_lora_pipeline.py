# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Pruebas unitarias para el pipeline de ML / LoRA (fase 2 / contrato §10).
"""

import json
from pathlib import Path
import pytest

from src.ml.serve import plan_with_lora
from src.ml.eval_lora import predict_rules, validate_plan_schema, evaluate_all


def test_lora_dataset_files_exist_and_valid():
    """Verifica que los archivos del dataset LoRA existen y cumplen el formato jsonl."""
    root = Path(__file__).resolve().parent.parent.parent
    lora_dir = root / "data" / "lora"

    sys_prompt = lora_dir / "system_prompt.txt"
    assert sys_prompt.exists()
    assert len(sys_prompt.read_text(encoding="utf-8")) > 50

    for split in ["train", "val", "test"]:
        split_file = lora_dir / f"{split}.jsonl"
        assert split_file.exists(), f"Falta {split_file}"
        with open(split_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) >= 20, f"Pocos registros en {split}: {len(lines)}"

        # Verificar primer registro
        first = json.loads(lines[0])
        assert "messages" in first
        assert len(first["messages"]) == 3
        assert first["messages"][0]["role"] == "system"
        assert first["messages"][1]["role"] == "user"
        assert first["messages"][2]["role"] == "assistant"

        assistant_json = json.loads(first["messages"][2]["content"])
        assert "intent" in assistant_json
        assert "variable_ids" in assistant_json


def test_rules_planner_prediction():
    """Verifica que el planificador por reglas genera planes conformes al contrato."""
    candidates = [
        ("T2M", "Air temperature at 2 m"),
        ("PRECTOTCORR", "Precipitation"),
        ("AOD_55", "Aerosol optical depth")
    ]
    cand_ids = [c[0] for c in candidates]

    # Pregunta de calor en Piura
    plan = predict_rules("¿Hace más calor en Piura?", candidates, lang="es")
    assert validate_plan_schema(plan, cand_ids)
    assert plan["intent"] == "investigate"
    assert plan["place"] == "Piura"
    assert plan["hypothesis"] == "up"
    assert plan["variable_ids"] == ["T2M"]

    # Pregunta fuera de dominio
    oos_plan = predict_rules("¿Quién ganó el partido de fútbol?", candidates, lang="es")
    assert oos_plan["intent"] == "out_of_scope"
    assert oos_plan["variable_ids"] == []


def test_plan_with_lora_inference():
    """Verifica la función pública plan_with_lora con fallback."""
    candidates = [
        {"id": "T2M", "title": "Air temperature at 2 m"},
        {"id": "PRECTOTCORR", "title": "Precipitation"}
    ]
    res = plan_with_lora("¿Está disminuyendo la lluvia en Piura?", candidates, lang="es")
    assert res["intent"] == "investigate"
    assert "PRECTOTCORR" in res["variable_ids"]
    assert res["place"] == "Piura"
    assert res["mode"] in ("lora", "rules")


def test_evaluation_benchmark_runs():
    """Verifica que el script de evaluación ejecuta y produce métricas completas."""
    summary = evaluate_all()
    assert "LoRA Fine-Tuned" in summary
    assert "Reglas (Rules Baseline)" in summary
    assert summary["LoRA Fine-Tuned"]["valid_schema_pct"] == 100.0
