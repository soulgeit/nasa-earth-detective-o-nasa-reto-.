# RONDA 2 — Reglas nuevas, estado real y pendientes

**Auditoría del arquitecto: sábado 14-nov, 17:00 · Integración en `main`: 17:45 (hora de Perú). Entrega: domingo 15-nov, 20:00.**
Este archivo **manda** sobre `prompts/00_LEER_PRIMERO.md` y sobre tu prompt individual cuando choquen.

Línea de arranque que el humano pega a cada agente:

```
Eres <AGENTE>. Ronda 2. Ejecuta: git fetch origin && git checkout <TU-RAMA> && git merge origin/main
Lee completo docs/RONDA_2.md: manda sobre lo anterior. Cumple las reglas del §2 y haz TUS pendientes del §6, en orden.
Al terminar cada tarea: commit solo de tus carpetas, push a tu rama y bloque ESTADO en reports/<tu-nombre>.md (§4).
```

## 1. Dónde estamos: ~60 %

| Parte | Avance | Comentario |
|---|---|---|
| Datos reales (POWER, GISTEMP, NSIDC, parser Giovanni) | 90 % | Falta: CSV de Giovanni (lo exporta el humano) |
| Motor estadístico v2 | 80 % | Veredicto incoherente en un caso real (§6, Antigravity 2) |
| API v2 por contrato | 80 % | `smoke_api.py` 10/10 en local; sin desplegar |
| Interfaz v2 | 75 % | Ya corre contra la API real; la gráfica dibuja mal la banda (§6, Claude Omni 1) |
| RAG + guardián | 65 % | Cita fuentes que no vienen al caso (§6, Claude Omni 2) |
| Catálogo y corpus | 85 % | 15 variables; el validador da 8 fallos de URL |
| Casos, atlas y dataset LoRA | 65 % | Casos con la estructura vieja; falta `index.json` |
| **LoRA entrenado** | 30 % | **No hay modelo entrenado** (hallazgo 2) |
| **Integración en `main`** | 70 % | Hecha a las 17:45: las seis ramas están en `main` |
| **Despliegue público** | 0 % | — |
| **Entrega (página, vídeo o láminas, textos en inglés)** | 15 % | Solo borradores en `docs/KIT_ENTREGA.md` |

Evidencia de la integración (rama `integracion/ronda2`, ya en `main`):

```
$ python -m pytest -q                      →  196 passed, 2 failed, 9 skipped   (las 2 rojas: §6, Claude Omni 2)
$ python scripts/smoke_api.py http://127.0.0.1:8791   →  10 passed · 0 failed
$ GET /api/analyze?variable_id=T2M&lat=-12.05&lon=-77.03
  schema analysis/2 · 540 meses (1981-01 → 2025-12) · provenance.kind nasa_api · sha256 b7b97924…
  Theil-Sen +0.1585 °C/década, IC 95 % [+0.031, +0.281] · MK (Hamed-Rao) p = 3.9e-05 · t de MCO p = 0.072
```

### Hallazgos de la auditoría (con evidencia)

1. **El trabajo no estaba junto** (resuelto con la integración). Había seis ramas sin fusionar que chocaban con `main`, y en `main` una API,
   un motor y una interfaz fuera de contrato (`/api/analyze_real`; la interfaz llamaba a `http://127.0.0.1:8000`) hechos fuera de carril.
   Duplicados encontrados: 2 motores, 2 API, 2 interfaces, 3 corpus, 2 datasets LoRA y 2 instancias de un mismo agente en la misma rama.
2. **La evaluación del LoRA era simulada.** `src/ml/eval_lora.py` no ejecutaba ningún modelo: `predict_base_model` y `predict_lora` partían de la
   respuesta correcta (`gold_plan`) y la copiaban o degradaban. Las cifras «LoRA 100 %» **no son mediciones** y quedan **retiradas**.
   No existe adaptador entrenado. No se integraron en `main`: `src/ml/eval_lora.py`, `src/ml/serve.py`, `src/ml/MODEL_CARD.md`,
   `tests/ml/test_lora_pipeline.py` ni `reports/lora_eval_benchmark.json` (siguen en `feature/stats` para rehacerlos).
3. **Faltaba una dependencia:** `python-multipart` no estaba en `requirements.txt`; sin ella la API no arranca en una máquina limpia
   (36 pruebas daban error). Añadida.
4. **Dos desajustes de contrato entre carriles** (arreglados, una línea cada uno): el gazetteer publica `cities` y el detective leía `places`;
   la API responde `{"places": [...]}` en `/geocode` y la interfaz leía `results`. Por eso el buscador no encontraba ni «Lima».
