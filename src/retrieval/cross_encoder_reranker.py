#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cross-Encoder Reranker - Re-rank retrieved chunks using cross-encoder model

Uses BAAI/bge-reranker-v2-m3 for precise relevance scoring
Implements ensemble scoring: semantic (55%) + BM25 (35%) + cross-encoder (10%)

Architecture:
1. Take top-k results from hybrid search (BM25 + semantic)
2. Score each (query, chunk) pair with cross-encoder
3. Ensemble scoring with original retrieval scores
4. Return top-k reranked results
"""

import sys
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class RerankResult:
    """Result from reranking"""
    chunk: Dict
    ensemble_score: float
    semantic_score: float
    bm25_score: float
    cross_encoder_score: float
    rank: int


class CrossEncoderReranker:
    """
    Cross-Encoder based reranker using bge-reranker-v2-m3

    Features:
    - Cross-encoder scoring via Ollama API
    - Ensemble scoring (semantic + BM25 + cross-encoder)
    - Configurable score weights
    - Batch processing for efficiency

    Scoring formula:
        ensemble_score = α×semantic + β×BM25 + γ×cross_encoder
        Default: α=0.55, β=0.35, γ=0.10
    """

    def __init__(
        self,
        model_name: str = "bge-reranker-v2-m3",
        ollama_host: str = "http://localhost:11434",
        semantic_weight: float = 0.55,
        bm25_weight: float = 0.35,
        cross_encoder_weight: float = 0.10,
        batch_size: int = 16,
        use_cross_encoder: bool = True
    ):
        """
        Initialize cross-encoder reranker

        Args:
            model_name: Reranker model name (default: bge-reranker-v2-m3)
            ollama_host: Ollama API endpoint
            semantic_weight: Weight for semantic scores (0-1)
            bm25_weight: Weight for BM25 scores (0-1)
            cross_encoder_weight: Weight for cross-encoder scores (0-1)
            batch_size: Batch size for cross-encoder scoring
            use_cross_encoder: Enable cross-encoder scoring (if False, use semantic+BM25 only)
        """
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        self.cross_encoder_weight = cross_encoder_weight
        self.batch_size = batch_size
        self.use_cross_encoder = use_cross_encoder

        # API endpoint
        self.embed_url = f"{ollama_host}/api/embeddings"

        # Normalize weights to sum to 1.0
        total_weight = semantic_weight + bm25_weight + cross_encoder_weight
        self.semantic_weight /= total_weight
        self.bm25_weight /= total_weight
        self.cross_encoder_weight /= total_weight

        print(f"✅ CrossEncoderReranker initialized")
        print(f"   Weights: semantic={self.semantic_weight:.2f}, "
              f"BM25={self.bm25_weight:.2f}, "
              f"cross-encoder={self.cross_encoder_weight:.2f}")
        print(f"   Cross-encoder: {'enabled' if use_cross_encoder else 'disabled'}")

    def score_pair(self, query: str, text: str) -> Optional[float]:
        """
        Score a (query, text) pair using cross-encoder via embeddings similarity

        Note: Since Ollama doesn't have native reranker API, we use
        embedding similarity as a proxy for cross-encoder scoring.

        Args:
            query: Query text
            text: Document text to score

        Returns:
            Similarity score (0-1) or None if failed
        """
        if not self.use_cross_encoder:
            return 0.5  # Neutral score when cross-encoder disabled

        try:
            # Get embeddings for query and text
            query_embedding = self._get_embedding(query)
            text_embedding = self._get_embedding(text)

            if query_embedding is None or text_embedding is None:
                return None

            # Compute cosine similarity
            similarity = self._cosine_similarity(query_embedding, text_embedding)

            # Convert to 0-1 range (cosine similarity is -1 to 1)
            score = (similarity + 1) / 2

            return score

        except Exception as e:
            print(f"   ⚠️  Error scoring pair: {str(e)[:100]}")
            return None

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from Ollama"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": text[:512]  # Limit length for efficiency
            }

            response = requests.post(
                self.embed_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return data.get("embedding")

        except Exception:
            return None

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5,
        show_progress: bool = False
    ) -> List[RerankResult]:
        """
        Rerank chunks using ensemble scoring

        Args:
            query: User query
            chunks: List of chunks with scores
            top_k: Number of top results to return
            show_progress: Show progress during reranking

        Returns:
            List of RerankResult sorted by ensemble score (descending)
        """
        if not chunks:
            return []

        rerank_results = []

        if show_progress:
            print(f"   🔄 Reranking {len(chunks)} chunks...")

        for i, chunk in enumerate(chunks):
            # Get original scores
            semantic_score = chunk.get("score", 0.0)  # From vector search
            bm25_score = chunk.get("bm25_score", 0.0)  # From BM25

            # Normalize scores to 0-1 range
            semantic_score = min(max(semantic_score, 0.0), 1.0)
            bm25_score = min(max(bm25_score, 0.0), 1.0)

            # Get cross-encoder score
            cross_encoder_score = 0.5  # Default neutral score
            if self.use_cross_encoder:
                # Score using chunk content
                chunk_text = chunk.get("content", "")[:500]  # Limit length
                ce_score = self.score_pair(query, chunk_text)

                if ce_score is not None:
                    cross_encoder_score = ce_score

            # Ensemble scoring
            ensemble_score = (
                self.semantic_weight * semantic_score +
                self.bm25_weight * bm25_score +
                self.cross_encoder_weight * cross_encoder_score
            )

            rerank_results.append(RerankResult(
                chunk=chunk,
                ensemble_score=ensemble_score,
                semantic_score=semantic_score,
                bm25_score=bm25_score,
                cross_encoder_score=cross_encoder_score,
                rank=i + 1  # Original rank
            ))

        # Sort by ensemble score (descending)
        rerank_results.sort(key=lambda x: x.ensemble_score, reverse=True)

        # Update ranks
        for i, result in enumerate(rerank_results, 1):
            result.rank = i

        # Return top-k
        top_results = rerank_results[:top_k]

        if show_progress:
            print(f"   ✅ Reranked to top {len(top_results)} results")

        return top_results

    def rerank_simple(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Simplified reranking that returns just the chunks (not RerankResult)

        Args:
            query: User query
            chunks: List of chunks with scores
            top_k: Number of top results to return

        Returns:
            List of reranked chunks with updated 'ensemble_score' field
        """
        rerank_results = self.rerank(query, chunks, top_k=top_k)

        # Convert back to chunks with ensemble score
        reranked_chunks = []
        for result in rerank_results:
            chunk = result.chunk.copy()
            chunk["final_score"] = result.ensemble_score  # Fixed: use consistent field name
            chunk["original_rank"] = result.rank
            reranked_chunks.append(chunk)

        return reranked_chunks


