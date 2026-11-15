# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Script oficial de entrenamiento LoRA para EarthTrend Planner (Fase 2 / Ronda 2 §9.2).
Ajusta un modelo base abierto y permisivo (HuggingFaceTB/SmolLM2-1.7B-Instruct)
usando PEFT / LoRA en GPU local (con 4-bit QLoRA para operar de forma segura en VRAM <= 4 GB).
Aplica máscara de pérdida (-100) únicamente sobre los tokens del asistente (JSON).
Guarda el adaptador en models/etd-planner-lora/ y el registro en reports/lora/training_log.json.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainerCallback,
    TrainingArguments,
    set_seed,
)


def resolve_base_model_path(base_model_id: str) -> str:
    """Busca primero si el modelo ya está descargado en la caché local de Hugging Face."""
    repo_folder = f"models--{base_model_id.replace('/', '--')}"
    hub_cache = Path.home() / ".cache" / "huggingface" / "hub" / repo_folder / "snapshots"
    if hub_cache.exists():
        snapshots = list(hub_cache.iterdir())
        if snapshots:
            # Seleccionar el snapshot que contiene model.safetensors
            for s in snapshots:
                if (s / "model.safetensors").exists():
                    print(f"[LoRA Train] Usando snapshot local cacheado: {s}")
                    return str(s)
            return str(snapshots[0])
    return base_model_id


class TrainingLogCallback(TrainerCallback):
    """Registra la pérdida por paso y evaluación en una estructura exportable."""

    def __init__(self):
        super().__init__()
        self.step_history: List[Dict[str, Any]] = []
        self.eval_history: List[Dict[str, Any]] = []

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            entry = {"step": state.global_step, "epoch": state.epoch, **logs}
            if "loss" in logs:
                self.step_history.append(entry)
            if "eval_loss" in logs:
                self.eval_history.append(entry)


def format_example(example: Dict[str, Any], tokenizer: AutoTokenizer, max_length: int = 512) -> Dict[str, Any]:
    """
    Aplica la plantilla ChatML y enmascara los tokens del prompt con -100
    para calcular la pérdida únicamente sobre la respuesta JSON del asistente.
    """
    messages = example["messages"]
    prompt_messages = messages[:2]  # system + user
    full_messages = messages        # system + user + assistant

    prompt_text = tokenizer.apply_chat_template(prompt_messages, tokenize=False, add_generation_prompt=True)
    full_text = tokenizer.apply_chat_template(full_messages, tokenize=False)

    prompt_tokens = tokenizer.encode(prompt_text, add_special_tokens=False)
    full_tokens = tokenizer.encode(full_text, add_special_tokens=False)

    if len(full_tokens) > max_length:
        full_tokens = full_tokens[:max_length]

    # Enmascarar prompt con -100
    prompt_len = min(len(prompt_tokens), len(full_tokens))
    labels = [-100] * prompt_len + full_tokens[prompt_len:]

    return {
        "input_ids": full_tokens,
        "labels": labels,
        "attention_mask": [1] * len(full_tokens),
    }


