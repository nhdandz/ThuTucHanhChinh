#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate embeddings for chunks using BGE-M3
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class EmbeddingGenerator:
    """
    Generate embeddings using BGE-M3 model
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """Initialize embedding model"""
        print(f"🔄 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded. Embedding dimension: {self.embedding_dim}")

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding

    def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """Generate embeddings for batch of texts"""
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings

    def embed_chunks(
        self,
        chunks: List[Dict],
        batch_size: int = 32
    ) -> List[Dict]:
        """
        Generate embeddings for all chunks
        Returns chunks with added 'embedding' field
        """
        print(f"\n🔄 Generating embeddings for {len(chunks)} chunks...")
        print(f"Batch size: {batch_size}")
        print()

        # Extract texts
        texts = [chunk["content"] for chunk in chunks]

        # Generate embeddings
        embeddings = self.generate_batch_embeddings(
            texts,
            batch_size=batch_size,
            show_progress=True
        )

        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i].tolist()

        print(f"\n✅ Generated {len(chunks)} embeddings")
        print(f"Embedding shape: ({len(chunks)}, {self.embedding_dim})")

        return chunks


def main():
    """Main function"""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_dir = project_root / "data"
    chunks_dir = data_dir / "chunks"
    embeddings_dir = data_dir / "embeddings"

    # Load chunks
    chunks_file = chunks_dir / "all_chunks.json"
    print(f"📂 Loading chunks from: {chunks_file}")

    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"✅ Loaded {len(chunks)} chunks")
    print()

    # Create embedding generator
    generator = EmbeddingGenerator()

    # Generate embeddings
    chunks_with_embeddings = generator.embed_chunks(chunks, batch_size=32)

    # Save
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    output_file = embeddings_dir / "chunks_with_embeddings.json"

    print(f"\n💾 Saving chunks with embeddings...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks_with_embeddings, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved to: {output_file}")

    # Generate statistics
    print("\n" + "=" * 80)
    print("EMBEDDING STATISTICS")
    print("=" * 80)

    # Check embedding stats
    embeddings_array = np.array([c["embedding"] for c in chunks_with_embeddings])
    print(f"Shape: {embeddings_array.shape}")
    print(f"Mean: {embeddings_array.mean():.4f}")
    print(f"Std: {embeddings_array.std():.4f}")
    print(f"Min: {embeddings_array.min():.4f}")
    print(f"Max: {embeddings_array.max():.4f}")

    # Check by chunk type
    print("\nBy chunk type:")
    chunk_types = set(c["chunk_type"] for c in chunks_with_embeddings)
    for chunk_type in sorted(chunk_types):
        type_chunks = [c for c in chunks_with_embeddings if c["chunk_type"] == chunk_type]
        print(f"  {chunk_type}: {len(type_chunks)} chunks")

    print("=" * 80)


if __name__ == "__main__":
    main()
