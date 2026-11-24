from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class BenchmarkQuery(BaseModel):
    id: str
    query: str
    expected_answer: str
    relevant_doc_names: List[str]
    relevant_pages: List[int]
    ground_truth_passages: List[str]

class BenchmarkConfig(BaseModel):
    dataset_name: Optional[str] = "research_benchmark_v1"
    chunk_strategies: List[str] = Field(default=["recursive", "page_based"])
    retrieval_modes: List[str] = Field(default=["semantic", "bm25", "hybrid", "hybrid_rerank"])
    top_k_values: List[int] = Field(default=[1, 3, 5])
    llm_provider: Optional[str] = None

class EvaluationRunResult(BaseModel):
    id: str
    timestamp: datetime
    dataset_name: str
    chunk_strategy: str
    chunk_size: int
    chunk_overlap: int
    retrieval_mode: str
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    mrr: float
    faithfulness: float
    answer_relevance: float
    total_queries: int
    metrics_json: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True

class BenchmarkReport(BaseModel):
    runs: List[EvaluationRunResult]
    comparison_summary: Dict[str, Any]
    best_configuration: str
