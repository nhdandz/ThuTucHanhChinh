#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hierarchical Chunking Strategy for Administrative Procedures
Implements 2-tier chunking: Parent (overview) + Child (detailed)
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import tiktoken
from dataclasses import dataclass, asdict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class Chunk:
    """Chunk data structure"""
    chunk_id: str
    thu_tuc_id: str
    chunk_type: str  # parent_overview, child_documents, child_requirements, child_process, child_legal
    chunk_tier: str  # parent or child
    parent_chunk_id: Optional[str]
    content: str
    metadata: Dict
    char_count: int
    token_count: int


class HierarchicalChunker:
    """
    Hierarchical + Semantic Field-Based Chunker
    Creates Parent chunks (overview) and Child chunks (detailed)
    """

    # Chunk parameters from plan
    CHUNK_PARAMS = {
        "parent_overview": {
            "max_tokens": 512,
            "overlap": 0,
            "priority": "always_retrieve"
        },
        "child_documents": {
            "max_tokens": 1024,
            "overlap": 100,
            "preserve_structure": True,
            "separators": ["\n\n", "\nSTT", "\n1.", "\n2."]
        },
        "child_requirements": {
            "max_tokens": 768,
            "overlap": 200,
            "separators": ["\n\nĐiều kiện", "\n\nYêu cầu", "\n-", ". ", "; "]
        },
        "child_process": {
            "max_tokens": 896,
            "overlap": 150,
            "separators": ["\n\nBước", "\nBước", ". "]
        },
        "child_legal": {
            "max_tokens": 512,
            "overlap": 50,
            "separators": ["\n\n", "\n1.", "\n2."]
        }
    }

    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize with tiktoken encoder"""
        self.encoder = tiktoken.get_encoding(encoding_name)
        self.chunks = []

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))

    def chunk_thu_tuc(self, thu_tuc_data: Dict) -> List[Chunk]:
        """
        Main function: Chunk một thủ tục thành parent + child chunks
        """
        thu_tuc_id = thu_tuc_data["thu_tuc_id"]
        chunks = []

        # TIER 1: Create Parent chunk (overview)
        parent_chunk = self._create_parent_chunk(thu_tuc_data)
        chunks.append(parent_chunk)

        # TIER 2: Create Child chunks
        # Child A: Documents (Thành phần hồ sơ)
        docs_chunks = self._create_documents_chunks(thu_tuc_data, parent_chunk.chunk_id)
        chunks.extend(docs_chunks)

        # Child B: Requirements (Yêu cầu & Điều kiện)
        req_chunks = self._create_requirements_chunks(thu_tuc_data, parent_chunk.chunk_id)
        chunks.extend(req_chunks)

        # Child C: Process (Quy trình)
        process_chunks = self._create_process_chunks(thu_tuc_data, parent_chunk.chunk_id)
        chunks.extend(process_chunks)

        # Child D: Legal Basis (Căn cứ pháp lý)
        legal_chunks = self._create_legal_chunks(thu_tuc_data, parent_chunk.chunk_id)
        chunks.extend(legal_chunks)

        return chunks

    def _create_parent_chunk(self, data: Dict) -> Chunk:
        """
        TIER 1: Parent Chunk - Master Overview
        Mục đích: Quick answer, routing đến child chunks
        """
        meta = data["metadata"]
        content_data = data["content"]
        tables = data["tables"]

        # Extract thời gian và phí từ bảng
        thoi_han = ""
        phi_le_phi = ""
        if tables.get("hinh_thuc_nop") and len(tables["hinh_thuc_nop"]) > 0:
            first_form = tables["hinh_thuc_nop"][0]
            thoi_han = first_form.get("thoi_han_giai_quyet", "")
            phi_le_phi = first_form.get("phi_le_phi", "")

        # Build content
        content = f"""THỦ TỤC: {meta.get('tên_thủ_tục', '')}
MÃ: {meta.get('mã_thủ_tục', '')}
LĨNH VỰC: {meta.get('lĩnh_vực', '')}
LOẠI: {meta.get('loại_thủ_tục', '')}
CẤP THỰC HIỆN: {meta.get('cấp_thực_hiện', '')}