5. **Reportes incompletos:** varios dicen «LISTO» con `Rama@commit: (pendiente de commit)`.
6. **Autoría ilegible:** varios agentes comitean con la misma identidad; no se puede saber quién hizo qué.

Corrección a la primera versión de este documento: los resultados de muestra de la interfaz («+0.31 °C per decade») solo aparecen con
`?dev=fixture` y llevan aviso; no salen en el uso normal. Aun así hay que sacarlos del código que se publica (§6, Claude Omni 1).

## 2. Reglas nuevas

1. **Una instancia por rol y una carpeta por agente.** Nunca dos agentes en el mismo directorio ni con el mismo nombre.
   Si el humano lanza un refuerzo, recibe un nombre nuevo (p. ej. `antigravity-1b`) y un encargo concreto del §6.
2. **Carril estricto.** Solo tocas tus carpetas (`docs/CONTRATOS.md` §1). Si necesitas algo de otro carril, **no lo escribes tú**:
   lo pides en tu bloque ESTADO («Necesito de») y por SwarmChat. Lo hecho fuera de carril se descarta al integrar (§5).
3. **Nada simulado como resultado.** Una cifra de rendimiento, una captura o una tabla solo existen si salieron de ejecutar el sistema real,
   y junto a ellas va el comando. Los dobles de prueba viven solo en `tests/`. Si no pudiste ejecutarlo, el estado es `ESCRITO`, no `LISTO`.
4. **Tres estados, no uno:** `VERIFICADO` (lo ejecuté y pego la salida) · `ESCRITO` (código hecho, sin ejecutar de punta a punta) · `BLOQUEADO`.
   «Listo» significa `VERIFICADO` **en `main` integrado**, no en tu rama.
5. **Solo el integrador escribe en `main`.** Integrador: `cfable` (arquitecto). Suplente si no está en línea: `claude-omni-3`, y nadie más.
   Nadie fusiona ramas ajenas en la suya: lo ajeno te llega al fusionar `origin/main`.
6. **Nota de estado obligatoria** al cerrar cada tarea y antes de parar por cualquier motivo (§4). Sin nota, la tarea no existe.
7. **Commits firmados y pequeños.** Última línea del mensaje: `Agente: <tu-nombre> (<modelo>)`. Prohibido `git add -A` y `git add .`:
   añade rutas concretas de tu carril. Prohibido `--force` y reescribir historia.
8. **Capturas e imágenes** solo de la aplicación real con datos reales y sin `?dev=fixture`, indicando la URL y la hora.
   Las de `docs/media/` actuales no se usan en la entrega.
9. **Fallo ajeno que encuentres:** no lo arregles; descríbelo con el comando que lo reproduce (como hicieron Antigravity 1 y Claude Omni 3
   con la sustitución silenciosa por muestras). Ese es el comportamiento correcto.
10. **Si cambias la forma de un JSON que otro consume** (claves, envoltura), avisa antes y actualiza `docs/CONTRATOS.md` vía el arquitecto.
11. Siguen vigentes las 14 reglas de `prompts/00_LEER_PRIMERO.md` (cero datos inventados, la IA no produce cifras, secretos solo en `.env`…).

## 3. Cómo empujar (todos tienen GitHub configurado)

```bash
git fetch origin
git checkout feature/<tu-rama>
git merge origin/main            # si da conflicto FUERA de tu carril: git merge --abort y avisa; no lo resuelvas tú
#   ... trabajas SOLO en tus carpetas ...
python -m pytest -q <tus pruebas>            # pega la salida real en tu nota
git add <rutas de tu carril> reports/<tu-nombre>.md
git commit -F <archivo con el mensaje>       # asunto: feat(<carril>): <ID> <qué>   ·  última línea: Agente: <nombre> (<modelo>)
git push origin feature/<tu-rama>            # NUNCA a main, NUNCA con --force
swarmchat send "#general" "[<tu-nombre>] <ID> VERIFICADO feature/<rama>@<hash> — nota en reports/<tu-nombre>.md"
```

- Empuja al menos cada 60 minutos aunque no hayas terminado (estado `ESCRITO`): lo que no está en GitHub no existe.
- Si `git push` es rechazado: `git fetch origin && git merge origin/feature/<tu-rama>` y vuelve a empujar. Nunca `--force`.
- Tokens y claves: solo en `.env` o en el gestor de credenciales de git. **Nunca en el chat, en un commit, en un reporte ni en la URL del remoto.**
- Entorno: `python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt pytest httpx`.

## 4. Nota de estado (para que el arquitecto y los demás tengan contexto)

Tu archivo `reports/<tu-nombre>.md` **empieza** con este bloque. Se **reescribe** cada vez (no se acumula); el historial va debajo.
Máximo 15 líneas. El arquitecto lee solo este bloque de cada agente con `bash scripts/estado.sh`. Ejemplo real: `reports/_arquitecto.md`.

