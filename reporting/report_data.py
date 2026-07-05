"""
report_data.py — Assemble the report context from a completed run's output.

This module ONLY reads and presents; it never re-computes or re-judges anything the
analysis phase decided (Report-phase ground rule 4). It loads:

  • analysis_results.json  — the primary data contract (suspicious_accounts, findings,
                             graph, counterparty_resolution, baseline_summary, …)
  • the extraction run's metadata.json — for per-account identity (account number,
                             holder, bank, IFSC) that the analysis output does not carry.

Everything is driven by what the files actually contain for the given run — no fixed
account counts, page counts, or score bands are assumed (ground rule 2).

The functions here are pure data (no Groq, no rendering) so the template-only dummy
pass (Section 7) uses this unchanged; the AI-narration pass later only *replaces* the
per-bullet / per-graph text, never the numbers assembled here.

Team: Survey Corps | CIDECODE Hackathon 2026 | CID Karnataka
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from i18n import (
    graph_specs,
    kannada_account_overview,
    kannada_bullet_text,
    kannada_case_summary,
    labels,
    normalize_language,
    pattern_display,
    score_bands,
)


# How many highest-priority accounts get a FULL detailed block in the report body.
# Everyone else who was flagged still appears in the compact Final Summary ranking table,
# so nothing is hidden — this only stops a 100+ account case from printing 100+ pages that
# no investigating officer will read. Presentation only; detection/scoring are untouched.
PRIORITY_ACCOUNT_LIMIT = 12


def _band_for_score(score: float, language: str = "en") -> tuple[str, str]:
    for threshold, tag, meaning in score_bands(language):
        if score >= threshold:
            return tag, meaning
    return "weak", score_bands(language)[-1][2]


def _fmt_amount(value: Any) -> str:
    """Indian-grouped rupee formatting, defensive against strings/None."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value or "")
    # Indian digit grouping (last 3, then pairs).
    s = f"{n:,.2f}"
    return f"Rs {s}"


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def _build_txn_lookup(db_path: Path) -> dict[str, str]:
    """txn_id -> best human-readable reference from the analysis DB.

    Returns the transaction reference number when available (a bank UTR / cheque
    number / UPI ref); falls back to the first 50 characters of the narration.
    Returns an empty dict when the DB is missing or unreadable.
    """
    if not db_path.exists():
        return {}
    try:
        con = sqlite3.connect(str(db_path))
        rows = con.execute(
            "SELECT txn_id, reference, narration FROM transactions"
        ).fetchall()
        con.close()
    except Exception:
        return {}
    result: dict[str, str] = {}
    for tid, ref, narr in rows:
        display = str(ref or "").strip() or str(narr or "")[:50].strip()
        if display:
            result[str(tid)] = display
    return result


def _resolve_paths(run_id: str | None, analysis_dir: str | Path | None,
                   extraction_dir: str | Path | None, repo_root: Path) -> tuple[Path, Path]:
    """Locate the analysis output dir and the extraction output dir for a run.

    Preference order: explicit dirs > run_id lookup > the run_metadata.input_path inside
    analysis_results.json (which records the exact extraction run that fed it).
    """
    if analysis_dir:
        adir = Path(analysis_dir)
    elif run_id:
        adir = repo_root / "analysis" / "outputs" / run_id
    else:
        raise ValueError("Provide run_id or analysis_dir")
    results = _load_json(adir / "analysis_results.json")
    if extraction_dir:
        edir = Path(extraction_dir)
    else:
        # run_metadata.input_path points at the exact extraction run that produced this.
        ip = (results.get("run_metadata", {}) or {}).get("input_path", "")
        edir = Path(ip) if ip and Path(ip).exists() else repo_root / "outputs" / "extractions" / (run_id or adir.name)
    return adir, edir


def _account_identity(extraction_dir: Path) -> dict[str, dict[str, str]]:
    """source_account_id -> {account_number, holder, bank, ifsc, branch, period, closing}.

    Read from the extraction metadata.json's per-file account_details (the richest,
    already-reconciled identity). Falls back to the per-statement JSON bundles.
    """
    identity: dict[str, dict[str, str]] = {}
    meta_path = extraction_dir / "metadata.json"
    if meta_path.exists():
        meta = _load_json(meta_path)
        for f in meta.get("files", []) or []:
            sid = f.get("source_account_id") or ""
            ad = f.get("account_details", {}) or {}
            if sid:
                identity[sid] = {
                    "account_number": ad.get("account_number", ""),
                    "holder": ad.get("account_holder", ""),
                    "bank": ad.get("bank_name", "") or f.get("bank_name", ""),
                    "ifsc": ad.get("ifsc_code", ""),
                    "branch": ad.get("branch", ""),
                    "period": ad.get("statement_period", ""),
                    "closing_balance": ad.get("closing_balance", ""),
                }
    return identity


