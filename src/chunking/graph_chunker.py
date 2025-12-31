#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced Graph-Based Hierarchical Chunking Strategy for Administrative Procedures
Extends HierarchicalChunker with:
- Enriched chunk fields (parent_context, breadcrumb, importance_score)
- Graph relationships (sibling_chunk_ids, related_procedure_ids)
- Two new chunk types: child_fees_timing, child_agencies
- Complete information preservation from source documents

CRITICAL: All 20 fields from source .doc files must be preserved in chunks
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import tiktoken
from dataclasses import dataclass, asdict, field

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class EnrichedChunk:
    """
    Enhanced Chunk data structure with graph relationships and enriched context

    IMPORTANT: All fields from original Chunk class preserved for backward compatibility
    New fields added for graph-based enrichment and improved retrieval
    """
    # ===== CORE FIELDS (REQUIRED) =====
    chunk_id: str
    thu_tuc_id: str
    chunk_type: str  # parent_overview, child_documents, child_requirements, child_process, child_legal, child_fees_timing, child_agencies
    chunk_tier: str  # parent or child
    parent_chunk_id: Optional[str]
    content: str
    metadata: Dict
    char_count: int
    token_count: int

    # ===== NEW ENRICHED FIELDS (WITH DEFAULTS) =====
    # Graph relationships for sibling enrichment
    sibling_chunk_ids: List[str] = field(default_factory=list)  # Other chunks from same procedure
    related_procedure_ids: List[str] = field(default_factory=list)  # Related procedures (same lĩnh vực, similar)

    # Enriched context for better embeddings
    parent_context: str = ""  # First 200 chars of parent chunk for context
    breadcrumb: str = ""  # "Lĩnh vực > Procedure name > Section"

    # Metadata for scoring and filtering
    importance_score: float = 0.5  # 0-1, based on chunk type and content
    complexity_level: str = "medium"  # "simple", "medium", "complex"


