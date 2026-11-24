import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)     # in bytes
    page_count = Column(Integer, default=1)
    chunk_count = Column(Integer, default=0)
    chunk_strategy = Column(String(50), default="recursive")
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(30), default="indexed")  # uploaded, indexing, indexed, error
    meta_info = Column(JSON, default=dict)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True, index=True)  # doc_id_chunk_idx
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False, default=1)
    text = Column(Text, nullable=False)
    start_char = Column(Integer, default=0)
    end_char = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    meta_info = Column(JSON, default=dict)

    document = relationship("Document", back_populates="chunks")
