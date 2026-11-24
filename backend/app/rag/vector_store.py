import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from backend.app.config import settings

logger = logging.getLogger("neuralsearch.vector_store")

class NeuralVectorStore:
    """
    Enterprise In-Memory and Persistent Vector Database with Cosine / Inner Product
    similarity search, metadata filtering, dynamic deletion, and index serialization.
    """
    def __init__(self, index_name: str = "neuralsearch_vectors"):
        self.index_name = index_name
        self.index_dir = settings.INDEX_DIR
        self.vectors_file = self.index_dir / f"{index_name}.npz"
        self.metadata_file = self.index_dir / f"{index_name}_meta.json"
        
        self.chunk_ids: List[str] = []
        self.metadata_list: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None  # Shape: (N, D)
        
        self.load()

    def add_chunks(self, chunk_ids: List[str], vectors: np.ndarray, metadata_list: List[Dict[str, Any]]) -> None:
        """Add new chunk embeddings and metadata."""
        if len(chunk_ids) == 0:
            return

        assert len(chunk_ids) == len(metadata_list) == len(vectors), "Mismatched lengths"
        
        # Ensure vectors are normalized
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_vectors = vectors / norms

        if self.vectors is None or len(self.chunk_ids) == 0:
            self.vectors = normalized_vectors.astype(np.float32)
            self.chunk_ids = list(chunk_ids)
            self.metadata_list = list(metadata_list)
        else:
            self.vectors = np.vstack([self.vectors, normalized_vectors.astype(np.float32)])
            self.chunk_ids.extend(chunk_ids)
            self.metadata_list.extend(metadata_list)

        self.save()
        logger.info(f"Added {len(chunk_ids)} chunks to vector store. Total chunks: {len(self.chunk_ids)}")

    def delete_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a document."""
        if not self.chunk_ids:
            return 0

        keep_indices = [
            i for i, meta in enumerate(self.metadata_list)
            if meta.get("document_id") != document_id
        ]
        deleted_count = len(self.chunk_ids) - len(keep_indices)

        if deleted_count > 0:
            if keep_indices:
                self.chunk_ids = [self.chunk_ids[i] for i in keep_indices]
                self.metadata_list = [self.metadata_list[i] for i in keep_indices]
                self.vectors = self.vectors[keep_indices]
            else:
                self.chunk_ids = []
                self.metadata_list = []
                self.vectors = None
            self.save()
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            
        return deleted_count

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Cosine similarity search with optional document ID filtering.
        Returns List of (chunk_id, similarity_score, metadata)
        """
        if self.vectors is None or len(self.chunk_ids) == 0:
            return []

        # Normalize query vector
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            q_vec = (query_vector / query_norm).reshape(1, -1)
        else:
            q_vec = query_vector.reshape(1, -1)

        # Compute dot product (cosine similarity on unit vectors)
        scores = np.dot(self.vectors, q_vec.T).flatten()

        # Apply filtering if document_ids specified
        if document_ids:
            doc_id_set = set(document_ids)
            mask = np.array([
                meta.get("document_id") in doc_id_set
                for meta in self.metadata_list
            ], dtype=bool)
            scores = np.where(mask, scores, -1e9)

        # Get top indices
        top_k = min(top_k, len(scores))
        if top_k <= 0:
            return []

        # Argpartition for top K
        partition_indices = np.argpartition(scores, -top_k)[-top_k:]
        sorted_indices = partition_indices[np.argsort(-scores[partition_indices])]

        results = []
        for idx in sorted_indices:
            score = float(scores[idx])
            if score < -1e8:  # Filtered out
                continue
            # Clamp cosine score between 0.0 and 1.0
            clamped_score = max(0.0, min(1.0, (score + 1.0) / 2.0))
            results.append((
                self.chunk_ids[idx],
                clamped_score,
                self.metadata_list[idx]
            ))

        return results

    def save(self) -> None:
        """Persist index to disk."""
        try:
            if self.vectors is not None and len(self.chunk_ids) > 0:
                np.savez_compressed(self.vectors_file, vectors=self.vectors)
            elif self.vectors_file.exists():
                self.vectors_file.unlink()

            data = {
                "chunk_ids": self.chunk_ids,
                "metadata_list": self.metadata_list
            }
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def load(self) -> None:
        """Load index from disk."""
        if self.vectors_file.exists() and self.metadata_file.exists():
            try:
                npz = np.load(self.vectors_file)
                self.vectors = npz["vectors"]
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunk_ids = data.get("chunk_ids", [])
                    self.metadata_list = data.get("metadata_list", [])
                logger.info(f"Loaded vector store with {len(self.chunk_ids)} chunks.")
            except Exception as e:
                logger.warning(f"Error loading vector index: {e}. Starting fresh.")
                self.vectors = None
                self.chunk_ids = []
                self.metadata_list = []

    def clear(self) -> None:
        """Reset entire vector index."""
        self.chunk_ids = []
        self.metadata_list = []
        self.vectors = None
        if self.vectors_file.exists():
            self.vectors_file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()

vector_store = NeuralVectorStore()
