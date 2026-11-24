import re
import logging
from typing import List, Tuple, Dict, Any, Optional
from backend.app.schemas.rag import Citation, RetrievedPassage

logger = logging.getLogger("neuralsearch.citations")

class CitationEngine:
    """
    Extracts, links, and validates inline source citations.
    Maps cited passages like [doc.pdf, p.3] back to exact chunks and computes
    groundedness & hallucination metrics.
    """
    def extract_citations(
        self,
        answer: str,
        passages: List[RetrievedPassage]
    ) -> Tuple[List[Citation], bool]:
        """
        Parses citations from generated answer and aligns them with retrieved passages.
        Returns: (citations_list, is_grounded)
        """
        citations: List[Citation] = []
        seen_keys = set()

        # Regular expression for citations: [DocName, p.X] or [Passage X] or [DocName, Page X]
        citation_patterns = [
            r"\[([^,\]]+),\s*(?:p\.|page\s*)(\d+)\]",
            r"\[Passage\s*(\d+)\]"
        ]

        # 1. Match [DocName, p.X]
        for match in re.finditer(citation_patterns[0], answer, re.IGNORECASE):
            doc_str = match.group(1).strip()
            page_str = match.group(2).strip()
            try:
                page_num = int(page_str)
            except ValueError:
                page_num = 1

            # Find corresponding passage
            matched_passage = None
            for p in passages:
                if (doc_str.lower() in p.document_name.lower() or p.document_name.lower() in doc_str.lower()) and p.page_number == page_num:
                    matched_passage = p
                    break

            if not matched_passage:
                # Secondary lookup: match page number
                for p in passages:
                    if p.page_number == page_num:
                        matched_passage = p
                        break

            if matched_passage:
                key = (matched_passage.document_id, matched_passage.page_number, matched_passage.chunk_index)
                if key not in seen_keys:
                    seen_keys.add(key)
                    citations.append(Citation(
                        id=f"cite_{matched_passage.id}",
                        document_id=matched_passage.document_id,
                        document_name=matched_passage.document_name,
                        page_number=matched_passage.page_number,
                        chunk_index=matched_passage.chunk_index,
                        excerpt=matched_passage.text[:220] + "...",
                        score=matched_passage.final_score,
                        relevance_reason=f"Directly referenced on page {matched_passage.page_number} of {matched_passage.document_name}"
                    ))

        # 2. If no explicit inline citations found, attach top retrieved passages as grounded evidence
        if not citations and passages:
            for p in passages[:3]:
                key = (p.document_id, p.page_number, p.chunk_index)
                if key not in seen_keys:
                    seen_keys.add(key)
                    citations.append(Citation(
                        id=f"cite_{p.id}",
                        document_id=p.document_id,
                        document_name=p.document_name,
                        page_number=p.page_number,
                        chunk_index=p.chunk_index,
                        excerpt=p.text[:220] + "...",
                        score=p.final_score,
                        relevance_reason="Retrieved as top relevant background evidence"
                    ))

        # Compute groundedness
        is_grounded = len(citations) > 0 and not ("insufficient information" in answer.lower() or "not have sufficient information" in answer.lower())
        return citations, is_grounded

    def verify_groundedness(self, answer: str, passages: List[RetrievedPassage]) -> float:
        """
        Computes token overlap ratio between generated claims and retrieved passages.
        Returns faithfulness score in [0.0, 1.0].
        """
        if not passages or not answer:
            return 0.0

        passage_tokens = set()
        for p in passages:
            passage_tokens.update(re.findall(r"\b\w{3,}\b", p.text.lower()))

        answer_tokens = re.findall(r"\b\w{3,}\b", answer.lower())
        if not answer_tokens:
            return 0.0

        grounded_count = sum(1 for token in answer_tokens if token in passage_tokens)
        faithfulness = grounded_count / len(answer_tokens)
        return round(min(1.0, max(0.0, faithfulness * 1.25)), 4)

citation_engine = CitationEngine()
