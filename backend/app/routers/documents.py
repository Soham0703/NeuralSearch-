import shutil
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.document import Document, DocumentChunk
from backend.app.schemas.document import DocumentResponse, DocumentListResponse, ReindexRequest, DocumentChunkSchema
from backend.app.document_processing.manager import document_manager

logger = logging.getLogger("neuralsearch.routers.documents")
router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_strategy: str = Form("recursive"),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(100),
    db: Session = Depends(get_db)
):
    """Uploads and indexes a research document (PDF, DOCX, TXT)."""
    filename = file.filename or "uploaded_document.txt"
    suffix = Path(filename).suffix.lower()
    if suffix not in [".pdf", ".docx", ".doc", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}. Supported: PDF, DOCX, TXT.")

    # Save to storage dir
    dest_path = settings.STORAGE_DIR / filename
    # Avoid collision
    counter = 1
    stem = Path(filename).stem
    while dest_path.exists():
        dest_path = settings.STORAGE_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        doc = document_manager.process_and_index_file(
            file_path=dest_path,
            filename=dest_path.name,
            db=db,
            chunk_strategy=chunk_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return doc
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process and index document: {e}")

@router.get("", response_model=DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Lists all indexed documents."""
    total = db.query(Document).count()
    docs = db.query(Document).order_by(Document.upload_date.desc()).offset(skip).limit(limit).all()
    return DocumentListResponse(documents=docs, total=total)

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieves document details."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@router.get("/{document_id}/chunks", response_model=List[DocumentChunkSchema])
def get_document_chunks(document_id: str, db: Session = Depends(get_db)):
    """Retrieves all chunks for a document."""
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
    return chunks

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Deletes a document from the database and indices."""
    success = document_manager.delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Document deleted successfully.", "document_id": document_id}

@router.post("/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    document_id: str,
    request: ReindexRequest,
    db: Session = Depends(get_db)
):
    """Re-chunks and re-indexes an existing document."""
    doc = document_manager.reindex_document(
        document_id=document_id,
        db=db,
        chunk_strategy=request.chunk_strategy or "recursive",
        chunk_size=request.chunk_size or 500,
        chunk_overlap=request.chunk_overlap or 100
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or source file missing.")
    return doc

@router.post("/load-samples")
def load_sample_documents(db: Session = Depends(get_db)):
    """Loads and indexes the pre-packaged scientific benchmark research papers."""
    sample_dir = Path(__file__).resolve().parent.parent.parent / "sample_data"
    if not sample_dir.exists():
        raise HTTPException(status_code=404, detail="Sample data directory not found.")

    indexed = []
    for file_path in sample_dir.glob("*.txt"):
        # Check if already indexed by filename
        existing = db.query(Document).filter(Document.filename == file_path.name).first()
        if not existing:
            # Copy to storage
            dest = settings.STORAGE_DIR / file_path.name
            shutil.copy(file_path, dest)
            doc = document_manager.process_and_index_file(
                file_path=dest,
                filename=dest.name,
                db=db,
                chunk_strategy="recursive",
                chunk_size=500,
                chunk_overlap=100
            )
            indexed.append(doc.filename)

    return {"message": f"Indexed {len(indexed)} sample documents.", "documents": indexed}

@router.post("/index/rebuild")
def rebuild_indices(db: Session = Depends(get_db)):
    """Rebuilds all vector and BM25 indices from DB records."""
    res = document_manager.rebuild_all_indices(db)
    return {"message": "Indices rebuilt successfully.", **res}
