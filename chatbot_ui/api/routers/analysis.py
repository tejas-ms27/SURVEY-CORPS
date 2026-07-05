from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.deps import load_case_resources
from api.utils import df_to_records
from chatbot.case_analytics import (
    account_summary_dataframe,
    build_relationship_graph,
    counterparty_summary_dataframe,
    duplicate_dataframe,
    flag_reason_dataframe,
    relationship_graph_to_json,
)

router = APIRouter(prefix="/api/cases/{case_id}", tags=["analysis"])


def _resources(case_id: str):
    try:
        return load_case_resources(case_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/accounts")
def get_accounts(case_id: str):
    resources = _resources(case_id)
    return {"accounts": df_to_records(account_summary_dataframe(resources["case"]))}


@router.get("/flags")
def get_flags(case_id: str):
    resources = _resources(case_id)
    return {"flags": df_to_records(flag_reason_dataframe(resources["case"]))}


@router.get("/duplicates")
def get_duplicates(case_id: str):
    resources = _resources(case_id)
    return {"duplicates": df_to_records(duplicate_dataframe(resources["case"]))}


@router.get("/counterparties")
def get_counterparties(case_id: str, top_n: int = Query(25, ge=1, le=200)):
    resources = _resources(case_id)
    return {"counterparties": df_to_records(counterparty_summary_dataframe(resources["case"], top_n=top_n))}


@router.get("/graph")
def get_graph(case_id: str):
    resources = _resources(case_id)
    graph = build_relationship_graph(resources["case"])
    return relationship_graph_to_json(graph)


@router.get("/transactions")
def get_transactions(
    case_id: str,
    source: str = Query("clean", pattern="^(clean|flagged|duplicates)$"),
    account: str | None = None,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    resources = _resources(case_id)
    case = resources["case"]
    df = case[source]
    if account:
        account_col = "account_number" if "account_number" in df.columns else "Account_ID"
        if account_col in df.columns:
            df = df[df[account_col].astype(str) == account]
    total = len(df)
    page = df.iloc[offset:offset + limit]
    return {"total": total, "offset": offset, "limit": limit, "rows": df_to_records(page)}
