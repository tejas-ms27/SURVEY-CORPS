# Use full Python image (not slim) — binary packages like opencv, pymupdf,
# kaleido need system libraries that slim strips out.
FROM python:3.11

# System packages: Tesseract OCR + language packs, OpenCV runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-kan \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer — only rebuilds if requirements.txt changes)
# NOTE: sentence-transformers pulls in PyTorch (~2 GB). First build takes 15–20 min.
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Install Playwright and download Chromium for PDF report generation
RUN pip install --no-cache-dir playwright jinja2 && \
    playwright install chromium --with-deps

# Copy project source (see .dockerignore for what is excluded)
COPY . .

# Pre-create all runtime directories so the app starts cleanly
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
