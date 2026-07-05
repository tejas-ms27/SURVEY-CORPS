# Survey Corps — Automated Financial Data Analysis System

> Built for **CIDECODE Hackathon 2026** | Problem Statement 1
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

## Problem Statement

Financial cybercrime investigations in India are severely hampered by the manual effort required to analyse bank statements. CID investigators regularly receive statements from multiple suspects across different banks in inconsistent formats — PDF, scanned images, and Excel sheets. The current process requires manually reviewing thousands of transactions, takes weeks, and routinely misses hidden connections between accounts.

### Core Challenges

- Every bank produces statements in a different layout, making unified analysis impractical
- Cyber-fraud cases routinely involve hundreds of accounts and thousands of transactions
- Money-mule chains and hawala networks span multiple accounts and are invisible without cross-account analysis
- Manually compiling a court-ready forensic report from raw findings is slow and error-prone

---

## Solution

**Survey Corps** is a fully implemented AI-powered investigation platform that processes multi-format bank statements end-to-end — from raw uploads to a court-ready forensic report and an interactive investigation chatbot — in minutes.

The design principle: every numeric finding is produced by **deterministic code** (pandas, NetworkX, scikit-learn) so results are reproducible and legally defensible. LLMs are used only where they add genuine value over code — reading the investigator's case brief, generating context-appropriate thresholds, and writing plain-English explanations of what the mathematics found.

---

## System Architecture

```
uploads/  →  Extraction  →  Analysis Engine  →  Reporting  →  Chatbot (RAG)
              (Phase 2)       (Phase 3)          (Phase 4)
                ↓                 ↓                  ↓              ↓
          Standardised      25 Fraud          PDF + Excel      Natural-language
          transaction       Detectors         Reports          query over data
          tables            + Scoring
```

---

## Implementation Status

| Phase | Component | Status |
|-------|-----------|--------|
| Phase 1 | Case brief intake & file upload | ✅ Complete |
| Phase 2 | Extraction pipeline (PDF/OCR/Excel/CSV/DOCX) | ✅ Complete |
| Phase 2 | LLM structuring & column identification | ✅ Complete |
| Phase 2 | Account anonymisation & standardisation | ✅ Complete |
| Phase 3 | Analysis engine — all 25 detectors | ✅ Complete |
| Phase 3 | Composite suspicion scoring | ✅ Complete |
| Phase 3 | Money-flow graph generation (NetworkX) | ✅ Complete |
| Phase 4 | PDF report generation (ReportLab) | ✅ Complete |
| Phase 4 | Excel report generation (openpyxl) | ✅ Complete |
| Phase 4 | RAG chatbot (ChromaDB + sentence-transformers) | ✅ Complete |
| API | FastAPI backend with full routing | ✅ Complete |
| Frontend | React + TypeScript + Tailwind UI | ✅ Complete |

---

## Key Features

- **Multi-format ingestion** — PDF (digital and scanned via OCR), Excel, CSV, DOCX, JPG, PNG covering multiple suspect accounts in a single session
- **LLM-guided extraction** — Claude/Groq identifies document structure and standardises transactions regardless of bank format
- **25 fraud detection cases** across seven categories with weighted composite suspicion scoring (0–100 per account)
- **Interactive money-flow graph** — NetworkX-powered visualisation of the full suspect transaction network
- **Court-ready forensic reports** — PDF and Excel with executive summary, per-account findings, graph exports, and technical appendix
- **RAG-powered investigation chatbot** — ChromaDB + sentence-transformers lets investigators query transaction data in plain English
- **React + TypeScript frontend** — full-featured UI for case management, upload, analysis dashboard, and chatbot
- **FastAPI backend** — RESTful API serving all pipeline stages with session management

---

## Fraud Detection Cases (Phase 3)

### Graph-Based
| Case | Description |
|------|-------------|
| Round-trip detection | Identifies money that returns to sender via intermediaries |
| Multi-hop layering | Detects funds routed through 3+ accounts to obscure origin |
| Hub identification | Flags accounts that act as central routing nodes |
| Circular flow | Money loops between a set of accounts |
| Cross-statement links | Counterparty connections across different uploaded statements |

