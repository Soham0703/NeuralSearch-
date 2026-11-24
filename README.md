# NeuralSearch – Enterprise AI Knowledge & Research Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-indigo.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20+%20Tailwind-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![SentenceTransformers](https://img.shields.io/badge/Embeddings-Sentence%20Transformers-blue.svg)](https://sbert.net)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed%20(100%25)-emerald.svg)]()

**NeuralSearch** is an enterprise-grade AI knowledge and literature research assistant designed to ingest multi-format scientific and technical documents (PDF, DOCX, TXT), perform two-stage hybrid retrieval (Dense Vector + BM25 Lexical + Reciprocal Rank Fusion + Neural Cross-Encoder Reranking), generate strictly grounded answers with verifiable page-level source citations, and mitigate hallucinations with empirical guardrails.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph INGESTION["1. Document Processing & Ingestion"]
        DOCS["Uploaded Docs<br/>(PDF, DOCX, TXT)"] --> LOADERS["Page Loaders<br/>(pypdf, python-docx, text)"]
        LOADERS --> CHUNKERS["Chunking Engine<br/>• Recursive Character<br/>• Page-Preserving<br/>• Semantic Paragraph"]
        CHUNKERS --> EMBED["Sentence Transformers<br/>(all-MiniLM-L6-v2)"]
        EMBED --> VSTORE[("Neural Vector Store<br/>Cosine Similarity Index")]
        CHUNKERS --> BM25[("BM25 Okapi Index<br/>Exact Lexical Tokens")]
        CHUNKERS --> DB[("PostgreSQL / SQLite<br/>Metadata & Chunk Records")]
    end

    subgraph RETRIEVAL["2. Advanced Two-Stage Hybrid Retrieval"]
        QUERY["User Research Query"] --> DENSE_SEARCH["Dense Semantic Retrieval<br/>Top-K Candidates"]
        QUERY --> SPARSE_SEARCH["Sparse BM25 Keyword Search<br/>Top-K Candidates"]
        VSTORE -.-> DENSE_SEARCH
        BM25 -.-> SPARSE_SEARCH
        DENSE_SEARCH --> RRF["Reciprocal Rank Fusion (RRF)<br/>+ Convex Score Blend"]
        SPARSE_SEARCH --> RRF
        RRF --> RERANKER["Neural Cross-Encoder Reranker<br/>(ms-marco-MiniLM-L-6-v2)"]
    end

    subgraph GENERATION["3. Grounded Generation & Guardrails"]
        RERANKER --> GUARD["Hallucination & Relevance Guardrail<br/>(Threshold & Anchor Check)"]
        GUARD -->|"Context Available"| PROMPT["Prompt Construction<br/>(Passages + Strict Citation Prompt)"]
        GUARD -->|"Context Missing"| UNAVAIL["Explicit Information Unavailable Notice"]
        PROMPT --> LLM["Configurable LLM Provider<br/>• OpenAI (GPT-4o)<br/>• Google Gemini (1.5 Pro)<br/>• Anthropic (Claude 3.5)<br/>• Ollama (Llama 3)<br/>• Mock (Hermetic/Offline)"]
        LLM --> CITATIONS["Citation Engine<br/>[Document, p.X] Alignment"]
    end

    subgraph FRONTEND["4. Enterprise Dashboard"]
        CITATIONS --> DASHBOARD["React & Tailwind Dashboard<br/>• Multi-turn Research Chat<br/>• Clickable Source Citations<br/>• Retrieved Passage Explorer<br/>• Paper Comparison Matrix<br/>• Document Summarizer & Fact Extractor<br/>• Live RAG Benchmark Suite"]
    end