TÓM TẮT:
- Đối tượng: {content_data.get('đối_tượng_thực_hiện', 'Không có thông tin')}
- Cơ quan: {content_data.get('cơ_quan_thực_hiện', 'Không có thông tin')}
- Kết quả: {content_data.get('kết_quả_thực_hiện', 'Không có thông tin')}
- Thời gian: {thoi_han}
- Chi phí: {phi_le_phi}

→ Chi tiết về: Giấy tờ cần nộp, Yêu cầu điều kiện, Quy trình thực hiện, Căn cứ pháp lý (xem chunks con)
"""

        chunk_id = f"{data['thu_tuc_id']}_parent_overview"

        chunk = Chunk(
            chunk_id=chunk_id,
            thu_tuc_id=data["thu_tuc_id"],
            chunk_type="parent_overview",
            chunk_tier="parent",
            parent_chunk_id=None,
            content=content.strip(),
            metadata={
                "mã_thủ_tục": meta.get('mã_thủ_tục', ''),
                "tên_thủ_tục": meta.get('tên_thủ_tục', ''),
                "lĩnh_vực": meta.get('lĩnh_vực', ''),
                "loại_thủ_tục": meta.get('loại_thủ_tục', ''),
                "cấp_thực_hiện": meta.get('cấp_thực_hiện', ''),
                "số_quyết_định": meta.get('số_quyết_định', '')
            },
            char_count=len(content),
            token_count=self.count_tokens(content)
        )

        return chunk

    def _create_documents_chunks(self, data: Dict, parent_id: str) -> List[Chunk]:
        """
        Child Type A: Documents (Thành phần hồ sơ)
        Max: 1024 tokens, preserve numbered list structure
        """
        chunks = []
        thanh_phan_ho_so = data["tables"].get("thanh_phan_ho_so", [])

        if not thanh_phan_ho_so or len(thanh_phan_ho_so) == 0:
            return chunks

        # Build parent context (để trong mỗi child chunk)
        parent_context = f"""[PARENT CONTEXT]
Thủ tục: {data['metadata'].get('tên_thủ_tục', '')}
Mã: {data['metadata'].get('mã_thủ_tục', '')}
"""

        # Build documents list
        main_content = "[MAIN CONTENT]\nTHÀNH PHẦN HỒ SƠ CẦN NỘP:\n\n"

        for i, doc in enumerate(thanh_phan_ho_so, 1):
            ten_giay_to = doc.get("ten_giay_to", "")
            so_luong = doc.get("so_luong", "")
            ghi_chu = doc.get("ghi_chu", "")

            doc_text = f"{i}. {ten_giay_to}\n"
            if so_luong:
                doc_text += f"   - Số lượng: {so_luong}\n"
            if ghi_chu:
                doc_text += f"   - Ghi chú: {ghi_chu}\n"
            doc_text += "\n"

            main_content += doc_text

        # Build submission methods
        hinh_thuc_section = "\nCÁCH THỨC NỘP HỒ SƠ:\n"
        hinh_thuc_nop = data["tables"].get("hinh_thuc_nop", [])
        if hinh_thuc_nop:
            for form in hinh_thuc_nop:
                hinh_thuc = form.get("hinh_thuc", "")
                thoi_han = form.get("thoi_han_giai_quyet", "")
                phi = form.get("phi_le_phi", "")
                hinh_thuc_section += f"- {hinh_thuc}: Thời hạn {thoi_han}, {phi}\n"

        dia_chi = data["content"].get("địa_chỉ_tiếp_nhận_hs", "")
        if dia_chi and dia_chi != "Không có thông tin":
            hinh_thuc_section += f"\nĐịa chỉ tiếp nhận: {dia_chi}\n"

        main_content += hinh_thuc_section

        # Check token count
        full_content = parent_context + "\n" + main_content
        token_count = self.count_tokens(full_content)

        # Nếu < 1024 tokens: 1 chunk duy nhất
        if token_count <= self.CHUNK_PARAMS["child_documents"]["max_tokens"]:
            chunk = Chunk(
                chunk_id=f"{data['thu_tuc_id']}_child_documents_0",
                thu_tuc_id=data["thu_tuc_id"],
                chunk_type="child_documents",
                chunk_tier="child",
                parent_chunk_id=parent_id,
                content=full_content.strip(),
                metadata=data["metadata"].copy(),
                char_count=len(full_content),
                token_count=token_count
            )
            chunks.append(chunk)
        else:
            # Nếu > 1024 tokens: Split theo nhóm giấy tờ (5 items/chunk)
            chunk_size = 5
            for i in range(0, len(thanh_phan_ho_so), chunk_size):
                group = thanh_phan_ho_so[i:i+chunk_size]

                group_content = "[MAIN CONTENT]\nTHÀNH PHẦN HỒ SƠ CẦN NỘP:\n\n"
                for j, doc in enumerate(group, i+1):
                    ten_giay_to = doc.get("ten_giay_to", "")
                    so_luong = doc.get("so_luong", "")
                    ghi_chu = doc.get("ghi_chu", "")

                    doc_text = f"{j}. {ten_giay_to}\n"
                    if so_luong:
                        doc_text += f"   - Số lượng: {so_luong}\n"
                    if ghi_chu:
                        doc_text += f"   - Ghi chú: {ghi_chu}\n"
                    doc_text += "\n"

                    group_content += doc_text

                # Add submission info to last chunk
                if i + chunk_size >= len(thanh_phan_ho_so):
                    group_content += hinh_thuc_section

                chunk_content = parent_context + "\n" + group_content

                chunk = Chunk(
                    chunk_id=f"{data['thu_tuc_id']}_child_documents_{i//chunk_size}",
                    thu_tuc_id=data["thu_tuc_id"],
                    chunk_type="child_documents",
                    chunk_tier="child",
                    parent_chunk_id=parent_id,
                    content=chunk_content.strip(),
                    metadata=data["metadata"].copy(),
                    char_count=len(chunk_content),
                    token_count=self.count_tokens(chunk_content)
                )
                chunks.append(chunk)

        return chunks

    def _create_requirements_chunks(self, data: Dict, parent_id: str) -> List[Chunk]:
        """
        Child Type B: Requirements (Yêu cầu & Điều kiện)
        Max: 768 tokens, overlap: 200 tokens
        """
        chunks = []

        yeu_cau = data["content"].get("yêu_cầu_điều_kiện_thực_hiện", "")
        doi_tuong = data["content"].get("đối_tượng_thực_hiện", "")

        # Nếu không có thông tin
        if (not yeu_cau or yeu_cau in ["Không", "Không có thông tin"]) and \
           (not doi_tuong or doi_tuong in ["Không", "Không có thông tin"]):
            return chunks

        # Parent context
        parent_context = f"""[PARENT CONTEXT]
Thủ tục: {data['metadata'].get('tên_thủ_tục', '')}
Mã: {data['metadata'].get('mã_thủ_tục', '')}
"""

        # Main content
        main_content = "[MAIN CONTENT]\n"

        if doi_tuong and doi_tuong not in ["Không", "Không có thông tin"]:
            main_content += f"ĐỐI TƯỢNG ĐƯỢC LÀM THỦ TỤC:\n{doi_tuong}\n\n"

        if yeu_cau and yeu_cau not in ["Không", "Không có thông tin"]:
            main_content += f"YÊU CẦU VÀ ĐIỀU KIỆN:\n{yeu_cau}\n"

        full_content = parent_context + "\n" + main_content
        token_count = self.count_tokens(full_content)

        # Nếu < 768 tokens: 1 chunk
        if token_count <= self.CHUNK_PARAMS["child_requirements"]["max_tokens"]:
            chunk = Chunk(
                chunk_id=f"{data['thu_tuc_id']}_child_requirements_0",
                thu_tuc_id=data["thu_tuc_id"],
                chunk_type="child_requirements",
                chunk_tier="child",
                parent_chunk_id=parent_id,
                content=full_content.strip(),
                metadata=data["metadata"].copy(),
                char_count=len(full_content),
                token_count=token_count
            )
            chunks.append(chunk)
        else:
            # Split với overlap 200 tokens
            chunks_list = self._split_with_overlap(
                text=yeu_cau,
                max_tokens=self.CHUNK_PARAMS["child_requirements"]["max_tokens"],
                overlap_tokens=self.CHUNK_PARAMS["child_requirements"]["overlap"],
                prefix=parent_context + "\n[MAIN CONTENT]\nYÊU CẦU VÀ ĐIỀU KIỆN:\n"
            )

            for i, chunk_text in enumerate(chunks_list):
                chunk = Chunk(
                    chunk_id=f"{data['thu_tuc_id']}_child_requirements_{i}",
                    thu_tuc_id=data["thu_tuc_id"],
                    chunk_type="child_requirements",
                    chunk_tier="child",
                    parent_chunk_id=parent_id,
                    content=chunk_text.strip(),
                    metadata=data["metadata"].copy(),
                    char_count=len(chunk_text),
                    token_count=self.count_tokens(chunk_text)
                )
                chunks.append(chunk)

        return chunks

    def _create_process_chunks(self, data: Dict, parent_id: str) -> List[Chunk]:
        """
        Child Type C: Process (Quy trình & Bước thực hiện)
        Max: 896 tokens, overlap: 150 tokens
        """
        chunks = []

        trinh_tu = data["content"].get("trình_tự_thực_hiện", "")
        cach_thuc = data["content"].get("cách_thức_thực_hiện", "")

        # Nếu không có thông tin
        if (not trinh_tu or trinh_tu in ["", "Không có thông tin"]) and \
           (not cach_thuc or cach_thuc in ["", "Không có thông tin"]):
            return chunks

        # Parent context
        parent_context = f"""[PARENT CONTEXT]
