from typing import List, Dict, Any
from backend.app.schemas.eval import BenchmarkQuery

BENCHMARK_DATASET: List[BenchmarkQuery] = [
    BenchmarkQuery(
        id="q1",
        query="What is the computational complexity of the self-attention mechanism compared to recurrent layers?",
        expected_answer="Self-attention layers connect all positions with a constant number of sequentially executed operations O(1) and have O(n^2 * d) per-layer complexity, whereas recurrent layers require O(n) sequential operations with O(n * d^2) per-layer complexity.",
        relevant_doc_names=["attention_is_all_you_need.txt", "transformers_overview.txt"],
        relevant_pages=[1, 2],
        ground_truth_passages=[
            "Self-attention layers connect all positions with a constant number of sequentially executed operations, whereas recurrent layers require O(n) sequential operations.",
            "Per-layer complexity for self-attention is O(n^2 * d) while recurrent is O(n * d^2)."
        ]
    ),
    BenchmarkQuery(
        id="q2",
        query="How does hybrid search combine dense vector embeddings and sparse BM25 keyword retrieval?",
        expected_answer="Hybrid search combines dense retrieval (which captures semantic meaning and synonyms) with BM25 (which captures exact keyword and lexical matches) using Reciprocal Rank Fusion (RRF) or convex linear score combination.",
        relevant_doc_names=["rag_survey_2024.txt", "hybrid_search_techniques.txt"],
        relevant_pages=[1, 2],
        ground_truth_passages=[
            "Hybrid search leverages dense retrieval for semantic similarity and BM25 for precise keyword matching.",
            "Reciprocal Rank Fusion fuses ranked lists by computing RRF score = sum(1 / (k + rank))."
        ]
    ),
    BenchmarkQuery(
        id="q3",
        query="What role does the Cross-Encoder reranker play in a two-stage RAG pipeline?",
        expected_answer="A Cross-Encoder performs joint self-attention across both the query and candidate passage simultaneously, capturing fine-grained token-level interactions to re-rank initial top candidates with higher precision than bi-encoder embeddings.",
        relevant_doc_names=["rag_survey_2024.txt", "reranking_in_rag.txt"],
        relevant_pages=[2, 3],
        ground_truth_passages=[
            "Cross-Encoders allow full cross-attention between query and passage tokens, yielding superior ranking precision.",
            "Two-stage retrieval uses bi-encoders for high-recall candidate generation and cross-encoders for precision reranking."
        ]
    ),
    BenchmarkQuery(
        id="q4",
        query="How does page-level chunking prevent cross-page citation errors in enterprise RAG systems?",
        expected_answer="Page-level chunking respects physical page boundaries during segmentation, ensuring that every chunk and citation maps unambiguously to an exact source page without bleeding across adjacent unrelated pages.",
        relevant_doc_names=["document_chunking_strategies.txt"],
        relevant_pages=[1, 2],
        ground_truth_passages=[
            "Page-level chunking preserves strict page boundaries, preventing chunks from spanning across multiple pages and ensuring 100% accurate page-level citations.",
            "Boundaries prevent attribution confusion between consecutive sections."
        ]
    ),
    BenchmarkQuery(
        id="q5",
        query="What are the primary metrics used to evaluate RAG answer faithfulness and hallucination rates?",
        expected_answer="Faithfulness measures the proportion of claims in the generated answer that can be directly inferred from the retrieved context, while Answer Relevance measures how well the response addresses the user query.",
        relevant_doc_names=["rag_evaluation_benchmarks.txt"],
        relevant_pages=[1, 3],
        ground_truth_passages=[
            "Faithfulness evaluates whether every factual claim in the generated answer is grounded in the retrieved context passages.",
            "Answer relevance computes the alignment between the generated response and the initial user question."
        ]
    ),
    BenchmarkQuery(
        id="q6",
        query="Why do Bi-Encoders and Cross-Encoders differ in computational throughput during retrieval?",
        expected_answer="Bi-Encoders encode queries and documents independently allowing pre-computed offline document embeddings and fast MIPS vector search, whereas Cross-Encoders require quadratic joint inference for every (query, doc) pair making them slower but more accurate.",
        relevant_doc_names=["reranking_in_rag.txt", "transformers_overview.txt"],
        relevant_pages=[2],
        ground_truth_passages=[
            "Bi-encoders allow pre-computing document representations offline for millisecond vector lookups.",
            "Cross-encoders process query and document concatenated together, making real-time computation over millions of documents computationally prohibitive."
        ]
    ),
    BenchmarkQuery(
        id="q7",
        query="What is Reciprocal Rank Fusion (RRF) and why is it parameter-free?",
        expected_answer="Reciprocal Rank Fusion (RRF) is a rank aggregation algorithm that scores candidates purely based on their reciprocal position 1/(k + rank) across multiple rankers without requiring score calibration or normalization across disparate scales.",
        relevant_doc_names=["hybrid_search_techniques.txt"],
        relevant_pages=[1],
        ground_truth_passages=[
            "RRF is an empirical rank aggregation method that does not require score normalization across different retrieval models.",
            "The formula 1/(k + rank) robustly merges disparate ranking distributions."
        ]
    ),
    BenchmarkQuery(
        id="q8",
        query="What strategies mitigate hallucinations when retrieved context is irrelevant or missing?",
        expected_answer="Hallucination mitigation strategies include setting similarity score thresholds, instruction-tuning the LLM to explicitly report unavailable information, and verifying claim-level entailment against retrieved passages before returning the response.",
        relevant_doc_names=["rag_evaluation_benchmarks.txt"],
        relevant_pages=[2],
        ground_truth_passages=[
            "Strict similarity cutoff thresholds prevent the generator from conditioning on noise.",
            "Prompt guardrails force the model to state information is unavailable when confidence is low."
        ]
    )
]

def get_benchmark_dataset() -> List[BenchmarkQuery]:
    return BENCHMARK_DATASET
