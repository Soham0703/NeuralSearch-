import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.rag import (
    QueryRequest, QueryResponse, CompareRequest, CompareResponse,
    SummarizeRequest, SummarizeResponse, ExtractFactsRequest, ExtractFactsResponse
)
from backend.app.rag.rag_service import rag_service

logger = logging.getLogger("neuralsearch.routers.rag")
router = APIRouter(prefix="/rag", tags=["RAG"])

@router.post("/chat", response_model=QueryResponse)
def chat_endpoint(request: QueryRequest, db: Session = Depends(get_db)):
    """Multi-turn grounded conversational question answering with citations."""
    try:
        return rag_service.answer_query(request, db)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest, db: Session = Depends(get_db)):
    """Direct RAG query with citations and passage inspection."""
    return rag_service.answer_query(request, db)

@router.post("/compare", response_model=CompareResponse)
def compare_endpoint(request: CompareRequest, db: Session = Depends(get_db)):
    """Multi-document research paper comparison across key dimensions."""
    if len(request.document_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 document IDs are required for comparison.")
    try:
        return rag_service.compare_documents(request, db)
    except Exception as e:
        logger.error(f"Error in compare endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize", response_model=SummarizeResponse)
def summarize_endpoint(request: SummarizeRequest, db: Session = Depends(get_db)):
    """Document executive summary and bulleted key findings."""
    try:
        return rag_service.summarize_document(request, db)
    except Exception as e:
        logger.error(f"Error in summarize endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-facts", response_model=ExtractFactsResponse)
def extract_facts_endpoint(request: ExtractFactsRequest, db: Session = Depends(get_db)):
    """Categorized factual metrics and findings extraction with citations."""
    try:
        return rag_service.extract_facts(request, db)
    except Exception as e:
        logger.error(f"Error in extract-facts endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
