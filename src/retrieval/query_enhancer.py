#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Query Enhancement - Stage 1 of Retrieval Pipeline
Uses Ollama LLM to enhance and expand queries
"""

import sys
import re
import json
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Procedure code pattern (e.g., 1.013133, 2.002767, 3.000423)
PROCEDURE_CODE_PATTERN = r'\b\d+\.\d{5,6}\b'

# Intent mapping for query classification
INTENT_MAPPING = {
    "documents": ["giấy tờ cần nộp", "hồ sơ bao gồm", "văn bản nộp", "tài liệu cần", "nộp gì"],
    "requirements": ["điều kiện", "yêu cầu", "ai được", "đối tượng", "được làm", "được phép"],
    "process": ["trình tự", "các bước", "làm thế nào", "quy trình", "cách thức"],
    "legal": ["căn cứ", "pháp lý", "luật", "nghị định", "thông tư", "quy định"],
    "timeline": ["thời gian", "bao lâu", "thời hạn", "mất bao lâu", "trong vòng", "ngày làm việc"],
    "fees": ["phí", "lệ phí", "chi phí", "tốn", "giá", "mất bao nhiêu"],
    "location": ["ở đâu", "địa chỉ", "nơi", "cơ quan nào", "đến đâu"]
}

# Negative patterns - if these appear, disqualify the intent
# Used to handle compound queries where "hồ sơ" appears but question is about timing/process
INTENT_EXCLUSIONS = {
    "documents": ["thời gian", "bao lâu", "thời hạn", "hình thức thông báo", "thông báo"]
}


@dataclass
class QueryInfo:
    """Enhanced query information"""
    original_query: str
    intent: str
    query_variations: List[str]
    entities: Dict[str, str]
    filters: Dict[str, str]
    exact_code: Optional[str] = None  # Detected procedure code (e.g., "1.013133")


class OllamaQueryEnhancer:
    """
    Query enhancer using Ollama LLM
    Detects intent, extracts entities, generates query variations
    """

    def __init__(
        self,
        model_name: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize query enhancer

        Args:
            model_name: Ollama LLM model (e.g., "qwen3:8b", "mistral", "llama3.1")
            ollama_url: Ollama server URL
        """
        print(f"🔄 Initializing Query Enhancer")
        print(f"   Model: {model_name}")
        print(f"   Server: {ollama_url}")

        self.model_name = model_name
        self.ollama_url = ollama_url
        self.generate_endpoint = f"{ollama_url}/api/generate"

        print(f"✅ Query Enhancer initialized!")

    def _call_ollama(self, prompt: str, system: Optional[str] = None) -> str:
        """Call Ollama LLM API"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3  # Low temperature for consistency
            }
        }

        if system:
            payload["system"] = system

        response = requests.post(
            self.generate_endpoint,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")

        return response.json()["response"].strip()

    def detect_intent(self, question: str) -> str:
        """
        Detect question intent using weighted keyword matching + LLM

        Args:
            question: User question

        Returns:
            Intent type (documents, requirements, process, etc.)
        """
        # Try multi-intent keyword scoring
        question_lower = question.lower()

        # Count matches for each intent
        intent_scores = {}
        for intent, keywords in INTENT_MAPPING.items():
            score = sum(1 for kw in keywords if kw in question_lower)

            # Apply exclusions - disqualify intent if exclusion keywords present
            if intent in INTENT_EXCLUSIONS:
                has_exclusion = any(excl in question_lower for excl in INTENT_EXCLUSIONS[intent])
                if has_exclusion:
                    score = 0  # Disqualify this intent

            if score > 0:
                intent_scores[intent] = score

        # Return intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            return best_intent

        # If no keyword match, use LLM
        prompt = f"""Câu hỏi của người dùng: "{question}"

Xác định intent (mục đích) của câu hỏi. Chọn MỘT trong các intent sau:
- documents: Hỏi về giấy tờ, hồ sơ cần nộp
- requirements: Hỏi về điều kiện, yêu cầu, đối tượng được làm
- process: Hỏi về quy trình, trình tự, các bước thực hiện
- legal: Hỏi về căn cứ pháp lý
- timeline: Hỏi về thời gian, thời hạn
- fees: Hỏi về phí, lệ phí
- location: Hỏi về địa chỉ, địa điểm
- overview: Hỏi tổng quan về thủ tục

Chỉ trả về TÊN INTENT, không giải thích.
Intent:"""

        try:
            intent = self._call_ollama(prompt).strip().lower()
            # Validate intent
            valid_intents = list(INTENT_MAPPING.keys()) + ["overview"]
            if intent in valid_intents:
                return intent
        except:
            pass

        # Default to overview
        return "overview"

    def extract_entities(self, question: str) -> Dict[str, str]:
        """
        Extract entities from question (procedure name, field, keywords)

        Args:
            question: User question

        Returns:
            Dictionary of extracted entities
        """
        prompt = f"""Trích xuất thông tin từ câu hỏi sau:
"{question}"

Hãy trích xuất:
1. thu_tuc_name: Tên thủ tục hành chính (nếu có)
2. linh_vuc: Lĩnh vực (VD: hộ tịch, đăng ký kinh doanh, xây dựng...)
3. keywords: Từ khóa chính

Trả về JSON với format:
{{
  "thu_tuc_name": "...",
  "linh_vuc": "...",
  "keywords": ["...", "..."]
}}

