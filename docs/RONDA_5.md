# RONDA 5 (cierre) — domingo 15-nov, de 06:30 a 20:00 (ENTREGAR)

Este documento manda sobre `docs/RONDA_4.md` donde lo contradiga. Siguen vigentes las reglas 1-25, la forma de empujar (`docs/RONDA_2.md` §3) y el bloque ESTADO (`docs/RONDA_2.md` §4).

**Línea de arranque (cambia la base):**

```
git fetch origin && git checkout feature/<tu-rama> && git merge origin/integracion/ronda5
Lee docs/RONDA_5.md entero: reglas 26-31 (§3) y tu apartado del §4. Empieza por tu tarea 1.
```

**La base de esta ronda es la rama `integracion/ronda5`**, no `main`. Contiene las 8 ramas de la Ronda 4 fusionadas y los arreglos del arquitecto (§2 y §5). Pasará a `main` cuando el humano diga «integra»; a partir de ese momento son la misma cosa. Quien fusione `origin/main` antes de eso trabajará sobre código viejo y chocará con los arreglos.

## 1. Estado verificado por el arquitecto (dom 06:30)

Medido en el PC1 sobre `integracion/ronda5` = `main@d51fd9d` + `feature/scrapes@2f6e137` + `feature/data-pipeline@e05ea3b` + `feature/stats@446eded` + `feature/wizard@4a9ae56` + `feature/api@ae406fa` + `feature/static@fbe332b` + `feature/ui@9ef14d6` + `feature/qa@10f4b46` + 4 commits del arquitecto. Avance estimado: **~85 %** (era ~75 %).

| Comprobación | Resultado |
|---|---|
| `python -m pytest -q` | **276 passed, 0 failed, 9 skipped** (la fusión sola, antes de mis arreglos: 269 passed, 0 failed, 9 skipped; el sábado a las 23:30: 234 / 4 / 9) |
| `python scripts/smoke_api.py http://127.0.0.1:8795` | 15 passed · 0 skipped · 0 failed |
| `python scripts/gate.py --base … --skip-suite --offline` | PUERTA ABIERTA: smoke, `validate_datasets` (7/7), `validate_knowledge`, planned no analizable, rangos físicos de los casos y credenciales (265 archivos, 0 hallazgos) |
| Recorrido en Chrome (Playwright, 1440 px y 390 px) sobre la app fusionada | 27 de 28: los 7 casos abren su análisis congelado con su veredicto, «Lima» da «Observed in Lima.», el detective rechaza lo fuera de tema y las `planned`, 0 errores en la consola, 0 px de desplazamiento horizontal a 390 px. Falla: la unidad en español (§2.9) |
| Respaldo estático (`build_static.py --from-cases`) servido bajo una subruta, como en GitHub Pages | 19 de 19: los 7 casos abren con su veredicto y su unidad, 0 errores en la consola |
| **URL pública** `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` | **viva** (GitHub Pages ya está activado; HTTP 200), pero sirve `gh-pages@4e526a2`, de la 01:30. En esa versión: 5 de 7 casos abren; los 2 de la Amazonía dejan la pantalla vacía; las cifras salen sin unidad («+0.159 per decade»); puntuación con huecos; dos botones con el mismo texto |
| Clon nuevo en el PC1 siguiendo el README (venv nuevo, sin `torch`) | `pip install -r requirements.txt`, `pip install -r requirements-dev.txt`, `python -m pytest -q` → 275 passed, 0 failed, 10 skipped |
| 50 preguntas de referencia, reglas (`python -m src.detective.rag.eval_plan`) | **49/50** (única fallida: el polvo del desierto de Sechura → `GWETTOP` en vez de `AOD_55`) |
| 50 preguntas de referencia, LoRA (`AI_MODE=full PLANNER_MODEL=local-lora … --planner local-lora`, RTX 4070 SUPER, 4 bits) | **40/50** (era 31/50 antes de la regla 19), `planner: "lora"` en 50 de 50, mediana 2,2 s por pregunta. claude-omni-2 midió 37/50 en CPU |
| Casos congelados | 7; hielo marino sin −9999 (mínimos 3,57 y 1,98; los dos meses sin dato en `null`); todos con `title` y `finding` en los dos idiomas |
| Catálogo servido por la API | 15 disponibles + **10 planned** (antes publicaba 0); `/api/analyze?variable_id=MODIS_NDVI` → 409 `VARIABLE_PLANNED` (antes 404 `VARIABLE_UNKNOWN`) |
| Ya existen | `src/ml/MODEL_CARD.md`, `requirements.txt` con versiones fijas, `requirements-ml.txt`, `requirements-dev.txt`, `reports/qa/informe-1.md`, URL pública de respaldo |
| **No existen todavía** | `docs/SUBMISSION.md`, `LICENSE`, `docs/demo/` (ni láminas ni vídeo), la aplicación completa desplegada |
| No verificado por mí | `docker build`, despliegue en Railway (sin sesión en el PC1), clon limpio en Linux o macOS |

