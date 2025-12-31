#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để validate dữ liệu đã extract từ file .doc
Đảm bảo chất lượng dữ liệu trước khi chunking
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class DataValidator:
    """Validator cho dữ liệu thủ tục hành chính"""

    # Các trường bắt buộc phải có
    REQUIRED_METADATA_FIELDS = ["ma_thu_tuc", "ten_thu_tuc", "linh_vuc"]
    REQUIRED_CONTENT_FIELDS = ["doi_tuong_thuc_hien", "co_quan_thuc_hien"]

    def __init__(self):
        self.validation_results = []
        self.issues = []

    def validate_json_structure(self, data: Dict, file_id: str) -> bool:
        """Kiểm tra cấu trúc JSON cơ bản"""
        issues = []

        # Check required top-level keys
        required_keys = ["thu_tuc_id", "metadata", "content", "tables"]
        for key in required_keys:
            if key not in data:
                issues.append(f"Missing key: {key}")

        if issues:
            self.issues.append({"file_id": file_id, "type": "structure", "issues": issues})
            return False

        return True

    def validate_metadata(self, data: Dict, file_id: str) -> Tuple[bool, List[str]]:
        """Kiểm tra metadata fields"""
        issues = []
        metadata = data.get("metadata", {})

        # Check required fields
        for field in self.REQUIRED_METADATA_FIELDS:
            if not metadata.get(field) or metadata.get(field).strip() == "":
                issues.append(f"Empty required metadata: {field}")

        # Check field lengths
        if metadata.get("ten_thu_tuc"):
            length = len(metadata["ten_thu_tuc"])
            if length < 10:
                issues.append(f"Tên thủ tục quá ngắn ({length} chars)")
            elif length > 500:
                issues.append(f"Tên thủ tục quá dài ({length} chars)")

        if issues:
            self.issues.append({"file_id": file_id, "type": "metadata", "issues": issues})
            return False, issues

        return True, []

    def validate_content(self, data: Dict, file_id: str) -> Tuple[bool, List[str]]:
        """Kiểm tra content fields"""
        issues = []
        content = data.get("content", {})

        # Check required fields
        for field in self.REQUIRED_CONTENT_FIELDS:
            if not content.get(field) or content.get(field).strip() == "":
                issues.append(f"Empty required content: {field}")

        # Check important fields có dữ liệu
        important_fields = [
            "yeu_cau_dieu_kien_thuc_hien",
            "trinh_tu_thuc_hien",
            "cach_thuc_thuc_hien"
        ]

        empty_important = []
        for field in important_fields:
            if not content.get(field) or content.get(field).strip() == "":
                empty_important.append(field)

        if len(empty_important) >= 2:
            issues.append(f"Nhiều trường quan trọng trống: {', '.join(empty_important)}")

        if issues:
            self.issues.append({"file_id": file_id, "type": "content", "issues": issues})
            return False, issues

        return True, []

    def validate_tables(self, data: Dict, file_id: str) -> Tuple[bool, List[str]]:
        """Kiểm tra dữ liệu bảng"""
        issues = []
        tables = data.get("tables", {})

        # Check thành phần hồ sơ
        thanh_phan_ho_so = tables.get("thanh_phan_ho_so", [])
        if not thanh_phan_ho_so or len(thanh_phan_ho_so) == 0:
            issues.append("Không có thành phần hồ sơ")
        else:
            # Check structure của từng item
            for i, item in enumerate(thanh_phan_ho_so):
                if not isinstance(item, dict):
                    issues.append(f"Thành phần hồ sơ item {i} không phải dict")
                elif not item.get("ten_giay_to"):
                    issues.append(f"Thành phần hồ sơ item {i} thiếu tên giấy tờ")

        # Check căn cứ pháp lý
        can_cu_phap_ly = tables.get("can_cu_phap_ly", [])
        if not can_cu_phap_ly or len(can_cu_phap_ly) == 0:
            issues.append("Không có căn cứ pháp lý")

        # Warning nếu không có hình thức nộp (không phải lỗi critical)
        hinh_thuc_nop = tables.get("hinh_thuc_nop", [])
        if not hinh_thuc_nop or len(hinh_thuc_nop) == 0:
            # Không thêm vào issues vì một số thủ tục có thể không có
            pass

        if issues:
            self.issues.append({"file_id": file_id, "type": "tables", "issues": issues})
            return False, issues

        return True, []

    def validate_file(self, file_path: Path) -> Dict:
        """Validate một file JSON"""
        file_id = file_path.stem

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            result = {
                "file_id": file_id,
                "file_path": str(file_path),
                "valid": True,
                "issues": []
            }

            # Validate structure
            if not self.validate_json_structure(data, file_id):
                result["valid"] = False

            # Validate metadata
            valid_metadata, metadata_issues = self.validate_metadata(data, file_id)
            if not valid_metadata:
                result["valid"] = False
                result["issues"].extend(metadata_issues)

            # Validate content
            valid_content, content_issues = self.validate_content(data, file_id)
            if not valid_content:
                result["valid"] = False
                result["issues"].extend(content_issues)

            # Validate tables
            valid_tables, table_issues = self.validate_tables(data, file_id)
            if not valid_tables:
                result["valid"] = False
                result["issues"].extend(table_issues)

            return result

        except json.JSONDecodeError as e:
            return {
                "file_id": file_id,
                "file_path": str(file_path),
                "valid": False,
                "issues": [f"JSON decode error: {str(e)}"]
            }
        except Exception as e:
            return {
                "file_id": file_id,
                "file_path": str(file_path),
                "valid": False,
                "issues": [f"Error: {str(e)}"]
            }

    def validate_all(self, json_dir: Path) -> Dict:
        """Validate tất cả files trong directory"""
        json_files = list(json_dir.glob("*.json"))

        print(f"🔍 Bắt đầu validate {len(json_files)} files...")
        print()

        valid_count = 0
        invalid_count = 0

        for i, file_path in enumerate(json_files, 1):
            print(f"\r⏳ Validating: {i}/{len(json_files)}", end='', flush=True)

            result = self.validate_file(file_path)
            self.validation_results.append(result)

            if result["valid"]:
                valid_count += 1
            else:
                invalid_count += 1

        print("\n")

        # Tạo summary
        summary = {
            "total_files": len(json_files),
            "valid_files": valid_count,
            "invalid_files": invalid_count,
            "validation_rate": valid_count / len(json_files) * 100 if json_files else 0
        }

        return summary

    def generate_report(self, output_path: Path):
        """Tạo báo cáo validation chi tiết"""
        print("=" * 80)
        print("KẾT QUẢ VALIDATION")
        print("=" * 80)
        print()

        # Tổng quan
        valid_count = sum(1 for r in self.validation_results if r["valid"])
        total_count = len(self.validation_results)

        print(f"📊 Tổng số files: {total_count}")
        print(f"✅ Files hợp lệ: {valid_count} ({valid_count/total_count*100:.1f}%)")
        print(f"❌ Files có vấn đề: {total_count - valid_count} ({(total_count-valid_count)/total_count*100:.1f}%)")
        print()

        # Files có vấn đề
        invalid_files = [r for r in self.validation_results if not r["valid"]]

        if invalid_files:
            print("=" * 80)
            print("FILES CÓ VẤN ĐỀ")
            print("=" * 80)

            # Nhóm theo loại vấn đề
            issue_types = {}
            for r in invalid_files:
                for issue in r["issues"]:
                    issue_type = issue.split(":")[0]
                    if issue_type not in issue_types:
                        issue_types[issue_type] = []
                    issue_types[issue_type].append(r["file_id"])

            for issue_type, file_ids in sorted(issue_types.items()):
                print(f"\n📌 {issue_type}: {len(file_ids)} files")
                for fid in file_ids[:5]:  # Hiển thị max 5
                    print(f"   - {fid}")
                if len(file_ids) > 5:
                    print(f"   ... và {len(file_ids) - 5} files khác")

        # Lưu detailed report
        print()
        print(f"💾 Lưu báo cáo chi tiết...")

        # Save validation results to JSON
        report_json = output_path / "validation_report.json"
        with open(report_json, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_files": total_count,
                    "valid_files": valid_count,
                    "invalid_files": total_count - valid_count
                },
                "details": self.validation_results,
                "issues": self.issues
            }, f, ensure_ascii=False, indent=2)

        print(f"   ✓ JSON report: {report_json}")

        # Save to CSV for easy viewing
        df = pd.DataFrame(self.validation_results)
        report_csv = output_path / "validation_report.csv"
        df.to_csv(report_csv, index=False, encoding='utf-8-sig')
        print(f"   ✓ CSV report: {report_csv}")

        print()
        print("=" * 80)


def main():
    """Main function"""
    # Tìm đường dẫn
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_dir = project_root / "data"
    extracted_dir = data_dir / "extracted"

    if not extracted_dir.exists():
        print(f"❌ Không tìm thấy thư mục extracted: {extracted_dir}")
        print("   Hãy chạy extract_documents.py trước!")
        return

    # Create validator và run
    validator = DataValidator()
    summary = validator.validate_all(extracted_dir)

    # Generate report
    validator.generate_report(data_dir)

    # Return summary
    return summary


if __name__ == "__main__":
    main()
