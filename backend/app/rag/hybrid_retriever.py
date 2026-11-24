import logging
from typing import List, Optional, Dict, Any
from backend.app.config import settings
from backend.app.rag.embeddings import embedding_engine
from backend.app.rag.vector_store import vector_store
from backend.app.rag.keyword_search import bm25_engine
from backend.app.rag.reranker import reranker
from backend.app.schemas.rag import RetrievedPassage

logger = logging.getLogger("neuralsearch.hybrid_retriever")

class HybridRetriever:
    """
    Advanced Enterprise Hybrid Retrieval Engine:
    - Semantic Dense Vector Search via SentenceTransformers & NeuralVectorStore
    - Exact Keyword Lexical Search via BM25Okapi
    - Reciprocal Rank Fusion (RRF) & Convex Combination Score Blending
    - Cross-Encoder Neural Reranking Stage
    """
    def __init__(self, rrf_k: int = 60, alpha: float = None):
        self.rrf_k = rrf_k
        self.alpha = alpha if alpha is not None else settings.HYBRID_ALPHA

    def retrieve(
        self,
        query: str,
        mode: str = "hybrid_rerank",
        document_ids: Optional[List[str]] = None,
        top_k: int = 6,
        rerank_top_k: int = 4
    ) -> List[RetrievedPassage]:
        """
        Retrieves top passages using specified search mode:
        - 'semantic': Dense vector embeddings only
        - 'bm25': BM25 keyword search only
        - 'hybrid': Reciprocal Rank Fusion of Dense + BM25
        - 'hybrid_rerank': Hybrid RRF + Cross-Encoder Reranking
        """
        mode = (mode or "hybrid_rerank").lower()
        candidate_k = max(top_k * 2, 10) if mode == "hybrid_rerank" else top_k

        # 1. Semantic Dense Search
        dense_results = []
        if mode in ["semantic", "hybrid", "hybrid_rerank"]:
            query_vec = embedding_engine.encode(query)
            dense_results = vector_store.search(
                query_vector=query_vec,
                top_k=candidate_k,
                document_ids=document_ids
            )

        # 2. BM25 Keyword Search
        bm25_results = []
        if mode in ["bm25", "hybrid", "hybrid_rerank"]:
            bm25_results = bm25_engine.search(
                query=query,
                top_k=candidate_k,
                document_ids=document_ids
            )

        # 3. Mode dispatch
        if mode == "semantic":
            passages = [
                RetrievedPassage(
                    id=cid,
                    document_id=meta.get("document_id", ""),
                    document_name=meta.get("document_name", "Unknown Document"),
                    page_number=meta.get("page_number", 1),
                    chunk_index=meta.get("chunk_index", 0),
                    text=meta.get("text", ""),
                    dense_score=round(score, 4),
                    final_score=round(score, 4)
                )
                for cid, score, meta in dense_results[:top_k]
            ]
            return passages

        if mode == "bm25":
            passages = [
                RetrievedPassage(
                    id=cid,
                    document_id=meta.get("document_id", ""),
                    document_name=meta.get("document_name", "Unknown Document"),
                    page_number=meta.get("page_number", 1),
                    chunk_index=meta.get("chunk_index", 0),
                    text=meta.get("text", ""),
                    bm25_score=round(score, 4),
                    final_score=round(score, 4)
                )
                for cid, score, meta in bm25_results[:top_k]
            ]
            return passages

        # 4. Hybrid Fusion (RRF + Weighted blend)
        passages = self._reciprocal_rank_fusion(
            dense_results=dense_results,
            bm25_results=bm25_results,
            top_k=candidate_k if mode == "hybrid_rerank" else top_k
        )

        # 5. Reranking Stage
        if mode == "hybrid_rerank":
            passages = reranker.rerank(
                query=query,
                passages=passages,
                top_k=rerank_top_k
            )

        return passages

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Tuple[str, float, Dict[str, Any]]],
        bm25_results: List[Tuple[str, float, Dict[str, Any]]],
        top_k: int = 6
    ) -> List[RetrievedPassage]:
        """
        Combines ranked lists using Reciprocal Rank Fusion (RRF) and convex scoring:
        RRF_Score = 1/(k + rank_dense) + 1/(k + rank_bm25)
        """
        scores_map: Dict[str, Dict[str, Any]] = {}

        # Process Dense results
        for rank, (cid, score, meta) in enumerate(dense_results):
            rrf_val = 1.0 / (self.rrf_k + rank + 1)
            scores_map[cid] = {
                "id": cid,
                "meta": meta,
                "dense_score": score,
                "bm25_score": 0.0,
                "rrf_score": rrf_val
            }

        # Process BM25 results
        for rank, (cid, score, meta) in enumerate(bm25_results):
            rrf_val = 1.0 / (self.rrf_k + rank + 1)
            if cid in scores_map:
                scores_map[cid]["bm25_score"] = score
                scores_map[cid]["rrf_score"] += rrf_val
            else:
                scores_map[cid] = {
                    "id": cid,
                    "meta": meta,
                    "dense_score": 0.0,
                    "bm25_score": score,
                    "rrf_score": rrf_val
                }

        # Calculate hybrid score (normalized convex blend + RRF)
        candidates = []
        for cid, data in scores_map.items():
            dense_s = data["dense_score"]
            bm25_s = data["bm25_score"]
            meta = data["meta"]
            
            # Hybrid score: convex combination with alpha weighting
            convex_score = self.alpha * dense_s + (1.0 - self.alpha) * bm25_s
            # Scaled RRF contribution
            blended_score = float(0.6 * convex_score + 0.4 * (data["rrf_score"] * 30.0))
            blended_score = min(1.0, max(0.0, blended_score))

            passage = RetrievedPassage(
                id=cid,
                document_id=meta.get("document_id", ""),
                document_name=meta.get("document_name", "Unknown Document"),
                page_number=meta.get("page_number", 1),
                chunk_index=meta.get("chunk_index", 0),
                text=meta.get("text", ""),
                dense_score=round(dense_s, 4),
                bm25_score=round(bm25_s, 4),
                hybrid_score=round(blended_score, 4),
                final_score=round(blended_score, 4)
            )
            candidates.append(passage)

        candidates.sort(key=lambda x: x.final_score, reverse=True)
        return candidates[:top_k]

hybrid_retriever = HybridRetriever()
