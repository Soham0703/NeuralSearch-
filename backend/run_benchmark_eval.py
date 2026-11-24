import os
import sys

# Ensure environment variables are active
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TQDM_DISABLE"] = "1"
os.environ["NO_COLOR"] = "1"

from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import init_db, SessionLocal
from backend.app.routers.documents import load_sample_documents
from backend.app.evaluation.benchmark_runner import benchmark_runner
from backend.app.schemas.eval import BenchmarkConfig

def main():
    print("=" * 80)
    print("NEURALSEARCH EMPIRICAL RAG BENCHMARK & EVALUATION RUNNER")
    print("=" * 80)

    init_db()
    db = SessionLocal()

    # Ensure samples are loaded
    print("[1/3] Ensuring benchmark sample documents are indexed...")
    load_sample_documents(db)

    # Run full grid benchmark
    print("[2/3] Executing live benchmark evaluation across retrieval modes and chunking strategies...")
    config = BenchmarkConfig(
        dataset_name="research_benchmark_v1",
        chunk_strategies=["recursive", "page_based"],
        retrieval_modes=["semantic", "bm25", "hybrid", "hybrid_rerank"]
    )
    report = benchmark_runner.run_benchmark(db=db, config=config)

    print("\n[3/3] EMPIRICAL BENCHMARK EVALUATION RESULTS:")
    print("-" * 105)
    print(f"{'Retrieval Mode':<16} | {'Chunk Strategy':<14} | {'Recall@1':<9} | {'Recall@3':<9} | {'Recall@5':<9} | {'MRR':<7} | {'Faithfulness':<12} | {'Relevance':<10}")
    print("-" * 105)

    for run in report.runs:
        print(
            f"{run.retrieval_mode.upper():<16} | "
            f"{run.chunk_strategy:<14} | "
            f"{run.recall_at_1 * 100:>7.1f}% | "
            f"{run.recall_at_3 * 100:>7.1f}% | "
            f"{run.recall_at_5 * 100:>7.1f}% | "
            f"{run.mrr:>7.3f} | "
            f"{run.faithfulness * 100:>10.1f}% | "
            f"{run.answer_relevance * 100:>8.1f}%"
        )
    print("-" * 105)

    print(f"\nBest Overall Configuration: {report.best_configuration}")
    print("\nEvaluation Key Insights:")
    for insight in report.comparison_summary.get("insights", []):
        print(f"  * {insight}")
    print("=" * 80)

if __name__ == "__main__":
    main()
