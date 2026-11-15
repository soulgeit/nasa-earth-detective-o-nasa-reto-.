<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-c — 2026-11-15 08:35 hora de Perú
Rama@commit: main@e67873e · empujado: sí
VERIFICADO: docs/demo/EarthTrend_Detective_30s.mp4 dura exactamente 29.00s (cumple límite oficial <= 30.0s) según ffprobe (1920x1080, H.264, 795 KB). docs/demo/GUION.md describe segundo a segundo las 6 escenas del video (intro, Hielo Ártico, Hielo Antártico con detectabilidad honesta, TrendMap FDR, Comparación con ejes sincronizados, y cierre con URL pública de GitHub Pages). 100% en inglés, sin voz sintética, sin marcas/logos NASA, sin menores, bajo congelación de código (Ronda 6).
ESCRITO (sin ejecutar de punta a punta): ninguno
ROTO / NO HECHO: ninguno en el carril de demo
Siguiente paso: el equipo y humano deciden si envían la opción A (láminas 7 págs) o la opción B (video 29s) en el formulario oficial.
Necesito de: humano / equipo: seleccionar video o láminas para el campo demo de docs/SUBMISSION.md.
Avisos para otros carriles:
- Para @claude-omni-2: El video dura exactamente 29.0s y su guión está verificado en `docs/demo/GUION.md`. En `docs/SUBMISSION.md` se puede enlazar directamente junto con las láminas de 7 páginas.
- Para @claude-omni-e: Video y guión verificados en `main@e67873e` con `ffprobe` (29.00s <= 30.0s).
<!-- ESTADO:FIN -->

# Reportes de Claude Omni C (Demo / Vídeo)

## RONDA 6 — Verificación Final de Demostración (2026-11-15 08:35 UTC-5)
Rama@commit: `main@e67873e`

### 1. Verificación Técnica de `EarthTrend_Detective_30s.mp4`
Comprobación oficial ejecutada con `ffprobe` sobre la versión integrada en `main`:

```json
{
    "streams": [
        {
            "codec_name": "h264",
            "width": 1920,
            "height": 1080
        }
    ],
    "format": {
        "duration": "29.000000",
        "size": "795958",
        "bit_rate": "219574"
    }
}
```

- **Duración:** `29.000000 s` (Límite máximo permitido: `30.0 s` → **APROBADO**).
- **Resolución:** `1920×1080` (Full HD 16:9 → **APROBADO**).
- **Códec de vídeo:** `H.264` (perfil baseline/high universalmente reproducible en web y móviles).
- **Peso de archivo:** `777 KB` (0.76 MB) (Límite máximo permitido: `25 MB` → **APROBADO**).

---

### 2. Concordancia con `docs/demo/GUION.md`
El archivo `docs/demo/GUION.md` detalla con exactitud las escenas montadas en el archivo MP4:
- **00:00 - 00:03:** Tarjeta de título con misión y lema en inglés.
- **00:03 - 00:09:** Caso Hielo Ártico (1978–2026), declive fuerte de `-0.50M km²/década`, veredicto `SIGNIFICANT_STRONG` (5/5).
- **00:09 - 00:15:** Caso Hielo Antártico, honestidad científica con veredicto `NOT_SIGNIFICANT` (p = 0.63) y cálculo de detectabilidad de ~133 años restantes.
- **00:15 - 00:21:** TrendMap Global con control FDR Benjamini-Hochberg ($q=0.10$, 60% celdas significativas destacadas con stippling central).
- **00:21 - 00:26:** Modo Comparar con ejes Y sincronizados (Lima vs. Ártico).
- **00:26 - 00:29:** Tarjeta final con enlace público al despliegue en GitHub Pages (`soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./`).

---

### 3. Normativa y Requisitos Oficiales del Hackathon Space Apps 2026
- **Idioma:** 100% en inglés en pantalla, textos y subtítulos.
- **Marcas de identidad:** Sin logos, insignias ni tipografías institucionales de la NASA (cumple norma de no suplantación).
- **Privacidad y menores:** Cero personas, menores de edad o rostros.
- **Voz y audio:** Sin locución sintética generada por IA (acorde con directrices de la Ronda 5/6).
- **Código y datos:** 100% de datos reales procedentes de `data/cases/` y `data/atlas/`.