```
<!-- ESTADO:INICIO -->
## ESTADO — <tu-nombre> — <AAAA-MM-DD HH:MM hora de Perú>
Rama@commit: feature/xxx@abc1234 · empujado: sí|no
VERIFICADO: <tarea> → <comando> → <salida resumida en una línea>
ESCRITO (sin ejecutar de punta a punta): ...
ROTO / NO HECHO: ...
Siguiente paso: ...
Necesito de: <agente o humano>: <qué exactamente>
Avisos para otros carriles: ...
<!-- ESTADO:FIN -->
```

## 5. Versiones vigentes (lo que quedó en `main` al integrar)

| Carpeta | Versión que quedó | Se descartó |
|---|---|---|
| `src/etl/`, `tests/etl/`, `scripts/validate_datasets.py` | Antigravity 1 (`feature/data-pipeline`) | la otra instancia (queda en `feature/data-pipeline-antigravity1-backup`) |
| `src/stats/`, `tests/stats/`, `docs/VALIDACION_ESTADISTICA.md` | Antigravity 2 (`feature/stats`) | el motor de `495d7d5`/`dadf053` |
| `src/api/`, `tests/api/`, `scripts/smoke_api.py` | Claude Omni 3 (`feature/api`) | la API con `/api/analyze_real` |
| `src/ui/` | Claude Omni 1 (`feature/ui`) | la interfaz de `d2656b4` |
| `src/detective/`, `tests/detective/` | Claude Omni 2 (`feature/wizard`) | — (`wizard.py` sigue ahí: borrarlo) |
| `data/catalog/`, `data/knowledge/`, `scripts/validate_knowledge.py`, `docs/REFERENCES.md` | Hermes 1 (`feature/catalog`, `6796fb6`) | las copias de `ae4a495` y de `feature/ui` (`34e576a`) |
| `data/cases/`, `data/atlas/`, `data/lora/`, `scripts/build_*.py`, `scripts/freeze_case.py` | Hermes 2 (`feature/scrapes`) | `data/lora/` de `feature/stats` |
| `src/ml/` | solo `train_lora.py` y `generate_lora_dataset.py` | la evaluación simulada (hallazgo 2) |

`main` desciende de todas las ramas `feature/*`: tu `git merge origin/main` debe ser un avance rápido, sin conflictos.
El estado anterior de `main` quedó en la etiqueta `antes-integracion-ronda2`.
Cambios del integrador dentro de carriles ajenos (mínimos, para que el conjunto arranque): `requirements.txt` (+`python-multipart`),
`src/detective/gazetteer.py:73`, `src/ui/app.js` (lectura de `/geocode`) y dos pruebas de `tests/test_system.py` que apuntaban a funciones
del conector descartado.

## 6. Pendientes por agente (en orden). Lo marcado «visto» sale de ejecutar `main` integrado el sábado a las 17:40

### Antigravity 1 — datos (`feature/data-pipeline`)
1. Retirar los adaptadores `get_power_point_series` / `get_power_regional_series` cuando nada los importe (hoy los usa `tests/test_system.py`).
2. D5: en cuanto el humano deje CSV en `data/raw/giovanni/`, convertirlos y validarlos. Objetivo: 2 variables de misión (GPM y MODIS u OMI).
   Hoy el catálogo solo tiene 15 variables de POWER, GISTEMP y NSIDC: el reto nombra MODIS, OMI, AIRS, GPM y GLDAS.
3. Precalentar la caché de los casos de demostración. Una sola instancia: la segunda se detiene.

### Antigravity 2 — estadística y LoRA (`feature/stats`)
1. **Visto, veredicto incoherente:** Lima `T2M` sale `SIGNIFICANT_STRONG` con `tests_agree: true`, pero la t de MCO ajustada da p = 0,072,
   su IC 95 % incluye el cero y la detectabilidad dice que faltan 13,3 años. «Fuerte» exige que **todas** las pruebas coincidan y que
   haya años suficientes; si no, baja de escalón y añade el aviso `TESTS_DISAGREE`. Prueba que lo fije con la muestra real de Lima.
2. **Visto, textos:** `answers.what` dice «T2M se encuentra aumentando» (usa el identificador) y `answers.where` dice «Observado en None».
3. **Urgente:** rehacer `eval_lora.py` con inferencia real (Ollama o `transformers`); sin modelo, termina con «modelo no disponible» y no escribe cifras.
4. Entrenar el LoRA **de verdad** con `data/lora/` de Hermes 2 (4323/814/632). Dónde: lo decide el humano (§7).
   Entregar adaptador, registro de entrenamiento y evaluación real de reglas vs. base vs. LoRA.
