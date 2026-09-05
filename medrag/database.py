from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
  sha256 TEXT NOT NULL, indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL, locator TEXT NOT NULL, text TEXT NOT NULL,
  UNIQUE(document_id, chunk_index)
);
CREATE TABLE IF NOT EXISTS concepts (
  concept_id TEXT PRIMARY KEY, canonical_name TEXT NOT NULL UNIQUE, entity_type TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '', confidence REAL NOT NULL DEFAULT 0.5,
  status TEXT NOT NULL DEFAULT 'accepted'
);
CREATE TABLE IF NOT EXISTS mentions (
  concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  chunk_id TEXT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  evidence TEXT NOT NULL, PRIMARY KEY(concept_id, chunk_id, evidence)
);
CREATE TABLE IF NOT EXISTS edges (
  edge_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  target_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
  relation TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', confidence REAL NOT NULL DEFAULT 0.5,
  status TEXT NOT NULL DEFAULT 'accepted',
  chunk_id TEXT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
  evidence TEXT NOT NULL, UNIQUE(source_id, target_id, relation, chunk_id)
);
CREATE TABLE IF NOT EXISTS runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL, mode TEXT NOT NULL,
  provider TEXT NOT NULL, model TEXT NOT NULL, request_json TEXT NOT NULL,
  evidence_json TEXT NOT NULL, response_text TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_mentions_chunk_id ON mentions(chunk_id);
CREATE INDEX IF NOT EXISTS idx_edges_source_id ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target_id ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    for table, column in (("concepts", "status"), ("edges", "status")):
        columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN status TEXT NOT NULL DEFAULT 'accepted'")
    conn.execute("PRAGMA optimize")
    return conn


def reset_content(conn: sqlite3.Connection) -> None:
    for table in ("edges", "mentions", "concepts", "chunks", "documents"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def log_run(conn: sqlite3.Connection, task: str, mode: str, provider: str, model: str, request: Any, evidence: Any, response: str) -> int:
    cur = conn.execute(
        "INSERT INTO runs(task,mode,provider,model,request_json,evidence_json,response_text) VALUES(?,?,?,?,?,?,?)",
        (task, mode, provider, model, json.dumps(request), json.dumps(evidence), response),
    )
    conn.commit()
    return int(cur.lastrowid)
