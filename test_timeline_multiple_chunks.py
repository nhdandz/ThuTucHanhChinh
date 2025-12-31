#!/usr/bin/env python3
"""Test that timeline queries now retrieve both child_process AND child_fees_timing chunks"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline.rag_pipeline import ThuTucRAGPipeline


def test_timeline_multiple_chunk_types():
    """Test that timeline queries now include BOTH process and fees_timing chunks"""
    print("=" * 80)
    print("TEST: Timeline Query Should Include Multiple Chunk Types")
    print("=" * 80)

    pipeline = ThuTucRAGPipeline()

    question = "Thời gian giải quyết của 'Thủ tục đăng ký nghĩa vụ quân sự lần đầu' (Mã 1.013133) là bao lâu?"

    print(f"\nQuery: {question}")
    print()

    result = pipeline.answer_question(question, top_k_parent=5, top_k_child=20, top_k_final=2)

    print("\n📊 RESULTS:")
    print(f"Intent: {result.intent}")
    print(f"Sources: {len(result.sources)}")

    # Check chunk types
    chunk_types = [s.chunk_type for s in result.sources]
    print(f"\nChunk types retrieved: {chunk_types}")

    # Expected: parent_overview + child_process + child_fees_timing (3 chunks)
    expected_types = {'parent_overview', 'child_process', 'child_fees_timing'}
    actual_types = set(chunk_types)

    print("\n✅ Expected chunk types:")
    for ct in expected_types:
        if ct in actual_types:
            print(f"   ✅ {ct}")
        else:
            print(f"   ❌ {ct} (MISSING!)")

    # Check if answer contains both timelines
    print("\n📝 Checking answer content:")
    if "1 Ngày làm việc" in result.answer or "1 ngày" in result.answer:
        print("   ✅ Contains in-person timeline (1 Ngày)")
    else:
        print("   ⚠️  Missing in-person timeline")

    if "02 Giờ" in result.answer or "2 giờ" in result.answer or "trực tuyến" in result.answer.lower():
        print("   ✅ Contains online timeline (02 Giờ)")
    else:
        print("   ❌ Missing online timeline (THIS IS THE BUG WE'RE FIXING!)")

    print(f"\nFull answer:\n{result.answer}")
    print()


if __name__ == "__main__":
    try:
        test_timeline_multiple_chunk_types()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