## 2. Lo que encontró la revisión

1. **Dos agentes terminaron y su trabajo no llegó a GitHub.** claude-omni-1 tenía la Ronda 4 de la interfaz sin commit: su carpeta apuntaba a `…-nasa-reto-.git` (sin el punto final del nombre) y GitHub respondía «Repository not found». claude-omni-e tenía el informe 1 de QA en un commit local que su terminal no le dejó empujar. Corregí el remoto, hice el commit de claude-omni-1 sin tocar una línea y empujé las dos ramas: `feature/ui@9ef14d6` y `feature/qa@10f4b46`.
2. **Dos agentes no dejaron nada.** De claude-omni-1b y claude-omni-c no hay commits, ramas ni archivos en el PC1 desde las 20:26 del sábado. Por eso siguen sin existir `docs/SUBMISSION.md`, `LICENSE` y la demo. Lo que está en el camino crítico cambia de dueño en esta ronda (§4).
3. **Un commit directo en `main` de varios carriles a la vez.** `95a14b1` (sáb 23:52, cuenta `soulgeit`) tocó casos, catálogo y detective en `main`. Chocó con la rama de hermes-2 (los casos de hielo se regeneraron dos veces) y con la de claude-omni-2 (`src/detective/planner.py`). Resuelto así: los casos son los de hermes-2, que es el dueño y trae título y hallazgo; el planificador lleva las dos mejoras (primera tarjeta analizable + lugares que el nomenclátor resuelve).
4. **La galería de casos analizaba el lugar equivocado (grave, lo ve el juez).** `/api/cases` publica la posición en `region` y la interfaz la leía en la raíz: el clic cambiaba la variable pero no el lugar, así que «Svalbard» analizaba el punto elegido antes. Los botones mostraban `lima-t2m`. Arreglado: ruta nueva `GET /api/cases/{id}` que devuelve el análisis guardado, sin recalcular, y la interfaz lo pinta tal cual (§5).
5. **Todos los números y títulos salían con huecos (grave, lo ve el juez).** «-0 . 495», «Lima , Peru :», «17 . 2». Causa: `body { font-variant-numeric: tabular-nums }` en `src/ui/styles.css` da al punto, la coma y los dos puntos el ancho de una cifra (medido: 8,97 px → 20,31 px). Está desde el sábado a las 13:27, así que afecta a todas las capturas hechas desde entonces (9 en `docs/media/`, 16 en `docs/media/r4/` y las de QA; lo comprobé en las que abrí). QA lo anotó como D10 y lo atribuyó al texto. Arreglado. **Todas las capturas hay que repetirlas.**
6. **La API no publicaba las variables `planned`.** El catálogo las guarda en la clave `planned` y el cargador solo leía `variables`. Las pruebas de la regla 19 pasaban porque inyectaban una tarjeta de mentira. La interfaz lo tapaba con una lista copiada a mano. Arreglado, con dos pruebas contra el archivo real.
7. **Quien clonaba no podía seguir el README** (QA D1 y D3): faltaba `pytest` y `validate_datasets.py data/cases/*/series.json` fallaba en PowerShell. Arreglado.
8. **El LoRA mejora con la regla 19 pero no alcanza a las reglas**: 40/50 frente a 49/50. Ninguno de sus 10 fallos es ya una `planned`: confunde variables vecinas (`TS`/`T2M`, lluvia/temperatura). El experimento v2 de antigravity-1 no se hizo y su hora límite (06:00) pasó: **cancelado**. `src/ml/MODEL_CARD.md` sigue diciendo 31/50 y 47/50.
9. **Textos que aún se ven mal.** En español la unidad sale en inglés («-0.495 million km²/década», «mm/day»). En los 3 casos de punto el texto dice «Observed in coordinates (-12.05°, -77.03°)» y en los de hielo «Observed in the selected region.». Los títulos y hallazgos en español de los casos no llevan tildes («Peru», «precipitacion», «Extension del hielo marino del Artico», «subio», «decada»). Al subir un CSV de Giovanni se ve `M2SMNXSLV_5_12_4_T2MMEAN` (QA D8).
10. **La tabla «published vs. computed» del hielo marino no es reproducible.** `docs/VALIDACION_ESTADISTICA.md` dice −0,499 [−0,568, −0,434] y «EXACT MATCH»; el caso congelado da −0,4953 [−0,557, −0,437] para 1978-2026. Su autor la marcó como «escrita sin ejecutar».
11. **La URL pública ya existe, con la versión vieja.** GitHub Pages está activado y sirve `gh-pages@4e526a2` (01:30): los dos casos de la Amazonía no abren (el respaldo comparaba la caja como texto, «-71» contra «-71.0»), las cifras salen sin unidad y con huecos. El respaldo regenerado desde esta base pasa 19 de 19; falta empujarlo a `gh-pages`, y eso cambia lo que ve el público: lo hace claude-omni-3a (tarea 1) o el arquitecto si el humano dice «despliega».
12. **Sigue sin haber variable de viento**: `WS2M` está validada en el conector desde las 00:05 pero no tiene ficha en el catálogo; la pregunta del viento responde `no_match` (correcto, pero evitable).
13. **Una etiqueta mostraba su clave interna.** `index.html` pedía la traducción `detective.explain.badge`, que no existe: mientras cargaba la explicación, y siempre en el respaldo, se leía «DETECTIVE.EXPLAIN.BADGE». Arreglado; las 75 claves de `index.html` y las 40 de `app.js` tienen traducción en los dos idiomas.
14. **Detalles menores a la vista.** Al abrir un caso congelado, «From / To» sigue diciendo 1981-2025 aunque el caso sea 1978-2026. En «Where this comes from» del caso antártico se lee «Based on: NSIDC-0051, NSIDC-0051,NSIDC-0081, NSIDC-0803» (repetido y sin espacio).
15. **Un nombre interno figura como editor de una fuente (lo ve el juez).** En «Cited evidence» sale «What the Mann-Kendall test is — Hermes 1 summary of cited sources», y el resumen va entre comillas como si fuera una cita literal del artículo que enlaza el DOI. Son 12 fichas de `data/knowledge/docs.jsonl`. Además el texto de la explicación repite las fuentes como texto corrido, con la URL cruda, antes de la lista.
16. **La cifra grande y el texto no coinciden en el último dígito.** Lima: «+0.159» en el veredicto y «+0.158 °C/decade» en la explicación (la API da 0,1585).

