#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Evaluation Metrics for RAG System
Implements accuracy, precision, recall, F1-score, and hallucination rate
"""

import sys
import re
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class FactMatchResult:
    """Result of fact matching"""
    predicted_facts: List[str]
    ground_truth_facts: List[str]
    true_positives: List[str]
    false_positives: List[str]
    false_negatives: List[str]
    precision: float
    recall: float
    f1_score: float


@dataclass
class EvaluationMetrics:
    """Complete evaluation metrics for a single answer"""
    test_id: str
    question: str

    # Fact-based metrics
    fact_precision: float
    fact_recall: float
    fact_f1_score: float

    # Completeness
    completeness_score: float
    addressed_aspects: int
    total_aspects: int

    # Hallucination
    hallucination_rate: float
    hallucinated_facts: List[str]

    # Overall
    accuracy_score: float  # Combined metric
    is_correct: bool  # True if meets all thresholds


class MetricsCalculator:
    """
    Calculate evaluation metrics for RAG system

    Metrics:
    - Accuracy: Overall correctness
    - Precision: Correct facts / Total predicted facts
    - Recall: Correct facts / Total ground truth facts
    - F1-Score: Harmonic mean of precision and recall
    - Hallucination Rate: Hallucinated facts / Total facts
    """

    def __init__(
        self,
        accuracy_threshold: float = 0.95,
        precision_threshold: float = 0.90,
        recall_threshold: float = 0.90,
        f1_threshold: float = 0.90,
        hallucination_threshold: float = 0.05
    ):
        """
        Initialize metrics calculator

        Args:
            accuracy_threshold: Min accuracy for passing (default: 95%)
            precision_threshold: Min precision (default: 90%)
            recall_threshold: Min recall (default: 90%)
            f1_threshold: Min F1-score (default: 90%)
            hallucination_threshold: Max hallucination rate (default: 5%)
        """
        self.accuracy_threshold = accuracy_threshold
        self.precision_threshold = precision_threshold
        self.recall_threshold = recall_threshold
        self.f1_threshold = f1_threshold
        self.hallucination_threshold = hallucination_threshold

    def _normalize_fact(self, fact: str) -> str:
        """Normalize fact for comparison"""
        # Lowercase
        fact = fact.lower()
        # Remove punctuation
        fact = re.sub(r'[^\w\s]', ' ', fact)
        # Remove extra whitespace
        fact = re.sub(r'\s+', ' ', fact).strip()
        return fact

    def _calculate_similarity(self, fact1: str, fact2: str) -> float:
        """Calculate Jaccard similarity between two facts"""
        words1 = set(self._normalize_fact(fact1).split())
        words2 = set(self._normalize_fact(fact2).split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _match_facts(
        self,
        predicted_facts: List[str],
        ground_truth_facts: List[str],
        similarity_threshold: float = 0.7
    ) -> FactMatchResult:
        """
        Match predicted facts against ground truth

        Args:
            predicted_facts: Facts from generated answer
            ground_truth_facts: Expected facts
            similarity_threshold: Min similarity to consider match

        Returns:
            FactMatchResult with TP, FP, FN
        """
        true_positives = []
        false_positives = []
        matched_gt = set()

        # Match predicted facts to ground truth
        for pred_fact in predicted_facts:
            matched = False

            for i, gt_fact in enumerate(ground_truth_facts):
                if i in matched_gt:
                    continue

                similarity = self._calculate_similarity(pred_fact, gt_fact)

                if similarity >= similarity_threshold:
                    true_positives.append(pred_fact)
                    matched_gt.add(i)
                    matched = True
                    break

            if not matched:
                false_positives.append(pred_fact)

        # Find false negatives (ground truth facts not matched)
        false_negatives = [
            gt_fact for i, gt_fact in enumerate(ground_truth_facts)
            if i not in matched_gt
        ]

        # Calculate metrics
        tp_count = len(true_positives)
        fp_count = len(false_positives)
        fn_count = len(false_negatives)

        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
        recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )

        return FactMatchResult(
            predicted_facts=predicted_facts,
            ground_truth_facts=ground_truth_facts,
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
            f1_score=f1_score
        )

    def _extract_facts_from_answer(self, answer: str) -> List[str]:
        """
        Extract facts from generated answer

        Args:
            answer: Generated answer text

        Returns:
            List of extracted facts
        """
        facts = []

        # Remove thinking tags
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)

        # Extract numbered items
        numbered_pattern = r'^\d+\.\s*(.+?)(?=\n|$)'
        numbered = re.findall(numbered_pattern, answer, re.MULTILINE)
        facts.extend([item.strip() for item in numbered if len(item.strip()) > 10])

        # Extract bullet points
        bullet_pattern = r'^[•\-]\s*(.+?)(?=\n|$)'
        bullets = re.findall(bullet_pattern, answer, re.MULTILINE)
        facts.extend([item.strip() for item in bullets if len(item.strip()) > 10])

        # If no structured facts, extract sentences
        if not facts:
            sentences = re.split(r'[.!?]\n', answer)
            facts = [s.strip() for s in sentences if 15 < len(s.strip()) < 200]

        return facts[:20]  # Limit

    def _check_aspect_coverage(
        self,
        answer: str,
        required_aspects: List[str]
    ) -> Tuple[int, int]:
        """
        Check how many required aspects are addressed in answer

        Args:
            answer: Generated answer
            required_aspects: List of required aspects

        Returns:
            Tuple of (addressed_count, total_count)
        """
        answer_lower = answer.lower()
        addressed = 0

        for aspect in required_aspects:
            # Simple keyword matching
            aspect_lower = aspect.lower()

            # Check if aspect keywords appear in answer
            aspect_words = set(re.findall(r'\w+', aspect_lower))
            answer_words = set(re.findall(r'\w+', answer_lower))

            overlap = len(aspect_words & answer_words)
            overlap_ratio = overlap / len(aspect_words) if aspect_words else 0

            if overlap_ratio > 0.5:  # >50% keyword match
                addressed += 1

        return addressed, len(required_aspects)

    def evaluate_answer(
        self,
        test_id: str,
        question: str,
        generated_answer: str,
        ground_truth_facts: List[str],
        required_aspects: List[str],
        validation_result: Optional[Dict] = None
    ) -> EvaluationMetrics:
        """
        Evaluate a generated answer against ground truth

        Args:
            test_id: Test case ID
            question: Question
            generated_answer: Generated answer
            ground_truth_facts: Expected facts
            required_aspects: Required aspects to address
            validation_result: Optional validation result from Phase 5

        Returns:
            EvaluationMetrics object
        """
        # Extract facts from generated answer
        predicted_facts = self._extract_facts_from_answer(generated_answer)

        # Match facts
        fact_match = self._match_facts(predicted_facts, ground_truth_facts)

        # Check aspect coverage
        addressed_aspects, total_aspects = self._check_aspect_coverage(
            generated_answer, required_aspects
        )

        completeness_score = (
            addressed_aspects / total_aspects
            if total_aspects > 0 else 0.0
        )

        # Calculate hallucination rate
        hallucination_rate = 0.0
        hallucinated_facts = []

        if validation_result and 'nli_result' in validation_result:
            nli_result = validation_result['nli_result']
            hallucination_rate = nli_result.get('hallucination_rate', 0.0)
            hallucinated_facts = [
                v['sentence'] for v in nli_result.get('validations', [])
                if v.get('is_hallucination', False)
            ]
        else:
            # Use false positives as proxy for hallucinations
            hallucination_rate = (
                len(fact_match.false_positives) / len(predicted_facts)
                if predicted_facts else 0.0
            )
            hallucinated_facts = fact_match.false_positives

        # Calculate overall accuracy
        # Weighted combination: 40% F1 + 30% Completeness + 30% (1 - Hallucination)
        accuracy_score = (
            0.4 * fact_match.f1_score +
            0.3 * completeness_score +
            0.3 * (1.0 - hallucination_rate)
        )

        # Check if meets all thresholds
        is_correct = (
            accuracy_score >= self.accuracy_threshold and
            fact_match.precision >= self.precision_threshold and
            fact_match.recall >= self.recall_threshold and
            fact_match.f1_score >= self.f1_threshold and
            hallucination_rate <= self.hallucination_threshold
        )

        return EvaluationMetrics(
            test_id=test_id,
            question=question,
            fact_precision=fact_match.precision,
            fact_recall=fact_match.recall,
            fact_f1_score=fact_match.f1_score,
            completeness_score=completeness_score,
            addressed_aspects=addressed_aspects,
            total_aspects=total_aspects,
            hallucination_rate=hallucination_rate,
            hallucinated_facts=hallucinated_facts,
            accuracy_score=accuracy_score,
            is_correct=is_correct
        )

    def format_metrics_report(self, metrics: EvaluationMetrics) -> str:
        """Format metrics as human-readable report"""
        lines = []

        lines.append("\n" + "=" * 80)
        lines.append("📊 EVALUATION METRICS REPORT")
        lines.append("=" * 80)

        lines.append(f"\nTest ID: {metrics.test_id}")
        lines.append(f"Question: {metrics.question}")

        lines.append("\n" + "-" * 80)
        lines.append("FACT-BASED METRICS:")
        lines.append("-" * 80)
        lines.append(f"Precision:  {metrics.fact_precision:.2%} (Target: ≥{self.precision_threshold:.0%})")
        lines.append(f"Recall:     {metrics.fact_recall:.2%} (Target: ≥{self.recall_threshold:.0%})")
        lines.append(f"F1-Score:   {metrics.fact_f1_score:.2%} (Target: ≥{self.f1_threshold:.0%})")

        lines.append("\n" + "-" * 80)
        lines.append("COMPLETENESS:")
        lines.append("-" * 80)
        lines.append(f"Score:      {metrics.completeness_score:.2%}")
        lines.append(f"Aspects:    {metrics.addressed_aspects}/{metrics.total_aspects} addressed")

        lines.append("\n" + "-" * 80)
        lines.append("HALLUCINATION:")
        lines.append("-" * 80)
        lines.append(f"Rate:       {metrics.hallucination_rate:.2%} (Target: ≤{self.hallucination_threshold:.0%})")
        lines.append(f"Count:      {len(metrics.hallucinated_facts)} facts")

        if metrics.hallucinated_facts:
            lines.append("\nHallucinated facts:")
            for i, fact in enumerate(metrics.hallucinated_facts[:5], 1):
                lines.append(f"  {i}. {fact[:80]}...")

        lines.append("\n" + "-" * 80)
        lines.append("OVERALL:")
        lines.append("-" * 80)
        lines.append(f"Accuracy:   {metrics.accuracy_score:.2%} (Target: ≥{self.accuracy_threshold:.0%})")
        lines.append(f"Status:     {'✅ PASS' if metrics.is_correct else '❌ FAIL'}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


def test_metrics_calculator():
    """Test metrics calculator"""
    print("=" * 80)
    print("TEST METRICS CALCULATOR")
    print("=" * 80)

    calculator = MetricsCalculator()

    # Test case
    question = "Đăng ký kết hôn cần giấy tờ gì?"

    ground_truth_facts = [
        "CMND/CCCD - 02 bản sao",
        "Giấy xác nhận tình trạng hôn nhân - 01 bản chính",
        "Giấy khám sức khỏe tiền hôn nhân - 01 bản chính",
        "Đơn đăng ký kết hôn - 01 bản"
    ]

    # Good answer (high precision, recall)
    good_answer = """
