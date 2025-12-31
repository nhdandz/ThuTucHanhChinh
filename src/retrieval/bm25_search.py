#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BM25 Search Module - Keyword-based retrieval
Implements BM25 ranking with inverted index for fast lexical matching
Ported from backend_v2/optimized_retrieval.py
"""

import sys
import re
import math
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Vietnamese stopwords for BM25 filtering
VIETNAMESE_STOPWORDS = {
    # Common Vietnamese stopwords
    'và', 'của', 'có', 'là', 'được', 'trong', 'các', 'để', 'cho',
    'với', 'theo', 'từ', 'về', 'này', 'đó', 'khi', 'như', 'không',
    'tại', 'hoặc', 'những', 'đã', 'vào', 'nếu', 'hay', 'do', 'sẽ',
    'bởi', 'bằng', 'đến', 'trên', 'dưới', 'sau', 'trước', 'ngoài',
    'giữa', 'thì', 'nhưng', 'mà', 'vì', 'nên', 'đây', 'đấy', 'cũng',
    'thêm', 'nhiều', 'ít'
}


@dataclass
class InvertedIndexEntry:
    """Entry in inverted index"""
    doc_id: int
    term_freq: int


class SimpleBM25:
    """
    BM25 with Inverted Index for fast keyword matching

    Features:
    - Inverted index construction (10x faster than naive BM25)
    - Pre-calculated IDF scores
    - Disk persistence (save/load index)
    - Vietnamese text tokenization

    Usage:
        # Build index once
        bm25 = SimpleBM25(chunks, k1=1.5, b=0.75)
        bm25.build_index()

        # Search
        results = bm25.search(query, top_k=20)
    """

    def __init__(
        self,
        chunks: List[Dict] = None,
        k1: float = 1.5,
        b: float = 0.75
    ):
        """
        Initialize BM25 search

        Args:
            chunks: List of chunk dictionaries (optional, can load later)
            k1: BM25 k1 parameter (term saturation)
            b: BM25 b parameter (length normalization)
        """
        self.k1 = k1
        self.b = b
        self.chunks = chunks or []

        # Inverted index: term -> list of (doc_id, term_freq)
        self.inverted_index: Dict[str, List[InvertedIndexEntry]] = defaultdict(list)

        # Document metadata
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0
        self.num_docs: int = 0

        # IDF cache
        self.idf_cache: Dict[str, float] = {}

        # Index built flag
        self.is_built = False

    @staticmethod
    def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize Vietnamese text into terms

        Args:
            text: Input text
            remove_stopwords: Filter out Vietnamese stopwords (default: True)

        Returns:
            List of tokens (lowercase, >1 char, stopwords removed)
        """
        if not text:
            return []

        # Remove special characters, keep alphanumeric and spaces
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())

        # Split and filter tokens (> 1 char)
        tokens = [word for word in cleaned.split() if len(word) > 1]

        # Remove stopwords if requested
        if remove_stopwords:
            tokens = [word for word in tokens if word not in VIETNAMESE_STOPWORDS]

        return tokens

    def build_index(self, show_progress: bool = True):
        """
        Build inverted index from chunks

        Args:
            show_progress: Show progress during indexing
        """
        if not self.chunks:
            raise ValueError("No chunks provided. Pass chunks to __init__ or set self.chunks")

        if show_progress:
            print(f"\n🔧 Building BM25 inverted index for {len(self.chunks)} chunks...")

        self.num_docs = len(self.chunks)
        self.doc_lengths = []
        self.inverted_index = defaultdict(list)

        # Build inverted index
        for doc_id, chunk in enumerate(self.chunks):
            # Extract content from chunk
            content = chunk.get("content", "")
            tokens = self.tokenize(content)
            self.doc_lengths.append(len(tokens))

            # Count term frequencies
            term_freqs = Counter(tokens)

            # Add to inverted index
            for term, freq in term_freqs.items():
                self.inverted_index[term].append(
                    InvertedIndexEntry(doc_id=doc_id, term_freq=freq)
                )

            if show_progress and (doc_id + 1) % 100 == 0:
                print(f"  Indexed {doc_id + 1}/{self.num_docs} chunks...")

        # Calculate average document length
        self.avg_doc_length = sum(self.doc_lengths) / self.num_docs if self.num_docs > 0 else 0

        # Pre-calculate IDF for all terms
        if show_progress:
            print(f"  Calculating IDF scores...")

        for term, postings in self.inverted_index.items():
            df = len(postings)  # Document frequency
            # IDF formula with smoothing
            idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
            self.idf_cache[term] = idf

        self.is_built = True

        if show_progress:
            print(f"✅ BM25 index built successfully!")
            print(f"   - Unique terms: {len(self.inverted_index)}")
            print(f"   - Avg chunk length: {self.avg_doc_length:.1f} tokens\n")

    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: Dict = None
    ) -> List[Dict]:
        """
        Search using BM25 scoring

        Args:
            query: Search query
            top_k: Number of top results to return
            filters: Optional filters (e.g., {"chunk_type": "child_process"})

        Returns:
            List of chunk dicts with BM25 scores, sorted by relevance
        """
        if not self.is_built:
            raise RuntimeError("Index not built. Call build_index() first.")

        query_terms = self.tokenize(query)
        if not query_terms:
            return []

        # Initialize scores
        scores = [0.0] * self.num_docs

        # Only process documents containing query terms (inverted index speedup)
        for term in query_terms:
            if term not in self.inverted_index:
                continue  # Term not in corpus

            idf = self.idf_cache[term]
            postings = self.inverted_index[term]

            # Calculate BM25 for each document containing this term
            for entry in postings:
                doc_id = entry.doc_id
                tf = entry.term_freq
                doc_len = self.doc_lengths[doc_id]

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)

                scores[doc_id] += idf * (numerator / denominator)

        # Get top-k documents
        doc_score_pairs = [
            (doc_id, score)
            for doc_id, score in enumerate(scores)
            if score > 0
        ]

        # Apply filters if specified
        if filters:
            filtered_pairs = []
            for doc_id, score in doc_score_pairs:
                chunk = self.chunks[doc_id]
                # Check all filter conditions
                match = True
                for key, value in filters.items():
                    if chunk.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_pairs.append((doc_id, score))
            doc_score_pairs = filtered_pairs

        # Sort by score descending
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for doc_id, score in doc_score_pairs[:top_k]:
            chunk = self.chunks[doc_id].copy()
            chunk["score"] = score
            chunk["bm25_score"] = score  # Explicit BM25 score
            results.append(chunk)

        return results

    def save_index(self, filepath: str):
        """
        Save index to disk for later reuse

        Args:
            filepath: Path to save index (pickle format)
        """
        data = {
            'inverted_index': dict(self.inverted_index),
            'doc_lengths': self.doc_lengths,
            'avg_doc_length': self.avg_doc_length,
            'num_docs': self.num_docs,
            'idf_cache': self.idf_cache,
            'k1': self.k1,
            'b': self.b
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

        print(f"✅ Saved BM25 index to: {filepath}")

    def load_index(self, filepath: str):
        """
        Load pre-built index from disk

        Args:
            filepath: Path to load index from
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.inverted_index = defaultdict(list, data['inverted_index'])
        self.doc_lengths = data['doc_lengths']
        self.avg_doc_length = data['avg_doc_length']
        self.num_docs = data['num_docs']
        self.idf_cache = data['idf_cache']
        self.k1 = data['k1']
        self.b = data['b']
        self.is_built = True

        print(f"✅ Loaded BM25 index from: {filepath}")
        print(f"   - {self.num_docs} documents indexed")
        print(f"   - {len(self.inverted_index)} unique terms")


def test_bm25():
    """Test BM25 search"""
    print("=" * 80)
    print("TEST BM25 SEARCH")
    print("=" * 80)
    print()

    # Mock chunks
    chunks = [
        {"chunk_id": "1", "content": "Thủ tục đăng ký nghĩa vụ quân sự lần đầu"},
        {"chunk_id": "2", "content": "Thủ tục đăng ký kết hôn"},
        {"chunk_id": "3", "content": "Thủ tục đăng ký kinh doanh"},
        {"chunk_id": "4", "content": "Nghĩa vụ quân sự cho nam thanh niên"},
        {"chunk_id": "5", "content": "Điều kiện đăng ký kết hôn tại Việt Nam"}
    ]

    # Build index
    bm25 = SimpleBM25(chunks, k1=1.5, b=0.75)
    bm25.build_index(show_progress=True)

    # Test searches
    test_queries = [
        "đăng ký nghĩa vụ quân sự",
        "kết hôn",
        "kinh doanh"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: \"{query}\"")
        results = bm25.search(query, top_k=3)

        for i, result in enumerate(results, 1):
            print(f"   [{i}] Score: {result['bm25_score']:.4f} - {result['content'][:60]}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_bm25()