Chỉ trả về JSON, không giải thích."""

        try:
            response = self._call_ollama(prompt)
            # Extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                entities = json.loads(response[start:end])
                return entities
        except:
            pass

        # Default empty entities
        return {"thu_tuc_name": "", "linh_vuc": "", "keywords": []}

    def generate_query_variations(self, question: str, intent: str, num_variations: int = 3) -> List[str]:
        """
        Generate query variations for multi-query retrieval

        Args:
            question: Original question
            intent: Detected intent
            num_variations: Number of variations to generate

        Returns:
            List of query variations
        """
        prompt = f"""Câu hỏi gốc: "{question}"
Intent: {intent}

Hãy tạo {num_variations} variations (cách diễn đạt khác) của câu hỏi này để tìm kiếm hiệu quả hơn.

Yêu cầu:
1. Giữ nguyên ý nghĩa của câu hỏi gốc
2. Sử dụng từ đồng nghĩa
3. Thay đổi cấu trúc câu
4. Tập trung vào intent "{intent}"

Trả về JSON array:
["variation 1", "variation 2", "variation 3"]

Chỉ trả về JSON array, không giải thích."""

        try:
            response = self._call_ollama(prompt)
            # Extract JSON array
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end > start:
                variations = json.loads(response[start:end])
                return variations[:num_variations]
        except:
            pass

        # Fallback: simple variations
        return [
            question,
            question.replace("cần gì", "bao gồm những gì"),
            question.replace("làm thế nào", "quy trình")
        ][:num_variations]

    def _extract_procedure_code(self, question: str) -> Optional[str]:
        """
        Extract procedure code from query using regex pattern

        Args:
            question: User question

        Returns:
            Procedure code if found (e.g., "1.013133"), None otherwise
        """
        match = re.search(PROCEDURE_CODE_PATTERN, question)
        if match:
            return match.group(0)
        return None

    def _rewrite_query(self, question: str) -> str:
        """
        Rewrite complex queries into simplified form for better retrieval

        Removes filler words and question patterns, keeps domain-specific keywords

        Args:
            question: Original query

        Returns:
            Simplified query
        """
        # Filler words/patterns to remove
        filler_patterns = [
            r'^nếu\s+(tôi|mình|em)\s+',  # "Nếu tôi/mình/em"
            r'\s+thì\s+',  # " thì "
            r'\s+có\s+',  # " có " (when not part of domain term)
            r'(khác\s+gì|khác\s+nhau\s+như\s+thế\s+nào|sự\s+khác\s+biệt)',  # Comparison phrases
            r'(so\s+với|với)',  # "so với", "với"
            r'(bằng\s+cách\s+nào|như\s+thế\s+nào)',  # How questions
            r'\?$',  # Question mark at end
        ]

        simplified = question.lower()

        # Remove filler patterns
        for pattern in filler_patterns:
            simplified = re.sub(pattern, ' ', simplified, flags=re.IGNORECASE)

        # Normalize spaces
        simplified = re.sub(r'\s+', ' ', simplified).strip()

        # If query became too short after cleaning, keep original
        if len(simplified.split()) < 3:
            return question

        return simplified

    def enhance_query(self, question: str) -> QueryInfo:
        """
        Main method: Enhance query with intent detection, entity extraction, variations

        Args:
            question: User question

        Returns:
            QueryInfo object with enhanced information
        """
        print(f"\n🔍 Enhancing query: '{question}'")

        # Step 0: Extract exact procedure code (if present)
        exact_code = self._extract_procedure_code(question)
        if exact_code:
            print(f"   ✅ Exact code detected: {exact_code}")

        # Step 0.5: Query rewriting for better retrieval
        rewritten_query = self._rewrite_query(question)
        if rewritten_query != question and rewritten_query.lower() != question.lower():
            print(f"   🔄 Query rewritten: '{rewritten_query}'")
            # Use rewritten query for intent detection and variations
            query_for_processing = rewritten_query
        else:
            query_for_processing = question

        # Step 1: Detect intent (use original for better context)
        intent = self.detect_intent(question)
        print(f"   Intent: {intent}")

        # Step 2: Extract entities (use original for completeness)
        entities = self.extract_entities(question)
        print(f"   Entities: {entities}")

        # Step 3: Generate variations (include rewritten query as first variation)
        if query_for_processing != question:
            variations = [query_for_processing] + self.generate_query_variations(question, intent, num_variations=2)
        else:
            variations = self.generate_query_variations(question, intent, num_variations=3)
        print(f"   Variations: {len(variations)} generated")

        # Step 4: Build filters for vector search
        filters = {}
        if intent != "overview":
            # Map intent to chunk_type (can be single string or list of strings)
            intent_to_chunk_type = {
                "documents": "child_documents",
                "requirements": "child_requirements",
                "process": "child_process",
                "timeline": ["child_process", "child_fees_timing"],  # Timeline needs both process steps AND detailed timing info
                "legal": "child_legal"
            }
            if intent in intent_to_chunk_type:
                filters["chunk_type"] = intent_to_chunk_type[intent]

        query_info = QueryInfo(
            original_query=question,
            intent=intent,
            query_variations=variations,
            entities=entities,
            filters=filters,
            exact_code=exact_code
        )

        return query_info


def test_query_enhancer():
    """Test query enhancer"""
    print("=" * 80)
    print("TEST QUERY ENHANCER")
    print("=" * 80)

    enhancer = OllamaQueryEnhancer(model_name="qwen3:8b")

    test_queries = [
        "Đăng ký kết hôn cần giấy tờ gì?",
        "Ai được phép đăng ký kinh doanh?",
        "Thủ tục xin giấy phép xây dựng mất bao lâu?",
        "Căn cứ pháp lý của thủ tục đăng ký hộ tịch là gì?"
    ]

    for query in test_queries:
        print()
        result = enhancer.enhance_query(query)
        print(f"   Filters: {result.filters}")
        print()

    print("=" * 80)


if __name__ == "__main__":
    test_query_enhancer()
