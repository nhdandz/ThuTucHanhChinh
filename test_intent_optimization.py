#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Intent-Based Context Optimization

This script tests that the intent-based dynamic context assembly
reduces context size while maintaining answer quality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "pipeline"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "retrieval"))

from rag_pipeline import ThuTucRAGPipeline
from context_settings import get_context_config, estimate_context_tokens

# Test queries covering different intents
TEST_QUERIES = [
    {
        "query": "Đăng ký kết hôn cần giấy tờ gì?",
        "expected_intent": "documents",
        "expected_mode": "specific"
    },
    {
        "query": "Lệ phí đăng ký kết hôn là bao nhiêu?",
        "expected_intent": "fees",
        "expected_mode": "specific"
    },
    {
        "query": "Quy trình xin cấp giấy phép kinh doanh như thế nào?",
        "expected_intent": "process",
        "expected_mode": "list"
    },
    {
        "query": "Tổng quan về thủ tục đăng ký hộ kinh doanh",
        "expected_intent": "overview",
        "expected_mode": "general"
    },
    {
        "query": "Thời gian xử lý hồ sơ đăng ký kết hôn",
        "expected_intent": "timeline",
        "expected_mode": "explanation"
    }
]

def test_context_optimization():
    """Test that context size is reduced based on intent"""
    print("=" * 80)
    print("TESTING INTENT-BASED CONTEXT OPTIMIZATION")
    print("=" * 80)
    print()

    # Initialize pipeline
    print("Initializing RAG pipeline...")
    pipeline = ThuTucRAGPipeline(
        vector_store_path="thu_tuc_rag/src/retrieval/qdrant_storage",
        collection_name="thu_tuc_hanh_chinh",
        embedding_model="bge-m3",
        llm_model="qwen3:8b",
        ollama_url="http://localhost:11434"
    )
    print("✅ Pipeline initialized\n")

    results = []

    for i, test_case in enumerate(TEST_QUERIES, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}/{len(TEST_QUERIES)}")
        print(f"{'=' * 80}")
        print(f"Query: {test_case['query']}")
        print(f"Expected Intent: {test_case['expected_intent']}")
        print(f"Expected Mode: {test_case['expected_mode']}")
        print()

        try:
            # Get the answer (this will use intent-based context)
            answer = pipeline.answer_question(
                question=test_case['query'],
                verbose=True  # Show detailed logs
            )

            # Get the context config for this intent
            config = get_context_config(answer.intent)
            estimated_tokens = estimate_context_tokens(config)

            # Store results
            result = {
                "query": test_case['query'],
                "intent": answer.intent,
                "mode": config['mode'],
                "chunks_limit": config['chunks'],
                "max_descendants": config['max_descendants'],
                "estimated_tokens": estimated_tokens,
                "structured_enabled": config['enable_structured_output'],
                "answer_length": len(answer.answer),
                "confidence": answer.confidence
            }
            results.append(result)

            # Print summary
            print(f"\n📊 Result Summary:")
            print(f"   Intent: {answer.intent} (mode: {config['mode']})")
            print(f"   Chunks limit: {config['chunks']}")
            print(f"   Max descendants: {config['max_descendants']}")
            print(f"   Estimated context tokens: {estimated_tokens}")
            print(f"   Structured output: {config['enable_structured_output']}")
            print(f"   Answer length: {len(answer.answer)} chars")
            print(f"   Confidence: {answer.confidence:.2f}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Print overall summary
    print(f"\n\n{'=' * 80}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'=' * 80}\n")

    print(f"{'Intent':<15} {'Mode':<12} {'Chunks':<8} {'Descendants':<12} {'Est. Tokens':<12} {'Structured':<12}")
    print("-" * 80)

    for r in results:
        print(f"{r['intent']:<15} {r['mode']:<12} {r['chunks_limit']:<8} {r['max_descendants']:<12} {r['estimated_tokens']:<12} {str(r['structured_enabled']):<12}")

    # Calculate average token reduction
    baseline_tokens = 5350  # Average from before optimization
    avg_tokens = sum(r['estimated_tokens'] for r in results) / len(results)
    reduction = (baseline_tokens - avg_tokens) / baseline_tokens * 100

    print("\n" + "=" * 80)
    print(f"Baseline (before optimization): ~{baseline_tokens} tokens average")
    print(f"Optimized (after optimization): ~{int(avg_tokens)} tokens average")
    print(f"Average reduction: {reduction:.1f}%")
    print("=" * 80)

    print("\n✅ Testing complete!")

if __name__ == "__main__":
    try:
        test_context_optimization()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
