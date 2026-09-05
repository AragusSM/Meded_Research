from __future__ import annotations

import argparse
import json
import pickle
import shutil
import sqlite3
import re
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer

from .database import connect, reset_content


def _locator(value: str | None) -> str:
    try:
        page = json.loads(value or "{}").get("page")
        return f"page {page}" if page else "document"
    except (TypeError, ValueError, json.JSONDecodeError):
        return "document"


def _find_document(source_root: Path, relative_path: str, filename: str) -> Path | None:
    candidates = [source_root / Path(relative_path), *source_root.rglob(filename)]
    exact = next((path for path in candidates if path.is_file()), None)
    if exact:
        return exact
    normalize = lambda value: re.sub(r"[^a-z0-9]", "", value.lower()).replace("medivale", "medvale")
    wanted = normalize(filename)
    return next((path for path in source_root.rglob("*") if path.is_file() and normalize(path.name) == wanted), None)


def _module_specs(source: sqlite3.Connection) -> list[dict[str, str | None]]:
    rows = source.execute(
        "SELECT source_module_id,display_name FROM source_modules WHERE status='active' ORDER BY display_name"
    ).fetchall()
    specs: list[dict[str, str | None]] = [{"id": None, "name": "All Internal Medicine", "collection": "medivale-im"}]
    specs.extend({
        "id": row["source_module_id"], "name": row["display_name"],
        "collection": f"medivale-{row['source_module_id'].replace('_', '-')}",
    } for row in rows)
    return specs


def _placeholders(count: int) -> str:
    return ",".join("?" for _ in range(count))


