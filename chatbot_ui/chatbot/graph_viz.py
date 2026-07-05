"""
graph_viz.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Interactive Transaction Network Graph in chat (spec Section 1)

When an investigator asks a money-flow question, render an interactive
node-and-edge graph inline in the chat response (zoom/drag/click) alongside a
short text summary — not instead of it, since some investigators/judges want
the citation-backed text explanation too (spec 1.5).

DATA LIMITATION + HONESTY (spec 0.2, 1.3, 1.6): there is NO counterparty/
account column in the schema. Counterparty nodes are derived heuristically
from narration text via the SAME extract_counterparty_hint() used by the
Reports tab graph — reused, not re-implemented. Real accounts and heuristic
counterparties are visually distinguished (shape + size + colour) and the
same approximate-data disclaimer is shown. The in-chat version must NOT be a
weaker/abbreviated version of that honesty discipline just because it is
embedded in chat.
"""

from __future__ import annotations

import re

import networkx as nx
import pandas as pd

from chatbot.counterparty import extract_counterparty_hint, infer_direction_amount
from chatbot.investigation_rules import CASH_NARRATION_RE

# Shown whenever a heuristic counterparty node appears (spec 1.6) — same
# meaning as the Reports & Graph tab caption.
HEURISTIC_DISCLAIMER = (
    "Counterparty nodes are derived from transaction narration text and are "
    "approximate — likely external parties inferred from free-text descriptions, "
    "not verified account matches."
)

_GRAPH_REQUEST_RE = re.compile(
    r"\b(show|visualiz|map|graph|flow|trace|track)\b.*\b(money|transfer|flow|fund|transaction)\b",
    re.IGNORECASE,
)
_GRAPH_KEYWORD_RE = re.compile(r"\b(graph|network|visuali[sz]e)\b", re.IGNORECASE)


def matches_graph_request(question: str) -> bool:
    """True when the question asks to SEE relationships/flow, not just a fact."""
    return bool(_GRAPH_REQUEST_RE.search(question) or _GRAPH_KEYWORD_RE.search(question))


def get_flagged_account_ids(case: dict) -> set[str]:
    """Account IDs that have at least one flagged transaction."""
    flagged = case.get("flagged")
    if flagged is None or flagged.empty or "Account_ID" not in flagged.columns:
        return set()
    return {str(a) for a in flagged["Account_ID"].dropna().unique()}


def transactions_for_graph(case: dict, focus_account: str | None = None) -> list[dict]:
    """
    Build the list of transaction records build_transaction_graph() expects,
    directly from the in-memory clean transactions (optionally scoped to one
    account named in the question). Keys: account_id, narration, direction,
    amount, date.
    """
    df = case["clean"]
    if focus_account and "account_number" in df.columns:
        df = df[df["account_number"].astype(str) == str(focus_account)]

    records = []
    for _, row in df.iterrows():
        account_id = str(row.get("account_number") or row.get("Account_ID") or "")
        if not account_id:
            continue
        direction, amount = infer_direction_amount(row)
        date = row.get("Date")
        date_str = date.strftime("%d/%m/%Y") if isinstance(date, pd.Timestamp) and pd.notna(date) else str(date)
        records.append({
            "account_id": account_id,
            "narration": row.get("Narration", ""),
            "direction": direction,
            "amount": float(amount or 0),
            "date": date_str,
        })
    return records


# ─────────────────────────────────────────────────────────────────────────────
# SANKEY (whole-case view) — aggregates by transaction-type CATEGORY rather
# than by literal counterparty string, which is what keeps the node-link
# graph from exploding to ~1700+ nodes at full-case scale. No physics
# simulation, so it stays fast regardless of transaction volume.
# ─────────────────────────────────────────────────────────────────────────────

