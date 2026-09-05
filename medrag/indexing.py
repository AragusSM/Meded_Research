from __future__ import annotations

import hashlib
import json
import pickle
import re
import time
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer

from .database import connect, reset_content
from .providers import LLMProvider, ProviderError
from .readers import chunk_sections, discover_documents, read_document


GRAPH_SYSTEM = """You extract a medical knowledge graph strictly from supplied text.
Do not add outside knowledge. Every node and edge must include a short verbatim evidence quote
that appears in the text. Return JSON only. Omit uncertain or unsupported relationships.
Each node description must define the concept itself in document-grounded medical language. Put
relationships, patient-specific observations, indications, and management claims on edges instead.
Use the MedVale graph schema exactly so generated collections remain interoperable with bundled collections."""

ENTITY_TYPES = (
    "disease|syndrome|symptom|sign|finding|lab_test|imaging_test|procedure|treatment|drug|drug_class|"
    "anatomy|mechanism|physiologic_process|complication|risk_factor|outcome|management_strategy|"
    "diagnostic_criterion|other"
)
RELATION_TYPES = (
    "CAUSES|TREATS|INDICATES|DIAGNOSED_BY|RISK_FACTOR_FOR|ASSOCIATED_WITH|PART_OF|MANIFESTS_AS|"
    "COMPLICATED_BY|CONTRAINDICATED_WITH|MONITORED_BY|PREVENTS|PREDICTS|MECHANISM_OF|OTHER"
)


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value[:80] or "concept"


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def graph_prompt(text: str) -> str:
    return f'''Extract medical concepts and directed relationships from this passage.
Use concise canonical concept names, lowercase snake_case entity types, and uppercase snake_case relation labels.
Return exactly:
{{"schema_version":"medivale_graph_v1","nodes":[{{"name":"...","entity_type":"{ENTITY_TYPES}","description":"one or two standalone sentences defining what the concept is medically; do not describe only its relationship to another concept, this passage, or a patient","confidence":0.0,"status":"accepted","evidence":"exact quote"}}],
"edges":[{{"source":"node name","target":"node name","relation":"{RELATION_TYPES}","description":"...","confidence":0.0,"status":"accepted","evidence":"exact quote"}}]}}

PASSAGE:
{text}'''


def _grounded(evidence: str, text: str) -> bool:
    norm = lambda s: re.sub(r"\s+", " ", (s or "").strip().lower())
    return bool(norm(evidence)) and norm(evidence) in norm(text)


def _store_graph(conn, chunk_id: str, text: str, payload: dict[str, Any]) -> tuple[int, int]:
    names: dict[str, str] = {}
    nodes_added = edges_added = 0
    for node in payload.get("nodes", []):
        name, evidence = str(node.get("name", "")).strip(), str(node.get("evidence", "")).strip()
        if not name or not _grounded(evidence, text):
            continue
        concept_id = _slug(name)
        names[name.lower()] = concept_id
        entity_type = _slug(str(node.get("entity_type", "other")))
        conn.execute(
            "INSERT INTO concepts(concept_id,canonical_name,entity_type,description,confidence,status) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(concept_id) DO UPDATE SET confidence=MAX(confidence,excluded.confidence)",
            (concept_id, name, entity_type, str(node.get("description", "")), float(node.get("confidence", 0.5)), "accepted"),
        )
        conn.execute("INSERT OR IGNORE INTO mentions(concept_id,chunk_id,evidence) VALUES(?,?,?)", (concept_id, chunk_id, evidence))
        nodes_added += 1
    for edge in payload.get("edges", []):
        source_name, target_name = str(edge.get("source", "")).lower(), str(edge.get("target", "")).lower()
        evidence = str(edge.get("evidence", "")).strip()
        source_id, target_id = names.get(source_name), names.get(target_name)
        if not source_id or not target_id or source_id == target_id or not _grounded(evidence, text):
            continue
        relation = re.sub(r"[^A-Z0-9]+", "_", str(edge.get("relation", "ASSOCIATED_WITH")).upper()).strip("_")
        edge_id = _sha(f"{source_id}|{relation}|{target_id}|{chunk_id}".encode())[:24]
        conn.execute(
            "INSERT OR IGNORE INTO edges(edge_id,source_id,target_id,relation,description,confidence,status,chunk_id,evidence) VALUES(?,?,?,?,?,?,?,?,?)",
            (edge_id, source_id, target_id, relation, str(edge.get("description", "")), float(edge.get("confidence", 0.5)), "accepted", chunk_id, evidence),
        )
        edges_added += 1
    return nodes_added, edges_added


