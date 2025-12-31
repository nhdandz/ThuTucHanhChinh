#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG System Evaluator
Runs comprehensive evaluation across test dataset with performance benchmarking
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))
sys.path.insert(0, str(Path(__file__).parent.parent / "generation"))
sys.path.insert(0, str(Path(__file__).parent.parent / "validation"))

from test_dataset import TestDatasetManager, TestCase
from metrics import MetricsCalculator, EvaluationMetrics

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class PerformanceBenchmark:
    """Performance metrics for a single test"""
    test_id: str
    total_time: float  # seconds
    retrieval_time: float
    generation_time: float
    validation_time: float
    tokens_generated: int
    chunks_retrieved: int


@dataclass
class EvaluationSummary:
    """Summary of evaluation results"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float

    # Aggregate metrics
    avg_accuracy: float
    avg_precision: float
    avg_recall: float
    avg_f1_score: float
    avg_hallucination_rate: float
    avg_completeness: float

    # Performance
    avg_total_time: float
    avg_retrieval_time: float
    avg_generation_time: float

    # By category
    results_by_category: Dict[str, Dict]
    results_by_difficulty: Dict[str, Dict]


@dataclass
class EvaluationReport:
    """Complete evaluation report"""
    report_id: str
    timestamp: str
    dataset_name: str
    test_results: List[EvaluationMetrics]
    performance_benchmarks: List[PerformanceBenchmark]
    summary: EvaluationSummary
    configuration: Dict


class RAGEvaluator:
    """
    Complete RAG System Evaluator

    Runs comprehensive evaluation including:
    - Answer quality metrics
    - Performance benchmarking
    - Category/difficulty analysis
    """

    def __init__(
        self,
        metrics_calculator: Optional[MetricsCalculator] = None
    ):
        """
        Initialize evaluator

        Args:
            metrics_calculator: MetricsCalculator instance (optional)
        """
        print("🔄 Initializing RAG Evaluator")

        self.metrics_calculator = metrics_calculator or MetricsCalculator()
        self.test_results = []
        self.performance_benchmarks = []

        print("✅ RAG Evaluator initialized!")

    def evaluate_single_test(
        self,
        test_case: TestCase,
        generated_answer: str,
        retrieval_time: float = 0.0,
        generation_time: float = 0.0,
        validation_result: Optional[Dict] = None,
        chunks_retrieved: int = 0
    ) -> tuple[EvaluationMetrics, PerformanceBenchmark]:
        """
        Evaluate a single test case

        Args:
            test_case: TestCase object
            generated_answer: Generated answer string
            retrieval_time: Time spent on retrieval (seconds)
            generation_time: Time spent on generation (seconds)
            validation_result: Optional validation result
            chunks_retrieved: Number of chunks retrieved

        Returns:
            Tuple of (EvaluationMetrics, PerformanceBenchmark)
        """
        start_time = time.time()

        # Evaluate metrics
        metrics = self.metrics_calculator.evaluate_answer(
            test_id=test_case.test_id,
            question=test_case.question,
            generated_answer=generated_answer,
            ground_truth_facts=test_case.ground_truth.key_facts,
            required_aspects=test_case.ground_truth.required_aspects,
            validation_result=validation_result
        )

        # Performance benchmark
        validation_time = time.time() - start_time - retrieval_time - generation_time
        total_time = retrieval_time + generation_time + validation_time

        # Estimate tokens (rough approximation)
        tokens_generated = len(generated_answer.split())

        benchmark = PerformanceBenchmark(
            test_id=test_case.test_id,
            total_time=total_time,
            retrieval_time=retrieval_time,
            generation_time=generation_time,
            validation_time=validation_time,
            tokens_generated=tokens_generated,
            chunks_retrieved=chunks_retrieved
        )

        return metrics, benchmark

    def evaluate_batch(
        self,
        test_cases: List[TestCase],
        answer_generator_fn,
        verbose: bool = True
    ) -> EvaluationReport:
        """
        Evaluate batch of test cases

        Args:
            test_cases: List of TestCase objects
            answer_generator_fn: Function that takes (question, context) and returns (answer, retrieval_time, generation_time, chunks)
            verbose: Print progress

        Returns:
            EvaluationReport
        """
        print("\n" + "=" * 80)
        print(f"🧪 BATCH EVALUATION: {len(test_cases)} test cases")
        print("=" * 80)

        self.test_results = []
        self.performance_benchmarks = []

        for i, test_case in enumerate(test_cases, 1):
            if verbose:
                print(f"\n[{i}/{len(test_cases)}] {test_case.test_id}: {test_case.question}")

            try:
                # Generate answer (user-provided function)
                result = answer_generator_fn(test_case.question)

                generated_answer = result.get('answer', '')
                retrieval_time = result.get('retrieval_time', 0.0)
                generation_time = result.get('generation_time', 0.0)
                chunks_retrieved = result.get('chunks_retrieved', 0)
                validation_result = result.get('validation_result')

                # Evaluate
                metrics, benchmark = self.evaluate_single_test(
                    test_case=test_case,
                    generated_answer=generated_answer,
                    retrieval_time=retrieval_time,
                    generation_time=generation_time,
                    validation_result=validation_result,
                    chunks_retrieved=chunks_retrieved
                )

                self.test_results.append(metrics)
                self.performance_benchmarks.append(benchmark)

                if verbose:
                    status = "✅ PASS" if metrics.is_correct else "❌ FAIL"
                    print(f"   {status}")
                    print(f"   Accuracy: {metrics.accuracy_score:.1%}")
                    print(f"   F1-Score: {metrics.fact_f1_score:.1%}")
                    print(f"   Hallucination: {metrics.hallucination_rate:.1%}")
                    print(f"   Time: {benchmark.total_time:.2f}s")

            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()

        # Generate summary
        summary = self._generate_summary(test_cases)

        # Create report
        report = EvaluationReport(
            report_id=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            dataset_name="RAG Test Dataset",
            test_results=self.test_results,
            performance_benchmarks=self.performance_benchmarks,
            summary=summary,
            configuration={
                "total_tests": len(test_cases),
                "thresholds": {
                    "accuracy": self.metrics_calculator.accuracy_threshold,
                    "precision": self.metrics_calculator.precision_threshold,
                    "recall": self.metrics_calculator.recall_threshold,
                    "f1_score": self.metrics_calculator.f1_threshold,
                    "hallucination": self.metrics_calculator.hallucination_threshold
                }
            }
        )

        print("\n" + "=" * 80)
        print("✅ BATCH EVALUATION COMPLETE")
        print("=" * 80)

        return report

    def _generate_summary(self, test_cases: List[TestCase]) -> EvaluationSummary:
        """Generate evaluation summary"""
        if not self.test_results:
            return EvaluationSummary(
                total_tests=0, passed_tests=0, failed_tests=0, pass_rate=0.0,
                avg_accuracy=0.0, avg_precision=0.0, avg_recall=0.0,
                avg_f1_score=0.0, avg_hallucination_rate=0.0, avg_completeness=0.0,
                avg_total_time=0.0, avg_retrieval_time=0.0, avg_generation_time=0.0,
                results_by_category={}, results_by_difficulty={}
            )

        passed = sum(1 for m in self.test_results if m.is_correct)
        failed = len(self.test_results) - passed

        # Aggregate metrics
        avg_accuracy = sum(m.accuracy_score for m in self.test_results) / len(self.test_results)
        avg_precision = sum(m.fact_precision for m in self.test_results) / len(self.test_results)
        avg_recall = sum(m.fact_recall for m in self.test_results) / len(self.test_results)
        avg_f1 = sum(m.fact_f1_score for m in self.test_results) / len(self.test_results)
        avg_hallucination = sum(m.hallucination_rate for m in self.test_results) / len(self.test_results)
        avg_completeness = sum(m.completeness_score for m in self.test_results) / len(self.test_results)

        # Performance
        avg_total = sum(b.total_time for b in self.performance_benchmarks) / len(self.performance_benchmarks)
        avg_retrieval = sum(b.retrieval_time for b in self.performance_benchmarks) / len(self.performance_benchmarks)
        avg_generation = sum(b.generation_time for b in self.performance_benchmarks) / len(self.performance_benchmarks)

        # By category
        results_by_category = {}
        for test_case in test_cases:
            cat = test_case.category
            if cat not in results_by_category:
                results_by_category[cat] = {"total": 0, "passed": 0}

            results_by_category[cat]["total"] += 1

            # Find corresponding result
            result = next((r for r in self.test_results if r.test_id == test_case.test_id), None)
            if result and result.is_correct:
                results_by_category[cat]["passed"] += 1

        # By difficulty
        results_by_difficulty = {}
        for test_case in test_cases:
            diff = test_case.difficulty
            if diff not in results_by_difficulty:
                results_by_difficulty[diff] = {"total": 0, "passed": 0}

            results_by_difficulty[diff]["total"] += 1

            result = next((r for r in self.test_results if r.test_id == test_case.test_id), None)
            if result and result.is_correct:
                results_by_difficulty[diff]["passed"] += 1

        return EvaluationSummary(
            total_tests=len(self.test_results),
            passed_tests=passed,
            failed_tests=failed,
            pass_rate=passed / len(self.test_results),
            avg_accuracy=avg_accuracy,
            avg_precision=avg_precision,
            avg_recall=avg_recall,
            avg_f1_score=avg_f1,
            avg_hallucination_rate=avg_hallucination,
            avg_completeness=avg_completeness,
            avg_total_time=avg_total,
            avg_retrieval_time=avg_retrieval,
            avg_generation_time=avg_generation,
            results_by_category=results_by_category,
            results_by_difficulty=results_by_difficulty
        )

    def format_evaluation_report(self, report: EvaluationReport) -> str:
        """Format evaluation report"""
        lines = []

        lines.append("\n" + "=" * 80)
        lines.append("📊 COMPREHENSIVE EVALUATION REPORT")
        lines.append("=" * 80)

        lines.append(f"\nReport ID: {report.report_id}")
        lines.append(f"Timestamp: {report.timestamp}")
        lines.append(f"Dataset: {report.dataset_name}")

        lines.append("\n" + "=" * 80)
        lines.append("OVERALL SUMMARY")
        lines.append("=" * 80)

        summary = report.summary

        lines.append(f"\nTotal Tests:    {summary.total_tests}")
        lines.append(f"Passed:         {summary.passed_tests} ✅")
        lines.append(f"Failed:         {summary.failed_tests} ❌")
        lines.append(f"Pass Rate:      {summary.pass_rate:.1%}")

        lines.append("\n" + "-" * 80)
        lines.append("AVERAGE METRICS")
        lines.append("-" * 80)

        lines.append(f"Accuracy:       {summary.avg_accuracy:.1%} (Target: ≥95%)")
        lines.append(f"Precision:      {summary.avg_precision:.1%} (Target: ≥90%)")
        lines.append(f"Recall:         {summary.avg_recall:.1%} (Target: ≥90%)")
        lines.append(f"F1-Score:       {summary.avg_f1_score:.1%} (Target: ≥90%)")
        lines.append(f"Hallucination:  {summary.avg_hallucination_rate:.1%} (Target: ≤5%)")
        lines.append(f"Completeness:   {summary.avg_completeness:.1%}")

        lines.append("\n" + "-" * 80)
        lines.append("PERFORMANCE BENCHMARKS")
        lines.append("-" * 80)

        lines.append(f"Avg Total Time:      {summary.avg_total_time:.2f}s")
        lines.append(f"Avg Retrieval Time:  {summary.avg_retrieval_time:.2f}s")
        lines.append(f"Avg Generation Time: {summary.avg_generation_time:.2f}s")

        lines.append("\n" + "-" * 80)
        lines.append("RESULTS BY CATEGORY")
        lines.append("-" * 80)

        for cat, stats in summary.results_by_category.items():
            pass_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0.0
            lines.append(f"{cat:15s}: {stats['passed']:2d}/{stats['total']:2d} ({pass_rate:.0%})")

        lines.append("\n" + "-" * 80)
        lines.append("RESULTS BY DIFFICULTY")
        lines.append("-" * 80)

        for diff, stats in summary.results_by_difficulty.items():
            pass_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0.0
            lines.append(f"{diff:10s}: {stats['passed']:2d}/{stats['total']:2d} ({pass_rate:.0%})")

        lines.append("\n" + "=" * 80)

        # Target achievement
        lines.append("🎯 TARGET ACHIEVEMENT")
        lines.append("=" * 80)

        targets = [
            ("Accuracy", summary.avg_accuracy, 0.95),
            ("Precision", summary.avg_precision, 0.90),
            ("Recall", summary.avg_recall, 0.90),
            ("F1-Score", summary.avg_f1_score, 0.90),
        ]

        for name, value, target in targets:
            status = "✅" if value >= target else "❌"
            lines.append(f"{status} {name:12s}: {value:.1%} (Target: ≥{target:.0%})")

        # Hallucination (inverse)
        halluc_ok = summary.avg_hallucination_rate <= 0.05
        status = "✅" if halluc_ok else "❌"
        lines.append(f"{status} Hallucination: {summary.avg_hallucination_rate:.1%} (Target: ≤5%)")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def export_report(self, report: EvaluationReport, filepath: str):
        """Export evaluation report to JSON"""
        # Convert to dict (simplified)
        report_dict = {
            "report_id": report.report_id,
            "timestamp": report.timestamp,
            "dataset_name": report.dataset_name,
            "summary": asdict(report.summary),
            "configuration": report.configuration,
            "test_results": [
                {
                    "test_id": m.test_id,
                    "accuracy": m.accuracy_score,
                    "precision": m.fact_precision,
                    "recall": m.fact_recall,
                    "f1_score": m.fact_f1_score,
                    "hallucination_rate": m.hallucination_rate,
                    "is_correct": m.is_correct
                }
                for m in report.test_results
            ],
            "performance_benchmarks": [asdict(b) for b in report.performance_benchmarks]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)

        print(f"✅ Report exported to: {filepath}")


def test_evaluator():
    """Test evaluator with mock data"""
    print("=" * 80)
    print("TEST EVALUATOR")
    print("=" * 80)

    evaluator = RAGEvaluator()

    # Mock test cases
    from test_dataset import TestCase, GroundTruthAnswer

    test_cases = [
        TestCase(
            test_id="TEST_001",
            category="documents",
            difficulty="easy",
            question="Đăng ký kết hôn cần giấy tờ gì?",
            ground_truth=GroundTruthAnswer(
                natural_language="...",
                key_facts=["CMND/CCCD - 02 bản", "Giấy xác nhận - 01 bản"],
                structured_data={},
                required_aspects=["Giấy tờ"]
            ),
            source_procedure="1.013124",
            metadata={}
        )
    ]

    # Mock answer generator
    def mock_answer_generator(question):
        return {
            "answer": "Cần CMND hoặc CCCD (02 bản sao) và giấy xác nhận tình trạng hôn nhân (01 bản chính).",
            "retrieval_time": 5.0,
            "generation_time": 30.0,
            "chunks_retrieved": 3
        }

    # Run evaluation
    report = evaluator.evaluate_batch(test_cases, mock_answer_generator)

    # Display
    print(evaluator.format_evaluation_report(report))

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_evaluator()