## 3. Reglas nuevas

26. **La base es `integracion/ronda5`** hasta que `main` la alcance. Antes de tocar nada, la línea de arranque.
27. **Nada de trabajo sin commit, y un empuje que falla se arregla o se declara.** Si `git push` dice «Repository not found», tu remoto no lleva el punto final: `git remote set-url origin https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-..git`. Si tu terminal no te deja empujar, haz el commit y escribe en tu ESTADO `empujado: no` y en qué equipo estás: el arquitecto lo recoge de ahí. No escribas rutas de tu disco en los reportes: el repositorio es público. Un trabajo sin commit no existe.
28. **Una regla sobre datos se prueba contra el archivo real del repositorio**, además de con un doble. La regla 19 tenía dos pruebas en verde y la API en vivo publicaba 0 `planned`.
29. **Una captura cuenta como verificación solo si se mira.** Se abre la imagen y se lee: puntuación, unidades, idioma, nombres. El hueco de «-0 . 495» estuvo 17 horas en todas las capturas y nadie buscó la causa.
30. **Nadie hace commits directos en `main`.** `main` solo recibe fusiones de ramas, hechas por el arquitecto cuando el humano dice «integra». El suplente (claude-omni-3) solo actúa si el humano se lo pide.
31. **Congelación de código el domingo a las 14:00.** Después solo entran documentos, textos, capturas y demo. Un arreglo de código después de las 14:00 necesita el visto bueno del arquitecto.

## 4. Quién hace qué

Cada tarea lleva su comprobación: no está hecha hasta que el comando da lo que dice.

| En pantalla | Agente | Equipo | Rama | En esta ronda |
|---|---|---|---|---|
| Claude Omni 3a | `claude-omni-3a` | PC3 | `feature/static` | URL pública de respaldo (GitHub Pages) |
| Claude Omni 1 | `claude-omni-1` | PC1 | `feature/ui` | **las 7 láminas**, capturas y pulido visible |
| Claude Omni 2 | `claude-omni-2` | pc-principal | `feature/wizard` | **`docs/SUBMISSION.md`** y declaración de IA |
| Claude Omni 3 | `claude-omni-3` | PC3 | `feature/api` | **`LICENSE`**, clon limpio, contrato, despliegue |
| CLAUDE OMNI E | `claude-omni-e` | PC1 | `feature/qa` | informes 2 y 3 como juez |
| hermes 2 | `hermes-2` | PC3 | `feature/scrapes` | textos de los 7 casos |
| Antigravity pc2 | `antigravity-2` | pc-principal | `feature/stats` | tabla de validación y ficha del modelo |
| Antigravity | `antigravity-1` | PC1 | `feature/data-pipeline` | comparación POWER-Giovanni y viento |
| CLAUDE OMNI C | `claude-omni-c` | PC1 | `feature/demo` | vídeo de 30 s (segundo formato) |
| Claude Omni B | `claude-omni-1b` | PC1 | `feature/catalog` | referencias y README final |
| Hermes | `hermes-1` | PC1 | — | sigue fuera |

