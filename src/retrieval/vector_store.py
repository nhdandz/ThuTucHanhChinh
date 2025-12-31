#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qdrant Vector Store for Administrative Procedures
Manages vector database for hierarchical chunks
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    SearchRequest,
    ScrollRequest
)
from tqdm import tqdm

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class QdrantVectorStore:
    """
    Qdrant Vector Store for hierarchical chunks
    Supports filtering by chunk_type, chunk_tier, thu_tuc_id, etc.
    """

    def __init__(
        self,
        collection_name: str = "thu_tuc_hanh_chinh",
        embedding_dim: int = 1024,
        host: str = "localhost",
        port: int = 6333,
        path: Optional[str] = None
    ):
        """
        Initialize Qdrant vector store

        Args:
            collection_name: Name of the collection
            embedding_dim: Dimension of embeddings (1024 for BGE-M3)
            host: Qdrant server host
            port: Qdrant server port
            path: Path for local storage (if None, use in-memory)
        """
        print(f"🔄 Initializing Qdrant Vector Store")
        print(f"   Collection: {collection_name}")
        print(f"   Embedding dim: {embedding_dim}")

        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

        # Initialize client
        if path:
            # Use local file storage
            print(f"   Mode: Local storage at {path}")
            self.client = QdrantClient(path=path)
        else:
            # Try to connect to server, fallback to in-memory
            try:
                print(f"   Mode: Server at {host}:{port}")
                self.client = QdrantClient(host=host, port=port, timeout=5)
                # Test connection
                self.client.get_collections()
            except Exception as e:
                print(f"   ⚠️  Could not connect to Qdrant server: {e}")
                print(f"   Falling back to in-memory mode")
                self.client = QdrantClient(":memory:")

        # Create collection if not exists
        self._create_collection_if_not_exists()

        print(f"✅ Vector store initialized!")

    def _create_collection_if_not_exists(self):
        """Create collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            print(f"   Creating new collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE  # Cosine similarity
                )
            )
        else:
            print(f"   Collection already exists: {self.collection_name}")

    def add_chunks(
        self,
        chunks: List[Dict],
        embeddings: np.ndarray,
        batch_size: int = 100
    ):
        """
        Add chunks with embeddings to vector store

        Args:
            chunks: List of chunk dictionaries
            embeddings: Numpy array of embeddings (N x embedding_dim)
            batch_size: Batch size for uploading
        """
        print(f"📤 Uploading {len(chunks)} chunks to Qdrant...")

        assert len(chunks) == len(embeddings), "Chunks and embeddings must have same length"

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Create point
            point = PointStruct(
                id=i,  # Use index as ID (or generate UUID)
                vector=embedding.tolist(),
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "thu_tuc_id": chunk["thu_tuc_id"],
                    "chunk_type": chunk["chunk_type"],
                    "chunk_tier": chunk["chunk_tier"],
                    "parent_chunk_id": chunk.get("parent_chunk_id"),
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "token_count": chunk["token_count"],
                    "char_count": chunk["char_count"]
                }
            )
            points.append(point)

            # Upload in batches
            if len(points) >= batch_size:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                points = []

        # Upload remaining points
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        print(f"✅ Upload complete!")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar chunks

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Filter conditions (e.g., {"chunk_type": "child_documents"})

        Returns:
            List of search results with scores
        """
        # Build filter
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                query_filter = Filter(must=conditions)

        # Ensure query_embedding is 1D
        if len(query_embedding.shape) > 1:
            query_embedding = query_embedding.flatten()

        # Search using query_points
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
            with_vectors=False
        )
        results = response.points

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "chunk_id": result.payload["chunk_id"],
                "mã_thủ_tục": result.payload["thu_tuc_id"],  # Return as mã_thủ_tục for consistency
                "chunk_type": result.payload["chunk_type"],
                "chunk_tier": result.payload["chunk_tier"],
                "parent_chunk_id": result.payload.get("parent_chunk_id"),
                "content": result.payload["content"],
                "metadata": result.payload["metadata"],
                "score": result.score
            })

        return formatted_results

    def search_by_code(
        self,
        thu_tuc_id: str,
        include_parent: bool = True,
        include_children: bool = True,
        chunk_type_filter: Optional[Union[str, List[str]]] = None
    ) -> List[Dict]:
        """
        Search for chunks by exact procedure code using Qdrant filter

        Args:
            thu_tuc_id: Exact procedure code (e.g., "1.013133")
            include_parent: Include parent chunks
            include_children: Include child chunks
            chunk_type_filter: Optional filter by chunk_type. Can be:
                              - Single string: "child_requirements"
                              - List of strings: ["child_process", "child_fees_timing"]
                              Only applies to child chunks - parent chunks are always included if include_parent=True

        Returns:
            List of all chunks matching the procedure code, sorted by tier (parent first)
        """
        try:
            all_points = []

            # Strategy: When chunk_type_filter is specified, retrieve parent and child chunks separately
            # to ensure parent chunks are not filtered out

            if chunk_type_filter and include_parent:
                # Query 1: Get parent chunks (always include for context)
                parent_filter = Filter(
                    must=[
                        FieldCondition(key="thu_tuc_id", match=MatchValue(value=thu_tuc_id)),
                        FieldCondition(key="chunk_tier", match=MatchValue(value="parent"))
                    ]
                )
                parent_scroll = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=parent_filter,
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )
                all_points.extend(parent_scroll[0] if parent_scroll else [])

            if include_children:
                # Query 2: Get child chunks with chunk_type filter
                child_must_conditions = [
                    FieldCondition(key="thu_tuc_id", match=MatchValue(value=thu_tuc_id)),
                    FieldCondition(key="chunk_tier", match=MatchValue(value="child"))
                ]

                # Apply chunk_type filter only to child chunks
                if chunk_type_filter:
                    # Support both single string and list of strings
                    if isinstance(chunk_type_filter, list):
                        # Multiple chunk types - use MatchAny
                        child_must_conditions.append(
                            FieldCondition(key="chunk_type", match=MatchAny(any=chunk_type_filter))
                        )
                    else:
                        # Single chunk type - use MatchValue
                        child_must_conditions.append(
                            FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type_filter))
                        )

                child_filter = Filter(must=child_must_conditions)
                child_scroll = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=child_filter,
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )
                all_points.extend(child_scroll[0] if child_scroll else [])

            # Fallback: If no chunk_type_filter, use single query (original behavior)
            if not chunk_type_filter:
                basic_filter = Filter(
                    must=[FieldCondition(key="thu_tuc_id", match=MatchValue(value=thu_tuc_id))]
                )
                scroll_result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=basic_filter,
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )
                all_points = scroll_result[0] if scroll_result else []

            # Format results
            formatted_results = []
            for point in all_points:
                formatted_result = {
                    "chunk_id": point.payload["chunk_id"],
                    "mã_thủ_tục": point.payload["thu_tuc_id"],
                    "chunk_type": point.payload["chunk_type"],
                    "chunk_tier": point.payload["chunk_tier"],
                    "parent_chunk_id": point.payload.get("parent_chunk_id"),
                    "content": point.payload["content"],
                    "metadata": point.payload["metadata"],
                    "score": 1.0  # Perfect match score for exact code lookup
                }
                formatted_results.append(formatted_result)

            # Filter by tier if needed (respect include_parent/include_children flags)
            if not include_parent:
                formatted_results = [r for r in formatted_results if r["chunk_tier"] != "parent"]
            if not include_children:
                formatted_results = [r for r in formatted_results if r["chunk_tier"] != "child"]

            # Sort: parent chunks first, then children
            formatted_results.sort(key=lambda x: (x["chunk_tier"] != "parent", x["chunk_id"]))

            return formatted_results

        except Exception as e:
            print(f"⚠️ Error in exact code search: {e}")
            return []

    def get_collection_info(self) -> Dict:
        """Get collection statistics"""
        info = self.client.get_collection(self.collection_name)
        return {
            "collection_name": self.collection_name,
            "vectors_count": info.points_count if hasattr(info, 'points_count') else 0,
            "vector_size": info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else 0,
            "status": info.status if hasattr(info, 'status') else 'unknown'
        }


