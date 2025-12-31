#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Index Chunks to Qdrant Vector Database
Load all chunks from all_chunks.json and index them into Qdrant
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

# Add paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from embedding_model import OllamaEmbedder
from vector_store import QdrantVectorStore

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def load_chunks(chunks_file: str) -> List[Dict]:
    """Load chunks from JSON file"""
    print(f"📂 Loading chunks from: {chunks_file}")

    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"✅ Loaded {len(chunks)} chunks")
    return chunks


def index_chunks_to_qdrant(
    chunks: List[Dict],
    vector_store: QdrantVectorStore,
    embedder: OllamaEmbedder,
    batch_size: int = 50
):
    """
    Index chunks to Qdrant with embeddings

    Args:
        chunks: List of chunk dictionaries
        vector_store: QdrantVectorStore instance
        embedder: OllamaEmbedder instance
        batch_size: Number of chunks to process in each batch
    """
    print(f"\n🔄 Indexing {len(chunks)} chunks to Qdrant...")
    print(f"   Batch size: {batch_size}")
    print()

    total_chunks = len(chunks)
    indexed_count = 0
    failed_count = 0

    # Process in batches
    for i in tqdm(range(0, total_chunks, batch_size), desc="Indexing batches"):
        batch = chunks[i:i + batch_size]

        try:
            # Prepare batch data
            texts = []
            metadatas = []

            for chunk in batch:
                # Extract text (content)
                text = chunk.get('content', '')
                if not text:
                    failed_count += 1
                    continue

                # Prepare metadata (all other fields)
                metadata = {
                    'chunk_id': chunk.get('chunk_id', ''),
                    'procedure_id': chunk.get('procedure_id', ''),
                    'procedure_name': chunk.get('procedure_name', ''),
                    'tier': chunk.get('tier', ''),
                    'chunk_type': chunk.get('chunk_type', ''),
                    'intent': chunk.get('intent', ''),
                    'parent_id': chunk.get('parent_id', ''),
                    'section_name': chunk.get('section_name', ''),
                    'order': chunk.get('order', 0),
                    'content_preview': text[:200]  # First 200 chars for preview
                }

                texts.append(text)
                metadatas.append(metadata)

            # Generate embeddings for batch
            embeddings = embedder.encode(texts, show_progress=False)

            # Add to vector store
            vector_store.add_vectors(
                vectors=embeddings,
                metadatas=metadatas
            )

            indexed_count += len(texts)

        except Exception as e:
            print(f"\n⚠️  Error indexing batch {i//batch_size + 1}: {e}")
            failed_count += len(batch)

    print()
    print(f"✅ Indexing complete!")
    print(f"   Successfully indexed: {indexed_count} chunks")
    print(f"   Failed: {failed_count} chunks")
    print(f"   Success rate: {indexed_count / total_chunks * 100:.1f}%")


def main():
    """Main indexing function"""
    print("=" * 80)
    print("INDEXING CHUNKS TO QDRANT VECTOR DATABASE")
    print("=" * 80)
    print()

    # Paths
    chunks_file = current_dir.parent.parent / "data" / "chunks_v2_complete" / "all_chunks_enriched_complete.json"
    vector_store_path = current_dir / "qdrant_storage"

    # Configuration
    embedding_model = "bge-m3"
    ollama_url = "http://localhost:11434"
    batch_size = 50

    print("Configuration:")
    print(f"  Chunks file: {chunks_file}")
    print(f"  Vector store: {vector_store_path}")
    print(f"  Embedding model: {embedding_model}")
    print(f"  Ollama URL: {ollama_url}")
    print(f"  Batch size: {batch_size}")
    print()

    # 1. Load chunks
    chunks = load_chunks(str(chunks_file))

    # Show statistics
    print("\n📊 Chunk Statistics:")

    # Count by tier
    tier_counts = {}
    type_counts = {}
    for chunk in chunks:
        tier = chunk.get('tier', 'unknown')
        chunk_type = chunk.get('chunk_type', 'unknown')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1

    print("   By tier:")
    for tier, count in sorted(tier_counts.items()):
        print(f"      {tier}: {count} chunks")

    print("   By type:")
    for ctype, count in sorted(type_counts.items()):
        print(f"      {ctype}: {count} chunks")

    # 2. Initialize components
    print("\n🔧 Initializing components...")

    # Embedder
    embedder = OllamaEmbedder(
        model_name=embedding_model,
        ollama_url=ollama_url
    )

    # Vector store (will create collection if doesn't exist)
    vector_store = QdrantVectorStore(
        path=str(vector_store_path),
        collection_name="thu_tuc_hanh_chinh"
    )

    print()

    # 3. Confirm before proceeding (auto-confirmed for re-indexing)
    print("⚠️  WARNING: This will RECREATE the collection and DELETE all existing data!")
    print("✅ Auto-confirmed - proceeding with re-indexing...")
    # response = input("Continue? (yes/no): ").strip().lower()
    # if response != 'yes':
    #     print("\n❌ Indexing cancelled by user")
    #     return

    # 4. Index chunks
    index_chunks_to_qdrant(
        chunks=chunks,
        vector_store=vector_store,
        embedder=embedder,
        batch_size=batch_size
    )

    # 5. Verify indexing
    print("\n🔍 Verifying indexed data...")
    info = vector_store.get_collection_info()

    print(f"\n📊 Collection Info:")
    print(f"   Collection: {info.get('collection_name', 'N/A')}")
    print(f"   Total vectors: {info.get('vectors_count', 0)}")
    print(f"   Vector size: {info.get('vector_size', 0)}")

    # 6. Test search
    print("\n🧪 Testing search...")
    test_query = "Đăng ký kết hôn cần giấy tờ gì?"
    print(f"   Query: {test_query}")

    # Embed query
    query_embedding = embedder.encode(test_query, show_progress=False)[0]

    # Search
    results = vector_store.search(
        query_vector=query_embedding,
        top_k=3
    )

    print(f"   Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n   [{i}] Score: {result['score']:.3f}")
        print(f"       Chunk ID: {result['metadata'].get('chunk_id', 'N/A')}")
        print(f"       Procedure: {result['metadata'].get('procedure_name', 'N/A')}")
        print(f"       Type: {result['metadata'].get('chunk_type', 'N/A')}")
        print(f"       Content: {result['metadata'].get('content_preview', 'N/A')[:100]}...")

    print("\n" + "=" * 80)
    print("✅ INDEXING COMPLETE!")
    print("=" * 80)
    print()
    print("Vector database is ready for use!")
    print(f"Total indexed: {info.get('vectors_count', 0)} chunks")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Indexing cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
