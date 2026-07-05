"""
narration.py — Optional Groq polish for the report, with the analysis phase's exact
validation discipline (Section 5).

Every specific number, date, or account token in Groq-written text is checked against
the underlying evidence BEFORE it is shown; if the check fails, that bullet (or graph
explanation) falls back to the deterministic template sentence — never the whole report.
So a reader gets a consistent investigator register whether a block was Groq-written or
template fallback, and no figure is ever invented.

The evidence for a rewritten bullet is the deterministic narration the ANALYSIS phase
already produced and validated — the rewrite may sharpen wording but may not introduce
any amount/date/account that was not already in that authoritative text.

Team: Survey Corps | CIDECODE Hackathon 2026 | CID Karnataka
"""
from __future__ import annotations

import json
import re
from typing import Any

from report_llm import ReportKeyPool

_DATE_RE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b")
_ACCOUNT_TOKEN_RE = re.compile(r"\b(?:acct|account)[_-]?[A-Za-z0-9]{2,}\b", re.IGNORECASE)
_LONGNUM_RE = re.compile(r"\b\d{5,}\b")


def _validate(text: str, evidence: str) -> tuple[bool, str]:
    """True only if every account token, date and 5+digit number in `text` appears in
    `evidence` (the authoritative deterministic string). Mirrors analysis narration."""
    if not text.strip():
        return False, "empty"
    ev = evidence
    ev_lower = evidence.lower()
    for tok in _ACCOUNT_TOKEN_RE.findall(text):
        if tok.lower() not in ev_lower:
            return False, f"unsupported_account_token:{tok}"
    for d in _DATE_RE.findall(text):
        if d not in ev:
            return False, f"unsupported_date:{d}"
    ev_nums = set(_LONGNUM_RE.findall(ev.replace(",", "")))
    for n in _LONGNUM_RE.findall(text.replace(",", "")):
        if n not in ev_nums:
            return False, f"unsupported_number:{n}"
    return True, "verified"


def _parse_json(content: str) -> dict:
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return {}


def narrate_account_bullets(pool: ReportKeyPool, account: dict, language: str = "en") -> str:
    """In ONE call, write a short account overview AND rewrite each finding into a
    fuller, specific investigator explanation. The overview is validated against the
    account's combined evidence and each bullet against its own richer evidence; any
    item that fails validation keeps its deterministic template text. Mutates the
    account in place. Returns a status string."""
    bullets = account.get("bullets", [])
    if not bullets or not pool.available:
        return "template" if bullets else "empty"

    # Pass the RICH per-finding evidence (narration + detail facts) so the model can
    # explain more fully while staying inside the validated facts. Evidence strings and the
    # bullet count are trimmed to keep each call well under Groq's tokens-per-minute limit,
    # so a large case's top accounts all get real narration instead of rate-limiting out.
    payload = [{"i": i, "pattern": b["pattern"], "evidence": b.get("evidence", b["text"])[:320]}
               for i, b in enumerate(bullets[:8])]
    language_instruction = ""
    if language == "kn":
        language_instruction = (
            "Write the narrative in professional, formal Kannada suitable for a Karnataka Police "
            "investigation report. Preserve all evidence exactly. Do not translate or alter account "
            "numbers, account ids, dates, transaction ids, IFSC codes, monetary values, bank names, "
            "reference numbers, or evidence strings. Only the surrounding narrative language changes.\n"
        )
    system = (
        "You are a forensic financial investigator writing the findings section of a "
        "court-admissible report. Work ONLY from the structured facts given.\n"
        f"{language_instruction}"
        "1) Write an 'overview': 2-3 sentences explaining, in an investigator's voice, "
        "why this account is suspicious overall — what the money behaviour looks like and "
        "why it matters.\n"
        "2) For each finding item, write a FULL, specific explanation (1-3 sentences, up "
        "to ~55 words): state what happened — the amounts, dates, counterparties, counts, "
        "direction of funds — and briefly why it is suspicious. Be concrete and readable, "
        "not a bare label.\n"
        "CRITICAL: use ONLY facts present in the provided evidence for that item (and, for "
        "the overview, the account_context). Never invent, change, or round any amount, "
        "date, account id, counterparty, or count.\n"
        'Return JSON: {"overview":"<text>","bullets":[{"i":<index>,"text":"<explanation>"}]} '
        "with one entry per finding item."
    )
    user = {"account_context": account.get("overview_evidence", "")[:1600], "findings": payload}
    result = pool.chat_json(
        [{"role": "system", "content": system},
         {"role": "user", "content": json.dumps(user)}],
        context=f"account:{account.get('account_id')}", temperature=0.3,
    )
    if not result.ok:
        return f"template_fallback:{result.error}"

    data = _parse_json(result.content)
    # Overview (validated against the account's combined evidence).
    cand_overview = str(data.get("overview", "")).strip()
    ok_ov, _r = _validate(cand_overview, account.get("overview_evidence", "")) if cand_overview else (False, "missing")
    if ok_ov:
        account["overview"] = cand_overview
        account["overview_ai"] = True

    rewritten = {int(item["i"]): item.get("text", "")
                 for item in data.get("bullets", []) if "i" in item}
    n_ai = 0
    for i, b in enumerate(bullets):
        cand = rewritten.get(i, "").strip()
        ok, _reason = _validate(cand, b.get("evidence", b["text"])) if cand else (False, "missing")
        if ok:
            b["text"] = cand
            b["ai"] = True
            n_ai += 1
        else:
            b["ai"] = False  # keep deterministic text
    return f"groq:overview={'ai' if ok_ov else 'template'},bullets={n_ai}/{len(bullets)}"


