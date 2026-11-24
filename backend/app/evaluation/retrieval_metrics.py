import math
from typing import List, Dict, Any, Set
from backend.app.schemas.eval import BenchmarkQuery
from backend.app.schemas.rag import RetrievedPassage

class RetrievalEvaluator:
    """
    Computes rigorous Information Retrieval metrics:
    - Recall@K
    - MRR (Mean Reciprocal Rank)
    - NDCG@K (Normalized Discounted Cumulative Gain)
    """
    @staticmethod
    def is_hit(passage: RetrievedPassage, query: BenchmarkQuery) -> bool:
        """Determines if a retrieved passage matches ground truth targets."""
        # 1. Match document name
        doc_match = any(
            t.lower() in passage.document_name.lower() or passage.document_name.lower() in t.lower()
            for t in query.relevant_doc_names
        )
        if not doc_match:
            return False

        # 2. Check page match if available
        if query.relevant_pages and passage.page_number in query.relevant_pages:
            return True

        # 3. Check text semantic overlap with ground truth passages
        passage_text_lower = passage.text.lower()
        for gt in query.ground_truth_passages:
            gt_words = [w for w in gt.lower().split() if len(w) > 4]
            if gt_words:
                matches = sum(1 for w in gt_words if w in passage_text_lower)
                if matches / len(gt_words) >= 0.4:
                    return True

        return doc_match

    def compute_recall_at_k(
        self,
        retrieved_passages: List[RetrievedPassage],
        query: BenchmarkQuery,
        k: int
    ) -> float:
        """Recall@K: 1.0 if any relevant passage appears in top K, else 0.0."""
        top_k = retrieved_passages[:k]
        for p in top_k:
            if self.is_hit(p, query):
                return 1.0
        return 0.0

    def compute_reciprocal_rank(
        self,
        retrieved_passages: List[RetrievedPassage],
        query: BenchmarkQuery
    ) -> float:
        """MRR contribution: 1 / rank of first relevant passage."""
        for rank, p in enumerate(retrieved_passages):
            if self.is_hit(p, query):
                return 1.0 / (rank + 1)
        return 0.0

    def compute_ndcg_at_k(
        self,
        retrieved_passages: List[RetrievedPassage],
        query: BenchmarkQuery,
        k: int
    ) -> float:
        """NDCG@K calculation."""
        top_k = retrieved_passages[:k]
        dcg = 0.0
        for i, p in enumerate(top_k):
            rel = 1.0 if self.is_hit(p, query) else 0.0
            dcg += (2.0 ** rel - 1.0) / math.log2(i + 2)

        # Ideal DCG (at least 1 relevant item at rank 1)
        idcg = (2.0 ** 1.0 - 1.0) / math.log2(1 + 1)
        return dcg / idcg if idcg > 0 else 0.0

retrieval_evaluator = RetrievalEvaluator()