Để đăng ký kết hôn, bạn cần:
1. CMND hoặc CCCD (02 bản sao)
2. Giấy xác nhận tình trạng hôn nhân (01 bản chính)
3. Giấy khám sức khỏe tiền hôn nhân (01 bản chính)
4. Đơn đăng ký kết hôn (01 bản)
"""

    print("\n🔵 Test Case 1: Good Answer")
    metrics1 = calculator.evaluate_answer(
        test_id="TEST_001",
        question=question,
        generated_answer=good_answer,
        ground_truth_facts=ground_truth_facts,
        required_aspects=["Danh sách giấy tờ", "Số lượng bản"]
    )
    print(calculator.format_metrics_report(metrics1))

    # Poor answer (missing facts, hallucination)
    poor_answer = """
Để đăng ký kết hôn, bạn cần:
1. CMND hoặc CCCD (02 bản sao)
2. Giấy khai sinh gốc
3. Nộp phí 500.000 VNĐ
"""

    print("\n🔴 Test Case 2: Poor Answer (missing facts + hallucination)")
    metrics2 = calculator.evaluate_answer(
        test_id="TEST_002",
        question=question,
        generated_answer=poor_answer,
        ground_truth_facts=ground_truth_facts,
        required_aspects=["Danh sách giấy tờ", "Số lượng bản"]
    )
    print(calculator.format_metrics_report(metrics2))

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_metrics_calculator()
