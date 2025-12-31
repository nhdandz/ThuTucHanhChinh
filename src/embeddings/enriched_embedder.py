#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enriched Embedder - Generate embeddings với context enrichment cho RAG retrieval

Features:
1. Enriched Format: Breadcrumb + Parent Context + Main Content
2. Ollama Integration: Sử dụng bge-m3 model (local)
3. Batch Processing: Xử lý nhiều chunks cùng lúc
4. Metadata Preservation: Giữ nguyên metadata cho indexing

Format ví dụ:
    [BREADCRUMB] Chính sách > Thủ tục xác nhận bệnh binh > Quy trình
    [CONTEXT] Thủ tục: Thủ tục xác nhận đối với quân nhân...
    [CONTENT] Bước 1: Đối tượng làm đơn đề nghị...
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import requests
from tqdm import tqdm
import time

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class EnrichedEmbedder:
    """
    Generate enriched embeddings for chunks using Ollama bge-m3

    Enrichment strategy:
    - Parent chunks: Full content (already has all info)
    - Child chunks: Breadcrumb + Parent Context (200 chars) + Main Content

    This provides better context for semantic search.
    """

    def __init__(
        self,
        model_name: str = "bge-m3",
        ollama_host: str = "http://localhost:11434",
        batch_size: int = 32,
        max_retries: int = 3
    ):
        """
        Initialize enriched embedder

        Args:
            model_name: Ollama model name (default: bge-m3)
            ollama_host: Ollama API endpoint
            batch_size: Number of chunks to process in parallel
            max_retries: Max retry attempts for failed requests
        """
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.batch_size = batch_size
        self.max_retries = max_retries

        # API endpoints
        self.embed_url = f"{ollama_host}/api/embeddings"
        self.list_url = f"{ollama_host}/api/tags"

        # Verify Ollama is running
        self._verify_ollama_connection()

    def _verify_ollama_connection(self):
        """Verify Ollama server is running and model is available"""
        try:
            response = requests.get(self.list_url, timeout=5)
            response.raise_for_status()

            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            if self.model_name not in model_names and f"{self.model_name}:latest" not in model_names:
                print(f"⚠️  Warning: Model '{self.model_name}' not found in Ollama")
                print(f"   Available models: {', '.join(model_names)}")
                print(f"   To download: ollama pull {self.model_name}")
            else:
                print(f"✅ Ollama connected: {self.ollama_host}")
                print(f"✅ Model available: {self.model_name}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Error: Cannot connect to Ollama at {self.ollama_host}")
            print(f"   Make sure Ollama is running: ollama serve")
            raise

    def format_chunk_for_embedding(self, chunk: Dict) -> str:
        """
        Format chunk with enrichment for better embeddings

        Format:
            [BREADCRUMB] Lĩnh vực > Thủ tục > Section
            [CONTEXT] First 200 chars of parent...
            [CONTENT] Main chunk content

        Args:
            chunk: Chunk dictionary with all fields

        Returns:
            Formatted string for embedding
        """
        # Parent chunks: Use full content (already comprehensive)
        if chunk["chunk_tier"] == "parent":
            return chunk["content"]

        # Child chunks: Add enrichment
        parts = []

        # 1. Breadcrumb for domain/hierarchy context
        if chunk.get("breadcrumb"):
            parts.append(f"[BREADCRUMB] {chunk['breadcrumb']}")

        # 2. Parent context for procedure overview
        if chunk.get("parent_context"):
            parts.append(f"[CONTEXT] {chunk['parent_context']}")

        # 3. Main content
        parts.append(f"[CONTENT] {chunk['content']}")

        return "\n".join(parts)

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate single embedding using Ollama

        Args:
            text: Text to embed

        Returns:
            Embedding vector (list of floats) or None if failed
        """
        payload = {
            "model": self.model_name,
            "prompt": text
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.embed_url,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                embedding = data.get("embedding")

                if embedding:
                    return embedding

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"   ⚠️  Retry {attempt + 1}/{self.max_retries} after {wait_time}s: {str(e)[:100]}")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ Failed after {self.max_retries} attempts: {str(e)[:100]}")
                    return None

        return None

    def embed_chunks(
        self,
        chunks: List[Dict],
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Generate embeddings for all chunks with enrichment

        Args:
            chunks: List of chunk dictionaries
            show_progress: Show progress bar

        Returns:
            List of chunks with 'embedding' field added
        """
        print(f"📊 Embedding {len(chunks)} chunks with enrichment...")
        print(f"   Model: {self.model_name}")
        print(f"   Batch size: {self.batch_size}")
        print()

        enriched_chunks = []
        failed_count = 0

        # Process in batches
        iterator = range(0, len(chunks), self.batch_size)
        if show_progress:
            iterator = tqdm(iterator, desc="Embedding batches", unit="batch")

        for i in iterator:
            batch = chunks[i:i + self.batch_size]

            for chunk in batch:
                # Format with enrichment
                formatted_text = self.format_chunk_for_embedding(chunk)

                # Generate embedding
                embedding = self.generate_embedding(formatted_text)

                if embedding:
                    # Add embedding to chunk
                    chunk_with_embedding = chunk.copy()
                    chunk_with_embedding["embedding"] = embedding
                    chunk_with_embedding["embedding_model"] = self.model_name
                    chunk_with_embedding["enriched_text_preview"] = formatted_text[:200] + "..."

                    enriched_chunks.append(chunk_with_embedding)
                else:
                    failed_count += 1
                    print(f"   ⚠️  Failed to embed chunk: {chunk['chunk_id']}")

        print()
        print(f"✅ Successfully embedded: {len(enriched_chunks)}/{len(chunks)} chunks")
        if failed_count > 0:
            print(f"⚠️  Failed: {failed_count} chunks")

        return enriched_chunks

    def save_embeddings(
        self,
        chunks_with_embeddings: List[Dict],
        output_path: Path
    ):
        """
        Save chunks with embeddings to JSON file

        Args:
            chunks_with_embeddings: Chunks with 'embedding' field
            output_path: Output JSON file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_with_embeddings, f, ensure_ascii=False, indent=2)

        # Calculate file size
        file_size_mb = output_path.stat().st_size / (1024 * 1024)

        print(f"💾 Saved embeddings to: {output_path}")
        print(f"   File size: {file_size_mb:.2f} MB")
        print(f"   Chunks: {len(chunks_with_embeddings)}")

        # Estimate vector dimensions
        if chunks_with_embeddings:
            embedding_dim = len(chunks_with_embeddings[0]["embedding"])
            print(f"   Embedding dimensions: {embedding_dim}")

    @classmethod
    def load_embeddings(cls, embeddings_path: Path) -> List[Dict]:
        """
        Load chunks with embeddings from JSON file

        Args:
            embeddings_path: Path to embeddings JSON file

        Returns:
            List of chunks with embeddings
        """
        with open(embeddings_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        print(f"✅ Loaded {len(chunks)} chunks with embeddings")
        if chunks:
            embedding_dim = len(chunks[0]["embedding"])
            print(f"   Embedding dimensions: {embedding_dim}")

        return chunks


def main():
    """Generate enriched embeddings for all chunks"""
    print("=" * 80)
    print("ENRICHED EMBEDDINGS GENERATOR")
    print("=" * 80)
    print()

    # Paths
    chunks_path = Path("data/chunks_v2_complete/all_chunks_enriched_complete.json")
    output_path = Path("data/embeddings/enriched_embeddings.json")

    # Load chunks
    print(f"📂 Loading chunks from: {chunks_path}")
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"✅ Loaded {len(chunks)} chunks")
    print()

    # Initialize embedder
    embedder = EnrichedEmbedder(
        model_name="bge-m3",
        batch_size=16,  # Smaller batches for stability
        max_retries=3
    )
    print()

    # Show enrichment example
    print("=" * 80)
    print("ENRICHMENT EXAMPLE")
    print("=" * 80)
    sample_chunk = chunks[0]
    formatted = embedder.format_chunk_for_embedding(sample_chunk)
    print(f"Chunk ID: {sample_chunk['chunk_id']}")
    print(f"Type: {sample_chunk['chunk_type']}")
    print()
    print("Formatted for embedding:")
    print("-" * 80)
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
    print()
    print("=" * 80)
    print()

    # Generate embeddings
    chunks_with_embeddings = embedder.embed_chunks(chunks, show_progress=True)

    # Save
    embedder.save_embeddings(chunks_with_embeddings, output_path)

    print()
    print("=" * 80)
    print("✅ DONE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
