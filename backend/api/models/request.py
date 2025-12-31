"""
Pydantic request models for API endpoints
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ChatQueryRequest(BaseModel):
    """Request model for chat query"""
    query: str = Field(..., min_length=1, max_length=500, description="User question")
    session_id: Optional[str] = Field(None, description="Session ID for chat history")
    include_sources: bool = Field(True, description="Include source citations")
    include_structured: bool = Field(True, description="Include structured JSON data")

    @field_validator('query')
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Sanitize query input"""
        # Remove excessive whitespace
        v = ' '.join(v.split())

        # Check for potentially malicious patterns
        malicious_patterns = ['<script>', 'javascript:', '<iframe>']
        for pattern in malicious_patterns:
            if pattern.lower() in v.lower():
                raise ValueError('Invalid query content detected')

        return v
