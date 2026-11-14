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
