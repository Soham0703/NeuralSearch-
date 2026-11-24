import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db, SessionLocal
from backend.app.routers import documents_router, rag_router, conversations_router, evaluation_router
from backend.app.models.document import Document
from backend.app.document_processing.manager import document_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("neuralsearch")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise-grade AI Knowledge & Research Assistant with Multi-document Q&A, Hybrid Search, Neural Reranking, Strict Citations, and Empirical Benchmarking."
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: configure explicit origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(rag_router, prefix=settings.API_V1_PREFIX)
app.include_router(conversations_router, prefix=settings.API_V1_PREFIX)
app.include_router(evaluation_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing Database...")
    init_db()

    # Automatically load sample research papers on first startup if document table is empty
    db = SessionLocal()
    try:
        doc_count = db.query(Document).count()
        if doc_count == 0:
            logger.info("No documents found. Ingesting benchmark research papers...")
            sample_dir = Path(__file__).resolve().parent.parent / "sample_data"
            if sample_dir.exists():
                for sample_file in sample_dir.glob("*.txt"):
                    dest = settings.STORAGE_DIR / sample_file.name
                    import shutil
                    shutil.copy(sample_file, dest)
                    document_manager.process_and_index_file(
                        file_path=dest,
                        filename=dest.name,
                        db=db,
                        chunk_strategy="recursive",
                        chunk_size=500,
                        chunk_overlap=100
                    )
            logger.info("Sample research documents loaded and indexed.")
    except Exception as e:
        logger.error(f"Error during sample data bootstrap: {e}")
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "reranker_model": settings.RERANKER_MODEL_NAME,
        "default_provider": settings.DEFAULT_LLM_PROVIDER
    }

@app.get("/api/config")
def get_system_config():
    return {
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "reranker_model": settings.RERANKER_MODEL_NAME,
        "default_chunk_size": settings.DEFAULT_CHUNK_SIZE,
        "default_chunk_overlap": settings.DEFAULT_CHUNK_OVERLAP,
        "default_llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "providers_available": ["mock", "openai", "gemini", "anthropic", "ollama"],
        "retrieval_modes": [
            {"id": "hybrid_rerank", "label": "Hybrid + Neural Reranker (Recommended)", "desc": "Dense + BM25 with Cross-Encoder scoring"},
            {"id": "hybrid", "label": "Hybrid Search (RRF)", "desc": "Reciprocal Rank Fusion of Dense and BM25"},
            {"id": "semantic", "label": "Semantic Dense Search", "desc": "Sentence Transformer vector embeddings"},
            {"id": "bm25", "label": "BM25 Keyword Search", "desc": "Lexical exact term matching"}
        ],
        "chunking_strategies": [
            {"id": "recursive", "label": "Recursive Character", "desc": "Hierarchical boundary splitting (paragraphs, sentences)"},
            {"id": "page_based", "label": "Page-Preserving", "desc": "Strict page boundary isolation for 100% citation attribution"},
            {"id": "semantic", "label": "Semantic Paragraph", "desc": "Paragraph and thematic transition breaks"}
        ]
    }