def import_module(source: sqlite3.Connection, source_root: Path, data_root: Path, spec: dict[str, str | None]) -> dict[str, Any]:
    module_id, collection_id = spec["id"], str(spec["collection"])
    collection = data_root / collection_id
    documents_dir = collection / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    target = connect(collection / "knowledge.sqlite3")
    reset_content(target)

    condition, params = ("", ()) if module_id is None else ("WHERE source_module_id=?", (module_id,))
    documents = source.execute(
        f"SELECT document_id,title,filename,relative_path,checksum FROM source_documents {condition} ORDER BY filename", params
    ).fetchall()
    chunks = source.execute(
        f"SELECT chunk_id,document_id,chunk_index,text,locator_json FROM source_chunks {condition} ORDER BY document_id,chunk_index", params
    ).fetchall()
    if not chunks:
        target.close()
        return {"collection_id": collection_id, "skipped": True}

    copied = 0
    document_titles = {row["document_id"]: row["title"] or row["filename"] for row in documents}
    document_paths: dict[str, Path] = {}
    for row in documents:
        destination = documents_dir / row["filename"]
        source_file = _find_document(source_root, row["relative_path"] or "", row["filename"])
        if source_file:
            shutil.copy2(source_file, destination)
            copied += 1
        document_paths[row["document_id"]] = destination
        target.execute(
            "INSERT INTO documents(document_id,path,title,sha256) VALUES(?,?,?,?)",
            (row["document_id"], str(destination), document_titles[row["document_id"]], row["checksum"] or "bundled"),
        )

    chunk_records: list[dict[str, Any]] = []
    chunk_ids = []
    for row in chunks:
        locator = _locator(row["locator_json"])
        target.execute(
            "INSERT INTO chunks(chunk_id,document_id,chunk_index,locator,text) VALUES(?,?,?,?,?)",
            (row["chunk_id"], row["document_id"], row["chunk_index"], locator, row["text"]),
        )
        chunk_ids.append(row["chunk_id"])
        chunk_records.append({
            "chunk_id": row["chunk_id"], "document_id": row["document_id"],
            "source_path": str(document_paths[row["document_id"]]),
            "title": document_titles[row["document_id"]], "locator": locator, "text": row["text"],
        })

    chunk_marks = _placeholders(len(chunk_ids))
    if module_id is None:
        concept_rows = source.execute("SELECT * FROM concept_nodes").fetchall()
    else:
        concept_rows = source.execute(
            f"SELECT DISTINCT cn.* FROM concept_nodes cn JOIN mentions m ON m.concept_id=cn.concept_id "
            f"WHERE m.chunk_id IN ({chunk_marks}) AND cn.status!='rejected'", chunk_ids,
        ).fetchall()
    concept_ids = {row["concept_id"] for row in concept_rows}
    for row in concept_rows:
        target.execute(
            "INSERT INTO concepts(concept_id,canonical_name,entity_type,description,confidence,status) VALUES(?,?,?,?,?,?)",
            (row["concept_id"], row["canonical_name"], row["entity_type"] or "other", row["description"] or "", row["confidence"] or .5, row["status"] or "candidate"),
        )
    mention_rows = source.execute(
        f"SELECT concept_id,chunk_id,raw_text FROM mentions WHERE chunk_id IN ({chunk_marks}) "
        "AND concept_id IS NOT NULL AND status!='rejected'", chunk_ids,
    ).fetchall()
    for row in mention_rows:
        if row["concept_id"] in concept_ids:
            target.execute(
                "INSERT OR IGNORE INTO mentions(concept_id,chunk_id,evidence) VALUES(?,?,?)",
                (row["concept_id"], row["chunk_id"], row["raw_text"] or "source mention"),
            )

    concept_list = sorted(concept_ids)
    edge_rows = []
    if concept_list:
        marks = _placeholders(len(concept_list))
        status_filter = "" if module_id is None else "AND status!='rejected'"
        edge_rows = source.execute(
            f"SELECT * FROM concept_edges WHERE source_concept_id IN ({marks}) "
            f"AND target_concept_id IN ({marks}) {status_filter}",
            [*concept_list, *concept_list],
        ).fetchall()
    fallback_chunk = chunk_ids[0]
    chunk_set = set(chunk_ids)
    edges_added = 0
    for edge in edge_rows:
        support = source.execute(
            "SELECT m.chunk_id,fm.quote,f.normalized_claim FROM edge_facts ef "
            "JOIN facts f ON f.fact_id=ef.fact_id LEFT JOIN fact_mentions fm ON fm.fact_id=f.fact_id "
            "LEFT JOIN mentions m ON m.mention_id=fm.mention_id WHERE ef.edge_id=?",
            (edge["edge_id"],),
        ).fetchall()
        selected = next((row for row in support if row["chunk_id"] in chunk_set), None)
        chunk_id = selected["chunk_id"] if selected else fallback_chunk
        evidence = (selected["quote"] or selected["normalized_claim"]) if selected else (edge["description"] or "Imported MedVale relationship")
        target.execute(
            "INSERT OR IGNORE INTO edges(edge_id,source_id,target_id,relation,description,confidence,status,chunk_id,evidence) VALUES(?,?,?,?,?,?,?,?,?)",
            (edge["edge_id"], edge["source_concept_id"], edge["target_concept_id"], edge["edge_type"].upper(),
             edge["description"] or "", edge["confidence"] or .5, edge["status"] or "candidate", chunk_id, evidence),
        )
        edges_added += 1

    vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2), max_features=100_000)
    matrix = vectorizer.fit_transform([row["text"] for row in chunk_records])
    with (collection / "vectors.pkl").open("wb") as handle:
        pickle.dump({"vectorizer": vectorizer, "matrix": matrix, "chunks": chunk_records}, handle)
    manifest = {
        "schema_version": "medivale_graph_v1",
        "display_name": f"MedVale IM · {spec['name']}", "bundled": True, "read_only": True,
        "module_id": module_id, "documents": len(documents), "documents_available": copied,
        "chunks": len(chunks), "graph_node_mentions": len(mention_rows), "graph_nodes": len(concept_rows),
        "graph_edges": edges_added, "graph_errors": 0, "provider": "MedVale curated", "model": "prebuilt",
    }
    (collection / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    target.commit()
    target.execute("PRAGMA optimize")
    target.close()
    return {"collection_id": collection_id, **manifest}


def import_medivale(source_db: Path, source_root: Path, data_root: Path) -> list[dict[str, Any]]:
    source = sqlite3.connect(f"file:{source_db.as_posix()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    try:
        return [import_module(source, source_root, data_root, spec) for spec in _module_specs(source)]
    finally:
        source.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import MedVale internal medicine as built-in RAG collections")
    parser.add_argument("--source-db", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    results = import_medivale(args.source_db.resolve(), args.source_root.resolve(), args.data_root.resolve())
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