Thủ tục: {data['metadata'].get('tên_thủ_tục', '')}
Mã: {data['metadata'].get('mã_thủ_tục', '')}
"""

        # Main content
        main_content = "[MAIN CONTENT]\n"

        if trinh_tu and trinh_tu not in ["", "Không có thông tin"]:
            main_content += f"TRÌNH TỰ THỰC HIỆN:\n{trinh_tu}\n\n"

        if cach_thuc and cach_thuc not in ["", "Không có thông tin"]:
            main_content += f"CÁCH THỨC THỰC HIỆN:\n{cach_thuc}\n\n"

        # Thời gian và địa điểm
        main_content += "THỜI GIAN VÀ ĐỊA ĐIỂM:\n"

        hinh_thuc_nop = data["tables"].get("hinh_thuc_nop", [])
        if hinh_thuc_nop and len(hinh_thuc_nop) > 0:
            thoi_han = hinh_thuc_nop[0].get("thoi_han_giai_quyet", "")
            phi = hinh_thuc_nop[0].get("phi_le_phi", "")
            main_content += f"- Thời hạn giải quyết: {thoi_han}\n"
            main_content += f"- Phí, lệ phí: {phi}\n"

        dia_chi = data["content"].get("địa_chỉ_tiếp_nhận_hs", "")
        if dia_chi and dia_chi != "Không có thông tin":
            main_content += f"- Địa điểm tiếp nhận: {dia_chi}\n"

        co_quan = data["content"].get("cơ_quan_thực_hiện", "")
        if co_quan:
            main_content += f"- Cơ quan thực hiện: {co_quan}\n"

        full_content = parent_context + "\n" + main_content
        token_count = self.count_tokens(full_content)

        # Nếu < 896 tokens: 1 chunk
        if token_count <= self.CHUNK_PARAMS["child_process"]["max_tokens"]:
            chunk = Chunk(
                chunk_id=f"{data['thu_tuc_id']}_child_process_0",
                thu_tuc_id=data["thu_tuc_id"],
                chunk_type="child_process",
                chunk_tier="child",
                parent_chunk_id=parent_id,
                content=full_content.strip(),
                metadata=data["metadata"].copy(),
                char_count=len(full_content),
                token_count=token_count
            )
            chunks.append(chunk)
        else:
            # Split với overlap 150 tokens
            combined_text = ""
            if trinh_tu:
                combined_text += f"TRÌNH TỰ THỰC HIỆN:\n{trinh_tu}\n\n"
            if cach_thuc:
                combined_text += f"CÁCH THỨC THỰC HIỆN:\n{cach_thuc}\n"

            chunks_list = self._split_with_overlap(
                text=combined_text,
                max_tokens=self.CHUNK_PARAMS["child_process"]["max_tokens"],
                overlap_tokens=self.CHUNK_PARAMS["child_process"]["overlap"],
                prefix=parent_context + "\n[MAIN CONTENT]\n"
            )

            for i, chunk_text in enumerate(chunks_list):
                chunk = Chunk(
                    chunk_id=f"{data['thu_tuc_id']}_child_process_{i}",
                    thu_tuc_id=data["thu_tuc_id"],
                    chunk_type="child_process",
                    chunk_tier="child",
                    parent_chunk_id=parent_id,
                    content=chunk_text.strip(),
                    metadata=data["metadata"].copy(),
                    char_count=len(chunk_text),
                    token_count=self.count_tokens(chunk_text)
                )
                chunks.append(chunk)

        return chunks

    def _create_legal_chunks(self, data: Dict, parent_id: str) -> List[Chunk]:
        """
        Child Type D: Legal Basis (Căn cứ pháp lý)
        Max: 512 tokens, overlap: 50 tokens
        """
        chunks = []
        can_cu_phap_ly = data["tables"].get("can_cu_phap_ly", [])

        if not can_cu_phap_ly or len(can_cu_phap_ly) == 0:
            return chunks

        # Parent context
        parent_context = f"""[PARENT CONTEXT]