def _extract_graph(provider: LLMProvider, text: str, attempts: int = 4) -> dict[str, Any]:
    """Retry transient provider failures while preserving a useful final error."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            payload = provider.generate_json(graph_prompt(text), GRAPH_SYSTEM, 0.0)
            if not isinstance(payload, dict):
                raise ProviderError("graph response must be a JSON object")
            return payload
        except Exception as exc:
            last_error = exc
            status = getattr(exc, "status_code", None)
            retryable = status in {408, 409, 429, 500, 502, 503, 504} or status is None
            if attempt + 1 >= attempts or not retryable:
                break
            delay = getattr(exc, "retry_after", None) or (2 ** (attempt + 1))
            time.sleep(min(float(delay), 20.0))
    raise last_error or ProviderError("graph extraction failed")


def index_directory(collection_dir: Path, document_dir: Path, provider: LLMProvider | None, build_graph: bool) -> dict[str, Any]:
    db_path, vector_path = collection_dir / "knowledge.sqlite3", collection_dir / "vectors.pkl"
    files = discover_documents(document_dir)
    if not files:
        raise ValueError("no supported PDF, DOCX, TXT, or Markdown documents found")
    conn = connect(db_path)
    reset_content(conn)
    chunk_records: list[dict[str, Any]] = []
    graph_nodes = graph_edges = graph_errors = 0
    graph_error_details: list[dict[str, str]] = []
    graph_pause = 8.0 if getattr(provider, "name", "") == "groq" else 0.25
    last_graph_request = 0.0
    for path in files:
        raw = path.read_bytes()
        document_id = _sha(str(path).encode())[:20]
        conn.execute("INSERT INTO documents(document_id,path,title,sha256) VALUES(?,?,?,?)", (document_id, str(path), path.name, _sha(raw)))
        for index, section in enumerate(chunk_sections(read_document(path))):
            chunk_id = f"{document_id}_{index:05d}"
            conn.execute("INSERT INTO chunks(chunk_id,document_id,chunk_index,locator,text) VALUES(?,?,?,?,?)", (chunk_id, document_id, index, section.locator, section.text))
            chunk_records.append({"chunk_id": chunk_id, "document_id": document_id, "source_path": str(path), "title": path.name, "locator": section.locator, "text": section.text})
            if build_graph:
                if provider is None:
                    raise ValueError("a provider is required when build_graph is true")
                try:
                    elapsed = time.monotonic() - last_graph_request
                    if last_graph_request and elapsed < graph_pause:
                        time.sleep(graph_pause - elapsed)
                    payload = _extract_graph(provider, section.text)
                    last_graph_request = time.monotonic()
                    n, e = _store_graph(conn, chunk_id, section.text, payload)
                    graph_nodes += n
                    graph_edges += e
                except Exception as exc:
                    graph_errors += 1
                    graph_error_details.append({"chunk_id": chunk_id, "error": str(exc)[:500]})
        conn.commit()
    vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2), max_features=100_000)
    matrix = vectorizer.fit_transform([c["text"] for c in chunk_records])
    with vector_path.open("wb") as handle:
        pickle.dump({"vectorizer": vectorizer, "matrix": matrix, "chunks": chunk_records}, handle)
    manifest = {"schema_version": "medivale_graph_v1", "documents": len(files), "chunks": len(chunk_records), "graph_node_mentions": graph_nodes, "graph_edges": graph_edges, "graph_errors": graph_errors, "graph_error_details": graph_error_details[:50], "provider": getattr(provider, "name", None), "model": getattr(provider, "model", None)}
    (collection_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    conn.close()
    return manifest
