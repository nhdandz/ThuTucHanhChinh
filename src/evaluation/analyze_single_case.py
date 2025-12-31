#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze a single test case in detail to find why metrics are low
"""

import sys
from pathlib import Path

# Add parent directories to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from evaluation.test_dataset import TestDatasetManager
from pipeline.rag_pipeline import ThuTucRAGPipeline
from evaluation.metrics import MetricsCalculator
import json

def analyze_case():
    """Analyze first test case in detail"""

    print("=" * 80)
    print("DETAILED ANALYSIS OF SINGLE TEST CASE")
    print("=" * 80)
    print()

    # Load test dataset
    manager = TestDatasetManager()
    manager.load_dataset("real_test_dataset.json")

    # Get first test case
    test_case = manager.test_cases[0]

    print("📋 TEST CASE INFO")
    print("-" * 80)
    print(f"ID: {test_case.test_id}")
    print(f"Category: {test_case.category}")
    print(f"Difficulty: {test_case.difficulty}")
    print(f"Source: {test_case.source_procedure}")
    print()
    print(f"QUESTION:")
    print(f"{test_case.question}")
    print()

    # Initialize RAG pipeline
    print("🚀 Initializing RAG pipeline...")
    rag_pipeline = ThuTucRAGPipeline(
        vector_store_path="../retrieval/qdrant_storage",
        embedding_model="bge-m3",
        llm_model="qwen3:8b",
        ollama_url="http://localhost:11434"
    )
    print()

    # Generate answer
    print("🔍 Generating answer...")
    result = rag_pipeline.answer_question(test_case.question, verbose=False)
    print()

    # Show retrieval results
    print("=" * 80)
    print("📊 RETRIEVAL RESULTS")
    print("-" * 80)
    print(f"Chunks retrieved: {len(result.sources)}")
    print()
    for i, source in enumerate(result.sources, 1):
        # SourceCitation is a dataclass, not a dict
        print(f"[{i}] Chunk: {source.chunk_id}")
        print(f"    Thủ tục: {source.thu_tuc_name}")
        print(f"    Type: {source.chunk_type}")
        print(f"    Score: {source.relevance_score:.3f}")
        print(f"    Content snippet:")
        print(f"    {source.content_snippet[:200]}...")
        print()

    # Show generated answer
    print("=" * 80)
    print("📝 GENERATED ANSWER")
    print("-" * 80)
    print(result.answer)
    print()

    print("Structured Data:")
    print(json.dumps(result.structured_data, ensure_ascii=False, indent=2))
    print()

    # Show ground truth
    print("=" * 80)
    print("✅ GROUND TRUTH")
    print("-" * 80)
    print("Natural Language:")
    print(test_case.ground_truth.natural_language)
    print()

    print("Key Facts:")
    for i, fact in enumerate(test_case.ground_truth.key_facts, 1):
        print(f"{i}. {fact}")
    print()

    print("Structured Data:")
    print(json.dumps(test_case.ground_truth.structured_data, ensure_ascii=False, indent=2))
    print()

    # Fact matching analysis
    print("=" * 80)
    print("🔍 FACT MATCHING ANALYSIS")
    print("-" * 80)

    calculator = MetricsCalculator()

    # Extract facts from generated answer
    generated_facts = calculator._extract_facts_from_answer(result.answer)

    print(f"Generated facts ({len(generated_facts)} extracted):")
    for i, fact in enumerate(generated_facts, 1):
        print(f"{i}. {fact}")
    print()

    print(f"Ground truth facts ({len(test_case.ground_truth.key_facts)}):")
    for i, fact in enumerate(test_case.ground_truth.key_facts, 1):
        print(f"{i}. {fact}")
    print()

    # Match each ground truth fact
    print("Matching results:")
    print("-" * 80)
    matched_count = 0

    for gt_fact in test_case.ground_truth.key_facts:
        print(f"\nGT: {gt_fact}")

        best_match = None
        best_score = 0

        for gen_fact in generated_facts:
            score = calculator._calculate_similarity(gt_fact, gen_fact)
            if score > best_score:
                best_score = score
                best_match = gen_fact

        if best_score >= 0.7:
            matched_count += 1
            print(f"✅ MATCHED (score: {best_score:.2f})")
            print(f"   GEN: {best_match}")
        else:
            print(f"❌ NO MATCH (best score: {best_score:.2f})")
            if best_match:
                print(f"   Best: {best_match}")

    print()
    print("-" * 80)
    print(f"Total matched: {matched_count}/{len(test_case.ground_truth.key_facts)}")
    print(f"Recall: {matched_count/len(test_case.ground_truth.key_facts)*100:.1f}%")
    print()

    # Check hallucination
    print("=" * 80)
    print("👻 HALLUCINATION CHECK")
    print("-" * 80)

    hallucinated = []
    for gen_fact in generated_facts:
        best_score = 0
        for gt_fact in test_case.ground_truth.key_facts:
            score = calculator._calculate_similarity(gen_fact, gt_fact)
            if score > best_score:
                best_score = score

        if best_score < 0.3:  # Likely hallucination
            hallucinated.append((gen_fact, best_score))

    if hallucinated:
        print(f"Possible hallucinations ({len(hallucinated)}):")
        for fact, score in hallucinated:
            print(f"  - {fact} (best match score: {score:.2f})")
    else:
        print("No obvious hallucinations detected")

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    analyze_case()
