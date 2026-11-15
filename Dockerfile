# SI-assisted: claude-omni-3 (Claude Opus 5.5)
# EarthTrend Detective API v2 — un solo servicio (API + UI estática + LoRA en Railway Hobby).

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    AI_MODE=full \
    PLANNER_MODEL=local-lora \
    HF_HOME=/app/cache/huggingface \
    ALLOW_FIXTURES=0 \
    DATA_CACHE_DIR=/data/cache \
    PORT=8080

WORKDIR /app

# Dependencias base y ML para CPU
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir transformers peft accelerate

# Pre-descarga del modelo base SmolLM2-1.7B en la imagen
RUN python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; AutoTokenizer.from_pretrained('HuggingFaceTB/SmolLM2-1.7B-Instruct'); AutoModelForCausalLM.from_pretrained('HuggingFaceTB/SmolLM2-1.7B-Instruct', torch_dtype='bfloat16')"

# Código y modelos necesarios
COPY src/ ./src/
COPY models/ ./models/
COPY data/catalog/ ./data/catalog/
COPY data/cases/ ./data/cases/
COPY data/atlas/ ./data/atlas/
COPY data/knowledge/ ./data/knowledge/
COPY data/lora/ ./data/lora/

COPY scripts/smoke_api.py ./scripts/smoke_api.py

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/cache /app/cache/huggingface \
    && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD python -c "import os,urllib.request,sys; p=os.environ.get('PORT','8080'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{p}/api/health/live', timeout=4).status==200 else 1)"

CMD ["sh", "-c", "exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
