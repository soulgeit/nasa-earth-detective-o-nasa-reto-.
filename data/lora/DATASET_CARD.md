# Dataset Card — EarthTrend Planner LoRA Dataset

## Summary
- **Purpose**: Fine-tuning lightweight open models (e.g., Gemma 2B, Phi-3.5-mini, Granite 3B) to act as structured planners that convert student natural language queries into executable `InvestigationPlan` JSON objects.
- **Contract Compliance**: Strictly conforms to NASA Space Apps Challenge 2026 Contratos v2 §10.
- **Total Samples**: 267 (Train: 213, Validation: 26, Test: 28).
- **Languages**: 50% Spanish (es), 50% English (en).
- **Intents Covered**: `investigate`, `compare`, `define`, `out_of_scope`.
- **License**: Public Domain / NASA Space Apps Challenge 2026.

## Structure
Each line in `train.jsonl`, `val.jsonl`, and `test.jsonl` contains:
```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "QUESTION: ...\nCANDIDATES:\n- ID: Name"},
    {"role": "assistant", "content": "{\"intent\": \"...\", ...}"}
  ],
  "meta": {
    "lang": "es|en",
    "intent": "investigate|compare|define|out_of_scope",
    "gold": ["T2M"],
    "template_id": "...",
    "source": "template"
  }
}
```

## Quality Invariants
1. `place` is ALWAYS an exact case-sensitive substring of `QUESTION`.
2. `variable_ids` is ALWAYS a strict subset of `CANDIDATES`.
3. Out-of-scope queries (sports, politics, recipes) map to `intent: "out_of_scope"` with empty `variable_ids`.
4. Zero personal data (PII) or copyright violations.