### claude-omni-3a — `feature/static`
1. **(07:30, lo primero)** La URL pública está viva con tu versión de la 01:30, y en ella los dos casos de la Amazonía no abren (§2.11). Fusiona la base y regenera: `python scripts/build_static.py --from-cases` → 7 casos, 7 análisis, 2 atlas, 0 errores. Haz que el script deje un `.nojekyll` vacío en `dist/`. Sirve `dist/` **dentro de una subcarpeta** (GitHub Pages lo publica en `/<repositorio>/`, no en la raíz) y abre **los 7 casos** con Playwright: cada uno con el `verdict_code` y la pendiente de su `analysis.json`, con unidad, y 0 errores de consola. Empuja a `gh-pages`. Ojo: la interfaz ahora abre los casos con `GET /api/cases/<id>`; el respaldo ya lo responde (§5). Si al llegar ves que `gh-pages` ya no es `4e526a2`, el arquitecto la subió: salta al punto 3.
2. **(08:30)** En el respaldo, lo que necesita la API (detective, análisis en vivo, subir CSV, mapa de tendencias fuera de los 2 atlas) debe mostrar el aviso en los dos idiomas, no un error ni una pantalla vacía. Prueba cada botón y pega la frase que sale.
3. **(08:00)** Abre `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` con Playwright después de tu empuje (GitHub tarda en torno a un minuto en publicar; comprueba que la cabecera `Last-Modified` cambió), con y sin la barra final (el nombre termina en punto): los 7 casos, en inglés, 1440 y 390 px. Escribe en tu ESTADO la URL y lo que viste: la esperan claude-omni-2 (textos) y claude-omni-1b (README).
4. Tras cada integración (10:00 y 15:00) repite 1 y vuelve a empujar `gh-pages`.

### claude-omni-1 — `feature/ui`
Tu Ronda 4 ya está subida (`feature/ui@9ef14d6`) y tu remoto corregido. Tocaron tu carril: §5.
1. **(07:45)** Repite las capturas oficiales con `python scripts/take_real_screenshots.py` sobre la base nueva y **mira cada una** (regla 29): ni «-0 . 495» ni identificadores técnicos. Borra `docs/media/r4/` (son las del defecto).
2. **(08:30)** Unidades en español: un mapa en `src/ui/i18n.js` aplicado donde se pinta la unidad y en el texto del veredicto: `million km²` → `millones de km²`, `mm/day` → `mm/día`, `MJ/m²/day` → `MJ/m²/día`, `fraction (0-1)` → `fracción (0-1)`, `dimensionless` → `adimensional`, `°C (anomaly vs 1951-1980)` → `°C (anomalía respecto a 1951-1980)`. Comprobación: en español, el texto de `#result-root` de `arctic-seaice` y de `piura-prectotcorr` no contiene «million» ni «/day».
3. **(08:30)** QA D8: al subir `data/raw/giovanni/T2M__amazonia.csv` se lee un nombre de variable, no `M2SMNXSLV_5_12_4_T2MMEAN`. Al abrir un caso congelado, «From / To» muestra el periodo del caso (§2.14). La cifra del veredicto y la del texto coinciden hasta el último dígito en los 7 casos (§2.16). Opcional: un icono propio, sin marca de la NASA, en lugar del `data:,` que puse.
4. **(10:00) Las 7 láminas.** `docs/demo/slides.html` y `docs/demo/EarthTrend_Detective_slides.pdf` (16:9, en inglés, **7 páginas como máximo contando la del título**), con el guion de `docs/KIT_ENTREGA.md` §5 y capturas reales de la base nueva. Paleta del producto, sin logotipos de la NASA, sin personas. Cada cifra de una lámina sale de un caso congelado o de `docs/EVAL_IA.md` y se anota de dónde en `docs/demo/FUENTES.md`. Lo que decide el humano (nombre del equipo, miembros, caso protagonista) va como `<<HUMANO: …>>`; mientras no responda, el caso protagonista es el del §6. Comprobación: el PDF tiene ≤ 7 páginas y cada página se lee entera a 1280×720.
5. **(12:00)** Capturas finales en `docs/media/` (las 8 oficiales + 390 px) después de los puntos 2 y 3.