def test_reranker():
    """Test cross-encoder reranker"""
    print("=" * 80)
    print("CROSS-ENCODER RERANKER TEST")
    print("=" * 80)
    print()

    # Initialize reranker
    reranker = CrossEncoderReranker(
        use_cross_encoder=False,  # Disable for faster testing
        semantic_weight=0.6,
        bm25_weight=0.4,
        cross_encoder_weight=0.0
    )
    print()

    # Sample chunks with scores
    chunks = [
        {
            "chunk_id": "1.013133_child_process_0",
            "content": "Thủ tục đăng ký nghĩa vụ quân sự lần đầu",
            "score": 0.85,  # High semantic score
            "bm25_score": 0.92,  # High BM25 score
            "metadata": {"tên_thủ_tục": "Đăng ký nghĩa vụ quân sự lần đầu"}
        },
        {
            "chunk_id": "1.013138_child_process_0",
            "content": "Thủ tục đăng ký nghĩa vụ quân sự tạm vắng",
            "score": 0.75,  # Medium semantic score
            "bm25_score": 0.65,  # Medium BM25 score
            "metadata": {"tên_thủ_tục": "Đăng ký nghĩa vụ quân sự tạm vắng"}
        },
        {
            "chunk_id": "1.013136_child_process_0",
            "content": "Thủ tục đăng ký nghĩa vụ quân sự bổ sung",
            "score": 0.70,  # Lower semantic score
            "bm25_score": 0.80,  # High BM25 score
            "metadata": {"tên_thủ_tục": "Đăng ký nghĩa vụ quân sự bổ sung"}
        }
    ]

    query = "đăng ký nghĩa vụ quân sự lần đầu"

    print(f"Query: '{query}'")
    print()
    print("Original scores:")
    for i, chunk in enumerate(chunks, 1):
        print(f"   {i}. {chunk['chunk_id']}")
        print(f"      Semantic: {chunk['score']:.2f}, BM25: {chunk['bm25_score']:.2f}")

    print()

    # Rerank
    reranked = reranker.rerank(query, chunks, top_k=3, show_progress=True)

    print()
    print("After ensemble reranking:")
    for result in reranked:
        print(f"   {result.rank}. {result.chunk['chunk_id']}")
        print(f"      Ensemble: {result.ensemble_score:.3f} "
              f"(S:{result.semantic_score:.2f} × {reranker.semantic_weight:.2f} + "
              f"B:{result.bm25_score:.2f} × {reranker.bm25_weight:.2f})")

    print()
    print("=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    test_reranker()
