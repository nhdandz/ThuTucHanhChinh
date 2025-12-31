#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Dataset Structure for RAG Evaluation
Defines schema and manages test question-answer pairs
"""

import sys
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class GroundTruthAnswer:
    """Ground truth answer with structured data"""
    natural_language: str
    key_facts: List[str]
    structured_data: Dict
    required_aspects: List[str]


@dataclass
class TestCase:
    """Single test case for evaluation"""
    test_id: str
    category: str  # documents, requirements, process, timeline, legal, fees, overview
    difficulty: str  # easy, medium, hard
    question: str
    ground_truth: GroundTruthAnswer
    source_procedure: str  # Procedure name/code
    metadata: Dict


@dataclass
class TestDataset:
    """Complete test dataset"""
    dataset_name: str
    version: str
    created_at: str
    test_cases: List[TestCase]
    statistics: Dict


class TestDatasetManager:
    """Manages test dataset for RAG evaluation"""

    def __init__(self):
        """Initialize dataset manager"""
        self.test_cases = []

    def add_test_case(
        self,
        test_id: str,
        category: str,
        difficulty: str,
        question: str,
        natural_language_answer: str,
        key_facts: List[str],
        structured_data: Dict,
        required_aspects: List[str],
        source_procedure: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add a test case to the dataset

        Args:
            test_id: Unique test identifier
            category: Intent category
            difficulty: easy, medium, hard
            question: Test question
            natural_language_answer: Expected answer in natural language
            key_facts: List of key facts that must be present
            structured_data: Expected structured JSON data
            required_aspects: List of aspects that must be addressed
            source_procedure: Source procedure name/code
            metadata: Additional metadata
        """
        ground_truth = GroundTruthAnswer(
            natural_language=natural_language_answer,
            key_facts=key_facts,
            structured_data=structured_data,
            required_aspects=required_aspects
        )

        test_case = TestCase(
            test_id=test_id,
            category=category,
            difficulty=difficulty,
            question=question,
            ground_truth=ground_truth,
            source_procedure=source_procedure,
            metadata=metadata or {}
        )

        self.test_cases.append(test_case)

    def get_statistics(self) -> Dict:
        """Get dataset statistics"""
        stats = {
            "total_cases": len(self.test_cases),
            "by_category": {},
            "by_difficulty": {}
        }

        for test_case in self.test_cases:
            # By category
            cat = test_case.category
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

            # By difficulty
            diff = test_case.difficulty
            stats["by_difficulty"][diff] = stats["by_difficulty"].get(diff, 0) + 1

        return stats

    def export_dataset(self, filepath: str):
        """
        Export dataset to JSON file

        Args:
            filepath: Output file path
        """
        dataset = TestDataset(
            dataset_name="Thu Tuc Hanh Chinh RAG Test Dataset",
            version="1.0",
            created_at=datetime.now().isoformat(),
            test_cases=self.test_cases,
            statistics=self.get_statistics()
        )

        # Convert to dict
        dataset_dict = asdict(dataset)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset_dict, f, ensure_ascii=False, indent=2)

        print(f"✅ Dataset exported to: {filepath}")
        print(f"   Total test cases: {len(self.test_cases)}")
        print(f"   Statistics: {self.get_statistics()}")

    def load_dataset(self, filepath: str):
        """
        Load dataset from JSON file

        Args:
            filepath: Input file path
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            dataset_dict = json.load(f)

        self.test_cases = []

        for tc_dict in dataset_dict.get('test_cases', []):
            # Reconstruct GroundTruthAnswer
            gt_dict = tc_dict['ground_truth']
            ground_truth = GroundTruthAnswer(**gt_dict)

            # Reconstruct TestCase
            test_case = TestCase(
                test_id=tc_dict['test_id'],
                category=tc_dict['category'],
                difficulty=tc_dict['difficulty'],
                question=tc_dict['question'],
                ground_truth=ground_truth,
                source_procedure=tc_dict['source_procedure'],
                metadata=tc_dict.get('metadata', {})
            )

            self.test_cases.append(test_case)

        print(f"✅ Dataset loaded from: {filepath}")
        print(f"   Total test cases: {len(self.test_cases)}")

    def filter_by_category(self, category: str) -> List[TestCase]:
        """Filter test cases by category"""
        return [tc for tc in self.test_cases if tc.category == category]

    def filter_by_difficulty(self, difficulty: str) -> List[TestCase]:
        """Filter test cases by difficulty"""
        return [tc for tc in self.test_cases if tc.difficulty == difficulty]

    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """Get specific test case by ID"""
        for tc in self.test_cases:
            if tc.test_id == test_id:
                return tc
        return None


def create_sample_dataset():
    """Create a sample test dataset"""
    print("=" * 80)
    print("CREATING SAMPLE TEST DATASET")
    print("=" * 80)
    print()

    manager = TestDatasetManager()

    # Test Case 1: Documents query (easy)
    manager.add_test_case(
        test_id="TEST_001",
        category="documents",
        difficulty="easy",
        question="Đăng ký kết hôn cần giấy tờ gì?",
        natural_language_answer="""
