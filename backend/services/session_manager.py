"""
In-memory session management with TTL
For production: Replace with Redis
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from backend.api.models.response import ChatMessage


@dataclass
class ChatSession:
    """Chat session data model"""
    session_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)  # Store retrieval context

    def add_message(self, message: ChatMessage):
        """Add message to session"""
        self.messages.append(message)
        self.last_updated = datetime.now()

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if session is expired"""
        expiry_time = self.created_at + timedelta(seconds=ttl_seconds)
        return datetime.now() > expiry_time


class SessionManager:
    """
    In-memory session manager with TTL

    For production: Replace with Redis for:
    - Persistent storage
    - Multi-server support
    - Built-in TTL
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.sessions: Dict[str, ChatSession] = {}
        self.ttl_seconds = ttl_seconds

    def create_session(self) -> str:
        """Create new session and return session ID"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ChatSession(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get session by ID
        Returns None if session doesn't exist or is expired
        """
        session = self.sessions.get(session_id)

        if session is None:
            return None

        # Check if expired
        if session.is_expired(self.ttl_seconds):
            # Clean up expired session
            del self.sessions[session_id]
            return None

        return session

    def add_message(self, session_id: str, message: ChatMessage):
        """Add message to session history"""
        session = self.get_session(session_id)
        if session:
            session.add_message(message)

    def get_history(self, session_id: str) -> List[ChatMessage]:
        """Get full chat history for session"""
        session = self.get_session(session_id)
        return session.messages if session else []

    def delete_session(self, session_id: str):
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def cleanup_expired_sessions(self):
        """Cleanup all expired sessions"""
        expired_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if session.is_expired(self.ttl_seconds)
        ]

        for session_id in expired_sessions:
            del self.sessions[session_id]

        return len(expired_sessions)

    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self.sessions)

    def update_metadata(self, session_id: str, key: str, value):
        """Update session metadata"""
        session = self.get_session(session_id)
        if session:
            session.metadata[key] = value

    def get_metadata(self, session_id: str, key: str):
        """Get session metadata"""
        session = self.get_session(session_id)
        return session.metadata.get(key) if session else None