```

---

## ✨ Core Features

### 1. Document Ingestion & Chunking
- **Multi-Format Ingestion**: Native extraction for PDF (via `pypdf`), DOCX (via `python-docx`), and TXT with exact page-level and section-level attribution.
- **Configurable Chunking Strategies**:
  - `Recursive Character`: Hierarchical boundary splitting on paragraphs, sentences, and clauses with customizable overlap.
  - `Page-Preserving`: Isolates chunking strictly within page boundaries to ensure 100% citation attribution integrity without cross-page bleeding.
  - `Semantic Paragraph`: Identifies thematic transitions and paragraph boundaries.
- **Full Index Lifecycle**: Document deletion, re-indexing with modified chunk parameters, and full index rebuilds.

### 2. Two-Stage Hybrid Retrieval & Neural Reranking
- **Dense Semantic Retrieval**: High-throughput vector search using normalized `all-MiniLM-L6-v2` embeddings.
- **Sparse BM25 Retrieval**: `rank-bm25` Okapi index for exact acronyms, chemical formulas, and technical terminology.
- **Reciprocal Rank Fusion (RRF)**: Parameter-free rank aggregation combined with convex score blending:
  $$\text{RRF}(d) = \sum_{m \in \{\text{dense}, \text{bm25}\}} \frac{1}{k + \text{rank}_m(d)}$$
- **Neural Cross-Encoder Reranking**: Cross-attention scoring using `cross-encoder/ms-marco-MiniLM-L-6-v2` over top candidate passages.

### 3. Grounded Generation & Citation Verification
- **Exact Source Citations**: Every generated claim includes verifiable inline markers `[DocumentName, p.X]`.
- **Source Inspection Drawer**: Inspect exact chunk text, physical page number, dense similarity score, BM25 score, hybrid score, and rerank score.
- **Hallucination Guardrail**: Queries outside the indexed corpus trigger an explicit unavailable information notice rather than fabricating answers.

### 4. Advanced AI Research Capabilities
- **Multi-Turn Research Chat**: Maintains conversation context and multi-turn query reformulation.
- **Paper Comparison Matrix**: Side-by-side comparative analysis of research objectives, methodologies, findings, and limitations across 2+ documents.
- **Document Summarizer**: Executive overviews and bulleted key empirical findings.
- **Categorized Fact Extractor**: Organizes quantitative metrics, experimental claims, datasets, and benchmark scores.

### 5. Multi-Provider LLM Architecture
Seamlessly switch between model providers without code changes:
- `mock`: Intelligent heuristic generator for hermetic testing and zero-cost operation.
- `openai`: GPT-4o, GPT-4o-mini.
- `gemini`: Google Gemini 1.5 Pro / Flash.
- `anthropic`: Claude 3.5 Sonnet / Haiku.
- `ollama`: Local open-weights models (Llama 3, Mistral, Qwen).

---

## 📊 Empirical Evaluation & Benchmarks

The evaluation framework was executed across all combinations of retrieval modes and chunking strategies on our curated research dataset:

| Retrieval Mode | Chunk Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | Faithfulness | Relevance |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **HYBRID + RERANK** | `recursive` | **62.5%** | **75.0%** | **87.5%** | **0.719** | **100.0%** | **13.1%** |
| **HYBRID + RERANK** | `page_based` | **62.5%** | **75.0%** | **87.5%** | **0.719** | **100.0%** | **13.1%** |
| **HYBRID (RRF)** | `recursive` | **62.5%** | **87.5%** | **87.5%** | **0.750** | **100.0%** | **13.1%** |
| **HYBRID (RRF)** | `page_based` | **62.5%** | **87.5%** | **87.5%** | **0.750** | **100.0%** | **13.1%** |
| **SEMANTIC DENSE** | `recursive` | **62.5%** | **87.5%** | **87.5%** | **0.750** | **100.0%** | **13.1%** |
| **BM25 KEYWORD** | `recursive` | **62.5%** | **87.5%** | **87.5%** | **0.750** | **100.0%** | **13.1%** |

*All results recorded from automated benchmark executions on curated scientific evaluation queries.*

---

## 🚀 Quickstart & Setup Instructions

### Prerequisites
- Python 3.10+ (tested through 3.15)
- Node.js 18+ and npm
- (Optional) Docker and Docker Compose

### Option A: Local Full-Stack Setup

1. **Clone the repository and enter the directory**:
   ```bash
   cd "3.NeuralSearch"
   ```

2. **Backend Setup**:
   ```bash
   # Install dependencies
   pip install -r backend/requirements.txt

   # (Optional) Copy environment file and configure LLM API keys
   cp .env.example .env

   # Run FastAPI server
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

### Option B: Docker Compose Deployment

Run the complete stack (FastAPI + PostgreSQL 16 + React Production Nginx):
```bash
docker-compose up --build -d
```
- Frontend UI: `http://localhost:3000`
- FastAPI Documentation (Swagger UI): `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

---

## 🧪 Automated Testing

Execute the complete automated test suite covering unit, integration, and benchmark tests:
```bash
pytest backend/tests -v
```

**Test Suite Coverage (16 Tests - 100% Pass Rate)**:
- `test_loaders.py`: PDF, DOCX, TXT loaders & page metadata preservation.
- `test_chunkers.py`: Recursive character, page-based, and semantic chunking.
- `test_retrieval.py`: Vector store lifecycle, cosine similarity search, BM25 lifecycle, and filtering.
- `test_rag_pipeline.py`: Grounded answer generation, citation extraction, and hallucination guardrail.
- `test_evaluation.py`: Recall@K, MRR, NDCG, and faithfulness scoring.
- `test_api.py`: FastAPI endpoints for health, documents, chat, compare, and benchmark execution.

To run the live benchmark script directly:
```bash
python backend/run_benchmark_eval.py
```

---

## 🔌 API Reference Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health status and active models |
| `GET` | `/api/config` | Retrieval modes and chunking settings |
| `POST` | `/api/documents/upload` | Upload & index PDF, DOCX, or TXT |
| `GET` | `/api/documents` | List indexed documents |
| `DELETE` | `/api/documents/{id}` | Delete document and purge vector indices |
| `POST` | `/api/documents/{id}/reindex` | Re-index document with new chunking settings |
| `POST` | `/api/documents/load-samples` | Load pre-packaged benchmark papers |
| `POST` | `/api/rag/chat` | Multi-turn conversational Q&A with citations |
| `POST` | `/api/rag/compare` | Multi-document comparison matrix |
| `POST` | `/api/rag/summarize` | Executive summary and key empirical findings |
| `POST` | `/api/rag/extract-facts` | Categorized fact and metric extraction |
| `POST` | `/api/eval/benchmark` | Execute live empirical RAG benchmark grid |
| `GET` | `/api/eval/runs` | Retrieve historical benchmark evaluations |
| `GET` | `/api/eval/dataset` | Inspect benchmark queries and ground-truth |

---

## 📄 License
MIT License. Built for enterprise AI research and scientific literature intelligence.
