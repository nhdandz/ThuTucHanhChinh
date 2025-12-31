#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
9-Stage Enhanced Retrieval Pipeline
Implements accuracy-first approach with semantic caching, hybrid search, and intelligent reranking
"""

import sys
from typing import List, Dict, Optional
from pathlib import Path
import numpy as np
from dataclasses import dataclass

from embedding_model import OllamaEmbedder
from vector_store import QdrantVectorStore
from query_enhancer import OllamaQueryEnhancer
from bm25_search import SimpleBM25
from cross_encoder_reranker import CrossEncoderReranker
from semantic_cache import SemanticCache
from context_settings import get_context_config, ContextConfig

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class RetrievalResult:
    """Result from retrieval pipeline"""
    query: str
    intent: str
    retrieved_chunks: List[Dict]
    context: str
    confidence: float
    metadata: Dict


class HierarchicalRetrievalPipeline:
    """
    9-Stage Enhanced Retrieval Pipeline:

    Stage 0: Semantic Cache Check - Return cached results for similar queries
    Stage 1: Query Understanding - Enhanced query analysis + intent detection
    Stage 2: Exact Match Routing - Direct lookup for procedure codes
    Stage 3: Parent Retrieval - Semantic search for top-level parent chunks
    Stage 4: Child Retrieval - Cross-tier filtered child chunk search
    Stage 5: Keyword Augmentation - BM25 keyword-based retrieval
    Stage 6: Multi-Source Fusion - RRF fusion of semantic + keyword results
    Stage 7: Intelligent Reranking - Ensemble scoring with quality filtering
    Stage 8: Context Assembly - Final context validation and assembly

    Key Optimizations:
    - Semantic caching (0.92 threshold, LRU + TTL)
    - Hybrid search (Dense embeddings + BM25)
    - Cross-encoder reranking (55% semantic + 35% BM25 + 10% CE)
    - Cross-tier filtering (children must belong to top parents)
    - Vietnamese stopword filtering
    """

    def __init__(
        self,
        embedder: OllamaEmbedder,
        vector_store: QdrantVectorStore,
        query_enhancer: OllamaQueryEnhancer,
        bm25: Optional[SimpleBM25] = None,
        chunks: Optional[List[Dict]] = None,
        auto_init_bm25: bool = True,
        reranker: Optional[CrossEncoderReranker] = None,
        use_reranker: bool = True,
        cache: Optional[SemanticCache] = None,
        use_cache: bool = True
    ):
        """
        Initialize retrieval pipeline

        Args:
            embedder: Embedding model
            vector_store: Vector database
            query_enhancer: Query enhancement module
            bm25: BM25 search engine (optional, will be auto-initialized if chunks provided)
            chunks: Chunk list for BM25 initialization (optional)
            auto_init_bm25: Auto-initialize BM25 with chunks if not provided (default: True)
            reranker: Cross-encoder reranker (optional, will be auto-initialized)
            use_reranker: Enable cross-encoder reranking (default: True)
            cache: Semantic cache (optional, will be auto-initialized)
            use_cache: Enable semantic caching (default: True)
        """
        print("🔄 Initializing Retrieval Pipeline")
        self.embedder = embedder
        self.vector_store = vector_store
        self.query_enhancer = query_enhancer

        # FIXED: Auto-initialize BM25 if not provided but chunks are available
        if bm25 is None and auto_init_bm25 and chunks:
            print("   🔧 Auto-initializing BM25 with Vietnamese stopwords...")
            self.bm25 = SimpleBM25(chunks=chunks, k1=1.5, b=0.75)
            self.bm25.build_index(show_progress=True)
            print(f"   ✅ BM25 index built: {len(chunks)} chunks")
        else:
            self.bm25 = bm25

        if self.bm25 and self.bm25.is_built:
            print("   ✅ BM25 ready for hybrid search")
        else:
            print("   ⚠️  BM25 not available (semantic search only)")

        # Auto-initialize reranker if not provided
        if reranker is None and use_reranker:
            print("   🔧 Auto-initializing Cross-Encoder reranker...")
            self.reranker = CrossEncoderReranker(
                use_cross_encoder=False,  # Disable actual cross-encoder for speed
                semantic_weight=0.55,
                bm25_weight=0.35,
                cross_encoder_weight=0.10
            )
            print("   ✅ Reranker ready (ensemble scoring: 55% semantic + 35% BM25 + 10% CE)")
        else:
            self.reranker = reranker

        # Auto-initialize cache if not provided
        if cache is None and use_cache:
            print("   🔧 Auto-initializing Semantic Cache...")
            self.cache = SemanticCache(
                max_size=100,
                ttl_hours=24.0,
                similarity_threshold=0.92
            )
            print("   ✅ Cache ready (max: 100 entries, TTL: 24h, threshold: 0.92)")
        else:
            self.cache = cache

        print("✅ Retrieval Pipeline ready!")

    def retrieve(
        self,
        question: str,
        top_k_parent: int = 5,
        top_k_child: int = 100,  # Increased from 20 to 100 for better recall
        top_k_final: int = 5
    ) -> RetrievalResult:
        """
        Main retrieval method implementing 9-stage enhanced pipeline

        Args:
            question: User question
            top_k_parent: Number of parent chunks to retrieve
            top_k_child: Number of child chunks to retrieve per query (before reranking)
            top_k_final: Number of final results after re-ranking

        Returns:
            RetrievalResult with retrieved chunks and context
        """
        print("\n" + "=" * 80)
        print("9-STAGE ENHANCED RETRIEVAL PIPELINE")
        print("=" * 80)

        # STAGE 0: Semantic Cache Check
        cached_result = None
        query_embedding = None

        if self.cache:
            print("\n[STAGE 0] Semantic Cache Check")
            # Generate embedding for cache lookup
            query_embedding = self.embedder.encode(question, show_progress=False)

            # Try to get cached result
            cached_result = self.cache.get(question, query_embedding)

            if cached_result:
                print("   🎯 Cache HIT! Returning cached result")
                stats = self.cache.get_stats()
                print(f"   📊 Cache stats: {stats['hits']}/{stats['total_queries']} hits ({stats['hit_rate']:.1%})")
                return cached_result
            else:
                print("   ❌ Cache MISS - proceeding with retrieval")

        # STAGE 1: Query Understanding
        print("\n[STAGE 1] Query Understanding & Enhancement")
        query_info = self.query_enhancer.enhance_query(question)

        # STAGE 1.5: Intent-Based Context Configuration
        context_config = get_context_config(query_info.intent)
        print(f"\n[STAGE 1.5] Context Configuration")
        print(f"   Intent: {query_info.intent} → Mode: {context_config['mode']}")
        print(f"   Chunks: {context_config['chunks']}, Descendants: {context_config['max_descendants']}, Siblings: {context_config['max_siblings']}")

        # Override top_k_final with intent-based value
        top_k_final = context_config['chunks']

        # STAGE 2: Exact Match Routing (if code detected)
        if query_info.exact_code:
            print(f"\n[STAGE 2] Exact Match Routing - Code detected: {query_info.exact_code}")

            # Get chunk_type filter from query_info (intent-based filtering)
            chunk_type_filter = query_info.filters.get("chunk_type") if query_info.filters else None

            # Call exact match with intent-based chunk_type filter
            exact_results = self.vector_store.search_by_code(
                thu_tuc_id=query_info.exact_code,
                chunk_type_filter=chunk_type_filter
            )

            if exact_results:
                print(f"   ✅ Found {len(exact_results)} chunks via exact match")

                # Separate parent and child results
                parent_results = [r for r in exact_results if r["chunk_tier"] == "parent"]
                child_results = [r for r in exact_results if r["chunk_tier"] == "child"]

                # Use intent-based config for exact match (instead of unlimited)
                print(f"        ⚠️  Exact match: Using intent-based config ({query_info.intent})")
                print(f"           max_descendants={context_config['max_descendants']}, chunk_type={chunk_type_filter or 'all'}")

                # Assemble context with INTENT-BASED limits
                context, _ = self._assemble_context(parent_results, child_results, context_config)

                # Create exact match result
                exact_match_result = RetrievalResult(
                    query=question,
                    intent=query_info.intent,
                    retrieved_chunks=exact_results,
                    context=context,
                    confidence=1.0,  # Perfect confidence for exact match
                    metadata={
                        "search_type": "exact_code_match",
                        "thu_tuc_id": query_info.exact_code,
                        "num_parent_chunks": len(parent_results),
                        "num_child_chunks": len(child_results)
                    }
                )

                # Cache exact match result
                if self.cache:
                    if query_embedding is None:
                        query_embedding = self.embedder.encode(question, show_progress=False)
                    self.cache.put(question, query_embedding, exact_match_result)
                    print("   💾 Exact match result cached")

                return exact_match_result
            else:
                print(f"   ⚠️ No exact match found for code {query_info.exact_code}, falling back to hybrid search")

        # STAGE 3: Parent Retrieval (Semantic Search)
        print("\n[STAGE 3] Parent Retrieval - Semantic Search")
        parent_results, child_results = self._hierarchical_retrieve(
            query_info,
            top_k_parent=top_k_parent,
            top_k_child=top_k_child
        )

        # STAGE 5: Keyword Augmentation (BM25 Search)
        bm25_results = {}
        if self.bm25 and self.bm25.is_built:
            print("\n[STAGE 5] Keyword Augmentation - BM25 Search")

            # Build filters for BM25 (same as semantic search)
            bm25_filters = {"chunk_tier": "child"}
            if query_info.filters.get("chunk_type"):
                bm25_filters["chunk_type"] = query_info.filters["chunk_type"]
                print(f"        Applying chunk_type filter: {bm25_filters['chunk_type']}")

            # Use same top_k for consistency and better recall
            bm25_chunks = self.bm25.search(question, top_k=top_k_child, filters=bm25_filters)
            if bm25_chunks:
                bm25_results["bm25"] = bm25_chunks
                print(f"        Found {len(bm25_chunks)} chunks via BM25")
        else:
            print("\n[STAGE 5] Keyword Augmentation - BM25 (skipped - not initialized)")

        # Merge BM25 results with semantic results
        all_child_results = {**child_results, **bm25_results}

        # STAGE 6: Multi-Source Fusion (RRF)
        print("\n[STAGE 6] Multi-Source Fusion - Reciprocal Rank Fusion")
        fused_results = self._reciprocal_rank_fusion(all_child_results)

        # STAGE 7: Intelligent Reranking (Ensemble Scoring)
        print("\n[STAGE 7] Intelligent Reranking - Ensemble Scoring")
        reranked_results = self._rerank_with_score_fusion(
            question,
            fused_results,
            top_k=top_k_final
        )

        # STAGE 8: Context Assembly & Validation
        print("\n[STAGE 8] Context Assembly & Validation")
        context, confidence = self._assemble_context(
            parent_results,
            reranked_results,
            context_config  # Pass intent-based config
        )

        print("\n" + "=" * 80)
        print(f"✅ Retrieval Complete! Confidence: {confidence:.2f}")
        print("=" * 80)

        # Create result
        result = RetrievalResult(
            query=question,
            intent=query_info.intent,
            retrieved_chunks=reranked_results,
            context=context,
            confidence=confidence,
            metadata={
                "num_parent_chunks": len(parent_results),
                "num_child_chunks": len(reranked_results),
                "query_variations": query_info.query_variations
            }
        )

        # Cache the result for future queries
        if self.cache:
            # Reuse query_embedding from cache check, or generate if not done yet
            if query_embedding is None:
                query_embedding = self.embedder.encode(question, show_progress=False)

            self.cache.put(question, query_embedding, result)
            print("   💾 Result cached for future queries")

        return result

    def _hierarchical_retrieve(
        self,
        query_info,
        top_k_parent: int = 5,
        top_k_child: int = 20
    ) -> tuple:
        """
        Stages 3-4: Hierarchical retrieval (Parent → Child)

        Stage 3: Parent retrieval via semantic search
        Stage 4: Child retrieval with cross-tier filtering

        Returns:
            Tuple of (parent_results, child_results)
        """
        # Stage 3: Retrieve Parent chunks first
        print("   🔍 Searching parent chunks (procedure overviews)...")
        query_embedding = self.embedder.encode(query_info.original_query, show_progress=False)

        parent_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k_parent,
            filters={"chunk_tier": "parent"}
        )

        print(f"   ✅ Found {len(parent_results)} parent chunks")

        # Extract parent IDs for cross-tier filtering
        parent_ids = [r["chunk_id"] for r in parent_results]
        parent_thu_tuc_ids = [r["mã_thủ_tục"] for r in parent_results]

        print(f"   📋 Top parent procedures: {parent_thu_tuc_ids[:3]}...")

        # STAGE 4: Child Retrieval with Cross-Tier Filtering
        print(f"\n[STAGE 4] Child Retrieval - Cross-Tier Filtering (intent: {query_info.intent})")
        print(f"   🔍 Retrieving child chunks for {len(query_info.query_variations)} query variations...")

        # Retrieve for each query variation
        all_child_results = {}
        total_before_filter = 0
        total_after_filter = 0

        for i, query_variation in enumerate(query_info.query_variations, 1):
            print(f"        Query variation {i}/{len(query_info.query_variations)}")

            query_emb = self.embedder.encode(query_variation, show_progress=False)

            # Build filters
            filters = {"chunk_tier": "child"}

            # Try with chunk_type filter first (if specified)
            if query_info.filters.get("chunk_type"):
                filters["chunk_type"] = query_info.filters["chunk_type"]

                # Retrieve with chunk_type filter
                child_results = self.vector_store.search(
                    query_embedding=query_emb,
                    top_k=top_k_child,
                    filters=filters
                )

                # If no results with strict filter, remove chunk_type and search all child chunks
                if not child_results:
                    print(f"           ⚠️ No results with chunk_type={filters['chunk_type']}, searching all child chunks")
                    filters = {"chunk_tier": "child"}  # Remove chunk_type filter
                    child_results = self.vector_store.search(
                        query_embedding=query_emb,
                        top_k=top_k_child,
                        filters=filters
                    )
            else:
                # No chunk_type filter specified, search all child chunks
                child_results = self.vector_store.search(
                    query_embedding=query_emb,
                    top_k=top_k_child,
                    filters=filters
                )

            total_before_filter += len(child_results)

            # Debug: Show what thu_tuc_ids we got
            if child_results:
                child_thu_tuc_ids = [c["mã_thủ_tục"] for c in child_results[:5]]
                print(f"           Sample child thu_tuc_ids: {child_thu_tuc_ids}")

            # Filter to only keep chunks from top parent procedures
            filtered_children = [
                c for c in child_results
                if c["mã_thủ_tục"] in parent_thu_tuc_ids
            ]

            total_after_filter += len(filtered_children)

            # If no matches after filtering, keep top results anyway (with lower weight)
            if not filtered_children and child_results:
                print(f"           ⚠️ No children matched parent procedures, keeping top {min(5, len(child_results))} anyway")
                filtered_children = child_results[:5]  # Keep top 5 even if not matching
                # Mark these as lower confidence
                for c in filtered_children:
                    c["cross_tier_match"] = False
            else:
                for c in filtered_children:
                    c["cross_tier_match"] = True

            # Store results per query
            all_child_results[query_variation] = filtered_children

        print(f"        Retrieved from {len(all_child_results)} query variations")
        print(f"        Before filter: {total_before_filter}, After filter: {total_after_filter}")

        return parent_results, all_child_results

    def _reciprocal_rank_fusion(
        self,
        results_per_query: Dict[str, List[Dict]],
        k: int = 60
    ) -> List[Dict]:
        """
        Stage 6: Multi-Source Fusion - Reciprocal Rank Fusion

        Combines results from multiple sources (semantic queries + BM25)
        using RRF scoring with source tracking and BM25 boosting.

        Args:
            results_per_query: Dict mapping query name to results
                              Can include: semantic query variations + "bm25"
            k: RRF constant (default 60)

        Returns:
            Fused and ranked results with source tracking
        """
        fused_scores = {}

        for query_name, results in results_per_query.items():
            # Determine if this is BM25 or semantic source
            is_bm25 = "bm25" in query_name.lower()

            for rank, doc in enumerate(results, 1):
                doc_id = doc["chunk_id"]

                # RRF formula: 1 / (k + rank)
                rrf_score = 1.0 / (k + rank)

                # Boost BM25 results (keyword match is valuable)
                if is_bm25:
                    rrf_score *= 1.2  # 20% boost for keyword matches

                if doc_id not in fused_scores:
                    fused_scores[doc_id] = {
                        "doc": doc,
                        "rrf_score": 0.0,
                        "count": 0,
                        "source_counts": {"semantic": 0, "bm25": 0}
                    }

                fused_scores[doc_id]["rrf_score"] += rrf_score
                fused_scores[doc_id]["count"] += 1

                # Track which sources found this document
                if is_bm25:
                    fused_scores[doc_id]["source_counts"]["bm25"] += 1
                else:
                    fused_scores[doc_id]["source_counts"]["semantic"] += 1

        # Sort by RRF score
        ranked_docs = sorted(
            fused_scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        # Add RRF score and source tracking to metadata
        results = []
        for item in ranked_docs:
            doc = item["doc"]
            doc["rrf_score"] = item["rrf_score"]
            doc["retrieval_count"] = item["count"]
            doc["source_counts"] = item["source_counts"]
            results.append(doc)

        print(f"        Fused {len(results)} unique chunks")

        return results

    def _rerank_with_score_fusion(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Stage 7: Intelligent Reranking - Ensemble Scoring

        Uses CrossEncoderReranker with weighted ensemble scoring:
        - 55% semantic score (from vector search)
        - 35% BM25 score (from keyword search)
        - 10% cross-encoder score (optional, disabled by default)

        This stage refines the RRF-fused results by considering
        individual score components for more accurate ranking.

        Args:
            query: Original query
            documents: Retrieved documents from Stage 6
            top_k: Number of top results to return

        Returns:
            Re-ranked top-k documents with ensemble scores
        """
        if not documents:
            return []

        # Use reranker if available
        if self.reranker:
            reranked_chunks = self.reranker.rerank_simple(
                query=query,
                chunks=documents,
                top_k=top_k
            )
            print(f"        Re-ranked to top {len(reranked_chunks)} chunks via ensemble scoring")
            return reranked_chunks

        # Fallback: Simple scoring if no reranker
        for doc in documents:
            vector_score = doc.get("score", 0.0)
            rrf_score = doc.get("rrf_score", 0.0)

            # Simple weighted fusion
            final_score = 0.6 * rrf_score + 0.4 * vector_score
            doc["final_score"] = final_score  # Fixed: use consistent field name

        # Sort by score
        reranked = sorted(documents, key=lambda x: x.get("final_score", 0.0), reverse=True)
        print(f"        Re-ranked to top {top_k} chunks (fallback scoring)")

        return reranked[:top_k]

    def _truncate_chunk_if_needed(self, content: str, max_tokens: int = 1200) -> str:
        """
        Truncate chunk content if it exceeds token limit

        This is a safety net for exceptionally long chunks (e.g., child_documents
        with 2,114 tokens). Keeps first and last portions to preserve context.

        Args:
            content: Chunk content to potentially truncate
            max_tokens: Maximum tokens allowed (default 1200)

        Returns:
            Original or truncated content
        """
        # Rough estimate: 1 token ≈ 4 characters for Vietnamese text
        max_chars = max_tokens * 4

        if len(content) <= max_chars:
            return content

        # Truncate: keep first half and last half
        words = content.split()
        if len(words) > max_tokens:
            half = max_tokens // 2
            truncated = ' '.join(words[:half]) + '\n\n[... Nội dung quá dài, đã rút gọn ...]\n\n' + ' '.join(words[-half:])
            print(f"        ⚠️ Truncated long chunk from {len(words)} to {max_tokens} words")
            return truncated

        return content

    def _assemble_context(
        self,
        parent_results: List[Dict],
        child_results: List[Dict],
        config: ContextConfig  # NEW: Intent-based context config
    ) -> tuple:
        """
        Stage 8: Context Assembly & Validation (OPTIMIZED)

        Assembles final context using intent-based dynamic settings:
        - Groups chunks by procedure (mã_thủ_tục)
        - Limits to config['chunks'] top procedures
        - Limits to config['max_descendants'] per procedure
        - Adds sibling context if config['max_siblings'] > 0
        - Conditionally includes parent based on config['include_parents']

        This reduces context from avg 5,350 tokens to 2,000-4,400 tokens
        depending on intent, preventing overflow and improving response time.

        Args:
            parent_results: Parent chunk results from Stage 3
            child_results: Top child chunk results from Stage 7
            config: Intent-based context configuration

        Returns:
            Tuple of (context_string, confidence_score)
        """
        print(f"        Using dynamic context: chunks={config['chunks']}, descendants={config['max_descendants']}, siblings={config['max_siblings']}")
        
        context_blocks = []

        # Build parent lookup for quick access
        parent_lookup = {p["chunk_id"]: p for p in parent_results}

        # Group child chunks by procedure (mã_thủ_tục)
        chunks_by_procedure = {}
        for child in child_results:
            proc_id = child.get("mã_thủ_tục", child.get("metadata", {}).get("mã_thủ_tục", "unknown"))
            if proc_id not in chunks_by_procedure:
                chunks_by_procedure[proc_id] = []
            chunks_by_procedure[proc_id].append(child)

        # Sort procedures by max score of their chunks (descending)
        sorted_procedures = sorted(
            chunks_by_procedure.items(),
            key=lambda x: max(c.get("final_score", 0) for c in x[1]),
            reverse=True
        )

        # Limit to top config['chunks'] procedures
        top_procedures = sorted_procedures[:config['chunks']]

        # Assemble context from top procedures
        total_chunks_added = 0
        all_chunks = []  # For confidence calculation

        for proc_id, proc_chunks in top_procedures:
            # Sort chunks within procedure by score
            sorted_chunks = sorted(proc_chunks, key=lambda x: x.get("final_score", 0), reverse=True)

            # Limit to max_descendants per procedure
            selected_chunks = sorted_chunks[:config['max_descendants']]

            # Find parent for this procedure (if include_parents enabled)
            parent = None
            if config['include_parents'] and selected_chunks:
                parent_id = selected_chunks[0].get("parent_chunk_id")
                parent = parent_lookup.get(parent_id)
                if not parent:
                    # Fallback: find parent by mã_thủ_tục
                    parent = next(
                        (p for p in parent_results if p["mã_thủ_tục"] == proc_id),
                        None
                    )

            # Build context block for this procedure
            for i, child in enumerate(selected_chunks, 1):
                total_chunks_added += 1
                all_chunks.append(child)

                # Build header
                block = f"""
{'=' * 80}
[CHUNK {total_chunks_added}] THỦ TỤC: {child.get('metadata', {}).get('tên_thủ_tục', child.get('tên_thủ_tục', 'N/A'))}
Mã: {child.get('metadata', {}).get('mã_thủ_tục', child.get('mã_thủ_tục', 'N/A'))}
Lĩnh vực: {child.get('metadata', {}).get('lĩnh_vực', 'N/A')}
Chunk type: {child['chunk_type']}
Relevance score: {child.get('final_score', 0.0):.4f}
{'=' * 80}

"""
                # Add parent overview once per procedure (only for first chunk)
                if parent and i == 1 and config['include_parents']:
                    parent_content = self._truncate_chunk_if_needed(parent['content'])
                    block += f"[OVERVIEW]\n{parent_content}\n\n"

                # Add detailed child content (with truncation for safety)
                child_content = self._truncate_chunk_if_needed(child['content'])
                block += f"[DETAILED INFO]\n{child_content}\n"

                context_blocks.append(block)

        # Add sibling context (chunks from other procedures) if configured
        if config['max_siblings'] > 0:
            # Get chunks from procedures NOT in top_procedures
            top_proc_ids = {proc_id for proc_id, _ in top_procedures}
            sibling_chunks = []

            for proc_id, proc_chunks in sorted_procedures:
                if proc_id not in top_proc_ids:
                    # Take top chunk from this procedure
                    if proc_chunks:
                        sibling_chunks.append(max(proc_chunks, key=lambda x: x.get("final_score", 0)))

                if len(sibling_chunks) >= config['max_siblings']:
                    break

            # Add sibling chunks to context
            for child in sibling_chunks[:config['max_siblings']]:
                total_chunks_added += 1
                all_chunks.append(child)

                # Truncate sibling content if needed
                sibling_content = self._truncate_chunk_if_needed(child['content'])

                block = f"""
{'=' * 80}
[RELATED CHUNK {total_chunks_added}] THỦ TỤC: {child.get('metadata', {}).get('tên_thủ_tục', child.get('tên_thủ_tục', 'N/A'))}
Mã: {child.get('metadata', {}).get('mã_thủ_tục', child.get('mã_thủ_tục', 'N/A'))}
Lĩnh vực: {child.get('metadata', {}).get('lĩnh_vực', 'N/A')}
Chunk type: {child['chunk_type']}
Relevance score: {child.get('final_score', 0.0):.4f}
{'=' * 80}

[RELATED INFO]\n{sibling_content}\n"""

                context_blocks.append(block)

        # Calculate confidence based on all selected chunks
        if all_chunks:
            avg_score = sum(c.get("final_score", 0) for c in all_chunks) / len(all_chunks)
            confidence = min(1.0, avg_score * 2)  # Scale to 0-1
        else:
            avg_score = 0.0
            confidence = 0.0

        context = "\n".join(context_blocks)

        print(f"        Assembled {len(context_blocks)} context blocks from {len(top_procedures)} procedures")
        if all_chunks:
            print(f"        Average relevance: {avg_score:.4f}")
            print(f"        Estimated tokens: ~{len(context) // 4} (reduced from default)")
        else:
            print("        No results")

        return context, confidence


