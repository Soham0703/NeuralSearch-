import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.conversation import EvaluationRun
from backend.app.schemas.eval import BenchmarkConfig, BenchmarkReport, EvaluationRunResult, BenchmarkQuery
from backend.app.evaluation.benchmark_runner import benchmark_runner
from backend.app.evaluation.dataset import get_benchmark_dataset

logger = logging.getLogger("neuralsearch.routers.eval")
router = APIRouter(prefix="/eval", tags=["Evaluation"])

@router.post("/benchmark", response_model=BenchmarkReport)
def run_benchmark_endpoint(
    config: BenchmarkConfig = None,
    db: Session = Depends(get_db)
):
    """
    Executes live RAG evaluation benchmark across chunking and retrieval modes.
    Computes Recall@1, Recall@3, Recall@5, MRR, Faithfulness, and Answer Relevance.
    """
    try:
        report = benchmark_runner.run_benchmark(db=db, config=config)
        return report
    except Exception as e:
        logger.error(f"Benchmark error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs", response_model=List[EvaluationRunResult])
def get_evaluation_runs(db: Session = Depends(get_db)):
    """Returns historical evaluation benchmark runs."""
    runs = db.query(EvaluationRun).order_by(EvaluationRun.timestamp.desc()).all()
    return runs

@router.get("/dataset", response_model=List[BenchmarkQuery])
def get_dataset_endpoint():
    """Returns curated research evaluation dataset."""
    return get_benchmark_dataset()
