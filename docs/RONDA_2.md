# RONDA 2 — Reglas nuevas, estado real y pendientes

**Auditoría del arquitecto: sábado 14-nov, 17:00 (hora de Perú). Entrega: domingo 15-nov, 20:00.**
Este archivo **manda** sobre `prompts/00_LEER_PRIMERO.md` y sobre tu prompt individual cuando choquen.
Para leerlo sin fusionar nada: `git fetch origin && git show origin/main:docs/RONDA_2.md`

Línea de arranque que el humano pega a cada agente:

```
Eres <AGENTE>. Ronda 2. Ejecuta: git fetch origin && git show origin/main:docs/RONDA_2.md
Léelo completo: manda sobre lo anterior. Cumple las reglas del §2 y haz TUS pendientes del §6, en orden.
Al terminar cada tarea: commit solo de tus carpetas, push a tu rama y bloque ESTADO en reports/<tu-nombre>.md (§4).
```

## 1. Dónde estamos: ~55 %

| Parte | Avance | Dónde vive | Comentario |
|---|---|---|---|
| Datos reales (POWER, GISTEMP, NSIDC, parser Giovanni) | 90 % | `main` | Falta: CSV de Giovanni (lo exporta el humano) |
| Motor estadístico v2 | 80 % | `feature/stats` | Sin integrar en `main` |
| API v2 por contrato | 75 % | `feature/api` | 158 pruebas en verde en su rama; sin desplegar |
| Interfaz v2 | 70 % | `feature/ui` | **Nunca se ejecutó contra la API v2** |
| RAG + guardián | 70 % | `feature/wizard` | R4 y R5 parciales |
| Catálogo y corpus | 90 % | `feature/catalog` | — |
| Casos, atlas y dataset LoRA | 65 % | `feature/scrapes` | Casos con la estructura vieja del análisis |
| **LoRA entrenado** | 30 % | — | **No hay modelo entrenado** (ver hallazgo 2) |
| **Integración en `main`** | 25 % | — | Hallazgo 1 |
| **Despliegue público** | 0 % | — | — |
| **Entrega (página, vídeo o láminas, textos en inglés)** | 15 % | `docs/KIT_ENTREGA.md` | Solo borradores |

Las piezas están construidas en un ~80 %; lo que falta es **juntarlas, probarlas juntas y publicarlas**.

### Hallazgos (con evidencia)

1. **El trabajo no está junto.** Seis ramas sin fusionar y todas chocan con `main`. En `main` hay una API, un motor y una interfaz
   **fuera de contrato** (`/api/analyze_real`; `src/ui/app.js:260` llama a `http://127.0.0.1:8000`) hechos fuera de carril, mientras las
   versiones por contrato y con pruebas siguen en `feature/api`, `feature/stats` y `feature/ui`. Hay duplicados: 2 motores, 2 API, 2 interfaces,
   3 corpus de conocimiento, 2 datasets LoRA y 2 instancias de un mismo agente empujando a la misma rama.
2. **La evaluación del LoRA es simulada.** `src/ml/eval_lora.py` no ejecuta ningún modelo: `predict_base_model` y `predict_lora` parten de la
   respuesta correcta (`gold_plan`) y la copian o degradan. Las cifras «LoRA 100 %» de `reports/lora_eval_benchmark.json`,
   `src/ml/MODEL_CARD.md` y `reports/antigravity-2.md` **no son mediciones** y quedan **retiradas**: no se citan en ningún sitio.
   No existe adaptador entrenado; el cuaderno de Colab y `train_standalone.py` que cita el reporte no están en la rama.
3. **La interfaz v2 lleva resultados de muestra escritos a mano.** La captura `docs/media/verdict_view.png` muestra «+0.31 °C per decade»
   y dos citas fijas; el motor real da +0,16 °C/década para Lima. Ese texto no puede existir en el producto.
4. **Reportes incompletos:** solo 2 de 7 están en `main`; varios dicen «LISTO» con `Rama@commit: (pendiente de commit)`.
5. **Autoría ilegible:** varios agentes comitean con la misma identidad, así que no se puede saber quién hizo qué.

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
8. **Capturas e imágenes** solo de la aplicación real con datos reales, indicando la URL y la hora. Las de `docs/media/` actuales no se usan.
9. **Fallo ajeno que encuentres:** no lo arregles; descríbelo con el comando que lo reproduce (como hicieron Antigravity 1 y Claude Omni 3
   con la sustitución silenciosa por muestras). Ese es el comportamiento correcto.
10. Siguen vigentes las 14 reglas de `prompts/00_LEER_PRIMERO.md` (cero datos inventados, la IA no produce cifras, secretos solo en `.env`…).

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

## 4. Nota de estado (para que el arquitecto y los demás tengan contexto)

Tu archivo `reports/<tu-nombre>.md` **empieza** con este bloque. Se **reescribe** cada vez (no se acumula); el historial va debajo.
Máximo 15 líneas. El arquitecto lee solo este bloque de cada agente con `bash scripts/estado.sh`.

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

## 5. Versiones vigentes (qué gana en cada choque)

