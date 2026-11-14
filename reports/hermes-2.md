# Reportes de Hermes 2

## S1 — LISTO  (2026-11-14 15:50 UTC-5)
Rama@commit: feature/scrapes (pendiente de commit)
Qué quedó:
- `scripts/build_lora_dataset.py`: generador del dataset de entrenamiento del planificador.
  - Formato contrato §10: mensajes system/user/assistant, 9 claves en orden fijo.
  - Variables y definiciones desde `data/catalog/variables.json` (si no existe, desde `variables.seed.json`).
  - Lugares desde `data/catalog/gazetteer.json` cuando exista; si no, lista provisional de ~150 nombres.
  - Reparto de intenciones por muestreo ponderado: investigate 60 %, compare 15 %, define 10 %, out_of_scope 10 %, no_match 5 %.
  - Idioma: 55 % ES / 45 % EN. Lugares: 35 % Perú, 25 % LatAm, 40 % mundo; 15 % sin lugar.
  - Años: 15 % rango explícito, 10 % «últimos N años». Hipótesis up/down cuando la pregunta la sugiere.
  - Candidatas: la correcta + 5 distractoras (2 de la misma esfera, 3 al azar), barajadas. En `no_match` se quita la correcta.
  - Ruido: 20 % sin tildes, 10 % minúsculas, 10 % una errata. Los nombres de lugar nunca se corrompen.
  - Plantillas distintas para train (familia A) y val/test (familia B): el test no repite frases de entrenamiento.
  - Semilla fija 20261114: mismo comando, mismo dataset.
- `data/lora/train.jsonl` (2558), `val.jsonl` (509), `test.jsonl` (452), `system_prompt.txt`, `DATASET_CARD.md`.
Evidencia:
```bash
$ python scripts/build_lora_dataset.py
train=2558 val=509 test=452

$ python scripts/build_lora_dataset.py --check
intent mix (train):
  investigate    wanted 60%  actual 59.0%
  compare        wanted 15%  actual 15.8%
  define         wanted 10%  actual 10.5%
  out_of_scope   wanted 10%  actual 9.7%
  no_match       wanted 5%  actual 5.0%
language mix (train): {'es': 1403, 'en': 1155}
counts: {'train': 2558, 'val': 509, 'test': 452}
--check passed
```
Falta / riesgos:
- Regenerar cuando Hermes 1 entregue `variables.json` y `gazetteer.json` finales (S4).
- No hay paráfrasis de modelo (opcional, no usado).
Necesito de otros: Hermes 1 (catálogo v2 y gazetteer) para S4.

## S4 — LISTO  (2026-11-14 16:40 UTC-5)
Rama@commit: feature/scrapes
Qué quedó:
- Dataset regenerado contra el catálogo v2 y el gazetteer finales de Hermes 1.
- Nueva deduplicación: igualdad exacta normalizada siempre; Jaccard ≥ 0,95 solo
  en preguntas de 8+ palabras (antes 0,9 desde 4 palabras, que colapsaba las
  preguntas cortas de "define").
- Reparto verificado tras deduplicar: intenciones dentro de ±1 punto y idioma
  53,1 % ES / 46,9 % EN.
Evidencia:
```bash
$ python scripts/build_lora_dataset.py
train=4323 val=814 test=632

$ python scripts/build_lora_dataset.py --check
intent mix (train):
  investigate    wanted 60%  actual 60.3%
  compare        wanted 15%  actual 15.3%
  define         wanted 10%  actual 9.1%
  out_of_scope   wanted 10%  actual 10.2%
  no_match       wanted 5%  actual 5.1%
language mix (train): {'es': 2294, 'en': 2029}
--check passed
```
Falta / riesgos: avisar a Antigravity 2 (fase LoRA) con el recuento nuevo.
Necesito de otros: nada.
