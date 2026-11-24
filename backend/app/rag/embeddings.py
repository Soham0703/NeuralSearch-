import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.app.config import settings

logger = logging.getLogger("neuralsearch.embeddings")

class EmbeddingEngine:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        model_name = settings.EMBEDDING_MODEL_NAME
        logger.info(f"Loading embedding model: {model_name}")
        try:
            # First try loading local cached model
            self._model = SentenceTransformer(model_name, local_files_only=True)
            logger.info("SentenceTransformer embedding model loaded from local cache.")
        except Exception:
            try:
                # If local_files_only fails, try standard load
                self._model = SentenceTransformer(model_name)
                logger.info("SentenceTransformer embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load {model_name}: {e}. Falling back to default.")
                try:
                    self._model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
                except Exception as e2:
                    self._model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32, normalize: bool = True) -> np.ndarray:
        """Generates normalized vector embeddings for texts."""
        if isinstance(texts, str):
            texts = [texts]
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )
        return embeddings.astype(np.float32)

    @property
    def dimension(self) -> int:
        if self._model:
            return self._model.get_sentence_embedding_dimension()
        return 384

embedding_engine = EmbeddingEngine()
