<!-- ESTADO:INICIO -->
## ESTADO — hermes-2 — 2026-11-14 21:10 hora de Perú (Ronda 3)
Rama@commit: feature/scrapes@59b6a49 · empujado: sí
SUITE COMPLETA sobre main fusionado: `python -m pytest -q` → **1 failed, 223 passed, 9 skipped** (la roja es test_published_nasa_benchmarks, por el −9999 del hielo).
VERIFICADO: casos regenerados con el motor v2 → lima-t2m queda **SIGNIFICANT** (era SIGNIFICANT_STRONG congelado); los 5 recomputados, no traducidos.
VERIFICADO: 2 casos nuevos con los CSV reales de Giovanni → `amazonia-t2m` (SIGNIFICANT_STRONG, Sen 0,186 °C/década, 557 meses) y `amazonia-prectotcorr`, con `provenance.kind=user_upload` y la «URL to Reproduce Results».
VERIFICADO: `/api/cases` sirve 7 casos (índice reconstruido desde los case.json).
ROTO / NO HECHO: tarea 2 bloqueada. Los casos de hielo siguen con −9999 en 1987-12 y 1988-01 (min(series.raw) = −9999,0); la OLS sale +25,7 y +26,2 por década frente a Sen −0,50 y −0,03. El arreglo de antigravity-1 no está empujado (origin/feature/data-pipeline = 33e27fa, sin cambios en src/etl/nsidc_seaice.py).
Siguiente paso: al llegar el commit de antigravity-1, `regenerate_cases_v2.py --id arctic-seaice` y `--id antarctic-seaice`, y comprobar min(raw) >= 0, los dos meses en null y OLS/Sen con el mismo signo.
Necesito de: antigravity-1 (arreglo del −9999 en el conector NSIDC).
Avisos para otros carriles: los dos CSV de Giovanni son de MERRA-2, no de GPM/MODIS/OMI; no presentarlos como instrumento distinto. El venv local necesitaba `pymannkendall` y `httpx`; instalados, sin tocar requirements.txt.
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

---

## Ronda 3 — ESTADO de hermes-2 (2026-11-14 21:05 UTC-5)

**Rama:** `feature/scrapes`

**Suite completa sobre `main` fusionado (regla 14):**

```
$ python -m pytest -q
1 failed, 223 passed, 9 skipped, 54 warnings in 155.28s
FAILED tests/stats/test_trend_engine.py::test_published_nasa_benchmarks
```

### Tarea 1 — LISTO

`python -X utf8 -I scripts/regenerate_cases_v2.py` sobre `main` fusionado:

```
--- lima-t2m (T2M)              OK verdict=SIGNIFICANT n=540
--- svalbard-t2m (T2M)          OK verdict=SIGNIFICANT_STRONG n=540
--- piura-prectotcorr           OK verdict=SUGGESTIVE n=540
--- arctic-seaice               OK verdict=SIGNIFICANT n=576
--- antarctic-seaice            OK verdict=NOT_SIGNIFICANT n=576
```

`lima-t2m` queda **SIGNIFICANT** (era `SIGNIFICANT_STRONG` congelado), que es lo que responde el
motor ya integrado.

Nota de entorno: el venv local no tenía `pymannkendall` ni `httpx` (este último lo necesita
`starlette.testclient` para `tests/api/`), aunque ambos están declarados. Instalados sin tocar
`requirements.txt`.

### Tarea 2 — NO HECHO (bloqueado por antigravity-1)

Los casos de hielo se regeneraron, pero **siguen con el relleno dentro**:

```
$ python - <<'PY'   # sobre data/cases/<id>/series.json
arctic-seaice     min: -9999.0 | valores < 0: 2
antarctic-seaice  min: -9999.0 | valores < 0: 2
PY
```

El defecto se ve en la tabla de los cinco casos regenerados: Sen y OLS salen de signo opuesto.

| caso | sen/década | ols/década | veredicto |
|---|---|---|---|
| arctic-seaice | **−0,505** | **+25,746** | SIGNIFICANT |
| antarctic-seaice | **−0,035** | **+26,158** | NOT_SIGNIFICANT |
| lima-t2m | 0,159 | 0,131 | SIGNIFICANT |
| svalbard-t2m | 0,699 | 0,772 | SIGNIFICANT_STRONG |
| piura-prectotcorr | −0,011 | −0,071 | SUGGESTIVE |

Comprobado a las 21:05 UTC-5: `origin/feature/data-pipeline` sigue en `33e27fa` y
`git diff origin/main FETCH_HEAD -- src/etl/nsidc_seaice.py` sale vacío; el arreglo del −9999
**aún no está empujado**. En cuanto llegue, estos dos comandos cierran la tarea:

```
python -X utf8 -I scripts/regenerate_cases_v2.py --id arctic-seaice
python -X utf8 -I scripts/regenerate_cases_v2.py --id antarctic-seaice
```

Criterio de aceptación que comprobaré: `min(series.raw) >= 0`, `1987-12` y `1988-01` en `null`,
y OLS con el mismo signo y orden de magnitud que Sen.

### Tarea 3 — LISTO

Dos casos nuevos con los CSV reales de Giovanni (557 meses cada uno, `user_upload`, con la
«URL to Reproduce Results» en `provenance.request_url`):

| caso | veredicto | Sen (°C o mm/día por década) | OLS | periodo |
|---|---|---|---|---|
| amazonia-t2m | SIGNIFICANT_STRONG | 0,186 | 0,191 | 1980-01 → 2026-05 |
| amazonia-prectotcorr | NOT_SIGNIFICANT | ver `analysis.json` | ver `analysis.json` | 1980-01 → 2026-05 |

`amazonia-t2m`: `n_obs` 557, `tests_agree: true`, Mann-Kendall p < 1e-4.

**Aviso para la entrega:** los dos CSV son de **MERRA-2** (vía GES DISC), la misma fuente que
POWER. Sirven como caso de «sube tu propio CSV», no como instrumento distinto. Nadie debe
presentarlos como GPM, MODIS u OMI.

### Tarea 4 — pendiente (dom 10:00)

Nombre y frase de hallazgo por caso, en inglés y español, sacados solo de los números.

### Para el resto del enjambre

- **antigravity-2:** cuando entre el arreglo del −9999, `test_published_nasa_benchmarks` debe
  volver a verde **sin tocar la aserción** (regla 13). Mi regeneración de casos no la afecta.
- **antigravity-1:** avisadme del commit; regenero los dos casos de hielo y publico la evidencia.
- **claude-omni-1:** hay **7** casos en `/api/cases` (antes 5); los dos nuevos son
  `amazonia-t2m` y `amazonia-prectotcorr`, con `provenance.kind = user_upload`.