def index_all_chunks(
    chunks_file: Path,
    embedder,
    vector_store: QdrantVectorStore,
    batch_size: int = 32
):
    """
    Generate embeddings and index all chunks

    Args:
        chunks_file: Path to all_chunks.json
        embedder: Embedding model
        vector_store: Qdrant vector store
        batch_size: Batch size for embedding generation
    """
    print("=" * 80)
    print("INDEXING CHUNKS TO QDRANT")
    print("=" * 80)
    print()

    # Load chunks
    print(f"📂 Loading chunks from: {chunks_file}")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"   Found {len(chunks)} chunks")
    print()

    # Generate embeddings
    print(f"🔄 Generating embeddings...")
    contents = [chunk["content"] for chunk in chunks]

    embeddings = embedder.encode(
        contents,
        batch_size=batch_size,
        show_progress=True,
        normalize=True
    )

    print(f"   Embeddings shape: {embeddings.shape}")
    print()

    # Index to Qdrant
    vector_store.add_chunks(chunks, embeddings, batch_size=100)

    # Show stats
    print()
    print("📊 Collection Info:")
    info = vector_store.get_collection_info()
    for key, value in info.items():
        print(f"   {key}: {value}")

    print()
    print("=" * 80)
    print("INDEXING COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    # Test
    from embedding_model import OllamaEmbedder

    print("Testing Qdrant Vector Store...")
    print()

    # Initialize
    embedder = OllamaEmbedder(model_name="bge-m3")
    vector_store = QdrantVectorStore(path="./qdrant_storage")

    # Find chunks file
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    chunks_file = project_root / "data" / "chunks" / "all_chunks.json"

    if chunks_file.exists():
        # Index all chunks
        index_all_chunks(
            chunks_file=chunks_file,
            embedder=embedder,
            vector_store=vector_store,
            batch_size=1  # Small batch for Ollama (one at a time)
        )
    else:
        print(f"❌ Chunks file not found: {chunks_file}")
