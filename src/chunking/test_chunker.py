#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test hierarchical chunker với một vài file mẫu
"""

import sys
import json
from pathlib import Path
from hierarchical_chunker import HierarchicalChunker
from dataclasses import asdict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_single_file(file_path: Path):
    """Test chunking với 1 file"""
    print("=" * 80)
    print(f"TESTING: {file_path.name}")
    print("=" * 80)
    print()

    # Load data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create chunker
    chunker = HierarchicalChunker()

    # Chunk
    chunks = chunker.chunk_thu_tuc(data)

    # Display results
    print(f"📊 Thủ tục: {data['metadata'].get('tên_thủ_tục', '')}")
    print(f"📦 Tổng số chunks: {len(chunks)}")
    print()

    # Display each chunk
    for i, chunk in enumerate(chunks, 1):
        print(f"--- Chunk {i}: {chunk.chunk_type} ---")
        print(f"ID: {chunk.chunk_id}")
        print(f"Tier: {chunk.chunk_tier}")
        print(f"Parent ID: {chunk.parent_chunk_id}")
        print(f"Tokens: {chunk.token_count}")
        print(f"Content preview (first 200 chars):")
        print(chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content)
        print()

    return chunks


def test_multiple_files(extracted_dir: Path, num_files: int = 5):
    """Test với nhiều files"""
    json_files = list(extracted_dir.glob("*.json"))[:num_files]

    chunker = HierarchicalChunker()
    all_chunks = []

    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunks = chunker.chunk_thu_tuc(data)
        all_chunks.extend(chunks)

    # Statistics
    print("=" * 80)
    print(f"SUMMARY: {num_files} files")
    print("=" * 80)
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Parent chunks: {sum(1 for c in all_chunks if c.chunk_tier == 'parent')}")
    print(f"Child chunks: {sum(1 for c in all_chunks if c.chunk_tier == 'child')}")
    print()

    # By type
    chunk_types = {}
    for chunk in all_chunks:
        chunk_type = chunk.chunk_type
        if chunk_type not in chunk_types:
            chunk_types[chunk_type] = {"count": 0, "total_tokens": 0}
        chunk_types[chunk_type]["count"] += 1
        chunk_types[chunk_type]["total_tokens"] += chunk.token_count

    print("Chunks by type:")
    for chunk_type, stats in chunk_types.items():
        avg_tokens = stats["total_tokens"] / stats["count"]
        print(f"  {chunk_type}: {stats['count']} chunks, avg {avg_tokens:.1f} tokens")

    return all_chunks


def main():
    """Main test function"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    extracted_dir = project_root / "data" / "extracted"

    if not extracted_dir.exists():
        print(f"❌ Directory not found: {extracted_dir}")
        return

    # Test 1: Single file
    print("\n" + "="*80)
    print("TEST 1: SINGLE FILE")
    print("="*80 + "\n")

    sample_file = extracted_dir / "1.013124.json"
    test_single_file(sample_file)

    # Test 2: Multiple files
    print("\n" + "="*80)
    print("TEST 2: MULTIPLE FILES (5 samples)")
    print("="*80 + "\n")

    test_multiple_files(extracted_dir, num_files=5)


if __name__ == "__main__":
    main()