class GraphChunker:
    """
    Enhanced Hierarchical + Graph-Based Chunker

    Creates:
    - 1 Parent chunk (overview of all 20 fields)
    - 6 Child chunk types:
      1. child_documents (Thành phần hồ sơ)
      2. child_requirements (Yêu cầu & Điều kiện)
      3. child_process (Trình tự & Cách thức thực hiện)
      4. child_legal (Căn cứ pháp lý)
      5. child_fees_timing (NEW: Phí lệ phí + Thời hạn + Hình thức nộp - ALL items)
      6. child_agencies (NEW: Tất cả cơ quan + địa chỉ)

    Enriches all chunks with:
    - Parent context (first 200 chars)
    - Breadcrumb path (Lĩnh vực > Procedure > Section)
    - Sibling chunk IDs
    - Importance score
    """

    # Chunk parameters (existing + new)
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
        },
        # NEW CHUNK TYPES
        "child_fees_timing": {
            "max_tokens": 512,
            "overlap": 0,
            "preserve_structure": True
        },
        "child_agencies": {
            "max_tokens": 640,
            "overlap": 0,
            "preserve_structure": True
        }
    }

    # Importance scoring by chunk type
    CHUNK_IMPORTANCE = {
        "parent_overview": 1.0,  # Highest - always needed
        "child_documents": 0.9,  # Very high - required docs
        "child_requirements": 0.85,  # High - eligibility
        "child_process": 0.8,  # High - how to do it
        "child_fees_timing": 0.75,  # Medium-high - cost & time
        "child_agencies": 0.7,  # Medium - where to go
        "child_legal": 0.6  # Medium - legal references
    }

    def __init__(self, encoding_name: str = "cl100k_base", procedure_graph=None):
        """
        Initialize with tiktoken encoder

        Args:
            encoding_name: Tokenizer encoding name
            procedure_graph: Optional ProcedureGraph for relationship enrichment
        """
        self.encoder = tiktoken.get_encoding(encoding_name)
        self.chunks = []
        self.procedure_graph = procedure_graph

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))

    def chunk_thu_tuc(self, thu_tuc_data: Dict) -> List[EnrichedChunk]:
        """
        Main function: Chunk một thủ tục thành parent + enriched child chunks

        IMPORTANT: Preserves ALL information from source data
        """
        thu_tuc_id = thu_tuc_data["thu_tuc_id"]
        chunks = []

        # TIER 1: Create Parent chunk (overview of ALL 20 fields)
        parent_chunk = self._create_parent_chunk(thu_tuc_data)
        chunks.append(parent_chunk)

        # TIER 2: Create Child chunks (existing + new types)
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

        # NEW: Child E: Fees & Timing (Phí lệ phí + Thời hạn + Hình thức nộp)
        fees_chunks = self._create_fees_timing_chunks(thu_tuc_data, parent_chunk.chunk_id)
        chunks.extend(fees_chunks)

        # NEW: Child F: Agencies (Tất cả cơ quan + địa chỉ)
        agency_chunks = self._create_agencies_chunks(thu_tuc_data, parent_chunk.chunk_id)
        chunks.extend(agency_chunks)

        # ENRICHMENT: Add parent context, breadcrumbs, sibling IDs, importance scores
        enriched_chunks = self._enrich_all_chunks(chunks, parent_chunk, thu_tuc_data)

        return enriched_chunks

    def _create_parent_chunk(self, data: Dict) -> EnrichedChunk:
        """
        TIER 1: Parent Chunk - Master Overview of ALL 20 fields

        IMPORTANT: This chunk summarizes ALL information from the procedure
        """
        meta = data["metadata"]
        content_data = data["content"]
        tables = data["tables"]

        # Extract timing & fees from table
        thoi_han = ""
        phi_le_phi = ""
        if tables.get("hinh_thuc_nop") and len(tables["hinh_thuc_nop"]) > 0:
            first_form = tables["hinh_thuc_nop"][0]
            thoi_han = first_form.get("thoi_han_giai_quyet", "")
            phi_le_phi = first_form.get("phi_le_phi", "")

        # Build comprehensive content covering all 20 fields
        content = f"""THỦ TỤC: {meta.get('tên_thủ_tục', '')}
MÃ: {meta.get('mã_thủ_tục', '')}
LĨNH VỰC: {meta.get('lĩnh_vực', '')}
LOẠI: {meta.get('loại_thủ_tục', '')}
CẤP THỰC HIỆN: {meta.get('cấp_thực_hiện', '')}
SỐ QUYẾT ĐỊNH: {meta.get('số_quyết_định', '')}

TÓM TẮT:
- Đối tượng: {content_data.get('đối_tượng_thực_hiện', 'Không có thông tin')}
- Cơ quan thực hiện: {content_data.get('cơ_quan_thực_hiện', 'Không có thông tin')}
- Cơ quan thẩm quyền: {content_data.get('cơ_quan_có_thẩm_quyền', 'Không có thông tin')}
- Kết quả: {content_data.get('kết_quả_thực_hiện', 'Không có thông tin')}
- Thời gian: {thoi_han}
- Chi phí: {phi_le_phi}

→ Chi tiết về: Giấy tờ cần nộp, Yêu cầu điều kiện, Quy trình thực hiện, Phí & thời gian, Cơ quan, Căn cứ pháp lý (xem chunks con)
"""

        chunk_id = f"{data['thu_tuc_id']}_parent_overview"

        chunk = EnrichedChunk(
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
            token_count=self.count_tokens(content),
            importance_score=self.CHUNK_IMPORTANCE["parent_overview"]
        )

        return chunk

    # ========== EXISTING CHUNK METHODS (PRESERVED) ==========
    # Keep all existing logic intact for backward compatibility

    def _create_documents_chunks(self, data: Dict, parent_id: str) -> List[EnrichedChunk]:
        """
        Child Type A: Documents (Thành phần hồ sơ)

        PRESERVED: Original logic maintained
        """
        chunks = []
        thanh_phan_ho_so = data["tables"].get("thanh_phan_ho_so", [])

        if not thanh_phan_ho_so or len(thanh_phan_ho_so) == 0:
            return chunks

        # Build parent context
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

        # If < 1024 tokens: single chunk
        if token_count <= self.CHUNK_PARAMS["child_documents"]["max_tokens"]:
            chunk = EnrichedChunk(
                chunk_id=f"{data['thu_tuc_id']}_child_documents_0",
                thu_tuc_id=data["thu_tuc_id"],
                chunk_type="child_documents",
                chunk_tier="child",
                parent_chunk_id=parent_id,
                content=full_content.strip(),
                metadata=data["metadata"].copy(),
                char_count=len(full_content),
                token_count=token_count,
                importance_score=self.CHUNK_IMPORTANCE["child_documents"]
            )
            chunks.append(chunk)
        else:
            # Split into groups of 5 documents
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

                chunk = EnrichedChunk(
                    chunk_id=f"{data['thu_tuc_id']}_child_documents_{i//chunk_size}",
                    thu_tuc_id=data["thu_tuc_id"],
                    chunk_type="child_documents",
                    chunk_tier="child",
                    parent_chunk_id=parent_id,
                    content=chunk_content.strip(),
                    metadata=data["metadata"].copy(),
                    char_count=len(chunk_content),
                    token_count=self.count_tokens(chunk_content),
                    importance_score=self.CHUNK_IMPORTANCE["child_documents"]
                )
                chunks.append(chunk)

        return chunks

    def _create_requirements_chunks(self, data: Dict, parent_id: str) -> List[EnrichedChunk]:
        """
        Child Type B: Requirements (Yêu cầu & Điều kiện)

        PRESERVED: Original logic maintained
        """
        chunks = []

        yeu_cau = data["content"].get("yêu_cầu_điều_kiện_thực_hiện", "")
        doi_tuong = data["content"].get("đối_tượng_thực_hiện", "")

        # If no information
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

        # If < 768 tokens: single chunk
        if token_count <= self.CHUNK_PARAMS["child_requirements"]["max_tokens"]:
            chunk = EnrichedChunk(
                chunk_id=f"{data['thu_tuc_id']}_child_requirements_0",
                thu_tuc_id=data["thu_tuc_id"],
                chunk_type="child_requirements",
                chunk_tier="child",
                parent_chunk_id=parent_id,
                content=full_content.strip(),
                metadata=data["metadata"].copy(),
                char_count=len(full_content),
                token_count=token_count,
                importance_score=self.CHUNK_IMPORTANCE["child_requirements"]
            )
            chunks.append(chunk)
        else:
            # Split with overlap
            chunks_list = self._split_with_overlap(
                text=yeu_cau,
                max_tokens=self.CHUNK_PARAMS["child_requirements"]["max_tokens"],
                overlap_tokens=self.CHUNK_PARAMS["child_requirements"]["overlap"],
                prefix=parent_context + "\n[MAIN CONTENT]\nYÊU CẦU VÀ ĐIỀU KIỆN:\n"
            )

            for i, chunk_text in enumerate(chunks_list):
                chunk = EnrichedChunk(
                    chunk_id=f"{data['thu_tuc_id']}_child_requirements_{i}",
                    thu_tuc_id=data["thu_tuc_id"],
                    chunk_type="child_requirements",
                    chunk_tier="child",
                    parent_chunk_id=parent_id,
                    content=chunk_text.strip(),
                    metadata=data["metadata"].copy(),
                    char_count=len(chunk_text),
                    token_count=self.count_tokens(chunk_text),
                    importance_score=self.CHUNK_IMPORTANCE["child_requirements"]
                )
                chunks.append(chunk)

        return chunks

    def _create_process_chunks(self, data: Dict, parent_id: str) -> List[EnrichedChunk]:
        """
        Child Type C: Process (Quy trình & Bước thực hiện)

        PRESERVED: Original logic maintained
        IMPORTANT: Preserves both trình_tự_thực_hiện AND cách_thức_thực_hiện
        """
        chunks = []

        trinh_tu = data["content"].get("trình_tự_thực_hiện", "")
        cach_thuc = data["content"].get("cách_thức_thực_hiện", "")

        # If no information
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

        # Time and location
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

        # If < 896 tokens: single chunk
        if token_count <= self.CHUNK_PARAMS["child_process"]["max_tokens"]:
            chunk = EnrichedChunk(
                chunk_id=f"{data['thu_tuc_id']}_child_process_0",
                thu_tuc_id=data["thu_tuc_id"],
                chunk_type="child_process",
                chunk_tier="child",
                parent_chunk_id=parent_id,
                content=full_content.strip(),
                metadata=data["metadata"].copy(),
                char_count=len(full_content),
                token_count=token_count,
                importance_score=self.CHUNK_IMPORTANCE["child_process"]
            )
            chunks.append(chunk)
        else:
            # Split with overlap
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
                chunk = EnrichedChunk(
                    chunk_id=f"{data['thu_tuc_id']}_child_process_{i}",
                    thu_tuc_id=data["thu_tuc_id"],
                    chunk_type="child_process",
                    chunk_tier="child",
                    parent_chunk_id=parent_id,
                    content=chunk_text.strip(),
                    metadata=data["metadata"].copy(),
                    char_count=len(chunk_text),
                    token_count=self.count_tokens(chunk_text),
                    importance_score=self.CHUNK_IMPORTANCE["child_process"]
                )
                chunks.append(chunk)

        return chunks

    def _create_legal_chunks(self, data: Dict, parent_id: str) -> List[EnrichedChunk]:
        """
        Child Type D: Legal Basis (Căn cứ pháp lý)

        PRESERVED: Original logic maintained
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
            ngay_ban_hanh = legal.get("ngay_ban_hanh", "")  # FIXED: Add date
            co_quan_ban_hanh = legal.get("co_quan_ban_hanh", "")  # FIXED: Add issuing agency

            legal_text = f"{i}. {so_ky_hieu}\n"
            if trich_yeu:
                legal_text += f"   Trích yếu: {trich_yeu}\n"
            if ngay_ban_hanh:  # FIXED: Include date
                legal_text += f"   Ngày ban hành: {ngay_ban_hanh}\n"
            if co_quan_ban_hanh:  # FIXED: Include issuing agency
                legal_text += f"   Cơ quan ban hành: {co_quan_ban_hanh}\n"
            legal_text += "\n"

            main_content += legal_text

        full_content = parent_context + "\n" + main_content
        token_count = self.count_tokens(full_content)

        # If < 512 tokens: single chunk
        if token_count <= self.CHUNK_PARAMS["child_legal"]["max_tokens"]:
            chunk = EnrichedChunk(
                chunk_id=f"{data['thu_tuc_id']}_child_legal_0",
                thu_tuc_id=data["thu_tuc_id"],
                chunk_type="child_legal",
                chunk_tier="child",
                parent_chunk_id=parent_id,
                content=full_content.strip(),
                metadata=data["metadata"].copy(),
                char_count=len(full_content),
                token_count=token_count,
                importance_score=self.CHUNK_IMPORTANCE["child_legal"]
            )
            chunks.append(chunk)
        else:
            # Split into groups of 5 legal documents
            chunk_size = 5
            for i in range(0, len(can_cu_phap_ly), chunk_size):
                group = can_cu_phap_ly[i:i+chunk_size]

                group_content = "[MAIN CONTENT]\nCĂN CỨ PHÁP LÝ:\n\n"
                for j, legal in enumerate(group, i+1):
                    so_ky_hieu = legal.get("so_ky_hieu", "")
                    trich_yeu = legal.get("trich_yeu", "")
                    ngay_ban_hanh = legal.get("ngay_ban_hanh", "")  # FIXED: Add date
                    co_quan_ban_hanh = legal.get("co_quan_ban_hanh", "")  # FIXED: Add issuing agency

                    legal_text = f"{j}. {so_ky_hieu}\n"
                    if trich_yeu:
                        legal_text += f"   Trích yếu: {trich_yeu}\n"
                    if ngay_ban_hanh:  # FIXED: Include date
                        legal_text += f"   Ngày ban hành: {ngay_ban_hanh}\n"
                    if co_quan_ban_hanh:  # FIXED: Include issuing agency
                        legal_text += f"   Cơ quan ban hành: {co_quan_ban_hanh}\n"
                    legal_text += "\n"

                    group_content += legal_text

                chunk_content = parent_context + "\n" + group_content

                chunk = EnrichedChunk(
                    chunk_id=f"{data['thu_tuc_id']}_child_legal_{i//chunk_size}",
                    thu_tuc_id=data["thu_tuc_id"],
                    chunk_type="child_legal",
                    chunk_tier="child",
                    parent_chunk_id=parent_id,
                    content=chunk_content.strip(),
                    metadata=data["metadata"].copy(),
                    char_count=len(chunk_content),
                    token_count=self.count_tokens(chunk_content),
                    importance_score=self.CHUNK_IMPORTANCE["child_legal"]
                )
                chunks.append(chunk)

        return chunks

    # ========== NEW CHUNK METHODS ==========

    def _create_fees_timing_chunks(self, data: Dict, parent_id: str) -> List[EnrichedChunk]:
        """
        NEW Child Type E: Fees & Timing (Phí lệ phí + Thời hạn + Hình thức nộp)

        CRITICAL: Includes ALL items from hinh_thuc_nop table, not just first one!
        This consolidates all submission methods, fees, and timing information.
        """
        chunks = []
        hinh_thuc_nop = data["tables"].get("hinh_thuc_nop", [])

        # If no timing/fees information
        if not hinh_thuc_nop or len(hinh_thuc_nop) == 0:
            return chunks

        # Parent context
        parent_context = f"""[PARENT CONTEXT]
