#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Self-Consistency Validator - Layer 4 Validation
Uses majority voting across N independent generations to improve reliability
"""

import sys
import requests
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class ConsistencyResult:
    """Result of self-consistency validation"""
    question: str
    num_generations: int
    generated_answers: List[str]
    extracted_facts: List[List[str]]
    fact_frequencies: Dict[str, int]
    consensus_facts: List[Tuple[str, int, float]]  # (fact, count, agreement)
    final_answer: str
    average_agreement: float
    is_consistent: bool


class SelfConsistencyValidator:
    """
    Self-Consistency through Majority Voting

    Process:
    1. Generate N independent answers (temperature > 0)
    2. Extract key facts from each answer
    3. Count frequency of each fact across answers
    4. Select facts with ≥60% agreement
    5. Synthesize final answer from consensus facts
    """

    def __init__(
        self,
        model_name: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434",
        num_generations: int = 5,
        agreement_threshold: float = 0.6
    ):
        """
        Initialize self-consistency validator

        Args:
            model_name: Ollama model name
            ollama_url: Ollama server URL
            num_generations: Number of independent generations (N)
            agreement_threshold: Minimum agreement for consensus (0.6 = 60%)
        """
        print(f"🔄 Initializing Self-Consistency Validator")
        print(f"   Model: {model_name}")
        print(f"   Generations (N): {num_generations}")
        print(f"   Agreement threshold: {agreement_threshold:.0%}")

        self.model_name = model_name
        self.ollama_url = ollama_url
        self.generate_endpoint = f"{ollama_url}/api/generate"
        self.num_generations = num_generations
        self.agreement_threshold = agreement_threshold

        print(f"✅ Self-Consistency Validator initialized!")

    def _call_ollama(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Call Ollama API"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature  # Higher temp for diversity
            }
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=120
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            return response.json()["response"].strip()
        except Exception as e:
            print(f"⚠️ Ollama API call failed: {e}")
            return ""

    def _extract_key_facts(self, answer: str) -> List[str]:
        """
        Extract key facts from an answer

        Simple approach: extract sentences and bullet points

        Args:
            answer: Generated answer

        Returns:
            List of fact strings
        """
        # Remove thinking tags
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)

        facts = []

        # Extract bullet points (numbered or symbols)
        bullet_pattern = r'(?:^\d+\.|^•|^-)\s*(.+?)(?=\n|$)'
        bullets = re.findall(bullet_pattern, answer, re.MULTILINE)
        facts.extend([b.strip() for b in bullets if len(b.strip()) > 15])

        # Extract sentences (if no bullets)
        if not facts:
            sentences = re.split(r'[.!?]\n', answer)
            facts = [s.strip() for s in sentences if 15 < len(s.strip()) < 200]

        return facts[:10]  # Limit per answer

    def _normalize_fact(self, fact: str) -> str:
        """
        Normalize fact for comparison

        Args:
            fact: Original fact string

        Returns:
            Normalized fact
        """
        # Lowercase
        fact = fact.lower()

        # Remove punctuation
        fact = re.sub(r'[^\w\s]', ' ', fact)

        # Remove extra whitespace
        fact = re.sub(r'\s+', ' ', fact).strip()

        return fact

    def _calculate_similarity(self, fact1: str, fact2: str) -> float:
        """
        Calculate similarity between two facts (Jaccard)

        Args:
            fact1: First fact
            fact2: Second fact

        Returns:
            Similarity score (0.0-1.0)
        """
        words1 = set(self._normalize_fact(fact1).split())
        words2 = set(self._normalize_fact(fact2).split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _cluster_facts(self, all_facts: List[str]) -> Dict[str, int]:
        """
        Cluster similar facts and count frequencies

        Args:
            all_facts: All facts from all generations

        Returns:
            Dictionary of {representative_fact: count}
        """
        if not all_facts:
            return {}

        clusters = {}  # {representative_fact: [similar_facts]}

        for fact in all_facts:
            # Find if this fact belongs to existing cluster
            matched_cluster = None

            for representative in clusters.keys():
                similarity = self._calculate_similarity(fact, representative)

                # If >70% similar, same cluster
                if similarity > 0.7:
                    matched_cluster = representative
                    break

            if matched_cluster:
                clusters[matched_cluster].append(fact)
            else:
                # New cluster
                clusters[fact] = [fact]

        # Convert to frequency count
        frequencies = {
            rep: len(facts) for rep, facts in clusters.items()
        }

        return frequencies

    def validate_with_self_consistency(
        self,
        question: str,
        context: str
    ) -> ConsistencyResult:
        """
        Validate answer using self-consistency

        Args:
            question: User question
            context: Retrieved context

        Returns:
            ConsistencyResult object
        """
        print(f"\n🔍 Self-consistency validation (N={self.num_generations})...")
        print(f"   Question: {question}")

        system_prompt = """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

CHỈ trả lời dựa trên CONTEXT được cung cấp.
KHÔNG bịa đặt thông tin.
"""

        prompt = f"""Câu hỏi: {question}

Context:
{context[:2000]}

