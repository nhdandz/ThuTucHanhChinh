#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chạy đánh giá đầy đủ trên Comprehensive Test Dataset
"""

import sys
import os
from pathlib import Path

# Add parent directories to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from evaluation.test_dataset import TestDatasetManager
from evaluation.evaluator import RAGEvaluator
from evaluation.metrics import MetricsCalculator

# OPTION 1: Sử dụng RAG Pipeline thật (nếu đã có)
USE_REAL_RAG = True  # Đổi thành True khi đã có RAG pipeline VÀ dữ liệu trong DB

if USE_REAL_RAG:
    # Import RAG pipeline
    from pipeline.rag_pipeline import ThuTucRAGPipeline

    # Khởi tạo pipeline
    rag_pipeline = ThuTucRAGPipeline(
        vector_store_path="../retrieval/qdrant_storage",  # Đường dẫn đến Qdrant DB
        embedding_model="bge-m3",                         # Model embedding
        llm_model="qwen3:8b",                             # Model LLM (không phải model_name!)
        ollama_url="http://localhost:11434"
    )

    def answer_generator_fn(question: str):
        """Hàm tạo câu trả lời từ RAG pipeline thật"""
        import time

        start_time = time.time()

        # Gọi RAG pipeline
        result = rag_pipeline.answer_question(question, verbose=False)

        total_time = time.time() - start_time

        # GeneratedAnswer có các field: answer, structured_data, sources, etc.
        return {
            'answer': result.answer,  # Natural language answer
            'retrieval_time': total_time * 0.6,  # Estimate: 60% retrieval
            'generation_time': total_time * 0.4,  # Estimate: 40% generation
            'chunks_retrieved': len(result.sources)  # Số lượng source chunks
        }

else:
    # OPTION 2: Sử dụng mock answer (cho demo)
    print("⚠️  ĐANG DÙNG MOCK DATA - Đổi USE_REAL_RAG = True để dùng RAG thật")
    print()

    def answer_generator_fn(question: str):
        """Hàm mock - trả về câu trả lời giả"""

        # Mock answers cho một số câu hỏi
        mock_answers = {
            "Đăng ký kết hôn cần giấy tờ gì?": """
Hồ sơ đăng ký kết hôn gồm:
1. Giấy tờ tùy thân (CMND/CCCD/Hộ chiếu) của cả hai bên - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính (đối với người từ 30 tuổi trở lên)
3. Giấy khám sức khỏe tiền hôn nhân - 01 bản chính
4. Đơn đăng ký kết hôn - 01 bản
            """.strip(),

            "Đăng ký kết hôn mất bao lâu?": """
Thời gian giải quyết: Trong ngày làm việc.
Trường hợp đặc biệt: Không quá 03 ngày làm việc.
            """.strip(),

            "Cấp CCCD cần những giấy tờ nào?": """
