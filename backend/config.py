"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration settings"""

    # Ollama configuration
    ollama_url: str = "http://localhost:11434"
    embedding_model: str = "bge-m3"
    llm_model: str = "qwen3:8b"
    reranker_model: str = "bge-reranker-v2-m3"

    # Qdrant configuration
    qdrant_path: str = "/home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag/qdrant_storage"
    collection_name: str = "thu_tuc_hanh_chinh"  # Actual collection name in Qdrant
    embedding_dim: int = 1024

    # Session configuration
    session_ttl_seconds: int = 3600  # 1 hour

    # CORS configuration
    cors_origins: List[str] = ["http://localhost:3000"]

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # App metadata
    app_name: str = "Thu Tuc RAG API"
    version: str = "2.0.0"  # Updated for Sprint 2 features

    # === Sprint 2 Features Configuration ===

    # BM25 Search Configuration
    enable_bm25: bool = True  # Enable BM25 keyword search
    bm25_k1: float = 1.5  # BM25 term frequency saturation parameter
    bm25_b: float = 0.75  # BM25 length normalization parameter

    # Semantic Cache Configuration
    enable_cache: bool = True  # Enable semantic caching
    cache_max_size: int = 100  # Maximum number of cached queries
    cache_ttl_hours: float = 24.0  # Cache entry expiration time (hours)
    cache_similarity_threshold: float = 0.92  # Minimum similarity for cache hit

    # Cross-Encoder Reranking Configuration
    enable_reranker: bool = True  # Enable ensemble reranking
    use_cross_encoder: bool = False  # Disable actual cross-encoder (use ensemble only)
    reranker_semantic_weight: float = 0.55  # Weight for semantic scores
    reranker_bm25_weight: float = 0.35  # Weight for BM25 scores
    reranker_ce_weight: float = 0.10  # Weight for cross-encoder scores

    # Retrieval Pipeline Configuration
    # NOTE: Now DEFAULT values - overridden by intent-based context settings
    top_k_parent: int = 5  # Fallback if intent unknown
    top_k_child: int = 100  # Number of child chunks to retrieve (before reranking)
    top_k_final: int = 5  # Fallback if intent unknown

    # Answer Generation Configuration
    enable_structured_output: bool = False  # CHANGED: Now controlled by intent-based settings (user confirmed frontend doesn't use structured_data)

    # Intent-Based Context Optimization (Sprint 3)
    enable_intent_based_context: bool = True  # Enable dynamic context assembly based on query intent
    log_context_stats: bool = True  # Log context size and token estimates for monitoring

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
