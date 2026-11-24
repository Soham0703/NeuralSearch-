import pytest
import numpy as np
from backend.app.rag.vector_store import NeuralVectorStore
from backend.app.rag.keyword_search import BM25SearchEngine
from backend.app.rag.hybrid_retriever import HybridRetriever

def test_vector_store_lifecycle(tmp_path):
    vs = NeuralVectorStore(index_name="test_index")
    vs.index_dir = tmp_path
    vs.vectors_file = tmp_path / "test_index.npz"
    vs.metadata_file = tmp_path / "test_index_meta.json"
    vs.clear()

    # Add 3 chunks
    chunk_ids = ["c1", "c2", "c3"]
    # 3-dim vectors: c1 and c2 are close, c3 is orthogonal
    vecs = np.array([
        [1.0, 0.0, 0.0],
        [0.9, 0.1, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float32)

    meta = [
        {"chunk_id": "c1", "document_id": "docA", "text": "Transformer architecture", "page_number": 1},
        {"chunk_id": "c2", "document_id": "docA", "text": "Self-attention layers", "page_number": 2},
        {"chunk_id": "c3", "document_id": "docB", "text": "Convolutional networks", "page_number": 1}
    ]

    vs.add_chunks(chunk_ids, vecs, meta)
    assert len(vs.chunk_ids) == 3

    # Search with query vector pointing along x-axis
    q = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    results = vs.search(q, top_k=2)

    assert len(results) == 2
    assert results[0][0] == "c1"  # Highest cosine similarity

    # Filter by document_id
    filtered = vs.search(q, top_k=5, document_ids=["docB"])
    assert len(filtered) == 1
    assert filtered[0][0] == "c3"

    # Delete docA
    deleted = vs.delete_document("docA")
    assert deleted == 2
    assert len(vs.chunk_ids) == 1

def test_bm25_lifecycle(tmp_path):
    bm25 = BM25SearchEngine(index_name="test_bm25")
    bm25.index_dir = tmp_path
    bm25.corpus_file = tmp_path / "test_bm25.json"
    bm25.clear()

    chunk_ids = ["b1", "b2"]
    texts = [
        "Self-attention mechanism has O(n^2) computational complexity",
        "Convolutional layers have local receptive fields"
    ]
    meta = [
        {"chunk_id": "b1", "document_id": "d1", "text": texts[0]},
        {"chunk_id": "b2", "document_id": "d2", "text": texts[1]}
    ]

    bm25.add_chunks(chunk_ids, texts, meta)
    res = bm25.search("computational complexity", top_k=2)
    assert len(res) > 0
    assert res[0][0] == "b1"
