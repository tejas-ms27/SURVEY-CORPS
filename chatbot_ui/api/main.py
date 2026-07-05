"""
Survey Corps — Financial Forensics Engine (FastAPI backend).

Run from the project root:
    uvicorn api.main:app --reload --port 8000

Wraps the exact same project logic app.py (the Streamlit console) uses —
extraction pipeline, case analytics, RAG chatbot — behind a REST API so the
React frontend can drive it.
"""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from api.routers import analysis, cases, chat, extraction, reports  # noqa: E402

app = FastAPI(title="Survey Corps — Financial Forensics Engine API")

app.add_middleware(
    CORSMiddleware,
    # Vite picks the next free port (5174, 5175, ...) whenever 5173 is
    # already taken, so pin to localhost/127.0.0.1 on any port rather than
    # one hardcoded port — a mismatch here fails CORS preflight with a 400,
    # which surfaces in the browser as an opaque "Failed to fetch".
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(extraction.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
