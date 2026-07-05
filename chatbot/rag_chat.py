"""
rag_chat.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: RAG Answer Generation (Groq API + ChromaDB)

KEY DESIGN DECISION — structural citations:
  We do NOT trust the LLM to "cite correctly" in its own generated prose —
  instead:
    1. ChromaDB retrieval gives us the exact metadata (txn_id, account_id,
       flag_reason, pattern_id, etc.) for every chunk used.
    2. The LLM is only asked to SYNTHESIZE a natural-language answer from
       the retrieved text.
    3. We programmatically attach citation chips built from the retrieved
       metadata — guaranteed correct because they come directly from the
       database, not from the model's generation.
  This still matters even on a strong API model: it removes an entire class
  of failure (ID/date hallucination) by construction rather than relying on
  instruction-following alone.

PROVIDER NOTE — this uses GROQ (console.groq.com, custom LPU hardware,
extremely fast inference), NOT xAI's Grok. These are two different
companies with confusingly similar names — the extraction pipeline's
"groq" column-map source already confirmed Groq was the provider in use.
Endpoint: https://api.groq.com/openai/v1/chat/completions
Env var:  GROQ_API_KEY (NOT XAI_API_KEY — different provider, different key)

PURE-API BUILD — no local/Ollama fallback. This trades the offline-safety
net of a local model for speed and answer quality. Be aware this means the
chatbot depends on a live internet connection and the Groq API being up —
worth testing venue WiFi reliability ahead of the actual demo if this
matters for your situation.

Requires: requests, and a GROQ_API_KEY environment variable.
"""

import os
import re

import requests

from chatbot.vector_store import get_client, get_collection, query, build_metadata_filter
from chatbot.structured_queries import try_structured_answer
from chatbot.language import detect_and_translate_to_english, translate_answer
from chatbot.id_lookup import try_id_lookup_answer
from chatbot.aggregations import try_aggregation_answer
from chatbot.investigation_queries import try_investigation_answer
from chatbot.graph_viz import matches_graph_request, build_graph_response
from chatbot.balance_chart import build_balance_trend_response
from chatbot.timeseries_chart import build_timeseries_response
from chatbot.structuring import format_structuring_alert
from chatbot.context_resolver import resolve_followup

# openai/gpt-oss-120b is Groq's current recommended strong general model as
# of mid-2026 (llama-3.3-70b-versatile and llama-3.1-8b-instant were
# deprecated June 17, 2026). Swap to "qwen/qwen3-32b" if you want to compare
# — both are live on Groq's free tier.
GROQ_MODEL_NAME = "openai/gpt-oss-120b"


# Status codes where a DIFFERENT key may still succeed: rate limits (429), transient
# server errors (5xx), and per-key auth failures (401/403 — a single revoked/typo'd key
# in the pool). On these we rotate to the next configured key instead of failing the
# whole chat. Request-level errors (400/413/422 — same on every key) are surfaced
# immediately rather than looping.
_ROTATABLE_STATUS = {401, 403, 429, 500, 502, 503, 504}


def chatbot_groq_keys() -> list[str]:
    """All Groq keys available to the chatbot, in try order.

    GROQ10 is the chatbot's OWN dedicated lane, so it is tried FIRST (it doesn't
    compete with the extraction/analysis pools). The other numbered keys GROQ1..GROQ9
    and GROQ_API_KEY(S) follow as fallbacks used only when the dedicated key is over
    its rate limit. Deduplicated, order preserved."""
    keys: list[str] = []

    def _add(value: str | None) -> None:
        for part in re.split(r"[,\s]+", str(value or "")):
            part = part.strip()
            if part and part not in keys:
                keys.append(part)

    _add(os.environ.get("GROQ10"))
    for i in range(1, 10):
        _add(os.environ.get(f"GROQ{i}"))
    _add(os.environ.get("GROQ_API_KEYS"))
    _add(os.environ.get("GROQ_API_KEY"))
    return keys


