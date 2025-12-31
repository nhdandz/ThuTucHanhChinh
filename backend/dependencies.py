"""
Dependency injection for RAG pipeline and services
"""
import sys
import os
from functools import lru_cache

# Add src to path for importing RAG pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.pipeline.rag_pipeline import ThuTucRAGPipeline
from backend.config import settings
from backend.services.session_manager import SessionManager


@lru_cache()
def get_rag_pipeline() -> ThuTucRAGPipeline:
    """
    Get singleton RAG pipeline instance
    Initialized once at startup, reused across requests
    """
    print("Initializing RAG pipeline...")
    pipeline = ThuTucRAGPipeline(
        vector_store_path=settings.qdrant_path,
        collection_name=settings.collection_name,
        embedding_model=settings.embedding_model,
        llm_model=settings.llm_model,
        ollama_url=settings.ollama_url
    )
    print("RAG pipeline initialized successfully")
    return pipeline


@lru_cache()
def get_session_manager() -> SessionManager:
    """Get singleton session manager instance"""
    return SessionManager(ttl_seconds=settings.session_ttl_seconds)
