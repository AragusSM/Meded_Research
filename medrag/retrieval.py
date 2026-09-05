from __future__ import annotations

import pickle
import re
from pathlib import Path
from typing import Any

from sklearn.metrics.pairwise import cosine_similarity

from .database import connect


VALID_MODES = {"document", "vector", "graph", "hybrid"}


def _chunk_evidence(chunk: dict[str, Any], score: float, source: str) -> dict[str, Any]:
    return {"kind": "chunk", "source": source, "score": round(float(score), 6), **chunk}


def vector_retrieve(collection_dir: Path, query: str, k: int = 8) -> list[dict[str, Any]]:
    with (collection_dir / "vectors.pkl").open("rb") as handle:
        store = pickle.load(handle)
    scores = cosine_similarity(store["vectorizer"].transform([query]), store["matrix"])[0]
    ids = scores.argsort()[::-1][:k]
    return [_chunk_evidence(store["chunks"][int(i)], scores[int(i)], "vector") for i in ids if scores[int(i)] > 0]


def document_retrieve(collection_dir: Path, k: int = 8) -> list[dict[str, Any]]:
    with (collection_dir / "vectors.pkl").open("rb") as handle:
        chunks = pickle.load(handle)["chunks"]
    return [_chunk_evidence(c, 0.0, "document") for c in chunks[:k]]


def graph_retrieve(collection_dir: Path, query: str, limit: int = 24) -> list[dict[str, Any]]:
    terms = [t for t in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", query.lower()) if t not in {"what", "which", "when", "where", "does", "with", "from", "about", "explain"}]
    if not terms:
        return []
    conn = connect(collection_dir / "knowledge.sqlite3")
    clauses = " OR ".join("lower(canonical_name) LIKE ?" for _ in terms)
    roots = conn.execute(f"SELECT concept_id FROM concepts WHERE {clauses} ORDER BY confidence DESC LIMIT 6", tuple(f"%{t}%" for t in terms)).fetchall()
    root_ids = [r["concept_id"] for r in roots]
    if not root_ids:
        conn.close()
        return []
    placeholders = ",".join("?" for _ in root_ids)
    rows = conn.execute(
        f"""SELECT e.*, s.canonical_name source_name, t.canonical_name target_name,
        c.text, c.locator, d.title, d.path source_path
        FROM edges e JOIN concepts s ON s.concept_id=e.source_id JOIN concepts t ON t.concept_id=e.target_id
        JOIN chunks c ON c.chunk_id=e.chunk_id JOIN documents d ON d.document_id=c.document_id
        WHERE e.source_id IN ({placeholders}) OR e.target_id IN ({placeholders})
        ORDER BY e.confidence DESC LIMIT ?""", (*root_ids, *root_ids, limit)).fetchall()
    out = [{"kind": "edge", "source": "graph", "score": float(r["confidence"]), "source_name": r["source_name"], "relation": r["relation"], "target_name": r["target_name"], "description": r["description"], "evidence": r["evidence"], "text": r["text"], "locator": r["locator"], "title": r["title"], "source_path": r["source_path"]} for r in rows]
    conn.close()
    return out


def retrieve(collection_dir: Path, query: str, mode: str, k: int = 8) -> list[dict[str, Any]]:
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")
    if mode == "document":
        return document_retrieve(collection_dir, k)
    if mode == "vector":
        return vector_retrieve(collection_dir, query, k)
    if mode == "graph":
        return graph_retrieve(collection_dir, query, max(k, 12))
    vector = vector_retrieve(collection_dir, query, k)
    graph = graph_retrieve(collection_dir, query, max(k, 12))
    seen, merged = set(), []
    for item in [*vector, *graph]:
        key = (item.get("kind"), item.get("chunk_id"), item.get("source_name"), item.get("relation"), item.get("target_name"))
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged

