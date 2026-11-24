import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models.conversation import Conversation, Message
from backend.app.models.document import Document
from backend.app.schemas.rag import (
    QueryRequest, QueryResponse, Citation, RetrievedPassage,
    CompareRequest, CompareResponse, SummarizeRequest, SummarizeResponse,
    ExtractFactsRequest, ExtractFactsResponse
)
from backend.app.rag.hybrid_retriever import hybrid_retriever
from backend.app.rag.citation_engine import citation_engine
from backend.app.rag.llm_provider import get_llm_provider

logger = logging.getLogger("neuralsearch.rag_service")

class RAGService:
    """
    Enterprise RAG Orchestrator providing:
    - Conversational multi-turn question answering
    - Grounded attribution and strict hallucination guardrails
    - Multi-document research paper comparison
    - Document summarization & key fact extraction
    """
    def answer_query(self, request: QueryRequest, db: Session) -> QueryResponse:
        start_time = time.time()
        
        # 1. Manage or create conversation
        conv_id = request.conversation_id or str(uuid.uuid4())
        conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conversation:
            # Generate a title from the first 40 chars of query
            title = request.query[:45].strip() + ("..." if len(request.query) > 45 else "")
            conversation = Conversation(id=conv_id, title=title)
            db.add(conversation)
            db.commit()

        # 2. Retrieve relevant context passages
        search_mode = request.search_mode or "hybrid_rerank"
        passages: List[RetrievedPassage] = hybrid_retriever.retrieve(
            query=request.query,
            mode=search_mode,
            document_ids=request.document_ids,
            top_k=request.top_k or 6,
            rerank_top_k=request.rerank_top_k or 4
        )

        # 3. Guardrail: Check for unavailable context
        # Check query term overlap against retrieved text
        q_tokens = [w for w in request.query.lower().split() if len(w) > 3 and w not in {"what", "when", "where", "which", "explain", "describe", "compare"}]
        has_lexical_anchor = any(
            any(t in p.text.lower() for t in q_tokens)
            for p in passages
        ) if q_tokens else True

        if not passages or (passages and passages[0].final_score < 0.28) or not has_lexical_anchor:
            unavailable_text = (
                "I do not have sufficient information in the provided documents to answer this question. "
                "None of the uploaded research papers contain relevant context for this query. "
                "Please verify your uploaded documents or ask a question pertinent to their contents."
            )
            # Record user & assistant messages
            user_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="user",
                content=request.query,
                search_mode=search_mode
            )
            asst_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="assistant",
                content=unavailable_text,
                search_mode=search_mode,
                citations=[],
                retrieved_chunks=[]
            )
            db.add(user_msg)
            db.add(asst_msg)
            db.commit()

            latency_ms = round((time.time() - start_time) * 1000, 2)
            return QueryResponse(
                query=request.query,
                answer=unavailable_text,
                conversation_id=conv_id,
                citations=[],
                retrieved_passages=[],
                grounded=False,
                unavailable_info=True,
                search_mode=search_mode,
                provider=request.llm_provider or settings.DEFAULT_LLM_PROVIDER,
                model=request.llm_model or "default",
                latency_ms=latency_ms
            )

        # 4. Construct prompt with strict grounding and citation instructions
        context_blocks = []
        for idx, p in enumerate(passages):
            header = f"[Passage {idx + 1} | Doc: {p.document_name} | Page: {p.page_number}]"
            context_blocks.append(f"{header}\n{p.text}")
        context_str = "\n\n".join(context_blocks)

        system_instruction = (
            "You are NeuralSearch, an enterprise-grade AI research assistant specializing in scientific "
            "literature, technical documents, and empirical research. "
            "Your answers MUST be strictly grounded in the provided context passages. "
            "For EVERY factual statement, claim, metric, or finding you state, you MUST provide inline "
            "source citations in the exact format: [DocumentName, p.X] (e.g. [attention_is_all_you_need.pdf, p.3]). "
            "If the provided context does not contain sufficient information to answer the question, clearly state "
            "that the information is unavailable rather than fabricating an answer."
        )

        # Include recent conversation turns for context
        history_msgs = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.timestamp.desc()).limit(4).all()
        history_str = ""
        if history_msgs:
            history_blocks = []
            for h in reversed(history_msgs):
                history_blocks.append(f"{h.role.upper()}: {h.content[:200]}")
            history_str = "\nCONVERSATION HISTORY:\n" + "\n".join(history_blocks) + "\n"

        prompt = (
            f"{history_str}\n"
            f"CONTEXT PASSAGES:\n{context_str}\n\n"
            f"USER QUESTION: {request.query}\n\n"
            "RESEARCH ASSISTANT ANSWER (Grounded with [DocumentName, p.X] citations):"
        )

        # 5. Generate LLM response
        provider = get_llm_provider(request.llm_provider, request.llm_model)
        answer = provider.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=request.temperature or 0.1
        )

        # 6. Extract and validate citations
        citations, is_grounded = citation_engine.extract_citations(answer, passages)

        # 7. Persist messages
        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv_id,
            role="user",
            content=request.query,
            search_mode=search_mode
        )
        asst_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv_id,
            role="assistant",
            content=answer,
            search_mode=search_mode,
            citations=[c.dict() for c in citations],
            retrieved_chunks=[p.dict() for p in passages]
        )
        db.add(user_msg)
        db.add(asst_msg)
        db.commit()

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return QueryResponse(
            query=request.query,
            answer=answer,
            conversation_id=conv_id,
            citations=citations,
            retrieved_passages=passages,
            grounded=is_grounded,
            unavailable_info=False,
            search_mode=search_mode,
            provider=request.llm_provider or settings.DEFAULT_LLM_PROVIDER,
            model=request.llm_model or "default",
            latency_ms=latency_ms
        )

    def compare_documents(self, request: CompareRequest, db: Session) -> CompareResponse:
        """
        Executes multi-document research paper comparison across specified aspects.
        """
        docs = db.query(Document).filter(Document.id.in_(request.document_ids)).all()
        doc_map = {d.id: d.filename for d in docs}
        aspects = request.aspects or ["Objectives", "Methodology", "Key Results", "Limitations"]

        matrix: Dict[str, Dict[str, str]] = {}
        all_citations: List[Citation] = []
        provider = get_llm_provider(request.llm_provider)

        for aspect in aspects:
            matrix[aspect] = {}
            for doc in docs:
                # Retrieve passages specific to this aspect for this document
                passages = hybrid_retriever.retrieve(
                    query=f"{doc.filename} {aspect}",
                    mode="hybrid_rerank",
                    document_ids=[doc.id],
                    top_k=3,
                    rerank_top_k=2
                )
                if passages:
                    summary_prompt = (
                        f"CONTEXT:\n" + "\n".join([f"[{p.document_name}, p.{p.page_number}]: {p.text}" for p in passages]) + "\n\n"
                        f"Briefly summarize the '{aspect}' for document {doc.filename} in 1-2 sentences with inline citation [Doc, p.X]."
                    )
                    cell_text = provider.generate(summary_prompt)
                    cites, _ = citation_engine.extract_citations(cell_text, passages)
                    all_citations.extend(cites)
                else:
                    cell_text = f"Information regarding {aspect} not explicitly identified in indexed passages."
                matrix[aspect][doc.filename] = cell_text

        # Executive synthesis across all documents
        doc_names = list(doc_map.values())
        summary = (
            f"Comparative analysis conducted across {len(doc_names)} documents ({', '.join(doc_names)}) "
            f"evaluating {len(aspects)} key research dimensions. Each paper presents distinct contributions "
            f"as detailed in the matrix below."
        )

        return CompareResponse(
            comparison_matrix=matrix,
            executive_summary=summary,
            citations=all_citations[:8],
            document_names=doc_names
        )

    def summarize_document(self, request: SummarizeRequest, db: Session) -> SummarizeResponse:
        """
        Generates executive summary and bulleted key findings for a document.
        """
        doc = db.query(Document).filter(Document.id == request.document_id).first()
        if not doc:
            raise ValueError(f"Document {request.document_id} not found.")

        # Retrieve representative chunks
        passages = hybrid_retriever.retrieve(
            query=f"{doc.filename} abstract introduction conclusion key findings",
            mode="hybrid_rerank",
            document_ids=[doc.id],
            top_k=5,
            rerank_top_k=4
        )

        context_str = "\n\n".join([f"[{p.document_name}, p.{p.page_number}]: {p.text}" for p in passages])
        prompt = (
            f"DOCUMENT: {doc.filename}\n"
            f"CONTEXT:\n{context_str}\n\n"
            f"Provide a comprehensive structured summary of {doc.filename}:\n"
            f"1. Executive Summary (2-3 sentences with citations)\n"
            f"2. Key Findings (3 bullet points with citations [Doc, p.X])"
        )
        provider = get_llm_provider(request.llm_provider)
        response_text = provider.generate(prompt)

        # Parse key findings
        key_findings = []
        for line in response_text.split("\n"):
            line_str = line.strip()
            if line_str.startswith("-") or (len(line_str) > 2 and line_str[0].isdigit() and line_str[1] in [".", ")"]):
                clean_finding = line_str.lstrip("- 0123456789.)").strip()
                if clean_finding:
                    key_findings.append(clean_finding)

        if not key_findings and passages:
            key_findings = [p.text[:120] + f"... [{doc.filename}, p.{p.page_number}]" for p in passages[:3]]

        citations, _ = citation_engine.extract_citations(response_text, passages)

        return SummarizeResponse(
            document_id=doc.id,
            document_name=doc.filename,
            summary=response_text,
            key_findings=key_findings[:5],
            citations=citations
        )

    def extract_facts(self, request: ExtractFactsRequest, db: Session) -> ExtractFactsResponse:
        """
        Extracts verified facts, metrics, and quantitative results organized by category.
        """
        categories = request.categories or ["Key Metrics", "Methodology Claims", "Datasets Used", "Quantitative Results"]
        facts_by_category: Dict[str, List[Dict[str, Any]]] = {}
        all_citations: List[Citation] = []
        provider = get_llm_provider(request.llm_provider)

        for cat in categories:
            passages = hybrid_retriever.retrieve(
                query=f"{cat} experimental results numerical benchmark evaluation",
                mode="hybrid_rerank",
                document_ids=request.document_ids,
                top_k=4,
                rerank_top_k=3
            )
            cat_facts = []
            for p in passages:
                prompt = (
                    f"CONTEXT [{p.document_name}, p.{p.page_number}]:\n{p.text}\n\n"
                    f"Extract 1 specific factual claim or metric related to '{cat}' from this passage. Include citation [{p.document_name}, p.{p.page_number}]."
                )
                fact_text = provider.generate(prompt)
                cat_facts.append({
                    "fact": fact_text.strip(),
                    "document_name": p.document_name,
                    "page_number": p.page_number,
                    "score": p.final_score
                })
            facts_by_category[cat] = cat_facts
            cites, _ = citation_engine.extract_citations("", passages)
            all_citations.extend(cites)

        return ExtractFactsResponse(
            facts_by_category=facts_by_category,
            citations=all_citations[:8]
        )

rag_service = RAGService()