Trả lời câu hỏi một cách chính xác, ngắn gọn:"""

        # Step 1: Generate N independent answers
        print(f"\n   [1/3] Generating {self.num_generations} independent answers...")
        generated_answers = []

        for i in range(self.num_generations):
            print(f"         [{i+1}/{self.num_generations}] Generating...")

            answer = self._call_ollama(
                prompt,
                system=system_prompt,
                temperature=0.7  # Higher temp for diversity
            )

            if answer:
                generated_answers.append(answer)
                print(f"             ✓ Generated ({len(answer)} chars)")
            else:
                print(f"             ✗ Failed")

        if not generated_answers:
            print("   ⚠️ No answers generated!")
            return ConsistencyResult(
                question=question,
                num_generations=0,
                generated_answers=[],
                extracted_facts=[],
                fact_frequencies={},
                consensus_facts=[],
                final_answer="Error: No answers generated",
                average_agreement=0.0,
                is_consistent=False
            )

        # Step 2: Extract facts from each answer
        print(f"\n   [2/3] Extracting facts from each answer...")
        extracted_facts = []
        all_facts = []

        for i, answer in enumerate(generated_answers, 1):
            facts = self._extract_key_facts(answer)
            extracted_facts.append(facts)
            all_facts.extend(facts)
            print(f"         Answer {i}: {len(facts)} facts extracted")

        # Step 3: Count fact frequencies with clustering
        print(f"\n   [3/3] Clustering and counting fact frequencies...")
        fact_frequencies = self._cluster_facts(all_facts)

        # Calculate consensus facts (≥60% agreement)
        min_count = int(self.agreement_threshold * self.num_generations)

        consensus_facts = [
            (fact, count, count / self.num_generations)
            for fact, count in fact_frequencies.items()
            if count >= min_count
        ]

        # Sort by frequency
        consensus_facts.sort(key=lambda x: x[1], reverse=True)

        print(f"         Total unique facts: {len(fact_frequencies)}")
        print(f"         Consensus facts (≥{self.agreement_threshold:.0%}): {len(consensus_facts)}")

        # Calculate average agreement
        if fact_frequencies:
            average_agreement = sum(fact_frequencies.values()) / len(fact_frequencies) / self.num_generations
        else:
            average_agreement = 0.0

        # Synthesize final answer from consensus facts
        final_answer_lines = []
        for fact, count, agreement in consensus_facts:
            final_answer_lines.append(f"• {fact} ({agreement:.0%} agreement)")

        final_answer = "\n".join(final_answer_lines) if final_answer_lines else "Không có đồng thuận"

        # Consistent if we have at least 3 consensus facts
        is_consistent = len(consensus_facts) >= 3

        result = ConsistencyResult(
            question=question,
            num_generations=len(generated_answers),
            generated_answers=generated_answers,
            extracted_facts=extracted_facts,
            fact_frequencies=fact_frequencies,
            consensus_facts=consensus_facts,
            final_answer=final_answer,
            average_agreement=average_agreement,
            is_consistent=is_consistent
        )

        print(f"\n   📊 Self-Consistency Summary:")
        print(f"      Answers generated: {len(generated_answers)}")
        print(f"      Consensus facts: {len(consensus_facts)}")
        print(f"      Average agreement: {average_agreement:.0%}")
        print(f"      Is consistent: {'✅' if is_consistent else '❌'}")

        return result

    def format_consistency_report(self, result: ConsistencyResult) -> str:
        """Format consistency result as report"""
        lines = []

        lines.append("\n" + "=" * 80)
        lines.append("📋 SELF-CONSISTENCY VALIDATION REPORT")
        lines.append("=" * 80)

        lines.append(f"\n❓ Question: {result.question}")
        lines.append(f"\n✅ Consistent: {'YES' if result.is_consistent else 'NO'}")
        lines.append(f"📊 Average Agreement: {result.average_agreement:.0%}")
        lines.append(f"🔢 Generations: {result.num_generations}")
        lines.append(f"✓  Consensus Facts: {len(result.consensus_facts)}")

        lines.append("\n" + "-" * 80)
        lines.append("CONSENSUS FACTS (Majority Agreement):")
        lines.append("-" * 80)

        for i, (fact, count, agreement) in enumerate(result.consensus_facts, 1):
            lines.append(f"\n[{i}] {fact}")
            lines.append(f"    Agreement: {count}/{result.num_generations} ({agreement:.0%})")

        if len(result.consensus_facts) < 3:
            lines.append("\n⚠️  Warning: Low number of consensus facts")
            lines.append("    The generated answers may be inconsistent")

        lines.append("\n" + "-" * 80)
        lines.append("FINAL SYNTHESIZED ANSWER:")
        lines.append("-" * 80)
        lines.append(result.final_answer)

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


def test_self_consistency():
    """Test self-consistency validator"""
    print("=" * 80)
    print("TEST SELF-CONSISTENCY VALIDATOR")
    print("=" * 80)

    validator = SelfConsistencyValidator(
        model_name="qwen3:8b",
        num_generations=3,  # Use 3 for faster testing
        agreement_threshold=0.6
    )

    question = "Đăng ký kết hôn cần giấy tờ gì?"
    context = """
Hồ sơ đăng ký kết hôn bao gồm:
1. Giấy tờ tùy thân (CMND/CCCD/Hộ chiếu) - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính
3. Giấy khám sức khỏe tiền hôn nhân - 01 bản chính

Thời gian giải quyết: Trong ngày làm việc.
"""

    result = validator.validate_with_self_consistency(question, context)
    print(validator.format_consistency_report(result))

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_self_consistency()
