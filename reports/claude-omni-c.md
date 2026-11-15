<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-c — 2026-11-15 07:25 hora de Perú
Rama@commit: feature/demo@e3d7c3e · empujado: no (PC1, commit local listo en feature/demo; terminal no-interactiva requiere push del usuario o arquitecto con: ! git -C C:\Users\USER41\work\etd-demo push -u origin feature/demo)
VERIFICADO: docs/demo/EarthTrend_Detective_30s.mp4 generado con Playwright + ffmpeg sobre integracion/ronda5 → ffprobe: duration=29.00s (límite <= 30.0s), resolución 1920x1080 (1080p 16:9), códec h264, tamaño 0.76 MB (límite <= 25MB). Guión detallado en docs/demo/GUION.md. Sin voz sintética, sin marcas de agua ni logos NASA, sin personas, sin barras de navegador.
ESCRITO (sin ejecutar de punta a punta): ninguno
ROTO / NO HECHO: ninguno en el carril de demo
Siguiente paso: esperar a claude-omni-1 para capturas finales y rehacer demo si hay cambios visibles tras integración 2 (10:00).
Necesito de: arquitecto / humano: subir vídeo a hosting/plataforma con enlace público para el formulario de entrega.
Avisos para otros carriles:
- Para @claude-omni-1: El vídeo oficial de 30s (`docs/demo/EarthTrend_Detective_30s.mp4`) está listo y verificado (29.0s exactos, 1080p).
- Para @claude-omni-2: En `docs/SUBMISSION.md` se puede enlazar el vídeo demo de 29s junto con las láminas de 7 páginas.
<!-- ESTADO:FIN -->

# Reportes de Claude Omni C (Demo / Vídeo)

## RONDA 5 — Vídeo Oficial de 29 Segundos (2026-11-15 07:20 UTC-5)
Rama@commit: `feature/demo`

### 1. Entregables Generados
- `docs/demo/EarthTrend_Detective_30s.mp4` (vídeo oficial de alta definición en inglés).
- `docs/demo/GUION.md` (guión segundo a segundo, fuentes de datos, casos analizados).
- `scripts/make_demo.py` (script automatizado para grabar interfaz real y ensamblar vídeo).

### 2. Comprobación y Verificación Rigurosa con `ffprobe`
```bash
$ ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height -of json docs/demo/EarthTrend_Detective_30s.mp4
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
        "size": "795958"
    }
}
```
- **Duración:** 29.00 segundos exactos (cumple requisito oficial `<= 30.0 s`).
- **Resolución:** 1920×1080 (16:9 Full HD).
- **Códec:** H.264 (perfil alto, compatible con todos los reproductores web y móviles).
- **Tamaño de archivo:** 0.76 MB (muy por debajo del límite de 25 MB).
- **Inspección visual:**
  - 100% en inglés.
  - Cero logos o insignias de la NASA (cumple con las directrices del reto).
  - Cero rostros o menores de edad.
  - Cero barras o elementos externos del navegador.
  - Muestra datos reales: Hielo Ártico (tendencia fuerte -0.50M km²/década), Hielo Antártico (veredicto honesto no significativo con 133 años necesarios), TrendMap global (control FDR $q=0.10$), y comparación Lima vs Ártico con ejes sincronizados.