Để đăng ký kết hôn, bạn cần chuẩn bị các giấy tờ sau:
1. Giấy tờ tùy thân (CMND/CCCD/Hộ chiếu) của cả hai bên - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính (đối với người từ 30 tuổi trở lên hoặc đã ly hôn)
3. Giấy khám sức khỏe tiền hôn nhân - 01 bản chính
4. Đơn đăng ký kết hôn - 01 bản
5. Ảnh 4x6 - 02 ảnh (nếu nhận Giấy chứng nhận kết hôn có ảnh)

Số lượng hồ sơ: 02 bộ
        """.strip(),
        key_facts=[
            "CMND/CCCD/Hộ chiếu - 02 bản sao",
            "Giấy xác nhận tình trạng hôn nhân - 01 bản chính",
            "Giấy khám sức khỏe tiền hôn nhân - 01 bản chính",
            "Đơn đăng ký kết hôn - 01 bản",
            "Ảnh 4x6 - 02 ảnh"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Giấy tờ tùy thân (CMND/CCCD/Hộ chiếu)",
                "Giấy xác nhận tình trạng hôn nhân",
                "Giấy khám sức khỏe tiền hôn nhân",
                "Đơn đăng ký kết hôn",
                "Ảnh 4x6"
            ],
            "so_ban": {
                "Giấy tờ tùy thân": "02",
                "Giấy xác nhận tình trạng hôn nhân": "01",
                "Giấy khám sức khỏe tiền hôn nhân": "01",
                "Đơn đăng ký kết hôn": "01",
                "Ảnh 4x6": "02"
            }
        },
        required_aspects=["Danh sách giấy tờ", "Số lượng bản sao"],
        source_procedure="Đăng ký kết hôn (1.013124)"
    )

    # Test Case 2: Timeline query (medium)
    manager.add_test_case(
        test_id="TEST_002",
        category="timeline",
        difficulty="medium",
        question="Thủ tục đăng ký kết hôn mất bao lâu?",
        natural_language_answer="""
Thời gian giải quyết thủ tục đăng ký kết hôn:
- Thời hạn: Trong ngày làm việc
- Trường hợp đặc biệt: Không quá 03 ngày làm việc
        """.strip(),
        key_facts=[
            "Trong ngày làm việc",
            "Trường hợp đặc biệt không quá 03 ngày"
        ],
        structured_data={
            "thoi_han_giai_quyet": "Trong ngày làm việc",
            "thoi_han_dac_biet": "Không quá 03 ngày làm việc",
            "ghi_chu": "Tính từ khi hồ sơ hợp lệ"
        },
        required_aspects=["Thời hạn giải quyết"],
        source_procedure="Đăng ký kết hôn (1.013124)"
    )

    # Test Case 3: Requirements query (medium)
    manager.add_test_case(
        test_id="TEST_003",
        category="requirements",
        difficulty="medium",
        question="Đăng ký kinh doanh cần những điều kiện gì?",
        natural_language_answer="""
