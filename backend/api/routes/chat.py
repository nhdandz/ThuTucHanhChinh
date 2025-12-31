"""
Chat endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from backend.api.models.request import ChatQueryRequest
from backend.api.models.response import ChatQueryResponse, ChatHistoryResponse, ChatMessage
from backend.services.chat_service import ChatService
from backend.services.session_manager import SessionManager
from backend.dependencies import get_rag_pipeline, get_session_manager
from src.pipeline.rag_pipeline import ThuTucRAGPipeline


router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_chat_service(
    rag_pipeline: ThuTucRAGPipeline = Depends(get_rag_pipeline),
    session_manager: SessionManager = Depends(get_session_manager)
) -> ChatService:
    """Dependency injection for ChatService"""
    return ChatService(rag_pipeline, session_manager)


@router.post("/query", response_model=ChatQueryResponse)
def chat_query(
    request: ChatQueryRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Primary chat endpoint for single query processing

    Process user query and return answer with optional:
    - Source citations
    - Structured data (JSON)
    - Multiple procedures selection (if applicable)
    """
    try:
        response = chat_service.process_query(
            query=request.query,
            session_id=request.session_id,
            include_sources=request.include_sources,
            include_structured=request.include_structured
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Retrieve chat history for a session
    """
    session = session_manager.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return ChatHistoryResponse(
        session_id=session_id,
        messages=session.messages,
        created_at=session.created_at.isoformat(),
        last_updated=session.last_updated.isoformat()
    )


@router.delete("/session/{session_id}")
def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Clear a session's chat history
    """
    session_manager.delete_session(session_id)
    return {"message": "Session deleted successfully"}


@router.get("/stats")
def get_stats(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get chat statistics
    """
    return {
        "active_sessions": session_manager.get_session_count(),
        "ttl_seconds": session_manager.ttl_seconds
    }
