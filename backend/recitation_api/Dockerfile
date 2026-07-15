FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ML engine deps (CPU-only) for the real recitation inference pipeline.
COPY requirements.ml.txt .
RUN pip install --no-cache-dir -r requirements.ml.txt

COPY . .

# ctranslate2 (used by faster-whisper) ships a shared lib flagged with an
# executable-stack (RWE GNU_STACK). Some container kernels refuse to enable an
# exec stack and abort loading the lib ("cannot enable executable stack as
# shared object requires: Invalid argument"). Clear the execute bit on the
# GNU_STACK program header so the live ASR engine can load on the VPS.
RUN python3 fix_execstack.py

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