def narrate_graph(pool: ReportKeyPool, graph: dict, language: str = "en") -> str:
    """Write a short explanation of a graph FROM ITS STRUCTURED DATA (never the image),
    validated against that data. Falls back to the template explanation on any failure.
    Mutates graph['explanation']. Returns a status string."""
    data = graph.get("data_summary") or {}
    if not data or not pool.available:
        return "template"
    evidence = json.dumps(data)
    language_instruction = ""
    if language == "kn":
        language_instruction = (
            "Write in professional, formal Kannada suitable for a Karnataka Police investigation report. "
            "Do not translate or alter account numbers, account ids, dates, transaction ids, IFSC codes, "
            "monetary values, bank names, reference numbers, or evidence strings. "
        )
    system = (
        "You are a forensic investigator explaining a money-flow graph to a colleague. "
        f"{language_instruction}"
        "Using ONLY the numbers in the provided JSON data (node/edge/event facts — you "
        "cannot see the image), write 2-4 plain-English sentences: describe what the graph "
        "shows, call out the most notable figures (largest transfers, busiest patterns, the "
        "time span), and what an investigator should take from it. Never invent or round "
        "any figure. "
        'Return JSON: {"explanation":"<text>"}.'
    )
    result = pool.chat_json(
        [{"role": "system", "content": system},
         {"role": "user", "content": f"Graph: {graph.get('title')}\nData: {evidence}"}],
        context=f"graph:{graph.get('title')}",
    )
    if not result.ok:
        return f"template_fallback:{result.error}"
    cand = _parse_json(result.content).get("explanation", "").strip()
    ok, _reason = _validate(cand, evidence)
    if ok and cand:
        graph["explanation"] = cand
        graph["ai"] = True
        return "groq"
    return f"template_fallback:{_reason}"


def narrate_case_narrative(pool: ReportKeyPool, case_narrative: dict, language: str = "en") -> str:
    """Polish the officer-first Case Narrative lines with the report LLM pool.

    The deterministic lines (already language-correct) are the evidence AND the fallback:
    the model may only sharpen wording, and each rewritten line is validated against the
    concatenated originals — any line that introduces an unsupported figure/account keeps
    its deterministic text. Never fabricates. Mutates case_narrative['lines'] in place."""
    lines = case_narrative.get("lines", [])
    if not lines or not pool.available:
        return "template"
    evidence = " || ".join(lines)
    lang_instr = ""
    if language == "kn":
        lang_instr = (
            "Write in professional, formal Kannada for a Karnataka Police investigation report. "
            "Do not translate or alter any account number, account id, amount, bank name, date, "
            "reference, or IFSC — only the surrounding narrative language may change. "
        )
    system = (
        "You are a forensic investigator writing the opening case summary for a police officer. "
        f"{lang_instr}"
        "Rewrite each provided line into one clear, plain sentence an officer grasps instantly — "
        "no graph-theory, ML, or statistics vocabulary. Use ONLY the facts in that line; never add, "
        "change, or round any amount, account, or count. "
        'Return JSON: {"lines":[{"i":<index>,"text":"<sentence>"}]} with one entry per input line.'
    )
    user = {"lines": [{"i": i, "text": t} for i, t in enumerate(lines)]}
    result = pool.chat_json(
        [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user)}],
        context="case_narrative", temperature=0.2,
    )
    if not result.ok:
        return f"template_fallback:{result.error}"
    rewritten = {int(item["i"]): item.get("text", "")
                 for item in _parse_json(result.content).get("lines", []) if "i" in item}
    n_ai = 0
    for i in range(len(lines)):
        cand = rewritten.get(i, "").strip()
        ok, _reason = _validate(cand, evidence) if cand else (False, "missing")
        if ok:
            lines[i] = cand
            n_ai += 1
    case_narrative["lines"] = lines
    return f"groq:{n_ai}/{len(lines)}"


def narrate_report(pool: ReportKeyPool, context: dict, language: str = "en") -> dict:
    """Apply Groq polish across the whole report context. Safe no-op if the pool is
    unavailable. Returns a run-log summary (surfaced in the log, not the PDF)."""
    log = {"accounts": [], "graphs": []}
    if context.get("case_narrative"):
        log["case_narrative"] = narrate_case_narrative(pool, context["case_narrative"], language=language)
    for acc in context.get("ranked_accounts", []):
        log["accounts"].append({acc.get("account_id"): narrate_account_bullets(pool, acc, language=language)})
    for g in context.get("graphs", []):
        if g.get("has_data"):
            if g.get("title") == "Account Interconnection Graph":
                log["graphs"].append({g.get("title"): "template:filtered_static_exhibit"})
                continue
            log["graphs"].append({g.get("title"): narrate_graph(pool, g, language=language)})
    log["pool"] = pool.run_log()
    return log