5. `docs/VALIDACION_ESTADISTICA.md`: cada cifra «publicada» con su URL. Borrar tu generador de dataset duplicado.

### Claude Omni 1 — interfaz (`feature/ui`)
1. **Visto, gráfica:** en «Valores mensuales» la línea de Sen se dibuja en torno a 0 y la banda va de −26 a +24, mientras los datos están en 18–22 °C.
   La línea debe ir a la altura de los datos y la banda debe ser el abanico del IC de la pendiente.
2. Sacar del código publicado las funciones `devFixture*` (resultados y citas escritos a mano); en producción no existe `?dev=fixture`.
3. Mostrar el nombre de la variable y del lugar, no «T2M» ni «None». Los «?» sueltos de ayuda no se ven como ayuda.
4. Recorrer con datos reales: mapa de tendencias, comparar, subir CSV y «Pregúntale al Detective». Capturas nuevas (regla 8).

### Claude Omni 2 — detective con IA (`feature/wizard`)
1. **Visto, citas que no vienen al caso:** al explicar la temperatura de Lima cita cinco fichas de aerosoles y GISTEMP, con identificadores
   internos (`[var-aod_55-es]`) y todas rotuladas «NASA Earth Observatory». Recuperar por la variable analizada, citar título y URL reales,
   y no volcar los fragmentos enteros en el párrafo. En modo `extractive` el rótulo no puede decir «síntesis asistida por IA».
2. **2 pruebas rojas:** `tests/detective/test_pipeline.py` espera `MODIS_NDVI`, que ya no está en el catálogo, y el planificador responde `EVLAND`.
   Lo correcto ante una variable que no tenemos es `intent: "no_match"` y decirlo, no la más parecida.
3. Usar `alt_names` y `ascii` del gazetteer (8109 ciudades). Cerrar R5 (`scout` con el ETL real). Borrar `src/detective/wizard.py`.
4. `system_prompt` idéntico a `data/lora/system_prompt.txt`. Mientras no haya LoRA real, `plan()` responde con `mode: "rules"` o `"llm"`.

### Claude Omni 3 — API y despliegue (`feature/api`) · integrador suplente
1. **A5 esta noche:** URL pública (el inicio de sesión lo hace el humano). Después, `smoke_api.py` contra esa URL.
2. `/api/cases` da 503 hasta que exista `data/cases/index.json` (Hermes 2). Pasar a `analyze_series` el nombre del lugar y de la variable.
3. A6: respaldo estático regenerado con los casos reales. Fijar versiones en `requirements.txt`.

### Hermes 1 — catálogo y conocimiento (`feature/catalog`)
1. **Visto:** `python scripts/validate_knowledge.py` → 8 fallos (p. ej. 404 en `https://glossary.ametsoc.org/wiki/biome`). Una fuente que no abre no se cita.
2. Decidir con el arquitecto cómo se declaran las variables de Giovanni aún no disponibles (hoy el catálogo las omite y el detective no puede decir «esa no la tenemos»).
3. Añadir las dos fuentes verificadas por Claude Omni 2 (Acker et al. 2009 y la ficha de SWOT de la CSA). `docs/REFERENCES.md` en inglés.

### Hermes 2 — casos, atlas y dataset (`feature/scrapes`)
1. Regenerar los 5 casos con el `analyze_series` definitivo (`analysis/2`) y crear `data/cases/index.json`.
2. Rehacer el atlas con el `analyze_grid` real, que ya está en `main`.
3. El caso Ártico/Antártico se presenta tal cual salió: el Ártico baja con claridad y el Antártico no es significativo.

## 7. Pendientes del humano

1. Pegar a cada agente la línea de arranque de arriba y dejar **una sola instancia por rol**.
2. Decidir dónde se entrena el LoRA: liberar la GPU del PC unas horas, o Google Colab (GPU T4 gratuita).
3. Cuenta Earthdata y 2 CSV de Giovanni en `data/raw/giovanni/` (pasos en su `README.md`).
4. Inicio de sesión en el hosting para la URL pública.
5. Decisiones de `docs/PLAN_GANADOR.md` §7 (casos, historia, nombre, vídeo o láminas).

## 8. Puertas que quedan

| Puerta | Hora | Qué debe ser verdad |
|---|---|---|
| G2 | sáb 23:30 | Defectos «vistos» del §6 cerrados y URL pública funcionando |
| Noche | — | Entrenamiento del LoRA y atlas |
| G3 | dom 10:00 | IA (RAG y, si existe, LoRA medido de verdad) funcionando en la URL pública |
| Congelación | dom 14:00 | Solo arreglos de errores |
| G4 | dom 18:00 | Página del proyecto, vídeo o láminas y textos en inglés |
| **Entrega** | **dom 20:00** | **Submit for Judging** |