_TXN_TYPE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("UPI", re.compile(r"\bUPI\b", re.IGNORECASE)),
    ("NEFT", re.compile(r"\bNEFT\b", re.IGNORECASE)),
    ("RTGS", re.compile(r"\bRTGS\b", re.IGNORECASE)),
    ("IMPS", re.compile(r"\bIMPS\b", re.IGNORECASE)),
    ("Cheque", re.compile(r"\b(cheque|chq|cheq)\b", re.IGNORECASE)),
    ("Cash", CASH_NARRATION_RE),
]


def classify_transaction_type(narration: str) -> str:
    """Bucket a narration into a coarse transaction-type category for the Sankey."""
    text = str(narration or "")
    for label, pattern in _TXN_TYPE_PATTERNS:
        if pattern.search(text):
            return label
    return "Other"


def _truncate_label(label: str, max_len: int = 26) -> str:
    """Short label for the diagram itself; the full name still shows on hover
    (via customdata) so nothing is actually lost, just kept off the canvas."""
    return label if len(label) <= max_len else label[: max_len - 1].rstrip() + "…"


def build_sankey_figure(transactions: list[dict], case: dict):
    """
    3-layer Sankey: source account/'External' -> transaction-type bucket ->
    destination account/'External'. 'External' stands in for the unknown
    other party on a debit/credit — the schema has no verified sender/
    receiver account link. Link width = summed amount. Returns None if no
    transaction has a usable amount.
    """
    import plotly.graph_objects as go

    node_labels: list[str] = []
    node_full_labels: list[str] = []
    node_index: dict[str, int] = {}

    def _idx(label: str) -> int:
        if label not in node_index:
            node_index[label] = len(node_labels)
            node_labels.append(_truncate_label(label))
            node_full_labels.append(label)
        return node_index[label]

    link_totals: dict[tuple[int, int], float] = {}
    for txn in transactions:
        amount = float(txn.get("amount") or 0)
        if amount <= 0:
            continue
        holder = (case.get("accounts", {}).get(txn["account_id"], {})
                      .get("account_details", {}).get("account_holder"))
        account_label = f"{holder} ({txn['account_id']})" if holder else f"Acct {txn['account_id']}"
        bucket = classify_transaction_type(txn["narration"])
        src, dst = (account_label, "External") if txn["direction"] == "debit" else ("External", account_label)

        s_idx, b_idx, d_idx = _idx(src), _idx(bucket), _idx(dst)
        link_totals[(s_idx, b_idx)] = link_totals.get((s_idx, b_idx), 0.0) + amount
        link_totals[(b_idx, d_idx)] = link_totals.get((b_idx, d_idx), 0.0) + amount

    if not link_totals:
        return None

    sources, targets = zip(*link_totals.keys())
    link_hover = [
        f"{node_full_labels[s]} → {node_full_labels[t]}<br>₹{v:,.2f}"
        for (s, t), v in link_totals.items()
    ]
    fig = go.Figure(go.Sankey(
        node=dict(
            label=node_labels, pad=15, thickness=18,
            customdata=node_full_labels,
            hovertemplate="%{customdata}<br>₹%{value:,.2f}<extra></extra>",
        ),
        link=dict(
            source=list(sources), target=list(targets), value=list(link_totals.values()),
            customdata=link_hover, hovertemplate="%{customdata}<extra></extra>",
        ),
    ))
    # Full width, generous height and margins so long node labels don't clip
    # against the card edge — the "graph isn't fitting properly" fix.
    fig.update_layout(
        title_text="Money flow by transaction type",
        font_size=12,
        height=640,
        margin=dict(l=10, r=10, t=50, b=10),
        autosize=True,
    )
    return fig


def _summarize_sankey(transactions: list[dict]) -> str:
    accounts = {t["account_id"] for t in transactions}
    total = sum(float(t.get("amount") or 0) for t in transactions)
    bucket_totals: dict[str, float] = {}
    for t in transactions:
        bucket = classify_transaction_type(t["narration"])
        bucket_totals[bucket] = bucket_totals.get(bucket, 0.0) + float(t.get("amount") or 0)
    top = sorted(bucket_totals.items(), key=lambda kv: -kv[1])[:3]
    top_str = ", ".join(f"{b}: ₹{v:,.2f}" for b, v in top)
    return (
        f"Money-flow Sankey across {len(accounts)} account(s) and "
        f"{len(transactions)} transaction(s) totalling ₹{total:,.2f}. "
        f"Top categories by amount: {top_str}."
    )


