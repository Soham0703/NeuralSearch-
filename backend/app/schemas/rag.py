from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Citation(BaseModel):
    id: str
    document_id: str
    document_name: str
    page_number: int
    chunk_index: int
    excerpt: str
    score: float
    relevance_reason: Optional[str] = None

class RetrievedPassage(BaseModel):
    id: str
    document_id: str
    document_name: str
    page_number: int
    chunk_index: int
    text: str
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    rerank_score: Optional[float] = None
    final_score: float

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    search_mode: Optional[str] = Field(
        default="hybrid_rerank",
        description="Search mode: 'semantic', 'bm25', 'hybrid', or 'hybrid_rerank'"
    )
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional filter for specific document IDs"
    )
    top_k: Optional[int] = 6
    rerank_top_k: Optional[int] = 4
    temperature: Optional[float] = 0.1
    llm_provider: Optional[str] = None  # None = use default
    llm_model: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    conversation_id: str
    citations: List[Citation]
    retrieved_passages: List[RetrievedPassage]
    grounded: bool
    unavailable_info: bool = False
    search_mode: str
    provider: str
    model: str
    latency_ms: float

class CompareRequest(BaseModel):
    document_ids: List[str]
    aspects: Optional[List[str]] = Field(
        default=["Objectives & Problem Statement", "Methodology & Architecture", "Key Findings & Results", "Limitations & Future Work"]
    )
    llm_provider: Optional[str] = None

class CompareResponse(BaseModel):
    comparison_matrix: Dict[str, Dict[str, str]]
    executive_summary: str
    citations: List[Citation]
    document_names: List[str]

class SummarizeRequest(BaseModel):
    document_id: str
    focus: Optional[str] = "executive"  # executive, methodology, findings, comprehensive
    llm_provider: Optional[str] = None

class SummarizeResponse(BaseModel):
    document_id: str
    document_name: str
    summary: str
    key_findings: List[str]
    citations: List[Citation]

class ExtractFactsRequest(BaseModel):
    document_ids: Optional[List[str]] = None
    categories: Optional[List[str]] = Field(
        default=["Key Metrics", "Methodology Claims", "Datasets Used", "Quantitative Results"]
    )
    llm_provider: Optional[str] = None

class ExtractFactsResponse(BaseModel):
    facts_by_category: Dict[str, List[Dict[str, Any]]]
    citations: List[Citation]
