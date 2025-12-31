"""
Pydantic response models for API endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SourceCitation(BaseModel):
    """Source citation model"""
    chunk_id: str = Field(..., description="Chunk ID")
    thu_tuc_name: str = Field(..., description="Thủ tục name")
    thu_tuc_code: str = Field(..., description="Thủ tục code")
    chunk_type: str = Field(..., description="Chunk type (parent/child_documents/etc)")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score")
    content_snippet: str = Field(..., description="Content snippet preview")


class ChatQueryResponse(BaseModel):
    """Response model for chat query"""
    session_id: str = Field(..., description="Session ID")
    message_id: str = Field(..., description="Message ID")
    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Natural language answer")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Structured JSON data")
    sources: List[SourceCitation] = Field(default_factory=list, description="Source citations")
    confidence: float = Field(..., ge=0, le=1, description="Answer confidence score")
    intent: str = Field(..., description="Detected intent")
    timestamp: str = Field(..., description="ISO format timestamp")


class ChatMessage(BaseModel):
    """Single chat message"""
    message_id: str
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    sources: Optional[List[SourceCitation]] = None
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    session_id: str
    messages: List[ChatMessage]
    created_at: str
    last_updated: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    qdrant_status: str
    ollama_status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    timestamp: str
