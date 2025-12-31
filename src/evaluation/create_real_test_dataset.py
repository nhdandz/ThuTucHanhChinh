#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create Test Dataset Based on ACTUAL 207 Procedures
Uses real procedures from Bộ Quốc phòng database
"""

import sys
import json
import re
from pathlib import Path
from test_dataset import TestDatasetManager

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def load_procedures_from_chunks():
    """Load all procedures from chunks file"""
    chunks_file = Path(__file__).parent.parent.parent / "data" / "chunks" / "all_chunks.json"

    print(f"📂 Loading chunks from: {chunks_file}")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Extract procedures
    procedures = {}
    for chunk in chunks:
        thu_tuc_id = chunk.get('thu_tuc_id')
        chunk_type = chunk.get('chunk_type')

        if thu_tuc_id not in procedures:
            procedures[thu_tuc_id] = {
                'id': thu_tuc_id,
                'chunks': []
            }

        procedures[thu_tuc_id]['chunks'].append({
            'type': chunk_type,
            'tier': chunk.get('chunk_tier'),
            'content': chunk.get('content', ''),
            'chunk_id': chunk.get('chunk_id')
        })

    # Parse each procedure
    for proc_id, proc in procedures.items():
        # Find parent chunk
        parent = next((c for c in proc['chunks'] if c['tier'] == 'parent'), None)
        if parent:
            content = parent['content']

            # Extract metadata
            name_match = re.search(r'THỦ TỤC: (.+?)\n', content)
            linh_vuc_match = re.search(r'LĨNH VỰC: (.+?)\n', content)

            proc['name'] = name_match.group(1) if name_match else 'N/A'
            proc['linh_vuc'] = linh_vuc_match.group(1) if linh_vuc_match else 'N/A'
            proc['parent_content'] = content

    print(f"✅ Loaded {len(procedures)} procedures")
    return procedures


def extract_documents_from_chunk(chunk_content):
    """Extract required documents from a child_documents chunk"""
    # Look for structured list
    docs = []

    # Pattern: numbered lists
    lines = chunk_content.split('\n')
    for line in lines:
        # Match patterns like "1. Document name - số lượng"
        if re.match(r'^\d+\.\s+', line):
            docs.append(line.strip())

    return docs


def extract_timeline_from_chunk(chunk_content):
    """Extract timeline information"""
    # Look for time-related patterns
    time_patterns = [
        r'(\d+)\s+ngày làm việc',
        r'Trong\s+(\d+)\s+ngày',
        r'Không quá\s+(\d+)\s+ngày',
    ]

    for pattern in time_patterns:
        match = re.search(pattern, chunk_content)
        if match:
            return match.group(0)

    return None


def create_test_case_for_procedure(proc_id, proc, intent_type, difficulty):
    """Create a test case for a specific procedure and intent"""

    # Find relevant child chunk
    child_chunks = [c for c in proc['chunks'] if c['tier'] == 'child' and intent_type in c['type']]

    if not child_chunks:
        return None

    child_chunk = child_chunks[0]
    content = child_chunk['content']

    # Create test case based on intent
    if intent_type == 'documents':
        # Documents query
        question = f"{proc['name']} cần giấy tờ gì?"
        docs = extract_documents_from_chunk(content)

        if not docs:
            return None

        return {
            'test_id': f"DOC_{difficulty.upper()}_{proc_id.replace('.', '_')}",
            'category': 'documents',
            'difficulty': difficulty,
            'question': question,
            'natural_language_answer': f"Hồ sơ {proc['name']} bao gồm:\n" + "\n".join(docs),
            'key_facts': docs[:5],  # Top 5 documents
            'structured_data': {
                'ho_so_bao_gom': [doc.split('.', 1)[1].strip() if '.' in doc else doc for doc in docs[:5]]
            },
            'required_aspects': ['Danh sách giấy tờ'],
            'source_procedure': proc['name'],
            'metadata': {'thu_tuc_id': proc_id, 'linh_vuc': proc['linh_vuc']}
        }

    elif intent_type == 'timeline':
        # Timeline query
        question = f"{proc['name']} mất bao lâu?"
        timeline = extract_timeline_from_chunk(content)

        if not timeline:
            # Try parent content
            timeline = extract_timeline_from_chunk(proc.get('parent_content', ''))

        if not timeline:
            return None

        return {
            'test_id': f"TIME_{difficulty.upper()}_{proc_id.replace('.', '_')}",
            'category': 'timeline',
            'difficulty': difficulty,
            'question': question,
            'natural_language_answer': f"Thời gian giải quyết: {timeline}",
            'key_facts': [timeline],
            'structured_data': {
                'thoi_han_giai_quyet': timeline
            },
            'required_aspects': ['Thời hạn giải quyết'],
            'source_procedure': proc['name'],
            'metadata': {'thu_tuc_id': proc_id, 'linh_vuc': proc['linh_vuc']}
        }

    elif intent_type == 'requirements':
        # Requirements query
        question = f"{proc['name']} cần điều kiện gì?"

        # Extract from child_requirements chunk
        req_chunks = [c for c in proc['chunks'] if 'requirements' in c['type']]
        if not req_chunks:
            return None

        req_content = req_chunks[0]['content']

        # Extract requirements (simple pattern matching)
        requirements = []
        lines = req_content.split('\n')
        for line in lines:
            if re.match(r'^[-•\*]\s+', line) or re.match(r'^\d+\.\s+', line):
                requirements.append(line.strip())

        if not requirements:
            return None

        return {
            'test_id': f"REQ_{difficulty.upper()}_{proc_id.replace('.', '_')}",
            'category': 'requirements',
            'difficulty': difficulty,
            'question': question,
            'natural_language_answer': f"Điều kiện thực hiện:\n" + "\n".join(requirements[:5]),
            'key_facts': requirements[:5],
            'structured_data': {
                'dieu_kien': [req.lstrip('-•* ').lstrip('0123456789. ') for req in requirements[:5]]
            },
            'required_aspects': ['Điều kiện'],
            'source_procedure': proc['name'],
            'metadata': {'thu_tuc_id': proc_id, 'linh_vuc': proc['linh_vuc']}
        }

    elif intent_type == 'overview':
        # Overview query
        question = f"Thủ tục {proc['name']} là gì?"

        parent_content = proc.get('parent_content', '')

        # Extract summary
        summary_match = re.search(r'TÓM TẮT:\n(.+?)(?:\n\n|$)', parent_content, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else parent_content[:200]

        return {
            'test_id': f"OVER_{difficulty.upper()}_{proc_id.replace('.', '_')}",
            'category': 'overview',
            'difficulty': difficulty,
            'question': question,
            'natural_language_answer': summary,
            'key_facts': [proc['name']],
            'structured_data': {
                'ten_thu_tuc': proc['name'],
                'linh_vuc': proc['linh_vuc']
            },
            'required_aspects': ['Tên thủ tục', 'Mục đích'],
            'source_procedure': proc['name'],
            'metadata': {'thu_tuc_id': proc_id, 'linh_vuc': proc['linh_vuc']}
        }

    return None


def create_comprehensive_dataset():
    """Create comprehensive test dataset from real procedures"""

    print("=" * 80)
    print("CREATING TEST DATASET FROM REAL PROCEDURES")
    print("=" * 80)
    print()

    # Load procedures
    procedures = load_procedures_from_chunks()

    # Select diverse procedures across domains
    selected_procedures = []

    # Priority domains with procedure examples
    priority_selections = [
        ('1.013133', 'easy'),     # Đăng ký NVQS lần đầu
        ('1.013134', 'easy'),     # Đăng ký NVQS chuyển đi
        ('1.013140', 'medium'),   # Chế độ hưu trí quân nhân
        ('1.013272', 'medium'),   # Cấp phép bay tàu bay không người lái
        ('1.013614', 'easy'),     # Cấp giấy phép hành nghề y tế
        ('1.013124', 'medium'),   # Ứng phó sự cố tràn dầu
        ('1.013270', 'hard'),     # Cấp phép dịch vụ bảo vệ tàu quân sự
        ('1.013129', 'medium'),   # Thẩm định xe cơ giới
        ('1.013524', 'medium'),   # Giải quyết khiếu nại
        ('1.013513', 'easy'),     # Dân quân tự vệ
    ]

    for proc_id, difficulty in priority_selections:
        if proc_id in procedures:
            selected_procedures.append((proc_id, procedures[proc_id], difficulty))

    print(f"📋 Selected {len(selected_procedures)} diverse procedures")
    print()

    # Create test dataset manager
    manager = TestDatasetManager()

    # Create test cases
    test_count = 0
    intent_types = ['documents', 'timeline', 'requirements', 'overview']

    for proc_id, proc, difficulty in selected_procedures:
        print(f"Creating tests for: [{proc_id}] {proc['name'][:60]}...")

        for intent in intent_types:
            test_case = create_test_case_for_procedure(proc_id, proc, intent, difficulty)

            if test_case:
                manager.add_test_case(**test_case)
                test_count += 1
                print(f"  ✅ {intent}")
            else:
                print(f"  ⏭️  {intent} (không có data)")

        print()

    print(f"✅ Created {test_count} test cases")
    print()

    # Export
    output_file = Path(__file__).parent / "real_test_dataset.json"
    manager.export_dataset(str(output_file))

    # Show statistics
    stats = manager.get_statistics()
    print()
    print("📊 Dataset Statistics:")
    print(f"   Total: {stats['total_cases']} cases")
    print(f"   By category:")
    for cat, count in sorted(stats['by_category'].items()):
        print(f"      {cat}: {count}")
    print(f"   By difficulty:")
    for diff, count in sorted(stats['by_difficulty'].items()):
        print(f"      {diff}: {count}")

    return manager


if __name__ == "__main__":
    try:
        create_comprehensive_dataset()
        print()
        print("=" * 80)
        print("✅ TEST DATASET CREATED SUCCESSFULLY!")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
