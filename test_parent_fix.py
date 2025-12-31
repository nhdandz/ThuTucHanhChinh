#!/usr/bin/env python3
"""Test that parent chunks are now included with chunk_type filter"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline.rag_pipeline import ThuTucRAGPipeline


def test_timeline_with_parent():
    """Test that timeline queries now include parent_overview chunks"""
    print("=" * 80)
    print("TEST: Timeline Query Should Include Parent Chunk")
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
    print(f"Chunk types: {chunk_types}")

    # Expected: parent_overview + child_process (2 chunks)
    if 'parent_overview' in chunk_types:
        print("✅ Parent chunk included")
    else:
        print("❌ Missing parent chunk (BUG!)")

    if 'child_process' in chunk_types:
        print("✅ Child process chunk included")
    else:
        print("❌ Missing child_process chunk")

    expected_chunks = 2  # 1 parent + 1 child_process
    if len(result.sources) == expected_chunks:
        print(f"✅ Correct number of chunks: {len(result.sources)}")
    else:
        print(f"⚠️  Expected {expected_chunks} chunks, got {len(result.sources)}")

    print()


if __name__ == "__main__":
    try:
        test_timeline_with_parent()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
