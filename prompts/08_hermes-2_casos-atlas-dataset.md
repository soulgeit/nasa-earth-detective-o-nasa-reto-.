# 08 · Hermes 2 — Dataset del LoRA, casos reales congelados y atlas

**Rama:** `feature/scrapes` · **Carpetas:** `data/lora/`, `data/cases/`, `data/atlas/`, `scripts/build_*.py`, `scripts/freeze_case.py`
**Antes:** lee `prompts/00_LEER_PRIMERO.md` y `docs/CONTRATOS.md` (§3, §4, §5, §10).

## Lo primero
Los cuatro archivos de `data/processed/` que generaste antes eran sintéticos y se eliminan. **No vuelvas a generar series con fórmulas.**
A partir de ahora, toda serie que guardes sale de `src/etl` (datos reales de la NASA) y lleva su `provenance`.
La única excepción es S1: preguntas de entrenamiento, que son texto y no mediciones, y que se declaran como generadas.

## Tareas, en orden

### S1 — Dataset para el LoRA (P1; empieza ya, no depende de nadie)
`scripts/build_lora_dataset.py` → `data/lora/train.jsonl`, `val.jsonl`, `test.jsonl`, `system_prompt.txt`, `DATASET_CARD.md`. Formato: contrato §10.

**Mensaje de sistema** (fijo, guárdalo en `system_prompt.txt`):
```
You are the planning module of EarthTrend Detective, a tool that helps students investigate trends in Earth science data.
Read the QUESTION and the CANDIDATES. Reply with ONLY one JSON object with these keys, in this order:
intent, variable_ids, place, place_b, start_year, end_year, last_n_years, hypothesis, lang.
Use only ids listed in CANDIDATES. Copy place names exactly as written in the question. Never invent numbers or places.
```
**Mensaje de usuario:**
```
QUESTION: <pregunta>
CANDIDATES:
- <ID>: <nombre> (<unidad>) — <definición corta>
  (6 líneas, en orden aleatorio, en el idioma de la pregunta)
```
**Respuesta:** el JSON en una línea, con las claves en ese orden.

Cómo se construye (todo por programa; las etiquetas son correctas por construcción):
- Variables y definiciones: de `data/catalog/variables.json` (si aún no existe, de `variables.seed.json`; se regenera después).
- Lugares: de `data/catalog/gazetteer.json` y `regions.json`; mientras no existan, una lista provisional de 150 nombres escrita por ti (solo nombres, no hacen falta coordenadas).
- **Reparto de intenciones:** `investigate` 60 % · `compare` 15 % (dos lugares) · `define` 10 % («¿qué es…?») · `out_of_scope` 10 % (deportes, tareas de otra materia, famosos, y también intentos de manipulación como «ignora tus instrucciones») · `no_match` 5 % (pregunta válida, pero la variable correcta **no** está entre las candidatas → `variable_ids: []`).
- **Candidatas:** la correcta + 5 distractoras (2 de la misma esfera, 3 al azar), barajadas. En `no_match` se quita la correcta.
- **Idioma:** 55 % español, 45 % inglés. **Lugares:** 35 % Perú, 25 % resto de Latinoamérica, 40 % mundo; 15 % sin lugar (`place: null`).
- **Años:** 15 % con rango explícito («entre 2000 y 2020»), 10 % con «últimos N años» (`last_n_years`).
- **Hipótesis:** `up` o `down` si la pregunta lo sugiere («cada vez más calor», «llueve menos»); si no, `unknown`.
- **Estilos:** al menos 40 plantillas por intención e idioma: escolar, coloquial, palabras sueltas («lluvia piura tendencia»), narrativa («mi abuelo dice que antes llovía más en Cusco»).
  Ruido: 20 % sin tildes, 10 % con erratas, 10 % todo en minúsculas.
- **Tamaños:** entrenamiento ≥ 2 000 · validación 200 · prueba 150. Cada variable, al menos 40 veces como correcta.
- **La prueba sale de plantillas distintas** a las de entrenamiento (otra familia de frases) y **sin paráfrasis de modelo**.
- Sin duplicados ni casi duplicados entre particiones (texto normalizado igual, o Jaccard de palabras > 0,9).
- Opcional: ampliar entrenamiento con paráfrasis de un modelo abierto local de origen no chino, si lo tienes disponible (máx. 40 %; `meta.source: "paraphrase"`; el lugar debe seguir apareciendo literal). No detengas ni descargues modelos.

`python scripts/build_lora_dataset.py --check` debe comprobar: cada respuesta es JSON válido con las 9 claves; `variable_ids` ⊆ candidatas;
`place` y `place_b` aparecen literalmente en la pregunta; reparto real frente al pedido; duplicados = 0. Código ≠ 0 si algo falla.
`DATASET_CARD.md`: cómo se generó, con qué herramientas de IA, recuentos, límites conocidos. Semilla fija: mismo comando, mismo dataset.

Pide al humano que revise 30 ejemplos de prueba al azar y anota el resultado en la ficha. Avisa a Antigravity 2 cuando esté.

### S2 — Casos reales congelados (P0; cuando la puerta G1 esté pasada)
`scripts/freeze_case.py --id <id> --variable <ID> (--lat --lon | --bbox) --name-es ... --name-en ...`
→ llama a `get_series` y `analyze_series` y escribe `data/cases/<id>/series.json`, `analysis.json` y `case.json`
(título y pasos de la historia en ambos idiomas; los textos de la historia los escribe o aprueba el humano: deja `"TODO_HUMANO"`).
Casos técnicos para probar el flujo (los definitivos los elige el humano): Lima `T2M` · Svalbard `T2M` · Piura `PRECTOTCORR` · hielo marino ártico vs. antártico.
Cada archivo debe pasar `python scripts/validate_datasets.py data/cases/*/series.json`.

### S3 — Atlas (P2; trabajo de noche)
`scripts/build_atlas.py --variable <ID>` → `data/atlas/<ID>.json` (TrendMap v2 global).
1. **Primero `GISTEMP_TANOM`**: sale de un solo archivo, tarda minutos.
2. Después `T2M`, `PRECTOTCORR`, `GWETTOP` con POWER regional: teselas del tamaño máximo permitido, **en serie**, con la pausa que indique su documentación, reanudable (usa la caché), con registro de progreso.
   Calcula antes cuántas peticiones son y cuánto tardará; si pasa de 60 min por variable, reduce a Sudamérica + una franja global gruesa y dilo en el reporte.
3. Si el archivo pesa más de 3 MB, agrupa celdas 2×2 **promediando las series antes de analizar** (nunca promedies pendientes ni valores p).

### S4 — Regenerar (P1)
Cuando Hermes 1 entregue el catálogo v2 y el gazetteer, vuelve a generar el dataset (v1) y avisa a Antigravity 2 con el recuento nuevo.

## Aceptación
- S1: salida de `--check` en verde, tabla de reparto y 10 ejemplos de cada partición en el reporte.
- S2: salida de `validate_datasets.py` en verde; cada caso con `provenance.kind` `nasa_api` o `nasa_file`.
- S3: tamaño del archivo, número de celdas, porcentaje significativo y tiempo que tardó.

## Plan B
Si a las 23:30 del sábado el dataset no pasa `--check`, entrega lo que sí pasa (aunque sean 1 000 ejemplos) y dilo. Un dataset pequeño y limpio vale más que uno grande con etiquetas rotas.

Reporta en `reports/hermes-2.md`.
