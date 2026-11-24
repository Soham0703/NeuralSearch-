import re
from typing import List, Dict, Any
from backend.app.schemas.eval import BenchmarkQuery
from backend.app.schemas.rag import RetrievedPassage
from backend.app.rag.embeddings import embedding_engine
import numpy as np

class RAGMetricsEvaluator:
    """
    Evaluates generation quality:
    - Faithfulness (Context Groundedness): checks if answer claims are grounded in context
    - Answer Relevance: semantic alignment between answer and question/ground truth
    - Context Precision: ratio of relevant chunks among retrieved passages
    """
    def evaluate_faithfulness(self, answer: str, passages: List[RetrievedPassage]) -> float:
        if not passages or not answer:
            return 0.0

        ans_lower = answer.lower()
        if (
            "insufficient information" in ans_lower
            or "not have sufficient information" in ans_lower
            or "unavailable" in ans_lower
            or "no supporting passages" in ans_lower
        ):
            return 1.0  # Refusing to answer unsupported query is 100% faithful

        # Aggregate context tokens
        context_text = " ".join([p.text.lower() for p in passages])
        context_words = set(re.findall(r"\b\w{3,}\b", context_text))

        # Strip citations like [doc.txt, p.1] before extracting sentences
        clean_text_for_claims = re.sub(r"\[[^\]]+\]", "", answer).strip()

        # Extract answer claims / sentences
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text_for_claims) if s.strip()]
        if not sentences:
            return 0.0

        grounded_sentences = 0
        for s in sentences:
            words = [w for w in re.findall(r"\b\w{3,}\b", s.lower()) if w not in {"the", "and", "that", "this", "with", "from"}]
            if not words:
                continue
            matched = sum(1 for w in words if w in context_words)
            if matched / len(words) >= 0.40:
                grounded_sentences += 1

        score = grounded_sentences / len(sentences)
        return round(float(min(1.0, max(0.0, score))), 4)

    def evaluate_answer_relevance(self, query: str, answer: str, expected_answer: str) -> float:
        if not answer:
            return 0.0

        # Encode query, answer, and expected answer
        vecs = embedding_engine.encode([query, answer, expected_answer])
        q_vec, a_vec, exp_vec = vecs[0], vecs[1], vecs[2]

        # Cosine similarity
        def cos_sim(v1, v2):
            norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(v1, v2) / (norm1 * norm2))

        sim_to_query = max(0.0, cos_sim(q_vec, a_vec))
        sim_to_expected = max(0.0, cos_sim(a_vec, exp_vec))

        # Blended relevance score
        blended = 0.40 * sim_to_query + 0.60 * sim_to_expected
        return round(float(min(1.0, max(0.0, blended))), 4)

    def evaluate_context_precision(self, passages: List[RetrievedPassage], query: BenchmarkQuery) -> float:
        from backend.app.evaluation.retrieval_metrics import retrieval_evaluator
        if not passages:
            return 0.0

        relevant_count = sum(1 for p in passages if retrieval_evaluator.is_hit(p, query))
        return round(relevant_count / len(passages), 4)

rag_metrics_evaluator = RAGMetricsEvaluator()