def build_transaction_graph(transactions: list[dict], focus_account: str | None = None) -> nx.DiGraph:
    """
    Build a directed graph from already-retrieved/filtered transaction records
    (this function does not query ChromaDB itself).

    Nodes: real accounts (from case data) + heuristic counterparty labels.
    Edges: one per transaction, directed by direction, weighted by amount.
    """
    G = nx.DiGraph()
    for txn in transactions:
        account_id = txn["account_id"]
        counterparty = extract_counterparty_hint(txn["narration"])
        if counterparty is None:
            continue  # skip transactions with no extractable counterparty signal

        G.add_node(account_id, node_type="real_account")
        G.add_node(counterparty, node_type="heuristic_counterparty")

        if txn["direction"] == "credit":
            G.add_edge(counterparty, account_id, amount=txn["amount"], date=txn.get("date", "?"))
        else:
            G.add_edge(account_id, counterparty, amount=txn["amount"], date=txn.get("date", "?"))
    return G


# Past this many nodes the radial layout gets too dense for always-on labels
# to stay legible, so labels collapse to hover/click-only (the name still lives
# in each node's tooltip). Below it, labels stay visible (round 5, item 2).
_LABEL_HIDE_THRESHOLD = 18


def render_graph_html(G: nx.DiGraph, flagged_accounts: set[str] | None = None) -> str:
    """
    Render the graph as interactive HTML via pyvis. flagged_accounts get a
    distinct red-tinted styling; real accounts are indigo dots, heuristic
    counterparties are dimmer squares (shape distinction, not just colour, so
    the real-vs-heuristic split survives grayscale/print).

    Once there are many nodes the physics simulation is frozen the moment it
    stabilises (no more perpetual drifting) and node labels collapse to
    hover/click-only so they stop colliding (round 5, item 2). Pan / zoom /
    drag stay available.
    """
    import json

    from pyvis.network import Network

    # cdn_resources defaults to "local", which emits <script src="lib/...">
    # relative to wherever the HTML file sits on disk. That breaks the moment
    # this HTML is embedded anywhere else (an iframe srcDoc has no such
    # location to resolve against) — "in_line" bakes every JS/CSS asset
    # directly into the returned HTML string instead.
    net = Network(height="500px", width="100%", directed=True, notebook=False, cdn_resources="in_line")
    flagged_accounts = flagged_accounts or set()

    node_count = G.number_of_nodes()
    hide_labels = node_count > _LABEL_HIDE_THRESHOLD

    for node, attrs in G.nodes(data=True):
        is_real = attrs.get("node_type") == "real_account"
        is_flagged = str(node) in flagged_accounts
        name = str(node)
        net.add_node(
            name,
            # Past the threshold the on-canvas label is dropped but the name
            # still shows on hover via `title`, so nothing is lost.
            label=" " if hide_labels else name,
            title=name,
            color="#C7401E" if is_flagged else ("#291EC7" if is_real else "#6B6358"),
            size=25 if is_real else 12,
            shape="dot" if is_real else "square",
        )
    for u, v, attrs in G.edges(data=True):
        amount = attrs.get("amount", 0)
        net.add_edge(
            str(u), str(v),
            value=max(1, amount / 1000),
            title=f"₹{amount:,.2f} on {attrs.get('date', '?')}",
        )

    # Bounded stabilisation + interaction options. dragNodes/dragView/zoomView
    # keep the manual controls; hover surfaces labels once they're hidden.
    net.set_options(json.dumps({
        "physics": {
            "stabilization": {"enabled": True, "iterations": 200, "fit": True},
            "barnesHut": {"avoidOverlap": 0.2},
        },
        "interaction": {
            "dragNodes": True, "dragView": True, "zoomView": True,
            "hover": True, "tooltipDelay": 80,
        },
    }))

    try:
        html = net.generate_html(notebook=False)
    except TypeError:
        html = net.generate_html()

    # Freeze the layout the instant stabilisation finishes so it stops drifting
    # (pyvis names its vis-network instance `network`). Manual drag/pan/zoom is
    # unaffected — only the continuous auto-simulation is switched off.
    freeze_script = (
        "<script type=\"text/javascript\">"
        "if (typeof network !== 'undefined') {"
        "  network.once('stabilizationIterationsDone', function () {"
        "    network.setOptions({ physics: false });"
        "  });"
        "}"
        "</script>"
    )
    if "</body>" in html:
        html = html.replace("</body>", freeze_script + "</body>", 1)
    else:
        html += freeze_script
    return html