Điều kiện để đăng ký kinh doanh:

Đối tượng:
- Công dân Việt Nam từ đủ 18 tuổi trở lên
- Có năng lực hành vi dân sự đầy đủ
- Tổ chức, cá nhân nước ngoài được phép thành lập doanh nghiệp tại Việt Nam

Yêu cầu:
- Tên doanh nghiệp chưa trùng với doanh nghiệp đã đăng ký
- Ngành nghề kinh doanh không thuộc danh mục cấm
- Có địa chỉ trụ sở chính tại Việt Nam
- Có vốn điều lệ phù hợp với quy định pháp luật
        """.strip(),
        key_facts=[
            "Công dân từ 18 tuổi trở lên",
            "Có năng lực hành vi dân sự đầy đủ",
            "Tên doanh nghiệp chưa trùng",
            "Ngành nghề không thuộc danh mục cấm",
            "Có địa chỉ trụ sở tại Việt Nam"
        ],
        structured_data={
            "doi_tuong": "Công dân Việt Nam từ đủ 18 tuổi, có năng lực hành vi dân sự đầy đủ",
            "dieu_kien": [
                "Tên doanh nghiệp chưa trùng",
                "Ngành nghề không thuộc danh mục cấm",
                "Có địa chỉ trụ sở tại Việt Nam",
                "Có vốn điều lệ phù hợp"
            ]
        },
        required_aspects=["Đối tượng", "Điều kiện"],
        source_procedure="Đăng ký kinh doanh lần đầu (1.013145)"
    )

    # Test Case 4: Process query (hard)
    manager.add_test_case(
        test_id="TEST_004",
        category="process",
        difficulty="hard",
        question="Quy trình đăng ký kết hôn như thế nào?",
        natural_language_answer="""
Quy trình đăng ký kết hôn:

Bước 1: Chuẩn bị hồ sơ
- Thu thập các giấy tờ cần thiết
- Làm đơn đăng ký kết hôn theo mẫu

Bước 2: Nộp hồ sơ
- Nộp trực tiếp tại UBND cấp xã nơi một trong hai bên thường trú
- Hoặc nộp qua dịch vụ bưu chính

Bước 3: Tiếp nhận và kiểm tra hồ sơ
- Cán bộ tiếp nhận kiểm tra tính hợp lệ
- Hẹn ngày đăng ký kết hôn

Bước 4: Đăng ký kết hôn
- Hai bên đến cùng ngày hẹn
- Ký xác nhận đăng ký kết hôn

Bước 5: Nhận Giấy chứng nhận kết hôn
- Nhận trong ngày hoặc theo hẹn
        """.strip(),
        key_facts=[
            "Chuẩn bị hồ sơ",
            "Nộp hồ sơ tại UBND cấp xã",
            "Kiểm tra hồ sơ",
            "Hai bên đến ký xác nhận",
            "Nhận Giấy chứng nhận"
        ],
        structured_data={
            "cac_buoc": [
                {"buoc": 1, "mo_ta": "Chuẩn bị hồ sơ"},
                {"buoc": 2, "mo_ta": "Nộp hồ sơ tại UBND cấp xã"},
                {"buoc": 3, "mo_ta": "Tiếp nhận và kiểm tra hồ sơ"},
                {"buoc": 4, "mo_ta": "Đăng ký kết hôn - hai bên ký xác nhận"},
                {"buoc": 5, "mo_ta": "Nhận Giấy chứng nhận kết hôn"}
            ]
        },
        required_aspects=["Các bước thực hiện"],
        source_procedure="Đăng ký kết hôn (1.013124)"
    )

    # Export dataset
    manager.export_dataset("test_dataset_sample.json")

    print("\n" + "=" * 80)
    print("SAMPLE DATASET CREATED")
    print("=" * 80)

    return manager


if __name__ == "__main__":
    create_sample_dataset()
