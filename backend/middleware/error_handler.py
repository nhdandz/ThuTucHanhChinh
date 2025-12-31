"""
Global error handling middleware
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime


class APIError(Exception):
    """Base API error"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class QueryProcessingError(APIError):
    """RAG pipeline processing error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class InvalidQueryError(APIError):
    """Invalid user query"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class SessionNotFoundError(APIError):
    """Session not found"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class OllamaConnectionError(APIError):
    """Ollama server connection error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=503)


async def api_error_handler(request: Request, exc: APIError):
    """Global error handler for APIError"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "timestamp": datetime.now().isoformat()
        }
    )
