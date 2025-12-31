"""
Statistics endpoints for monitoring Sprint 2 features
"""
from fastapi import APIRouter, Depends
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from backend.dependencies import get_rag_pipeline
from backend.config import settings
from src.pipeline.rag_pipeline import ThuTucRAGPipeline


router = APIRouter(prefix="/api/stats", tags=["statistics"])


class CacheStatsResponse(BaseModel):
    """Cache statistics response model"""
    size: int
    max_size: int
    hits: int
    misses: int
    hit_rate: float
    evictions: int
    expired: int
    total_queries: int
    enabled: bool
    timestamp: str


class PipelineConfigResponse(BaseModel):
    """Pipeline configuration response model"""
    # BM25 configuration
    bm25_enabled: bool
    bm25_k1: float
    bm25_b: float

    # Cache configuration
    cache_enabled: bool
    cache_max_size: int
    cache_ttl_hours: float
    cache_similarity_threshold: float

    # Reranker configuration
    reranker_enabled: bool
    use_cross_encoder: bool
    semantic_weight: float
    bm25_weight: float
    ce_weight: float

    # Retrieval configuration
    top_k_parent: int
    top_k_child: int
    top_k_final: int

    version: str
    timestamp: str


class BM25StatsResponse(BaseModel):
    """BM25 statistics response model"""
    enabled: bool
    is_built: bool
    num_docs: Optional[int] = None
    avg_doc_length: Optional[float] = None
    index_size: Optional[int] = None
    k1: float
    b: float
    timestamp: str


@router.get("/cache", response_model=CacheStatsResponse)
def get_cache_stats(
    rag_pipeline: ThuTucRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get semantic cache statistics

    Returns cache hit rate, size, evictions, and other metrics.
    Useful for monitoring cache performance and tuning parameters.
    """
    cache_stats = {
        "size": 0,
        "max_size": settings.cache_max_size,
        "hits": 0,
        "misses": 0,
        "hit_rate": 0.0,
        "evictions": 0,
        "expired": 0,
        "total_queries": 0,
        "enabled": settings.enable_cache
    }

    # Get cache stats from retrieval pipeline
    try:
        if (settings.enable_cache and
            hasattr(rag_pipeline, 'retrieval_pipeline') and
            rag_pipeline.retrieval_pipeline and
            hasattr(rag_pipeline.retrieval_pipeline, 'cache') and
            rag_pipeline.retrieval_pipeline.cache):

            cache = rag_pipeline.retrieval_pipeline.cache
            cache_stats.update(cache.get_stats())

    except Exception as e:
        print(f"Error getting cache stats: {e}")

    return CacheStatsResponse(
        **cache_stats,
        timestamp=datetime.now().isoformat()
    )


@router.get("/bm25", response_model=BM25StatsResponse)
def get_bm25_stats(
    rag_pipeline: ThuTucRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get BM25 search statistics

    Returns BM25 index status, document count, and configuration.
    """
    bm25_stats = {
        "enabled": settings.enable_bm25,
        "is_built": False,
        "num_docs": None,
        "avg_doc_length": None,
        "index_size": None,
        "k1": settings.bm25_k1,
        "b": settings.bm25_b
    }

    # Get BM25 stats from retrieval pipeline
    try:
        if (settings.enable_bm25 and
            hasattr(rag_pipeline, 'retrieval_pipeline') and
            rag_pipeline.retrieval_pipeline and
            hasattr(rag_pipeline.retrieval_pipeline, 'bm25') and
            rag_pipeline.retrieval_pipeline.bm25):

            bm25 = rag_pipeline.retrieval_pipeline.bm25
            bm25_stats["is_built"] = bm25.is_built

            if bm25.is_built:
                bm25_stats["num_docs"] = bm25.num_docs
                bm25_stats["avg_doc_length"] = bm25.avg_doc_length
                bm25_stats["index_size"] = len(bm25.inverted_index)

    except Exception as e:
        print(f"Error getting BM25 stats: {e}")

    return BM25StatsResponse(
        **bm25_stats,
        timestamp=datetime.now().isoformat()
    )


@router.get("/config", response_model=PipelineConfigResponse)
def get_pipeline_config():
    """
    Get current pipeline configuration

    Returns all configuration parameters for Sprint 2 features:
    - BM25 search settings
    - Semantic cache settings
    - Reranker weights
    - Retrieval top-k values
    """
    return PipelineConfigResponse(
        # BM25 configuration
        bm25_enabled=settings.enable_bm25,
        bm25_k1=settings.bm25_k1,
        bm25_b=settings.bm25_b,

        # Cache configuration
        cache_enabled=settings.enable_cache,
        cache_max_size=settings.cache_max_size,
        cache_ttl_hours=settings.cache_ttl_hours,
        cache_similarity_threshold=settings.cache_similarity_threshold,

        # Reranker configuration
        reranker_enabled=settings.enable_reranker,
        use_cross_encoder=settings.use_cross_encoder,
        semantic_weight=settings.reranker_semantic_weight,
        bm25_weight=settings.reranker_bm25_weight,
        ce_weight=settings.reranker_ce_weight,

        # Retrieval configuration
        top_k_parent=settings.top_k_parent,
        top_k_child=settings.top_k_child,
        top_k_final=settings.top_k_final,

        version=settings.version,
        timestamp=datetime.now().isoformat()
    )


@router.post("/cache/clear")
def clear_cache(
    rag_pipeline: ThuTucRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Clear semantic cache

    Removes all cached entries. Useful for:
    - Testing
    - Forcing fresh retrieval
    - After data/model updates
    """
    try:
        if (settings.enable_cache and
            hasattr(rag_pipeline, 'retrieval_pipeline') and
            rag_pipeline.retrieval_pipeline and
            hasattr(rag_pipeline.retrieval_pipeline, 'cache') and
            rag_pipeline.retrieval_pipeline.cache):

            cache = rag_pipeline.retrieval_pipeline.cache
            cache.clear()

            return {
                "status": "success",
                "message": "Cache cleared successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Cache not available (disabled or not initialized)",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error clearing cache: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@router.post("/cache/clear-expired")
def clear_expired_cache(
    rag_pipeline: ThuTucRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Clear expired cache entries

    Removes only expired entries (TTL exceeded).
    Active entries are preserved.
    """
    try:
        if (settings.enable_cache and
            hasattr(rag_pipeline, 'retrieval_pipeline') and
            rag_pipeline.retrieval_pipeline and
            hasattr(rag_pipeline.retrieval_pipeline, 'cache') and
            rag_pipeline.retrieval_pipeline.cache):

            cache = rag_pipeline.retrieval_pipeline.cache
            expired_count = cache.clear_expired()

            return {
                "status": "success",
                "message": f"Cleared {expired_count} expired entries",
                "expired_count": expired_count,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Cache not available (disabled or not initialized)",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error clearing expired cache: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