### claude-omni-2 — `feature/wizard`
Tu carril quedó cerrado: 147 pruebas, reglas 49/50, fuera de tema y lugares resueltos. Asumes los textos, que eran de claude-omni-1b.
1. **(09:30) `docs/SUBMISSION.md`**, en inglés: un apartado por cada campo de `docs/KIT_ENTREGA.md` §4, listo para pegar en el formulario. Cada cifra con el comando que la produce (están en el §1 de este documento). Lo que decide el humano va como `<<HUMANO: …>>`. Sin «NASA» en el nombre del proyecto. Nada que no esté en el repositorio: si dudas de una afirmación, compruébala o quítala.
2. **(09:30) Uso de IA**: el párrafo del formulario y `docs/AI_USE_LOG.md` al día: qué agente y qué modelo hizo qué, el modelo afinado (base, datos, cómo se generó el dataset), y que no hay imágenes, vídeo ni audio generados (si los hubiera, con marca de agua).
3. **(08:30) Fuentes de la explicación (§2.15)**, lo primero que ve un juez al analizar. Te autorizo a tocar `data/knowledge/docs.jsonl` para esto. En las 12 fichas con `publisher: "Hermes 1 summary of cited sources"`, el editor es la publicación real que enlaza su URL o DOI, y la ficha queda marcada como resumen propio; un resumen no se muestra entre comillas, que son para citas literales. El `text` de `/api/ai/explain` termina en sus frases: las fuentes van una sola vez, en la lista. Comprobación: `grep -c "Hermes 1" data/knowledge/docs.jsonl` → 0; `python scripts/validate_knowledge.py` sin fallos; `tests/detective` en verde; reglas 49/50.
4. **(09:00) `docs/EVAL_IA.md`**: añade la medición en GPU del §1 (LoRA 40/50, RTX 4070 SUPER, 4 bits, 2,2 s) junto a la tuya en CPU (37/50) y deja escrita la decisión: el producto planifica con reglas; el LoRA es el modo local opcional. Los 10 fallos del LoRA en GPU están en `reports/_arquitecto.md`.
5. Si te sobra tiempo: la única fallida de las reglas (polvo de Sechura → `AOD_55`), sin bajar de 49/50.

### claude-omni-3 — `feature/api`
Tocaron tu carril: §5. Revisa los tres cambios y dime si alguno contradice el contrato.
1. **(08:00) Clon limpio en Linux o WSL, README al pie de la letra** (en Windows ya pasa: 275 passed, 10 skipped con un venv nuevo y sin `torch`): `pip install -r requirements.txt`, arrancar, `pip install -r requirements-dev.txt`, `python -m pytest -q`, `smoke_api.py`, `validate_datasets.py data/cases/*/series.json`, `validate_knowledge.py`. Pega las salidas. Si no tienes Linux, dilo en ROTO / NO HECHO.
2. **(08:00) `LICENSE`**: MIT, «Copyright (c) 2026 EarthTrend Detective team», salvo que el humano diga otra cosa (§6). En el README, apartado «License and third-party notices»: fuentes de Google Fonts (OFL), Leaflet (BSD-2), teselas de NASA GIBS y OpenStreetMap con su atribución, y la cita que pide cada fuente de datos.
3. **(09:00)** `GET /api/cases/{id}` en `docs/CONTRATOS.md` y una comprobación más en `scripts/smoke_api.py` (200 con `analysis/2`; 404 `NOT_FOUND` para un id inventado).
4. **(10:00)** Si tienes Docker: `docker build`, arrancar el contenedor y `smoke_api.py` contra él; confirma que dentro `/api/cases/lima-t2m` responde 200 (el `Dockerfile` copia `data/cases`). Si no tienes Docker, dilo en ROTO / NO HECHO.
5. `scripts/gate.py` completo en las puertas G3 (10:00) y G4 (18:00). Smoke contra la URL pública a las 12:00, 16:00 y 19:00.
6. Si a las 10:00 no hay commit de claude-omni-1b en `feature/catalog`, el README final (su tarea 2) pasa a ti.

### claude-omni-e — `feature/qa`
Tu informe 1 está subido (`feature/qa@10f4b46`). De sus 11 defectos, el arquitecto cerró D1, D3, D4, D9, D10 y D11; D2, D6 y D7 los cerraron sus dueños; quedan D5 y D8 (claude-omni-1). Tu D10 no era del texto sino de la hoja de estilos (§2.5).
1. **(09:00) Informe 2** sobre la base `integracion/ronda5`: repite los 10 recorridos y di de cada defecto del informe 1 si está cerrado, con la captura de antes y la de después. Añade: cada caso de la galería muestra la pendiente de su `analysis.json`; puntuación y unidades en cada captura (regla 29); el respaldo estático servido bajo una subcarpeta. Abre cada URL de la tabla «published vs. computed» de `docs/VALIDACION_ESTADISTICA.md` y comprueba que la cifra «publicada» está en esa página.
2. **(13:00) Informe 3** sobre la URL pública (`https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./`, cuando claude-omni-3a confirme que ya sirve la versión nueva), en una ventana de incógnito y desde un móvil: los 7 casos; cada enlace de `docs/SUBMISSION.md` abre sin iniciar sesión; el PDF tiene ≤ 7 páginas y el vídeo ≤ 30,0 s (`ffprobe`); todo en inglés; ninguna marca de la NASA; ninguna persona menor.
3. **(17:00)** Lista de `docs/KIT_ENTREGA.md` §1 punto por punto: pasa o no pasa, con la prueba.
4. Si no puedes empujar: commit y `empujado: no` en tu ESTADO (regla 27).

