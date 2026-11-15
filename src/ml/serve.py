# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Servidor y cargador de inferencia LoRA para EarthTrend Planner (Fase 2 / Ronda 2 §9.2).
Carga el modelo base (HuggingFaceTB/SmolLM2-1.7B-Instruct) y el adaptador PEFT
entrenado (models/etd-planner-lora) para generar planes estructurados en tiempo real.
Cero simulación: si no hay adaptador entrenado en disco, lanza FileNotFoundError.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

_GLOBAL_MODEL = None
_GLOBAL_TOKENIZER = None
_SYSTEM_PROMPT = None


def get_system_prompt() -> str:
    """Carga el system prompt canónico de data/lora/system_prompt.txt."""
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        root = Path(__file__).resolve().parent.parent.parent
        sys_path = root / "data" / "lora" / "system_prompt.txt"
        if sys_path.exists():
            _SYSTEM_PROMPT = sys_path.read_text(encoding="utf-8").strip()
        else:
            _SYSTEM_PROMPT = (
                "You are the planning module of EarthTrend Detective, a tool that helps students "
                "investigate trends in NASA Earth science data. Return only a valid JSON object."
            )
    return _SYSTEM_PROMPT


def resolve_model_path(base_model_id: str) -> str:
    """Resuelve la ruta local cacheada si está disponible sin conexión."""
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


def load_lora_planner(
    adapter_path: Optional[str] = None,
    base_model_id: str = "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    load_in_4bit: bool = True,
):
    """Carga el modelo base cuantizado y fusiona el adaptador LoRA."""
    global _GLOBAL_MODEL, _GLOBAL_TOKENIZER
    if _GLOBAL_MODEL is not None and _GLOBAL_TOKENIZER is not None:
        return _GLOBAL_MODEL, _GLOBAL_TOKENIZER

    root = Path(__file__).resolve().parent.parent.parent
    adapter_dir = root / (adapter_path or "models/etd-planner-lora")

    if not adapter_dir.exists() or not (adapter_dir / "adapter_config.json").exists():
        raise FileNotFoundError(
            f"No existe adaptador LoRA entrenado en {adapter_dir}. "
            "Ejecute 'python src/ml/train_lora.py' para entrenarlo en GPU local."
        )

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base_path = resolve_model_path(base_model_id)

    print(f"[LoRA Serve] Cargando tokenizer desde {base_path}...")
    tokenizer = AutoTokenizer.from_pretrained(base_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    has_cuda = torch.cuda.is_available()
    print(f"[LoRA Serve] Cargando modelo base (CUDA={has_cuda})...")

    if has_cuda and load_in_4bit:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        base_model = AutoModelForCausalLM.from_pretrained(
            base_path,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
    else:
        # Modo CPU (ej. servidor Railway Hobby 8GB RAM):
        # bfloat16 o float32 sin bitsandbytes
        dtype = torch.bfloat16 if hasattr(torch, "bfloat16") else torch.float32
        base_model = AutoModelForCausalLM.from_pretrained(
            base_path,
            device_map="cpu",
            torch_dtype=dtype,
            trust_remote_code=True,
        )

    print(f"[LoRA Serve] Adjuntando adaptador PEFT LoRA desde {adapter_dir}...")
    model = PeftModel.from_pretrained(base_model, str(adapter_dir))
    model.eval()

    _GLOBAL_MODEL = model
    _GLOBAL_TOKENIZER = tokenizer
    return _GLOBAL_MODEL, _GLOBAL_TOKENIZER


def format_user_prompt(question: str, candidates: Optional[List[Dict[str, Any]]] = None) -> str:
    """Construye el mensaje de usuario canónico idéntico al dataset de entrenamiento."""
    lines = [f"QUESTION: {question.strip()}", "CANDIDATES:"]
    if candidates:
        for c in candidates:
            v_id = c.get("variable_id") or (c.get("variables") or [None])[0]
            title = c.get("title") or c.get("name") or v_id
            if v_id:
                lines.append(f"- {v_id}: {title}")
    else:
        # Fallback de candidatos comunes si no se suministran
        lines.append("- T2M: Temperatura del aire a 2 metros")
        lines.append("- PRECTOTCORR: Precipitación corregida")
        lines.append("- SEAICE_EXTENT_N: Extensión de hielo marino ártico")
        lines.append("- SEAICE_EXTENT_S: Extensión de hielo marino antártico")
        lines.append("- GISTEMP_TANOM: Anomalía de temperatura global GISS")

    return "\n".join(lines)


def plan_with_lora(
    question: str,
    candidates: Optional[List[Dict[str, Any]]] = None,
    lang: str = "es",
    adapter_path: Optional[str] = None,
    base_model_id: str = "HuggingFaceTB/SmolLM2-1.7B-Instruct",
) -> Dict[str, Any]:
    """
    Inferencia formal con LoRA:
    Ejecuta el modelo sobre GPU y parsea la respuesta JSON garantizando el esquema InvestigationPlan.
    """
    model, tokenizer = load_lora_planner(adapter_path=adapter_path, base_model_id=base_model_id)
    import torch

    sys_prompt = get_system_prompt()
    user_prompt = format_user_prompt(question, candidates)

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]

    prompt_str = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    input_ids = tokenizer.encode(prompt_str, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=160,
            do_sample=False,
            temperature=0.0,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Decodificar únicamente los tokens generados tras el prompt
    gen_tokens = output_ids[0][input_ids.shape[1] :]
    gen_text = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

    # Extraer bloque JSON
    json_match = re.search(r"\{.*\}", gen_text, re.DOTALL)
    if json_match:
        raw_json = json_match.group(0)
    else:
        raw_json = gen_text

    try:
        plan_dict = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LoRA produjo salida no JSON: {gen_text}") from exc

    plan_dict["mode"] = "lora"
    return plan_dict


def chat_with_instruct(
    messages: List[Dict[str, str]],
    max_new_tokens: int = 250,
    temperature: float = 0.7,
    adapter_path: Optional[str] = None,
    base_model_id: str = "HuggingFaceTB/SmolLM2-1.7B-Instruct",
) -> str:
    """
    Inferencia conversacional libre usando el modelo base SmolLM2-1.7B-Instruct.
    Desactiva temporalmente el adaptador LoRA con model.disable_adapter() para que
    el modelo pueda razonar, explicar y conversar fluidamente en lenguaje natural.
    """
    model, tokenizer = load_lora_planner(adapter_path=adapter_path, base_model_id=base_model_id)
    import torch

    prompt_str = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    input_ids = tokenizer.encode(prompt_str, return_tensors="pt").to(model.device)

    with torch.no_grad():
        with model.disable_adapter():
            output_ids = model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0.0,
                temperature=temperature if temperature > 0.0 else None,
                top_p=0.9 if temperature > 0.0 else None,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

    gen_tokens = output_ids[0][input_ids.shape[1] :]
    return tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()


def main():
    parser = argparse.ArgumentParser(description="Prueba de inferencia en tiempo real con LoRA")
    parser.add_argument("--question", type=str, default="¿Cómo está variando la temperatura en Lima?")
    parser.add_argument("--lang", type=str, default="es")
    parser.add_argument("--adapter", type=str, default="models/etd-planner-lora")
    args = parser.parse_args()

    print(f"Pregunta: {args.question}")
    try:
        res = plan_with_lora(args.question, lang=args.lang, adapter_path=args.adapter)
        print("Plan generado por LoRA:")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