### Time-Based
| Case | Description |
|------|-------------|
| Dormancy reactivation | Account idle >90 days suddenly becomes highly active |
| Velocity spike | Sudden surge in transaction frequency vs. account baseline |
| Synchronised transactions | Multiple accounts transact in tight time windows |
| Reversal clusters | Failed/reversed transactions that indicate testing |
| First-contact large transfer | Large credit from a never-before-seen counterparty |

### Amount-Based
| Case | Description |
|------|-------------|
| Structuring / smurfing | Repeated deposits just below reporting thresholds |
| Hawala matched pairs | Near-equal credit/debit pairs with short time gap |
| FIFO money trail | Inbound funds forwarded out within hours |
| Round-value debits | Unusually high proportion of round-number withdrawals |
| Low-value testing | Micro-transactions testing whether an account is live |

### Counterparty
| Case | Description |
|------|-------------|
| Fan-in / fan-out | Single account aggregating from or distributing to many |
| Single counterparty concentration | >60 % of volume to/from one entity |
| Shared UPI IDs | Multiple accounts using the same UPI handle |
| Hub ranking | Eigenvector-centrality ranking of the transaction graph |

### Narration & Statistical
| Case | Description |
|------|-------------|
| Blank / generic narrations | Systematic absence of meaningful transaction descriptions |
| Case-brief keyword matching | Narrations matching suspect names, addresses, or keywords |
| Isolation Forest anomaly | ML-detected statistical outliers (scikit-learn) |
| LLM-guided pattern matching | Hypothesis generation using investigator case brief |
| Balance parking | Funds held in an account with minimal further activity |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Data processing | pandas, NumPy |
| Graph analysis | NetworkX |
| Statistical anomaly detection | scikit-learn (Isolation Forest) |
| OCR | Tesseract (pytesseract) |
| Digital PDF extraction | pdfplumber |
| LLM integration | Claude API (Anthropic) / Groq API |
| Vector store & RAG | ChromaDB, sentence-transformers |
| Report generation | ReportLab, openpyxl, matplotlib |
| Backend API | Python, FastAPI |
| Frontend | React, TypeScript, Tailwind CSS, Vite |
| Database | SQLite (per-case analysis DB) |

---

## Repository Structure

```
survey-corps/
├── extraction/              # Multi-format file parsing and standardisation
│   ├── router.py            # File-type dispatcher
│   ├── extractor_digital_pdf.py
│   ├── extractor_ocr.py
│   ├── extractor_excel_csv.py
│   ├── extractor_docx.py
│   ├── vision_extractor.py
│   ├── llm_structurer.py    # LLM-based column identification
│   ├── standardiser.py
│   └── extraction_pipeline.py
├── analysis/
│   └── analysis_engine/     # 25 fraud detectors + scoring
│       ├── pipeline.py
│       ├── scoring.py
│       ├── graph.py
│       └── detectors/       # One file per detection case
├── reporting/               # PDF and Excel report generation
│   ├── build_report.py
│   └── report_template.html
├── chatbot/                 # RAG-powered investigation chatbot
│   ├── rag_chat.py
│   ├── vector_store.py
│   ├── reasoning_engine.py
│   └── language.py
├── api/                     # FastAPI backend
│   ├── main.py
│   └── routers/
├── frontend/                # React + TypeScript frontend
│   └── src/
├── config/                  # Settings and configuration
├── requirements.txt
└── .env.example

> **Note:** Bank statement files and upload data are excluded from version control (contain PII).
```

---

## Getting Started

### Prerequisites

```bash
# Python 3.10+
pip install -r requirements.txt

# Tesseract OCR (macOS)
brew install tesseract

# Frontend dependencies
cd frontend && npm install
```

### Environment Variables

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

### Running the Backend

```bash
uvicorn api.main:app --reload --port 8000
```

### Running the Frontend

```bash
cd frontend && npm run dev
```

---

*CIDECODE Hackathon 2026 — Survey Corps*