def load_jsonl_dataset(path: Path, tokenizer: AutoTokenizer, max_length: int = 512, max_samples: Optional[int] = None) -> Dataset:
    """Carga y tokeniza un archivo jsonl con chat messages."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if max_samples and idx >= max_samples:
                break
            line = line.strip()
            if line:
                records.append(json.loads(line))

    raw_ds = Dataset.from_list(records)
    tokenized_ds = raw_ds.map(
        lambda ex: format_example(ex, tokenizer, max_length=max_length),
        remove_columns=raw_ds.column_names,
    )
    return tokenized_ds


def train(
    base_model_id: str = "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    epochs: int = 2,
    max_steps: Optional[int] = None,
    batch_size: int = 2,
    grad_accum: int = 4,
    lr: float = 2e-4,
    max_length: int = 512,
    lora_r: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.05,
    seed: int = 42,
    max_train_samples: Optional[int] = None,
    max_val_samples: Optional[int] = 100,
    output_dir: str = "models/etd-planner-lora",
    log_file: str = "reports/lora/training_log.json",
) -> Dict[str, Any]:
    """Entrenamiento real de LoRA sobre GPU local."""
    set_seed(seed)
    start_time = time.time()

    root = Path(__file__).resolve().parent.parent.parent
    train_path = root / "data" / "lora" / "train.jsonl"
    val_path = root / "data" / "lora" / "val.jsonl"
    out_path = root / output_dir
    log_path = root / log_file
    out_path.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if not train_path.exists():
        raise FileNotFoundError(f"No se encontró dataset de entrenamiento: {train_path}")

    model_target = resolve_base_model_path(base_model_id)

    print(f"[LoRA Train] Cargando Tokenizer para {base_model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_target, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[LoRA Train] Preparando datasets...")
    train_ds = load_jsonl_dataset(train_path, tokenizer, max_length=max_length, max_samples=max_train_samples)
    val_ds = load_jsonl_dataset(val_path, tokenizer, max_length=max_length, max_samples=max_val_samples)
    print(f"[LoRA Train] Train samples: {len(train_ds)}, Val samples: {len(val_ds)}")

    print(f"[LoRA Train] Cargando Modelo Base con cuantización 4-bit...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_target,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, peft_config)
    trainable_params, all_params = model.get_nb_trainable_parameters()
    print(
        f"[LoRA Train] Parámetros entrenables: {trainable_params:,} / {all_params:,} "
        f"({100 * trainable_params / all_params:.2f}%)"
    )

    training_args = TrainingArguments(
        output_dir=str(out_path / "checkpoints"),
        num_train_epochs=epochs,
        max_steps=max_steps if max_steps else -1,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=lr,
        weight_decay=0.01,
        eval_strategy="steps" if (max_steps and max_steps > 0) else "epoch",
        eval_steps=max(10, (max_steps // 4)) if (max_steps and max_steps > 0) else None,
        save_strategy="steps" if (max_steps and max_steps > 0) else "epoch",
        save_steps=max(10, (max_steps // 2)) if (max_steps and max_steps > 0) else None,
        logging_steps=10,
        fp16=True,
        save_total_limit=1,
        report_to="none",
        seed=seed,
    )

    log_callback = TrainingLogCallback()

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt"),
        callbacks=[log_callback],
    )

    print("[LoRA Train] Iniciando entrenamiento formal...")
    train_result = trainer.train()
    elapsed = time.time() - start_time

    print(f"[LoRA Train] Guardando adaptador PEFT en {out_path}...")
    model.save_pretrained(str(out_path))
    tokenizer.save_pretrained(str(out_path))

    # Construir log estructurado
    gpu_info = {
        "available": torch.cuda.is_available(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if torch.cuda.is_available() else 0.0,
        "peak_vram_mb": round(torch.cuda.max_memory_allocated() / (1024**2), 2) if torch.cuda.is_available() else 0.0,
    }

    import peft
    import transformers

    log_data = {
        "base_model": base_model_id,
        "resolved_model_path": model_target,
        "seed": seed,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(elapsed, 2),
        "gpu": gpu_info,
        "libraries": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "peft": peft.__version__,
            "python": platform.python_version(),
        },
        "hyperparameters": {
            "epochs": epochs,
            "max_steps": max_steps,
            "per_device_batch_size": batch_size,
            "gradient_accumulation_steps": grad_accum,
            "effective_batch_size": batch_size * grad_accum,
            "learning_rate": lr,
            "max_length": max_length,
            "lora_r": lora_r,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout,
            "trainable_params": trainable_params,
            "all_params": all_params,
        },
        "metrics": {
            "train_loss": round(float(train_result.training_loss), 4),
            "step_history": log_callback.step_history,
            "eval_history": log_callback.eval_history,
        },
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"[LoRA Train] Registro de entrenamiento guardado en {log_path}")
    print(f"[LoRA Train] Completado exitosamente en {elapsed:.1f} s con train_loss={train_result.training_loss:.4f}")
    return log_data


def main():
    parser = argparse.ArgumentParser(description="Entrenamiento LoRA real para EarthTrend Planner")
    parser.add_argument("--base-model", type=str, default="HuggingFaceTB/SmolLM2-1.7B-Instruct")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=150)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--output-dir", type=str, default="models/etd-planner-lora")
    parser.add_argument("--log-file", type=str, default="reports/lora/training_log.json")

    args = parser.parse_args()
    train(
        base_model_id=args.base_model,
        epochs=args.epochs,
        max_steps=args.max_steps,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        lr=args.lr,
        max_length=args.max_length,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        seed=args.seed,
        max_train_samples=args.max_train_samples,
        output_dir=args.output_dir,
        log_file=args.log_file,
    )


if __name__ == "__main__":
    main()
