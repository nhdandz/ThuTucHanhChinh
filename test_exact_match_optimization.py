#!/usr/bin/env python3
"""
Test Exact Match Optimization

Tests that exact match now uses intent-based filtering and config
to reduce context length while maintaining correctness.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline.rag_pipeline import ThuTucRAGPipeline


def test_requirements_with_exact_code():
    """
    Test Case 1: Requirements intent with exact code
    Should filter to child_requirements chunks only
    """
    print("=" * 80)
    print("TEST 1: Requirements Query with Exact Code (1.013140)")
    print("=" * 80)

    pipeline = ThuTucRAGPipeline()

    question = "Một quân nhân nhập ngũ trước ngày 30/4/1975 và có 22 năm phục vụ quân đội nhưng hiện đang hưởng chế độ mất sức lao động hàng tháng thì có đủ điều kiện hưởng chế độ hưu trí theo thủ tục 1.013140 không?"

    print(f"\nQuery: {question}")
    print()

    result = pipeline.answer_question(question, top_k_parent=5, top_k_child=20, top_k_final=2)

    print("\n📊 RESULTS:")
    print(f"Intent detected: {result.intent}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Number of sources: {len(result.sources)}")

    # Check chunk types
    chunk_types = set(s.chunk_type for s in result.sources)
    print(f"Chunk types retrieved: {chunk_types}")

    # Expected: Only child_requirements chunks (plus parent_overview)
    if 'child_requirements' in chunk_types:
        print("✅ Contains child_requirements chunks")
    else:
        print("❌ Missing child_requirements chunks")

    # Should NOT contain other types like child_documents, child_legal, etc.
    unwanted_types = {'child_documents', 'child_legal', 'child_fees_timing', 'child_agencies'}
    if chunk_types & unwanted_types:
        print(f"⚠️  WARNING: Contains unwanted chunk types: {chunk_types & unwanted_types}")
    else:
        print("✅ No unwanted chunk types (optimization working)")

    print(f"\nAnswer preview: {result.answer[:200]}...")
    print()


def test_timeline_with_exact_code():
    """
    Test Case 2: Timeline intent with exact code
    Should filter to child_process chunks and still work correctly
    """
    print("=" * 80)
    print("TEST 2: Timeline Query with Exact Code (1.013614)")
    print("=" * 80)

    pipeline = ThuTucRAGPipeline()

    question = "Thời hạn giải quyết thủ tục 1.013614 là bao lâu?"

    print(f"\nQuery: {question}")
    print()

    result = pipeline.answer_question(question, top_k_parent=5, top_k_child=20, top_k_final=2)

    print("\n📊 RESULTS:")
    print(f"Intent detected: {result.intent}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Number of sources: {len(result.sources)}")

    # Check chunk types
    chunk_types = set(s.chunk_type for s in result.sources)
    print(f"Chunk types retrieved: {chunk_types}")

    # Expected: child_process chunks
    if 'child_process' in chunk_types:
        print("✅ Contains child_process chunks")
    else:
        print("❌ Missing child_process chunks")

    # Check answer mentions timeline
    if "03 ngày làm việc" in result.answer or "3 ngày" in result.answer:
        print("✅ Answer contains correct timeline")
    else:
        print("⚠️  Answer doesn't mention expected timeline")

    print(f"\nAnswer: {result.answer}")
    print()


def test_overview_with_exact_code():
    """
    Test Case 3: Overview intent with exact code
    Should return all chunk types (no chunk_type filter)
    """
    print("=" * 80)
    print("TEST 3: Overview Query with Exact Code (1.013140)")
    print("=" * 80)

    pipeline = ThuTucRAGPipeline()

    question = "Cho tôi biết về thủ tục 1.013140"

    print(f"\nQuery: {question}")
    print()

    result = pipeline.answer_question(question, top_k_parent=5, top_k_child=20, top_k_final=2)

    print("\n📊 RESULTS:")
    print(f"Intent detected: {result.intent}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Number of sources: {len(result.sources)}")

    # Check chunk types
    chunk_types = set(s.chunk_type for s in result.sources)
    print(f"Chunk types retrieved: {chunk_types}")

    # Expected: Multiple chunk types (comprehensive overview)
    if len(chunk_types) >= 3:
        print(f"✅ Multiple chunk types retrieved ({len(chunk_types)} types)")
    else:
        print(f"⚠️  Only {len(chunk_types)} chunk types (expected >= 3 for overview)")

    print(f"\nAnswer preview: {result.answer[:200]}...")
    print()


if __name__ == "__main__":
    try:
        # Run all test cases
        test_requirements_with_exact_code()
        test_timeline_with_exact_code()
        test_overview_with_exact_code()

        print("=" * 80)
        print("✅ ALL TESTS COMPLETE")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