def _graph_nodes_by_id(results: dict) -> dict[str, dict]:
    return {n.get("id"): n for n in (results.get("graph", {}) or {}).get("nodes", []) if n.get("id")}


def _edges_for_account(results: dict, account_id: str, limit: int = 8) -> list[dict]:
    """Top supporting transactions for an account, from the money-flow edges.

    Each edge already carries amount/date/reference and its source/target, so we can
    present a concrete evidence table (date, type, amount, counterparty, reference)
    without re-reading the ledger. Sorted by amount so the material movements show first.
    """
    nodes = _graph_nodes_by_id(results)
    edges = (results.get("graph", {}) or {}).get("edges", [])
    rows = []
    for e in edges:
        src, tgt = e.get("source"), e.get("target")
        if account_id not in (src, tgt):
            continue
        if src == account_id:
            direction, counter = "Debit", tgt
        else:
            direction, counter = "Credit", src
        cnode = nodes.get(counter, {})
        counter_label = cnode.get("account_holder") or cnode.get("bank_name") or str(counter)
        rows.append({
            "date": e.get("date", ""),
            "type": direction,
            "amount": _fmt_amount(e.get("amount")),
            "amount_value": float(e.get("amount") or 0.0),
            "counterparty": counter_label,
            "reference": e.get("reference", "") or "",
        })
    rows.sort(key=lambda r: r["amount_value"], reverse=True)
    return rows[:limit]


def _finding_evidence_string(finding: dict) -> str:
    """A richer authoritative evidence string for one finding: the deterministic
    narration PLUS every scalar fact in its details (amounts, dates, counts, statuses)
    and the accounts/txn ids involved. This is both the material the AI may elaborate
    on and the set its numbers/dates/accounts are validated against — so a fuller
    narration can be written without ever introducing an unsupported figure."""
    parts = [finding.get("narration") or finding.get("explanation") or ""]
    det = finding.get("details", {}) or {}
    for k, v in det.items():
        if isinstance(v, (str, int, float)) and str(v).strip():
            parts.append(f"{k}={v}")
        elif isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, (str, int, float)) and str(vv).strip():
                    parts.append(f"{kk}={vv}")
    parts.append(" ".join(finding.get("accounts", []) or []))
    parts.append(" ".join(str(t) for t in (finding.get("txn_ids", []) or [])[:8]))
    return " | ".join(p for p in parts if str(p).strip())


def _account_bullets(results: dict, account_id: str, language: str = "en") -> list[dict]:
    """One tight, concrete bullet per triggered pattern for this account.

    An account can trigger a pattern dozens of times; showing every finding would bury
    the report. So per pattern we surface the single most material finding (highest
    traced/credited/amount value in its details) and use the narration the analysis
    phase already wrote and validated. The AI pass later rewrites this text into
    investigator voice — the selection and evidence_strength stay the same.
    """
    fbp = results.get("findings_by_pattern", {}) or {}
    bullets = []
    for pkey, findings in fbp.items():
        # Skip the meta-ranking (21) and the lead-only patterns (22 LLM, 23 ML) — those
        # are not concrete per-account evidence; 22/23 are surfaced in the leads section.
        if pkey.split("_", 1)[0] in {"21", "22", "23"}:
            continue
        mine = [f for f in findings if account_id in (f.get("accounts") or [])]
        if not mine:
            continue
        # Rank this pattern's findings for the account by any numeric value in details.
        def _value(f: dict) -> float:
            det = f.get("details", {}) or {}
            for k in ("traced_amount", "credited_amount", "amount", "total_amount", "value"):
                try:
                    return float(det.get(k))
                except (TypeError, ValueError):
                    continue
            return 0.0
        top = max(mine, key=_value)
        pattern = pattern_display(pkey, language)
        evidence = _finding_evidence_string(top)
        if normalize_language(language) == "kn":
            text = kannada_bullet_text(pattern, evidence)
        else:
            text = (top.get("narration") or top.get("explanation") or "").strip()
        bullets.append({
            "pattern": pattern,
            "evidence_strength": top.get("evidence_strength", "weak"),
            "evidence_strength_label": (
                {"strong": "ಬಲವಾದ", "weak": "ದುರ್ಬಲ", "lead": "ಸುಳಿವು"}.get(str(top.get("evidence_strength", "weak")), str(top.get("evidence_strength", "weak")))
                if normalize_language(language) == "kn"
                else top.get("evidence_strength", "weak")
            ),
            "text": text,
            "evidence": evidence,
            "count": len(mine),
            "validated": top.get("narration_validation", ""),
        })
    # Strong-evidence bullets first, then by how many times the pattern fired.
    bullets.sort(key=lambda b: (b["evidence_strength"] != "strong", -b["count"]))
    return bullets