Thủ tục: {data['metadata'].get('tên_thủ_tục', '')}
Mã: {data['metadata'].get('mã_thủ_tục', '')}
"""

        # Build comprehensive fees & timing information
        main_content = "[MAIN CONTENT]\nPHÍ LỆ PHÍ VÀ THỜI HẠN GIẢI QUYẾT:\n\n"

        # IMPORTANT: Process ALL submission methods, not just the first one
        for i, form in enumerate(hinh_thuc_nop, 1):
            hinh_thuc = form.get("hinh_thuc", "")
            thoi_han = form.get("thoi_han_giai_quyet", "")
            phi = form.get("phi_le_phi", "")
            mo_ta = form.get("mo_ta", "")  # FIXED: Add mo_ta field from table

            main_content += f"{i}. HÌNH THỨC: {hinh_thuc}\n"
            if thoi_han:
                main_content += f"   - Thời hạn giải quyết: {thoi_han}\n"
            if phi:
                main_content += f"   - Phí, lệ phí: {phi}\n"
            if mo_ta:  # FIXED: Include mo_ta description
                main_content += f"   - Mô tả: {mo_ta}\n"
            main_content += "\n"

        # Add submission address if available
        dia_chi = data["content"].get("địa_chỉ_tiếp_nhận_hs", "")
        if dia_chi and dia_chi != "Không có thông tin":
            main_content += f"ĐỊA ĐIỂM TIẾP NHẬN HỒ SƠ:\n{dia_chi}\n"

        full_content = parent_context + "\n" + main_content
        token_count = self.count_tokens(full_content)

        # Create chunk (usually fits in 512 tokens)
        chunk = EnrichedChunk(
            chunk_id=f"{data['thu_tuc_id']}_child_fees_timing_0",
            thu_tuc_id=data["thu_tuc_id"],
            chunk_type="child_fees_timing",
            chunk_tier="child",
            parent_chunk_id=parent_id,
            content=full_content.strip(),
            metadata=data["metadata"].copy(),
            char_count=len(full_content),
            token_count=token_count,
            importance_score=self.CHUNK_IMPORTANCE["child_fees_timing"]
        )
        chunks.append(chunk)

        return chunks

    def _create_agencies_chunks(self, data: Dict, parent_id: str) -> List[EnrichedChunk]:
        """
        NEW Child Type F: Agencies (Tất cả cơ quan + địa chỉ)

        CRITICAL: Includes ALL agency-related fields:
        - Cơ quan thực hiện
        - Cơ quan có thẩm quyền
        - Cơ quan phối hợp
        - Địa chỉ tiếp nhận hồ sơ
        - Kết quả thực hiện (what agency provides)
        """
        chunks = []
        content_data = data["content"]

        # Extract all agency fields
        co_quan_thuc_hien = content_data.get("cơ_quan_thực_hiện", "")
        co_quan_tham_quyen = content_data.get("cơ_quan_có_thẩm_quyền", "")
        co_quan_phoi_hop = content_data.get("cơ_quan_phối_hợp", "")
        dia_chi = content_data.get("địa_chỉ_tiếp_nhận_hs", "")
        ket_qua = content_data.get("kết_quả_thực_hiện", "")

        # If no agency information at all
        if not any([co_quan_thuc_hien, co_quan_tham_quyen, co_quan_phoi_hop, dia_chi]):
            return chunks

        # Parent context
        parent_context = f"""[PARENT CONTEXT]
