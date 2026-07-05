from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import invalidate_case, load_case_resources
from chatbot.chat_history import append_to_history, load_history
from chatbot.rag_chat import handle_investigator_question

router = APIRouter(prefix="/api/cases/{case_id}/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


def _resources(case_id: str):
    try:
        return load_case_resources(case_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _chart_to_json(chart):
    if chart is None:
        return None
    try:
        # Plotly figures carry numpy arrays / pandas Timestamps in their trace
        # data, which FastAPI's default jsonable_encoder can't serialize.
        # fig.to_json() runs it through Plotly's own encoder first (numpy ->
        # list, Timestamp -> ISO string), giving back a plain JSON-safe dict.
        return json.loads(chart.to_json())
    except Exception:
        return None


@router.get("/status")
def chat_status():
    # The chatbot accepts any configured Groq key — the numbered pool (GROQ1..GROQ10)
    # or GROQ_API_KEY(S) — not just GROQ_API_KEY, so report accordingly.
    from chatbot.rag_chat import chatbot_groq_keys

    return {"groq_configured": bool(chatbot_groq_keys())}


@router.get("/history")
def get_history(case_id: str):
    resources = _resources(case_id)
    entries = load_history(resources["case_dir"])
    messages = []
    for entry in entries:
        messages.append({"role": "user", "content": entry["question"]})
        messages.append({
            "role": "assistant",
            "content": entry["answer"],
            "meta": f"{entry.get('timestamp', '')} · {entry.get('language', '?')} · {entry.get('matched_pattern', 'semantic_search')}",
            "citations": [],
        })
    return {"messages": messages}


@router.post("")
def ask_question(case_id: str, body: ChatRequest):
    if not body.question or not body.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    resources = _resources(case_id)
    case = resources["case"]
    collection = resources["collection"]
    case_dir = resources["case_dir"]

    # Prior turns for THIS case, so follow-ups ("this account", "he", "the same")
    # resolve to the account the investigator actually means instead of an
    # unrelated one. Newest-last; the resolver clips/limits how much it uses.
    history = load_history(case_dir)

    try:
        result = handle_investigator_question(
            body.question, case, collection,
            structuring_by_account=resources.get("structuring_by_account"),
            history=history,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {exc}") from exc

    append_to_history(
        case_dir, body.question, result["answer"],
        result["detected_language"], result.get("matched_pattern"),
    )

    return {
        "answer": result["answer"],
        "citations": result.get("citations") or [],
        "matched_pattern": result.get("matched_pattern") or "semantic_search",
        "detected_language": result.get("detected_language"),
        "structuring_alerts": result.get("structuring_alerts") or [],
        "graph_html": result.get("graph_html"),
        "disclaimer": result.get("disclaimer"),
        "chart": _chart_to_json(result.get("chart")),
    }


@router.post("/reindex")
def reindex(case_id: str):
    invalidate_case(case_id)
    resources = _resources(case_id)
    return {"indexed_chunks": resources["indexed_count"]}
