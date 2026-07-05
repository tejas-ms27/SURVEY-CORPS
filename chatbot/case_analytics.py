"""
case_analytics.py
─────────────────────────────────────────────────────────────────────────────
Framework-agnostic case analytics helpers shared by the Streamlit console
(app.py) and the FastAPI backend (api/). Pulled out of app.py so both
front ends compute identical numbers from a single source of truth instead
of two copies of the same logic drifting apart.

Every function here takes a `case` dict (the same shape returned by
chatbot.data_loader.load_full_case) and returns plain pandas DataFrames or
JSON-serialisable structures — no Streamlit, no matplotlib.
"""

from __future__ import annotations

import html as html_lib
import re
from datetime import datetime

import networkx as nx
import pandas as pd

from chatbot.counterparty import extract_counterparty_hint, infer_direction_amount


def build_case_id(user_input: str | None) -> str:
    """
    Turn an investigator-typed case name into a safe, unique folder/case id.
    Blank input falls back to the timestamp-only 'run_<ts>' name. A timestamp
    suffix is ALWAYS appended so re-running the same name never collides with
    an earlier run's folder.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not user_input or not user_input.strip():
        return f"run_{ts}"
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_input.strip())
    safe = re.sub(r"_+", "_", safe).strip("_")
    # Chroma collection names are "case_<id>" and capped at 63 chars; with the
    # 5-char prefix + 16-char "_<timestamp>" suffix, keep the name part <= 40.
    safe = safe[:40].strip("_")
    if not safe:
        return f"run_{ts}"
    return f"{safe}_{ts}"


def fmt_duration(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, remaining = divmod(int(round(seconds)), 60)
    return f"{minutes} min {remaining} s"


def fmt_amount(value) -> str:
    if value in (None, "") or pd.isna(value):
        return "not extracted"
    try:
        return f"Rs. {float(value):,.2f}"
    except (TypeError, ValueError):
        return "not extracted"


def account_summary_dataframe(case: dict) -> pd.DataFrame:
    clean_df = case["clean"]
    flagged_df = case["flagged"]
    rows = []
    for account_id, account_json in case["accounts"].items():
        details = account_json.get("account_details", {})
        rows.append({
            "holder": details.get("account_holder") or "not extracted",
            "bank": details.get("bank_name") or "not extracted",
            "account": account_id,
            "statement_period": details.get("statement_period") or "not extracted",
            "opening_balance": fmt_amount(details.get("opening_balance")),
            "closing_balance": fmt_amount(details.get("closing_balance")),
            "transactions": int((clean_df["account_number"] == account_id).sum()) if "account_number" in clean_df else 0,
            "flagged": int((flagged_df["Account_ID"] == account_id).sum()) if "Account_ID" in flagged_df else 0,
        })
    return pd.DataFrame(rows)


def flag_reason_dataframe(case: dict) -> pd.DataFrame:
    flagged_df = case["flagged"]
    if flagged_df.empty or "flag_reason" not in flagged_df:
        return pd.DataFrame(columns=["flag_reason", "count"])
    return (
        flagged_df["flag_reason"].fillna("unknown").value_counts()
        .rename_axis("flag_reason").reset_index(name="count")
    )


def duplicate_dataframe(case: dict) -> pd.DataFrame:
    dup_df = case["duplicates"]
    if dup_df.empty or "account_number" not in dup_df:
        return pd.DataFrame(columns=["account_number", "duplicates"])
    return dup_df.groupby("account_number").size().rename("duplicates").reset_index()


def counterparty_summary_dataframe(case: dict, top_n: int = 25) -> pd.DataFrame:
    clean_df = case["clean"]
    agg: dict[str, dict] = {}
    for _, row in clean_df.iterrows():
        hint = extract_counterparty_hint(row.get("Narration", ""))
        if not hint:
            continue
        direction, amount = infer_direction_amount(row)
        record = agg.setdefault(hint, {"counterparty": hint, "inflow": 0.0, "outflow": 0.0, "txns": 0})
        record["txns"] += 1
        if direction == "debit":
            record["outflow"] += float(amount or 0)
        else:
            record["inflow"] += float(amount or 0)
    if not agg:
        return pd.DataFrame(columns=["counterparty", "inflow", "outflow", "txns", "total"])
    df = pd.DataFrame(agg.values())
    df["total"] = df["inflow"] + df["outflow"]
    return df.sort_values("total", ascending=False).head(top_n).reset_index(drop=True)


def build_relationship_graph(case: dict, max_edges: int = 80) -> nx.DiGraph:
    clean_df = case["clean"]
    graph = nx.DiGraph()
    real_accounts = set(case["accounts"].keys())
    for account_id, account_json in case["accounts"].items():
        details = account_json.get("account_details", {})
        label = details.get("account_holder") or account_id
        graph.add_node(account_id, label=label, node_type="account")
    edge_weights: dict[tuple[str, str], float] = {}
    edge_counts: dict[tuple[str, str], int] = {}
    for _, row in clean_df.iterrows():
        account_id = str(row.get("account_number") or row.get("Account_ID") or "")
        if not account_id:
            continue
        hint = extract_counterparty_hint(row.get("Narration", ""))
        if not hint:
            continue
        counterparty_id = f"counterparty:{hint}"
        graph.add_node(counterparty_id, label=hint, node_type="counterparty")
        direction, amount = infer_direction_amount(row)
        source, target = (account_id, counterparty_id) if direction == "debit" else (counterparty_id, account_id)
        key = (source, target)
        edge_weights[key] = edge_weights.get(key, 0.0) + float(amount or 0)
        edge_counts[key] = edge_counts.get(key, 0) + 1
    top_edges = sorted(edge_weights.items(), key=lambda item: item[1], reverse=True)[:max_edges]
    trimmed = nx.DiGraph()
    for account_id in real_accounts:
        if account_id in graph:
            trimmed.add_node(account_id, **graph.nodes[account_id])
    for (source, target), weight in top_edges:
        for node in (source, target):
            if node in graph and node not in trimmed:
                trimmed.add_node(node, **graph.nodes[node])
        trimmed.add_edge(source, target, weight=weight, count=edge_counts[(source, target)])
    return trimmed


def relationship_graph_to_json(graph: nx.DiGraph) -> dict:
    """
    Convert the networkx relationship graph into a plain node/edge JSON shape
    a frontend graph library (e.g. react-force-graph) can consume directly.
    """
    nodes = [
        {
            "id": node_id,
            "label": data.get("label", str(node_id))[:40],
            "type": data.get("node_type", "account"),
        }
        for node_id, data in graph.nodes(data=True)
    ]
    edges = [
        {
            "source": source,
            "target": target,
            "weight": data.get("weight", 0.0),
            "count": data.get("count", 1),
        }
        for source, target, data in graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}


def citations_dataframe(citations: list[dict]) -> pd.DataFrame:
    if not citations:
        return pd.DataFrame()
    return pd.DataFrame(citations).fillna("")


def _html_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "<p class='muted'>No data.</p>"
    return df.to_html(index=False, border=0, classes="report-table", justify="left")


def build_case_report_html(case_id: str, resources: dict) -> str:
    case = resources["case"]
    accounts = account_summary_dataframe(case)
    flags = flag_reason_dataframe(case)
    dups = duplicate_dataframe(case)
    counterparties = counterparty_summary_dataframe(case, top_n=20)
    generated = datetime.now().strftime("%d %b %Y, %H:%M")
    dup_total = int(dups["duplicates"].sum()) if not dups.empty else 0
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Survey Corps — Case Report {html_lib.escape(case_id)}</title>
<style>
  :root {{ --blood:#B45309; --ink:#15110f; --muted:#6b625c; --line:#e6ddd6; }}
  *{{ box-sizing:border-box; }}
  body {{ font-family:"Segoe UI",Arial,sans-serif; color:var(--ink); margin:0; background:#efe9e2; }}
  .sheet {{ max-width:980px; margin:24px auto; background:#fbf8f4; padding:48px 56px;
            box-shadow:0 1px 5px rgba(0,0,0,.12); border-top:5px solid var(--blood); }}
  .eyebrow {{ font-family:"Consolas",monospace; letter-spacing:.26em; text-transform:uppercase;
             font-size:11px; color:var(--blood); }}
  h1 {{ font-size:30px; margin:6px 0 2px; letter-spacing:.01em; text-transform:uppercase; }}
  h2 {{ font-size:14px; text-transform:uppercase; letter-spacing:.08em; margin:30px 0 10px;
        border-bottom:2px solid var(--ink); padding-bottom:6px; }}
  .meta {{ color:var(--muted); font-size:13px; margin-bottom:8px; }}
  .stat-row {{ display:flex; gap:12px; margin:18px 0 4px; flex-wrap:wrap; }}
  .stat {{ border:1px solid var(--line); border-left:3px solid var(--blood); border-radius:4px;
           padding:10px 16px; min-width:118px; }}
  .stat .n {{ font-size:23px; font-weight:700; }}
  .stat .l {{ font-family:"Consolas",monospace; font-size:10px; letter-spacing:.12em;
              text-transform:uppercase; color:var(--muted); }}
  table.report-table {{ border-collapse:collapse; width:100%; font-size:12.5px; margin-top:6px; }}
  table.report-table th {{ text-align:left; background:#f0ebe4; padding:7px 9px;
        font-family:"Consolas",monospace; font-size:10.5px; letter-spacing:.06em;
        text-transform:uppercase; color:#39312c; border-bottom:1px solid var(--line); }}
  table.report-table td {{ padding:6px 9px; border-bottom:1px solid var(--line); }}
  .muted {{ color:var(--muted); font-size:13px; }}
  .disclaimer {{ margin-top:14px; font-size:12px; color:var(--muted); border-left:3px solid var(--blood);
                 padding:8px 12px; background:#fbf1ec; }}
  .foot {{ margin-top:36px; padding-top:12px; border-top:1px solid var(--line);
           font-family:"Consolas",monospace; font-size:11px; color:var(--muted);
           display:flex; justify-content:space-between; }}
  @media print {{ body {{ background:#fff; }} .sheet {{ box-shadow:none; margin:0; }} }}
</style></head>
<body><div class="sheet">
  <div class="eyebrow">Survey Corps · Financial Forensics Engine · Confidential</div>
  <h1>Case Report</h1>
  <div class="meta">Case <b>{html_lib.escape(case_id)}</b> &nbsp;·&nbsp; generated {generated}</div>
  <div class="stat-row">
    <div class="stat"><div class="n">{len(case['accounts'])}</div><div class="l">Accounts</div></div>
    <div class="stat"><div class="n">{len(case['clean'])}</div><div class="l">Clean rows</div></div>
    <div class="stat"><div class="n">{len(case['flagged'])}</div><div class="l">Flagged rows</div></div>
    <div class="stat"><div class="n">{dup_total}</div><div class="l">Duplicates</div></div>
    <div class="stat"><div class="n">{resources['indexed_count']}</div><div class="l">Indexed chunks</div></div>
  </div>
  <h2>Accounts in this case</h2>
  {_html_table(accounts)}
  <h2>Flagged transaction reasons</h2>
  {_html_table(flags)}
  <h2>Duplicate transactions removed</h2>
  {_html_table(dups)}
  <h2>Top counterparties (approximate)</h2>
  {_html_table(counterparties)}
  <div class="disclaimer">Counterparties are inferred from free-text transaction narrations and are
  approximate — they indicate likely external parties, not verified account matches.</div>
  <div class="foot"><span>SURVEY CORPS // CIDECODE</span><span>{html_lib.escape(case_id)}</span></div>
</div></body></html>"""
