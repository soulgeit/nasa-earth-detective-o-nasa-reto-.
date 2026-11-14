# 00 · LEER PRIMERO (todos los agentes)

Eres parte del enjambre que construye **EarthTrend Detective** para el NASA Space Apps Challenge 2026
(reto: *crear una herramienta que seleccione variables de ciencias de la Tierra, visualice cómo cambian
en el tiempo y determine qué cambia, dónde, cuánto y si el cambio es «significativo»*).

- **Entrega: domingo 15-nov-2026, 23:59 hora local. Entregamos a las 20:00.** Después no se puede tocar nada.
- Lee, en este orden: este archivo → `docs/CONTRATOS.md` → tu prompt (`prompts/0X_*.md`). El plan completo está en `docs/PLAN_GANADOR.md`.
- Antes de empezar: `git fetch origin && git merge origin/main` en tu rama.

## Cómo nos califican (rúbrica oficial 2026, 1 a 5 por criterio)

| Criterio | Qué mira el juez | Qué significa para tu trabajo |
|---|---|---|
| **Impacto** | Problema grande, alcance amplio | Sirve a un estudiante real, en español e inglés, sin instalar nada |
| **Creatividad** | Algo no intentado o una mejora con sentido | Mapa de tendencias, «años que faltan para estar seguros», detective con IA que cita fuentes |
| **Validez** | Ciencia correcta, factible, completo, **usable** | Datos NASA reales, estadística correcta y contrastada, cero números inventados |
| **Relevancia** | Responde al reto y **usa datos NASA como núcleo, no de adorno** | Las 4 preguntas (qué, dónde, cuánto, ¿significativo?) con datos traídos de la NASA en vivo |
| **Presentación** | Historia clara: reto, solución, por qué importa | Textos en inglés, capturas buenas, demo de 30 s o 7 láminas |

## Reglas de oro (romper una = tu trabajo no se integra)

1. **Cero datos inventados.** Prohibido `random`, senos, series «de ejemplo» o valores escritos a mano fuera de `tests/`.
   Todo número que vea un usuario sale de una respuesta real de la NASA guardada con su URL, fecha y hash (`provenance`, ver contratos).
   El repo tenía 4 series sintéticas etiquetadas como MODIS/SWOT/MERRA-2/GLDAS: **se eliminan**, no se reutilizan.
2. **Sin sustituciones silenciosas.** Si falta un dato, error explícito con código. Nunca devuelvas otro archivo «parecido».
3. **Primero verifica, después programa.** Llama al servicio real, guarda la respuesta en `tests/fixtures/real/` y escribe el parser contra esa muestra.
   No te fíes de tu memoria para URLs, nombres de parámetros, firmas de librerías ni identificadores de modelos: compruébalo en la documentación vigente.
4. **La IA no produce números ni coordenadas.** Las cifras salen del motor estadístico; las coordenadas, del gazetteer o del clic en el mapa.
   El modelo de lenguaje solo elige variables, extrae el lugar como texto y explica con las cifras que se le dan.
5. **Nada de citas inventadas.** Toda fuente del corpus se descarga de verdad (HTTP 200) y el texto guardado sale de esa página.
6. **Quédate en tu carril.** Solo tocas tus carpetas (tabla en `docs/CONTRATOS.md`). Si necesitas cambiar un contrato, propónlo en tu reporte; no lo cambies por tu cuenta.
7. **«Hecho» = con evidencia.** Cada tarea terminada lleva en `reports/<tu-nombre>.md` el comando ejecutado y su salida real. Sin evidencia no está hecho.
8. **Todo texto visible va en inglés y español** (la entrega se juzga en inglés).
9. **Secretos solo en `.env`** (nunca en git, reportes ni chat). Usa `.env.example` como guía.
10. **Sin marca NASA.** No uses logotipos, insignias ni parches de misión de la NASA, ni «NASA» en el nombre del producto. Sí se atribuye: «Data: NASA POWER…».
11. **Marca lo hecho con IA.** La regla oficial exige reconocer el código y los datos generados con IA, en el texto y en los metadatos:
    pon como primera línea de cada archivo de código que generes el comentario `SI-assisted: <agente> (<modelo>)`, y añade tu fila en `docs/AI_USE_LOG.md`
    (agente, modelo, archivos, qué hiciste) en cada entrega. No lo omitas: es requisito de la entrega.
12. **Límite de 20 minutos por bloqueo.** Si algo no cede en 20 min, escribe el bloqueo en tu reporte, avisa por el canal y pasa al plan B que indica tu prompt.
13. **No toques procesos ni modelos del humano.** No detengas ni descargues modelos de Ollama, ni mates procesos, ni instales software global. La GPU está ocupada: pide ventana.
14. **No desactives la verificación TLS** (`-k`, `verify=False`). En esta PC `curl` falla con algunos dominios `*.nasa.gov`/spaceappschallenge.org por un certificado raíz que falta; usa Python (`requests`/`httpx`, con `certifi` actualizado).

## Git

- Trabajas en tu rama `feature/*` (tabla en contratos). Commits pequeños, `git push` frecuente. **Nunca a `main`.**
- Mensajes: `feat(stats): ...`, `fix(etl): ...`, `test(api): ...`, `docs: ...`.
- No reescribas historia ni fuerces push. No borres archivos de otro carril.

## Reporte (obligatorio al cerrar cada tarea)

Añade al final de `reports/<tu-nombre>.md`:

```
## <ID de tarea> — LISTO | BLOQUEADO | PARCIAL  (fecha y hora)
Rama@commit: feature/xxx@abc1234
Qué quedó: ...
Evidencia: <comando>  →  <salida real, recortada>
Falta / riesgos: ...
Necesito de otros: ...
```

Y avisa por el canal: `swarmchat send "#general" "[<tu-nombre>] <ID> LISTO feature/xxx@abc1234 — ver reports/<tu-nombre>.md"`.
Si no tienes `swarmchat`, basta con el reporte y el push.

## Entorno verificado el 14-nov-2026 (hora de Perú)

- PC1: Windows 11, Python 3.12.10, solo `numpy` instalado → **crea un venv** (`python -m venv .venv`) y usa `requirements.txt`.
- PC1 tiene RTX 4070 SUPER (12 GB) pero **casi llena**: hay un modelo de 35B cargado en Ollama de forma permanente. Ollama 0.40 disponible.
- Verificado con llamadas reales (muestras en `tests/fixtures/real/`):
  - **NASA POWER** (sin cuenta): `https://power.larc.nasa.gov/api/temporal/monthly/point?...` → 200 en 2 s, 1981-01 a 2025-12.
    Claves `YYYYMM`; **la clave `YYYY13` es el valor anual: se descarta**; faltante = `-999`.
  - **NASA POWER regional** (caja 4°×4°, un parámetro): 200 en 1,6 s, 63 celdas de 0,5°×0,625°, cada una con su serie.
  - **GISTEMP** `https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz` → 200.
  - **NSIDC Sea Ice Index v4** `https://noaadata.apps.nsidc.org/NOAA/G02135/north/monthly/data/N_09_extent_v4.0.csv` → 200.
  - **ORNL MODIS** `https://modis.ornl.gov/rst/api/v1/...` → **502/timeout hoy**: no dependas de él.
  - **Hydrology Data Rods** (GES DISC) → **descontinuado**, no lo uses.
  - GPM, GLDAS, AIRS, OMI y MODIS mensuales requieren cuenta Earthdata: llegan como **CSV de Giovanni** que exporta el humano.
