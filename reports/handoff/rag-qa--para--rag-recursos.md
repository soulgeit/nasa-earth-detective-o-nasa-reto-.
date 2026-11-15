# Handoff: rag-qa -> rag-recursos

**Fecha:** 2026-11-15 14:30 hora de Perú  
**De:** `rag-qa`  
**Para:** `rag-recursos`  
**Asunto:** Auditoría QA de los 13 enlaces oficiales del reto (§8 de `docs/RONDA_7.md`)

Hola equipo de `rag-recursos`, desde `rag-qa` realizamos una auditoría de disponibilidad HTTP y validación online sobre la lista de recursos de §8 para que preparen sus fragmentos sin sorpresas en `validate_fragments.py`:

---

### Resumen del Muestreo de Enlaces (§8)

| URL | Estado HTTP | En `docs.jsonl` | Recomendación QA |
|---|:---:|:---:|---|
| `https://giovanni.gsfc.nasa.gov/giovanni/` | **200 OK** | No | Crear documento nuevo (`res-recursos-giovanni-...`). |
| `https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series` | **200 OK** | No | Crear documento nuevo (`res-recursos-gesdisc-hydrology-...`). |
| `https://appeears.earthdatacloud.nasa.gov/` | **200 OK** | No | Crear documento nuevo (`res-recursos-appeears-...`). |
| `https://www.ncei.noaa.gov/cdo-web/` | **200 OK** | No | Crear documento nuevo (`res-recursos-noaa-cdo-...`). |
| `https://ntrs.nasa.gov/api/citations/20090042747/downloads/20090042747.pdf` | **200 OK** | No | Documento PDF NASA disponible para cita/resumen. |
| `https://climexp.knmi.nl/` | **200 OK** | No | Crear documento nuevo (`res-recursos-knmi-climexp-...`). |
| `https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b` | **403 Forbidden** | No | **Alerta:** Medium bloquea peticiones de bots. Obligatorio resumen propio (`is_quotation: false`, `summary_by: "rag-recursos"`). Si `validate_fragments.py --online` falla por 403, avisar a `rag-qa`. |
| `https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance` | **200 OK** | No | Resumen propio con derechos de autor respetados. |
| `https://donnees-data.asc-csa.gc.ca/en/dataset/rcm` | **SSLError** | No | **Alerta:** Cadena de certificados del gobierno canadiense no está en el bundle por defecto de `certifi`. En modo `--online` lanzará `SSLError`. Considerar enlace alternativo o avisar a QA. |
| `https://geo.ca/` | **200 OK** | No | Crear documento nuevo. |
| `https://www.asc-csa.gc.ca/eng/satellites/swot/` | **200 OK** | **SÍ (`res-csa-swot`)** | **Alerta:** Ya existe en `data/knowledge/docs.jsonl`. Si lo mejoran, deben incluir `"supersedes": ["res-csa-swot"]` y `"supersedes_reason": "..."` según §2 de `RONDA_7.md`. No duplicar. |
| `https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp` | **200 OK** | No | Crear documento nuevo. |
| `https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial` | **200 OK** | No | Crear documento nuevo tutorial SAR. |

---

### Acciones Solicitadas
1. Tener en cuenta el `supersedes` para `https://www.asc-csa.gc.ca/eng/satellites/swot/` para no crear duplicados no justificados.
2. Formatear resúmenes propios con `is_quotation: false` para Medium y Statsig.
