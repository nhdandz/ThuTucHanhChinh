#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug Evaluation - Check one test case in detail
"""

import sys
from pathlib import Path

# Add parent directories to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from evaluation.test_dataset import TestDatasetManager
from evaluation.metrics import MetricsCalculator
from pipeline.rag_pipeline import ThuTucRAGPipeline

def debug_test_case():
    """Debug a single test case in detail"""

    print("=" * 80)
    print("DEBUG EVALUATION - TEST CASE DETAIL")
    print("=" * 80)
    print()

    # 1. Load test dataset
    print("📂 Loading test dataset...")
    manager = TestDatasetManager()
    manager.load_dataset("comprehensive_test_dataset.json")

    # Get first test case
    test_case = manager.test_cases[0]

    print(f"\n🧪 Test Case: {test_case.test_id}")
    print(f"   Category: {test_case.category}")
    print(f"   Difficulty: {test_case.difficulty}")
    print(f"   Question: {test_case.question}")
    print()

    # 2. Show ground truth
    print("=" * 80)
    print("📋 GROUND TRUTH")
    print("=" * 80)
    print()

    print("Natural Language Answer:")
    print(test_case.ground_truth.natural_language)
    print()

    print("Key Facts:")
    for i, fact in enumerate(test_case.ground_truth.key_facts, 1):
        print(f"  {i}. {fact}")
    print()

    print("Structured Data:")
    import json
    print(json.dumps(test_case.ground_truth.structured_data, ensure_ascii=False, indent=2))
    print()

    print("Required Aspects:")
    for aspect in test_case.ground_truth.required_aspects:
        print(f"  - {aspect}")
    print()

    # 3. Initialize RAG pipeline
    print("=" * 80)
    print("🚀 RUNNING RAG PIPELINE")
    print("=" * 80)
    print()

    rag_pipeline = ThuTucRAGPipeline(
        vector_store_path="../retrieval/qdrant_storage",
        embedding_model="bge-m3",
        llm_model="qwen3:8b",
        ollama_url="http://localhost:11434"
    )

    # Generate answer
    result = rag_pipeline.answer_question(test_case.question, verbose=True)

    print()
    print("=" * 80)
    print("📄 GENERATED ANSWER")
    print("=" * 80)
    print()

    print("Natural Language Answer:")
    print(result.answer)
    print()

    print("Structured Data:")
    print(json.dumps(result.structured_data, ensure_ascii=False, indent=2))
    print()

    print("Sources:")
    for i, source in enumerate(result.sources, 1):
        print(f"  {i}. {source.get('chunk_id', 'N/A')} (score: {source.get('score', 0):.3f})")
    print()

    # 4. Evaluate with MetricsCalculator
    print("=" * 80)
    print("📊 METRICS CALCULATION")
    print("=" * 80)
    print()

    calculator = MetricsCalculator(
        accuracy_threshold=0.95,
        precision_threshold=0.90,
        recall_threshold=0.90,
        f1_threshold=0.90,
        hallucination_threshold=0.05
    )

    # Calculate metrics
    metrics = calculator.calculate_metrics(
        generated_answer=result.answer,
        ground_truth_answer=test_case.ground_truth.natural_language,
        ground_truth_facts=test_case.ground_truth.key_facts,
        required_aspects=test_case.ground_truth.required_aspects
    )

    print("Metrics Results:")
    print(f"  Accuracy: {metrics.accuracy:.1%}")
    print(f"  Precision: {metrics.precision:.1%}")
    print(f"  Recall: {metrics.recall:.1%}")
    print(f"  F1-Score: {metrics.f1_score:.1%}")
    print(f"  Hallucination Rate: {metrics.hallucination_rate:.1%}")
    print(f"  Completeness: {metrics.completeness:.1%}")
    print()

    # 5. Show fact extraction details
    print("=" * 80)
    print("🔍 FACT EXTRACTION DETAIL")
    print("=" * 80)
    print()

    print("Ground Truth Facts:")
    for i, fact in enumerate(test_case.ground_truth.key_facts, 1):
        print(f"  {i}. {fact}")
    print()

    # Extract facts from generated answer
    from evaluation.metrics import FactMatcher
    matcher = FactMatcher()

    # Extract facts from generated answer
    generated_facts = matcher.extract_facts(result.answer)
    print(f"Generated Facts ({len(generated_facts)} extracted):")
    for i, fact in enumerate(generated_facts, 1):
        print(f"  {i}. {fact}")
    print()

    # Show matching
    print("Fact Matching:")
    matched = 0
    for gt_fact in test_case.ground_truth.key_facts:
        best_match = None
        best_score = 0

        for gen_fact in generated_facts:
            score = matcher.calculate_similarity(gt_fact, gen_fact)
            if score > best_score:
                best_score = score
                best_match = gen_fact

        if best_score >= 0.7:
            matched += 1
            print(f"  ✅ '{gt_fact}'")
            print(f"      → Matched: '{best_match}' (score: {best_score:.2f})")
        else:
            print(f"  ❌ '{gt_fact}'")
            if best_match:
                print(f"      → Best: '{best_match}' (score: {best_score:.2f})")

    print()
    print(f"Matched: {matched}/{len(test_case.ground_truth.key_facts)} facts")
    print()


if __name__ == "__main__":
    debug_test_case()
