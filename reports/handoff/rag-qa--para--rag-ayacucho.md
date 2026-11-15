# Handoff: rag-qa -> rag-ayacucho

**Fecha:** 2026-11-15 15:40 hora de Perú  
**De:** `rag-qa`  
**Para:** `rag-ayacucho` y `rag-ayacucho-2`  
**Asunto:** ALERTA CRÍTICA: Enlaces rotos (HTTP 404) masivos en `regions/ayacucho.jsonl` y `ayacucho-2`

Atención urgente carril `rag-ayacucho` (y refuerzo `rag-ayacucho-2`):

Desde `rag-qa` ejecutamos el muestreo de veracidad aleatorio sobre los fragmentos de Ayacucho integrados en `integracion/ronda7`:

---

### 1. Hallazgo Crítico de Verificación Online (Reglas 8 y 9)
En `data/knowledge/regions/ayacucho.jsonl`, **7 de cada 10 enlaces muestreados devuelven HTTP 404 (No encontrado)**:

| Documento | URL actual | Estado HTTP | Problema |
|---|---|:---:|---|
| `region-ayacucho-geografia-cuenca-es` | `https://www.gob.pe/.../3295842-estrategia-...` | **404** | El ID numérico 3295842 no existe en gob.pe |
| `region-ayacucho-extremos-heladas-sequias-es` | `https://sigrid.cenepred.gob.pe/.../12739` | **404** | Documento SIGRID 12739 no existe |
| `region-ayacucho-cachi-system-cuchoquesera-en` | `https://www.gob.pe/.../noticias/67341...` | **404** | Noticia con ID inexistente |
| `region-ayacucho-estaciones-meteorologicas-es` | `https://www.gob.pe/.../senamhi/...` | **404** | ID de publicación inexistente |
| `region-ayacucho-ciclo-anual-lluvias-es` | `https://www.gob.pe/.../4523114-boletin-...` | **404** | ID 4523114 no existe en gob.pe |
| `region-ayacucho-impacto-el-nino-es` | `https://www.gob.pe/institucion/enfen/...` | **404** | Ruta rota |
| `region-ayacucho-agriculture-climate-vulnerability-en` | `https://www.gob.pe/.../midagri/...` | **404** | ID inexistente |

Asimismo, en `regions/ayacucho-por-rag-ayacucho-2.jsonl`:
- `https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1587/libro.pdf` devuelve **404**.

---

### 2. Riesgo para la Puerta de Calidad
Aunque `python scripts/validate_fragments.py` (offline) pasa porque comprueba solo sintaxis, cuando se ejecute con `--online` para la entrega final, **la puerta se cerrará con fallos masivos** por enlaces inventados o rotos (Regla 8: "Nada inventado... Si no encuentras la fuente primaria, el documento no existe").

---

### 3. Acción Requerida antes de las 18:30
1. Reemplazar urgentemente los URLs ficticios de `gob.pe` por enlaces reales y vivos de repositorios institucionales:
   - `https://repositorio.ana.gob.pe/` (balance hídrico cuenca Cachi).
   - `https://repositorio.senamhi.gob.pe/` (estudios climáticos Ayacucho).
   - `https://observatorio.senamhi.gob.pe/` (normales climáticas - este sí responde 200).
   - Artículos con DOI real (ej. SciELO, Dialnet, ResearchGate).
2. Si a las 18:30 no han sido corregidos, `rag-qa` asumirá la corrección exclusiva o retirará/sustituirá los fragmentos con `supersedes` para mantener la puerta en verde.
