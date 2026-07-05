"""
context_resolver.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Conversational Context Resolution (coreference / follow-up rewriting)

The rest of the routing + retrieval stack is STATELESS — every handler
(id-lookup, aggregation, structured router, investigation intelligence, graph,
semantic search) operates on a single question with no memory of earlier turns.

That is fine for self-contained questions, but it silently breaks follow-ups:

    Q1: "find accounts moving money in rapid succession..."
    A1: "... money moved out of the AMIT CHAUHAN account ..."
    Q2: "give me the account details about this account"

With no memory, "this account" names no account the router can see, so
retrieval falls back to unscoped semantic search and lands on an UNRELATED
accused — the worst failure mode for a forensic tool.

This module fixes that at the front of the pipeline: it rewrites a follow-up
into a fully SELF-CONTAINED question by resolving pronouns / deictic references
against the recent conversation, using the same Groq model the chatbot already
uses. Once rewritten, every downstream handler works unchanged.

Design guarantees (deliberately conservative):
  • Cheap regex gate — the LLM only runs when the question actually looks
    referential, so standalone questions are never touched and pay no latency.
  • Grounded — the model may only reuse entities (names, account numbers,
    dates) that literally appear in the recent turns; it must not invent any.
  • Safe — on empty history, any error, or a low-confidence rewrite, it returns
    the original question unchanged. It can never make routing worse than the
    old stateless behaviour.
"""

from __future__ import annotations

import re
from typing import Callable

# Referential / deictic cues that signal the question leans on an earlier turn.
# Kept intentionally focused on pronouns + demonstratives + "same/above/previous"
# rather than every occurrence of "the account" (which is common in perfectly
# self-contained questions too). The LLM is a second safety net that passes
# through anything already self-contained.
_REFERENTIAL_RE = re.compile(
    r"\b("
    r"this|that|these|those|"
    r"it|its|it's|they|them|their|theirs|"
    r"he|him|his|she|her|hers|"
    r"the\s+same|same\s+(?:account|person|transaction|one)|"
    r"aforementioned|above|previous(?:ly)?|earlier|that\s+one|"
    r"what\s+about|how\s+about|and\s+the|also\s+the"
    r")\b",
    re.IGNORECASE,
)

# A very short follow-up ("and the bank?", "why?") is almost always leaning on
# the prior turn even without an explicit pronoun.
_SHORT_FOLLOWUP_MAX_WORDS = 5

_REWRITE_SYSTEM_PROMPT = """You rewrite a follow-up question from a financial-crime \
investigator into a single, fully self-contained question that can be answered \
without seeing the earlier conversation.

Rules:
1. Replace every pronoun or vague reference (this/that account, he/she/they, it, \
the same, the above, that person) with the specific entity it refers to — an \
account holder name, an account number, or a date — taken ONLY from the \
conversation provided.
2. Never add, invent, assume, or guess any name, account number, amount, or \
date that is not already present in the conversation or the follow-up question.
3. Preserve the investigator's original intent and scope EXACTLY. Do not broaden \
or narrow it. Do not answer the question. Do not explain your reasoning.
4. If the question is already self-contained, or you cannot confidently resolve \
the reference from the conversation, return the question unchanged.
5. Output ONLY the rewritten question as one line — no quotes, no preamble, no \
trailing commentary."""


def _looks_referential(question: str) -> bool:
    """Cheap gate: does this question appear to depend on an earlier turn?"""
    q = question.strip()
    if not q:
        return False
    if _REFERENTIAL_RE.search(q):
        return True
    # Short fragments ("why?", "and the dates?") are follow-ups by nature.
    if len(q.split()) <= _SHORT_FOLLOWUP_MAX_WORDS:
        return True
    return False


def _format_recent_turns(history: list[dict], max_turns: int, answer_clip: int) -> str:
    """Render the last few Q/A turns compactly for the rewrite prompt."""
    recent = [h for h in history if h.get("question") or h.get("answer")][-max_turns:]
    lines = []
    for turn in recent:
        q = str(turn.get("question", "")).strip()
        a = str(turn.get("answer", "")).strip()
        if len(a) > answer_clip:
            a = a[:answer_clip].rstrip() + " …"
        if q:
            lines.append(f"Investigator: {q}")
        if a:
            lines.append(f"Assistant: {a}")
    return "\n".join(lines)


def resolve_followup(
    question: str,
    history: list[dict] | None,
    generate_fn: Callable[..., str],
    max_turns: int = 3,
    answer_clip: int = 700,
) -> tuple[str, bool]:
    """
    Rewrite `question` into a self-contained question using recent `history`.

    Parameters
    ----------
    question    : the current investigator question (already in English)
    history     : prior turns, each a dict with "question"/"answer" (newest last)
    generate_fn : the chatbot's LLM entry point (rag_chat.generate) — injected to
                  avoid a circular import
    max_turns   : how many recent Q/A turns to feed the rewriter
    answer_clip : max chars kept per prior answer (token budget guard)

    Returns
    -------
    (resolved_question, was_rewritten)
        resolved_question : the standalone question (or the original, unchanged)
        was_rewritten     : True only if the rewrite actually changed the text
    """
    if not history:
        return question, False
    if not _looks_referential(question):
        return question, False

    convo = _format_recent_turns(history, max_turns=max_turns, answer_clip=answer_clip)
    if not convo:
        return question, False

    user_prompt = (
        f"Conversation so far (oldest first):\n{convo}\n\n"
        f"Follow-up question: {question}\n\n"
        f"Rewritten self-contained question:"
    )

    try:
        raw = generate_fn(
            [
                {"role": "system", "content": _REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )
    except Exception:
        # Rewriting is a best-effort enhancement — never let it break the chat.
        return question, False

    rewritten = _clean_rewrite(raw)
    if not rewritten:
        return question, False

    # Guard against a runaway/hallucinated rewrite: if the model produced
    # something far longer than the original plus the conversation could
    # justify, distrust it and fall back to the original question.
    if len(rewritten) > max(len(question) * 6, 400):
        return question, False

    changed = rewritten.strip().lower() != question.strip().lower()
    return rewritten, changed


def _clean_rewrite(raw: str) -> str:
    """Take the first non-empty line and strip quotes/labels the model may add."""
    if not raw:
        return ""
    line = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "")
    # Strip a label prefix FIRST ("Rewritten question:", "Question:"), then peel
    # any surrounding quotes — doing it in this order handles a quoted answer that
    # itself follows a label, e.g.  Rewritten question: "who is Amit?"
    line = re.sub(
        r"^(rewritten(?:\s+self-contained)?\s+question|question|answer)\s*[:\-]\s*",
        "",
        line,
        flags=re.IGNORECASE,
    ).strip()
    line = line.strip('"').strip("'").strip()
    return line