Hồ sơ cấp CCCD:
1. Giấy khai sinh - 01 bản sao
2. Sổ hộ khẩu hoặc giấy xác nhận cư trú - 01 bản sao
3. Ảnh 4x6 - 02 ảnh
            """.strip()
        }

        # Lấy mock answer hoặc trả về câu trả lời mặc định
        answer = mock_answers.get(
            question,
            "Đây là câu trả lời mock cho câu hỏi: " + question
        )

        return {
            'answer': answer,
            'retrieval_time': 5.0,
            'generation_time': 30.0,
            'chunks_retrieved': 3
        }


def main():
    """Chạy đánh giá đầy đủ"""

    print("=" * 80)
    print("ĐÁNH GIÁ TOÀN DIỆN HỆ THỐNG RAG")
    print("=" * 80)
    print()

    # 1. Load comprehensive test dataset
    print("📂 Đang load test dataset...")
    manager = TestDatasetManager()
    dataset_path = current_dir / "comprehensive_test_dataset.json"
    manager.load_dataset(str(dataset_path))

    print(f"✅ Đã load {len(manager.test_cases)} test cases")
    print()

    # Hiển thị thống kê
    stats = manager.get_statistics()
    print("📊 Thống kê dataset:")
    print(f"   Tổng số: {stats['total_cases']} cases")
    print(f"   Theo category:")
    for cat, count in stats['by_category'].items():
        print(f"      {cat}: {count} cases")
    print(f"   Theo difficulty:")
    for diff, count in stats['by_difficulty'].items():
        print(f"      {diff}: {count} cases")
    print()

    # 2. Khởi tạo evaluator
    print("🔧 Khởi tạo evaluator...")

    # Tạo MetricsCalculator với thresholds
    metrics_calculator = MetricsCalculator(
        accuracy_threshold=0.95,
        precision_threshold=0.90,
        recall_threshold=0.90,
        f1_threshold=0.90,
        hallucination_threshold=0.05
    )

    # Tạo RAGEvaluator với MetricsCalculator
    evaluator = RAGEvaluator(metrics_calculator=metrics_calculator)
    print()

    # 3. Chọn subset để test (bắt đầu với ít cases)
    print("🎯 Chọn test cases để đánh giá:")
    print("   1. Test 5 cases đầu tiên (nhanh)")
    print("   2. Test theo category")
    print("   3. Test theo difficulty")
    print("   4. Test tất cả 54 cases (đầy đủ)")
    print()

    # Mặc định: test 5 cases đầu
    test_mode = input("Chọn mode (1-4, mặc định=1): ").strip() or "1"
    print()

    if test_mode == "1":
        test_cases = manager.test_cases[:5]
        print(f"✅ Đang test 5 cases đầu tiên")
    elif test_mode == "2":
        print("Categories có sẵn:", list(stats['by_category'].keys()))
        category = input("Chọn category: ").strip()
        test_cases = manager.filter_by_category(category)
        print(f"✅ Đang test {len(test_cases)} cases trong category '{category}'")
    elif test_mode == "3":
        print("Difficulties: easy, medium, hard")
        difficulty = input("Chọn difficulty: ").strip()
        test_cases = manager.filter_by_difficulty(difficulty)
        print(f"✅ Đang test {len(test_cases)} cases với difficulty '{difficulty}'")
    else:
        test_cases = manager.test_cases
        print(f"✅ Đang test TẤT CẢ {len(test_cases)} cases")

    print()

    # 4. Chạy evaluation
    print("🧪 Bắt đầu đánh giá...")
    print()

    report = evaluator.evaluate_batch(
        test_cases=test_cases,
        answer_generator_fn=answer_generator_fn,
        verbose=True
    )

    # 5. Hiển thị kết quả
    print()
    print(evaluator.format_evaluation_report(report))

    # 6. Lưu report (optional)
    save_report = input("\nLưu report vào file? (y/n, mặc định=n): ").strip().lower()
    if save_report == 'y':
        report_file = f"evaluation_report_{report.report_id}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(evaluator.format_evaluation_report(report))
        print(f"✅ Đã lưu report: {report_file}")

    print()
    print("=" * 80)
    print("HOÀN THÀNH ĐÁNH GIÁ")
    print("=" * 80)

    # Tóm tắt kết quả
    if report.overall_accuracy >= 0.95:
        print("🎉 HỆ THỐNG ĐẠT MỨC PRODUCTION-READY!")
    elif report.overall_accuracy >= 0.80:
        print("⚠️  Hệ thống cần cải thiện thêm")
    else:
        print("❌ Hệ thống cần điều chỉnh nhiều")

    print(f"\n📊 Kết quả tổng quát:")
    print(f"   Accuracy: {report.overall_accuracy:.2%} (Target: ≥95%)")
    print(f"   Pass Rate: {report.pass_rate:.2%}")
    print(f"   Hallucination: {report.average_hallucination_rate:.2%} (Target: ≤5%)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đánh giá bị hủy bởi user")
    except Exception as e:
        print(f"\n\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