def _summarize_graph(G: nx.DiGraph, flagged_accounts: set[str]) -> str:
    real = [n for n, d in G.nodes(data=True) if d.get("node_type") == "real_account"]
    heuristic = [n for n, d in G.nodes(data=True) if d.get("node_type") == "heuristic_counterparty"]
    flagged_here = [n for n in real if str(n) in flagged_accounts]
    parts = [
        f"Money-flow graph: {len(real)} account node(s) and "
        f"{len(heuristic)} heuristic counterparty node(s) across "
        f"{G.number_of_edges()} transaction edge(s)."
    ]
    if flagged_here:
        parts.append(
            f"Account(s) with flagged transactions are highlighted in red: "
            f"{', '.join(str(a) for a in flagged_here)}."
        )
    return " ".join(parts)


def build_graph_response(question: str, case: dict, focus_account: str | None = None) -> dict:
    """
    Routing entry point for Section 1. Returns an answer dict with either an
    interactive pyvis graph (single-account, focused) or a Plotly Sankey
    (whole-case — pyvis's physics simulation is what gets slow/illegible at
    ~1700+ nodes, so the whole-case view aggregates by transaction-type
    category instead), plus a short text summary.
    """
    records = transactions_for_graph(case, focus_account)
    if not records:
        return {
            "answer": "No money-flow graph could be drawn — no transactions matched.",
            "graph_html": None,
            "chart": None,
            "disclaimer": None,
            "citations": [],
            "matched_pattern": "graph_request_empty",
        }

    if focus_account:
        graph = build_transaction_graph(records, focus_account)
        flagged_accounts = get_flagged_account_ids(case)
        if graph.number_of_edges() == 0:
            return {
                "answer": (
                    "No money-flow graph could be drawn — no usable counterparty "
                    "could be inferred from the transaction narrations for this "
                    "request."
                ),
                "graph_html": None,
                "chart": None,
                "disclaimer": None,
                "citations": [],
                "matched_pattern": "graph_request_empty",
            }
        html = render_graph_html(graph, flagged_accounts=flagged_accounts)
        return {
            "answer": _summarize_graph(graph, flagged_accounts),
            "graph_html": html,
            "chart": None,
            "disclaimer": HEURISTIC_DISCLAIMER,
            "citations": [],
            "matched_pattern": "graph_request",
        }

    sankey = build_sankey_figure(records, case)
    if sankey is None:
        return {
            "answer": "No money-flow Sankey could be drawn — no transactions had a usable amount.",
            "graph_html": None,
            "chart": None,
            "disclaimer": None,
            "citations": [],
            "matched_pattern": "graph_request_empty",
        }
    return {
        "answer": _summarize_sankey(records),
        "graph_html": None,
        "chart": sankey,
        "disclaimer": (
            "This whole-case view aggregates money flow by transaction-type category "
            "(UPI/NEFT/RTGS/IMPS/Cheque/Cash/Other) rather than by individual counterparty, "
            "for legibility and performance. Ask about a specific account by name or number "
            "for a detailed node-link view of that account's individual counterparties."
        ),
        "citations": [],
        "matched_pattern": "graph_request_sankey",
    }
