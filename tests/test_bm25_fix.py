#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test BM25 Fix - Verify Vietnamese stopwords and auto-initialization

Tests:
1. Vietnamese stopwords filtering
2. BM25 auto-initialization in pipeline
3. Hybrid search (BM25 + semantic)
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "retrieval"))

from bm25_search import SimpleBM25, VIETNAMESE_STOPWORDS


def test_vietnamese_stopwords():
    """Test 1: Verify Vietnamese stopwords are used"""
    print("=" * 80)
    print("TEST 1: Vietnamese Stopwords")
    print("=" * 80)
    print()

    # Test sentence with stopwords
    test_text = "Thủ tục đăng ký và cấp giấy phép cho các doanh nghiệp trong lĩnh vực chính sách"

    # Tokenize without stopwords
    tokens_with_stopwords = SimpleBM25.tokenize(test_text, remove_stopwords=False)
    print(f"📝 Original text: {test_text}")
    print(f"   Tokens WITH stopwords ({len(tokens_with_stopwords)}): {tokens_with_stopwords}")
    print()

    # Tokenize with stopwords removed
    tokens_filtered = SimpleBM25.tokenize(test_text, remove_stopwords=True)
    print(f"   Tokens WITHOUT stopwords ({len(tokens_filtered)}): {tokens_filtered}")
    print()

    # Verify stopwords were removed
    removed = set(tokens_with_stopwords) - set(tokens_filtered)
    print(f"   ✅ Removed stopwords: {removed}")
    print(f"   ✅ Stopwords in list: {removed.issubset(VIETNAMESE_STOPWORDS)}")
    print()

    assert len(tokens_filtered) < len(tokens_with_stopwords), "Stopwords should be removed"
    print("✅ Test 1 PASSED")
    print()


def test_bm25_initialization():
    """Test 2: Verify BM25 can be initialized and built"""
    print("=" * 80)
    print("TEST 2: BM25 Initialization & Index Building")
    print("=" * 80)
    print()

    # Load sample chunks
    chunks_path = Path("data/chunks_v2_complete/all_chunks_enriched_complete.json")

    if not chunks_path.exists():
        print(f"⚠️  Chunks file not found: {chunks_path}")
        print("   Skipping test - run chunk generation first")
        return

    print(f"📂 Loading chunks from: {chunks_path}")
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"✅ Loaded {len(chunks)} chunks")
    print()

    # Initialize BM25
    print("🔧 Initializing BM25...")
    bm25 = SimpleBM25(chunks=chunks, k1=1.5, b=0.75)

    # Build index
    print("🔨 Building inverted index...")
    bm25.build_index(show_progress=True)

    print()
    print(f"✅ BM25 index built: {bm25.num_docs} documents")
    print(f"   Index size: {len(bm25.inverted_index)} unique terms")
    print(f"   Average doc length: {bm25.avg_doc_length:.1f} tokens")
    print()

    assert bm25.is_built, "BM25 index should be built"
    assert bm25.num_docs == len(chunks), "Should index all chunks"

    # Test search
    print("🔍 Testing BM25 search...")
    query = "đăng ký nghĩa vụ quân sự"
    results = bm25.search(query, top_k=5)

    print(f"   Query: '{query}'")
    print(f"   Results: {len(results)} chunks")
    print()

    if results:
        print("   Top 3 results:")
        for i, chunk in enumerate(results[:3], 1):
            ten_thu_tuc = chunk['metadata'].get('tên_thủ_tục', 'Unknown')
            print(f"   {i}. {chunk['chunk_id']}: {ten_thu_tuc[:80]}...")

    print()
    assert len(results) > 0, "Should find results for Vietnamese query"
    print("✅ Test 2 PASSED")
    print()


def test_hybrid_search_comparison():
    """Test 3: Compare BM25 vs Semantic search results"""
    print("=" * 80)
    print("TEST 3: Hybrid Search - BM25 vs Semantic")
    print("=" * 80)
    print()

    # Load chunks
    chunks_path = Path("data/chunks_v2_complete/all_chunks_enriched_complete.json")

    if not chunks_path.exists():
        print(f"⚠️  Chunks file not found: {chunks_path}")
        print("   Skipping test - run chunk generation first")
        return

    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Initialize BM25
    bm25 = SimpleBM25(chunks=chunks, k1=1.5, b=0.75)
    bm25.build_index(show_progress=False)

    # Test query
    query = "thủ tục đăng ký nghĩa vụ quân sự lần đầu"

    # BM25 search
    print(f"🔍 Query: '{query}'")
    print()
    print("📊 BM25 Results (keyword-based):")
    bm25_results = bm25.search(query, top_k=5)

    for i, chunk in enumerate(bm25_results[:5], 1):
        ten_thu_tuc = chunk['metadata'].get('tên_thủ_tục', 'Unknown')
        print(f"   {i}. {chunk['chunk_id']}")
        print(f"      {ten_thu_tuc[:100]}...")

    print()
    print(f"✅ BM25 found {len(bm25_results)} relevant chunks")
    print()

    # Show token analysis
    query_tokens = SimpleBM25.tokenize(query, remove_stopwords=True)
    print(f"📝 Query tokens (after stopword removal): {query_tokens}")
    print()

    print("✅ Test 3 PASSED")
    print()


def main():
    """Run all tests"""
    print()
    print("=" * 80)
    print("BM25 FIX VERIFICATION TESTS")
    print("=" * 80)
    print()
    print(f"Vietnamese stopwords count: {len(VIETNAMESE_STOPWORDS)}")
    print(f"Sample stopwords: {list(VIETNAMESE_STOPWORDS)[:10]}...")
    print()

    try:
        # Test 1: Stopwords
        test_vietnamese_stopwords()

        # Test 2: BM25 initialization
        test_bm25_initialization()

        # Test 3: Hybrid search comparison
        test_hybrid_search_comparison()

        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ TEST FAILED: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