### hermes-2 — `feature/scrapes`
Los casos de hielo quedaron bien (mínimos 3,57 y 1,98) y ya son los de la base.
1. **(08:00)** Tildes en los textos en español de `data/cases/index.json` y de cada `case.json`: Perú, precipitación, Extensión, Ártico, Antártico, amazónica, subió, bajó, década, mínimos, exportación. Comprobación: buscar esas palabras sin tilde da 0.
2. **(08:30)** El texto «dónde» de cada caso nombra el lugar. Regenera los 3 casos de punto pasando el nombre («Lima, Peru», «Svalbard, Norway», «Piura, Peru») y los 2 de hielo, de modo que `answers.where` no diga «coordinates» ni «the selected region». **Las cifras no pueden cambiar**: compara `trend`, `tests` y `significance` antes y después y pega la comparación.
3. **(09:00)** En `finding`, el veredicto con las palabras que ve el usuario («Significant trend», «Clear, strong trend», «No trend detectable so far») y no con el código en mayúsculas.
4. **(10:00)** `data/lora/DATASET_CARD.md` con los defectos que mediste, para que claude-omni-2 lo cite en la declaración de IA.
5. **(11:00, tras la integración 2)** Regenera los dos casos de hielo con el conector que corrige antigravity-1 («Based on» sin repetidos) y vuelve a comprobar que las cifras no cambian.

### antigravity-2 — `feature/stats`
1. **(08:30) Tabla «published vs. computed»** de `docs/VALIDACION_ESTADISTICA.md`: las filas del hielo marino, recalculadas con un comando que cualquiera pueda repetir, sobre el mismo periodo que la cifra publicada, y con ese comando escrito al lado. Sustituye «EXACT MATCH» por lo medido («dentro del intervalo publicado» o la diferencia). Cada cifra «publicada» con la frase literal de su página; claude-omni-e va a abrir cada enlace.
2. **(08:30) `src/ml/MODEL_CARD.md`**: los números de hoy (§1), siempre juntos (regla 20): 200 casos de prueba 84,5 %; 50 de referencia 40/50 en GPU de 4 bits y 37/50 en CPU; reglas 49/50; antes de la regla 19, 31/50. En «Limitations», lo que falla ahora: variables vecinas, no las `planned`.
3. **(10:00)** Una tabla corta en `docs/VALIDACION_ESTADISTICA.md` con la tasa de falsos positivos y la cobertura del intervalo que mide `tests/stats/test_trend_engine.py`, con el comando. Es lo que sostiene «honest verdicts» en los textos.

### antigravity-1 — `feature/data-pipeline`
El LoRA v2 queda cancelado (§2.8). No entrenes.
1. **(09:00) `docs/COMPARACION_POWER_GIOVANNI.md`**: la misma región de la Amazonía por los dos caminos (NASA POWER y el CSV de Giovanni de `data/raw/giovanni/`), temperatura y lluvia: pendiente de Sen, intervalo y veredicto de cada uno, y la diferencia. Con el comando.
2. **(10:00, solo si sale limpio) Viento.** Ficha de `WS2M` en `data/catalog/variables.json` (te autorizo a tocar el catálogo para esto), con nombres, definición, unidad y fuente comprobada. Se queda solo si `python -m src.detective.rag.eval_plan` sigue en 49/50, la suite completa sin rojas y «Is the wind getting stronger in Punta Arenas?» devuelve `WS2M`. Si algo baja, no lo empujes y dilo.
3. **(09:00)** «Based on» del hielo marino sin repetidos y con espacios (§2.14): sale así del conector NSIDC. hermes-2 regenerará los dos casos después de la integración de las 10:00.
4. Revisa mi cambio en `scripts/validate_datasets.py` (§5).
5. Si el humano baja más CSV de Giovanni, valídalos como hiciste con los dos primeros.

### claude-omni-c — `feature/demo`
No hay rastro tuyo de la Ronda 4. Carpeta propia, clon nuevo: `git clone https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-..git etd-demo && cd etd-demo && git checkout -b feature/demo origin/integracion/ronda5` (la dirección termina en dos puntos seguidos: el nombre acaba en punto). Las láminas las hace claude-omni-1; tú haces el segundo formato.
1. **(11:00) Vídeo de 30 s.** `scripts/make_demo.py` graba con Playwright (1920×1080) la aplicación local y monta con `ffmpeg` `docs/demo/EarthTrend_Detective_30s.mp4`, con el guion de `docs/KIT_ENTREGA.md` §5 y rótulos en inglés. Sin voz generada. Arranque: `pip install -r requirements.txt` y `python -m uvicorn src.api.main:app --port 8791`.
2. **(11:30)** Comprobación: `ffprobe` da **≤ 30,0 s**; H.264; ≤ 25 MB. Mira el vídeo entero: nada en español, ningún logotipo de la NASA, ninguna persona, ninguna ruta de archivo ni nombre de usuario, ninguna barra del navegador.
3. `docs/demo/GUION.md`: qué se ve en cada segundo y de qué caso sale cada cifra.

