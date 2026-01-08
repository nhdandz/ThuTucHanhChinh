"""
Chat service - Core business logic
Handles query processing, multiple procedures detection, and behavior requirements
"""
import uuid
import sys
from typing import List, Optional
from datetime import datetime
from pathlib import Path

# Add src/retrieval to path for conversation_context import
# Use resolve() to get absolute path that works with uvicorn
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent
sys.path.insert(0, str(_project_root / "src" / "retrieval"))

from src.pipeline.rag_pipeline import ThuTucRAGPipeline
from backend.services.session_manager import SessionManager
from backend.api.models.request import ChatQueryRequest
from backend.api.models.response import (
    ChatQueryResponse,
    ChatMessage,
    SourceCitation
)
from backend.config import settings
from conversation_context import extract_conversation_context


class ChatService:
    """
    Business logic for chat operations
    Wraps ThuTucRAGPipeline with session management and behavioral logic
    """

    def __init__(self, rag_pipeline: ThuTucRAGPipeline, session_manager: SessionManager):
        self.rag_pipeline = rag_pipeline
        self.session_manager = session_manager

    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        include_sources: bool = True,
        include_structured: bool = True
    ) -> ChatQueryResponse:
        """
        Main query processing with behavioral logic

        Logic flow:
        1. Create/get session
        2. Call RAG pipeline for answer generation
        3. Detect multiple procedures scenario
        4. Generate appropriate response
        5. Save to session history
        6. Return response
        """
        # Step 1: Create or get session
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG: Received session_id: {session_id}")

        if session_id is None:
            session_id = self.session_manager.create_session()
            print(f"   ✨ Created NEW session: {session_id}")
        else:
            existing_session = self.session_manager.get_session(session_id)
            if existing_session:
                print(f"   ✅ Found EXISTING session with {len(existing_session.messages)} messages")
            else:
                print(f"   ⚠️ Session NOT FOUND - creating new session")
                session_id = self.session_manager.create_session()
                print(f"   ✨ Created NEW session: {session_id}")

        message_id = str(uuid.uuid4())

        # Step 2: Save user message to session
        user_message = ChatMessage(
            message_id=str(uuid.uuid4()),
            role="user",
            content=query,
            timestamp=datetime.now().isoformat()
        )
        self.session_manager.add_message(session_id, user_message)

        # Step 2.5: Extract conversation context (NEW)
        conversation_context = None
        if settings.enable_conversation_context:
            # Get recent history (excluding current user message we just added)
            history = self.session_manager.get_history(session_id)
            print(f"   🔍 DEBUG: Total history length: {len(history)}")
            # Remove last message (the current user query we just added)
            history_before_current = history[:-1] if len(history) > 0 else []
            print(f"   🔍 DEBUG: History before current: {len(history_before_current)} messages")

            if history_before_current:
                print(f"   🔍 DEBUG: Attempting to extract context from {len(history_before_current)} messages")
                conversation_context = extract_conversation_context(
                    messages=history_before_current,
                    depth=settings.conversation_history_depth
                )
                if conversation_context:
                    print(f"   📚 Using conversation context: last procedure = {conversation_context.last_procedure_name}")
                else:
                    print(f"   ⚠️ DEBUG: extract_conversation_context returned None")
            else:
                print(f"   ⚠️ DEBUG: No history before current message, skipping context extraction")

        try:
            # Step 3: Call RAG pipeline with configured parameters
            print(f"Processing query: {query}")
            rag_result = self.rag_pipeline.answer_question(
                question=query,
                top_k_parent=settings.top_k_parent,
                top_k_child=settings.top_k_child,
                top_k_final=settings.top_k_final,
                conversation_context=conversation_context
            )

            # Step 4: Extract sources from rag_result
            sources = self._extract_sources(rag_result) if include_sources else []

            # Step 4.5: Check if clarification is needed (multiple similar procedures)
            clarification_needed, clarification_msg = self._check_clarification_needed(sources)

            # Override answer if clarification needed
            final_answer = clarification_msg if clarification_needed else (
                rag_result.answer if hasattr(rag_result, 'answer') else str(rag_result)
            )

            # Step 5: Generate direct answer response
            response = ChatQueryResponse(
                session_id=session_id,
                message_id=message_id,
                query=query,
                answer=final_answer,
                structured_data=rag_result.structured_data if (include_structured and hasattr(rag_result, 'structured_data')) else None,
                sources=sources,
                confidence=rag_result.confidence if hasattr(rag_result, 'confidence') else 0.0,
                intent=rag_result.intent if hasattr(rag_result, 'intent') else "unknown",
                timestamp=datetime.now().isoformat()
            )

            # Step 7: Save assistant message to session
            assistant_message = ChatMessage(
                message_id=message_id,
                role="assistant",
                content=response.answer,
                structured_data=response.structured_data,
                sources=sources,
                timestamp=response.timestamp
            )
            self.session_manager.add_message(session_id, assistant_message)

            # Debug: Verify message was saved
            current_history = self.session_manager.get_history(session_id)
            print(f"   ✅ DEBUG: Assistant message saved. Total history now: {len(current_history)} messages")
            for i, msg in enumerate(current_history):
                print(f"      Message {i+1}: role={msg.role}, content_preview={msg.content[:50]}...")

            return response

        except Exception as e:
            print(f"Error processing query: {e}")
            # Return error response
            error_message = "Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn. Vui lòng thử lại."

            error_response = ChatQueryResponse(
                session_id=session_id,
                message_id=message_id,
                query=query,
                answer=error_message,
                structured_data=None,
                sources=[],
                confidence=0.0,
                intent="error",
                timestamp=datetime.now().isoformat()
            )

            # Save error message
            assistant_message = ChatMessage(
                message_id=message_id,
                role="assistant",
                content=error_message,
                timestamp=datetime.now().isoformat()
            )
            self.session_manager.add_message(session_id, assistant_message)

            return error_response

    def _extract_sources(self, rag_result) -> List[SourceCitation]:
        """Extract source citations from RAG result"""
        sources = []

        if not hasattr(rag_result, 'sources'):
            return sources

        for source in rag_result.sources:
            sources.append(SourceCitation(
                chunk_id=source.chunk_id,
                thu_tuc_name=source.thu_tuc_name,
                thu_tuc_code=source.thu_tuc_code,
                chunk_type=source.chunk_type if hasattr(source, 'chunk_type') else 'unknown',
                relevance_score=source.relevance_score,
                content_snippet=source.content_snippet[:200] + "..." if len(source.content_snippet) > 200 else source.content_snippet
            ))

        return sources

    def _check_clarification_needed(self, sources: List[SourceCitation]) -> tuple[bool, str]:
        """
        Check if query needs clarification due to multiple similar procedures

        Returns:
            (clarification_needed, clarification_message)
        """
        if not sources or len(sources) < 3:
            return False, ""

        # Group sources by procedure code
        procedures = {}
        for source in sources[:5]:  # Check top 5 sources
            code = source.thu_tuc_code
            if code not in procedures:
                procedures[code] = {
                    'name': source.thu_tuc_name,
                    'code': code,
                    'max_score': source.relevance_score,
                    'count': 0
                }
            procedures[code]['count'] += 1
            procedures[code]['max_score'] = max(procedures[code]['max_score'], source.relevance_score)

        # Check if we have multiple procedures with similar scores
        if len(procedures) >= 3:
            sorted_procs = sorted(procedures.values(), key=lambda x: x['max_score'], reverse=True)
            top_score = sorted_procs[0]['max_score']
            third_score = sorted_procs[2]['max_score']

            # If top 3 procedures have very similar scores (within 0.05), ask for clarification
            if top_score - third_score < 0.05:
                # Generate clarification message
                msg = "Tôi tìm thấy nhiều thủ tục liên quan. Bạn muốn biết về thủ tục nào?\n\n"
                for i, proc in enumerate(sorted_procs[:5], 1):
                    msg += f"{i}. {proc['name']} (Mã: {proc['code']})\n"
                msg += "\nVui lòng cung cấp tên hoặc mã thủ tục để tôi trả lời chính xác hơn."

                return True, msg

        return False, ""
