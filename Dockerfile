# SI-assisted: claude-omni-3 (Claude Opus 5.5)
# EarthTrend Detective API v2 — un solo servicio (API + UI estática).
# Ligero a propósito: sin torch, sin modelos. En producción la IA va en
# AI_MODE=extractive salvo que el humano configure un LLM_BASE_URL.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    AI_MODE=extractive \
    ALLOW_FIXTURES=0 \
    DATA_CACHE_DIR=/data/cache

WORKDIR /app

# Dependencias primero: mejor caché de capas.
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Código necesario para servir la API y la UI.
COPY src/ ./src/
COPY data/catalog/ ./data/catalog/
COPY scripts/smoke_api.py ./scripts/smoke_api.py

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/cache \
    && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health/live', timeout=4).status==200 else 1)"

# Un solo worker: la caché de análisis y el límite de peticiones viven en memoria.
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
