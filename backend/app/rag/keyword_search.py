import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
from backend.app.config import settings

logger = logging.getLogger("neuralsearch.bm25")

class BM25SearchEngine:
    """
    In-memory BM25 Okapi search engine with document persistence,
    incremental chunk addition, deletion, and normalized scoring.
    """
    def __init__(self, index_name: str = "neuralsearch_bm25"):
        self.index_name = index_name
        self.index_dir = settings.INDEX_DIR
        self.corpus_file = self.index_dir / f"{index_name}_corpus.json"
        
        self.chunk_ids: List[str] = []
        self.corpus_tokens: List[List[str]] = []
        self.metadata_list: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        
        self.load()

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, clean alphanumeric tokens
        tokens = re.findall(r"\b\w{2,}\b", text.lower())
        return tokens

    def add_chunks(self, chunk_ids: List[str], texts: List[str], metadata_list: List[Dict[str, Any]]) -> None:
        """Add new chunks to the BM25 index."""
        if not chunk_ids:
            return

        new_tokens = [self._tokenize(t) for t in texts]
        self.chunk_ids.extend(chunk_ids)
        self.corpus_tokens.extend(new_tokens)
        self.metadata_list.extend(metadata_list)
        
        self._rebuild_index()
        self.save()
        logger.info(f"Added {len(chunk_ids)} chunks to BM25 index. Total: {len(self.chunk_ids)}")

    def delete_document(self, document_id: str) -> int:
        """Remove all chunks associated with a document ID."""
        if not self.chunk_ids:
            return 0

        keep_indices = [
            i for i, meta in enumerate(self.metadata_list)
            if meta.get("document_id") != document_id
        ]
        deleted_count = len(self.chunk_ids) - len(keep_indices)

        if deleted_count > 0:
            self.chunk_ids = [self.chunk_ids[i] for i in keep_indices]
            self.corpus_tokens = [self.corpus_tokens[i] for i in keep_indices]
            self.metadata_list = [self.metadata_list[i] for i in keep_indices]
            self._rebuild_index()
            self.save()
            logger.info(f"Deleted {deleted_count} chunks from BM25 for doc {document_id}")

        return deleted_count

    def _rebuild_index(self) -> None:
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = None

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        BM25 search with normalized scores in [0.0, 1.0].
        Returns List of (chunk_id, normalized_score, metadata)
        """
        if self.bm25 is None or not self.chunk_ids:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        raw_scores = [max(0.0, float(s)) for s in self.bm25.get_scores(query_tokens)]
        
        # Max score normalization; if all zero, fall back to token overlap
        max_score = float(max(raw_scores)) if len(raw_scores) > 0 else 0.0
        if max_score <= 0.0:
            query_set = set(query_tokens)
            raw_scores = [
                float(sum(1 for t in doc_toks if t in query_set))
                for doc_toks in self.corpus_tokens
            ]
            max_score = float(max(raw_scores)) if len(raw_scores) > 0 else 0.0

        if max_score <= 0.0:
            return []

        # Filter and rank
        candidates = []
        doc_id_set = set(document_ids) if document_ids else None

        for idx, score in enumerate(raw_scores):
            if score <= 0.0:
                continue
            meta = self.metadata_list[idx]
            if doc_id_set and meta.get("document_id") not in doc_id_set:
                continue
            norm_score = float(score) / max_score
            candidates.append((
                self.chunk_ids[idx],
                norm_score,
                meta
            ))

        # Sort descending by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]

    def save(self) -> None:
        try:
            data = {
                "chunk_ids": self.chunk_ids,
                "metadata_list": self.metadata_list,
                "corpus_tokens": self.corpus_tokens
            }
            with open(self.corpus_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save BM25 corpus: {e}")

    def load(self) -> None:
        if self.corpus_file.exists():
            try:
                with open(self.corpus_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunk_ids = data.get("chunk_ids", [])
                    self.metadata_list = data.get("metadata_list", [])
                    self.corpus_tokens = data.get("corpus_tokens", [])
                self._rebuild_index()
                logger.info(f"Loaded BM25 index with {len(self.chunk_ids)} chunks.")
            except Exception as e:
                logger.warning(f"Error loading BM25 index: {e}")
                self.chunk_ids = []
                self.metadata_list = []
                self.corpus_tokens = []
                self.bm25 = None

    def clear(self) -> None:
        self.chunk_ids = []
        self.corpus_tokens = []
        self.metadata_list = []
        self.bm25 = None
        if self.corpus_file.exists():
            self.corpus_file.unlink()

bm25_engine = BM25SearchEngine()
