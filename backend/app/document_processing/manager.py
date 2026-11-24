import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models.document import Document, DocumentChunk
from backend.app.schemas.document import DocumentResponse
from backend.app.document_processing.loaders import get_loader_for_file
from backend.app.document_processing.chunkers import get_chunker
from backend.app.rag.embeddings import embedding_engine
from backend.app.rag.vector_store import vector_store
from backend.app.rag.keyword_search import bm25_engine

logger = logging.getLogger("neuralsearch.document_manager")

class DocumentManager:
    """
    Coordinates document ingestion, page extraction, chunking,
    database persistence, embedding computation, and hybrid index updates.
    """
    def process_and_index_file(
        self,
        file_path: Path,
        filename: str,
        db: Session,
        chunk_strategy: str = "recursive",
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ) -> Document:
        doc_id = str(uuid.uuid4())
        file_size = os.path.getsize(file_path)
        file_type = file_path.suffix.lower().lstrip(".") or "txt"
        
        logger.info(f"Ingesting {filename} ({file_type}, {file_size} bytes, strategy={chunk_strategy})")

        # 1. Extract text and page metadata
        loader = get_loader_for_file(file_path)
        pages = loader.load(file_path)
        page_count = len(pages)

        # 2. Chunk text
        chunker = get_chunker(strategy=chunk_strategy, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        raw_chunks = chunker.chunk_pages(pages)

        if not raw_chunks:
            logger.warning(f"No text chunks generated for {filename}")

        # 3. Create Document DB model
        doc = Document(
            id=doc_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            page_count=page_count,
            chunk_count=len(raw_chunks),
            chunk_strategy=chunk_strategy,
            status="indexing",
            meta_info={
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "original_path": str(file_path)
            }
        )
        db.add(doc)
        db.commit()

        # 4. Generate embeddings and prepare chunks
        chunk_ids: List[str] = []
        chunk_texts: List[str] = []
        metadata_list: List[Dict[str, Any]] = []
        db_chunk_models: List[DocumentChunk] = []

        for c in raw_chunks:
            cid = f"{doc_id}_c{c.chunk_index}"
            chunk_ids.append(cid)
            chunk_texts.append(c.text)

            meta = {
                "chunk_id": cid,
                "document_id": doc_id,
                "document_name": filename,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "start_char": c.start_char,
                "end_char": c.end_char,
                "text": c.text,
                "token_count": c.token_count,
                "strategy": chunk_strategy
            }
            metadata_list.append(meta)

            db_chunk = DocumentChunk(
                id=cid,
                document_id=doc_id,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                text=c.text,
                start_char=c.start_char,
                end_char=c.end_char,
                token_count=c.token_count,
                meta_info=meta
            )
            db_chunk_models.append(db_chunk)

        # 5. Insert Chunks into DB
        if db_chunk_models:
            db.bulk_save_objects(db_chunk_models)
            db.commit()

        # 6. Generate dense embeddings and add to vector store
        if chunk_texts:
            embeddings = embedding_engine.encode(chunk_texts)
            vector_store.add_chunks(chunk_ids, embeddings, metadata_list)
            # Add to BM25 index
            bm25_engine.add_chunks(chunk_ids, chunk_texts, metadata_list)

        doc.status = "indexed"
        db.commit()
        db.refresh(doc)
        logger.info(f"Successfully indexed {filename} ({len(raw_chunks)} chunks, {page_count} pages)")
        return doc

    def delete_document(self, document_id: str, db: Session) -> bool:
        """Deletes a document from DB, Vector Store, BM25 Index, and Storage."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return False

        # Remove from vector store and BM25
        vector_store.delete_document(document_id)
        bm25_engine.delete_document(document_id)

        # Remove file from disk
        original_path = doc.meta_info.get("original_path") if doc.meta_info else None
        if original_path and os.path.exists(original_path):
            try:
                os.remove(original_path)
            except Exception as e:
                logger.warning(f"Failed to remove file from disk: {e}")

        # Remove from DB (chunks cascade deleted)
        db.delete(doc)
        db.commit()
        logger.info(f"Deleted document {document_id}")
        return True

    def reindex_document(
        self,
        document_id: str,
        db: Session,
        chunk_strategy: str = "recursive",
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ) -> Optional[Document]:
        """Re-chunks and re-embeds a document with new chunking parameters."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return None

        original_path = doc.meta_info.get("original_path") if doc.meta_info else None
        if not original_path or not os.path.exists(original_path):
            logger.error(f"Cannot reindex: source file missing for {doc.filename}")
            return None

        # 1. Purge existing chunks from index and DB
        vector_store.delete_document(document_id)
        bm25_engine.delete_document(document_id)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        db.commit()

        # 2. Re-extract and re-chunk
        file_path = Path(original_path)
        loader = get_loader_for_file(file_path)
        pages = loader.load(file_path)

        chunker = get_chunker(strategy=chunk_strategy, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        raw_chunks = chunker.chunk_pages(pages)

        # 3. Create new chunks
        chunk_ids: List[str] = []
        chunk_texts: List[str] = []
        metadata_list: List[Dict[str, Any]] = []
        db_chunk_models: List[DocumentChunk] = []

        for c in raw_chunks:
            cid = f"{document_id}_c{c.chunk_index}"
            chunk_ids.append(cid)
            chunk_texts.append(c.text)

            meta = {
                "chunk_id": cid,
                "document_id": document_id,
                "document_name": doc.filename,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "start_char": c.start_char,
                "end_char": c.end_char,
                "text": c.text,
                "token_count": c.token_count,
                "strategy": chunk_strategy
            }
            metadata_list.append(meta)

            db_chunk = DocumentChunk(
                id=cid,
                document_id=document_id,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                text=c.text,
                start_char=c.start_char,
                end_char=c.end_char,
                token_count=c.token_count,
                meta_info=meta
            )
            db_chunk_models.append(db_chunk)

        if db_chunk_models:
            db.bulk_save_objects(db_chunk_models)
            db.commit()

        if chunk_texts:
            embeddings = embedding_engine.encode(chunk_texts)
            vector_store.add_chunks(chunk_ids, embeddings, metadata_list)
            bm25_engine.add_chunks(chunk_ids, chunk_texts, metadata_list)

        doc.chunk_count = len(raw_chunks)
        doc.chunk_strategy = chunk_strategy
        doc.meta_info = {
            **doc.meta_info,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "last_reindexed": str(os.getenv("CURRENT_TIME", ""))
        }
        db.commit()
        db.refresh(doc)
        logger.info(f"Re-indexed {doc.filename} with {len(raw_chunks)} chunks ({chunk_strategy})")
        return doc

    def rebuild_all_indices(self, db: Session) -> Dict[str, Any]:
        """Completely rebuilds vector store and BM25 index from all documents in the database."""
        vector_store.clear()
        bm25_engine.clear()

        docs = db.query(Document).all()
        total_chunks = 0
        for doc in docs:
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
            if not chunks:
                continue

            chunk_ids = [c.id for c in chunks]
            chunk_texts = [c.text for c in chunks]
            metadata_list = [c.meta_info or {
                "chunk_id": c.id,
                "document_id": doc.id,
                "document_name": doc.filename,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "text": c.text
            } for c in chunks]

            embeddings = embedding_engine.encode(chunk_texts)
            vector_store.add_chunks(chunk_ids, embeddings, metadata_list)
            bm25_engine.add_chunks(chunk_ids, chunk_texts, metadata_list)
            total_chunks += len(chunks)

        return {"documents_processed": len(docs), "total_chunks_indexed": total_chunks}

document_manager = DocumentManager()
