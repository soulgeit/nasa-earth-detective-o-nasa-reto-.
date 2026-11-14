# KIT DE ENTREGA — NASA Space Apps 2026

Fuente: *Project Submission Guide* y *Judging & Awards Guide* 2026 (publicadas el 13-nov-2026, leídas el 14-nov).
Los borradores en inglés son puntos de partida: **el equipo los reescribe con su voz y solo deja lo que de verdad esté construido.**

## 1. Requisitos oficiales (lista de comprobación)

- [ ] **«Submit for Judging» antes del domingo 15-nov, 23:59**, hora local del evento (en el evento Universal: hora de residencia del dueño del equipo). Lo guardado después no se evalúa. **Nuestro objetivo: 20:00.**
- [ ] Equipo: todos inscritos en el **mismo** evento local, ninguno en lista de espera, **máximo 6**. No se pueden añadir miembros tras el cierre.
- [ ] Todos los campos obligatorios completos y **en inglés** (página y materiales enlazados).
- [ ] **Demo**: vídeo de **30 s o menos**, *o* presentación de **hasta 7 láminas** (contando título e introducción). Pasarse del límite = fuera del juicio global.
      El vídeo puede hablarse en español **con subtítulos en inglés**; las láminas, en inglés.
- [ ] Enlaces **públicos**, sin contraseña, permiso ni registro. Probados en ventana de incógnito.
- [ ] Usar **al menos un dato o recurso de la NASA** (requisito para premio global) y detallarlo.
- [ ] Listar **todos** los datos, recursos, herramientas, código, textos e imágenes usados, aunque sean libres.
- [ ] Marcar las dos casillas: términos y condiciones, y trabajo original con referencias completas.
- [ ] **Uso de IA** (el formulario la llama «Super Intelligence (SI)»): decir dónde y cómo se usó. Imágenes y vídeos generados → **marca de agua visible**.
      Audio, **código y datos** generados → reconocerlo en el texto descriptivo y en los metadatos.
      La IA no debe ser quien idee cómo resolver el reto. El contenido generado no puede usar logotipos, banderas ni identificadores de misión de la NASA.
- [ ] **Ninguna persona menor de 18 años** en imágenes, vídeo o audio de la demo ni del proyecto.
- [ ] Sitio web propio: pedir la clasificación de **FortiGuard Web Filter** (recomendado por la guía para que los jueces puedan abrirlo).
- [ ] La página admite imágenes (JPG, PNG, GIF, hasta 10 MB); no admite subir vídeos ni documentos.
- [ ] La guía indica que hay una revisión de elegibilidad sobre vínculos con entidades chinas. Si alguien del equipo tiene dudas, consultar al Local Lead.

Fechas: nominados globales 3-dic-2026 · finalistas 17-dic-2026 · ganadores 26-ene-2027.

## 2. Lo que más pesa
La guía lo dice: **la mayor parte de la evaluación se basa en la página del proyecto**; la demo suma sobre todo en Presentación. Dedica al texto y a las capturas el tiempo que merecen.

| Criterio (1–5) | Qué debe ver el juez en la página | Evidencia que aportamos |
|---|---|---|
| Impact | Problema grande y público amplio | Cualquier estudiante, cualquier lugar, dos idiomas, gratis, sin instalar |
| Creativity | Algo no intentado | Veredicto honesto con «años que faltan», mapa con control de falsos positivos, detective con IA que cita y no inventa cifras |
| Validity | Ciencia sólida, completo, usable | `docs/VALIDACION_ESTADISTICA.md`: tabla «publicado vs. calculado», cobertura y falsos positivos medidos |
| Relevance | Responde al reto con datos NASA como núcleo | Las 4 preguntas del reto, las fuentes que nombra, procedencia visible en cada resultado |
| Presentation | Historia clara | Un caso local contado de principio a fin, capturas limpias, demo dentro del límite |

**Premios a los que apuntamos** (definiciones oficiales): *Best Use of Science* («best and most valid use of the scientific method»),
*Best Use of Data* («best makes space data accessible»), y *Local Impact* si el caso local es fuerte.

## 3. Qué enseñan los ganadores de 2025

| Premio | Equipo (país) | Qué hizo | Lección para nosotros |
|---|---|---|---|
| Best Use of Science | SpaceGenes+ (Alemania) | Motor de conocimiento de biología espacial | Rigor y método por delante |
| Best Use of Data | Resonant Exoplanets (EE. UU.) | IA que busca exoplanetas en datos de telescopios | La IA al servicio de los datos, con resultados medibles |
| Best Use of Technology | Twisters (México) | SkySense: pronóstico hiperlocal y riesgo para actividades | Datos NASA convertidos en una respuesta concreta para una persona |
| Galactic Impact | Astro Sweepers (Universal) | Riesgo de basura espacial por objeto | Un número claro y accionable |
| Best Mission Concept | PureFlow (Brasil) | Diseñador 3D de hábitats | Herramienta interactiva pulida |
| Most Inspirational | Photonics Odyssey (India) | Internet satelital como infraestructura pública | Visión grande, contada con claridad |
| Best Storytelling | HerCode Space (Universal) | Cuento ilustrado sobre clima espacial | La historia importa tanto como la técnica |
| Global Connection | Gaia+LEO (EE. UU.) | Optimización de centros de datos orbitales | Fundamento matemático explícito |
| Art & Technology | Zumorroda-X (Egipto) | Minijuegos de agricultura con datos NASA | Aprender jugando |
| **Local Impact** | **QUEÑARIS (Perú)** | Bosques de queñua y agua en Arequipa con satélite, drones e IA | **Un problema local real, contado por quienes lo viven** |

