#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cross-Reference Validator - Layer 3 Validation
Verifies facts across multiple source chunks for consistency
"""

import sys
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class Fact:
    """A single fact extracted from answer"""
    fact: str
    supporting_chunks: List[str]
    support_count: int
    confidence: float
    is_reliable: bool


@dataclass
class CrossReferenceResult:
    """Result of cross-reference validation"""
    answer: str
    facts: List[Fact]
    total_facts: int
    reliable_facts: int
    unreliable_facts: int
    average_support: float
    is_valid: bool


class CrossReferenceValidator:
    """
    Validates facts by cross-referencing multiple source chunks

    For each fact in the answer:
    1. Find supporting evidence across all chunks
    2. Count how many chunks support this fact
    3. Flag facts with low support as unreliable
    """

    def __init__(
        self,
        min_support: int = 1,
        reliability_threshold: float = 0.6
    ):
        """
        Initialize cross-reference validator

        Args:
            min_support: Minimum number of chunks that should support a fact
            reliability_threshold: Threshold for considering fact reliable
        """
        print(f"🔄 Initializing Cross-Reference Validator")
        print(f"   Min support chunks: {min_support}")
        print(f"   Reliability threshold: {reliability_threshold}")

        self.min_support = min_support
        self.reliability_threshold = reliability_threshold

        print(f"✅ Cross-Reference Validator initialized!")

    def _extract_facts_from_answer(self, answer: str) -> List[str]:
        """
        Extract key facts from answer

        Simple extraction: split by sentences and bullet points

        Args:
            answer: Generated answer

        Returns:
            List of fact strings
        """
        # Remove thinking tags
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)

        facts = []

        # Split by sentences
        sentences = re.split(r'[.!?]\n', answer)

        for sent in sentences:
            sent = sent.strip()

            # Skip very short sentences
            if len(sent) < 20:
                continue

            # Extract bullet points
            if re.match(r'^\d+\.', sent) or sent.startswith('•') or sent.startswith('-'):
                # This is a list item
                facts.append(sent)
            elif len(sent) > 30:
                # Regular sentence
                facts.append(sent)

        return facts[:20]  # Limit for performance

    def _find_supporting_chunks(
        self,
        fact: str,
        chunks: List[Dict]
    ) -> List[str]:
        """
        Find chunks that support a given fact

        Uses simple keyword matching and semantic similarity

        Args:
            fact: Fact to verify
            chunks: List of source chunks

        Returns:
            List of supporting chunk_ids
        """
        supporting_chunks = []

        # Extract key terms from fact (simple approach)
        # Remove common words
        stopwords = {'là', 'của', 'được', 'có', 'và', 'cho', 'với', 'trong', 'các', 'những'}

        fact_words = set([
            w.lower() for w in re.findall(r'\w+', fact)
            if len(w) > 2 and w.lower() not in stopwords
        ])

        # Check each chunk
        for chunk in chunks:
            content = chunk.get('content', '').lower()

            # Count matching keywords
            chunk_words = set([
                w for w in re.findall(r'\w+', content)
                if len(w) > 2
            ])

            # Calculate overlap
            overlap = len(fact_words & chunk_words)
            overlap_ratio = overlap / len(fact_words) if fact_words else 0

            # Consider chunk as supporting if >30% keyword overlap
            if overlap_ratio > 0.3:
                supporting_chunks.append(chunk.get('chunk_id', 'unknown'))

        return supporting_chunks

    def validate_facts(
        self,
        answer: str,
        source_chunks: List[Dict]
    ) -> CrossReferenceResult:
        """
        Validate facts in answer against source chunks

        Args:
            answer: Generated answer
            source_chunks: Retrieved source chunks

        Returns:
            CrossReferenceResult object
        """
        print(f"\n🔍 Cross-referencing facts...")

        # Step 1: Extract facts from answer
        print(f"   [1/2] Extracting facts from answer...")
        fact_strings = self._extract_facts_from_answer(answer)
        print(f"         Found {len(fact_strings)} facts")

        # Step 2: Validate each fact
        print(f"   [2/2] Validating each fact...")
        facts = []
        reliable_count = 0
        unreliable_count = 0

        for i, fact_str in enumerate(fact_strings, 1):
            print(f"         [{i}/{len(fact_strings)}] {fact_str[:60]}...")

            # Find supporting chunks
            supporting_chunks = self._find_supporting_chunks(fact_str, source_chunks)
            support_count = len(supporting_chunks)

            # Calculate confidence based on support
            # More supporting chunks = higher confidence
            max_possible_support = len(source_chunks)
            confidence = support_count / max_possible_support if max_possible_support > 0 else 0.0

            # Fact is reliable if it meets minimum support threshold
            is_reliable = (
                support_count >= self.min_support and
                confidence >= self.reliability_threshold
            )

            fact = Fact(
                fact=fact_str,
                supporting_chunks=supporting_chunks,
                support_count=support_count,
                confidence=confidence,
                is_reliable=is_reliable
            )

            facts.append(fact)

            if is_reliable:
                reliable_count += 1
                print(f"             ✅ Reliable (support: {support_count} chunks)")
            else:
                unreliable_count += 1
                print(f"             ⚠️ Low support ({support_count} chunks)")

        # Calculate metrics
        total_facts = len(facts)
        average_support = (
            sum(f.support_count for f in facts) / total_facts
            if total_facts > 0 else 0.0
        )

        # Overall valid if >80% facts are reliable
        is_valid = (reliable_count / total_facts) >= 0.8 if total_facts > 0 else False

        result = CrossReferenceResult(
            answer=answer,
            facts=facts,
            total_facts=total_facts,
            reliable_facts=reliable_count,
            unreliable_facts=unreliable_count,
            average_support=average_support,
            is_valid=is_valid
        )

        print(f"\n   📊 Cross-Reference Summary:")
        print(f"      Total facts: {total_facts}")
        print(f"      Reliable: {reliable_count}")
        print(f"      Unreliable: {unreliable_count}")
        print(f"      Average support: {average_support:.1f} chunks")
        print(f"      Is valid: {'✅' if is_valid else '❌'}")

        return result

    def format_validation_report(self, result: CrossReferenceResult) -> str:
        """Format validation result as report"""
        lines = []

        lines.append("\n" + "=" * 80)
        lines.append("📋 CROSS-REFERENCE VALIDATION REPORT")
        lines.append("=" * 80)

        lines.append(f"\n✅ Valid Answer: {'YES' if result.is_valid else 'NO'}")
        lines.append(f"📊 Average Support: {result.average_support:.1f} chunks per fact")
        lines.append(f"📝 Facts Analyzed: {result.total_facts}")
        lines.append(f"✓  Reliable Facts: {result.reliable_facts}")
        lines.append(f"⚠️  Unreliable Facts: {result.unreliable_facts}")

        lines.append("\n" + "-" * 80)
        lines.append("FACT BREAKDOWN:")
        lines.append("-" * 80)

        for i, fact in enumerate(result.facts, 1):
            status = "✅" if fact.is_reliable else "⚠️"
            lines.append(f"\n[{i}] {status} {fact.fact[:100]}...")
            lines.append(f"    Support count: {fact.support_count} chunks")
            lines.append(f"    Confidence: {fact.confidence:.2f}")
            if fact.supporting_chunks:
                lines.append(f"    Sources: {', '.join(fact.supporting_chunks[:3])}")

        if result.unreliable_facts > 0:
            lines.append("\n" + "-" * 80)
            lines.append("⚠️  LOW-SUPPORT FACTS:")
            lines.append("-" * 80)

            for fact in result.facts:
                if not fact.is_reliable:
                    lines.append(f"\n  • {fact.fact[:100]}...")
                    lines.append(f"    Support: {fact.support_count} chunks (needs >{self.min_support})")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


def test_cross_reference_validator():
    """Test cross-reference validator"""
    print("=" * 80)
    print("TEST CROSS-REFERENCE VALIDATOR")
    print("=" * 80)

    validator = CrossReferenceValidator(
        min_support=1,
        reliability_threshold=0.3
    )

    # Mock source chunks
    chunks = [
        {
            "chunk_id": "chunk_001",
            "content": "Hồ sơ đăng ký kết hôn bao gồm CMND/CCCD 02 bản sao, giấy xác nhận tình trạng hôn nhân 01 bản chính."
        },
        {
            "chunk_id": "chunk_002",
            "content": "Thời gian giải quyết thủ tục đăng ký kết hôn là trong ngày làm việc, tối đa không quá 03 ngày."
        },
        {
            "chunk_id": "chunk_003",
            "content": "Giấy khám sức khỏe tiền hôn nhân cần nộp 01 bản chính do cơ sở y tế có thẩm quyền cấp."
        }
    ]

    # Test case 1: Answer with well-supported facts
    answer1 = """
Để đăng ký kết hôn, bạn cần:
1. CMND/CCCD (02 bản sao)
2. Giấy xác nhận tình trạng hôn nhân (01 bản chính)
3. Giấy khám sức khỏe tiền hôn nhân (01 bản chính)

Thời gian xử lý: Trong ngày làm việc, tối đa 3 ngày.
"""

    print("\n" + "🔵" * 40)
    print("TEST CASE 1: Well-Supported Facts")
    print("🔵" * 40)

    result1 = validator.validate_facts(answer1, chunks)
    print(validator.format_validation_report(result1))

    # Test case 2: Answer with unsupported facts
    answer2 = """
Để đăng ký kết hôn, bạn cần:
1. CMND/CCCD (02 bản sao)
2. Giấy khai sinh gốc (01 bản)
3. Giấy chứng nhận tài chính (01 bản)

Phí đăng ký: 500.000 VNĐ
Thời gian xử lý: 30 ngày làm việc
"""

    print("\n\n" + "🔴" * 40)
    print("TEST CASE 2: Unsupported Facts")
    print("🔴" * 40)

    result2 = validator.validate_facts(answer2, chunks)
    print(validator.format_validation_report(result2))

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_cross_reference_validator()
