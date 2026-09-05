from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

from sklearn.decomposition import TruncatedSVD


def _scale(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [0.5] * len(values)
    return [(value - low) / (high - low) for value in values]


def collection_visualization(collection_dir: Path, limit: int = 300) -> dict[str, Any]:
    vector_path = collection_dir / "vectors.pkl"
    if not vector_path.exists():
        raise FileNotFoundError(f"collection has no vector index: {collection_dir.name}")
    with vector_path.open("rb") as handle:
        store = pickle.load(handle)
    chunks = store["chunks"][:limit]
    matrix = store["matrix"][:len(chunks)]
    if not chunks:
        return {"vectors": [], "chunks": []}
    if len(chunks) == 1 or min(matrix.shape) <= 1:
        coordinates = [(0.5, 0.5)] * len(chunks)
    else:
        components = min(2, min(matrix.shape) - 1)
        projected = TruncatedSVD(n_components=components, random_state=42).fit_transform(matrix)
        xs = _scale([float(row[0]) for row in projected])
        ys = _scale([float(row[1]) if components > 1 else float(index) for index, row in enumerate(projected)])
        coordinates = list(zip(xs, ys))
    rows = []
    for chunk, (x, y) in zip(chunks, coordinates):
        rows.append({
            "chunk_id": chunk["chunk_id"], "document_id": chunk["document_id"],
            "title": chunk["title"], "locator": chunk["locator"],
            "source_type": Path(chunk["source_path"]).suffix.lower().lstrip("."),
            "text": chunk["text"], "x": x, "y": y,
        })
    return {"vectors": rows, "chunks": rows}