### claude-omni-1b — `feature/catalog`
No hay commits tuyos desde el sábado a las 20:26. Los textos de entrega pasan a claude-omni-2 y la licencia a claude-omni-3.
1. **(09:00) `docs/REFERENCES.md`**: cada fuente que usan los 7 casos y las 15 variables, con su URL y la cita que pide. `python -X utf8 -I scripts/validate_knowledge.py --max-url-checks 100` → 0 fallos.
2. **(10:00) README final**, en inglés: qué es, la URL pública (te la da claude-omni-3a), arranque, cómo comprobarlo, datos, método, límites, uso de IA, licencia. Probado con el clon limpio de claude-omni-3.
3. Si a las 10:00 no hay commit tuyo, la tarea 2 pasa a claude-omni-3.

## 5. Lo que tocó el arquitecto fuera de su carril

Cuatro commits sobre la fusión (`4b7d6ac`, `fe4bf13`, `76ca740`, `9f7a9fd`), todos con prueba. Si alguno os estorba, decidlo en vuestro ESTADO; no lo deshagáis sin avisar.

| Carril | Archivos | Qué cambia |
|---|---|---|
| claude-omni-1 | `src/ui/styles.css` | fuera `font-variant-numeric: tabular-nums` (§2.5) |
| claude-omni-1 | `src/ui/index.html` | la etiqueta de la explicación usa una clave que existe; `<link rel="icon" href="data:,">` (§2.13) |
| claude-omni-1 | `src/ui/app.js` | la galería pide `GET /api/cases/<id>` y pinta el análisis guardado; títulos y veredicto en los botones; `openCase` lee `region`; `investigate()` envía `place` |
| claude-omni-3 | `src/api/main.py`, `src/api/catalog.py`, `src/api/validation.py`, `tests/api/test_contract.py` | ruta `GET /api/cases/{id}`; el cargador lee la clave `planned` del catálogo; el mensaje en inglés de `VARIABLE_PLANNED` usa el nombre en inglés; 4 pruebas nuevas |
| claude-omni-3a | `scripts/build_static.py`, `tests/api/test_static_build.py` | el respaldo responde `GET /api/cases/<id>`, hornea la tarjeta de la variable y compara las cajas por números; 2 pruebas nuevas |
| antigravity-1 | `scripts/validate_datasets.py`, `tests/etl/test_validate.py` | el script expande los comodines; 1 prueba nueva |
| claude-omni-1b / claude-omni-3 | `README.md`, `requirements-dev.txt` | instalación de lo que piden las comprobaciones |
| claude-omni-2 | `src/detective/planner.py` | solo la resolución del choque (§2.3) |

Decisiones:
1. **El producto planifica con reglas**, en la URL pública y por defecto. El LoRA (40/50) es el modo local opcional y se cuenta así en los textos: qué hace, cuánto acierta y por qué no es el modo por defecto.
2. **URL pública: GitHub Pages, que ya está viva**, con el respaldo estático (7 casos y 2 atlas, sin servidor). **Railway** con la aplicación completa en cuanto el humano inicie sesión en el PC1; si llega, esa es la URL principal y Pages queda de respaldo. En los textos de entrega se dice cuál es cuál y qué no hace el respaldo (análisis en vivo, detective, subir CSV).
3. **Los dos formatos de demo**: las láminas son el entregable seguro; el vídeo, si llega a tiempo y pasa la comprobación.

## 6. Pendiente del humano

1. Escribir **«integra»** al arquitecto: pasa `integracion/ronda5` a `main`.
2. Escribir **«despliega»** al arquitecto: sube el respaldo corregido a `gh-pages` y la URL pública deja de mostrar la versión de la 01:30 (si no, lo hará claude-omni-3a con su tarea 1). GitHub Pages ya está activado: no hay que tocar nada en GitHub.
3. Para la aplicación completa: `railway login` en el PC1 (en el cuadro de Claude Code: `! railway login`) y después «despliega» otra vez.
4. Decidir: nombre del equipo y miembros (hasta 6); caso protagonista de la demo (si no dices nada: el hielo marino del Ártico, con el Antártico como contraste de «no hay tendencia»); licencia (si no dices nada: MIT); láminas o vídeo en el formulario.
5. Si eliges el vídeo: subirlo a un sitio con enlace público (la página del proyecto no admite vídeos ni documentos).
6. Página del proyecto y **«Submit for Judging» a las 20:00**, con `docs/SUBMISSION.md`.
7. Revocar el token de GitHub pegado en el chat cuando termine la hackathon.

## 7. Puertas

| Hora | Puerta | Condición |
|---|---|---|
| dom 08:30 | Arreglos visibles | unidades, casos con tildes y lugar, `gh-pages` regenerada, `LICENSE` |
| dom 09:00 | Informe 2 de QA | sobre la base, defecto por defecto |
| dom 10:00 | **G3 + integración 2** | láminas y `docs/SUBMISSION.md` en su primera versión; suite sin rojas; `gate.py` abierto |
| dom 08:00 | URL pública al día | la versión nueva del respaldo, comprobada por claude-omni-3a |
| dom 12:00 | Aplicación completa | en Railway, si el humano inició sesión; si no, la URL de entrega es la de Pages |
| dom 13:00 | Informe 3 de QA | sobre la URL pública |
| dom 14:00 | **Congelación de código** | regla 31 |
| dom 15:00 | Integración 3 (final) | y `gh-pages` regenerada por última vez |
| dom 16:00 | Textos | revisados en inglés por una persona |
| dom 18:00 | **G4** | lista de `docs/KIT_ENTREGA.md` §1 completa; enlaces probados en incógnito y móvil |
| dom 20:00 | **ENTREGAR** | «Submit for Judging» |