Thủ tục: {data['metadata'].get('tên_thủ_tục', '')}
Mã: {data['metadata'].get('mã_thủ_tục', '')}
"""

        # Build comprehensive agency information
        main_content = "[MAIN CONTENT]\nCÁC CƠ QUAN LIÊN QUAN:\n\n"

        # Implementing agency
        if co_quan_thuc_hien and co_quan_thuc_hien != "Không có thông tin":
            main_content += f"1. CƠ QUAN THỰC HIỆN:\n{co_quan_thuc_hien}\n\n"

        # Authorized agency
        if co_quan_tham_quyen and co_quan_tham_quyen != "Không có thông tin":
            main_content += f"2. CƠ QUAN CÓ THẨM QUYỀN:\n{co_quan_tham_quyen}\n\n"

        # Coordinating agencies
        if co_quan_phoi_hop and co_quan_phoi_hop != "Không có thông tin":
            main_content += f"3. CƠ QUAN PHỐI HỢP:\n{co_quan_phoi_hop}\n\n"

        # Submission address
        if dia_chi and dia_chi != "Không có thông tin":
            main_content += f"ĐỊA CHỈ TIẾP NHẬN HỒ SƠ:\n{dia_chi}\n\n"

        # Result (what you get from which agency)
        if ket_qua and ket_qua != "Không có thông tin":
            main_content += f"KẾT QUẢ THỰC HIỆN:\n{ket_qua}\n"

        full_content = parent_context + "\n" + main_content
        token_count = self.count_tokens(full_content)

        # Create chunk (usually fits in 640 tokens)
        chunk = EnrichedChunk(
            chunk_id=f"{data['thu_tuc_id']}_child_agencies_0",
            thu_tuc_id=data["thu_tuc_id"],
            chunk_type="child_agencies",
            chunk_tier="child",
            parent_chunk_id=parent_id,
            content=full_content.strip(),
            metadata=data["metadata"].copy(),
            char_count=len(full_content),
            token_count=token_count,
            importance_score=self.CHUNK_IMPORTANCE["child_agencies"]
        )
        chunks.append(chunk)

        return chunks

    # ========== ENRICHMENT METHODS ==========

    def _enrich_all_chunks(
        self,
        chunks: List[EnrichedChunk],
        parent_chunk: EnrichedChunk,
        thu_tuc_data: Dict
    ) -> List[EnrichedChunk]:
        """
        Enrich all chunks with:
        1. Parent context (first 200 chars of parent)
        2. Breadcrumb (Lĩnh vực > Procedure > Chunk type)
        3. Sibling chunk IDs (all other chunks from same procedure)
        4. Complexity level (based on content length)
        5. Related procedure IDs (from ProcedureGraph if available)
        """
        # Extract parent context (first 200 chars)
        parent_context_text = parent_chunk.content[:200]

        # Build sibling map
        chunk_ids = [c.chunk_id for c in chunks]

        # Get related procedures from graph (if available)
        related_procedure_ids = []
        if self.procedure_graph:
            thu_tuc_id = thu_tuc_data["thu_tuc_id"]

            # Get top 10 related procedures (mixed from all types)
            # Priority: same_domain > related_legal > similar > sequential
            related = self.procedure_graph.get_related_procedures(
                thu_tuc_id,
                relationship_types=None,  # All types
                min_strength=0.5,  # Only strong relationships
                max_results=10
            )
            related_procedure_ids = [rel_id for rel_id, _ in related]

        # Enrich each chunk
        for chunk in chunks:
            # 1. Add parent context
            chunk.parent_context = parent_context_text

            # 2. Build breadcrumb
            chunk.breadcrumb = self._build_breadcrumb(thu_tuc_data, chunk)

            # 3. Add sibling chunk IDs (all other chunks from same procedure)
            chunk.sibling_chunk_ids = [cid for cid in chunk_ids if cid != chunk.chunk_id]

            # 4. Determine complexity level
            chunk.complexity_level = self._calculate_complexity(chunk)

            # 5. Add related procedure IDs (from graph)
            chunk.related_procedure_ids = related_procedure_ids

        return chunks

    def _build_breadcrumb(self, thu_tuc_data: Dict, chunk: EnrichedChunk) -> str:
        """
        Build breadcrumb path: Lĩnh vực > Procedure name > Chunk type

        Example: "Hộ tịch > Đăng ký kết hôn > Documents"
        """
        linh_vuc = thu_tuc_data['metadata'].get('lĩnh_vực', 'Unknown')
        ten_thu_tuc = thu_tuc_data['metadata'].get('tên_thủ_tục', 'Unknown')

        # Map chunk type to Vietnamese readable name
        chunk_type_names = {
            "parent_overview": "Tổng quan",
            "child_documents": "Hồ sơ",
            "child_requirements": "Yêu cầu",
            "child_process": "Quy trình",
            "child_legal": "Căn cứ pháp lý",
            "child_fees_timing": "Phí & Thời hạn",
            "child_agencies": "Cơ quan"
        }

        chunk_name = chunk_type_names.get(chunk.chunk_type, chunk.chunk_type)

        # Truncate if too long
        if len(ten_thu_tuc) > 50:
            ten_thu_tuc = ten_thu_tuc[:47] + "..."

        breadcrumb = f"{linh_vuc} > {ten_thu_tuc} > {chunk_name}"

        return breadcrumb

    def _calculate_complexity(self, chunk: EnrichedChunk) -> str:
        """
        Calculate complexity level based on content length

        - simple: < 500 chars
        - medium: 500-1500 chars
        - complex: > 1500 chars
        """
        char_count = chunk.char_count

        if char_count < 500:
            return "simple"
        elif char_count < 1500:
            return "medium"
        else:
            return "complex"

    # ========== UTILITY METHODS ==========

    def _split_with_overlap(self, text: str, max_tokens: int, overlap_tokens: int, prefix: str = "") -> List[str]:
        """
        Split text into chunks with overlap

        PRESERVED: Original logic maintained
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

            # Move start with overlap
            if end >= len(tokens):
                break
            start = end - overlap_tokens

        return chunks

    def chunk_all_files(self, input_dir: Path, output_dir: Path):
        """
        Chunk all JSON files in directory

        Enhanced to show new chunk types in statistics
        """
        json_files = list(input_dir.glob("*.json"))

        print(f"🔄 Bắt đầu chunking với GraphChunker (enhanced)...")
        print(f"   - {len(json_files)} files")
        print(f"   - 6 chunk types (4 existing + 2 NEW)")
        print()

        all_chunks = []
        total_chunks_count = 0

        for i, file_path in enumerate(json_files, 1):
            print(f"\r⏳ Chunking: {i}/{len(json_files)}", end='', flush=True)

            # Load JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Chunk with enrichment
            chunks = self.chunk_thu_tuc(data)
            all_chunks.extend(chunks)
            total_chunks_count += len(chunks)

        print("\n")

        # Save all chunks to JSON
        output_dir.mkdir(parents=True, exist_ok=True)
        chunks_file = output_dir / "all_chunks_enriched.json"

        # Convert chunks to dict
        chunks_dict = [asdict(chunk) for chunk in all_chunks]

        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_dict, f, ensure_ascii=False, indent=2)

        # Print detailed statistics
        print("=" * 80)
        print("KẾT QUẢ CHUNKING VỚI ENRICHMENT")
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
        print(f"   - Fees & Timing: {sum(1 for c in all_chunks if c.chunk_type == 'child_fees_timing')} ⭐ NEW")
        print(f"   - Agencies: {sum(1 for c in all_chunks if c.chunk_type == 'child_agencies')} ⭐ NEW")
        print()
        print(f"✨ Enrichment:")
        print(f"   - All chunks have parent context (first 200 chars)")
        print(f"   - All chunks have breadcrumb paths")
        print(f"   - All chunks have sibling IDs")
        print(f"   - All chunks have importance scores")
        print()
        print(f"💾 Enriched chunks saved: {chunks_file}")
        print("=" * 80)

        # Generate statistics
        self._generate_chunking_stats(all_chunks, output_dir)

        return all_chunks

    def _generate_chunking_stats(self, chunks: List[EnrichedChunk], output_dir: Path):
        """Generate enhanced chunking statistics"""
        stats = {
            "total_chunks": len(chunks),
            "by_tier": {},
            "by_type": {},
            "token_stats": {
                "min": min(c.token_count for c in chunks),
                "max": max(c.token_count for c in chunks),
                "avg": sum(c.token_count for c in chunks) / len(chunks)
            },
            "enrichment_stats": {
                "chunks_with_parent_context": sum(1 for c in chunks if c.parent_context),
                "chunks_with_breadcrumb": sum(1 for c in chunks if c.breadcrumb),
                "chunks_with_siblings": sum(1 for c in chunks if c.sibling_chunk_ids),
                "avg_siblings_per_chunk": sum(len(c.sibling_chunk_ids) for c in chunks) / len(chunks)
            }
        }

        # By tier
        for tier in ["parent", "child"]:
            tier_chunks = [c for c in chunks if c.chunk_tier == tier]
            stats["by_tier"][tier] = {
                "count": len(tier_chunks),
                "avg_tokens": sum(c.token_count for c in tier_chunks) / len(tier_chunks) if tier_chunks else 0
            }

        # By type (including new types)
        chunk_types = set(c.chunk_type for c in chunks)
        for chunk_type in chunk_types:
            type_chunks = [c for c in chunks if c.chunk_type == chunk_type]
            stats["by_type"][chunk_type] = {
                "count": len(type_chunks),
                "avg_tokens": sum(c.token_count for c in type_chunks) / len(type_chunks) if type_chunks else 0,
                "max_tokens": max(c.token_count for c in type_chunks) if type_chunks else 0,
                "avg_importance": sum(c.importance_score for c in type_chunks) / len(type_chunks) if type_chunks else 0
            }

        # Save stats
        stats_file = output_dir / "enriched_chunking_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"📈 Enhanced statistics saved: {stats_file}")


def main():
    """Main function"""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_dir = project_root / "data"
    extracted_dir = data_dir / "extracted"
    chunks_dir = data_dir / "chunks_v2"  # NEW directory for enriched chunks

    if not extracted_dir.exists():
        print(f"❌ Không tìm thấy thư mục extracted: {extracted_dir}")
        print("   Hãy chạy extract_documents.py trước!")
        return

    # Create enhanced chunker
    print("🚀 Khởi tạo GraphChunker (Enhanced Hierarchical Chunker)")
    print("=" * 80)
    chunker = GraphChunker()

    # Chunk all files with enrichment
    chunks = chunker.chunk_all_files(extracted_dir, chunks_dir)

    return chunks


if __name__ == "__main__":
    main()
