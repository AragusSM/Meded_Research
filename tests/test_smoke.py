from __future__ import annotations

import tempfile
import os
from io import BytesIO
from pathlib import Path

import pymupdf

from medrag.api import create_app
from medrag.config import Settings
from medrag.database import connect
from medrag.providers import ProviderError, provider_from_config


def test_vector_index_and_mock_answer():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        docs = root / "docs"
        docs.mkdir()
        (docs / "heme.txt").write_text(
            "Iron deficiency anemia commonly causes microcytosis. Ferritin is usually low.",
            encoding="utf-8",
        )
        settings = Settings(root / "data", "mock", docs, "127.0.0.1", 8090)
        app = create_app(settings)
        client = app.test_client()

        verified = client.post("/v1/providers/verify", json={"provider": "mock"})
        assert verified.status_code == 200
        assert verified.get_json()["status"] == "online"

        indexed = client.post("/v1/collections/test/index", json={"directory": str(docs), "build_graph": False})
        assert indexed.status_code == 200
        assert indexed.get_json()["chunks"] == 1

        answered = client.post("/v1/collections/test/answer", json={"query": "What happens to ferritin?", "mode": "vector", "provider": "mock"})
        assert answered.status_code == 200
        assert answered.get_json()["answer"] == "Deterministic mock answer."

        generated = client.post("/v1/collections/test/questions", json={"topic": "iron deficiency", "mode": "vector", "provider": "mock"})
        assert generated.status_code == 200
        question = generated.get_json()["question"]
        assert len(question["choices"]) == 5
        assert question["correct_choice_id"] == "A"
        assert all(choice["explanation"] for choice in question["choices"])

        homepage = client.get("/")
        assert homepage.status_code == 200
        assert b"MedVale RAG Builder" in homepage.data
        assert b"API offline" in homepage.data
        assert b"medivale_icon.ico" in homepage.data
        assert b"3d-force-graph.min.js" not in homepage.data

        history = client.get("/v1/collections/test/runs")
        assert history.status_code == 200
        assert len(history.get_json()["runs"]) == 2

        graph = client.get("/v1/collections/test/graph")
        assert graph.status_code == 200
        assert graph.get_json() == {"edges": [], "nodes": []}

        viewer = client.get("/v1/collections/test/graph-viewer")
        assert viewer.status_code == 200
        assert b"vendor/medivale_graph/assets/viewer.js" in viewer.data

        visualization = client.get("/v1/collections/test/visualization")
        assert visualization.status_code == 200
        payload = visualization.get_json()
        assert len(payload["vectors"]) == 1
        assert payload["vectors"][0]["x"] == 0.5
        assert payload["vectors"][0]["text"].startswith("Iron deficiency")


def test_browser_upload_builds_collection_without_storing_key():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        settings = Settings(root / "data", "mock", None, "127.0.0.1", 8090)
        client = create_app(settings).test_client()
        response = client.post(
            "/v1/collections/upload-test/upload-index",
            data={
                "provider": "mock",
                "model": "deterministic-mock",
                "api_key": "must-not-be-stored",
                "build_graph": "false",
                "files": (BytesIO(b"Ferritin is low in iron deficiency anemia."), "notes.txt"),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert response.get_json()["documents"] == 1
        assert (root / "data" / "upload-test" / "documents" / "notes.txt").exists()
        visual = client.get("/v1/collections/upload-test/visualization").get_json()
        document_id = visual["chunks"][0]["document_id"]
        source = client.get(f"/v1/collections/upload-test/documents/{document_id}")
        assert source.status_code == 200
        assert source.data == b"Ferritin is low in iron deficiency anemia."
        source.close()
        for path in (root / "data" / "upload-test").rglob("*"):
            if path.is_file():
                assert b"must-not-be-stored" not in path.read_bytes()


def test_browser_provider_never_falls_back_to_server_key():
    previous = os.environ.get("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = "server-key-must-not-be-used"
    try:
        try:
            provider_from_config(name="groq", api_key="", model="openai/gpt-oss-120b")
            raise AssertionError("browser provider unexpectedly accepted a server key")
        except ProviderError as exc:
            assert "key is required" in str(exc)
    finally:
        if previous is None:
            os.environ.pop("GROQ_API_KEY", None)
        else:
            os.environ["GROQ_API_KEY"] = previous


def test_pdf_page_graph_filters_and_concept_sources():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        settings = Settings(root / "data", "mock", None, "127.0.0.1", 8090)
        client = create_app(settings).test_client()
        pdf = pymupdf.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "Ferritin is low in iron deficiency anemia.")
        pdf_bytes = pdf.tobytes()
        pdf.close()
        built = client.post(
            "/v1/collections/pdf-test/upload-index",
            data={"provider": "mock", "build_graph": "false", "files": (BytesIO(pdf_bytes), "hematology.pdf")},
            content_type="multipart/form-data",
        )
        assert built.status_code == 200
        visual = client.get("/v1/collections/pdf-test/visualization").get_json()
        chunk = visual["chunks"][0]
        conn = connect(root / "data" / "pdf-test" / "knowledge.sqlite3")
        conn.execute("INSERT INTO concepts(concept_id,canonical_name,entity_type,description,confidence) VALUES(?,?,?,?,?)", ("iron_deficiency_anemia", "Iron deficiency anemia", "disease", "A microcytic anemia", .95))
        conn.execute("INSERT INTO concepts(concept_id,canonical_name,entity_type,description,confidence) VALUES(?,?,?,?,?)", ("low_ferritin", "Low ferritin", "finding", "Reduced ferritin", .9))
        conn.execute("INSERT INTO mentions(concept_id,chunk_id,evidence) VALUES(?,?,?)", ("iron_deficiency_anemia", chunk["chunk_id"], "iron deficiency anemia"))
        conn.execute("INSERT INTO edges(edge_id,source_id,target_id,relation,confidence,chunk_id,evidence) VALUES(?,?,?,?,?,?,?)", ("edge-1", "iron_deficiency_anemia", "low_ferritin", "INDICATES", .9, chunk["chunk_id"], "Ferritin is low"))
        conn.commit()
        conn.close()

        preview = client.get(f"/v1/collections/pdf-test/documents/{chunk['document_id']}/pages/1")
        assert preview.status_code == 200
        assert preview.mimetype == "image/png"
        assert preview.data.startswith(b"\x89PNG")
        sources = client.get("/v1/collections/pdf-test/concepts/iron_deficiency_anemia/sources").get_json()
        assert sources["concept"]["canonical_name"] == "Iron deficiency anemia"
        assert sources["sources"][0]["document_id"] == chunk["document_id"]
        filtered = client.get("/v1/collections/pdf-test/graph?q=iron&max_nodes=10&max_edges=10").get_json()
        assert {node["concept_id"] for node in filtered["nodes"]} == {"iron_deficiency_anemia", "low_ferritin"}
        assert filtered["edges"][0]["relation"] == "INDICATES"
        options = client.get("/v1/collections/pdf-test/graph/options").get_json()
        assert "disease" in options["entity_types"]
        assert "INDICATES" in options["relations"]