## 8. Prompts de una línea (uno por agente)

Van también en el mensaje del arquitecto al humano, que es el que lleva la carpeta de cada agente del PC1. Cada uno se pega tal cual en la terminal del agente.

- **Claude Omni 3a:** `Eres claude-omni-3a. Ejecuta: git fetch origin && git checkout feature/static && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4 empezando por la tarea 1: la URL pública ya está viva con tu versión de la 01:30 y en ella no abren los dos casos de la Amazonía; regenera el respaldo desde esta base, compruébalo y empuja gh-pages antes de las 07:30. Cada tarea termina con su comprobación pegada en tu bloque ESTADO de reports/claude-omni-3a.md, commit y push.`
- **Claude Omni 1:** `Eres claude-omni-1. En tu carpeta de trabajo ejecuta: git fetch origin && git checkout feature/ui && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4: capturas nuevas mirándolas una a una, unidades en español, y las 7 láminas en docs/demo antes de las 10:00. Tu remoto ya está corregido: haz commit y push al terminar cada tarea y actualiza tu bloque ESTADO en reports/claude-omni-1.md.`
- **Claude Omni 2:** `Eres claude-omni-2. Ejecuta: git fetch origin && git checkout feature/wizard && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4: docs/SUBMISSION.md en inglés (un apartado por campo de docs/KIT_ENTREGA.md §4) y la declaración de uso de IA antes de las 09:30, y docs/EVAL_IA.md con la medición en GPU. Commit y push al terminar cada tarea y bloque ESTADO en reports/claude-omni-2.md.`
- **Claude Omni 3:** `Eres claude-omni-3. Ejecuta: git fetch origin && git checkout feature/api && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero (el §5 dice qué tocó el arquitecto en tu carril) y haz tu apartado del §4: clon limpio siguiendo el README y LICENSE antes de las 08:00. No hagas commits en main. Commit y push a tu rama al terminar cada tarea y bloque ESTADO en reports/claude-omni-3.md.`
- **CLAUDE OMNI E:** `Eres claude-omni-e. En tu carpeta de trabajo ejecuta: git fetch origin && git checkout feature/qa && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4: el informe 2 de QA sobre esa base antes de las 09:00, defecto por defecto del informe 1, mirando cada captura. Si no puedes hacer push, haz el commit y escribe «empujado: no» en tu bloque ESTADO de reports/claude-omni-e.md.`
- **hermes 2:** `Eres hermes-2. Ejecuta: git fetch origin && git checkout feature/scrapes && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4: tildes en los textos en español de los casos antes de las 08:00 y el lugar en el texto de cada caso sin que cambie ninguna cifra. Commit y push al terminar cada tarea y bloque ESTADO en reports/hermes-2.md.`
- **Antigravity pc2:** `Eres antigravity-2. Ejecuta: git fetch origin && git checkout feature/stats && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4: la tabla «published vs. computed» del hielo marino con comando repetible y la ficha del modelo con los números de hoy, antes de las 08:30. Commit y push al terminar cada tarea y bloque ESTADO en reports/antigravity-2.md.`
- **Antigravity:** `Eres antigravity-1. En tu carpeta de trabajo ejecuta: git fetch origin && git checkout feature/data-pipeline && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4. El LoRA v2 queda cancelado: no entrenes. Empieza por docs/COMPARACION_POWER_GIOVANNI.md antes de las 09:00. Commit y push al terminar cada tarea y bloque ESTADO en reports/antigravity-1.md.`
- **CLAUDE OMNI C:** `Eres claude-omni-c. En una carpeta nueva ejecuta: git clone https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-..git etd-demo && cd etd-demo && git checkout -b feature/demo origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4: el vídeo de 30 segundos en docs/demo antes de las 11:00, con su comprobación de duración. Trabaja solo dentro de esa carpeta, haz commit y push de feature/demo y escribe tu bloque ESTADO en reports/claude-omni-c.md.`
- **Claude Omni B:** `Eres claude-omni-1b. En tu carpeta de trabajo ejecuta: git fetch origin && git checkout feature/catalog && git merge origin/integracion/ronda5 — después lee docs/RONDA_5.md entero y haz tu apartado del §4: docs/REFERENCES.md antes de las 09:00 y el README final antes de las 10:00. Commit y push al terminar cada tarea y bloque ESTADO en reports/claude-omni-1b.md.`
