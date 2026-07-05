"""Small shared helpers for the API routers."""

from __future__ import annotations

import math

import pandas as pd


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """
    Convert a DataFrame to a JSON-safe list of dicts: NaN/NaT -> None,
    Timestamps -> ISO strings. `df.to_dict` alone leaves NaN in place, which
    is not valid JSON and breaks strict clients.
    """
    if df is None or df.empty:
        return []
    clean = df.copy()
    for col in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[col]):
            clean[col] = clean[col].dt.strftime("%Y-%m-%d").where(clean[col].notna(), None)
    clean = clean.astype(object).where(pd.notnull(clean), None)
    records = clean.to_dict(orient="records")
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None
    return records
