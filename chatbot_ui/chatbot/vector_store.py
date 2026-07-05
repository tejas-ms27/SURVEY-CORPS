"""
vector_store.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: ChromaDB Ingestion + Retrieval

Handles:
  1. Creating a persistent ChromaDB collection on disk
  2. Ingesting transaction + fraud-pattern chunks (with metadata)
  3. Querying with optional metadata filters (account, pattern_type, severity)

NOTE ON EMBEDDINGS:
  ChromaDB's default embedding function (all-MiniLM-L6-v2, run via
  onnxruntime) is used here. It downloads automatically on first use,
  requires no separate sentence-transformers install, and is more than
  good enough for this corpus size. If you later want a stronger
  embedding model, swap the `embedding_function` passed to
  chromadb.Client / get_or_create_collection.
"""

import chromadb
from pathlib import Path

PERSIST_DIR = Path("./chroma_store")  # change to wherever you want this to live


def get_client() -> chromadb.PersistentClient:
    """Returns a persistent ChromaDB client backed by local disk storage."""
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(PERSIST_DIR))


def get_collection(client: chromadb.PersistentClient, case_id: str = "default_case"):
    """
    Get or create a collection scoped to a single investigation case.
    Using one collection per case keeps cross-case data cleanly separated
    if you're running this against multiple accused-person cases.
    """
    return client.get_or_create_collection(name=f"case_{case_id}")


def ingest_chunks(collection, chunks: list[dict], batch_size: int = 200) -> None:
    """
    Ingest a list of chunk dicts (from chunking.py) into the collection.

    Each chunk dict must have: "id", "text", "metadata"
    ChromaDB handles embedding internally via the collection's embedding
    function — we just pass raw text.

    Ingests in batches with progress printed after each one. This matters
    for real case sizes (2000+ chunks) where a single unbatched upsert call
    embeds everything before printing anything — on a CPU-only embedding
    model that can take a couple of minutes with zero visible feedback,
    which looks identical to a hang. Batching here is purely for visible
    progress; ChromaDB itself can technically accept one large call.
    """
    if not chunks:
        return

    total = len(chunks)
    for start in range(0, total, batch_size):
        batch = chunks[start : start + batch_size]
        collection.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        done = min(start + batch_size, total)
        print(f"[vector_store] Embedded and ingested {done}/{total} chunks...")

    print(f"[vector_store] Done. {total} chunks ingested into '{collection.name}'.")


def query(
    collection,
    query_text: str,
    n_results: int = 5,
    where: dict | None = None,
) -> dict:
    """
    Run a similarity search against the collection, with an optional
    metadata filter.

    Parameters
    ----------
    query_text : the investigator's natural-language question
    n_results  : how many chunks to retrieve
    where      : optional ChromaDB metadata filter, e.g.
                 {"account_id": "ACC1001"}
                 {"pattern_type": "round_tripping"}
                 {"chunk_type": "fraud_pattern"}

    Returns
    -------
    dict with keys: "documents", "metadatas", "ids", "distances"
    (each a list of lists, per ChromaDB's API — we flatten for n_results=1 query)
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
    )
    return {
        "documents": results["documents"][0],
        "metadatas": results["metadatas"][0],
        "ids": results["ids"][0],
        "distances": results["distances"][0],
    }


def build_metadata_filter(
    account_id: str | None = None,
    pattern_type: str | None = None,
    severity: str | None = None,
    chunk_type: str | None = None,
) -> dict | None:
    """
    Helper to build a ChromaDB `where` filter from optional investigator
    constraints (e.g. parsed from the question, or from UI filter controls).

    ChromaDB requires a single top-level operator when combining multiple
    conditions, so we wrap multiple filters in "$and".
    """
    conditions = []
    if account_id:
        conditions.append({"account_id": account_id})
    if pattern_type:
        conditions.append({"pattern_type": pattern_type})
    if severity:
        conditions.append({"severity": severity})
    if chunk_type:
        conditions.append({"chunk_type": chunk_type})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}