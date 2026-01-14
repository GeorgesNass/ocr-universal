## ===========================================================
## Ultra-Optimized Dockerfile for ocr_universal
## FastAPI + Google Vision + Tesseract (French only)
## Target size: ~320 MB
## ===========================================================

# ---------- BUILDER STAGE ----------
FROM python:3.11-slim AS builder

## Disable interactive mode
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

## Install only minimal OCR dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr-fra \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

## Copy dependencies and install Python libraries (no cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- FINAL STAGE ----------
FROM python:3.11-slim

## Disable interactive mode and ensure live logs
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
WORKDIR /app

## Copy only runtime essentials from builder
COPY --from=builder /usr/local /usr/local

## Copy project structure (optimized)
COPY ./src ./src
COPY ./main.py ./main.py
COPY ./requirements.txt ./requirements.txt
COPY ./swagger.yaml ./swagger.yaml
COPY ./.env ./.env

## Expose FastAPI port
EXPOSE 8080

## Healthcheck endpoint
HEALTHCHECK CMD curl --fail http://localhost:8080/health || exit 1

## Default command to start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]