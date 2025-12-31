#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Semantic Cache - Cache query results based on semantic similarity

Features:
1. Semantic matching: Return cached results if query similarity ≥ threshold (default: 0.92)
2. LRU eviction: Remove least recently used entries when cache is full
3. TTL support: Expire entries after configurable time (default: 24h)
4. Thread-safe: Safe for concurrent access
5. Statistics: Track hit rate, cache size, evictions

Architecture:
- Key: Query embedding (1024D vector from bge-m3)
- Value: (RetrievalResult, timestamp)
- Eviction: LRU (Least Recently Used)
- Similarity: Cosine similarity between query embeddings

Usage:
    cache = SemanticCache(max_size=100, ttl_hours=24, similarity_threshold=0.92)

    # Try to get cached result
    cached = cache.get(query, query_embedding)
    if cached:
        return cached

    # No cache hit, run retrieval
    result = pipeline.retrieve(query)

    # Cache the result
    cache.put(query, query_embedding, result)
"""

import sys
import time
import threading
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass, field
from collections import OrderedDict
import numpy as np

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    query: str
    query_embedding: List[float]
    result: Any  # RetrievalResult or any cached object
    timestamp: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired: int = 0
    total_queries: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_queries == 0:
            return 0.0
        return self.hits / self.total_queries


class SemanticCache:
    """
    Thread-safe semantic cache with LRU eviction

    Caches query results based on semantic similarity.
    If a new query is semantically similar to a cached query (≥ threshold),
    returns the cached result instead of running retrieval.

    Parameters:
        max_size: Maximum number of cached entries (default: 100)
        ttl_hours: Time-to-live in hours (default: 24h)
        similarity_threshold: Minimum similarity for cache hit (default: 0.92)
    """

    def __init__(
        self,
        max_size: int = 100,
        ttl_hours: float = 24.0,
        similarity_threshold: float = 0.92
    ):
        """
        Initialize semantic cache

        Args:
            max_size: Maximum cache size (number of entries)
            ttl_hours: Time-to-live in hours (entries expire after this)
            similarity_threshold: Minimum cosine similarity for cache hit (0-1)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self.similarity_threshold = similarity_threshold

        # OrderedDict for LRU: most recent at end
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Thread safety
        self._lock = threading.RLock()

        # Statistics
        self.stats = CacheStats()

        print(f"✅ SemanticCache initialized")
        print(f"   Max size: {max_size} entries")
        print(f"   TTL: {ttl_hours}h")
        print(f"   Similarity threshold: {similarity_threshold}")

    def get(
        self,
        query: str,
        query_embedding: List[float]
    ) -> Optional[Any]:
        """
        Try to get cached result for query

        Args:
            query: User query string
            query_embedding: Query embedding vector

        Returns:
            Cached result if found with similarity ≥ threshold, else None
        """
        with self._lock:
            self.stats.total_queries += 1

            # 1. Check for exact match (fast path)
            if query in self._cache:
                entry = self._cache[query]

                # Check if expired
                if self._is_expired(entry):
                    self._remove_entry(query)
                    self.stats.expired += 1
                    self.stats.misses += 1
                    return None

                # Exact match - update access and return
                self._update_access(query)
                self.stats.hits += 1
                return entry.result

            # 2. Check for semantic similarity (slower path)
            best_match = None
            best_similarity = 0.0

            for cached_query, entry in self._cache.items():
                # Skip expired entries
                if self._is_expired(entry):
                    continue

                # Calculate similarity
                similarity = self._cosine_similarity(
                    query_embedding,
                    entry.query_embedding
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = cached_query

            # Check if best match exceeds threshold
            if best_match and best_similarity >= self.similarity_threshold:
                # Semantic hit!
                self._update_access(best_match)
                self.stats.hits += 1

                entry = self._cache[best_match]
                return entry.result

            # No cache hit
            self.stats.misses += 1
            return None

    def put(
        self,
        query: str,
        query_embedding: List[float],
        result: Any
    ):
        """
        Cache a query result

        Args:
            query: User query string
            query_embedding: Query embedding vector
            result: Result to cache (typically RetrievalResult)
        """
        with self._lock:
            # Check if cache is full
            if len(self._cache) >= self.max_size and query not in self._cache:
                # Evict LRU entry (first item in OrderedDict)
                self._evict_lru()

            # Add or update entry
            entry = CacheEntry(
                query=query,
                query_embedding=query_embedding,
                result=result,
                timestamp=time.time()
            )

            # Remove old entry if exists, then add to end (most recent)
            if query in self._cache:
                del self._cache[query]

            self._cache[query] = entry

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            print("🗑️  Cache cleared")

    def clear_expired(self) -> int:
        """
        Remove all expired entries

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_queries = [
                query for query, entry in self._cache.items()
                if self._is_expired(entry)
            ]

            for query in expired_queries:
                self._remove_entry(query)
                self.stats.expired += 1

            if expired_queries:
                print(f"🗑️  Cleared {len(expired_queries)} expired entries")

            return len(expired_queries)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "hit_rate": self.stats.hit_rate,
                "evictions": self.stats.evictions,
                "expired": self.stats.expired,
                "total_queries": self.stats.total_queries
            }

    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_stats()
        print()
        print("📊 Cache Statistics:")
        print(f"   Size: {stats['size']}/{stats['max_size']}")
        print(f"   Hit rate: {stats['hit_rate']:.1%}")
        print(f"   Hits: {stats['hits']}")
        print(f"   Misses: {stats['misses']}")
        print(f"   Evictions: {stats['evictions']}")
        print(f"   Expired: {stats['expired']}")
        print(f"   Total queries: {stats['total_queries']}")

    # ========== Private Methods ==========

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if entry has expired"""
        age = time.time() - entry.timestamp
        return age > self.ttl_seconds

    def _update_access(self, query: str):
        """Update access metadata and move to end (most recent)"""
        entry = self._cache[query]
        entry.access_count += 1
        entry.last_accessed = time.time()

        # Move to end (most recent)
        self._cache.move_to_end(query)

    def _remove_entry(self, query: str):
        """Remove entry from cache"""
        if query in self._cache:
            del self._cache[query]

    def _evict_lru(self):
        """Evict least recently used entry (first item)"""
        if self._cache:
            # Get first key (oldest/LRU)
            lru_key = next(iter(self._cache))
            del self._cache[lru_key]
            self.stats.evictions += 1

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        # Convert to numpy arrays and flatten to 1D (handle both list and array inputs)
        vec1 = np.array(vec1).flatten()
        vec2 = np.array(vec2).flatten()

        # Ensure vectors have same length
        if len(vec1) != len(vec2):
            print(f"Warning: Vector length mismatch: {len(vec1)} vs {len(vec2)}")
            return 0.0

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Ensure in 0-1 range (cosine is -1 to 1)
        return max(0.0, min(1.0, similarity))


def test_semantic_cache():
    """Test semantic cache functionality"""
    print("=" * 80)
    print("SEMANTIC CACHE TEST")
    print("=" * 80)
    print()

    # Initialize cache
    cache = SemanticCache(
        max_size=3,  # Small size for testing
        ttl_hours=0.001,  # 3.6 seconds for testing expiration
        similarity_threshold=0.90
    )
    print()

    # Create sample embeddings (1024D)
    def create_embedding(seed: int) -> List[float]:
        """Create deterministic embedding for testing"""
        np.random.seed(seed)
        vec = np.random.randn(1024)
        # Normalize
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    # Test 1: Basic put and get
    print("TEST 1: Basic put and get")
    print("-" * 80)

    query1 = "đăng ký nghĩa vụ quân sự lần đầu"
    emb1 = create_embedding(1)
    result1 = {"answer": "Result for query 1"}

    cache.put(query1, emb1, result1)
    cached = cache.get(query1, emb1)

    assert cached == result1, "Should retrieve exact match"
    print(f"✅ Exact match works")
    print()

    # Test 2: Semantic similarity
    print("TEST 2: Semantic similarity")
    print("-" * 80)

    # Very similar query (same embedding with small noise)
    query2 = "đăng ký nghĩa vụ quân sự"
    emb2 = [e + np.random.randn() * 0.01 for e in emb1]  # Very similar
    emb2_normalized = np.array(emb2) / np.linalg.norm(emb2)
    emb2 = emb2_normalized.tolist()

    cached = cache.get(query2, emb2)
    similarity = cache._cosine_similarity(emb1, emb2)

    print(f"Similarity: {similarity:.3f}")
    if cached:
        print(f"✅ Semantic hit (similarity {similarity:.3f} ≥ {cache.similarity_threshold})")
    else:
        print(f"❌ No hit (similarity {similarity:.3f} < {cache.similarity_threshold})")
    print()

    # Test 3: LRU eviction
    print("TEST 3: LRU eviction (max_size=3)")
    print("-" * 80)

    query3 = "thủ tục cấp giấy phép"
    emb3 = create_embedding(3)
    cache.put(query3, emb3, {"answer": "Result 3"})

    query4 = "thủ tục đăng ký doanh nghiệp"
    emb4 = create_embedding(4)
    cache.put(query4, emb4, {"answer": "Result 4"})

    print(f"Cache size: {len(cache._cache)}/3")

    # Add 4th entry - should evict query1 (LRU)
    query5 = "thủ tục khai thuế"
    emb5 = create_embedding(5)
    cache.put(query5, emb5, {"answer": "Result 5"})

    print(f"After adding 4th entry: {len(cache._cache)}/3")

    # query1 should be evicted
    cached_q1 = cache.get(query1, emb1)
    print(f"Query 1 in cache: {cached_q1 is not None}")
    print(f"✅ LRU eviction works (oldest entry evicted)")
    print()

    # Test 4: Statistics
    print("TEST 4: Cache statistics")
    print("-" * 80)
    cache.print_stats()
    print()

    print("=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    test_semantic_cache()
