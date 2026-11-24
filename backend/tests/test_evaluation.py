import pytest
from backend.app.schemas.eval import BenchmarkQuery
from backend.app.schemas.rag import RetrievedPassage
from backend.app.evaluation.retrieval_metrics import retrieval_evaluator
from backend.app.evaluation.rag_metrics import rag_metrics_evaluator

def test_retrieval_metrics():
    query = BenchmarkQuery(
        id="test_q",
        query="Explain self-attention complexity",
        expected_answer="Self-attention has O(n^2 * d) complexity.",
        relevant_doc_names=["attention.txt"],
        relevant_pages=[1],
        ground_truth_passages=["Self-attention layers have O(n^2 * d) complexity."]
    )

    # Candidate 1: Hit at rank 1
    passages_hit = [
        RetrievedPassage(
            id="p1", document_id="d1", document_name="attention.txt",
            page_number=1, chunk_index=0, text="Self-attention layers connect all positions with O(n^2 * d) complexity.",
            final_score=0.9
        ),
        RetrievedPassage(
            id="p2", document_id="d2", document_name="other.txt",
            page_number=1, chunk_index=1, text="Unrelated text.",
            final_score=0.5
        )
    ]

    r1 = retrieval_evaluator.compute_recall_at_k(passages_hit, query, k=1)
    r3 = retrieval_evaluator.compute_recall_at_k(passages_hit, query, k=3)
    mrr = retrieval_evaluator.compute_reciprocal_rank(passages_hit, query)
    ndcg = retrieval_evaluator.compute_ndcg_at_k(passages_hit, query, k=3)

    assert r1 == 1.0
    assert r3 == 1.0
    assert mrr == 1.0
    assert ndcg == 1.0

    # Candidate 2: Miss
    passages_miss = [
        RetrievedPassage(
            id="p3", document_id="d3", document_name="irrelevant.txt",
            page_number=5, chunk_index=0, text="Some completely different topic.",
            final_score=0.2
        )
    ]
    assert retrieval_evaluator.compute_recall_at_k(passages_miss, query, k=1) == 0.0
    assert retrieval_evaluator.compute_reciprocal_rank(passages_miss, query) == 0.0

def test_rag_faithfulness():
    passages = [
        RetrievedPassage(
            id="p1", document_id="d1", document_name="doc.txt",
            page_number=1, chunk_index=0, text="The model was trained on 8 P100 GPUs for twelve hours.",
            final_score=0.8
        )
    ]

    # Faithful answer
    faithful_answer = "The model was trained on 8 P100 GPUs for twelve hours. [doc.txt, p.1]"
    faith_score = rag_metrics_evaluator.evaluate_faithfulness(faithful_answer, passages)
    assert faith_score >= 0.7

    # Unavailable info refusal is 100% faithful
    refusal = "I do not have sufficient information in the provided documents."
    assert rag_metrics_evaluator.evaluate_faithfulness(refusal, passages) == 1.0