def generate(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
) -> str:
    """
    Single entry point for LLM generation — calls the Groq API directly.

    Rotates across every configured Groq key (see chatbot_groq_keys): if the dedicated
    chatbot key is rate-limited, the request falls through to the next key rather than
    failing the chat. Raises a clear error only when no key is configured or every key
    is exhausted, so callers can degrade gracefully.
    """
    keys = chatbot_groq_keys()
    if not keys:
        raise RuntimeError(
            "No chatbot Groq key set. Add GROQ10=<key> (or GROQ_API_KEY=<key>) to the "
            "project-root .env file. Get a key from console.groq.com."
        )

    last_error = ""
    for idx, api_key in enumerate(keys):
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model or GROQ_MODEL_NAME,
                    "messages": messages,
                    "temperature": temperature,
                },
                timeout=30,
            )
        except requests.RequestException as exc:  # network / timeout → try next key
            last_error = f"request error: {exc}"
            continue

        if response.ok:
            return response.json()["choices"][0]["message"]["content"].strip()

        last_error = f"{response.status_code}: {response.text[:200]}"
        # A rate-limited / transient error on THIS key: rotate to the next one. On the
        # last key this falls through to the clean RuntimeError below (a consistent,
        # catchable signal) instead of surfacing a raw provider error.
        if response.status_code in _ROTATABLE_STATUS:
            print(f"[rag_chat] Groq key #{idx + 1} returned {response.status_code}; "
                  f"{'rotating to next key.' if idx < len(keys) - 1 else 'no keys left.'}")
            continue
        # Auth error / bad request — a different key won't help; surface it immediately.
        print(f"[rag_chat] Groq API error {response.status_code}: {response.text}")
        response.raise_for_status()

    # Every key was rate-limited / erroring — a clear, catchable signal for callers.
    raise RuntimeError(f"All {len(keys)} chatbot Groq keys are unavailable "
                       f"(rate-limited or erroring). Last error: {last_error}")

_SYSTEM_PROMPT = """You are a forensic financial investigation assistant helping \
a police cyber-crime investigator analyze bank transaction data and flagged \
fraud patterns.

Rules:
1. Answer ONLY using the retrieved context provided below. Do not invent \
transactions, accounts, or amounts that are not present in the context.
2. If the retrieved context does not contain enough information to answer \
confidently, say so plainly rather than guessing.
3. Write in clear, plain language suitable for a police officer — avoid \
unnecessary jargon.
4. Do NOT include transaction IDs, reference numbers, or pattern IDs in your \
own text — citations will be attached separately and automatically. Focus \
purely on explaining what happened and why it matters.
5. Keep your answer focused and concise — 2-5 sentences unless the question \
specifically asks for a detailed breakdown.
"""


def build_context_block(retrieved: dict) -> str:
    """
    Format retrieved chunks into a context block for the prompt.
    """
    lines = []
    for i, doc in enumerate(retrieved["documents"], start=1):
        lines.append(f"[Context {i}] {doc}")
    return "\n".join(lines)


