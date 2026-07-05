"""
chat_history.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Persistent Per-Case Chat History

Every investigator question/answer pair is written to a JSON file that lives
INSIDE the case folder (chat_history.json), so history is scoped to the case
and survives a page reload or app restart — unlike st.session_state, which
resets. The raw (as-typed) question is stored, so Kannada questions appear in
the history in Kannada exactly as the investigator wrote them.
"""

import json
from datetime import datetime
from pathlib import Path


def get_history_path(case_dir: str | Path) -> Path:
    return Path(case_dir) / "chat_history.json"


def load_history(case_dir: str | Path) -> list[dict]:
    """Return the saved Q&A entries for a case (newest last), or [] if none."""
    path = get_history_path(case_dir)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        # A corrupt/half-written history file should never break the chat.
        return []


def append_to_history(
    case_dir: str | Path,
    question: str,
    answer: str,
    language: str,
    matched_pattern: str | None,
) -> None:
    """Append one Q&A pair (timestamped) to the case's chat_history.json."""
    history = load_history(case_dir)
    history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question": question,
        "answer": answer,
        "language": language,
        "matched_pattern": matched_pattern or "semantic_search",
    })
    path = get_history_path(case_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
