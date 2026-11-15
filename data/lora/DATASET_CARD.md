# DATASET CARD — LoRA planning dataset (EarthTrend Detective)

Generated: 2026-11-14 · Agent: Hermes 2 · File set: `data/lora/{train,val,test}.jsonl`,
`data/lora/system_prompt.txt`.

## What it is

Training data for the small open model that turns a student's question into an
`InvestigationPlan` (contract §10). Each example is a chat with three messages:

1. `system`: the fixed prompt in `system_prompt.txt`.
2. `user`: `QUESTION: <question>` plus six candidate variable lines.
3. `assistant`: the plan as one JSON object, keys in the contract order.

`meta` records `lang`, `intent`, `gold`, `template_id` and `source`.

## How it was generated

- **By program, from templates.** No example was written or paraphrased by a
  language model: `source` is `template` for every record.
- **Variables and definitions** come from `data/catalog/variables.json`; if the
  catalogue is missing, the seed is used, which produces the same ids but the
  long English names (regenerate after Hermes 1 ships the catalogue).
- **Places** come from `data/catalog/gazetteer.json` when present, limited to
  120 Peruvian and 200 world cities plus the fixed Peruvian region list; the
  fallback is a 150-name provisional list written for this task.
- **Templates**: at least 40 phrasings per intent per language. Train uses one
  template family; validation and test use the other, so the test set never
  repeats a training phrasing.
- **Intents**: investigate 60 %, compare 15 %, define 10 %, out_of_scope 10 %,
  no_match 5 %. In `no_match` the correct variable is removed from the
  candidates, so `variable_ids` is `[]`.
- **Candidates**: the correct one plus five distractors (two from the same
  sphere, three at random), shuffled.
- **Language**: 55 % Spanish, 45 % English.
- **Places**: 35 % Peru, 25 % rest of Latin America, 40 % world; 15 % of
  examples carry no place.
- **Years**: 15 % explicit range, 10 % "last N years".
- **Hypothesis**: `up`/`down` when the question suggests it, else `unknown`.
- **Noise**: 20 % without accents, 10 % lowercase, 10 % a single typo. Place
  names are never typo-ed and are restored exactly, because the plan must copy
  them literally.
- **Seed**: fixed (`20261114`). Same command, same dataset.

## Counts (this build)

| Split | Examples |
|---|---|
| train | 4 323 |
| val | 814 |
| test | 632 |

Intent mix actually obtained in train: investigate 60.3 %, compare 15.3 %,
define 9.1 %, out_of_scope 10.2 %, no_match 5.1 %. Language mix: 53.1 % Spanish,
46.9 % English. Every variable appears at least 322 times as the gold answer.
Built against the final `variables.json` and `gazetteer.json` from Hermes 1
(task S4).

## Checks

`python scripts/build_lora_dataset.py --check` verifies: valid JSON with the
nine keys in order, `variable_ids` ⊆ candidates, `place`/`place_b` appear
literally in the question, valid intents and hypothesis values, no exact
duplicates across splits, minimum sizes and the requested mixes. It exits
non-zero on any failure.

## Known limits

- Templates are transparently synthetic: they teach the output format and the
  intent split, not world knowledge.
- The place distribution over-weights Peru on purpose (challenge context).
- No paraphrase augmentation was applied (the optional step allows it only with
  a non-Chinese open model; none was used).
- The dataset must be regenerated once Hermes 1 publishes the final
  `variables.json` and `gazetteer.json` (task S4).

## AI use

Generated with AI assistance: templates and generator were produced by Hermes 2
(Claude Sonnet 5.5) and are declared in `docs/AI_USE_LOG.md`. The data itself is
program output, not a model's answers.

---

## Measured defects (Ronda 4 audit, 2026-11-15)

Both defects below were found in review. They are measured, not estimated, with the
command shown in each section. The JSONL files are **not** rewritten: the canonical
adapter was trained on them, so changing them would make the published evaluation
irreproducible (rule 21).

### 1. Range templates with empty years

Some questions promise an explicit date range but carry no years, e.g.
`"... in Bogotá between  and ?"` (double space where the years should be).
The plan is still valid, but the question is not a faithful rendering: it cannot be
answered as written.

| split | rows | `between  and` / `entre  y` (literal double space) | any `between`/`entre` with no 4-digit year |
|---|---|---|---|
| train | 4323 | 92 (2,1 %) | 174 (4,0 %) |
| val | 814 | 70 (8,6 %) | 97 (11,9 %) |
| test | 632 | 51 (8,1 %) | 63 (10,0 %) |

The literal `entre  y` / `between  and` archetype is the strict reading: it is
92 rows in train, not the 132 quoted in review. The wider reading (any range
connector without a year anywhere in the question) gives 174 in train, 97 in val and
63 in test. **Neither reproduces 132**, so the review figure is reported here with
both readings instead of a third unexplained number.

Cause: `scripts/build_lora_dataset.py` only fills `{year0}` when
`rng.random() < 0.15`; the remaining 85 % of range templates render with empty
placeholders.

Reproduce:
```
python -X utf8 -c "import json,re; rows=[json.loads(l) for l in open('data/lora/train.jsonl',encoding='utf-8') if l.strip()]; q=lambda r: r['messages'][1]['content'].split('CANDIDATES')[0]; print(sum(1 for r in rows if re.search(r'(entre\s{2,}y|between\s{2,}and)', q(r))))"
```

### 2. `out_of_scope` examples carry a variable

Every `out_of_scope` row (440 train / 83 val / 71 test) has a non-empty
`variable_ids`, and the same value in `meta.gold`. An out-of-scope question should
name no variable at all: `"¿Cuál es el sentido de la vida?"` is answered with
`variable_ids: ["SEAICE_EXTENT_S"]`.

| split | rows | `out_of_scope` | of those, with `variable_ids` | `no_match` | of those, with `variable_ids` |
|---|---|---|---|---|---|
| train | 4323 | 440 | **440 (100 %)** | 220 | 0 |
| val | 814 | 83 | **83 (100 %)** | 47 | 0 |
| test | 632 | 71 | **71 (100 %)** | 32 | 0 |

`investigate`/`compare` never lack a variable (0 of 3268 / 601 / 466), and
`no_match` is correct: the generator already strips the variable for `no_match`.

Cause, line 815 of `scripts/build_lora_dataset.py`:

```python
plan = make_plan(intent, vid if intent != "no_match" else None, ...)
```

`out_of_scope` should be in that condition:

```python
plan = make_plan(intent, None if intent in ("no_match", "out_of_scope") else vid, ...)
```

Impact: the model is taught to attach an earth-science variable to off-topic
questions. `reports/lora/predictions.jsonl` row 1 shows it at inference time
(the review of 2026-11-14 §2.7 reports the same). Rule 19 keeps `planned` variables
out of the candidates, but this defect is about `out_of_scope`, not availability.

Regenerating is a one-command fix (`python scripts/build_lora_dataset.py`), but the
1.7B adapter was trained on the current files; a retrain is needed to benefit from
it. Out of scope for the freeze (rule 18).
