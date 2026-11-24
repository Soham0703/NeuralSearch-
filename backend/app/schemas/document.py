from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class DocumentChunkSchema(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    page_number: int
    text: str
    start_char: int
    end_char: int
    token_count: int
    meta_info: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    page_count: int
    chunk_count: int
    chunk_strategy: str
    upload_date: datetime
    status: str
    meta_info: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

class ReindexRequest(BaseModel):
    chunk_strategy: Optional[str] = "recursive"
    chunk_size: Optional[int] = 500
    chunk_overlap: Optional[int] = 100
