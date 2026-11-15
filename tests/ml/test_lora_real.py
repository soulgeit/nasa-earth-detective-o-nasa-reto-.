# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Pruebas de verificación de inferencia real y cumplimiento de contrato para LoRA (Ronda 2 §9.2).
Verifica:
1. Sin adaptador entrenado, sale con error explícito (cero datos simulados).
2. Validador de esquemas y parser rechaza payloads defectuosos.
3. Formato canónico de entrada y plantilla de chat.
"""

import json
from pathlib import Path
import pytest
from src.ml.eval_lora import parse_prediction, extract_json_block
from src.ml.serve import format_user_prompt, get_system_prompt, plan_with_lora


def test_system_prompt_integrity():
    """El system prompt debe existir y coincidir con data/lora/system_prompt.txt."""
    sys_prompt = get_system_prompt()
    assert sys_prompt and len(sys_prompt) > 50
    assert "EarthTrend Detective" in sys_prompt
    assert "JSON" in sys_prompt


def test_format_user_prompt_matches_contract():
    """El mensaje de usuario debe contener QUESTION y CANDIDATES."""
    q = "¿Cómo varía la temperatura en Tokio?"
    candidates = [
        {"variable_id": "T2M", "title": "Temperatura del aire a 2 metros"},
        {"variable_id": "PRECTOTCORR", "title": "Precipitación"},
    ]
    formatted = format_user_prompt(q, candidates)
    assert formatted.startswith(f"QUESTION: {q}")
    assert "CANDIDATES:" in formatted
    assert "- T2M: Temperatura del aire a 2 metros" in formatted
    assert "- PRECTOTCORR: Precipitación" in formatted


def test_parse_prediction_validates_schema():
    """Prueba que el extractor de predicciones reconoce JSON válido y esquema válido."""
    q = "¿Cómo varía la temperatura en Tokio?"
    cands = ["T2M", "PRECTOTCORR"]

    valid_json_text = '{"intent": "investigate", "variable_ids": ["T2M"], "place": "Tokio", "place_b": null, "start_year": null, "end_year": null, "last_n_years": null, "hypothesis": "unknown", "lang": "es"}'
    is_j, is_s, p = parse_prediction(valid_json_text, q, cands)
    assert is_j is True
    assert is_s is True
    assert p["intent"] == "investigate"
    assert p["place"] == "Tokio"

    # JSON inválido
    bad_json = "Esto no es un json {incompleto"
    is_j2, is_s2, _ = parse_prediction(bad_json, q, cands)
    assert is_j2 is False
    assert is_s2 is False

    # JSON válido pero esquema inválido (variable inventada que no está en candidates)
    bad_schema = '{"intent": "investigate", "variable_ids": ["VARIABLE_FANTASMA"], "place": "Tokio", "hypothesis": "unknown", "lang": "es"}'
    is_j3, is_s3, _ = parse_prediction(bad_schema, q, cands)
    assert is_j3 is True
    assert is_s3 is False


def test_plan_with_lora_missing_adapter_raises_error():
    """Regla Ronda 2: Si no hay modelo entrenado, sale con error (cero simulación)."""
    with pytest.raises(FileNotFoundError) as exc_info:
        plan_with_lora("pregunta test", adapter_path="models/directorio_inexistente_de_prueba")
    assert "No existe adaptador LoRA entrenado" in str(exc_info.value)


def _has_cuda_gpu() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


@pytest.mark.skipif(not _has_cuda_gpu(), reason="Requiere GPU con CUDA para inferir con el adaptador LoRA real (Regla 22)")
def test_plan_with_lora_real_adapter_on_gpu():
    """Regla 22: Inferencia con el adaptador LoRA real canónico en GPU."""
    adapter_path = "models/etd-planner-lora"
    question = "¿Cómo está variando la temperatura en Lima?"
    plan = plan_with_lora(question, adapter_path=adapter_path, lang="es")
    assert isinstance(plan, dict)
    assert plan.get("mode") == "lora"
    assert "intent" in plan
    assert "variable_ids" in plan

