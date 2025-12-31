"""
Health check endpoint
"""
from fastapi import APIRouter, Depends
from datetime import datetime
import requests

from backend.api.models.response import HealthResponse
from backend.dependencies import get_rag_pipeline
from backend.config import settings
from src.pipeline.rag_pipeline import ThuTucRAGPipeline


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    rag_pipeline: ThuTucRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Health check endpoint
    Checks status of Qdrant and Ollama services
    """
    # Check Qdrant status
    qdrant_status = "unknown"
    try:
        if rag_pipeline.retrieval_pipeline and rag_pipeline.retrieval_pipeline.vector_store:
            # Try to get collection info
            collection_info = rag_pipeline.retrieval_pipeline.vector_store.get_collection_stats()
            qdrant_status = "connected" if collection_info else "disconnected"
        else:
            qdrant_status = "not_initialized"
    except Exception as e:
        qdrant_status = f"error: {str(e)[:50]}"

    # Check Ollama status
    ollama_status = "unknown"
    try:
        response = requests.get(f"{settings.ollama_url}/api/tags", timeout=2)
        ollama_status = "connected" if response.status_code == 200 else "disconnected"
    except Exception as e:
        ollama_status = f"error: {str(e)[:50]}"

    # Determine overall status
    overall_status = "healthy"
    if "error" in qdrant_status or "error" in ollama_status:
        overall_status = "degraded"
    if "disconnected" in qdrant_status or "disconnected" in ollama_status:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        qdrant_status=qdrant_status,
        ollama_status=ollama_status,
        version=settings.version,
        timestamp=datetime.now().isoformat()
    )
