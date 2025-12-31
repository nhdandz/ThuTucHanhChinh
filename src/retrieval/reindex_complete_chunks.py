#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Re-index Complete Chunks to Qdrant

Uses the complete chunks file (chunks_v2_complete) that includes child_process chunks.
This fixes the timeline query bug where child_process chunks were missing from the database.
"""

import sys
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from embedding_model import OllamaEmbedder
from vector_store import QdrantVectorStore, index_all_chunks

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    """Re-index from complete chunks file"""
    print("=" * 80)
    print("RE-INDEXING COMPLETE CHUNKS TO QDRANT")
    print("=" * 80)
    print()

    # Paths
    chunks_file = current_dir.parent.parent / "data" / "chunks_v2_complete" / "all_chunks_enriched_complete.json"
    vector_store_path = current_dir / "qdrant_storage"

    # Configuration
    embedding_model = "bge-m3"
    ollama_url = "http://localhost:11434"
    embedding_batch_size = 1  # Ollama works best with batch size 1

    print("Configuration:")
    print(f"  Chunks file: {chunks_file}")
    print(f"  Vector store: {vector_store_path}")
    print(f"  Embedding model: {embedding_model}")
    print(f"  Ollama URL: {ollama_url}")
    print(f"  Embedding batch size: {embedding_batch_size}")
    print()

    if not chunks_file.exists():
        print(f"❌ ERROR: Chunks file not found: {chunks_file}")
        return

    # Initialize components
    print("🔧 Initializing components...")
    print()

    # Embedder
    embedder = OllamaEmbedder(
        model_name=embedding_model,
        ollama_url=ollama_url
    )

    # Vector store - this will recreate the collection
    print()
    print("⚠️  WARNING: Deleting existing collection to ensure clean state...")

    # Create vector store (will create collection if not exists)
    vector_store = QdrantVectorStore(
        path=str(vector_store_path),
        collection_name="thu_tuc_hanh_chinh"
    )

    # Delete and recreate collection for clean re-indexing
    try:
        vector_store.client.delete_collection("thu_tuc_hanh_chinh")
        print("   ✅ Old collection deleted")
    except Exception as e:
        print(f"   ℹ️  No existing collection to delete: {e}")

    # Recreate collection
    from qdrant_client.models import VectorParams, Distance
    vector_store.client.create_collection(
        collection_name="thu_tuc_hanh_chinh",
        vectors_config=VectorParams(
            size=1024,  # BGE-M3 embedding dimension
            distance=Distance.COSINE
        )
    )
    print("   ✅ New collection created")
    print()

    # Index all chunks using the vector_store helper function
    print("🚀 Starting indexing process...")
    print()

    index_all_chunks(
        chunks_file=chunks_file,
        embedder=embedder,
        vector_store=vector_store,
        batch_size=embedding_batch_size
    )

    # Verify
    print()
    print("🔍 Verifying indexing...")
    info = vector_store.get_collection_info()

    print()
    print("📊 Collection Info:")
    print(f"   Collection: {info.get('collection_name', 'N/A')}")
    print(f"   Total vectors: {info.get('vectors_count', 0)}")
    print(f"   Vector size: {info.get('vector_size', 0)}")

    expected_count = 1738
    actual_count = info.get('vectors_count', 0)

    if actual_count == expected_count:
        print(f"   ✅ SUCCESS! All {expected_count} chunks indexed correctly")
    else:
        print(f"   ⚠️  WARNING: Expected {expected_count} chunks, got {actual_count}")

    # Test child_process chunk retrieval
    print()
    print("🧪 Testing child_process chunk retrieval...")
    test_query = "Trong trường hợp hồ sơ không hợp lệ, thời gian bao lâu?"
    print(f"   Query: {test_query}")

    # Generate query embedding
    query_embedding = embedder.encode(test_query, show_progress=False)[0]

    # Search with chunk_type filter for child_process
    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=5,
        filters={"chunk_type": "child_process"}
    )

    print(f"   Found {len(results)} child_process chunks:")
    for i, result in enumerate(results[:3], 1):
        print(f"\n   [{i}] Score: {result['score']:.3f}")
        print(f"       Procedure: {result['mã_thủ_tục']}")
        print(f"       Chunk Type: {result['chunk_type']}")
        print(f"       Content preview: {result['content'][:150]}...")

    print()
    print("=" * 80)
    print("✅ RE-INDEXING COMPLETE!")
    print("=" * 80)
    print()
    print(f"Database ready with {actual_count} chunks including child_process chunks!")
    print("Timeline queries should now work correctly.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Indexing cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
