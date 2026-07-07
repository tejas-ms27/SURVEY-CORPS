FROM python:3.11-slim

# System dependencies: Tesseract OCR, OpenCV libs, Playwright/Chromium deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-kan \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    poppler-utils \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and download Chromium for PDF report generation
RUN pip install --no-cache-dir playwright jinja2 && \
    playwright install chromium --with-deps

# Copy project source
COPY . .

# Pre-create all runtime directories
RUN mkdir -p \
    uploads \
    outputs/reports \
    outputs/graphs \
    outputs/extractions \
    storage/llm_cache \
    storage/chromadb \
    chroma_store

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
