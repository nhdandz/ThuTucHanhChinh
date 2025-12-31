#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete RAG Pipeline - Integrates Retrieval + Generation
Provides end-to-end question answering for administrative procedures
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "retrieval"))
sys.path.insert(0, str(Path(__file__).parent.parent / "generation"))

from embedding_model import OllamaEmbedder
from vector_store import QdrantVectorStore
from query_enhancer import OllamaQueryEnhancer
from retrieval_pipeline import HierarchicalRetrievalPipeline, RetrievalResult
from answer_generator import OllamaAnswerGenerator, GeneratedAnswer
from context_settings import get_context_config  # Intent-based context optimization

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class ThuTucRAGPipeline:
    """
    Complete RAG Pipeline for Administrative Procedures

    Pipeline stages:
    1. Query Enhancement (intent detection, entity extraction)
    2. Hierarchical Retrieval (5-stage retrieval)
    3. Answer Generation (JSON + Natural Language)
    4. Source Citation

    Features:
    - 100% context-based answers (no hallucination)
    - Hybrid output format
    - Confidence scoring
    - Source tracking
    """

    def __init__(
        self,
        vector_store_path: str = "./qdrant_storage",
        collection_name: str = "thu_tuc_procedures",
        embedding_model: str = "bge-m3",
        llm_model: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize complete RAG pipeline

        Args:
            vector_store_path: Path to Qdrant vector database
            collection_name: Qdrant collection name
            embedding_model: Embedding model name (for Ollama)
            llm_model: LLM model name (for Ollama)
            ollama_url: Ollama server URL
        """
        # Store configuration as instance variables
        self.vector_store_path = vector_store_path
        self.collection_name = collection_name

        print("\n" + "=" * 80)
        print("🚀 INITIALIZING THU TUC RAG PIPELINE")
        print("=" * 80)
        print()
        print("Configuration:")
        print(f"  Vector Store: {vector_store_path}")
        print(f"  Collection: {collection_name}")
        print(f"  Embedding Model: {embedding_model}")
        print(f"  LLM Model: {llm_model}")
        print(f"  Ollama URL: {ollama_url}")
        print()

        # Initialize components
        print("📦 Loading components...")
        print()

        # Embedder
        self.embedder = OllamaEmbedder(
            model_name=embedding_model,
            ollama_url=ollama_url
        )

        # Vector Store
        self.vector_store = QdrantVectorStore(path=vector_store_path)

        # Query Enhancer
        self.query_enhancer = OllamaQueryEnhancer(
            model_name=llm_model,
            ollama_url=ollama_url
        )

        # Load all chunks from Qdrant for BM25 initialization
        print("📥 Loading chunks from vector store for BM25...")
        chunks = self._load_chunks_from_vector_store()
        print(f"   ✓ Loaded {len(chunks)} chunks")

        # Retrieval Pipeline
        self.retrieval_pipeline = HierarchicalRetrievalPipeline(
            embedder=self.embedder,
            vector_store=self.vector_store,
            query_enhancer=self.query_enhancer,
            chunks=chunks  # Pass chunks for BM25 initialization
        )

        # Answer Generator
        self.answer_generator = OllamaAnswerGenerator(
            model_name=llm_model,
            ollama_url=ollama_url
        )

        print()
        print("=" * 80)
        print("✅ PIPELINE READY!")
        print("=" * 80)

    def _load_chunks_from_vector_store(self) -> List[Dict]:
        """
        Load all chunks from Qdrant vector store for BM25 initialization
        Uses the already-initialized vector_store to avoid concurrent access issues

        Returns:
            List of chunk dictionaries with content and metadata
        """
        import traceback

        try:
            # Reuse existing vector store client to avoid "already accessed" error
            client = self.vector_store.client

            # Scroll through all points in the collection
            chunks = []
            scroll_result = client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # Get all chunks in one go
                with_payload=True,
                with_vectors=False  # Don't need vectors, just payload
            )

            points = scroll_result[0]

            for point in points:
                chunk = {
                    "chunk_id": point.payload.get("chunk_id", ""),  # Read string chunk_id from payload
                    "content": point.payload.get("content", ""),
                    "chunk_type": point.payload.get("chunk_type", "unknown"),
                    "mã_thủ_tục": point.payload.get("thu_tuc_id", ""),  # Read from thu_tuc_id in payload
                    "tên_thủ_tục": point.payload.get("metadata", {}).get("tên_thủ_tục", ""),  # Read from metadata
                }
                chunks.append(chunk)

            return chunks

        except Exception as e:
            print(f"   ⚠️  Failed to load chunks from vector store: {e}")
            traceback.print_exc()  # Print full stack trace for debugging
            print("   ⚠️  BM25 will not be available")
            return []

    def answer_question(
        self,
        question: str,
        top_k_parent: int = 5,
        top_k_child: int = 20,
        top_k_final: int = 3,
        verbose: bool = True
    ) -> GeneratedAnswer:
        """
        Answer a question using complete RAG pipeline

        Args:
            question: User question
            top_k_parent: Number of parent chunks to retrieve
            top_k_child: Number of child chunks to retrieve
            top_k_final: Number of final chunks after re-ranking
            verbose: Whether to print detailed progress

        Returns:
            GeneratedAnswer with complete answer and sources
        """
        if verbose:
            print("\n\n")
            print("🔍" * 40)
            print(f"PROCESSING QUESTION: {question}")
            print("🔍" * 40)
            print()

        # PHASE 1-3: Retrieval (5-stage hierarchical retrieval)
        retrieval_result = self.retrieval_pipeline.retrieve(
            question=question,
            top_k_parent=top_k_parent,
            top_k_child=top_k_child,
            top_k_final=top_k_final
        )

        # Get context config for intent-based structured output control
        context_config = get_context_config(retrieval_result.intent)

        # PHASE 4: Generation
        answer = self.answer_generator.generate(
            question=retrieval_result.query,
            intent=retrieval_result.intent,
            context=retrieval_result.context,
            retrieved_chunks=retrieval_result.retrieved_chunks,
            confidence=retrieval_result.confidence,
            metadata=retrieval_result.metadata,
            enable_structured_output=context_config['enable_structured_output']  # Intent-based control
        )

        return answer

    def batch_answer(
        self,
        questions: List[str],
        export_dir: Optional[str] = None,
        **kwargs
    ) -> List[GeneratedAnswer]:
        """
        Answer multiple questions in batch

        Args:
            questions: List of questions
            export_dir: Optional directory to export answers
            **kwargs: Additional arguments for answer_question

        Returns:
            List of GeneratedAnswer objects
        """
        print("\n" + "=" * 80)
        print(f"🔄 BATCH PROCESSING: {len(questions)} questions")
        print("=" * 80)

        answers = []

        for i, question in enumerate(questions, 1):
            print(f"\n\n{'=' * 80}")
            print(f"QUESTION {i}/{len(questions)}")
            print(f"{'=' * 80}")

            answer = self.answer_question(question, **kwargs)
            answers.append(answer)

            # Export if directory specified
            if export_dir:
                export_path = Path(export_dir)
                export_path.mkdir(parents=True, exist_ok=True)
                filename = export_path / f"answer_{i:03d}.json"
                self.answer_generator.export_answer_json(answer, str(filename))

        print("\n" + "=" * 80)
        print(f"✅ BATCH COMPLETE: {len(answers)} answers generated")
        print("=" * 80)

        return answers

    def display_answer(self, answer: GeneratedAnswer):
        """
        Display answer in user-friendly format

        Args:
            answer: GeneratedAnswer object
        """
        print(self.answer_generator.format_answer_for_display(answer))

    def get_collection_stats(self):
        """Display statistics about the vector database"""
        stats = self.vector_store.get_collection_info()

        print("\n" + "=" * 80)
        print("📊 VECTOR DATABASE STATISTICS")
        print("=" * 80)
        print(f"Collection: {stats.get('collection_name', 'N/A')}")
        print(f"Total vectors: {stats.get('vectors_count', 0):,}")
        print(f"Vector dimension: {stats.get('vector_size', 0)}")
        print(f"Status: {stats.get('status', 'N/A')}")
        print("=" * 80)


def test_rag_pipeline():
    """Test complete RAG pipeline with sample queries"""
    print("\n\n")
    print("*" * 80)
    print("TESTING COMPLETE RAG PIPELINE")
    print("*" * 80)
    print()

    # Initialize pipeline
    # Use absolute path to vector store
    vector_store_path = str(Path(__file__).parent.parent / "retrieval" / "qdrant_storage")
    pipeline = ThuTucRAGPipeline(
        vector_store_path=vector_store_path,
        embedding_model="bge-m3",
        llm_model="qwen3:8b"
    )

    # Show database stats
    pipeline.get_collection_stats()

    # Test queries covering different intents
    test_queries = [
        "Đăng ký kết hôn cần giấy tờ gì?",  # documents
        "Thủ tục đăng ký kinh doanh có những điều kiện gì?",  # requirements
        "Xin giấy phép xây dựng mất bao lâu?",  # timeline
    ]

    # Process each query
    answers = pipeline.batch_answer(
        questions=test_queries,
        export_dir="./test_answers",
        top_k_parent=5,
        top_k_child=15,
        top_k_final=3,
        verbose=True
    )

    # Display results
    print("\n\n")
    print("*" * 80)
    print("📋 FINAL RESULTS SUMMARY")
    print("*" * 80)

    for i, answer in enumerate(answers, 1):
        print(f"\n[{i}] {answer.question}")
        print(f"    Intent: {answer.intent}")
        print(f"    Confidence: {answer.confidence:.0%}")
        print(f"    Sources: {len(answer.sources)}")
        print(f"    Answer length: {len(answer.answer)} chars")

    print("\n" + "*" * 80)
    print("✅ TEST COMPLETE!")
    print("*" * 80)


def interactive_mode():
    """Run pipeline in interactive mode"""
    print("\n\n")
    print("*" * 80)
    print("🤖 THỦ TỤC HÀNH CHÍNH - INTERACTIVE RAG")
    print("*" * 80)
    print()

    # Initialize pipeline
    # Use absolute path to vector store
    vector_store_path = str(Path(__file__).parent.parent / "retrieval" / "qdrant_storage")
    pipeline = ThuTucRAGPipeline(
        vector_store_path=vector_store_path,
        embedding_model="bge-m3",
        llm_model="qwen3:8b"
    )

    pipeline.get_collection_stats()

    print("\n" + "=" * 80)
    print("💡 Nhập câu hỏi của bạn (hoặc 'quit' để thoát)")
    print("=" * 80)

    while True:
        try:
            print()
            question = input("\n❓ Câu hỏi: ").strip()

            if not question:
                continue

            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Tạm biệt!")
                break

            # Process question
            answer = pipeline.answer_question(question)

            # Display answer
            pipeline.display_answer(answer)

        except KeyboardInterrupt:
            print("\n\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"\n⚠️ Lỗi: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        test_rag_pipeline()
