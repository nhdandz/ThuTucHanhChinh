#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Completeness Checker - Layer 2 Validation
Verifies that the answer addresses all aspects of the user's query
"""

import sys
import requests
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class QueryAspect:
    """A single aspect/requirement from the query"""
    aspect: str
    description: str
    is_addressed: bool
    evidence: str
    confidence: float


@dataclass
class CompletenessResult:
    """Result of completeness check"""
    query: str
    query_aspects: List[QueryAspect]
    total_aspects: int
    addressed_aspects: int
    completeness_score: float
    is_complete: bool
    missing_aspects: List[str]


class CompletenessChecker:
    """
    Checks if answer completely addresses all parts of the query

    Uses LLM to:
    1. Extract key aspects/requirements from query
    2. Verify each aspect is addressed in answer
    3. Calculate completeness score
    """

    def __init__(
        self,
        model_name: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434",
        completeness_threshold: float = 0.8
    ):
        """
        Initialize completeness checker

        Args:
            model_name: Ollama model name
            ollama_url: Ollama server URL
            completeness_threshold: Threshold for considering answer complete
        """
        print(f"🔄 Initializing Completeness Checker")
        print(f"   Model: {model_name}")
        print(f"   Completeness threshold: {completeness_threshold:.0%}")

        self.model_name = model_name
        self.ollama_url = ollama_url
        self.generate_endpoint = f"{ollama_url}/api/generate"
        self.completeness_threshold = completeness_threshold

        print(f"✅ Completeness Checker initialized!")

    def _call_ollama(self, prompt: str, system: Optional[str] = None) -> str:
        """Call Ollama API"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            return response.json()["response"].strip()
        except Exception as e:
            print(f"⚠️ Ollama API call failed: {e}")
            return ""

    def extract_query_aspects(self, query: str) -> List[Dict]:
        """
        Extract key aspects/requirements from query

        Args:
            query: User query

        Returns:
            List of aspect dictionaries
        """
        system_prompt = """Bạn là hệ thống phân tích câu hỏi.

NHIỆM VỤ: Trích xuất các khía cạnh/yêu cầu chính từ câu hỏi của người dùng.

VÍ DỤ:
Câu hỏi: "Đăng ký kết hôn cần giấy tờ gì và mất bao lâu?"
Khía cạnh:
1. Giấy tờ cần thiết cho đăng ký kết hôn
2. Thời gian xử lý thủ tục

QUAN TRỌNG:
- Mỗi khía cạnh là một thông tin riêng biệt mà người dùng muốn biết
- Trả về JSON array
- Mỗi khía cạnh có: aspect (tên ngắn) và description (mô tả chi tiết)
"""

        prompt = f"""Câu hỏi: "{query}"

Trích xuất các khía cạnh chính từ câu hỏi.

Trả về JSON array:
[
  {{"aspect": "tên khía cạnh", "description": "mô tả chi tiết"}},
  ...
]

Chỉ trả về JSON, không giải thích:"""

        response = self._call_ollama(prompt, system=system_prompt)

        if not response:
            # Fallback: single aspect = the entire query
            return [{"aspect": "Trả lời câu hỏi", "description": query}]

        try:
            # Extract JSON
            start = response.find("[")
            end = response.rfind("]") + 1

            if start != -1 and end > start:
                json_str = response[start:end]
                aspects = json.loads(json_str)
                return aspects if aspects else [{"aspect": "Trả lời câu hỏi", "description": query}]
        except:
            pass

        return [{"aspect": "Trả lời câu hỏi", "description": query}]

    def check_aspect_addressed(
        self,
        aspect: Dict,
        answer: str
    ) -> Tuple[bool, str, float]:
        """
        Check if an aspect is addressed in the answer

        Args:
            aspect: Aspect dictionary
            answer: Generated answer

        Returns:
            Tuple of (is_addressed, evidence, confidence)
        """
        system_prompt = """Bạn là hệ thống kiểm tra độ đầy đủ của câu trả lời.

NHIỆM VỤ: Xác định xem một khía cạnh cụ thể có được trả lời trong câu trả lời hay không.

QUAN TRỌNG:
- Trả lời YES nếu khía cạnh được đề cập rõ ràng
- Trả lời NO nếu khía cạnh không được đề cập hoặc đề cập mơ hồ
- Cung cấp bằng chứng (trích dẫn từ câu trả lời)
- Đánh giá độ tin cậy (0.0-1.0)
"""

        prompt = f"""Khía cạnh cần kiểm tra:
Aspect: {aspect['aspect']}
Description: {aspect['description']}

Câu trả lời:
{answer}

Khía cạnh này có được trả lời trong câu trả lời không?

Trả về theo format:
Addressed: [YES/NO]
Evidence: [Trích dẫn cụ thể từ câu trả lời, hoặc "N/A"]
Confidence: [0.0-1.0]

Chỉ trả về format trên, không giải thích:"""

        response = self._call_ollama(prompt, system=system_prompt)

        if not response:
            return False, "N/A", 0.0

        try:
            lines = response.strip().split('\n')

            # Parse Addressed
            addressed_line = next((l for l in lines if 'Addressed:' in l), None)
            is_addressed = False
            if addressed_line and "YES" in addressed_line.upper():
                is_addressed = True

            # Parse Evidence
            evidence_line = next((l for l in lines if 'Evidence:' in l), None)
            evidence = "N/A"
            if evidence_line:
                evidence = evidence_line.split('Evidence:', 1)[1].strip()

            # Parse Confidence
            conf_line = next((l for l in lines if 'Confidence:' in l), None)
            confidence = 0.5
            if conf_line:
                import re
                match = re.search(r'(\d+\.?\d*)', conf_line)
                if match:
                    confidence = float(match.group(1))
                    if confidence > 1.0:
                        confidence = confidence / 100.0

            return is_addressed, evidence, confidence

        except Exception as e:
            print(f"⚠️ Failed to parse aspect check: {e}")
            return False, "N/A", 0.0

    def check_completeness(
        self,
        query: str,
        answer: str
    ) -> CompletenessResult:
        """
        Check completeness of answer against query

        Args:
            query: User query
            answer: Generated answer

        Returns:
            CompletenessResult object
        """
        print(f"\n🔍 Checking answer completeness...")
        print(f"   Query: {query}")

        # Step 1: Extract query aspects
        print(f"\n   [1/2] Extracting query aspects...")
        aspects_data = self.extract_query_aspects(query)
        print(f"         Found {len(aspects_data)} aspects")

        # Step 2: Check each aspect
        print(f"\n   [2/2] Verifying each aspect...")
        query_aspects = []
        addressed_count = 0

        for i, aspect_dict in enumerate(aspects_data, 1):
            print(f"         [{i}/{len(aspects_data)}] {aspect_dict['aspect']}")

            is_addressed, evidence, confidence = self.check_aspect_addressed(
                aspect_dict, answer
            )

            aspect = QueryAspect(
                aspect=aspect_dict['aspect'],
                description=aspect_dict['description'],
                is_addressed=is_addressed,
                evidence=evidence,
                confidence=confidence
            )

            query_aspects.append(aspect)

            if is_addressed:
                addressed_count += 1
                print(f"             ✅ Addressed (confidence: {confidence:.2f})")
            else:
                print(f"             ❌ NOT addressed")

        # Calculate completeness
        total_aspects = len(query_aspects)
        completeness_score = addressed_count / total_aspects if total_aspects > 0 else 0.0
        is_complete = completeness_score >= self.completeness_threshold

        missing_aspects = [
            a.aspect for a in query_aspects
            if not a.is_addressed
        ]

        result = CompletenessResult(
            query=query,
            query_aspects=query_aspects,
            total_aspects=total_aspects,
            addressed_aspects=addressed_count,
            completeness_score=completeness_score,
            is_complete=is_complete,
            missing_aspects=missing_aspects
        )

        print(f"\n   📊 Completeness Summary:")
        print(f"      Total aspects: {total_aspects}")
        print(f"      Addressed: {addressed_count}")
        print(f"      Completeness: {completeness_score:.0%}")
        print(f"      Is complete: {'✅' if is_complete else '❌'}")

        return result

    def format_completeness_report(self, result: CompletenessResult) -> str:
        """Format completeness result as report"""
        lines = []

        lines.append("\n" + "=" * 80)
        lines.append("📋 COMPLETENESS CHECK REPORT")
        lines.append("=" * 80)

        lines.append(f"\n❓ Query: {result.query}")
        lines.append(f"\n✅ Complete Answer: {'YES' if result.is_complete else 'NO'}")
        lines.append(f"📊 Completeness Score: {result.completeness_score:.0%}")
        lines.append(f"📝 Aspects Analyzed: {result.total_aspects}")
        lines.append(f"✓  Aspects Addressed: {result.addressed_aspects}")

        lines.append("\n" + "-" * 80)
        lines.append("ASPECT BREAKDOWN:")
        lines.append("-" * 80)

        for i, aspect in enumerate(result.query_aspects, 1):
            status = "✅" if aspect.is_addressed else "❌"
            lines.append(f"\n[{i}] {status} {aspect.aspect}")
            lines.append(f"    Description: {aspect.description}")
            lines.append(f"    Addressed: {'YES' if aspect.is_addressed else 'NO'}")
            if aspect.is_addressed:
                lines.append(f"    Evidence: {aspect.evidence}")
                lines.append(f"    Confidence: {aspect.confidence:.2f}")

        if result.missing_aspects:
            lines.append("\n" + "-" * 80)
            lines.append("⚠️  MISSING ASPECTS:")
            lines.append("-" * 80)
            for aspect in result.missing_aspects:
                lines.append(f"  • {aspect}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


def test_completeness_checker():
    """Test completeness checker"""
    print("=" * 80)
    print("TEST COMPLETENESS CHECKER")
    print("=" * 80)

    checker = CompletenessChecker(
        model_name="qwen3:8b",
        completeness_threshold=0.8
    )

    # Test case 1: Complete answer
    query1 = "Đăng ký kết hôn cần giấy tờ gì và mất bao lâu?"
    answer1 = """
Để đăng ký kết hôn, bạn cần chuẩn bị các giấy tờ sau:
1. CMND/CCCD (02 bản sao)
2. Giấy xác nhận tình trạng hôn nhân (01 bản chính)
3. Giấy khám sức khỏe (01 bản chính)

Thời gian xử lý: Trong ngày làm việc, tối đa 3 ngày.
"""

    print("\n" + "🔵" * 40)
    print("TEST CASE 1: Complete Answer")
    print("🔵" * 40)

    result1 = checker.check_completeness(query1, answer1)
    print(checker.format_completeness_report(result1))

    # Test case 2: Incomplete answer (missing time info)
    answer2 = """
Để đăng ký kết hôn, bạn cần chuẩn bị các giấy tờ sau:
1. CMND/CCCD (02 bản sao)
2. Giấy xác nhận tình trạng hôn nhân (01 bản chính)
3. Giấy khám sức khỏe (01 bản chính)
"""

    print("\n\n" + "🔴" * 40)
    print("TEST CASE 2: Incomplete Answer (missing time)")
    print("🔴" * 40)

    result2 = checker.check_completeness(query1, answer2)
    print(checker.format_completeness_report(result2))

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_completeness_checker()
