"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import settings
from backend.api.routes import health, chat, stats
from backend.middleware.error_handler import APIError, api_error_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager
    Handles startup and shutdown events
    """
    # Startup
    print("=" * 60)
    print(f"Starting {settings.app_name} v{settings.version}")
    print(f"CORS Origins: {settings.cors_origins}")
    print(f"Ollama URL: {settings.ollama_url}")
    print(f"Qdrant Path: {settings.qdrant_path}")
    print("=" * 60)

    yield

    # Shutdown
    print("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="API for 207 Thủ Tục Hành Chính Chatbot",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add global error handler
app.add_exception_handler(APIError, api_error_handler)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(stats.router)  # Sprint 2 statistics endpoints


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
        "stats": {
            "cache": "/api/stats/cache",
            "bm25": "/api/stats/bm25",
            "config": "/api/stats/config"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