| Carpeta | Versión vigente | Se descarta |
|---|---|---|
| `src/etl/`, `tests/etl/`, `scripts/validate_datasets.py` | la de `main` (Antigravity 1) | la otra instancia (queda en `feature/data-pipeline-antigravity1-backup`) |
| `src/stats/`, `tests/stats/`, `docs/VALIDACION_ESTADISTICA.md` | `feature/stats` (Antigravity 2) | el motor de `495d7d5`/`dadf053` que hoy está en `main` |
| `src/api/`, `tests/api/`, `scripts/smoke_api.py` | `feature/api` (Claude Omni 3) | la API de `main` con `/api/analyze_real` |
| `src/ui/` | `feature/ui` (Claude Omni 1) | la interfaz de `main` (`d2656b4`) |
| `src/detective/`, `tests/detective/` | `feature/wizard` (Claude Omni 2) | `src/detective/wizard.py` |
| `data/catalog/`, `data/knowledge/`, `scripts/validate_knowledge.py`, `docs/REFERENCES.md` | `feature/catalog` (Hermes 1, `6796fb6`) | las copias de `main` (`ae4a495`) y de `feature/ui` (`34e576a`) |
| `data/cases/`, `data/atlas/`, `data/lora/`, `scripts/build_*.py`, `scripts/freeze_case.py` | `feature/scrapes` (Hermes 2) | `data/lora/` y `src/ml/generate_lora_dataset.py` de `feature/stats` |
| `src/ml/` (entrenar y servir) | `feature/stats` (Antigravity 2) | la evaluación simulada y su JSON |

**La integración la hace `cfable` en la rama `integracion/ronda2`.** Cuando `main` la incluya se avisa por SwarmChat con «INTEGRACIÓN LISTA».
Hasta entonces: no fusiones `origin/main` si te da conflictos y no integres por tu cuenta.

## 6. Pendientes por agente (en orden)

### Antigravity 1 — datos (`feature/data-pipeline`)
1. Tras «INTEGRACIÓN LISTA»: comprobar que `get_series` y `get_grid` sirven a la API v2 y retirar los adaptadores
   (`get_power_point_series`, `get_power_regional_series`) si ya nada los importa.
2. D5: en cuanto el humano deje CSV en `data/raw/giovanni/`, convertirlos y validarlos. Objetivo: 2 variables de misión (GPM y MODIS u OMI).
3. Precalentar la caché de los casos de demostración. Una sola instancia: la segunda se detiene.

### Antigravity 2 — estadística y LoRA (`feature/stats`)
1. **Urgente:** reescribir `src/ml/eval_lora.py` para que las predicciones salgan de inferencia real (Ollama o `transformers`);
   si no hay modelo, el script termina con «modelo no disponible» y no escribe cifras. Quitar las cifras retiradas de `MODEL_CARD.md` y de tu reporte.
2. Entrenar el LoRA **de verdad** con el dataset de Hermes 2 (`data/lora/`, 2558/509/452). Dónde: lo decide el humano (§7).
   Entregar adaptador, registro de entrenamiento y evaluación real de reglas vs. base vs. LoRA.
3. `docs/VALIDACION_ESTADISTICA.md`: cada cifra «publicada» con su URL; sustituir «coincidencia exacta» por el valor calculado y el rango citado.
   Marcar como `live` las pruebas que necesitan red.
4. Borrar tu generador y tu `data/lora/` duplicados: el dataset oficial es el de Hermes 2.

### Claude Omni 1 — interfaz (`feature/ui`)
1. Tras «INTEGRACIÓN LISTA»: ejecutar la interfaz contra la API real y **eliminar todo resultado, texto o cita escritos a mano** en `app.js`.
   Con la API caída se muestra un error claro, nunca cifras de muestra.
2. Recorrer con datos reales: punto, mapa de tendencias, comparar y subir CSV. Selector de variables desde `/api/catalog/variables`.
3. Capturas nuevas solo de la app real (regla 8). Retirar `scripts/build_knowledge_corpus.py` y el corpus de tu rama (carril de Hermes 1).

### Claude Omni 2 — detective con IA (`feature/wizard`)
1. Conectar con el catálogo, el gazetteer y las 50 preguntas doradas definitivas; regenerar la tabla de `docs/EVAL_IA.md`.
2. Cerrar R4 (`geocode`) y R5 (`scout` con el ETL real).
3. `system_prompt` idéntico a `data/lora/system_prompt.txt`. Mientras no haya LoRA real, `plan()` responde con `mode: "rules"` o `"llm"` y lo dice.

### Claude Omni 3 — API y despliegue (`feature/api`) · integrador suplente
1. Tras «INTEGRACIÓN LISTA»: `scripts/smoke_api.py` contra `main`; `/api/cases` desde `data/cases/`; catálogo desde `variables.json`, no la semilla.
2. **A5 esta noche:** URL pública (el inicio de sesión lo hace el humano). Después, `smoke_api.py` contra esa URL.
3. A6: respaldo estático regenerado con los casos reales.

### Hermes 1 — catálogo y conocimiento (`feature/catalog`)
1. Tras «INTEGRACIÓN LISTA»: `python scripts/validate_knowledge.py` en verde sobre `main`.
2. Añadir al corpus las dos fuentes verificadas por Claude Omni 2 (Acker et al. 2009 y la ficha de SWOT de la CSA).
3. `docs/REFERENCES.md` en inglés, listo para pegar en la página del proyecto.

### Hermes 2 — casos, atlas y dataset (`feature/scrapes`)
1. Regenerar los 5 casos con el `analyze_series` definitivo (`analysis/2`) y crear `data/cases/index.json`.
2. Rehacer el atlas con el `analyze_grid` real. Tu `scripts/validate_datasets.py` es antiguo: vale el de `main`.
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
| G2 | sáb 23:30 | `main` integrado corre de punta a punta con datos reales y hay URL pública |
| Noche | — | Entrenamiento del LoRA y atlas |
| G3 | dom 10:00 | IA (RAG y, si existe, LoRA medido de verdad) funcionando en la URL pública |
| Congelación | dom 14:00 | Solo arreglos de errores |
| G4 | dom 18:00 | Página del proyecto, vídeo o láminas y textos en inglés |
| **Entrega** | **dom 20:00** | **Submit for Judging** |
