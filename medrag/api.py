from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

try:
    from dotenv import load_dotenv
except ImportError:  # Optional convenience; environment variables still work.
    def load_dotenv() -> bool:
        return False

from .config import Settings
from .database import connect
from .indexing import index_directory
from .import_medivale import import_medivale
from .providers import ProviderError, provider_from_config, provider_from_env
from .visualization import collection_visualization
from .service import answer, generate_question


load_dotenv()


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    project_root = Path(__file__).resolve().parents[1]
    bundled_root = project_root / "bundled_data"
    default_data_root = (project_root / "data").resolve()
    if settings.data_dir.resolve() == default_data_root and not (settings.data_dir / "medivale-im" / "manifest.json").exists():
        source_db = bundled_root / "internal_medicine_source.db"
        source_documents = bundled_root / "documents"
        if source_db.exists() and source_documents.is_dir():
            import_medivale(source_db, source_documents, settings.data_dir)
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

    def request_provider(body):
        return provider_from_config(
            name=body.get("provider"), api_key=body.get("api_key"),
            model=body.get("model"), base_url=body.get("base_url"),
        )

    def ensure_writable_collection(collection: Path) -> None:
        manifest_path = collection / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("read_only") or manifest.get("bundled"):
                raise ValueError("Built-in MedVale collections are read-only; choose a different collection name")

    @app.errorhandler(ValueError)
    @app.errorhandler(ProviderError)
    def bad_request(exc):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(FileNotFoundError)
    def not_found(exc):
        return jsonify({"error": str(exc)}), 404

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "version": "0.1.0", "default_provider": settings.provider})

    @app.post("/v1/providers/verify")
    def verify_provider():
        body = request.get_json(force=True) or {}
        provider = request_provider(body)
        response = provider.generate(
            "Reply with only MEDVALE_OK.",
            "This is a connection check. Do not add an explanation.",
            0.0,
        )
        if not response.strip():
            raise ProviderError("provider returned an empty verification response")
        return jsonify({"status": "online", "provider": provider.name, "model": provider.model})

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/v1/collections")
    def collections():
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        items = []
        for path in sorted(p for p in settings.data_dir.iterdir() if p.is_dir()):
            manifest_path = path / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
            items.append({"collection_id": path.name, "manifest": manifest})
        return jsonify({"collections": items})

    @app.post("/v1/collections/<collection_id>/index")
    def index_collection(collection_id: str):
        body = request.get_json(force=True) or {}
        collection = settings.collection_dir(collection_id)
        ensure_writable_collection(collection)
        document_dir = settings.validate_document_directory(str(body.get("directory", "")))
        build_graph = bool(body.get("build_graph", True))
        provider = provider_from_env(body.get("provider")) if build_graph else None
        result = index_directory(collection, document_dir, provider, build_graph)
        return jsonify({"collection_id": collection_id, **result})

    @app.post("/v1/collections/<collection_id>/upload-index")
    def upload_and_index(collection_id: str):
        collection = settings.collection_dir(collection_id)
        ensure_writable_collection(collection)
        uploaded = request.files.getlist("files")
        if not uploaded or all(not item.filename for item in uploaded):
            raise ValueError("Select at least one PDF, DOCX, TXT, or Markdown file")
        document_dir = collection / "documents"
        document_dir.mkdir(parents=True, exist_ok=True)
        allowed = {".pdf", ".docx", ".txt", ".md"}
        saved = []
        for item in uploaded:
            filename = secure_filename(item.filename or "")
            if not filename:
                continue
            if Path(filename).suffix.lower() not in allowed:
                raise ValueError(f"unsupported file type: {filename}")
            item.save(document_dir / filename)
            saved.append(filename)
        if not saved:
            raise ValueError("No supported documents were uploaded")
        build_graph = request.form.get("build_graph", "true").lower() == "true"
        provider = request_provider(request.form) if build_graph else None
        result = index_directory(collection, document_dir, provider, build_graph)
        return jsonify({"collection_id": collection_id, "uploaded": saved, **result})

    @app.post("/v1/collections/<collection_id>/answer")
    def answer_route(collection_id: str):
        body = request.get_json(force=True) or {}
        query = str(body.get("query", "")).strip()
        if not query:
            raise ValueError("query is required")
        provider = request_provider(body)
        return jsonify(answer(settings.collection_dir(collection_id), provider, query, str(body.get("mode", "hybrid")), int(body.get("k", 8)), bool(body.get("allow_background", True))))

    @app.post("/v1/collections/<collection_id>/questions")
    def question_route(collection_id: str):
        body = request.get_json(force=True) or {}
        topic = str(body.get("topic", "")).strip()
        if not topic:
            raise ValueError("topic is required")
        provider = request_provider(body)
        return jsonify(generate_question(settings.collection_dir(collection_id), provider, topic, str(body.get("mode", "hybrid")), str(body.get("format", "basic")), int(body.get("k", 8))))

    @app.get("/v1/collections/<collection_id>/stats")
    def stats(collection_id: str):
        collection = settings.collection_dir(collection_id)
        conn = connect(collection / "knowledge.sqlite3")
        counts = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("documents", "chunks", "concepts", "edges", "runs")}
        conn.close()
        manifest_path = collection / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
        return jsonify({"collection_id": collection_id, "counts": counts, "manifest": manifest})

    @app.get("/v1/collections/<collection_id>/runs")
    def runs(collection_id: str):
        collection = settings.collection_dir(collection_id)
        conn = connect(collection / "knowledge.sqlite3")
        limit = min(200, max(1, int(request.args.get("limit", 30))))
        rows = conn.execute(
            "SELECT run_id,task,mode,provider,model,request_json,evidence_json,response_text,created_at "
            "FROM runs ORDER BY run_id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return jsonify({"runs": [{
            "run_id": row["run_id"], "task": row["task"], "mode": row["mode"],
            "provider": row["provider"], "model": row["model"],
            "request": json.loads(row["request_json"]),
            "evidence": json.loads(row["evidence_json"]),
            "response": row["response_text"], "created_at": row["created_at"],
        } for row in rows]})

    def graph_payload(
        collection_id: str, max_nodes: int, max_edges: int,
        query: str = "", entity_type: str = "", relation: str = "", hops: int = 1,
    ) -> dict:
        collection = settings.collection_dir(collection_id)
        conn = connect(collection / "knowledge.sqlite3")
        node_where, node_args = [], []
        if entity_type:
            node_where.append("entity_type = ?")
            node_args.append(entity_type)
        if query:
            node_where.append("(lower(canonical_name) LIKE ? OR lower(description) LIKE ?)")
            needle = f"%{query.lower()}%"
            node_args.extend((needle, needle))
        where_sql = f"WHERE {' AND '.join(node_where)}" if node_where else ""
        seed_limit = min(max_nodes, 50) if query else max_nodes
        seeds = conn.execute(
            "SELECT concept_id,canonical_name,entity_type,description,confidence,status FROM concepts "
            f"{where_sql} ORDER BY confidence DESC, canonical_name LIMIT ?",
            (*node_args, seed_limit),
        ).fetchall()
        seed_ids = [row["concept_id"] for row in seeds]
        edge_rows = []
        if seed_ids:
            allowed_ids = set(seed_ids)
            edge_ids, frontier = set(), set(seed_ids)
            for _ in range(hops if query else 1):
                placeholders = ",".join("?" for _ in frontier)
                edge_where = f"(source_id IN ({placeholders}) OR target_id IN ({placeholders}))" if query else f"source_id IN ({placeholders}) AND target_id IN ({placeholders})"
                edge_args = [*frontier, *frontier]
                if relation:
                    edge_where += " AND relation = ?"
                    edge_args.append(relation)
                candidates = conn.execute(
                    "SELECT edge_id,source_id,target_id,relation,description,confidence,status,evidence FROM edges "
                    f"WHERE {edge_where} ORDER BY confidence DESC LIMIT ?", (*edge_args, max_edges * 3),
                ).fetchall()
                next_frontier = set()
                for edge in candidates:
                    if edge["edge_id"] in edge_ids:
                        continue
                    additions = {edge["source_id"], edge["target_id"]} - allowed_ids
                    if len(allowed_ids) + len(additions) > max_nodes:
                        continue
                    allowed_ids.update(additions)
                    next_frontier.update(additions)
                    edge_ids.add(edge["edge_id"])
                    edge_rows.append(edge)
                    if len(edge_rows) >= max_edges:
                        break
                frontier = next_frontier
                if not frontier or len(edge_rows) >= max_edges:
                    break
            if allowed_ids != set(seed_ids):
                placeholders = ",".join("?" for _ in allowed_ids)
                nodes = conn.execute(
                    "SELECT concept_id,canonical_name,entity_type,description,confidence,status FROM concepts "
                    f"WHERE concept_id IN ({placeholders}) ORDER BY confidence DESC, canonical_name",
                    tuple(allowed_ids),
                ).fetchall()
            else:
                nodes = seeds
        else:
            nodes = []
        conn.close()
        return {
            "nodes": [dict(row) for row in nodes],
            "edges": [dict(row) for row in edge_rows],
        }

    def graph_request_options() -> tuple[int, int, str, str, str, int]:
        max_nodes = min(500, max(10, int(request.args.get("max_nodes", request.args.get("limit", 160)))))
        max_edges = min(1500, max(10, int(request.args.get("max_edges", max_nodes * 3))))
        hops = min(3, max(1, int(request.args.get("hops", 1))))
        return max_nodes, max_edges, request.args.get("q", "").strip(), request.args.get("entity_type", "").strip(), request.args.get("relation", "").strip(), hops

    @app.get("/v1/collections/<collection_id>/graph")
    def graph(collection_id: str):
        return jsonify(graph_payload(collection_id, *graph_request_options()))

    @app.get("/v1/collections/<collection_id>/graph/options")
    def graph_options(collection_id: str):
        conn = connect(settings.collection_dir(collection_id) / "knowledge.sqlite3")
        entity_types = [row[0] for row in conn.execute("SELECT DISTINCT entity_type FROM concepts WHERE entity_type != '' ORDER BY entity_type")]
        relations = [row[0] for row in conn.execute("SELECT DISTINCT relation FROM edges WHERE relation != '' ORDER BY relation")]
        counts = {
            "nodes": conn.execute("SELECT COUNT(*) FROM concepts").fetchone()[0],
            "edges": conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0],
        }
        conn.close()
        return jsonify({"entity_types": entity_types, "relations": relations, "counts": counts})

    @app.get("/v1/collections/<collection_id>/graph-viewer")
    def graph_viewer(collection_id: str):
        payload = graph_payload(collection_id, *graph_request_options())
        viewer_data = {
            "nodes": [{
                "id": node["concept_id"], "name": node["canonical_name"],
                "entity_type": node["entity_type"], "description": node["description"],
                "confidence": node["confidence"], "status": node["status"],
            } for node in payload["nodes"]],
            "links": [{
                "id": edge["edge_id"], "source": edge["source_id"], "target": edge["target_id"],
                "edge_type": edge["relation"].lower(), "description": edge["description"],
                "confidence": edge["confidence"], "status": edge["status"],
            } for edge in payload["edges"]],
            "meta": {"mode": "neighborhood" if request.args.get("q") else "overview", "collection_id": collection_id, "hops": min(3, max(1, int(request.args.get("hops", 1))))},
        }
        return render_template("graph_viewer.html", graph_data=viewer_data)

    @app.get("/v1/collections/<collection_id>/visualization")
    def visualization(collection_id: str):
        limit = min(500, max(1, int(request.args.get("limit", 300))))
        return jsonify(collection_visualization(settings.collection_dir(collection_id), limit))

    def resolve_source_document(collection_id: str, document_id: str):
        collection = settings.collection_dir(collection_id)
        conn = connect(collection / "knowledge.sqlite3")
        row = conn.execute("SELECT path,title FROM documents WHERE document_id = ?", (document_id,)).fetchone()
        conn.close()
        if row is None:
            raise FileNotFoundError("source document not found")
        source = Path(row["path"]).resolve()
        document_root = (collection / "documents").resolve()
        if not source.is_file() or not source.is_relative_to(document_root):
            raise FileNotFoundError("source document is unavailable")
        return source, row["title"]

    @app.get("/v1/collections/<collection_id>/documents/<document_id>")
    def source_document(collection_id: str, document_id: str):
        source, title = resolve_source_document(collection_id, document_id)
        return send_file(source, download_name=title, as_attachment=False, conditional=True)

    @app.get("/v1/collections/<collection_id>/documents/<document_id>/pages/<int:page_number>")
    def source_document_page(collection_id: str, document_id: str, page_number: int):
        source, _ = resolve_source_document(collection_id, document_id)
        if source.suffix.lower() != ".pdf":
            raise ValueError("page preview is only available for PDF documents")
        try:
            import pymupdf
        except ImportError as exc:
            raise ValueError("PDF page rendering requires PyMuPDF") from exc
        with pymupdf.open(source) as pdf:
            if page_number < 1 or page_number > pdf.page_count:
                raise FileNotFoundError("PDF page not found")
            pixmap = pdf.load_page(page_number - 1).get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6), alpha=False)
            image = BytesIO(pixmap.tobytes("png"))
        return send_file(image, mimetype="image/png", download_name=f"page-{page_number}.png", max_age=3600)

    @app.get("/v1/collections/<collection_id>/concepts/<concept_id>/sources")
    def concept_sources(collection_id: str, concept_id: str):
        collection = settings.collection_dir(collection_id)
        conn = connect(collection / "knowledge.sqlite3")
        concept = conn.execute(
            "SELECT concept_id,canonical_name,entity_type,description,confidence,status FROM concepts WHERE concept_id = ?",
            (concept_id,),
        ).fetchone()
        if concept is None:
            conn.close()
            raise FileNotFoundError("concept not found")
        rows = conn.execute(
            "SELECT DISTINCT d.document_id,d.title,d.path,c.chunk_id,c.chunk_index,c.locator,c.text,m.evidence "
            "FROM mentions m JOIN chunks c ON c.chunk_id=m.chunk_id JOIN documents d ON d.document_id=c.document_id "
            "WHERE m.concept_id=? ORDER BY d.title,c.chunk_index LIMIT 100", (concept_id,),
        ).fetchall()
        conn.close()
        return jsonify({"concept": dict(concept), "sources": [{
            "document_id": row["document_id"], "title": row["title"],
            "chunk_id": row["chunk_id"], "chunk_index": row["chunk_index"],
            "locator": row["locator"], "text": row["text"], "evidence": row["evidence"],
            "source_type": Path(row["path"]).suffix.lower().lstrip("."),
        } for row in rows]})

    return app


def main() -> None:
    settings = Settings.from_env()
    create_app(settings).run(host=settings.host, port=settings.port, debug=False)


if __name__ == "__main__":
    main()