Thủ tục: {data['metadata'].get('tên_thủ_tục', '')}
Mã: {data['metadata'].get('mã_thủ_tục', '')}
"""

        # Build legal basis list
        main_content = "[MAIN CONTENT]\nCĂN CỨ PHÁP LÝ:\n\n"

        for i, legal in enumerate(can_cu_phap_ly, 1):
            so_ky_hieu = legal.get("so_ky_hieu", "")
            trich_yeu = legal.get("trich_yeu", "")

            legal_text = f"{i}. {so_ky_hieu}\n"
            if trich_yeu:
                legal_text += f"   Trích yếu: {trich_yeu}\n"
            legal_text += "\n"

            main_content += legal_text

        full_content = parent_context + "\n" + main_content
        token_count = self.count_tokens(full_content)

        # Nếu < 512 tokens: 1 chunk
        if token_count <= self.CHUNK_PARAMS["child_legal"]["max_tokens"]:
            chunk = Chunk(
                chunk_id=f"{data['thu_tuc_id']}_child_legal_0",
                thu_tuc_id=data["thu_tuc_id"],
                chunk_type="child_legal",
                chunk_tier="child",
                parent_chunk_id=parent_id,
                content=full_content.strip(),
                metadata=data["metadata"].copy(),
                char_count=len(full_content),
                token_count=token_count
            )
            chunks.append(chunk)
        else:
            # Split theo nhóm văn bản (5 items/chunk)
            chunk_size = 5
            for i in range(0, len(can_cu_phap_ly), chunk_size):
                group = can_cu_phap_ly[i:i+chunk_size]

                group_content = "[MAIN CONTENT]\nCĂN CỨ PHÁP LÝ:\n\n"
                for j, legal in enumerate(group, i+1):
                    so_ky_hieu = legal.get("so_ky_hieu", "")
                    trich_yeu = legal.get("trich_yeu", "")

                    legal_text = f"{j}. {so_ky_hieu}\n"
                    if trich_yeu:
                        legal_text += f"   Trích yếu: {trich_yeu}\n"
                    legal_text += "\n"

                    group_content += legal_text

                chunk_content = parent_context + "\n" + group_content

                chunk = Chunk(
                    chunk_id=f"{data['thu_tuc_id']}_child_legal_{i//chunk_size}",
                    thu_tuc_id=data["thu_tuc_id"],
                    chunk_type="child_legal",
                    chunk_tier="child",
                    parent_chunk_id=parent_id,
                    content=chunk_content.strip(),
                    metadata=data["metadata"].copy(),
                    char_count=len(chunk_content),
                    token_count=self.count_tokens(chunk_content)
                )
                chunks.append(chunk)

        return chunks

    def _split_with_overlap(self, text: str, max_tokens: int, overlap_tokens: int, prefix: str = "") -> List[str]:
        """
        Split text into chunks với overlap
        """
        # Encode full text
        tokens = self.encoder.encode(text)

        # Account for prefix tokens
        prefix_tokens = self.encoder.encode(prefix) if prefix else []
        available_tokens = max_tokens - len(prefix_tokens)

        chunks = []
        start = 0

        while start < len(tokens):
            # Get chunk
            end = min(start + available_tokens, len(tokens))
            chunk_tokens = tokens[start:end]

            # Decode
            chunk_text = self.encoder.decode(chunk_tokens)

            # Add prefix
            full_chunk = prefix + chunk_text if prefix else chunk_text
            chunks.append(full_chunk)

            # Move start với overlap
            if end >= len(tokens):
                break
            start = end - overlap_tokens

        return chunks

    def chunk_all_files(self, input_dir: Path, output_dir: Path):
        """
        Chunk tất cả JSON files trong directory
        """
        json_files = list(input_dir.glob("*.json"))

        print(f"🔄 Bắt đầu chunking {len(json_files)} files...")
        print()

        all_chunks = []
        total_chunks_count = 0

        for i, file_path in enumerate(json_files, 1):
            print(f"\r⏳ Chunking: {i}/{len(json_files)}", end='', flush=True)

            # Load JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Chunk
            chunks = self.chunk_thu_tuc(data)
            all_chunks.extend(chunks)
            total_chunks_count += len(chunks)

        print("\n")

        # Save all chunks to JSON
        output_dir.mkdir(parents=True, exist_ok=True)
        chunks_file = output_dir / "all_chunks.json"

        # Convert chunks to dict
        chunks_dict = [asdict(chunk) for chunk in all_chunks]

        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_dict, f, ensure_ascii=False, indent=2)

        print("=" * 80)
        print("KẾT QUẢ CHUNKING")
        print("=" * 80)
        print(f"📊 Tổng số thủ tục: {len(json_files)}")
        print(f"📦 Tổng số chunks: {total_chunks_count}")
        print(f"   - Parent chunks: {sum(1 for c in all_chunks if c.chunk_tier == 'parent')}")
        print(f"   - Child chunks: {sum(1 for c in all_chunks if c.chunk_tier == 'child')}")
        print()
        print(f"Chi tiết child chunks:")
        print(f"   - Documents: {sum(1 for c in all_chunks if c.chunk_type == 'child_documents')}")
        print(f"   - Requirements: {sum(1 for c in all_chunks if c.chunk_type == 'child_requirements')}")
        print(f"   - Process: {sum(1 for c in all_chunks if c.chunk_type == 'child_process')}")
        print(f"   - Legal: {sum(1 for c in all_chunks if c.chunk_type == 'child_legal')}")
        print()
        print(f"💾 Chunks đã lưu tại: {chunks_file}")
        print("=" * 80)

        # Generate statistics
        self._generate_chunking_stats(all_chunks, output_dir)

        return all_chunks

    def _generate_chunking_stats(self, chunks: List[Chunk], output_dir: Path):
        """Generate chunking statistics"""
        stats = {
            "total_chunks": len(chunks),
            "by_tier": {},
            "by_type": {},
            "token_stats": {
                "min": min(c.token_count for c in chunks),
                "max": max(c.token_count for c in chunks),
                "avg": sum(c.token_count for c in chunks) / len(chunks)
            }
        }

        # By tier
        for tier in ["parent", "child"]:
            tier_chunks = [c for c in chunks if c.chunk_tier == tier]
            stats["by_tier"][tier] = {
                "count": len(tier_chunks),
                "avg_tokens": sum(c.token_count for c in tier_chunks) / len(tier_chunks) if tier_chunks else 0
            }

        # By type
        chunk_types = set(c.chunk_type for c in chunks)
        for chunk_type in chunk_types:
            type_chunks = [c for c in chunks if c.chunk_type == chunk_type]
            stats["by_type"][chunk_type] = {
                "count": len(type_chunks),
                "avg_tokens": sum(c.token_count for c in type_chunks) / len(type_chunks) if type_chunks else 0,
                "max_tokens": max(c.token_count for c in type_chunks) if type_chunks else 0
            }

        # Save stats
        stats_file = output_dir / "chunking_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"📈 Statistics saved: {stats_file}")


def main():
    """Main function"""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_dir = project_root / "data"
    extracted_dir = data_dir / "extracted"
    chunks_dir = data_dir / "chunks"

    if not extracted_dir.exists():
        print(f"❌ Không tìm thấy thư mục extracted: {extracted_dir}")
        print("   Hãy chạy extract_documents.py trước!")
        return

    # Create chunker
    chunker = HierarchicalChunker()

    # Chunk all files
    chunks = chunker.chunk_all_files(extracted_dir, chunks_dir)

    return chunks


if __name__ == "__main__":
    main()
