# Model Card: EarthTrend Detective Planner LoRA (`etd-planner-lora`)

<!-- SI-assisted: Antigravity 2 (Gemini 3.8 Flash) -->

## Model Details

- **Model Name:** EarthTrend Detective Planner LoRA (`etd-planner-lora`)
- **Base Model:** [`HuggingFaceTB/SmolLM2-1.7B-Instruct`](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct)
- **Base Model License:** Apache 2.0
- **Adapter Architecture:** Low-Rank Adaptation (LoRA) with 4-bit quantization (QLoRA)
- **Trainable Parameters:** 6,291,456 (0.37% of 1,717,667,840 total base model parameters; 96 non-zero adapter weight matrices B across 192 adapter tensors)
- **Artifact Weights:** `models/etd-planner-lora/adapter_model.safetensors`
- **File Size:** 25,191,536 bytes (~24.0 MB)
- **SHA-256 Checksum:** `70314779040b656cc8ed5e4dac0f4285bd9efc7b392acfa870b003794327341c`
- **Primary Language:** Multilingual (English and Spanish queries)
- **Input Format:** User question alongside candidate NASA climate variables formatted into a structured prompt
- **Output Format:** Strict schema-compliant JSON `InvestigationPlan` (`intent`, `variable_ids`, `place`, `place_b`, `start_year`, `end_year`, `last_n_years`, `hypothesis`, `lang`)

---

## Intended Use

`etd-planner-lora` is fine-tuned specifically to convert natural-language user queries about climate, environmental observations, and trends into structured query plans for EarthTrend Detective. The model:
- Discriminates query intent (`investigate`, `define`, `compare`, `out_of_scope`).
- Maps colloquial descriptions (e.g., rainfall, warming, ice extent) to precise NASA Earth observation variable identifiers (e.g., `T2M`, `PRECTOTCORR`, `SEAICE_EXTENT_MONTHLY`).
- Extracts geographic target entities (`place` and `place_b`).
- Extracts temporal bounding parameters (`start_year`, `end_year`, `last_n_years`).
- Proposes an initial trend hypothesis (`warming`, `cooling`, `increasing`, `decreasing`, `unknown`).

---

## Training Procedure & Hardware

Training metadata recorded in `reports/lora/train_meta.json`:

- **Training Script:** `src/ml/train_lora.py`
- **Dataset:** `data/lora/train.jsonl` (4,323 examples; masked loss applied strictly to assistant JSON tokens)
- **Hardware:** 1× NVIDIA GeForce RTX 4070 SUPER (12 GB VRAM)
- **Peak VRAM Usage:** 2,258.19 MB (operable on GPUs with <= 4 GB VRAM)
- **Training Wall Time:** 353.7 seconds (~5.9 minutes)
- **Training Steps:** 150 steps (1,200 examples seen; batch size 2, gradient accumulation 4, effective batch size 8)
- **Learning Rate:** 2e-4 with AdamW optimizer
- **LoRA Configuration:** rank $r=16$, $\alpha=32$, dropout $0.05$, target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
- **Sequence Length:** 512 tokens maximum
- **Quantization:** 4-bit NormalFloat4 (NF4) with double quantization
- **Loss Progression:** Final Training Loss: `0.0607`, Validation Loss: `0.0198`
- **Software Dependencies:** `torch==2.6.0+cu124`, `transformers==5.23.0`, `peft==0.21.3`, `bitsandbytes==0.50.2`, `accelerate==1.15.0`, Python 3.12.10

---

## Evaluation Results (Dual-Benchmark Rule)

In adherence to project Rule 20, the LoRA planner is always cited and evaluated on **both** evaluation benchmarks together:
1. **The 200-case synthetic test set** (`data/lora/test.jsonl`, seed 42, evaluated via `src/ml/eval_lora.py`).
2. **The 50 hand-crafted reference golden questions** (`data/knowledge/golden_questions.jsonl`, evaluated via `src/detective/rag/eval_plan.py`).

### 1. 200 Test Cases Benchmark (`data/lora/test.jsonl`, seed 42)

Evaluated end-to-end on `NVIDIA GeForce RTX 4070 SUPER` as recorded in `reports/lora/eval.json`:

| Metric | Base Model (Zero-Shot) | Deterministic Rules | LoRA Fine-Tuned (`etd-planner-lora`) |
|---|:---:|:---:|:---:|
| **Valid JSON** | 35.0% | 99.5% | **100.0%** |
| **Valid Schema** | 0.0% | 99.5% | **100.0%** |
| **Intent Accuracy** | 3.0% | 76.0% | **91.5%** |
| **Exact Variable Match** | 4.5% | 15.5% | **84.5%** |
| **Place Match** | 47.5% | 73.5% | **96.5%** |
| **Hypothesis Accuracy** | 0.0% | **78.5%** | 71.0% |

### 2. 50 Reference Golden Questions Benchmark (`data/knowledge/golden_questions.jsonl`)

Evaluated on hand-written domain questions covering English and Spanish queries:

| Planner System | Exact Variable Accuracy | Accuracy Rate |
|---|:---:|:---:|
| **Deterministic Rules (`_rules_plan`)** | 47 / 50 | 94.0% |
| **LoRA Fine-Tuned (`_local_lora`)** | 31 / 50 | 62.0% |

### In-Product Serving Latency (RTX 4070 SUPER, PC1)
- **First Query (Cold Start / Model Loading):** 9.5 s
- **Subsequent Queries (Warm Inference):** 2.3 s per query

---

## Limitations

As required by project specifications (§4.4 and §2), users and evaluators must account for the following constraints:

1. **Training Epoch Fraction:** The model was trained for only 150 steps (1,200 examples seen out of 4,323 training samples, equivalent to ~0.28 of a full epoch).
2. **Synthetic Evaluation Overlap:** The 200-case test set is derived from the same synthetic templated generator as the training dataset, explaining why LoRA excels on this set (84.5% exact variable match vs. 15.5% for rules) but achieves lower accuracy on hand-crafted questions (31/50 vs. 47/50 for rules).
3. **Hypothesis Accuracy vs Rules:** On the 200-case test split, LoRA hypothesis accuracy (71.0%) is lower than deterministic keyword heuristics (78.5%).
4. **Planned Variables Failure Mode:** Among the 19 errors on the 50 reference questions, 15 were attributed to candidate selection including `planned` dataset variables (`GPM_IMERG_PRECIP` ×4, `GLDAS_SOILM_0_10` ×3, `MODIS_LST_DAY` ×3, `OMI_O3_TOTAL` ×2, `GLDAS_EVAP` ×2, `AIRS_SURF_AIR_TEMP` ×1) that do not yet have active download pipelines or appear in the training corpus.
5. **Runtime Requirements:** Inference requires PyTorch with CUDA acceleration and >= 4 GB VRAM (`requirements-ml.txt`). When running without GPU or in the web deployment, the system transparently falls back to deterministic rules.
6. **Base Model Licensing & Governance:** The underlying base model is `HuggingFaceTB/SmolLM2-1.7B-Instruct`, released under the Apache 2.0 license. The LoRA adapter inherits this open, permissive licensing.
