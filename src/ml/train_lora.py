# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Script oficial de entrenamiento LoRA para EarthTrend Planner (Fase 2 / Contrato §10).
Ajusta un modelo base abierto y seguro (e.g. google/gemma-2-2b-it, TinyLlama/TinyLlama-1.1B-Chat-v1.0,
o microsoft/Phi-3.5-mini-instruct) usando PEFT / LoRA.
Aplica máscara de pérdida únicamente sobre los tokens de respuesta del asistente (JSON).
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional


def create_training_script_content(
    base_model_id: str = "google/gemma-2-2b-it",
    lora_r: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.05,
    epochs: int = 3,
    lr: float = 2e-4,
    batch_size: int = 4
) -> str:
    """Retorna el código ejecutable de fine-tuning para Hugging Face / PEFT / TRL."""
    code = f'''# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Pipeline de Fine-Tuning LoRA para EarthTrend Planner.
Ejecutable en entornos con PyTorch y GPU (e.g. Google Colab T4, Kaggle, o servidor local con CUDA).
"""

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType

BASE_MODEL_ID = "{base_model_id}"
LORA_R = {lora_r}
LORA_ALPHA = {lora_alpha}
LORA_DROPOUT = {lora_dropout}
EPOCHS = {epochs}
LEARNING_RATE = {lr}
BATCH_SIZE = {batch_size}

def format_chat_prompt(example, tokenizer):
    """Aplica plantilla de chat y máscara de pérdida en la respuesta del asistente."""
    messages = example["messages"]
    
    # Construir texto de entrada y salida
    prompt_messages = messages[:2]  # system + user
    full_messages = messages        # system + user + assistant
    
    prompt_text = tokenizer.apply_chat_template(prompt_messages, tokenize=False, add_generation_prompt=True)
    full_text = tokenizer.apply_chat_template(full_messages, tokenize=False)
    
    prompt_tokens = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
    full_tokens = tokenizer(full_text, add_special_tokens=False)["input_ids"]
    
    # Crear etiquetas enmascarando el prompt con -100
    labels = [-100] * len(prompt_tokens) + full_tokens[len(prompt_tokens):]
    
    return {{
        "input_ids": full_tokens,
        "labels": labels,
        "attention_mask": [1] * len(full_tokens)
    }}

def main():
    print(f"Cargando modelo base: {{BASE_MODEL_ID}}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    device_map = "auto" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float32
    
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch_dtype,
        device_map=device_map,
        trust_remote_code=True
    )
    
    # Configurar LoRA
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    # Cargar datos
    data_files = {{
        "train": "data/lora/train.jsonl",
        "validation": "data/lora/val.jsonl"
    }}
    raw_dataset = load_dataset("json", data_files=data_files)
    
    train_dataset = raw_dataset["train"].map(
        lambda ex: format_chat_prompt(ex, tokenizer),
        remove_columns=raw_dataset["train"].column_names
    )
    val_dataset = raw_dataset["validation"].map(
        lambda ex: format_chat_prompt(ex, tokenizer),
        remove_columns=raw_dataset["validation"].column_names
    )
    
    training_args = TrainingArguments(
        output_dir="models/lora_adapter",
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=2,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10,
        fp16=(torch.cuda.is_available() and not torch.cuda.is_bf16_supported()),
        bf16=(torch.cuda.is_available() and torch.cuda.is_bf16_supported()),
        save_total_limit=2,
        load_best_model_at_end=True,
        report_to="none"
    )
    
    from transformers import Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt")
    )
    
    print("Iniciando entrenamiento LoRA...")
    trainer.train()
    
    output_dir = "models/lora_adapter/final"
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Adaptador LoRA guardado exitosamente en: {{output_dir}}")

if __name__ == "__main__":
    main()
'''
    return code


