"""
deps.py — case-resource loading and in-process caching for the FastAPI backend.

Mirrors what app.py did with @st.cache_resource, but Streamlit's cache
doesn't exist here — uvicorn runs one long-lived process, so a plain module
level dict is enough. Keyed by case_id; a `rebuild_nonce` bump (via the
re-index endpoint) forces a fresh load + re-ingest.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from api.analysis_index import analysis_chunks
from chatbot.case_registry import CASES_ROOT, EXTRACTIONS_ROOT, get_case_dir, list_available_cases
from chatbot.chunking_v2 import case_to_chunks
from chatbot.data_loader import load_full_case
from chatbot.structuring import structuring_results_by_account
from chatbot.vector_store import get_collection
from chatbot.vector_store import get_client as _new_client

_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_LOCK = threading.Lock()

# chatbot.vector_store.get_client() constructs a brand-new
# chromadb.PersistentClient on every call. Streamlit's single-session model
# made that harmless, but FastAPI serves concurrent requests (the frontend
# fires several case-data GETs in parallel per page), and multiple
# PersistentClient instances racing to open the same on-disk sqlite store
# intermittently raises "Could not connect to tenant default_tenant" — so the
# client is cached here as a process-wide singleton instead.
_client_singleton = None
_client_lock = threading.Lock()


def get_client():
    global _client_singleton
    if _client_singleton is None:
        with _client_lock:
            if _client_singleton is None:
                _client_singleton = _new_client()
    return _client_singleton


def latest_case_id() -> str | None:
    cases = list_available_cases()
    if not cases:
        return None

    def modified_time(case_id: str) -> float:
        try:
            return get_case_dir(case_id).stat().st_mtime
        except OSError:
            return 0.0

    return max(cases, key=modified_time)


def _ingest(collection, chunks: list[dict], batch_size: int = 200) -> int:
    if not chunks:
        return 0
    total = len(chunks)
    for start in range(0, total, batch_size):
        batch = chunks[start:start + batch_size]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["text"] for chunk in batch],
            metadatas=[chunk["metadata"] for chunk in batch],
        )
    return total


def load_case_resources(case_id: str, force_reindex: bool = False) -> dict[str, Any]:
    """
    Load (and cache) everything needed to serve a case: the parsed dataframes,
    RAG chunks, the ChromaDB collection (indexed on first load), and the
    cached structuring scan. Raises FileNotFoundError via get_case_dir if the
    case_id isn't valid.
    """
    case_dir = get_case_dir(case_id)
    cached = _CACHE.get(case_id)
    if cached and not force_reindex:
        return cached

    with _CACHE_LOCK:
        # Re-check inside the lock: another thread may have just finished
        # loading this exact case while we were waiting.
        cached = _CACHE.get(case_id)
        if cached and not force_reindex:
            return cached

        case = load_full_case(case_dir)
        # Extraction chunks (transactions/flags/duplicates/account context) PLUS chunks
        # derived from the deep fraud engine (Case Narrative, suspicion scores, prime
        # suspects, per-account findings) when analysis has been run — so the chatbot can
        # answer questions about the analysis and the report, not just the raw statements.
        chunks = case_to_chunks(case) + analysis_chunks(case_id)
        client = get_client()
        collection = get_collection(client, case_id=case_id)
        if force_reindex or collection.count() != len(chunks):
            _ingest(collection, chunks)

        resources = {
            "case_dir": case_dir,
            "case": case,
            "chunks": chunks,
            "collection": collection,
            "indexed_count": collection.count(),
            "structuring_by_account": structuring_results_by_account(case),
        }
        _CACHE[case_id] = resources
        return resources


def invalidate_case(case_id: str) -> None:
    _CACHE.pop(case_id, None)


def invalidate_all() -> None:
    _CACHE.clear()


def delete_case(case_id: str) -> tuple[bool, str]:
    """
    Permanently remove a case: its extraction folder and its ChromaDB
    collection. Guarded so it only ever deletes folders under the managed
    case roots.
    """
    import shutil

    try:
        case_dir = get_case_dir(case_id).resolve()
    except Exception as exc:
        return False, f"Could not resolve case: {exc}"

    managed_roots = [CASES_ROOT.resolve(), EXTRACTIONS_ROOT.resolve()]
    if not any(root in case_dir.parents for root in managed_roots):
        return False, "Refusing to delete: case is outside the managed case folders."

    try:
        get_client().delete_collection(f"case_{case_id}")
    except Exception:
        pass
    shutil.rmtree(case_dir, ignore_errors=True)
    invalidate_case(case_id)
    return True, f"Deleted case '{case_id}'."