## 4. Campos del formulario (borradores en inglés, para reescribir)

**Project Name** — `EarthTrend Detective` (sin «NASA» en el nombre).

**High-Level Project Summary** (qué, cómo responde al reto, por qué importa):
> EarthTrend Detective turns students into data detectives. Choose any place on Earth, or ask a question in English or Spanish, and the tool retrieves real NASA Earth science data for that place, shows how it has changed over [N] years, and answers the four questions of the challenge: what is changing, where, how much, and whether the change is statistically significant. It gives honest verdicts: a trend is called significant only when [three independent tests agree after correcting for autocorrelation], and when it is not, the tool estimates how many more years of data would be needed. A trend map shows where the same variable rises in one region and falls in another. [An assistant grounded in cited NASA sources suggests what to investigate and never generates a number.]

**Detailed Project Description** (estructura sugerida):
1. *What it does* — recorrido de un estudiante por el caso local (con capturas).
2. *How it works* — datos (fuentes y acceso), estadística (pruebas y correcciones), mapa (significancia por celda), asistente (recuperación con fuentes, modelo afinado, guardián de cifras).
3. *Why you can trust it* — tabla de validación contra valores publicados; tasa de falsos positivos medida; procedencia de cada dato.
4. *Who benefits* — estudiantes y docentes; bilingüe; funciona sin cuentas.
5. *What we hope to achieve* — [lo decide el equipo].
6. *Tools* — lenguajes, librerías y modelos realmente usados (de `docs/REFERENCES.md`).
7. *Limitations* — lo que no hace todavía. Decirlo sube la nota de Validez, no la baja.

**NASA Data** (solo lo usado de verdad, con nombre exacto):
> NASA POWER Monthly API v[versión] (MERRA-2 meteorology; CERES/SRB radiation), parameters [lista]; NASA GISS Surface Temperature Analysis (GISTEMP v4); NASA GES DISC Giovanni area-averaged time series of [GPM IMERG / GLDAS / AIRS / OMI / MODIS: producto y versión]; [NASA GIBS imagery]. For each result the app shows the exact query, retrieval date and citation.

**Space Agency Partner Data and Other References** — de `docs/REFERENCES.md`. Si se usa GPM IMERG, mencionar que GPM es una misión conjunta NASA–JAXA. NSIDC Sea Ice Index, GeoNames, librerías y modelos con sus licencias.

**Use of Super Intelligence (SI)** — respuesta honesta y completa; base en `docs/AI_USE_LOG.md`:
> Yes. (1) SI coding agents ([lista de herramientas y modelos]) wrote most of the code under the team's direction; SI-generated files are identified in their headers and in docs/AI_USE_LOG.md. (2) The product includes a small open-weight language model fine-tuned with LoRA to turn questions into structured plans, trained on a question dataset generated by script (see DATASET_CARD.md), and a retrieval pipeline over cited sources. (3) [Imágenes, vídeo o audio generados: ninguno / con marca de agua.] The idea, the choice of cases and the scientific decisions were made by the team.

Esa última frase tiene que ser verdad: por eso las decisiones de `docs/PLAN_GANADOR.md` §7 son vuestras.

## 5. Demo (elegir una)

**Vídeo, 28 s** (estructura que propone la guía; grabar pantalla real, sin menores, subtítulos en inglés):

| Tiempo | Voz | Pantalla |
|---|---|---|
| 0:00–0:02 | «We are [equipo], from [ciudad], Peru.» | Título |
| 0:02–0:05 | «Is it really raining less in my town, or does it just feel that way?» | La pregunta escrita en el buscador |
| 0:05–0:10 | «EarthTrend Detective: ask the Earth a question, get an honest answer.» | Mapa, clic en el lugar |
| 0:10–0:20 | «It pulls decades of real NASA data for any place, measures the trend, and runs three tests before it says "significant", or tells you how many more years of data you would need.» | Serie → recta con banda → sello del veredicto → mapa de tendencias |
| 0:20–0:28 | «Any student can check a claim about our planet with NASA's open data, in English or Spanish.» | Comparación de dos regiones y dirección web |

**Láminas, 7** (en inglés, poco texto, capturas reales):
1. Título: proyecto, lema, equipo, miembros, reto. 2. El problema y las 4 preguntas. 3. La solución en una captura.
4. Datos reales de la NASA: fuentes y procedencia. 5. Estadística honesta: veredicto, validación, «años que faltan».
6. Dónde cambia: mapa y tendencias opuestas; el asistente con fuentes. 7. Impacto y próximos pasos, con el enlace.

## 6. Última hora (domingo)
- 14:00 congelación · 16:00 textos en inglés revisados por una persona · 17:00 capturas y demo subidas · 18:00 enlaces probados en incógnito y desde el móvil
- 19:00 repaso de la lista de la sección 1 en voz alta · **20:00 «Submit for Judging»** · comprobar el banner de confirmación y descargar el certificado.
- Se puede reenviar hasta el cierre: solo cuenta lo último guardado. No tocar nada pasadas las 23:00.
