#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Embedding Model Wrapper supporting Ollama and HuggingFace
Optimized for Vietnamese text
"""

import sys
from typing import List, Union, Optional
import numpy as np
import requests
import json
from tqdm import tqdm

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class OllamaEmbedder:
    """
    Wrapper for Ollama embedding models
    Supports: bge-m3, nomic-embed-text, etc.
    """

    def __init__(
        self,
        model_name: str = "bge-m3",
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize Ollama embedding model

        Args:
            model_name: Ollama model name (e.g., "bge-m3", "nomic-embed-text")
            ollama_url: Ollama server URL
        """
        print(f"🔄 Initializing Ollama embedding model: {model_name}")
        print(f"   Server: {ollama_url}")

        self.model_name = model_name
        self.ollama_url = ollama_url
        self.embed_endpoint = f"{ollama_url}/api/embeddings"

        # Determine embedding dimension based on model
        self.embedding_dim = 1024 if "bge-m3" in model_name else 768

        # Test connection
        self._test_connection()

        print(f"✅ Model initialized successfully!")
        print(f"   Embedding dimension: {self.embedding_dim}")

    def _test_connection(self):
        """Test connection to Ollama server"""
        try:
            response = requests.post(
                self.embed_endpoint,
                json={"model": self.model_name, "prompt": "test"},
                timeout=10
            )
            if response.status_code != 200:
                raise Exception(f"Ollama returned status {response.status_code}")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to Ollama: {e}")
            print(f"   Make sure Ollama is running: ollama serve")

    def _embed_single(self, text: str) -> np.ndarray:
        """Embed a single text using Ollama API"""
        response = requests.post(
            self.embed_endpoint,
            json={"model": self.model_name, "prompt": text},
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")

        embedding = response.json()["embedding"]
        return np.array(embedding, dtype=np.float32)

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = True,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Encode texts to embeddings using Ollama

        Args:
            texts: Single text or list of texts
            batch_size: Not used (Ollama processes one at a time)
            show_progress: Show progress bar
            normalize: Normalize embeddings to unit length

        Returns:
            Numpy array of embeddings (N x embedding_dim)
        """
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]

        # Encode each text
        embeddings = []
        iterator = tqdm(texts, desc="Encoding") if show_progress else texts

        for text in iterator:
            try:
                embedding = self._embed_single(text)
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error embedding text: {e}")
                # Return zero vector on error
                embeddings.append(np.zeros(self.embedding_dim, dtype=np.float32))

        embeddings = np.array(embeddings)

        # Normalize if requested
        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            embeddings = embeddings / norms

        return embeddings

    def encode_queries(self, queries: Union[str, List[str]], **kwargs) -> np.ndarray:
        """
        Encode queries (same as encode but with explicit name)

        Args:
            queries: Single query or list of queries
            **kwargs: Additional arguments for encode()

        Returns:
            Numpy array of query embeddings
        """
        return self.encode(queries, **kwargs)

    def encode_documents(self, documents: List[str], **kwargs) -> np.ndarray:
        """
        Encode documents in batches

        Args:
            documents: List of documents
            **kwargs: Additional arguments for encode()

        Returns:
            Numpy array of document embeddings
        """
        return self.encode(documents, **kwargs)

    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim


def test_embedder():
    """Test Ollama embedding model"""
    print("=" * 80)
    print("TEST OLLAMA EMBEDDER (BGE-M3)")
    print("=" * 80)
    print()

    # Initialize
    embedder = OllamaEmbedder(model_name="bge-m3")
    print()

    # Test với tiếng Việt
    test_texts = [
        "Thủ tục đăng ký kết hôn cần giấy tờ gì?",
        "Hồ sơ đăng ký kinh doanh bao gồm những gì?",
        "Cách thức nộp hồ sơ xin cấp giấy phép xây dựng"
    ]

    print("Test texts:")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. {text}")
    print()

    # Encode
    print("Encoding...")
    embeddings = embedder.encode(test_texts, show_progress=True)

    print()
    print("Results:")
    print(f"  Shape: {embeddings.shape}")
    print(f"  Dtype: {embeddings.dtype}")
    print(f"  Sample embedding (first 10 dims): {embeddings[0][:10]}")

    # Compute similarity
    print()
    print("Computing similarities...")
    similarities = []
    for i in range(len(embeddings)):
        for j in range(i+1, len(embeddings)):
            sim = np.dot(embeddings[i], embeddings[j])
            similarities.append((i, j, sim))
            print(f"  Text {i+1} <-> Text {j+1}: {sim:.4f}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    test_embedder()
