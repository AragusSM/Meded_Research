from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer

from .database import connect


def _fit(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    if not chunks:
        raise ValueError("collection contains no document chunks; upload and index a document first")
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=100_000,
    )
    matrix = vectorizer.fit_transform([str(chunk.get("text", "")) for chunk in chunks])
    return {
        "format_version": 2,
        "sklearn_version": sklearn.__version__,
        "vectorizer": vectorizer,
        "matrix": matrix,
        "chunks": chunks,
    }


def _write(path: Path, store: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".pkl.tmp")
    with temporary.open("wb") as handle:
        pickle.dump(store, handle, protocol=pickle.HIGHEST_PROTOCOL)
    temporary.replace(path)


def write_vector_store(collection_dir: Path, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    store = _fit(chunks)
    _write(collection_dir / "vectors.pkl", store)
    return store


def _database_chunks(collection_dir: Path) -> list[dict[str, Any]]:
    database = collection_dir / "knowledge.sqlite3"
    if not database.exists():
        return []
    conn = connect(database)
    rows = conn.execute(
        "SELECT c.chunk_id,c.document_id,c.locator,c.text,d.path source_path,d.title "
        "FROM chunks c JOIN documents d ON d.document_id=c.document_id "
        "ORDER BY d.title,c.chunk_index"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _validate(store: Any) -> dict[str, Any]:
    if not isinstance(store, dict):
        raise ValueError("vector index has an invalid format")
    chunks = store.get("chunks")
    matrix = store.get("matrix")
    vectorizer = store.get("vectorizer")
    if not isinstance(chunks, list) or matrix is None or vectorizer is None:
        raise ValueError("vector index is missing required data")
    if matrix.shape[0] != len(chunks):
        raise ValueError("vector index rows do not match its document chunks")
    # A transform exercises both vocabulary_ and the fitted IDF state. Merely
    # checking vocabulary_ does not detect some cross-version pickle failures.
    probe = vectorizer.transform(["medvale vector index validation"])
    if probe.shape[1] != matrix.shape[1]:
        raise ValueError("vector index dimensions do not match")
    return store


def load_vector_store(collection_dir: Path) -> dict[str, Any]:
    """Load a vector index, rebuilding recoverable fitted-state failures."""
    path = collection_dir / "vectors.pkl"
    if not path.exists():
        raise FileNotFoundError(f"collection has no vector index: {collection_dir.name}")

    store: Any = None
    try:
        with path.open("rb") as handle:
            store = pickle.load(handle)
        return _validate(store)
    except (OSError, EOFError, pickle.PickleError, ImportError, AttributeError, TypeError, ValueError):
        chunks = store.get("chunks", []) if isinstance(store, dict) else []
        if not chunks:
            chunks = _database_chunks(collection_dir)
        if not chunks:
            raise ValueError(
                f"vector index for {collection_dir.name} is damaged and has no chunks available to rebuild it"
            )
        repaired = _fit(chunks)
        _write(path, repaired)
        return repaired
