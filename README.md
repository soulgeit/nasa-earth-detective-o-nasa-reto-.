# EarthTrend Detective — NASA Space Apps Challenge 2026

> **Status (14 Nov 2026): rebuild in progress.** The first prototype in this repository used **synthetic placeholder series**
> (files under `data/processed/` and the client-side generator in `src/ui/app.js`). They are **not NASA data**, they are being removed,
> and no result derived from them should be quoted. The rebuild uses real NASA data with visible provenance. See `docs/PLAN_GANADOR.md`.

A tool that turns students into data detectives: pick a place on Earth, retrieve real NASA Earth science data for it, see how it changed over time,
and get an honest answer to four questions: **what** is changing, **where**, **how much**, and whether the change is **statistically significant**.

Herramienta para que un estudiante investigue un lugar del planeta con datos reales de la NASA y obtenga una respuesta honesta:
qué cambia, dónde, cuánto y si el cambio es estadísticamente significativo.

## Documentos

| Documento | Para qué |
|---|---|
| `docs/PLAN_GANADOR.md` | Diagnóstico, producto, arquitectura, calendario y riesgos |
| `docs/CONTRATOS.md` | Esquemas de datos, firmas, API y carriles de cada agente |
| `docs/KIT_ENTREGA.md` | Requisitos oficiales, criterios, borradores y demo |
| `TASKS.md` | Tablero, puertas y línea de arranque de cada agente |
| `prompts/` | Un prompt por agente (`00_LEER_PRIMERO.md` es común) |
| `docs/AI_USE_LOG.md` | Registro de uso de IA (requisito del reto) |

## Datos (verificados el 14-nov-2026)

- **NASA POWER** (MERRA-2, CERES/SRB), mensual 1981–2025, por punto o por caja, sin cuenta.
- **NASA GISTEMP v4**, anomalías de temperatura en rejilla desde 1880.
- **NSIDC Sea Ice Index v4**, hielo marino ártico y antártico.
- **Giovanni (GES DISC)**: GPM IMERG, GLDAS, AIRS, OMI y MODIS mediante CSV exportado (`data/raw/giovanni/README.md`).

Muestras reales para desarrollo y pruebas: `tests/fixtures/real/`.

## Ejecutar en local (se actualizará en la puerta G1)

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python src/api/main.py           # http://localhost:8000  (documentación en /docs)
```

## Uso de IA

Este proyecto se desarrolla con asistencia de agentes de IA bajo la dirección del equipo. El detalle está en `docs/AI_USE_LOG.md`.
