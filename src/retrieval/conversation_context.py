#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Conversation Context Extraction
Extracts relevant information from chat history for query contextualization
"""

from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class ConversationContext:
    """Extracted conversation context for query rewriting"""
    recent_turns: List[Dict[str, str]]  # [{role, content, procedure_name, procedure_code}]
    last_procedure_name: Optional[str] = None
    last_procedure_code: Optional[str] = None


def extract_conversation_context(
    messages: List,  # List[ChatMessage]
    depth: int = 2
) -> Optional[ConversationContext]:
    """
    Extract conversation context from chat history

    Args:
        messages: List of ChatMessage objects from session
        depth: Number of recent message PAIRS to consider (user + assistant = 1 pair)

    Returns:
        ConversationContext if history exists, None otherwise
    """
    print(f"      🔍 extract_conversation_context: Received {len(messages)} messages")

    if not messages or len(messages) < 2:
        print(f"      ⚠️ extract_conversation_context: Not enough messages (need >= 2)")
        return None

    # Get last N message pairs (user + assistant)
    # Each pair = 2 messages, so we need depth * 2 messages
    recent_messages = messages[-(depth * 2):]

    # Extract procedure info from assistant messages (they have sources/structured_data)
    last_procedure_name = None
    last_procedure_code = None

    # Build turn list and extract procedure info
    recent_turns = []

    for msg in recent_messages:
        turn = {
            "role": msg.role,
            "content": msg.content
        }

        # If assistant message, try to extract procedure info
        if msg.role == "assistant":
            print(f"      🔍 Checking assistant message for procedure info...")
            print(f"         hasattr sources: {hasattr(msg, 'sources')}")
            if hasattr(msg, 'sources'):
                print(f"         sources value: {msg.sources}")
                print(f"         sources length: {len(msg.sources) if msg.sources else 0}")

            # Try sources first (most reliable)
            if hasattr(msg, 'sources') and msg.sources and len(msg.sources) > 0:
                last_procedure_name = msg.sources[0].thu_tuc_name
                last_procedure_code = msg.sources[0].thu_tuc_code
                turn["procedure_name"] = last_procedure_name
                turn["procedure_code"] = last_procedure_code
                print(f"         ✅ Found via sources: {last_procedure_name} ({last_procedure_code})")

            # Try structured_data as fallback
            elif hasattr(msg, 'structured_data') and msg.structured_data:
                print(f"         🔍 Checking structured_data: {msg.structured_data}")
                if "ten_thu_tuc" in msg.structured_data:
                    last_procedure_name = msg.structured_data["ten_thu_tuc"]
                    turn["procedure_name"] = last_procedure_name
                if "ma_thu_tuc" in msg.structured_data:
                    last_procedure_code = msg.structured_data["ma_thu_tuc"]
                    turn["procedure_code"] = last_procedure_code
                print(f"         ✅ Found via structured_data")
            else:
                print(f"         ❌ No procedure info found in this assistant message")

        recent_turns.append(turn)

    result = ConversationContext(
        recent_turns=recent_turns,
        last_procedure_name=last_procedure_name,
        last_procedure_code=last_procedure_code
    )

    print(f"      📊 Extracted context: procedure={last_procedure_name}, code={last_procedure_code}")
    return result


def format_conversation_history(context: ConversationContext) -> str:
    """
    Format conversation context for LLM prompt

    Args:
        context: ConversationContext object

    Returns:
        Formatted history string for prompt
    """
    if not context or not context.recent_turns:
        return "Không có lịch sử hội thoại."

    history_lines = []
    for i, turn in enumerate(context.recent_turns, 1):
        role_label = "Người dùng" if turn["role"] == "user" else "Trợ lý"
        history_lines.append(f"{role_label}: {turn['content']}")

        # Add procedure info if available (for assistant turns)
        if turn["role"] == "assistant" and "procedure_name" in turn:
            history_lines.append(f"  (Thủ tục: {turn['procedure_name']} - Mã: {turn.get('procedure_code', 'N/A')})")

    return "\n".join(history_lines)
