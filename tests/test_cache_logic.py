#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Semantic Cache Logic - Verify cache get/put flow

Tests cache logic without needing full pipeline:
1. Cache initialization
2. Get/Put operations
3. Semantic similarity matching
4. Statistics tracking
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "retrieval"))

from semantic_cache import SemanticCache
import numpy as np


def create_mock_embedding(seed: int, dim: int = 1024) -> list:
    """Create deterministic embedding for testing"""
    np.random.seed(seed)
    vec = np.random.randn(dim)
    # Normalize
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def create_similar_embedding(base_embedding: list, noise_level: float = 0.01) -> list:
    """Create similar embedding with small noise"""
    base = np.array(base_embedding)
    noise = np.random.randn(len(base)) * noise_level
    vec = base + noise
    # Normalize
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def test_cache_logic():
    """Test semantic cache logic"""
    print("=" * 80)
    print("SEMANTIC CACHE LOGIC TEST")
    print("=" * 80)
    print()

    # Initialize cache
    print("TEST 1: Cache Initialization")
    print("-" * 80)
    cache = SemanticCache(
        max_size=100,
        ttl_hours=24.0,
        similarity_threshold=0.92
    )
    print("✅ Cache initialized")
    print()

    # Test 2: First query (MISS)
    print("TEST 2: First Query - Cache MISS")
    print("-" * 80)
    query1 = "đăng ký nghĩa vụ quân sự lần đầu"
    emb1 = create_mock_embedding(seed=1)
    result1 = {"answer": "Mocked result 1", "chunks": [1, 2, 3]}

    cached = cache.get(query1, emb1)
    assert cached is None, "Should be cache miss"
    print(f"   ✅ Cache MISS (as expected)")

    # Store in cache
    cache.put(query1, emb1, result1)
    print(f"   ✅ Result cached")

    # Check stats
    stats = cache.get_stats()
    print(f"   📊 Stats: {stats['hits']} hits, {stats['misses']} misses")
    assert stats['misses'] == 1 and stats['hits'] == 0
    print()

    # Test 3: Identical query (HIT)
    print("TEST 3: Identical Query - Cache HIT")
    print("-" * 80)
    query2 = "đăng ký nghĩa vụ quân sự lần đầu"  # Same
    emb2 = emb1  # Same embedding

    cached = cache.get(query2, emb2)
    assert cached is not None, "Should be cache hit"
    assert cached == result1, "Should return exact same result"
    print(f"   ✅ Cache HIT (exact match)")

    # Check stats
    stats = cache.get_stats()
    print(f"   📊 Stats: {stats['hits']} hits, {stats['misses']} misses")
    print(f"   📊 Hit rate: {stats['hit_rate']:.1%}")
    assert stats['hits'] == 1 and stats['misses'] == 1
    print()

    # Test 4: Similar query (semantic HIT)
    print("TEST 4: Similar Query - Semantic Cache HIT")
    print("-" * 80)
    query3 = "đăng ký nvqs lần đầu"  # Similar
    emb3 = create_similar_embedding(emb1, noise_level=0.005)  # Very similar

    # Calculate similarity
    similarity = cache._cosine_similarity(emb1, emb3)
    print(f"   Similarity: {similarity:.4f} (threshold: {cache.similarity_threshold})")

    cached = cache.get(query3, emb3)

    if similarity >= cache.similarity_threshold:
        assert cached is not None, "Should be semantic cache hit"
        assert cached == result1, "Should return same result via semantic matching"
        print(f"   ✅ Semantic Cache HIT (similarity {similarity:.4f} ≥ {cache.similarity_threshold})")
    else:
        assert cached is None, "Should be cache miss (similarity too low)"
        print(f"   ❌ Cache MISS (similarity {similarity:.4f} < {cache.similarity_threshold})")

    stats = cache.get_stats()
    print(f"   📊 Stats: {stats['hits']} hits, {stats['misses']} misses")
    print(f"   📊 Hit rate: {stats['hit_rate']:.1%}")
    print()

    # Test 5: Different query (MISS)
    print("TEST 5: Different Query - Cache MISS")
    print("-" * 80)
    query4 = "thủ tục cấp giấy phép kinh doanh"
    emb4 = create_mock_embedding(seed=99)  # Completely different

    similarity = cache._cosine_similarity(emb1, emb4)
    print(f"   Similarity to cached query: {similarity:.4f}")

    cached = cache.get(query4, emb4)
    assert cached is None, "Should be cache miss (different query)"
    print(f"   ✅ Cache MISS (as expected)")

    stats = cache.get_stats()
    print(f"   📊 Stats: {stats['hits']} hits, {stats['misses']} misses")
    print(f"   📊 Hit rate: {stats['hit_rate']:.1%}")
    print()

    # Final statistics
    print("=" * 80)
    print("FINAL CACHE STATISTICS")
    print("=" * 80)
    cache.print_stats()

    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print()

    # Summary
    final_stats = cache.get_stats()
    print("Summary:")
    print(f"   - Total queries: {final_stats['total_queries']}")
    print(f"   - Cache hits: {final_stats['hits']}")
    print(f"   - Cache misses: {final_stats['misses']}")
    print(f"   - Hit rate: {final_stats['hit_rate']:.1%}")
    print(f"   - Cache size: {final_stats['size']}/{final_stats['max_size']}")


if __name__ == "__main__":
    test_cache_logic()
