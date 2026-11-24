import logging
from typing import List, Tuple, Optional
import numpy as np
from sentence_transformers import CrossEncoder
from backend.app.config import settings
from backend.app.schemas.rag import RetrievedPassage

logger = logging.getLogger("neuralsearch.reranker")

class NeuralReranker:
    """
    Cross-Encoder neural reranker using cross-attention to score query-document pairs,
    with automatic fallbacks and calibration.
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NeuralReranker, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        model_name = settings.RERANKER_MODEL_NAME
        logger.info(f"Initializing CrossEncoder reranker: {model_name}")
        try:
            self._model = CrossEncoder(model_name, local_files_only=True)
            logger.info("CrossEncoder reranker loaded from local cache.")
        except Exception:
            try:
                self._model = CrossEncoder(model_name)
                logger.info("CrossEncoder reranker loaded successfully.")
            except Exception as e:
                logger.warning(f"CrossEncoder download failed ({e}). Using heuristic neural score fallback.")
                self._model = None

    def rerank(
        self,
        query: str,
        passages: List[RetrievedPassage],
        top_k: int = 4
    ) -> List[RetrievedPassage]:
        """
        Reranks a list of candidate RetrievedPassages against the query.
        Updates passage.rerank_score and passage.final_score.
        """
        if not passages:
            return []

        if len(passages) <= 1:
            passages[0].rerank_score = passages[0].hybrid_score or passages[0].dense_score or 1.0
            passages[0].final_score = passages[0].rerank_score
            return passages

        if self._model is not None:
            pairs = [[query, p.text] for p in passages]
            try:
                raw_scores = self._model.predict(pairs)
                # Apply sigmoid or min-max calibration to [0.0, 1.0]
                # CrossEncoder MS-MARCO outputs logits (approx -10 to +10)
                scores = 1.0 / (1.0 + np.exp(-np.array(raw_scores, dtype=np.float32)))
                for p, score in zip(passages, scores):
                    p.rerank_score = float(score)
                    # Blend 70% reranker + 30% prior hybrid score
                    prior = p.hybrid_score if p.hybrid_score is not None else (p.dense_score or 0.5)
                    p.final_score = round(float(0.75 * p.rerank_score + 0.25 * prior), 4)
            except Exception as e:
                logger.error(f"Inference error in reranker: {e}")
                self._fallback_rerank(query, passages)
        else:
            self._fallback_rerank(query, passages)

        # Sort descending by final_score
        passages.sort(key=lambda x: x.final_score, reverse=True)
        return passages[:top_k]

    def _fallback_rerank(self, query: str, passages: List[RetrievedPassage]) -> None:
        """Heuristic semantic reranker when CrossEncoder weights unavailable."""
        query_words = set(query.lower().split())
        for p in passages:
            passage_words = p.text.lower().split()
            # Term density and overlap
            exact_matches = sum(1 for w in query_words if w in p.text.lower())
            overlap_ratio = exact_matches / max(1, len(query_words))
            prior = p.hybrid_score or p.dense_score or 0.5
            p.rerank_score = round(float(0.5 * prior + 0.5 * overlap_ratio), 4)
            p.final_score = p.rerank_score

reranker = NeuralReranker()
