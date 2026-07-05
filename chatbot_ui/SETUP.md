# Survey Corps — Setup Guide (React UI + backend)

This gets the **React frontend** running on your machine. Important: the React UI is
only the presentation layer — it talks to a **Python (FastAPI) backend** that does the
real work (extraction, analysis, chatbot). You must run **both** at the same time:

```
[ React frontend  http://localhost:5173 ]  ──▶  [ FastAPI backend  http://localhost:8001 ]
```

You'll use **two terminals** — one for the backend, one for the frontend.

Estimated time: ~15 minutes (plus package downloads).

---

## 1. Prerequisites (install these first)

| Tool | Why | Get it |
|---|---|---|
| **Python 3.10+** | runs the backend | https://www.python.org/downloads/ (tick "Add Python to PATH" on Windows) |
| **Node.js 20.19+** (LTS 22 recommended) | runs the React frontend | https://nodejs.org/ |
| **Tesseract OCR** | reads scanned/photo statements | Win: https://github.com/UB-Mannheim/tesseract/wiki · macOS: `brew install tesseract` · Linux: `sudo apt install tesseract-ocr` |

Verify:
```
python --version
node --version
npm --version
```

---

## 2. Unzip the project

Unzip somewhere simple, e.g. `C:\Projects\Survey-Corps\`. Everything below is run from
inside that folder (the one containing the `api/` and `frontend/` folders).

---

## 3. Start the BACKEND (Terminal 1)

From the **project root**:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> First install downloads some large packages (torch, sentence-transformers,
> chromadb). Give it a few minutes.

### Add the API keys
I'll send you the Groq API keys separately. Create a file named **`.env`** in the
**project root** (next to `requirements.txt`) with:
```
GROQ1=<key 1>
GROQ2=<key 2>
GROQ3=<key 3>
GROQ4=<key 4>
GROQ5=<key 5>

GROQ_API_KEY=<main key>
```

### Run the backend — **must be port 8001**
```
uvicorn api.main:app --reload --port 8001
```
Leave this terminal running. Check it works by opening
http://localhost:8001/api/health — you should see `{"status":"ok"}`.

> Port 8001 is required — the frontend's `frontend/.env` is set to
> `VITE_API_URL=http://localhost:8001`. If you change one, change both.

---

## 4. Start the FRONTEND (Terminal 2)

Open a **second** terminal, then:

```
cd frontend
npm install
npm run dev
```

Vite prints a local URL — open **http://localhost:5173** in your browser.
(If 5173 is busy it picks 5174/5175 — that's fine, the backend allows any localhost
port.)

You now have the full app: the React UI in the browser, backed by the Python engine.

---

## 5. Using it

Work left-to-right through the app:

1. **Extraction** — upload a bank statement (PDF / scanned image / Excel / CSV). A
   sample dataset is included in the zip if you want something to try immediately.
2. **Analysis** — flags, counterparties, relationship graph.
3. **Chatbot** — ask about the case in plain English (needs a case extracted first, and
   uses the Groq keys from step 3).
4. **Reports** — generate the forensic report.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| UI loads but every action fails / "Failed to fetch" | The backend isn't running, or it's on the wrong port. It must be on **8001** (step 3) and Terminal 1 must stay open. |
| `{"status":"ok"}` check fails | Backend didn't start — look at Terminal 1 for the error (usually a missing package or bad `.env`). |
| PowerShell blocks `Activate.ps1` | Run `Set-ExecutionPolicy -Scope Process RemoteSigned`, then activate again. |
| Chatbot errors / "no API key" | Check `.env` exists in the project root and keys are pasted correctly (no quotes/trailing spaces). |
| `npm install` fails | Make sure Node is 20.19+ (`node --version`). Delete `frontend/node_modules` and retry. |
| OCR fails on scanned PDFs | Install Tesseract (step 1) and restart the backend. |
| `ModuleNotFoundError` (backend) | Re-run `pip install -r requirements.txt` with the venv active. |

---

Two terminals must stay open while you use the app: **backend (8001)** and
**frontend (5173)**. Any issues, send me a screenshot of both terminals.