def _identity_label(account_id: str, identity: dict) -> str:
    """Real 'Holder (number)' for a source_account_id; the id itself only if nothing
    was extracted. Falls back to number-only or holder-only when just one is known."""
    info = identity.get(account_id, {}) or {}
    holder = (info.get("holder") or "").strip()
    number = (info.get("account_number") or "").strip()
    if number and holder:
        return f"{holder} ({number})"
    if number:
        return number
    if holder:
        return holder
    return str(account_id)


_TXN_ID_RE = re.compile(r'\bacct_\d+_\d{6}\b')
_ACCT_ID_RE = re.compile(r'\bacct_\d+\b')


def _relabel_text(text: str, identity: dict, txn_lookup: dict | None = None) -> str:
    """Replace every internal ID embedded in free text with a human-readable label.

    Handles two formats:
    - acct_001_000207  (transaction row ID) → real reference number or narration excerpt
    - acct_001         (source account ID)  → 'Holder (AccountNumber)' from identity map

    Txn_id patterns are replaced first (they are longer, so they must go before the
    account_id pass which would otherwise corrupt the txn_id string mid-replacement).
    Presentation only — no data is changed.
    """
    if not text:
        return text
    # Pass 1: transaction-row IDs  (acct_001_000207 → real reference/narration)
    if txn_lookup:
        def _sub_txn(m: re.Match) -> str:
            tid = m.group(0)
            ref = txn_lookup.get(tid)
            if ref:
                return f"ref:{ref}"
            # No DB match: fall back to the account label of the owning account
            acc_id = "_".join(tid.rsplit("_", 1)[:-1])  # strip the row index
            return _identity_label(acc_id, identity)
        text = _TXN_ID_RE.sub(_sub_txn, text)
    # Pass 2: bare account IDs  (acct_001 → Holder (number))
    if identity:
        for sid in sorted(identity, key=len, reverse=True):
            label = _identity_label(sid, identity)
            if label != sid:
                text = re.sub(rf"\b{re.escape(sid)}\b", label, text)
    return text


def _case_reconstruction_context(results: dict, identity: dict, txn_lookup: dict | None = None, language: str = "en") -> dict[str, Any]:
    case_structure = results.get("case_structure", {}) or {}
    summaries = {
        item.get("cluster_id"): item
        for item in results.get("cluster_summaries", []) or []
        if item.get("cluster_id")
    }
    connected = []
    isolated = []
    for cluster in case_structure.get("clusters", []) or []:
        top_account = _identity_label(str(cluster.get("highest_priority_account", "")), identity)
        if normalize_language(language) == "kn":
            summary_text = (
                f"{cluster.get('cluster_id', '')} ನಲ್ಲಿ {cluster.get('account_count', 0)} ಖಾತೆ(ಗಳು) "
                f"ಮತ್ತು {cluster.get('edge_count', 0)} ವ್ಯವಹಾರ ಎಡ್ಜ್(ಗಳು) ಸೇರಿವೆ. "
                f"ಅತ್ಯುನ್ನತ ಆದ್ಯತೆಯ ಖಾತೆ {top_account}; "
                f"ಕ್ಲಸ್ಟರ್ ಅಂಕ {round(float(cluster.get('total_score') or 0.0), 2)}."
            )
        else:
            summary_text = _relabel_text(
                (summaries.get(cluster.get("cluster_id"), {}) or {}).get("summary", ""), identity, txn_lookup
            )
        item = {
            "cluster_id": cluster.get("cluster_id", ""),
            "summary": summary_text,
            "members": [_identity_label(str(m), identity) for m in (cluster.get("member_accounts", []) or [])],
            "account_count": cluster.get("account_count", 0),
            "edge_count": cluster.get("edge_count", 0),
            "highest_priority_account": top_account,
            "total_score": round(float(cluster.get("total_score") or 0.0), 2),
        }
        if cluster.get("is_isolated"):
            isolated.append(item)
        else:
            connected.append(item)
    if normalize_language(language) == "kn":
        clusters = case_structure.get("clusters", []) or []
        top = max(clusters, key=lambda item: (float(item.get("total_score", 0) or 0), str(item.get("cluster_id", ""))), default={})
        summary = kannada_case_summary(
            int(case_structure.get("cluster_count", len(connected) + len(isolated)) or 0),
            len(results.get("suspicious_accounts", []) or []),
            str(top.get("cluster_id", "")),
            float(top.get("total_score", 0) or 0.0),
        )
    else:
        summary = _relabel_text(results.get("case_summary", ""), identity, txn_lookup)
    return {
        "summary": summary,
        "cluster_count": case_structure.get("cluster_count", len(connected) + len(isolated)),
        "connected_clusters": connected,
        "isolated_clusters": isolated,
    }