def build_citations(retrieved: dict) -> list[dict]:
    """
    Build a structurally-guaranteed citation list from retrieved metadata.
    This is what gets rendered as "citation chips" in the UI — it does NOT
    depend on anything the LLM generated.

    Handles all four real chunk types produced by chunking_v2.py:
    transaction, flagged_transaction, duplicate_transaction, account_context
    (plus fraud_pattern, once that module's output exists).
    """
    citations = []
    for meta, dist in zip(retrieved["metadatas"], retrieved["distances"]):
        chunk_type = meta.get("chunk_type")
        relevance = round(1 - dist, 3)

        if chunk_type == "transaction":
            citations.append({
                "type": "transaction",
                "ref": meta["txn_id"],
                "account": meta["account_id"],
                "date": meta["date"],
                "relevance": relevance,
            })
        elif chunk_type == "flagged_transaction":
            citations.append({
                "type": "flagged_transaction",
                "account": meta["account_id"],
                "date": meta["date"],
                "flag_reason": meta["flag_reason"],
                "relevance": relevance,
            })
        elif chunk_type == "duplicate_transaction":
            citations.append({
                "type": "duplicate_transaction",
                "account": meta["account_id"],
                "date": meta["date"],
                "duplicate_row": meta["duplicate_row_number"],
                "original_row": meta["original_row_number"],
                "relevance": relevance,
            })
        elif chunk_type == "account_context":
            citations.append({
                "type": "account_context",
                "account": meta["account_id"],
                "bank_name": meta["bank_name"],
                "relevance": relevance,
            })
        elif chunk_type == "fraud_pattern":
            # fraud_pattern chunks come from two sources with slightly different
            # metadata: the original pattern chunker (chunking_v2) sets pattern_id,
            # while deep-analysis chunks (api/analysis_index) reuse this chunk_type
            # without a pattern_id. Use .get() so a missing key never crashes the
            # whole chatbot response.
            citations.append({
                "type": "fraud_pattern",
                "ref": meta.get("pattern_id") or meta.get("source") or "deep_analysis",
                "pattern_type": meta.get("pattern_type", "fraud_analysis"),
                "severity": meta.get("severity", "high"),
                "relevance": relevance,
            })
    return citations


def _format_conversation_context(history: list[dict] | None, max_turns: int = 3) -> str:
    """
    Render the last few Q/A turns as a compact block the semantic-answer LLM can
    use to understand what the current question refers to. Answers are clipped so
    a long prior reply can't dominate the prompt's token budget.
    """
    if not history:
        return ""
    recent = [h for h in history if h.get("question") or h.get("answer")][-max_turns:]
    lines = []
    for turn in recent:
        q = str(turn.get("question", "")).strip()
        a = str(turn.get("answer", "")).strip()
        if len(a) > 500:
            a = a[:500].rstrip() + " …"
        if q:
            lines.append(f"Investigator: {q}")
        if a:
            lines.append(f"Assistant: {a}")
    return "\n".join(lines)