def test_retrieval_pipeline():
    """Test retrieval pipeline with sample queries"""
    print("=" * 80)
    print("TEST RETRIEVAL PIPELINE")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing components...")
    embedder = OllamaEmbedder(model_name="bge-m3")
    vector_store = QdrantVectorStore(path="./qdrant_storage")
    query_enhancer = OllamaQueryEnhancer(model_name="qwen3:8b")

    # Create pipeline
    pipeline = HierarchicalRetrievalPipeline(
        embedder=embedder,
        vector_store=vector_store,
        query_enhancer=query_enhancer
    )

    # Test queries
    test_queries = [
        "Đăng ký kết hôn cần giấy tờ gì?",
        "Thủ tục đăng ký kinh doanh có những điều kiện gì?",
        "Xin giấy phép xây dựng mất bao lâu?"
    ]

    for query in test_queries:
        print("\n\n")
        print("🔍" * 40)
        print(f"QUERY: {query}")
        print("🔍" * 40)

        result = pipeline.retrieve(
            question=query,
            top_k_parent=5,
            top_k_child=15,
            top_k_final=3
        )

        print(f"\n📊 RESULTS:")
        print(f"   Intent: {result.intent}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Retrieved chunks: {len(result.retrieved_chunks)}")
        print()
        print("Context preview (first 500 chars):")
        print(result.context[:500])
        print("...")

    print("\n\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_retrieval_pipeline()