def run_smoke_test_or_pipeline(args):
    """
    Ejecuta el pipeline de preparación de entrenamiento.
    Si torch/peft están instalados, ejecuta entrenamiento real.
    Si no, valida la integridad de los datos de entrenamiento y exporta el script y cuaderno de entrenamiento.
    """
    root = Path(__file__).resolve().parent.parent.parent
    train_file = root / "data" / "lora" / "train.jsonl"
    val_file = root / "data" / "lora" / "val.jsonl"
    sys_file = root / "data" / "lora" / "system_prompt.txt"

    if not train_file.exists() or not sys_file.exists():
        print("Dataset no encontrado en data/lora. Ejecutando generador...")
        from src.ml.generate_lora_dataset import build_and_save_dataset
        build_and_save_dataset()

    print(f"Verificando integridad de datos para entrenamiento LoRA...")
    with open(train_file, "r", encoding="utf-8") as f:
        train_lines = [json.loads(line) for line in f]
    with open(val_file, "r", encoding="utf-8") as f:
        val_lines = [json.loads(line) for line in f]

    print(f"✓ Datos listos: {len(train_lines)} muestras en train, {len(val_lines)} en val.")

    # Guardar script de entrenamiento standalone
    train_script_path = root / "src" / "ml" / "train_standalone.py"
    train_script_content = create_training_script_content(
        base_model_id=args.base_model,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        epochs=args.epochs,
        lr=args.lr,
        batch_size=args.batch_size
    )
    train_script_path.write_text(train_script_content, encoding="utf-8")
    print(f"✓ Script standalone generado en {train_script_path}")

    # Intentar ejecutar con torch si está disponible
    try:
        import torch
        import peft
        import transformers
        print(f"Torch y PEFT detectados. Ejecutando entrenamiento en dispositivo: {'cuda' if torch.cuda.is_available() else 'cpu'}")
        # Ejecutar standalone
        import subprocess
        cmd = [sys.executable, str(train_script_path)]
        subprocess.run(cmd, check=True)
    except ImportError:
        print("Aviso: torch/peft no instalados en este entorno local.")
        print("El pipeline está 100% preparado para ejecución con GPU en Google Colab / Kaggle / Servidor.")
        print("Generando cuaderno reproducible: notebooks/train_lora_colab.ipynb ...")
        _export_colab_notebook(root, args.base_model)


def _export_colab_notebook(root: Path, base_model: str):
    """Genera un Jupyter Notebook ejecutable en Google Colab con 1 clic en GPU T4."""
    nb_dir = root / "notebooks"
    nb_dir.mkdir(parents=True, exist_ok=True)
    nb_path = nb_dir / "EarthTrend_LoRA_Training_Colab.ipynb"

    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# EarthTrend Detective — LoRA Planner Fine-Tuning\n",
                    "**NASA Space Apps Challenge 2026**\n",
                    "\n",
                    "Este cuaderno entrena el adaptador LoRA para el planificador estructurado `InvestigationPlan`.\n",
                    "Requiere entorno GPU (Google Colab T4 gratuito)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 1. Instalar dependencias optimizadas\n",
                    "!pip install -q transformers peft trl datasets accelerate bitsandbytes"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 2. Clonar el repositorio y verificar GPU\n",
                    "!nvidia-smi\n",
                    "# !git clone https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-..git repo\n",
                    "# %cd repo"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    f"# 3. Ejecutar entrenamiento LoRA con modelo base: {base_model}\n",
                    f"!python src/ml/train_standalone.py"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 4. Evaluar adaptador frente a Reglas y Modelo Base\n",
                    "!python src/ml/eval_lora.py"
                ]
            }
        ],
        "metadata": {
            "accelerator": "GPU",
            "language_info": {"name": "python"}
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    nb_path.write_text(json.dumps(notebook, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Cuaderno Colab guardado en: {nb_path}")


def main():
    parser = argparse.ArgumentParser(description="Entrenamiento LoRA para EarthTrend Planner")
    parser.add_argument("--base_model", type=str, default="google/gemma-2-2b-it", help="Modelo base de HuggingFace")
    parser.add_argument("--lora_r", type=int, default=16, help="Rango r de LoRA")
    parser.add_argument("--lora_alpha", type=int, default=32, help="Alpha de LoRA")
    parser.add_argument("--epochs", type=int, default=3, help="Épocas de entrenamiento")
    parser.add_argument("--lr", type=float, default=2e-4, help="Tasa de aprendizaje")
    parser.add_argument("--batch_size", type=int, default=4, help="Tamaño de lote")
    args = parser.parse_args()

    run_smoke_test_or_pipeline(args)


if __name__ == "__main__":
    main()
