<!-- ESTADO:INICIO -->
## ESTADO — hermes-2 — 2026-11-14 19:20 hora de Perú
Rama@commit: feature/scrapes@6ffe1bd · empujado: sí
VERIFICADO: casos analysis/2 → `python -X utf8 -I scripts/regenerate_cases_v2.py` → 5/5 recomputados con el motor real (no traducidos del JSON viejo) + `data/cases/index.json`.
VERIFICADO: atlas con el motor real → `python -X utf8 -I scripts/build_atlas.py --variable T2M --bbox -82 -18 -68 -2` → 759 celdas, 455 significativas (59,9 %); GISTEMP 16 041 celdas, 15 429 (96,2 %). Ya no usan el fallback local.
VERIFICADO: API → `src.api.main.list_cases()` devuelve 5 casos con precedencia NASA y `get_atlas('T2M')` responde trendmap/2.
ESCRITO (sin ejecutar de punta a punta): nada pendiente.
ROTO / NO HECHO: el veredicto sigue mal en `main`: arctic-seaice sale SIGNIFICANT_STRONG con OLS p=0,3985 y `tests_agree: true`. El arreglo existe en `origin/feature/stats@ef18e01`, no en main; no lo aplico (carril de Antigravity 2).
Siguiente paso: cuando se integre ef18e01, reejecutar `scripts/regenerate_cases_v2.py` (un comando).
Necesito de: cfable (integrador): integrar `origin/feature/stats@ef18e01` antes de congelar el veredicto de los casos.
Avisos para otros carriles: el dataset LoRA estaba truncado en disco (4323→281, 814→78, 632→78); restaurado desde el commit bueno, no regenerado.
<!-- ESTADO:FIN -->

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

## S2 — LISTO (con un pendiente de otro carril)  (2026-11-14 16:52 UTC-5)
Rama@commit: feature/scrapes
Qué quedó:
- `scripts/freeze_case.py`: llama a `get_series` y `analyze_series` del contrato §6 y escribe
  `data/cases/<id>/{series.json,analysis.json,case.json}`. Los textos de historia quedan `TODO_HUMANO`.
- Cinco casos técnicos congelados con datos reales:
  - `lima-t2m` (POWER, 540 meses, 1981-01 → 2025-12, 18.41 °C en 1981-01)
  - `svalbard-t2m` (POWER, 540 meses)
  - `piura-prectotcorr` (POWER, 540 meses)
  - `arctic-seaice` (NSIDC, 576 meses, 11.65 → 6.69 millones de km²)
  - `antarctic-seaice` (NSIDC, 576 meses)
- Las variables hemisféricas (NSIDC, GISTEMP) se piden sin coordenadas: el conector rechaza un punto y era el fallo inicial.
Evidencia:
```bash
$ python scripts/validate_datasets.py data/cases/*/series.json
[ OK ] data/cases/antarctic-seaice/series.json
[ OK ] data/cases/arctic-seaice/series.json
[ OK ] data/cases/lima-t2m/series.json
[ OK ] data/cases/piura-prectotcorr/series.json
[ OK ] data/cases/svalbard-t2m/series.json
5/5 archivos validos
```
Falta / riesgos:
- `analysis.json` sale con la estructura vieja del motor (`metrics`, `detective_answers`), no con `AnalysisResult v2` (`trend`, `significance`, `detectability`). El contrato §6 (`analyze_series`) aún no está en `origin/feature/stats`; cuando Antigravity 2 lo publique, se vuelve a ejecutar `freeze_case.py --technical` y se regeneran los cinco.
- El caso «tendencias opuestas» no se cumple con el periodo completo: Ártico −0.41 M km²/año (p<0.001, significativo) y Antártico −0.06 (no significativo). Es el resultado honesto; el caso debe presentarse como «el Ártico baja con claridad; el Antártico todavía no se puede afirmar».
Necesito de otros: Antigravity 2 (analyze_series v2) para la estructura final del análisis.

## S3 — LISTO  (2026-11-14 16:52 UTC-5)
Rama@commit: feature/scrapes
Qué quedó: `scripts/build_atlas.py` → `data/atlas/<ID>.json` (TrendMap v2).
- GISTEMP_TANOM: un archivo, 16 000 celdas, 15 398 significativas (96.2 %), 0.77 MB, 14 s.
- T2M regional Sudamérica: 16 teselas de 4°, 759 celdas, 455 significativas (59.9 %, todas al alza), 0.04 MB, 0.9 min.
- Progreso reanudable en `data/cache/atlas_<ID>.npz` (comprimido; la primera versión en JSON pesaba 542 MB y se descartó).
- Tendencia por celda sobre **medias anuales** (Sen + Mann-Kendall + BH FDR), que es la reducción que el contrato ya usa para la prueba anual; sin promediar pendientes ni valores p.
- Si el archivo supera 3 MB, agrupa 2×2 promediando las series antes de analizar.
Evidencia:
```bash
$ python scripts/build_atlas.py --variable GISTEMP_TANOM
wrote data/atlas/GISTEMP_TANOM.json
size=0.77 MB cells=16000 significant=15398 (96.2%) elapsed=0.2 min

$ python scripts/build_atlas.py --variable T2M --bbox -82 -18 -68 -2 --tile 4
wrote data/atlas/T2M.json
size=0.04 MB cells=759 significant=455 (59.9%) elapsed=0.9 min
```
Falta / riesgos: `analyze_grid` del contrato §6 aún no existe; se usa una implementación local equivalente marcada en `method_note`.
Necesito de otros: Antigravity 2 (`analyze_grid`) para sustituir el fallback.

### Nota de verificación (16:55)
La evidencia de S2 se obtuvo ejecutando `scripts/validate_datasets.py` de la versión de
`origin/feature/data-pipeline` (la que acepta rutas de `series.json`). La copia que trae mi
rama `feature/scrapes` es anterior a ese cambio: solo audita `data/processed/` y da por
buenos los 4 archivos sintéticos que la v2 manda borrar. No edito ese archivo porque es
del carril de Antigravity 1; lo señalo para que el arquitecto lo resuelva al integrar
(la versión vigente es la de `feature/data-pipeline`).