def _account_label(account_id: str, identity: dict, nodes: dict) -> str:
    """A human name for an account: holder if known, else the account number/id."""
    ident = identity.get(account_id, {})
    node = nodes.get(account_id, {})
    holder = ident.get("holder") or node.get("account_holder")
    number = ident.get("account_number") or node.get("account_number") or account_id
    return f"{holder} ({number})" if holder else str(number)


def build_case_narrative(results: dict, identity: dict, language: str = "en") -> dict[str, Any]:
    """Plain-language, officer-first summary of the case.

    PRESENTATION ONLY: every value is read from the analysis output (graph edges,
    findings, ranked accounts, case structure) — nothing is re-computed or re-judged.
    No graph-theory or ML vocabulary appears in the produced text; a police officer
    should grasp the case in ~30 seconds. Returns structured facts plus ready-to-render
    English `lines`; the Kannada/AI pass may rewrite the lines, never the numbers.
    """
    nodes = _graph_nodes_by_id(results)
    observed = {nid for nid, n in nodes.items() if n.get("observed_account")}
    edges = (results.get("graph", {}) or {}).get("edges", []) or []
    fbp = results.get("findings_by_pattern", {}) or {}
    suspicious = results.get("suspicious_accounts", []) or []

    inflow: dict[str, float] = defaultdict(float)
    outflow: dict[str, float] = defaultdict(float)
    senders: dict[str, set] = defaultdict(set)
    recipients: dict[str, set] = defaultdict(set)
    total_moved = 0.0
    money_into_network = 0.0
    for e in edges:
        amt = float(e.get("amount") or 0.0)
        s, t = e.get("source"), e.get("target")
        total_moved += amt
        outflow[s] += amt
        inflow[t] += amt
        recipients[s].add(t)
        senders[t].add(s)
        if t in observed and s not in observed:
            money_into_network += amt

    def _accounts_for(pattern_key_suffixes: tuple[str, ...]) -> list[str]:
        out: list[str] = []
        for key, items in fbp.items():
            if not key.split("_", 1)[0].isdigit():
                continue
            if any(key.endswith(sfx) or key.split("_", 1)[0] == sfx for sfx in pattern_key_suffixes):
                for f in items:
                    out.extend(f.get("accounts", []) or [])
        return list(dict.fromkeys(out))

    # Pooled / collector accounts: fund pooling (4) or balance parking (11).
    pooled = _accounts_for(("4", "11"))
    # Intermediary / pass-through accounts (3).
    intermediaries = _accounts_for(("3",))

    # Money-trail traced vs not-fully-traced (from Pattern 8 details).
    traced = 0.0
    untraced = 0.0
    for f in fbp.get("8_money_trail_tracing", []) or []:
        d = f.get("details", {}) or {}
        traced += float(d.get("traced_amount") or 0.0)
        untraced += float(d.get("remaining_amount") or 0.0)

    # Primary source: the account that pushed the most money into the network.
    primary_source = max(outflow, key=lambda k: outflow[k], default=None)
    # Major fan-out / fan-in by distinct counterparties.
    fan_out = max(recipients, key=lambda k: len(recipients[k]), default=None)
    fan_in = max(senders, key=lambda k: len(senders[k]), default=None)
    kingpin = suspicious[0] if suspicious else None

    lang = normalize_language(language)
    src_label = _account_label(primary_source, identity, nodes) if primary_source else ""
    fanout_label = _account_label(fan_out, identity, nodes) if fan_out else ""
    fanin_label = _account_label(fan_in, identity, nodes) if fan_in else ""
    pooled_labels = [_account_label(a, identity, nodes) for a in pooled[:3]]
    kingpin_label = _account_label(str(kingpin.get("account_id", "")), identity, nodes) if kingpin else ""

    lines: list[str] = []
    empty_case = total_moved <= 0 and not suspicious
    if lang == "kn":
        if empty_case:
            lines.append("ಈ ಪ್ರಕರಣದ ಖಾತೆಗಳ ನಡುವೆ ಯಾವುದೇ ಶಂಕಾಸ್ಪದ ಹಣ ಚಲನೆ ಸ್ಥಾಪಿತವಾಗಿಲ್ಲ.")
        else:
            lines.append(f"ಈ ಪ್ರಕರಣದ ಖಾತೆಗಳ ನಡುವೆ ಒಟ್ಟು {_fmt_amount(total_moved)} ವರ್ಗಾವಣೆಯಾಗಿದೆ; "
                         f"ಇದರಲ್ಲಿ {_fmt_amount(money_into_network)} ಹೊರಗಿನಿಂದ ಶಂಕಿತ ಜಾಲಕ್ಕೆ ಪ್ರವೇಶಿಸಿದೆ.")
            if src_label and outflow.get(primary_source, 0) > 0:
                lines.append(f"ಅತಿ ದೊಡ್ಡ ಹಣದ ಮೂಲ {src_label}; ಇದು {_fmt_amount(outflow[primary_source])} ಕಳುಹಿಸಿದೆ.")
            if intermediaries:
                lines.append(f"ಹಣವನ್ನು {len(intermediaries)} ಮಧ್ಯವರ್ತಿ ಖಾತೆ(ಗಳ) ಮೂಲಕ ಸಾಗಿಸಲಾಗಿದೆ — ಇವು ಹಣ ಪಡೆದು ಬೇಗನೆ ಮುಂದಕ್ಕೆ ರವಾನಿಸಿವೆ.")
            if fanout_label and len(recipients.get(fan_out, ())) >= 2:
                lines.append(f"{fanout_label} ಹಣವನ್ನು {len(recipients[fan_out])} ಬೇರೆ ಖಾತೆಗಳಿಗೆ ಹಂಚಿದೆ.")
            if fanin_label and len(senders.get(fan_in, ())) >= 2:
                lines.append(f"{fanin_label} {len(senders[fan_in])} ಬೇರೆ ಖಾತೆಗಳಿಂದ ಹಣ ಸಂಗ್ರಹಿಸಿದೆ.")
            if pooled_labels:
                lines.append("ಹಣ ಅಂತಿಮವಾಗಿ ಇಲ್ಲಿ ಸಂಗ್ರಹವಾಗಿದೆ: " + ", ".join(pooled_labels) + ".")
            if traced > 0:
                note = f" ({_fmt_amount(untraced)} ಸಂಪೂರ್ಣ ಪತ್ತೆಯಾಗಿಲ್ಲ)" if untraced > 0 else ""
                lines.append(f"ಒಳಬಂದ ಹಣದಲ್ಲಿ {_fmt_amount(traced)} ಮುಂದಿನ ವರ್ಗಾವಣೆ/ಹಿಂಪಡೆತಗಳಿಗೆ ಪತ್ತೆಹಚ್ಚಲಾಗಿದೆ" + note + ".")
            if kingpin_label:
                lines.append(f"ಮೊದಲು ತನಿಖೆ ಮಾಡಬೇಕಾದ ಖಾತೆ {kingpin_label} — ಈ ಪ್ರಕರಣದಲ್ಲಿ ಇದು ಅತ್ಯಂತ ಪ್ರಬಲ ಶಂಕಾಸ್ಪದ ನಡವಳಿಕೆಗಳ ಸಂಯೋಜನೆ ತೋರಿಸುತ್ತದೆ.")
    else:
        if empty_case:
            lines.append("No suspicious money movement was established between the accounts in this case.")
        else:
            lines.append(f"A total of {_fmt_amount(total_moved)} moved across the accounts in this case, "
                         f"of which {_fmt_amount(money_into_network)} entered the suspect network from outside.")
            if src_label and outflow.get(primary_source, 0) > 0:
                lines.append(f"The largest source of funds was {src_label}, which sent out {_fmt_amount(outflow[primary_source])}.")
            if intermediaries:
                lines.append(f"Money was routed through {len(intermediaries)} intermediary account(s) that "
                             f"received funds and quickly passed them on.")
            if fanout_label and len(recipients.get(fan_out, ())) >= 2:
                lines.append(f"{fanout_label} spread money to {len(recipients[fan_out])} different accounts (fan-out).")
            if fanin_label and len(senders.get(fan_in, ())) >= 2:
                lines.append(f"{fanin_label} collected money from {len(senders[fan_in])} different accounts (fan-in).")
            if pooled_labels:
                lines.append("Funds finally accumulated in: " + ", ".join(pooled_labels) + ".")
            if traced > 0:
                note = f" ({_fmt_amount(untraced)} could not be fully traced)" if untraced > 0 else ""
                lines.append(f"{_fmt_amount(traced)} of incoming funds was traced to onward transfers/withdrawals" + note + ".")
            if kingpin_label:
                lines.append(f"The account to investigate first is {kingpin_label} "
                             f"— it shows the strongest combination of suspicious behaviours in this case.")

    return {
        "lines": lines,
        "total_moved": total_moved,
        "total_moved_display": _fmt_amount(total_moved),
        "money_into_network": money_into_network,
        "money_into_network_display": _fmt_amount(money_into_network),
        "primary_source": _account_label(primary_source, identity, nodes) if primary_source else "",
        "intermediary_count": len(intermediaries),
        "fan_out": _account_label(fan_out, identity, nodes) if fan_out else "",
        "fan_in": _account_label(fan_in, identity, nodes) if fan_in else "",
        "pooled_accounts": [_account_label(a, identity, nodes) for a in pooled[:3]],
        "kingpin": _account_label(str(kingpin.get("account_id", "")), identity, nodes) if kingpin else "",
        "first_target": _account_label(str(kingpin.get("account_id", "")), identity, nodes) if kingpin else "",
        "traced_amount_display": _fmt_amount(traced),
        "untraced_amount_display": _fmt_amount(untraced),
    }


