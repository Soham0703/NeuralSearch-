import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), default="New Research Session")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.timestamp")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    search_mode = Column(String(30), default="hybrid")  # semantic, bm25, hybrid, hybrid_rerank
    citations = Column(JSON, default=list)
    retrieved_chunks = Column(JSON, default=list)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    dataset_name = Column(String(100), default="research_benchmark_v1")
    chunk_strategy = Column(String(50), default="recursive")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=100)
    retrieval_mode = Column(String(50), default="hybrid_rerank")
    recall_at_1 = Column(Float, default=0.0)
    recall_at_3 = Column(Float, default=0.0)
    recall_at_5 = Column(Float, default=0.0)
    mrr = Column(Float, default=0.0)
    faithfulness = Column(Float, default=0.0)
    answer_relevance = Column(Float, default=0.0)
    total_queries = Column(Integer, default=0)
    metrics_json = Column(JSON, default=dict)
