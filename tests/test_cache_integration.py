#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Semantic Cache Integration - Verify cache works in retrieval pipeline

Tests:
1. First query creates cache entry (MISS)
2. Identical query returns cached result (HIT)
3. Similar query returns cached result (HIT via semantic matching)
4. Cache statistics tracking
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "retrieval"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "embeddings"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "vectorstore"))

from retrieval_pipeline import RetrievalPipeline
from ollama_embedder import OllamaEmbedder
from qdrant_vector_store import QdrantVectorStore
from query_enhancer import OllamaQueryEnhancer


def test_cache_integration():
    """Test cache integration in retrieval pipeline"""
    print("=" * 80)
    print("CACHE INTEGRATION TEST")
    print("=" * 80)
    print()

    # Load chunks
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

    # Load embeddings
    embeddings_path = Path("data/embeddings/enriched_embeddings.json")

    if not embeddings_path.exists():
        print(f"⚠️  Embeddings file not found: {embeddings_path}")
        print("   Skipping test - run embedding generation first")
        return

    print(f"📂 Loading embeddings from: {embeddings_path}")
    with open(embeddings_path, 'r', encoding='utf-8') as f:
        chunks_with_embeddings = json.load(f)
    print(f"✅ Loaded {len(chunks_with_embeddings)} chunks with embeddings")
    print()

    # Initialize components
    print("🔧 Initializing components...")
    embedder = OllamaEmbedder(model_name="bge-m3")
    query_enhancer = OllamaQueryEnhancer(model_name="qwen2.5:7b")

    # Initialize vector store
    vector_store = QdrantVectorStore(
        collection_name="thu_tuc_test_cache",
        embedding_dim=1024
    )

    # Check if collection exists and has data
    try:
        collection_info = vector_store.client.get_collection(
            collection_name="thu_tuc_test_cache"
        )
        points_count = collection_info.points_count

        if points_count == 0:
            print(f"   ⚠️  Collection empty, indexing {len(chunks_with_embeddings)} chunks...")
            vector_store.index_chunks(chunks_with_embeddings)
        else:
            print(f"   ✅ Collection ready with {points_count} points")

    except Exception as e:
        print(f"   📦 Creating new collection and indexing chunks...")
        vector_store.index_chunks(chunks_with_embeddings)

    # Initialize retrieval pipeline WITH cache enabled
    print("🔧 Initializing retrieval pipeline with cache...")
    pipeline = RetrievalPipeline(
        embedder=embedder,
        vector_store=vector_store,
        query_enhancer=query_enhancer,
        chunks=chunks,
        auto_init_bm25=True,
        use_reranker=True,
        use_cache=True  # Enable cache
    )
    print()

    # Test 1: First query (MISS)
    print("=" * 80)
    print("TEST 1: First Query - Cache MISS")
    print("=" * 80)
    query1 = "đăng ký nghĩa vụ quân sự lần đầu"
    print(f"Query: '{query1}'")
    print()

    result1 = pipeline.retrieve(query1, top_k_final=3)
    print()
    print(f"✅ Retrieved {len(result1.retrieved_chunks)} chunks")
    print(f"   Confidence: {result1.confidence:.2f}")
    print()

    # Check cache stats
    stats1 = pipeline.cache.get_stats()
    print(f"📊 Cache Stats after Query 1:")
    print(f"   Total queries: {stats1['total_queries']}")
    print(f"   Hits: {stats1['hits']}")
    print(f"   Misses: {stats1['misses']}")
    print(f"   Hit rate: {stats1['hit_rate']:.1%}")
    assert stats1['misses'] == 1, "First query should be a miss"
    print()

    # Test 2: Identical query (HIT)
    print("=" * 80)
    print("TEST 2: Identical Query - Cache HIT")
    print("=" * 80)
    query2 = "đăng ký nghĩa vụ quân sự lần đầu"  # Same query
    print(f"Query: '{query2}'")
    print()

    result2 = pipeline.retrieve(query2, top_k_final=3)
    print()
    print(f"✅ Retrieved {len(result2.retrieved_chunks)} chunks")
    print()

    # Check cache stats
    stats2 = pipeline.cache.get_stats()
    print(f"📊 Cache Stats after Query 2:")
    print(f"   Total queries: {stats2['total_queries']}")
    print(f"   Hits: {stats2['hits']}")
    print(f"   Misses: {stats2['misses']}")
    print(f"   Hit rate: {stats2['hit_rate']:.1%}")
    assert stats2['hits'] == 1, "Identical query should be a hit"
    assert result2 == result1, "Cached result should be identical"
    print()

    # Test 3: Similar query (semantic HIT)
    print("=" * 80)
    print("TEST 3: Similar Query - Semantic Cache HIT")
    print("=" * 80)
    query3 = "đăng ký nvqs lần đầu"  # Similar query (nvqs = nghĩa vụ quân sự)
    print(f"Query: '{query3}'")
    print()

    result3 = pipeline.retrieve(query3, top_k_final=3)
    print()

    # Check cache stats
    stats3 = pipeline.cache.get_stats()
    print(f"📊 Cache Stats after Query 3:")
    print(f"   Total queries: {stats3['total_queries']}")
    print(f"   Hits: {stats3['hits']}")
    print(f"   Misses: {stats3['misses']}")
    print(f"   Hit rate: {stats3['hit_rate']:.1%}")
    print()

    # Test 4: Different query (MISS)
    print("=" * 80)
    print("TEST 4: Different Query - Cache MISS")
    print("=" * 80)
    query4 = "thủ tục cấp giấy phép kinh doanh"
    print(f"Query: '{query4}'")
    print()

    result4 = pipeline.retrieve(query4, top_k_final=3)
    print()
    print(f"✅ Retrieved {len(result4.retrieved_chunks)} chunks")
    print()

    # Final stats
    print("=" * 80)
    print("FINAL CACHE STATISTICS")
    print("=" * 80)
    pipeline.cache.print_stats()
    print()

    print("=" * 80)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 80)


if __name__ == "__main__":
    test_cache_integration()
