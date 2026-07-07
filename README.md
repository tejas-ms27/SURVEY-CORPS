# Survey Corps — Automated Financial Data Analysis System

> **CIDECODE Hackathon 2026** | Problem Statement 1
> Organised by **CCITR – CID Karnataka** in association with **PES University, Bengaluru**

---

## Team — Survey Corps

| Name | Role |
|------|------|
| Tejas M S | Backend & Analysis Engine |
| Nikhil Santosh | Extraction Pipeline & OCR |
| Tejas S | Reporting & RAG Chatbot |
| Vinayak G K | Frontend & API Integration |

---

## Project Overview

**Survey Corps** is an AI-powered financial forensics platform built for CID Karnataka investigators. It takes bank statements from multiple suspects — in any format (PDF, scanned image, Excel, CSV, Word) — and automatically:

- Extracts and standardises all transactions into a unified table
- Runs **23 fraud detection algorithms** (round-tripping, layering, smurfing, hawala, mule chains, dormancy activation, and more)
- Assigns each account a **suspicion score (0–100)**
- Generates an interactive **money-flow graph** of the suspect network
- Produces a **court-ready forensic report** (PDF + Excel)
- Provides a **RAG-powered investigation chatbot** that answers questions in plain English directly from the uploaded transaction data

The core design principle: every numeric finding is produced by **deterministic code** (pandas, NetworkX, scikit-learn) — reproducible and legally defensible. LLMs (Groq API) are used only for document understanding, plain-English explanations, and natural-language Q&A.

### System Flow

```
Upload Files + Case Brief
        ↓
  Extraction Pipeline
  (PDF / OCR / Excel / CSV / DOCX)
        ↓
  Analysis Engine
  (23 Fraud Detectors + Scoring)
        ↓
  Report Generation          RAG Chatbot
  (PDF + Excel + Graphs)     (ChromaDB + Groq)
```

---

## Prerequisites

Before running the project (Docker or manual), you need:

### 1. Groq API Key (Free)
The system uses [Groq](https://console.groq.com) for LLM-powered extraction and the investigation chatbot.

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key — you will need it in the `.env` setup step

> A single free-tier key is sufficient to run the demo. The system supports multiple keys for heavy workloads.

### 2. Docker (Recommended path)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac / Windows / Linux)
- Docker Compose (included with Docker Desktop)

### 3. Manual path (without Docker)
- Python 3.11+
- Node.js 18+
- Tesseract OCR (`brew install tesseract` on macOS, `apt install tesseract-ocr` on Linux)

---

## Docker Setup and Execution (Recommended)

This is the fastest way to run the full system — one command starts everything.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/tejas-ms27/SURVEY-CORPS.git
cd SURVEY-CORPS
```

### Step 2 — Set Up Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your Groq API key:

```env
GROQ1=gsk_your_key_here
GROQ2=gsk_your_key_here
GROQ3=gsk_your_key_here
```

> You can use the same key for GROQ1, GROQ2, and GROQ3 if you only have one. For best performance, use separate keys (each has its own free-tier quota).

### Step 3 — Build and Start

```bash
docker-compose up --build
```

This will:
- Build the Python backend image (installs Tesseract, OpenCV, Playwright/Chromium, all pip packages)
- Build the React frontend image (compiles the app, serves via nginx)
- Start both services

> **First build takes 15–20 minutes** — `sentence-transformers` pulls in PyTorch (~2 GB) and Playwright downloads Chromium (~300 MB). Subsequent starts are instant (under 30 seconds).
> You will need approximately **5 GB of free disk space** for the Docker images.

### Step 4 — Open the Application

| Service | URL |
|---------|-----|
| Frontend (React UI) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Health Check | http://localhost:8000/api/health |

### Step 5 — Stop

```bash
docker-compose down
```

To also remove stored data (uploads, outputs, ChromaDB):

```bash
docker-compose down -v
```

---

## Manual Setup and Installation (Without Docker)

Follow these steps if you prefer to run without Docker.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/tejas-ms27/SURVEY-CORPS.git
cd SURVEY-CORPS
```

### Step 2 — Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang   # includes Hindi and Kannada language packs
```

**Ubuntu / Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-hin tesseract-ocr-kan
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Step 3 — Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```env
GROQ1=gsk_your_key_here
GROQ2=gsk_your_key_here
GROQ3=gsk_your_key_here
```

### Step 4 — Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 5 — Install Playwright (for PDF Reports)

```bash
pip install playwright
playwright install chromium
```

### Step 6 — Install Frontend Dependencies

```bash
cd chatbot_ui/frontend
npm install
cd ../..
```

---

## Running the Project (Manual)

You need two terminals — one for the backend, one for the frontend.

### Terminal 1 — Start the Backend

```bash
source venv/bin/activate        # Windows: venv\Scripts\activate
uvicorn api.main:app --reload --port 8000
```

Backend is ready when you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 — Start the Frontend

```bash
cd chatbot_ui/frontend
npm run dev
```

Frontend is ready when you see:
```
  VITE ready in Xs
  ➜  Local:   http://localhost:5173/
```

### Open the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## How to Use

1. **Open the app** at http://localhost:3000 (Docker) or http://localhost:5173 (manual)
2. Click **Open Case** on the landing page
3. **Upload bank statements** — drag and drop PDF, Excel, CSV, DOCX, or image files
4. **Type a case brief** — describe the suspected fraud, suspect names, amounts of interest
5. Click **Run Extraction** — the system standardises all uploaded statements
6. Click **Run Analysis** — 23 fraud detectors run across all accounts
7. View the **suspicion scores**, **money-flow graph**, and **findings**
8. Download the **PDF or Excel report**
9. Ask questions in the **Investigation Chatbot** — "Which accounts show round-tripping?", "What is the total volume for ACCT_003?"

---

## Key Features

- **Multi-format ingestion** — PDF (digital & scanned), Excel, CSV, DOCX, JPG, PNG
- **LLM-guided extraction** — Groq identifies document structure regardless of bank format
- **23 fraud detection cases** — round-trips, layering, smurfing, hawala, mule chains, dormancy, velocity spikes, and more
- **Tiered suspicion scoring** — 0–100 composite score per account with tier-weighted evidence
- **Interactive money-flow graph** — NetworkX-powered network of the full suspect ecosystem
- **Court-ready reports** — PDF (A4, Playwright-rendered) and Excel with all findings and evidence
- **RAG investigation chatbot** — ChromaDB + Groq, answers questions from actual uploaded data
- **Multilingual support** — Kannada and Hindi question/answer support

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend API | Python, FastAPI, uvicorn |
| Data processing | pandas, NumPy |
| Graph analysis | NetworkX |
| Anomaly detection | scikit-learn (Isolation Forest) |
| OCR | Tesseract, OpenCV, Groq Vision |
| PDF extraction | pdfplumber, PyMuPDF |
| LLM | Groq API (llama / gpt-oss models) |
| Vector store & RAG | ChromaDB, sentence-transformers |
| Report generation | Jinja2, Playwright (Chromium), ReportLab |
| Charts | matplotlib, plotly |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| State management | Zustand |
| Containerisation | Docker, Docker Compose, nginx |

---

## Repository Structure

```
SURVEY-CORPS/
├── extraction/          # Phase 2 — multi-format extraction pipeline
├── analysis/            # Phase 3 — 23 fraud detectors + scoring engine
│   └── analysis_engine/
│       └── detectors/   # one file per fraud pattern
├── reporting/           # Phase 4 — PDF + Excel report generation
├── chatbot/             # Phase 5 — RAG chatbot (ChromaDB + Groq)
├── api/                 # FastAPI backend + route handlers
├── chatbot_ui/
│   └── frontend/        # React + TypeScript frontend (Vite)
├── config/              # Central settings and configuration
├── Dockerfile           # Backend container
├── Dockerfile.frontend  # Frontend container
├── docker-compose.yml   # Orchestrates backend + frontend
├── nginx.conf           # nginx config for React SPA
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── PROJECT.md           # Full technical documentation
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ1` | Yes | Groq API key for extraction (column identification) |
| `GROQ2` | Yes | Groq API key for OCR vision fallback |
| `GROQ3` | Yes | Groq API key for analysis + report narration |
| `GROQ4`–`GROQ10` | No | Additional keys for rotation under heavy load |
| `TESSERACT_CMD` | No | Path to Tesseract binary (auto-detected if on PATH) |

Get free Groq API keys at [console.groq.com](https://console.groq.com). A single key works for all three variables in a demo setting.

---

*CIDECODE Hackathon 2026 — Survey Corps — CID Karnataka / PES University, Bengaluru*
