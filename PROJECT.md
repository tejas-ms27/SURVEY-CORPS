# Survey Corps — Automated Financial Data Analysis System
## Complete Project Documentation

> **CIDECODE Hackathon 2026** | Problem Statement 1
> Organised by **CCITR – CID Karnataka** in association with **PES University, Bengaluru**

---

## Table of Contents

1. [Team](#1-team)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [Core Design Philosophy](#4-core-design-philosophy)
5. [Phase 1 — Input & Case Setup](#5-phase-1--input--case-setup)
6. [Phase 2 — Extraction Pipeline](#6-phase-2--extraction-pipeline)
7. [Phase 3 — Analysis Engine](#7-phase-3--analysis-engine)
8. [Phase 4 — Report Generation](#8-phase-4--report-generation)
9. [Phase 5 — RAG Investigation Chatbot](#9-phase-5--rag-investigation-chatbot)
10. [API Layer — FastAPI Backend](#10-api-layer--fastapi-backend)
11. [Frontend — React + TypeScript UI](#11-frontend--react--typescript-ui)
12. [Evaluation & Testing](#12-evaluation--testing)
13. [Technology Stack](#13-technology-stack)
14. [Repository Structure](#14-repository-structure)
15. [Environment & Configuration](#15-environment--configuration)
16. [Key Engineering Decisions](#16-key-engineering-decisions)

---

## 1. Team

| Member | Role |
|--------|------|
| **Tejas M S** | Backend, Analysis Engine, Pipeline Orchestration |
| **Nikhil Santosh** | Extraction Pipeline, OCR, LLM Structuring |
| **Tejas S** | Reporting Phase, RAG Chatbot, Narration |
| **Vinayak G K** | React Frontend, API Integration |

---

## 2. Problem Statement

Financial cybercrime investigations in India are severely hampered by the volume and variety of bank statements that CID investigators must process manually.

### The Challenges

- **Format fragmentation** — Every bank prints statements in a different layout: SBI looks nothing like HDFC, ICICI, Axis, Kotak, or Karnataka Gramin Bank. A unified parser is impossible to write with regex alone.
- **Scale** — A single cyber-fraud case can involve 50–200 suspect accounts. Reviewing thousands of transactions manually takes weeks.
- **Hidden connections** — Money-mule chains, hawala networks, and round-tripping schemes span multiple accounts and are completely invisible unless all accounts are analysed together.
- **Format mix** — Real cases arrive as a mix of computer-generated PDFs, photographed/scanned PDFs, Excel bank exports, CSV downloads, Word documents, and phone photographs of physical statements.
- **Report burden** — Manually writing a court-ready forensic investigation report from raw findings is slow, inconsistent, and error-prone.

---

## 3. Solution Overview

**Survey Corps** is a fully implemented AI-powered investigation platform. An investigator uploads all suspect bank statements (in any combination of formats), types a plain-English case brief, and the system delivers within minutes:

1. A standardised, unified transaction table across all uploaded accounts
2. Automated detection of 23 fraud patterns with a composite suspicion score (0–100) per account
3. An interactive money-flow graph showing the full suspect network
4. A court-ready forensic PDF report and Excel export
5. A natural-language chatbot that can answer investigative questions directly from the uploaded transaction data

The system flows through five sequential phases:

```
Phase 1          Phase 2            Phase 3             Phase 4        Phase 5
─────────        ──────────         ─────────────        ──────────     ──────────────
Case Brief   →   Extraction    →    Analysis Engine  →   Reporting  →   RAG Chatbot
+ Uploads        Pipeline           (23 detectors)        (PDF+Excel)    (ChromaDB+Groq)
```

---

## 4. Core Design Philosophy

### Deterministic Code for Facts, LLM for Intelligence

Every numeric finding — transaction counts, amounts, graph centrality, anomaly scores — is computed by **deterministic code** (pandas, NetworkX, scikit-learn). This makes the output reproducible and legally defensible.

LLMs (Groq API) are used **only** where they provide genuine value over code:
- Reading a bank statement whose layout the code has never seen before
- Generating context-appropriate thresholds from the investigator's case brief
- Writing plain-English explanations of mathematical findings
- Answering investigative questions in natural language

### Structural Citations over LLM-Generated Citations

The RAG chatbot never trusts the LLM to "cite correctly." Instead, ChromaDB retrieval gives exact metadata (transaction IDs, account IDs, pattern IDs, dates) and the LLM synthesises a natural-language answer from those chunks. Citation chips are built programmatically from the retrieved metadata — guaranteed correct because they come from the database, not from model generation.

### Fail-Safe Extraction

Each file in the extraction pipeline runs inside its own `try/except` block. If one file fails (corrupted PDF, password-protected file, unsupported format), it is added to a `files_failed` list and processing continues with the rest. One bad file never crashes an entire investigation.

### Multi-Key Groq Rotation

Groq's free tier imposes a daily token quota per API key per model. The system uses a `GroqKeyPool` — two separate pools (text extraction keys, vision/OCR keys) — with in-memory dead-key tracking within a run. When a key hits its daily limit (HTTP 429), it is marked dead for that run and the next key in the pool is tried immediately. This makes the system robust to quota exhaustion during long multi-statement runs.

---

## 5. Phase 1 — Input & Case Setup

### What Happens

The investigator:
1. Types a **case brief** — a natural-language description of the suspected crime, suspect names, amounts of interest, known accounts, and any specific patterns to look for.
2. **Uploads files** — any number of bank statements in any supported format. Multiple accounts can be uploaded in a single session.

### What the Case Brief Powers

The case brief is not decorative. It is used in Phase 3 to:
- Identify narration keywords matching suspect names and addresses (Pattern 21 — Narration Keyword Matching)
- Generate context-appropriate thresholds via LLM (e.g., "what counts as a large transfer in this specific case")
- Drive the LLM anomaly investigator's hypothesis generation (Pattern 22)
- Shape the RAG chatbot's understanding of what matters in this case

### Supported File Formats

| Format | Extension | Routing Path |
|--------|-----------|--------------|
| Computer-generated PDF | `.pdf` | `pdf_digital` |
| Scanned/photographed PDF | `.pdf` | `pdf_scanned` |
| Excel statement | `.xlsx`, `.xls` | `excel_csv` |
| CSV export | `.csv` | `excel_csv` |
| Word document | `.docx` | `docx` |
| Phone photograph | `.jpg`, `.jpeg`, `.png` | `image` |

---

## 6. Phase 2 — Extraction Pipeline

The extraction phase converts every uploaded file — regardless of format or bank — into one standardised transaction table with exactly these columns:

```
Date | Narration | Debit | Credit | Balance | Account_ID | Bank_Name
```

### Architecture — Five Components in Sequence

```
File Upload
    │
    ▼
[Component 1] Router (router.py)
    │   Inspects file extension + PDF text character count
    │   Returns: "pdf_digital" | "pdf_scanned" | "excel_csv" | "docx" | "image"
    │
    ▼
[Component 2] Extractor (extractor_*.py)
    │   pdf_digital  → pdfplumber extracts embedded text
    │   pdf_scanned  → Tesseract OCR + Groq Vision fallback
    │   excel_csv    → pandas reads directly into DataFrame
    │   docx         → python-docx extracts raw text
    │   image        → Tesseract OCR + Groq Vision
    │
    ▼
[Component 3] Column Identifier (column_identifier.py)
    │   Sends first 40 lines to Groq LLM
    │   Groq returns JSON column map: which column = date, narration, debit, credit, balance
    │
    ▼
[Component 4] Standardiser (standardiser.py)
    │   Uses column map to rename and reformat into the 7-column standard schema
    │   Parses dates, normalises amounts, assigns Account_ID and Bank_Name
    │
    ▼
[Component 5] Validator (validator.py)
    │   Checks date validity, balance arithmetic, debit/credit exclusivity
    │   Produces: clean_transactions.csv + flagged_transactions.csv
    │
    ▼
Post-processing (extraction_pipeline.py)
    Cross-file duplicate removal
    Identifier Vault (account → anonymised ID mapping)
    ChromaDB ingestion for RAG chatbot
```

### Component 1 — Router (`router.py`)

The router decides which processing path each file takes. For PDF files, it opens the file with `pdfplumber` and counts embedded characters. If the character count exceeds a configurable threshold (`DIGITAL_PDF_CHAR_THRESHOLD`), the file is classified as `pdf_digital` (computer-generated). Below the threshold, it is classified as `pdf_scanned` (photographed/printed and then scanned), which triggers the OCR path.

### Component 2 — Extractors

**`extractor_digital_pdf.py`** — Uses `pdfplumber` to extract tables and text from computer-generated PDFs. Tries coordinate-based table detection first, then full-text extraction as fallback.

**`extractor_ocr.py`** — Two-path OCR:
- **Path A (Tesseract)**: Uses `pytesseract` with `opencv-python` pre-processing (greyscale, threshold, deskew). Faster and fully offline.
- **Path B (Groq Vision)**: If Tesseract confidence is low, falls back to Groq's vision model which reads the image directly. Handles handwritten notes, poor scans, and rotated documents.

**`extractor_excel_csv.py`** — Uses `pandas` with `openpyxl` (for `.xlsx`) and `xlrd` (for `.xls`). Handles multi-sheet workbooks, merged cells, and header rows at arbitrary positions.

**`extractor_docx.py`** — Uses `python-docx` to extract text from Word documents, including text from tables inside the document.

### Component 3 — LLM Structurer (`llm_structurer.py`)

This is the core of what makes the extraction format-agnostic. Instead of writing regex patterns per bank, the system sends the raw extracted text to Groq and asks the LLM to parse it.

The LLM returns a strict JSON object:
```json
{
  "account_details": {
    "account_holder_name": "...",
    "account_number": "...",
    "ifsc_code": "...",
    "bank_name": "...",
    "statement_period": "...",
    "opening_balance": 0.0,
    "closing_balance": 0.0
  },
  "transactions": [
    {
      "date": "...",
      "description": "...",
      "debit": 0.0,
      "credit": 0.0,
      "balance": 0.0
    }
  ]
}
```

For large statements (hundreds of rows), the text is processed in **chunks of 30 lines**, with account metadata read once from the header and transaction rows merged from all chunks. Every unique document is cached on disk so repeated processing makes zero additional API calls.

### Component 4 — Column Identifier (`column_identifier.py`)

For Excel/CSV files where the data is already structured, the column identifier sends the first 40 rows to Groq as a text sample. Groq identifies which column name corresponds to which field in the standard schema, returning a column mapping. This handles every bank's custom column naming convention without per-bank code.

### Component 5 — Standardiser (`standardiser.py`)

Applies the column map to rename all columns to the standard 7-column schema. Normalises dates into ISO format, strips currency symbols from amounts, ensures Debit and Credit are non-negative floats.

### Validator (`validator.py`)

Runs three quality checks:
1. **Date validity** — Are all dates parseable and within a reasonable range?
2. **Balance arithmetic** — Does `balance[n] ≈ balance[n-1] ± debit[n] ± credit[n]`? Flags rows where arithmetic breaks.
3. **Debit/credit exclusivity** — A single transaction row should not have both a debit and a credit amount.

Produces two outputs: `clean_transactions.csv` (passed to analysis) and `flagged_transactions.csv` (for investigator review).

### Identifier Vault (`identifier_vault.py`)

Maintains a persistent mapping from real account numbers/names to anonymised IDs (`ACCT_001`, `ACCT_002`, etc.). This mapping is used consistently across all files in a session so that the same account referenced in two different statements gets the same anonymised ID, enabling cross-statement analysis.

### ChromaDB Ingestion (`chromadb_ingestor.py`, `chunking_v2.py`)

After all files are extracted and validated, the unified transaction DataFrame is chunked into text segments and ingested into ChromaDB via `sentence-transformers` embeddings. This powers the RAG chatbot in Phase 5.

### Key Pool & API Rotation (`key_pool.py`)

Two separate Groq key pools:
- **Text pool** — keys used for column identification and LLM structuring
- **Vision pool** — keys used for Groq Vision OCR fallback

When a key returns HTTP 429 (daily quota exceeded), it is marked dead in-memory for that run. The pool immediately tries the next available key. This prevents a single quota limit from stopping a multi-file extraction run.

---

## 7. Phase 3 — Analysis Engine

The analysis engine runs all 23 fraud detection cases over the unified transaction data. Each detector is a self-contained Python module in `analysis/analysis_engine/detectors/`.

### Pipeline Orchestration (`pipeline.py`)

The `AnalysisPipeline` class runs all steps in a fixed order:
1. Load transactions into a per-run SQLite database
2. Compute baselines (per-account statistics used as reference for anomaly detection)
3. Resolve counterparties (map narrations to account IDs where possible)
4. Build the money-flow graph (NetworkX `MultiDiGraph`)
5. Run all 23 detectors in sequence
6. Run the ML anomaly detector (Isolation Forest)
7. Run the LLM anomaly investigator (Groq)
8. Compute composite suspicion scores
9. Generate LLM narrations for each finding
10. Persist all findings, graph, and scores to SQLite

### Database (`database.py`)

Each analysis run uses its own SQLite database (`analysis.db`). Tables:

| Table | Contents |
|-------|----------|
| `transactions` | All transactions with parsed fields, eligibility flags, counterparty resolution |
| `accounts` | Per-account aggregates: total volume, throughput ratio, unique counterparty count |
| `findings` | All detected fraud pattern findings with pattern ID, accounts involved, evidence |
| `graph_edges` | Serialised money-flow graph edges for frontend visualisation |
| `baseline` | Per-account statistical baseline computed before detectors run |

### Money-Flow Graph (`graph.py`)

Built as a `networkx.MultiDiGraph`. Each node is an account (observed or external counterparty). Each edge is a detected transfer between accounts, weighted by amount. The graph is used by:
- All graph-based detectors (round-trip, circular flow, hub ranking, cross-statement links)
- The frontend 3D visualisation
- The chatbot graph query handler

### The 23 Fraud Detection Cases

Pattern IDs match the canonical catalog in `models.py`:

#### Group 1 — Reversal / Duplicate Patterns
| Pattern ID | Name | What it detects |
|------------|------|-----------------|
| 2 | `failed_reversed_transaction_detection` | Transaction pairs where a debit is quickly followed by a credit of the same amount — indicating a failed or reversed transfer. Used to detect account testing behaviour. |

#### Group 2 — Flow / Routing Patterns
| Pattern ID | Name | What it detects |
|------------|------|-----------------|
| 3 | `pass_through_routing_account` | Accounts that receive credits and immediately forward similar amounts out — with very little money retained. High throughput ratio, low balance delta. |
| 4 | `fund_pooling_account` | Accounts that aggregate inflows from many sources but have few outflows. Classic money-mule collection point. |
| 9 | `credit_to_cash_out_chains` | Sequences where credited amounts are quickly converted to cash withdrawals or informal transfers — breaking the paper trail. |

#### Group 3 — Amount Patterns
| Pattern ID | Name | What it detects |
|------------|------|-----------------|
| 5 | `structuring_smurfing_detection` | Repeated transactions just below reporting thresholds (e.g., Rs 49,500 instead of Rs 50,000). Deliberate fragmentation of large sums. |
| 13 | `low_value_account_testing` | Micro-transactions (Rs 1–10) sent to an account, indicating an attacker is verifying that an account is live before sending larger amounts. |
| 15 | `round_value_debit_patterns` | An unusually high proportion of round-number withdrawals (e.g., Rs 10,000, Rs 50,000). Round amounts are statistically rare in normal spending. |

#### Group 4 — Graph / Network Patterns
| Pattern ID | Name | What it detects |
|------------|------|-----------------|
| 6 | `money_flow_graph_construction` | The base graph structure — not a fraud signal itself, but the foundation all graph-based detectors rely on. |
| 7 | `circular_flow_multi_hop_cycle_detection` | Cycles in the money-flow graph where funds travel through a sequence of accounts and return to the origin. Classic round-tripping and layering. |
| 10 | `cross_statement_links` | Counterparty connections that appear in multiple uploaded statements — proving that two apparently separate accounts are actually transacting with each other. |
| 12 | `hub_ranking` | Accounts with high betweenness or eigenvector centrality in the transaction graph — the central routing nodes in a network. |
| 17 | `round_trip_detection` | Two-hop round-trips: Account A → Account B → Account A, typically within a short time window. The simplest form of layering. |

#### Group 5 — Time-Based Patterns
| Pattern ID | Name | What it detects |
|------------|------|-----------------|
| 11 | `balance_parking_account` | Accounts that receive a large sum and then hold it with minimal activity — "parking" funds before a later move. |
| 14 | `reversal_clusters` | Clusters of reversals concentrated in short time windows, indicating systematic testing or exploitation of a payment system. |
| 18 | `dormant_reactivation` | An account that was idle for a long period (>90 days) and then suddenly shows high-volume activity — a classic mule account activation signal. |
| 19 | `first_contact_large_transfer` | A large credit arriving from a counterparty that has never transacted with this account before. High risk indicator for fraud-initiated transfers. |

#### Group 6 — Counterparty Patterns
| Pattern ID | Name | What it detects |
|------------|------|-----------------|
| 16 | `shared_upi_identifiers` | Multiple accounts using the same UPI handle or VPA in their narrations — indicating a single controller operating multiple accounts. |

#### Group 7 — ML & LLM-Driven Patterns
| Pattern ID | Name | What it detects |
|------------|------|-----------------|
| 21 | `suspicious_account_ranking` | Composite ranking of all accounts by suspicion score — the final synthesised output of all other detectors. |
| 22 | `llm_investigated_anomalies` | The LLM reads the case brief and the top anomalous transactions from the Isolation Forest output, then generates hypotheses about what suspicious behaviour might be occurring. Produces "lead" quality findings for investigator follow-up. |
| 23 | `ml_ensemble_anomaly_lead` | scikit-learn Isolation Forest trained on each account's transaction features (amount, frequency, time-of-day, counterparty diversity). Statistical outliers are flagged as anomaly leads. |

#### Additional Detectors (in pipeline)
| Detector | What it detects |
|----------|-----------------|
| `detect_auto_money_trails` | FIFO money trails — inbound funds forwarded out within a short time window, tracing how money moves through transit accounts |
| `detect_high_throughput_pass_through` | Accounts where inflow ≈ outflow with minimal balance retention |
| `detect_transit_accounts` | Short-dwell-time accounts that serve purely as routing hops |
| `detect_holding_accounts` | Accounts that accumulate without distributing |
| `detect_high_risk_hub_ranking` | Top hub accounts by multiple centrality metrics |
| `detect_top_suspicious_ranking` | Final ranked list of all accounts by composite score |

### Tiered Suspicion Scoring (`scoring.py`)

Each account receives a composite suspicion score from 0–100 based on all findings that involve it. The scoring system uses four tiers with different weights:

| Tier | Weight | Pattern IDs | Meaning |
|------|--------|-------------|---------|
| Tier 1 | 100.0 | 7, 8, 10, 17 | Strong direct evidence (circular flow, cross-statement, round-trip) |
| Tier 2 | 35.0 | 3, 4, 5, 9, 11, 13, 18 | Significant behavioural indicators |
| Tier 3 | 8.0 | 12, 15, 16, 19 | Corroborating signals |
| Below Tier 3 | 2.0 | 22, 23 | Investigative leads only |

**Overlap reduction**: If two findings cover the same transactions (Jaccard similarity > 0.60), the second finding's score contribution is reduced by 80% to prevent double-counting the same underlying event.

**Ranking gate**: An account cannot appear in the suspicious ranking from score alone — it must have at least one Tier 1 or Tier 2 finding, preventing weak Tier 3 signals from generating false positives.

### LLM Narration (`narration.py`)

After all detectors run, each finding is passed to `explain_finding()`. This calls the Groq API with the raw finding data and asks it to write a plain-English explanation of what was detected and why it is suspicious. These narrations are what appears in the PDF report as the "findings" section.

---

## 8. Phase 4 — Report Generation

### HTML Template Approach (`build_report.py`, `report_template.html`)

Reports are generated using a **Jinja2 HTML template** that is filled with analysis data and then rendered to a PDF by **Playwright** (headless Chromium). This approach gives full CSS control over the PDF layout, supports charts embedded as base64 data URIs, and produces professional A4-formatted output.

Pipeline:
```
analysis_results.json
        +
extraction metadata
        │
        ▼
report_data.build_report_context()   ← assembles all data into template variables
        │
        ▼
Jinja2 fills report_template.html    ← HTML template with all findings, charts, tables
        │
        ▼
Playwright page.pdf()                ← headless Chromium renders to A4 PDF
```

### Report Sections

| Section | Contents |
|---------|----------|
| Executive Summary | Case brief, total accounts analysed, total transactions, top suspects table |
| Suspicion Scores | Per-account composite score with tier breakdown |
| Money-Flow Graph | Network visualisation showing all detected flows |
| Findings by Account | Per-account narrative of each detected pattern |
| Transaction Evidence | Specific transactions cited as evidence for each finding |
| Balance Trends | Per-account balance timeline charts |
| Technical Appendix | Raw scores, pattern catalog, methodology notes |

### Excel Report (`report_data.py`, `openpyxl`)

A separate Excel workbook is generated alongside the PDF with:
- Sheet 1: Suspicion scores and rankings
- Sheet 2: All detected findings
- Sheet 3: Evidence transactions
- Sheet 4: Full unified transaction table (clean rows)
- Sheet 5: Flagged / anomalous rows

### Graphs and Charts (`graph_generator.py`, `matplotlib`, `plotly`)

Several chart types are generated and embedded in both the PDF report and made available for the frontend:

| Chart | Library | Description |
|-------|---------|-------------|
| Money flow network | NetworkX + matplotlib | Node = account, edge = transfer, size = volume |
| Balance trend | matplotlib | Per-account balance over time |
| Fraud pattern summary | matplotlib | Bar chart of findings by category |
| Money trail flow | plotly | Sankey diagram of detected money flows |
| Suspicious timeline | matplotlib | Timeline of flagged transactions |
| 3D money flow | plotly | Interactive 3D network for frontend |

### LLM Report Enhancement (`report_llm.py`)

An optional second pass runs after the template fill. The Groq API is called to rewrite the raw narration bullets into more polished investigative prose — improving readability for the court report while keeping all numbers unchanged (the LLM never touches numeric values, only their textual framing).

### Internationalisation (`i18n.py`)

The report system supports multilingual output via `normalize_language()`. If the investigator's case brief is in Kannada or Hindi, the report can be generated in that language. Currently supports English, Hindi, and Kannada.

---

## 9. Phase 5 — RAG Investigation Chatbot

### Architecture

```
Investigator Question
        │
        ▼
detect_and_translate_to_english()      ← Detects language, translates if needed
        │
        ▼
resolve_followup()                     ← Resolves "it", "that account", "the suspect" to IDs
        │
        ├── try_id_lookup_answer()      ← Direct lookup by account ID or transaction ID
        │
        ├── try_structured_answer()    ← SQL-like deterministic answer for data questions
        │
        ├── try_aggregation_answer()   ← SUM, COUNT, AVERAGE queries on transactions
        │
        ├── try_investigation_answer() ← Pattern-based fraud investigation queries
        │
        ├── matches_graph_request()    ← Returns network graph visualisation
        │
        ├── build_balance_trend_response() ← Returns balance chart for an account
        │
        ├── build_timeseries_response() ← Returns transaction timeline chart
        │
        └── RAG fallback:
                ChromaDB semantic search
                        │
                Groq LLM synthesis
                        │
                Programmatic citation chips
```

### ChromaDB Vector Store (`vector_store.py`)

Transaction data is stored in ChromaDB as text chunks with rich metadata:
- `txn_id` — transaction identifier
- `account_id` — anonymised account ID
- `pattern_id` — fraud pattern IDs from the analysis
- `flag_reason` — why this transaction was flagged
- `date`, `amount`, `narration` — core fields for retrieval

Embeddings are generated using `sentence-transformers` (`all-MiniLM-L6-v2`). ChromaDB runs entirely on local disk — no internet required for vector search.

One ChromaDB **collection per investigation case** keeps data from different sessions cleanly separated.

### Chunking Strategy (`chunking_v2.py`)

Transactions are chunked into overlapping text windows. Each chunk includes:
- The transaction itself (date, narration, amount, balance)
- Its fraud pattern context (what was detected, why)
- Its account context (which account, what the account's risk tier is)

This ensures that semantic search retrieves contextually rich chunks rather than bare transaction rows.

### Specialised Query Handlers

Rather than routing all questions through the LLM, the chatbot first tries deterministic handlers:

| Handler | Handles |
|---------|---------|
| `try_id_lookup_answer()` | "What is account ACCT_003?" / "Show transaction TXN_0042" |
| `try_structured_answer()` | "What is the total debit for ACCT_001?" / "How many transactions on 2026-01-15?" |
| `try_aggregation_answer()` | "Sum of credits from UPI/9876543210" / "Average transaction amount this month" |
| `try_investigation_answer()` | "Which accounts show structuring?" / "Who is the most suspicious?" |
| `build_graph_response()` | "Show me the money flow graph" / "How are these accounts connected?" |
| `build_balance_trend_response()` | "Show ACCT_002's balance over time" |

Only when none of these handlers match does the system fall through to the full ChromaDB → Groq RAG pipeline.

### Context Resolution (`context_resolver.py`)

Handles follow-up questions: if an investigator asks "What else does it do?" after asking about ACCT_003, `resolve_followup()` injects the previous account ID into the query before it goes to ChromaDB. This makes multi-turn investigation conversations coherent.

### Language Support (`language.py`)

Detects the language of the investigator's question. If it is not English, translates it to English before retrieval, then translates the answer back to the original language. Supports Kannada and Hindi natively — important for CID Karnataka's investigative staff.

### LLM Model

The chatbot uses `openai/gpt-oss-120b` served on Groq's infrastructure (Groq LPU hardware, extremely low latency). This is distinct from OpenAI's GPT — Groq is a separate provider that hosts open-weight models on custom silicon.

---

## 10. API Layer — FastAPI Backend

The FastAPI backend (`api/main.py`) is the integration layer connecting the Python analysis pipeline to the React frontend.

### Endpoints

| Router | Prefix | Purpose |
|--------|--------|---------|
| `extraction.py` | `/api/extraction` | File upload, extraction run, status |
| `analysis.py` | `/api/analysis` | Trigger analysis, fetch results, scores |
| `cases.py` | `/api/cases` | Case management, session listing |
| `chat.py` | `/api/chat` | RAG chatbot query endpoint |
| `reports.py` | `/api/reports` | PDF/Excel report download |
| `fraud.py` | `/api/fraud` | Fraud pattern details, evidence |

### CORS Configuration

The API uses a regex-based CORS origin pattern `r"^http://(localhost|127\.0\.0\.1):\d+$"` — matching any localhost port. This handles Vite's behaviour of incrementing the port number (5173 → 5174 → 5175...) when a port is already in use, preventing CORS preflight failures during development.

### Session Management (`deps.py`)

Each investigation is assigned a unique `session_id` / `case_id` at the time of file upload. All subsequent API calls reference this ID to load the correct extraction results, analysis database, and ChromaDB collection for that case.

---

## 11. Frontend — React + TypeScript UI

The frontend is a full single-page application built with React + TypeScript + Vite, styled with Tailwind CSS, using shadcn/ui components.

### Pages

| Page | Route | Purpose |
|------|-------|---------|
| Landing | `/` | Project introduction, "Open Case" entry point |
| Extraction | `/extraction` | File upload, account hints, extraction progress |
| Analysis | `/analysis` | Suspicion scores, findings, interactive graph |
| Reports | `/reports` | Download PDF and Excel reports |
| Chatbot | `/chatbot` | Natural-language investigation interface |

### Key Components

| Component | Purpose |
|-----------|---------|
| `RelationshipGraph.tsx` | Interactive 3D money-flow network visualisation |
| `SimpleBarChart.tsx` | Suspicion score bar chart per account |
| `ChatBubble.tsx` | Chat message rendering with citation chips |
| `DataTable.tsx` | Sortable, filterable transaction table |
| `MetricCard.tsx` | KPI tiles (total accounts, total transactions, top suspect) |
| `DashboardLayout.tsx` | Sidebar navigation and layout wrapper |

### State Management (`useAppStore.ts`)

Zustand is used for global client state: current case ID, extraction results, analysis results, and chat history. The store persists the case ID to `sessionStorage` so a page refresh does not lose the active investigation.

---

## 12. Evaluation & Testing

### Synthetic Test Dataset

A comprehensive synthetic dataset was built to evaluate the system's detection accuracy. It covers all 23 fraud patterns across 20+ test cases:

```
synthetic_test_data/
├── pattern_01_duplicate_verification/
├── pattern_02_failed_reversed_transaction/
├── pattern_03_pass_through_routing/
├── pattern_04_fund_pooling/
├── pattern_05_structuring_smurfing/
├── pattern_07_circular_flow/
├── pattern_08_money_trail/
├── pattern_09_credit_to_cash_out/
├── pattern_10_cross_statement_links/
├── pattern_11_balance_parking/
├── pattern_12_hub_ranking/
├── pattern_13_low_value_testing/
├── pattern_14_reversal_clusters/
├── pattern_15_round_value_debit/
├── pattern_16_shared_upi/
├── pattern_17_round_trip/
├── pattern_18_dormant_reactivation/
├── pattern_19_first_contact_large_transfer/
├── pattern_22_llm_lead_unknown_shape/
└── pattern_23_ml_ensemble_unknown_shape/
```

Each pattern folder contains synthetic bank statements (PDF, CSV, Excel) with deliberately planted fraud signals and a `ground_truth.json` specifying exactly which accounts/transactions should be flagged.

### Regression Harness (`tools/regression_harness.py`)

A fully offline regression harness runs all synthetic test cases without making any API calls (using cached LLM responses). It computes precision, recall, and F1 for each pattern and reports any regressions vs. the previous run. This was run before and after every significant change to the extraction or analysis engine.

### Analysis Test Suite (`analysis/tests/`)

| Test File | What it covers |
|-----------|----------------|
| `test_pipeline.py` | End-to-end pipeline with synthetic inputs |
| `test_all_build_cases.py` | All 23 detection cases with known-pattern inputs |
| `test_heldout_cases.py` | Held-out cases the detectors were not tuned on |
| `test_false_positive_guards.py` | Clean accounts that should score zero |
| `test_case_structure.py` | Finding data structure integrity |
| `test_llm_assist_and_rotation.py` | Key rotation behaviour under simulated 429s |
| `test_priority_pattern_edge_cases.py` | Edge cases for Tier 1 pattern detectors |

### Extraction Test Suite (`tests/test_extraction.py`)

Tests the extraction pipeline end-to-end with real sample bank statements in all five supported formats.

### Evaluation Runner (`evaluation/`)

| Module | Purpose |
|--------|---------|
| `runner.py` | Orchestrates evaluation runs across all test cases |
| `scorer.py` | Computes precision / recall / F1 per pattern and overall |
| `report.py` | Generates a human-readable evaluation summary |

---

## 13. Technology Stack

### Python Backend

| Library | Version | Purpose |
|---------|---------|---------|
| `fastapi` | latest | REST API backend |
| `uvicorn` | latest | ASGI server |
| `pandas` | latest | Transaction data manipulation |
| `numpy` | latest | Numerical computation |
| `networkx` | latest | Money-flow graph construction and analysis |
| `scikit-learn` | latest | Isolation Forest anomaly detection |
| `pdfplumber` | latest | Digital PDF text and table extraction |
| `pymupdf` | latest | High-performance PDF rendering |
| `pytesseract` | latest | OCR via Tesseract engine |
| `pillow` | latest | Image processing for OCR pre-processing |
| `opencv-python` | latest | Image enhancement, deskewing, binarisation |
| `python-docx` | latest | Word document extraction |
| `openpyxl` | latest | Excel read/write |
| `xlrd` | ≥2.0.1 | Legacy `.xls` file reading |
| `groq` | latest | Groq API client (LLM + Vision) |
| `chromadb` | latest | Local vector database for RAG |
| `sentence-transformers` | latest | Text embeddings for ChromaDB |
| `reportlab` | latest | PDF generation (alternative path) |
| `matplotlib` | latest | Static charts and graphs |
| `plotly` | latest | Interactive charts and 3D graphs |
| `pyvis` | latest | Network graph visualisation |
| `jinja2` | latest | HTML report templating |
| `playwright` | latest | Headless Chromium PDF rendering |
| `python-dotenv` | latest | Environment variable management |
| `requests` | latest | Direct HTTP calls to Groq API |
| `streamlit` | latest | Development console / debugging UI |

### AI / LLM Stack

| Provider | Model | Used For |
|----------|-------|----------|
| Groq API | `openai/gpt-oss-120b` | RAG chatbot synthesis |
| Groq API | `llama-3.1-8b-instant` (or similar fast model) | Column identification, LLM structuring |
| Groq Vision | Vision model | OCR fallback for low-quality scans |
| scikit-learn | Isolation Forest | ML anomaly detection (no API — local) |
| sentence-transformers | `all-MiniLM-L6-v2` | ChromaDB embeddings (no API — local) |

### Frontend

| Library | Purpose |
|---------|---------|
| React 18 | UI framework |
| TypeScript | Type-safe JavaScript |
| Vite | Build tool and dev server |
| Tailwind CSS | Utility-first styling |
| shadcn/ui | Component library |
| Zustand | Lightweight state management |
| React Router | Client-side navigation |
| Plotly.js | Interactive charts and 3D graphs |

### Infrastructure

| Tool | Purpose |
|------|---------|
| SQLite | Per-case analysis database (zero server overhead) |
| ChromaDB | Local vector store (runs on disk, no server) |
| Tesseract OCR | Local OCR engine (no API dependency) |
| Playwright / Chromium | Headless browser for PDF rendering |

---

## 14. Repository Structure

```
survey-corps/
│
├── extraction/                  # Phase 2 — File parsing and standardisation
│   ├── router.py                # File type detection (5 routing paths)
│   ├── extractor_digital_pdf.py # pdfplumber-based PDF extraction
│   ├── extractor_ocr.py         # Tesseract + Groq Vision OCR
│   ├── extractor_excel_csv.py   # pandas-based Excel/CSV extraction
│   ├── extractor_docx.py        # python-docx extraction
│   ├── vision_extractor.py      # Groq Vision direct image reading
│   ├── llm_structurer.py        # Groq LLM document understanding
│   ├── llm_interface.py         # Provider-agnostic LLM interface
│   ├── column_identifier.py     # LLM-based column mapping
│   ├── standardiser.py          # Unified schema conversion
│   ├── validator.py             # Data quality checks
│   ├── account_extractor.py     # Account metadata extraction
│   ├── identifier_vault.py      # Account anonymisation mapping
│   ├── key_pool.py              # Multi-key Groq rotation
│   ├── chromadb_ingestor.py     # ChromaDB ingestion after extraction
│   ├── anonymiser.py            # PII anonymisation
│   ├── image_grouping.py        # Groups image pages for OCR
│   ├── storage.py               # Extraction result persistence
│   ├── report_generator.py      # Extraction summary report
│   └── extraction_pipeline.py  # Main orchestrator
│
├── analysis/                    # Phase 3 — Fraud detection
│   └── analysis_engine/
│       ├── pipeline.py          # Main analysis orchestrator
│       ├── models.py            # Pattern catalog, Finding dataclass
│       ├── scoring.py           # Tiered suspicion scoring
│       ├── graph.py             # NetworkX money-flow graph
│       ├── graph_generator.py   # Chart and graph export
│       ├── database.py          # SQLite read/write
│       ├── baseline.py          # Per-account statistical baselines
│       ├── counterparties.py    # Counterparty resolution from narrations
│       ├── narration.py         # LLM-powered finding explanations
│       ├── balance.py           # Balance arithmetic and trend analysis
│       ├── llm_client.py        # Groq client with key rotation
│       ├── llm_resolution.py    # LLM-assisted counterparty linking
│       ├── anomaly_investigator.py # LLM hypothesis generation (Pattern 22)
│       ├── case_structure.py    # Finding structure enforcement
│       ├── ingest.py            # Transaction loading
│       ├── output.py            # Results serialisation
│       ├── config.py            # Analysis configuration
│       ├── utils.py             # Shared utilities
│       ├── rich_report.py       # Terminal analysis summary
│       └── detectors/           # One file per fraud pattern
│           ├── accumulation.py
│           ├── circular.py
│           ├── common.py        # Shared detector utilities
│           ├── credit_to_cash.py
│           ├── cross_statement.py
│           ├── dormant_reactivation.py
│           ├── duplicates.py
│           ├── first_contact.py
│           ├── high_throughput.py
│           ├── holding_accounts.py
│           ├── hub_ranking.py
│           ├── internal_flow_hub.py
│           ├── low_value_testing.py
│           ├── ml_ensemble.py
│           ├── money_trail.py
│           ├── reversal_clusters.py
│           ├── reversals.py
│           ├── round_trip.py
│           ├── round_value_debits.py
│           ├── shared_upi.py
│           ├── structuring.py
│           ├── suspicious_ranking.py
│           └── transit.py
│   └── tests/                   # Analysis test suite
│
├── reporting/                   # Phase 4 — Report generation
│   ├── build_report.py          # HTML → PDF via Playwright
│   ├── report_data.py           # Data assembly for template
│   ├── report_llm.py            # LLM report enhancement
│   ├── report_template.html     # Jinja2 A4 HTML template
│   ├── narration.py             # Report narration utilities
│   └── i18n.py                  # Multilingual support
│
├── chatbot/                     # Phase 5 — RAG chatbot
│   ├── rag_chat.py              # Main chatbot entry point
│   ├── vector_store.py          # ChromaDB operations
│   ├── chunking_v2.py           # Transaction → text chunks
│   ├── reasoning_engine.py      # Multi-step reasoning
│   ├── structured_queries.py    # Deterministic data queries
│   ├── aggregations.py          # SUM/COUNT/AVG queries
│   ├── investigation_queries.py # Fraud-pattern queries
│   ├── id_lookup.py             # Direct ID lookup
│   ├── context_resolver.py      # Follow-up question resolution
│   ├── graph_viz.py             # Graph visualisation responses
│   ├── balance_chart.py         # Balance trend chart responses
│   ├── timeseries_chart.py      # Transaction timeline responses
│   ├── language.py              # Multilingual support
│   ├── briefing.py              # Case brief context injection
│   ├── case_analytics.py        # Case-level analytics
│   ├── case_registry.py         # Active case management
│   ├── chat_history.py          # Conversation memory
│   ├── counterparty.py          # Counterparty analysis queries
│   ├── frequency_analysis.py    # Transaction frequency queries
│   ├── data_loader.py           # Transaction data loading for chatbot
│   └── structuring.py           # Structuring alert formatting
│
├── api/                         # FastAPI backend
│   ├── main.py                  # App setup, CORS, router registration
│   ├── deps.py                  # Session management, case loading
│   ├── utils.py                 # Shared API utilities
│   └── routers/
│       ├── extraction.py        # /api/extraction endpoints
│       ├── analysis.py          # /api/analysis endpoints
│       ├── cases.py             # /api/cases endpoints
│       ├── chat.py              # /api/chat endpoints
│       ├── reports.py           # /api/reports endpoints
│       └── fraud.py             # /api/fraud endpoints
│
├── chatbot_ui/                  # React + TypeScript frontend
│   └── frontend/
│       └── src/
│           ├── pages/           # Landing, Extraction, Analysis, Reports, Chatbot
│           ├── components/      # UI components (charts, tables, chat, layout)
│           ├── store/           # Zustand state management
│           ├── hooks/           # Custom React hooks
│           ├── lib/             # API client, utilities
│           └── types/           # TypeScript type definitions
│
├── config/
│   └── settings.py              # Central configuration (paths, keys, thresholds)
│
├── evaluation/                  # Evaluation framework
│   ├── runner.py
│   ├── scorer.py
│   └── report.py
│
├── tools/                       # Developer tools
│   ├── regression_harness.py    # Offline regression testing
│   ├── run_batch.py             # Batch processing utility
│   └── verify_batch.py          # Batch verification
│
├── tests/                       # Integration tests
│   └── test_extraction.py
│
├── app.py                       # Streamlit development console
├── evaluate.py                  # Evaluation CLI entry point
├── run_case.py                  # CLI: run a single case
├── validate_original_run.py     # Validate against original run results
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── .gitignore
```

---

## 15. Environment & Configuration

### Environment Variables (`.env`)

```
# Groq API keys — separate keys per role to avoid quota conflicts
GROQ1=gsk_...    # Text pool key 1 (extraction)
GROQ2=gsk_...    # Text pool key 2
GROQ3=gsk_...    # Analysis phase dedicated key
GROQ4=gsk_...    # Vision pool key 1 (OCR fallback)
GROQ5=gsk_...    # Vision pool key 2
...

# Optional: path to Tesseract binary (auto-detected if on PATH)
TESSERACT_CMD=/opt/homebrew/bin/tesseract
```

### Configuration (`config/settings.py`)

All thresholds and paths are centralised:

| Setting | Purpose |
|---------|---------|
| `DIGITAL_PDF_CHAR_THRESHOLD` | Min characters to classify PDF as digital (not scanned) |
| `MIN_COMPLETENESS_RATIO` | Minimum fraction of rows that must have all required fields |
| `STANDARD_COLUMNS` | The 7 canonical column names of the standard schema |
| `SUPPORTED_EXTENSIONS` | List of allowed file extensions |
| `UPLOAD_DIR` | Where uploaded files are saved |
| `LLM_CACHE_DIR` | Where Groq API responses are cached |
| `CHROMADB_DIR` | Where ChromaDB vector store is persisted |

### Running the System

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Tesseract (macOS)
brew install tesseract

# 3. Install Playwright browser for PDF rendering
.report_venv/bin/playwright install chromium

# 4. Copy and fill .env
cp .env.example .env
# Fill in your Groq API keys

# 5. Start the FastAPI backend
uvicorn api.main:app --reload --port 8000

# 6. Start the React frontend
cd chatbot_ui/frontend
npm install
npm run dev
```

---

## 16. Key Engineering Decisions

### Why Groq and not OpenAI/Claude for the LLM calls?

Groq runs open-weight models on custom LPU (Language Processing Unit) hardware, delivering significantly lower latency than standard GPU inference. For an investigation platform where the investigator is watching extraction progress in real time, response speed matters more than marginal accuracy differences between similarly sized models.

### Why SQLite per run instead of a shared database?

Each analysis run's SQLite database (`analysis.db`) is self-contained. The investigator can copy it and share it. There is no shared database server to manage. For a tool used by CID investigators across different stations, a zero-server-setup approach is critical.

### Why Playwright for PDF generation instead of ReportLab?

ReportLab produces PDFs programmatically but requires coding every layout detail. Playwright lets us write the report layout in HTML/CSS — a far more expressive medium — and then renders it pixel-perfectly to A4. The result is a professionally formatted report that looks designed, not generated.

### Why two separate ChromaDB collections (one per case)?

If all cases shared one collection, a query like "show me structuring patterns" would retrieve results from any previously investigated case. Scoping one collection per `case_id` ensures that chatbot queries are always answerable from the current investigation's data only.

### Why not use a single Groq API key?

Groq's free tier enforces a daily token quota per key. A multi-file extraction run (20+ bank statements) can exhaust a single key's quota. The `GroqKeyPool` system allows multiple keys across two roles (text, vision) with automatic rotation on quota exhaustion, making the system practically quota-proof for hackathon-scale demonstrations.

---

*CIDECODE Hackathon 2026 — Survey Corps — CID Karnataka / PES University, Bengaluru*