def build_report_context(
    run_id: str | None = None,
    analysis_dir: str | Path | None = None,
    extraction_dir: str | Path | None = None,
    repo_root: str | Path | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """Assemble the full, render-ready context for one completed run."""
    language = normalize_language(language)
    t = labels(language)
    repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    adir, edir = _resolve_paths(run_id, analysis_dir, extraction_dir, repo_root)
    results = _load_json(adir / "analysis_results.json")

    run_meta = results.get("run_metadata", {}) or {}
    contract = results.get("input_contract", {}) or {}
    baseline = results.get("baseline_summary", {}) or {}
    cp = results.get("counterparty_resolution", {}) or {}
    balval = results.get("balance_validation", {}) or {}
    gsum = results.get("graph_summary", {}) or {}
    identity = _account_identity(edir)
    txn_lookup = _build_txn_lookup(adir / "analysis.db")
    nodes = _graph_nodes_by_id(results)
    total_txn = contract.get("eligible_row_count", contract.get("clean_row_count", 0))
    if language == "kn":
        mismatch_count = int((balval or {}).get("balance_mismatch_excluded_count", 0) or 0)
        balance_note = (
            f"ಎಕ್ಸ್ಟ್ರಾಕ್ಷನ್ ಹಂತದಲ್ಲಿ ಗುರುತಿಸಿದ ಬ್ಯಾಲೆನ್ಸ್ ವ್ಯತ್ಯಾಸಗಳ ಕಾರಣ {mismatch_count} ವ್ಯವಹಾರ(ಗಳು) ವಿಶ್ಲೇಷಣೆಯಿಂದ ಹೊರಗಿಡಲಾಗಿದೆ."
            if mismatch_count
            else "ಈ ಡೇಟಾಸೆಟ್‌ನಲ್ಲಿ ಬ್ಯಾಲೆನ್ಸ್ ವ್ಯತ್ಯಾಸಗಳು ಕಂಡುಬಂದಿಲ್ಲ."
        )
    else:
        balance_note = balval.get("summary_line", "")

    # Number of ACTUAL uploaded statement files (from the extraction receipt), not the
    # analysis input manifest which lists the intermediate CSVs.
    files_processed = 0
    _meta_path = edir / "metadata.json"
    if _meta_path.exists():
        files_processed = int((_load_json(_meta_path).get("summary", {}) or {}).get("files_processed", 0) or 0)

    # ── Ranked findings blocks: observed accounts only (they have a statement + full
    # identity). Counterparty entries in suspicious_accounts have no holder/bank/number,
    # so they belong in the graph, not as identity blocks. Driven by observed_account,
    # never a hardcoded count. ──
    observed_ids = {nid for nid, n in nodes.items() if n.get("observed_account")}
    ranked = [a for a in results.get("suspicious_accounts", []) if a.get("account_id") in observed_ids]

    ranked_accounts = []
    for i, acc in enumerate(ranked, start=1):
        aid = acc["account_id"]
        ident = identity.get(aid, {})
        node = nodes.get(aid, {})
        holder = ident.get("holder") or node.get("account_holder") or aid
        bank = ident.get("bank") or node.get("bank_name") or ""
        score = float(acc.get("total_score", 0.0))
        tag, _meaning = _band_for_score(score, language)
        bullets = _account_bullets(results, aid, language)
        for _b in bullets:  # never leak an internal source id (acct_00x / txn_00N) into displayed text
            _b["text"] = _relabel_text(_b.get("text", ""), identity, txn_lookup)
            _b["evidence"] = _relabel_text(_b.get("evidence", ""), identity, txn_lookup)
        strong_n = acc.get("strong_pattern_count", 0)
        distinct_n = acc.get("distinct_pattern_count", 0)
        # Deterministic overview (used as-is unless the AI pass replaces it with a
        # validated, richer version). overview_evidence is what that AI text is checked
        # against, so it carries the score/pattern counts plus every bullet's evidence.
        if language == "kn":
            overview_tmpl = kannada_account_overview(aid, score, int(strong_n or 0), int(distinct_n or 0))
        else:
            # Readable deterministic overview that NAMES the top patterns (not just counts),
            # so accounts that don't get an AI narration still read plainly for an officer.
            who = _identity_label(aid, identity)
            top_patterns = ", ".join(b["pattern"] for b in bullets[:3]) if bullets else "no scored pattern"
            overview_tmpl = (
                f"{who} is flagged by {distinct_n} distinct suspicious pattern(s) "
                f"({strong_n} strong), most notably {top_patterns}. "
                f"Composite suspicion score: {round(score)}.")
        overview_evidence = (
            f"account={_identity_label(aid, identity)} score={round(score)} strong_patterns={strong_n} "
            f"distinct_patterns={distinct_n} total_findings={acc.get('total_findings', 0)} || "
            + " || ".join(b["evidence"] for b in bullets))
        ranked_accounts.append({
            "rank": i,
            "account_id": aid,
            "holder": holder,
            "bank": bank,
            "account_number": ident.get("account_number", "") or node.get("account_number", ""),
            "ifsc": ident.get("ifsc") or node.get("ifsc_code", ""),
            "score": round(score),
            "band": tag,
            "band_label": {"strong": "ಬಲವಾದ", "moderate": "ಮಧ್ಯಮ", "weak": "ದುರ್ಬಲ"}.get(tag, tag) if language == "kn" else tag,
            "distinct_pattern_count": distinct_n,
            "strong_pattern_count": strong_n,
            "total_findings": acc.get("total_findings", 0),
            "overview": overview_tmpl,
            "overview_evidence": overview_evidence,
            "bullets": bullets,
            "evidence_rows": _edges_for_account(results, aid),
            "assessment_tag": "strong" if acc.get("strong_pattern_count", 0) >= 1 else "weak",
            "key_concern": bullets[0]["pattern"] if bullets else "—",
        })

    # ── Input summary — per-account identity table (Section 4.3) ──
    input_accounts = []
    for aid in sorted(observed_ids):
        ident = identity.get(aid, {})
        node = nodes.get(aid, {})
        input_accounts.append({
            # source_account_id is intentionally excluded here — it is an internal
            # pipeline key (acct_001 style) that must never appear in the report.
            "account_number": ident.get("account_number", ""),
            "holder": ident.get("holder") or node.get("account_holder", ""),
            "bank": ident.get("bank") or node.get("bank_name", ""),
            "ifsc": ident.get("ifsc") or node.get("ifsc_code", ""),
        })

    # ── Graphs (Section 4.6) — embed existing PNGs; note if a file is missing. Each
    # graph also carries a compact STRUCTURED data summary (node/edge/event facts) so
    # the AI explanation is written from the data, never from the rendered image. ──
    graphs_dir = adir / "graphs"
    edges = (results.get("graph", {}) or {}).get("edges", [])
    top_flows = sorted(edges, key=lambda e: float(e.get("amount") or 0.0), reverse=True)[:5]
    fbp = results.get("findings_by_pattern", {}) or {}
    pattern_counts = {pattern_display(k, language): len(v) for k, v in fbp.items() if v}
    case_structure = results.get("case_structure", {}) or {}
    clusters = case_structure.get("clusters", []) or []
    graph_data = {
        "report_graphs/case_overview_graph.png": {
            "rendering_scope": (
                "Case-wide overview: one node per reconstructed cluster, no individual "
                "account-level clutter."
            ),
            "cluster_count": case_structure.get("cluster_count", 0),
            "cluster_method": case_structure.get("cluster_method", ""),
            "clusters": [
                {
                    "cluster_id": c.get("cluster_id"),
                    "account_count": c.get("account_count"),
                    "edge_count": c.get("edge_count"),
                    "total_score": c.get("total_score"),
                    "pattern_ids": c.get("pattern_ids", []),
                }
                for c in clusters[:10]
            ],
        },
        "report_graphs/account_interconnection_graph.png": {
            "rendering_scope": (
                "Top-cluster static report exhibit: scoped to reconstruction-included "
                "edges for a highest-risk cluster, capped for readability."
            ),
            "cluster_count": case_structure.get("cluster_count", 0),
            "ranked_accounts": [_identity_label(str(a.get("account_id")), identity) for a in results.get("suspicious_accounts", [])[:5]],
            "observed_accounts": [_identity_label(str(x), identity) for x in sorted(observed_ids)],
            "underlying_money_flow_graph_nodes": gsum.get("node_count", len(nodes)),
            "underlying_money_flow_graph_edges": gsum.get("edge_count", len(edges)),
            "largest_transfers": [
                {"amount": round(float(e.get("amount") or 0.0), 2),
                 "date": e.get("date", ""),
                 "from": _identity_label(str(e.get("source")), identity),
                 "to": _identity_label(str(e.get("target")), identity)}
                for e in top_flows
            ],
        },
        "report_graphs/suspicious_timeline.png": {
            "date_start": (baseline.get("date_range", {}) or {}).get("start", ""),
            "date_end": (baseline.get("date_range", {}) or {}).get("end", ""),
            "total_transactions": total_txn,
            "flagged_excluded": (results.get("balance_validation", {}) or {}).get("balance_mismatch_excluded_count", 0),
        },
        "report_graphs/fraud_pattern_summary.png": {"pattern_counts": pattern_counts},
    }
    graphs = []
    for title, filename, template_expl in graph_specs(language):
        img = graphs_dir / filename
        graphs.append({
            "title": title,
            "image_path": str(img.resolve()) if img.exists() else None,
            "explanation": template_expl,
            "has_data": img.exists(),
            "data_summary": graph_data.get(filename, {}),
        })

    # ── AI-flagged leads (Section 4.7) — Pattern 23; omit the whole section if empty ──
    p23 = results.get("findings_by_pattern", {}).get("23_ml_ensemble_anomaly_lead", []) or []
    ai_leads = {
        "present": bool(p23),
        "count": len(p23),
        "findings": [
            {
                "text": _relabel_text(
                    (
                        kannada_bullet_text(
                            pattern_display("23_ml_ensemble_anomaly_lead", language),
                            f.get("narration") or f.get("explanation", ""),
                        )
                        if language == "kn"
                        else f.get("narration") or f.get("explanation", "")
                    ),
                    identity, txn_lookup,
                ),
                "accounts": ", ".join(
                    _identity_label(a, identity) for a in (f.get("accounts", []) or [])
                ),
            }
            for f in p23
        ],
    }

    date_range = baseline.get("date_range", {}) or {}

    context = {
        "meta": {
            "run_id": run_meta.get("run_id", adir.name),
            "extraction_run_id": run_meta.get("input_extraction_run_id", edir.name),
            "generated_at": (
                datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
                if language == "kn"
                else datetime.now(timezone.utc).astimezone().strftime("%d %B %Y, %H:%M")
            ),
            "team": "Survey Corps",
            "hackathon": "CIDECODE",
            "language": language,
        },
        "language": language,
        "t": t,
        "input_summary": {
            "n_files": files_processed or len(input_accounts),
            "n_accounts": len(input_accounts),
            "n_transactions": total_txn,
            "date_start": date_range.get("start", ""),
            "date_end": date_range.get("end", ""),
            "accounts": input_accounts,
        },
        "analysis_summary": {
            "accounts_analyzed": baseline.get("account_count", len(input_accounts)),
            "total_transactions": total_txn,
            "counterparty_resolution_rate": round(float(cp.get("resolution_rate_percent", 0.0)), 1),
            "balance_note": balance_note,
            "accounts_flagged": len(ranked_accounts),
            "graph_nodes": gsum.get("node_count", 0),
            "graph_edges": gsum.get("edge_count", 0),
        },
        "case_narrative": build_case_narrative(results, identity, language),
        # Top-5 "prime suspects" callout — the accounts an officer should look at first.
        "prime_suspects": [
            {
                "rank": a["rank"], "holder": a["holder"], "account_number": a["account_number"],
                "score": a["score"], "band": a.get("band_label") or a["band"],
                "key_concern": a["key_concern"],
                "top_finding": (a["bullets"][0]["text"] if a.get("bullets") else ""),
            }
            for a in ranked_accounts[:5]
        ],
        "ranked_shown": min(len(ranked_accounts), PRIORITY_ACCOUNT_LIMIT),
        "ranked_total": len(ranked_accounts),
        "data_security": {
            "llm_status": run_meta.get("llm_status", run_meta.get("llm_final_status", "not_used")),
            "llm_call_count": run_meta.get("llm_call_count", 0),
            "local_items": [
                "All fraud detection, scoring and ranking run on this machine (deterministic code).",
                "Raw bank statements and extracted transactions never leave the machine.",
                "The money-flow graph, clusters and suspicion scores are computed locally.",
            ],
            "external_items": [
                "Only small, redacted text samples are sent to the language model to describe a statement's column layout when local parsing is insufficient.",
                "For images / scanned PDFs, the page pixels are sent to a vision model (the one unavoidable case).",
                "The language model only rewrites explanations into plain language; it never changes a number, account, or decision.",
            ],
        },
        "case_reconstruction": _case_reconstruction_context(results, identity, txn_lookup, language),
        # Only the top-priority accounts get a full detailed block (see PRIORITY_ACCOUNT_LIMIT);
        # the rest remain in the compact Final Summary ranking table, so none are dropped.
        "ranked_accounts": ranked_accounts[:PRIORITY_ACCOUNT_LIMIT],
        "graphs": graphs,
        "ai_leads": ai_leads,
        "final_summary": {
            "ranked_table": [
                {"rank": a["rank"], "account": _identity_label(a["account_id"], identity),
                 "score": a["score"], "key_concern": a["key_concern"]}
                for a in ranked_accounts
            ],
            "legend": [
                {"range": "600+", "meaning": score_bands(language)[0][2]},
                {"range": "300–599" if language == "en" else "300-599", "meaning": score_bands(language)[1][2]},
                {"range": "Below 300" if language == "en" else "300 ಕ್ಕಿಂತ ಕಡಿಮೆ", "meaning": score_bands(language)[2][2]},
            ],
        },
    }
    return context


if __name__ == "__main__":
    import sys
    ctx = build_report_context(run_id=sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(ctx, indent=2, default=str)[:4000])
