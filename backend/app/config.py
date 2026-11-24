import os
import sys

# Prevent OpenMP runtime duplicate library collision on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TQDM_DISABLE"] = "1"
os.environ["NO_COLOR"] = "1"

try:
    import colorama.win32
    colorama.win32.winapi_test = lambda: False
    colorama.win32._winapi_test = lambda h: False
except Exception:
    pass

from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = DATA_DIR / "documents"
INDEX_DIR = DATA_DIR / "indices"

# Ensure directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    PROJECT_NAME: str = "NeuralSearch – Enterprise AI Knowledge & Research Assistant"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Storage paths
    STORAGE_DIR: Path = STORAGE_DIR
    INDEX_DIR: Path = INDEX_DIR
    
    # Database config (defaults to SQLite if PostgreSQL not supplied)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{DATA_DIR / 'neuralsearch.db'}"
    )
    
    # AI & Embeddings config
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    RERANKER_MODEL_NAME: str = os.getenv("RERANKER_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    # Chunking Defaults
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("DEFAULT_CHUNK_SIZE", "500"))
    DEFAULT_CHUNK_OVERLAP: int = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "100"))
    DEFAULT_CHUNKING_STRATEGY: str = os.getenv("DEFAULT_CHUNKING_STRATEGY", "recursive")
    
    # Retrieval Defaults
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "6"))
    DEFAULT_RERANK_TOP_K: int = int(os.getenv("DEFAULT_RERANK_TOP_K", "4"))
    HYBRID_ALPHA: float = float(os.getenv("HYBRID_ALPHA", "0.5"))  # 0.0 = BM25 only, 1.0 = Dense only
    
    # LLM Provider configuration
    # Options: "mock", "openai", "gemini", "anthropic", "ollama"
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "mock")
    
    # Provider Keys & Models
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

settings = Settings()
