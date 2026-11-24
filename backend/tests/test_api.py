import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "NeuralSearch" in data["service"]

def test_get_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "embedding_model" in data
    assert "retrieval_modes" in data
    assert len(data["retrieval_modes"]) >= 4

def test_load_sample_documents_and_list():
    # Load samples
    res = client.post("/api/documents/load-samples")
    assert res.status_code == 200

    # List documents
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    assert len(docs) >= 1

def test_rag_query_with_citations():
    query_payload = {
        "query": "What is the computational complexity of self-attention in Transformers?",
        "search_mode": "hybrid_rerank",
        "llm_provider": "mock"
    }
    response = client.post("/api/rag/chat", json=query_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == query_payload["query"]
    assert len(data["answer"]) > 0
    assert len(data["citations"]) > 0
    assert len(data["retrieved_passages"]) > 0
    assert data["grounded"] is True
    # Citation must contain document name and page number
    first_citation = data["citations"][0]
    assert first_citation["document_name"] != ""
    assert first_citation["page_number"] > 0

def test_rag_hallucination_guardrail():
    # Query completely outside indexed domain
    query_payload = {
        "query": "What is the recipe for baking chocolate chip cookies in an Italian woodfire pizza oven?",
        "search_mode": "hybrid_rerank",
        "llm_provider": "mock"
    }
    response = client.post("/api/rag/chat", json=query_payload)
    assert response.status_code == 200
    data = response.json()
    # Guardrail must trigger
    assert data["unavailable_info"] is True
    assert "sufficient information" in data["answer"].lower() or "unavailable" in data["answer"].lower()

def test_evaluation_dataset_endpoint():
    response = client.get("/api/eval/dataset")
    assert response.status_code == 200
    dataset = response.json()
    assert len(dataset) >= 5

def test_benchmark_runner_endpoint():
    config_payload = {
        "chunk_strategies": ["recursive"],
        "retrieval_modes": ["hybrid_rerank"]
    }
    response = client.post("/api/eval/benchmark", json=config_payload)
    assert response.status_code == 200
    report = response.json()
    assert len(report["runs"]) >= 1
    run = report["runs"][0]
    assert run["recall_at_1"] >= 0.0
    assert run["mrr"] >= 0.0
    assert run["faithfulness"] >= 0.0
