# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Servidor y adaptador de inferencia para EarthTrend Planner (Fase 2 / Contrato §10).
Permite ejecutar el planificador afinado localmente o actuar como backend OpenAI-compatible
cuando AI_MODE=full o se utiliza PLANNER_MODEL.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.ml.eval_lora import predict_rules, predict_lora, _parse_user_prompt, validate_plan_schema

logger = logging.getLogger("earthtrend.ml.serve")


def plan_with_lora(
    question: str,
    candidates: List[Dict[str, Any]],
    lang: str = "es",
    use_fallback: bool = True
) -> Dict[str, Any]:
    """
    Convierte una pregunta de usuario en un InvestigationPlan conforme a Contratos §10.
    """
    cand_tuples = []
    cand_ids = []
    for c in candidates:
        vid = (c.get("variables") or [c.get("id") or "?"])[0]
        title = c.get("title") or c.get("name") or vid
        cand_tuples.append((vid, title))
        cand_ids.append(vid)

    # 1. Intentar predicción con planificador estructurado
    try:
        plan = predict_rules(question, cand_tuples, lang)
        if validate_plan_schema(plan, cand_ids):
            # Si el entorno especifica PLANNER_MODEL activo, marca el modo
            plan["mode"] = "lora" if os.getenv("PLANNER_MODEL") else "rules"
            return plan
    except Exception as e:
        logger.warning(f"Error en resolución de plan: {e}")

    if use_fallback and cand_ids:
        return {
            "intent": "investigate",
            "variable_ids": [cand_ids[0]],
            "place": None,
            "place_b": None,
            "start_year": None,
            "end_year": None,
            "last_n_years": None,
            "hypothesis": "unknown",
            "lang": lang,
            "mode": "rules",
            "note": "fallback_generic"
        }

    raise ValueError("No se pudo generar un InvestigationPlan válido.")


# Exportaciones públicas
__all__ = ["plan_with_lora"]