def ask(
    collection,
    question: str,
    n_results: int = 5,
    account_id: str | None = None,
    pattern_type: str | None = None,
    severity: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """
    Full RAG query: retrieve relevant chunks, generate an answer via Groq,
    and return the answer alongside structurally-attached citations.

    Parameters
    ----------
    collection   : a ChromaDB collection (from vector_store.get_collection)
    question     : the investigator's natural-language question
    n_results    : how many chunks to retrieve
    account_id, pattern_type, severity : optional metadata filters,
                   pass these through if your UI has filter controls,
                   or if you parse them out of the question beforehand

    Returns
    -------
    dict with keys: "answer" (str), "citations" (list[dict]), "context_used" (str)
    """
    where = build_metadata_filter(
        account_id=account_id, pattern_type=pattern_type, severity=severity
    )

    retrieved = query(collection, question, n_results=n_results, where=where)

    if not retrieved["documents"]:
        return {
            "answer": (
                "I couldn't find any relevant transactions or flagged patterns "
                "for that question in the current case data."
            ),
            "citations": [],
            "context_used": "",
        }

    context_block = build_context_block(retrieved)
    citations = build_citations(retrieved)

    convo_block = _format_conversation_context(history)
    conversation_prefix = (
        f"Earlier in this conversation (for reference only — do NOT treat as "
        f"evidence):\n{convo_block}\n\n"
        if convo_block
        else ""
    )

    user_prompt = (
        f"{conversation_prefix}"
        f"Retrieved context:\n{context_block}\n\n"
        f"Investigator's question: {question}\n\n"
        f"Answer the question using ONLY the retrieved context above as evidence. "
        f"Use the earlier conversation only to understand what the question refers "
        f"to (for example who 'this account' or 'they' means), never as a source "
        f"of facts. Connect information across the retrieved chunks where they "
        f"describe the same account, counterparty, or money trail."
    )

    answer_text = generate([
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    return {
        "answer": answer_text,
        "citations": citations,
        "context_used": context_block,
    }


def format_citations_for_display(citations: list[dict]) -> str:
    """
    Render citation chips as plain text for the CLI demo.
    The dashboard's Tab 5 should render these as clickable chips instead,
    linking back to the relevant row in Tab 3 (Transaction Ledger).

    Uses .get() rather than bare indexing throughout, since citations from
    structured_queries.py (deterministic matches) don't carry a relevance
    score or always a date — only semantic-search citations (from
    build_citations()) have those fields populated.
    """
    if not citations:
        return "(no citations)"

    def _rel(c):
        r = c.get("relevance")
        return f" (relevance: {r})" if r is not None else ""

    lines = []
    for c in citations:
        if c["type"] == "transaction":
            lines.append(
                f"  [TXN {c.get('ref', '?')}] {c['account']} — {c.get('date', '?')}{_rel(c)}"
            )
        elif c["type"] == "flagged_transaction":
            lines.append(
                f"  [FLAGGED] {c['account']} — {c.get('date', '?')} — "
                f"reason: {c.get('flag_reason', '?')}{_rel(c)}"
            )
        elif c["type"] == "duplicate_transaction":
            lines.append(
                f"  [DUPLICATE] {c['account']} — {c.get('date', '?')} — "
                f"row {c.get('duplicate_row', '?')} duplicates row {c.get('original_row', '?')}{_rel(c)}"
            )
        elif c["type"] == "account_context":
            lines.append(
                f"  [ACCOUNT] {c['account']} — {c.get('bank_name', '?')}{_rel(c)}"
            )
        else:
            lines.append(
                f"  [PATTERN {c.get('ref', '?')}] {c.get('pattern_type', '?')} — "
                f"severity: {c.get('severity', '?')}{_rel(c)}"
            )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CLI CHAT LOOP — run this file directly to test end-to-end
# ─────────────────────────────────────────────────────────────────────────────

def resolve_account_filter(question: str, accounts: dict) -> str | None:
    """
    Check if the investigator's question mentions a known account number
    or account holder name, and if so, return that account_id so retrieval
    can be scoped to ONLY that account.

    This matters specifically because this is a MULTI-ACCUSED case — without
    this, a question naming one person can retrieve and blend chunks from a
    different accused's account purely on semantic similarity, which is the
    worst possible failure mode for a forensic tool. (Observed directly:
    asking about one account holder by name pulled in chunks from two other
    unrelated accused persons' accounts when no filter was applied.)
    """
    q_lower = question.lower()
    for acct_id, acct_json in accounts.items():
        if acct_id in question:
            return acct_id
        holder = acct_json["account_details"].get("account_holder", "")
        if holder and holder.lower() in q_lower:
            return acct_id
    return None


_SUSPICIOUS_PATTERN_RE = re.compile(
    r"\b(suspicious|structuring|structur|smurf|launder|red[\s-]?flag|"
    r"any\s+patterns?|unusual)\b",
    re.IGNORECASE,
)


def collect_structuring_alerts(
    english_question: str,
    case: dict,
    account_filter: str | None,
    structuring_by_account: dict | None,
) -> list[str]:
    """
    Decide which structuring alerts (if any) to surface for this question.

    Surfaces an alert when the question names an account that has a flagged
    structuring cluster, OR when the question is a general "any suspicious
    patterns" type ask (spec 3.3). Returns ready-to-render alert strings, each
    carrying the mandatory honesty caveat (spec 3.3).
    """
    if not structuring_by_account:
        return []

    if account_filter and account_filter in structuring_by_account:
        relevant = structuring_by_account[account_filter]
    elif _SUSPICIOUS_PATTERN_RE.search(english_question):
        relevant = [c for clusters in structuring_by_account.values() for c in clusters]
    else:
        return []

    return [format_structuring_alert(cluster) for cluster in relevant]


def handle_investigator_question(
    question: str,
    case: dict,
    collection,
    structuring_by_account: dict | None = None,
    history: list[dict] | None = None,
) -> dict:
    """
    Multilingual entry point for every investigator question.

    CONVERSATIONAL CONTEXT (Phase 4): before routing, a follow-up question is
    rewritten into a self-contained one by resolving pronouns / deictic
    references ("this account", "he", "the same") against `history` — the prior
    Q/A turns for this case. The whole routing + retrieval stack is stateless, so
    this single up-front step is what makes every downstream handler answer
    follow-ups about the RIGHT account instead of falling back to an unrelated
    one. `history` is newest-last; pass [] or None for a fresh conversation.

    Routing order (spec Section 4.3 / checklist #8), most-specific first:
        1. exact-ID / reference lookup   (deterministic substring match)
        2. aggregation                   (exact arithmetic via fixed registry)
        3. structured router             (deterministic list/count/lookup)
        4. investigation intelligence    (frequency/rules/reasoning/analytics)
        4.5. balance-trend chart         (per-account balance-over-time line chart)
        4.6. transaction-volume chart    (count + amount trending over time)
        5. graph request                 (interactive money-flow graph)
        6. semantic search               (LLM synthesis over retrieved chunks)

    Kannada is translated to English on input, and only the final natural
    language answer is translated back. Citations are never translated.
    Structuring alerts (spec Section 3) are surfaced alongside, independent of
    which path answered the question.
    """
    detection = detect_and_translate_to_english(question)
    english_question = detection["english_text"]
    investigator_language = detection["language"]

    # Resolve follow-up references ("this account", "he", "the same") into a
    # standalone question BEFORE routing, so exact-ID / account-name matching and
    # every deterministic handler see the entity the investigator actually means.
    # Passthrough (unchanged) for self-contained questions and on any failure.
    routing_question, was_rewritten = resolve_followup(
        english_question, history, generate
    )

    account_filter = resolve_account_filter(routing_question, case["accounts"])

    graph_html = None
    disclaimer = None
    chart = None
    context_used = ""

    id_result = try_id_lookup_answer(routing_question, case)
    aggregation = None if id_result is not None else try_aggregation_answer(routing_question, case)
    structured = (
        None if (id_result is not None or aggregation is not None)
        else try_structured_answer(routing_question, case)
    )
    # Investigation Intelligence layer (Phase 3): analytical/rule/reasoning/
    # frequency questions that are deterministic but NOT simple lookups. Runs
    # only when the earlier deterministic routers all declined, and before the
    # graph + semantic-search fallbacks (spec Phase 3 routing).
    investigation = (
        None if (id_result is not None or aggregation is not None or structured is not None)
        else try_investigation_answer(routing_question, case)
    )
    balance_trend = (
        None if (id_result is not None or aggregation is not None
                 or structured is not None or investigation is not None)
        else build_balance_trend_response(routing_question, case)
    )
    timeseries_trend = (
        None if (id_result is not None or aggregation is not None or structured is not None
                 or investigation is not None or balance_trend is not None)
        else build_timeseries_response(routing_question, case)
    )

    if id_result is not None:
        english_answer = id_result["answer"]
        citations = id_result["citations"]
        matched_pattern = id_result["matched_pattern"]
    elif aggregation is not None:
        english_answer = aggregation["answer"]
        citations = aggregation["citations"]
        matched_pattern = aggregation["matched_pattern"]
        chart = aggregation.get("chart")
    elif structured is not None:
        english_answer = structured["answer"]
        citations = structured["citations"]
        matched_pattern = structured["matched_pattern"]
    elif investigation is not None:
        english_answer = investigation["answer"]
        citations = investigation["citations"]
        matched_pattern = investigation["matched_pattern"]
    elif balance_trend is not None:
        english_answer = balance_trend["answer"]
        citations = balance_trend["citations"]
        matched_pattern = balance_trend["matched_pattern"]
        chart = balance_trend.get("chart")
    elif timeseries_trend is not None:
        english_answer = timeseries_trend["answer"]
        citations = timeseries_trend["citations"]
        matched_pattern = timeseries_trend["matched_pattern"]
        chart = timeseries_trend.get("chart")
    elif matches_graph_request(routing_question):
        graph_result = build_graph_response(routing_question, case, focus_account=account_filter)
        english_answer = graph_result["answer"]
        citations = graph_result["citations"]
        matched_pattern = graph_result["matched_pattern"]
        graph_html = graph_result.get("graph_html")
        disclaimer = graph_result.get("disclaimer")
        chart = graph_result.get("chart")
    else:
        # Semantic fallback: scope retrieval to the resolved account, deepen the
        # candidate set for cross-chunk (multi-hop) synthesis, and hand the LLM
        # the recent conversation so it knows what the follow-up refers to.
        result = ask(
            collection, routing_question, n_results=8,
            account_id=account_filter, history=history,
        )
        english_answer = result["answer"]
        citations = result["citations"]
        matched_pattern = None
        context_used = result.get("context_used", "")

    structuring_alerts = collect_structuring_alerts(
        routing_question, case, account_filter, structuring_by_account
    )

    final_answer = translate_answer(english_answer, investigator_language)

    return {
        "answer": final_answer,
        "citations": citations,
        "matched_pattern": matched_pattern,
        "detected_language": investigator_language,
        "english_question": english_question,
        "resolved_question": routing_question,
        "was_rewritten": was_rewritten,
        "context_used": context_used,
        "graph_html": graph_html,
        "disclaimer": disclaimer,
        "chart": chart,
        "structuring_alerts": structuring_alerts,
    }


def run_cli():
    from chatbot.case_registry import get_case_dir, pick_case_interactively
    from chatbot.data_loader import load_full_case
    from chatbot.chunking_v2 import case_to_chunks
    from chatbot.vector_store import ingest_chunks

    print("=" * 70)
    print("SURVEY CORPS — Investigator RAG Chatbot (CLI test mode)")
    print("=" * 70)
    case_id = pick_case_interactively()
    case_dir = get_case_dir(case_id)
    print(f"Loading case '{case_id}' from {case_dir} ...")

    client = get_client()
    collection = get_collection(client, case_id=case_id)

    from chatbot.structuring import structuring_results_by_account

    case = load_full_case(case_dir)
    all_chunks = case_to_chunks(case)
    ingest_chunks(collection, all_chunks)

    # Structuring detection is a whole-case scan — run it ONCE at case load,
    # not per question (spec 3.3), then reuse the cached result every turn.
    structuring_by_account = structuring_results_by_account(case)

    print(f"\nReady. {collection.count()} chunks indexed for this case.")
    print("Ask in English or Kannada (or 'quit' to exit). Examples:")
    print("  - What suspicious activity involves account 1357102000000198?")
    print("  - Why was a transaction flagged as balance_mismatch?")
    print("  - Were any duplicate transactions found?")
    print("  - What bank is account 12668100018596 with, and what's the statement period?")
    print()

    # In-memory conversation history so the CLI is context-aware too (follow-ups
    # like "give me details about that account" resolve against earlier turns).
    session_history: list[dict] = []

    while True:
        question = input("Investigator> ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        # Five-way routing happens inside handle_investigator_question
        # (exact-ID -> aggregation -> structured -> graph -> semantic), with
        # the cached structuring scan surfaced alongside. `history` lets it
        # resolve follow-up references before routing.
        result = handle_investigator_question(
            question, case, collection,
            structuring_by_account=structuring_by_account,
            history=session_history,
        )
        session_history.append({"question": question, "answer": result["answer"]})

        for alert in result.get("structuring_alerts", []):
            print(f"\n{alert}")

        print(f"\n[language: {result['detected_language']}]")
        print(f"\nAssistant: {result['answer']}\n")
        if result.get("graph_html"):
            print("[an interactive money-flow graph was generated — view it in the Streamlit UI]")
            if result.get("disclaimer"):
                print(f"Note: {result['disclaimer']}")
        if result.get("chart") is not None:
            print("[a Plotly chart was generated for this aggregation — view it in the Streamlit UI]")
        if result["matched_pattern"]:
            print(f"Citations (route: {result['matched_pattern']}):")
        else:
            print("Citations (semantic search):")
        print(format_citations_for_display(result["citations"]))
        print()


if __name__ == "__main__":
    run_cli()
