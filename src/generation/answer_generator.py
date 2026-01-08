#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Answer Generator - Phase 4: Generation & Answer Synthesis
Uses Ollama LLM to generate context-based answers with source citation
"""

import sys
import json
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Import configuration
try:
    from backend.config import settings
except ImportError:
    # Fallback if backend module is not in path
    settings = None

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Intent-specific system prompts for natural language answer generation
INTENT_SPECIFIC_PROMPTS = {
    "requirements": """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ trả lời dựa trên CONTEXT được cung cấp
2. KHÔNG bịa đặt thông tin không có trong context
3. Nếu context không có thông tin, hãy nói rõ "Thông tin này không có trong tài liệu"
4. Trả lời CHÍNH XÁC, SÚC TÍCH, DỄ HIỂU
5. Sử dụng ngôn ngữ tự nhiên, thân thiện
6. **BẮT BUỘC: Trả lời HOÀN TOÀN bằng TIẾNG VIỆT, KHÔNG được dùng tiếng Anh**

YÊU CẦU HÀNH VI:
- Nếu KHÔNG TÌM THẤY thông tin trong context, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết (tên thủ tục, lĩnh vực, hoặc mã thủ tục) để tôi tìm kiếm chính xác hơn không?"

CẤU TRÚC TRẢ LỜI (QUAN TRỌNG - Áp dụng cho câu hỏi về điều kiện/eligibility):
1. **KẾT LUẬN TRỰC TIẾP** ngay ở đầu (Có/Không, Đủ/Không đủ, Được/Không được)
2. **LÝ DO CHÍNH** (1-2 câu giải thích ngắn gọn tại sao)
3. **CHI TIẾT QUY ĐỊNH** (nếu cần thiết để làm rõ)

Ví dụ tốt:
"Dựa trên quy định hiện hành, trường hợp của bạn KHÔNG đủ điều kiện để hưởng chế độ này.

Lý do: Mặc dù bạn đáp ứng điều kiện về thời gian phục vụ (22 năm), nhưng bạn đang hưởng chế độ mất sức lao động hàng tháng - đây là điều kiện loại trừ theo quy định.

Chi tiết quy định:
- Đối tượng: Quân nhân có từ 20 năm phục vụ trở lên
- Điều kiện loại trừ: Không được đang hưởng chế độ mất sức lao động..."

ĐỊNH DẠNG TRẢ LỜI:
- ĐI THẲNG VÀO KẾT LUẬN trước, giải thích sau
- Sắp xếp thông tin theo danh sách nếu có nhiều mục
- Kết thúc bằng ghi chú quan trọng (nếu có)
""",

    "documents": """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ trả lời dựa trên CONTEXT được cung cấp
2. KHÔNG bịa đặt thông tin không có trong context
3. Nếu context không có thông tin, hãy nói rõ "Thông tin này không có trong tài liệu"
4. Trả lời CHÍNH XÁC, SÚC TÍCH, DỄ HIỂU
5. Sử dụng ngôn ngữ tự nhiên, thân thiện
6. **BẮT BUỘC: Trả lời HOÀN TOÀN bằng TIẾNG VIỆT, KHÔNG được dùng tiếng Anh**

YÊU CẦU HÀNH VI:
- Nếu KHÔNG TÌM THẤY thông tin trong context, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết để tôi tìm kiếm chính xác hơn không?"

CẤU TRÚC TRẢ LỜI (cho câu hỏi về giấy tờ/hồ sơ):
1. **LIỆT KÊ GIẤY TỜ** trực tiếp dưới dạng danh sách có số thứ tự
2. **SỐ BẢN** cần nộp cho mỗi loại giấy tờ (nếu có)
3. **GHI CHÚ** quan trọng (nếu có)

Ví dụ tốt:
"Hồ sơ bao gồm:

1. Giấy tờ tùy thân (CMND/CCCD) - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính
3. Giấy khám sức khỏe - 01 bản chính

Lưu ý: Nếu cơ quan có thể khai thác thông tin từ Cơ sở dữ liệu quốc gia về dân cư, không cần nộp bản sao CCCD."

ĐỊNH DẠNG TRẢ LỜI:
- Liệt kê giấy tờ NGAY LẬP TỨC, không có phần mở đầu dài dòng
- Sử dụng danh sách có số thứ tự
- Ghi rõ số bản (bản chính/bản sao) cho từng loại giấy tờ
""",

    "process": """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ trả lời dựa trên CONTEXT được cung cấp
2. KHÔNG bịa đặt thông tin không có trong context
3. Nếu context không có thông tin, hãy nói rõ "Thông tin này không có trong tài liệu"
4. Trả lời CHÍNH XÁC, SÚC TÍCH, DỄ HIỂU
5. Sử dụng ngôn ngữ tự nhiên, thân thiện
6. **BẮT BUỘC: Trả lời HOÀN TOÀN bằng TIẾNG VIỆT, KHÔNG được dùng tiếng Anh**

YÊU CẦU HÀNH VI:
- Nếu KHÔNG TÌM THẤY thông tin trong context, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết để tôi tìm kiếm chính xác hơn không?"

CẤU TRÚC TRẢ LỜI (cho câu hỏi về quy trình/các bước):
1. **LIỆT KÊ CÁC BƯỚC** theo thứ tự (Bước 1, Bước 2...)
2. **MÔ TẢ NGẮN GỌN** cho từng bước
3. **GHI CHÚ** quan trọng (nếu có)

Ví dụ tốt:
"Quy trình thực hiện gồm các bước sau:

Bước 1: Chuẩn bị hồ sơ theo quy định (bao gồm CMND, giấy xác nhận...)

Bước 2: Nộp hồ sơ tại bộ phận một cửa UBND cấp xã nơi cư trú

Bước 3: Nhận kết quả sau 3 ngày làm việc

Lưu ý: Có thể nộp hồ sơ trực tuyến qua Cổng dịch vụ công."

ĐỊNH DẠNG TRẢ LỜI:
- Liệt kê các bước NGAY LẬP TỨC
- Sử dụng "Bước 1", "Bước 2"...
- Mỗi bước có mô tả rõ ràng, súc tích
""",

    "fees": """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ trả lời dựa trên CONTEXT được cung cấp
2. KHÔNG bịa đặt thông tin không có trong context
3. Nếu context không có thông tin, hãy nói rõ "Thông tin này không có trong tài liệu"
4. Trả lời CHÍNH XÁC, SÚC TÍCH, DỄ HIỂU
5. Sử dụng ngôn ngữ tự nhiên, thân thiện
6. **BẮT BUỘC: Trả lời HOÀN TOÀN bằng TIẾNG VIỆT, KHÔNG được dùng tiếng Anh**

YÊU CẦU HÀNH VI:
- Nếu KHÔNG TÌM THẤY thông tin trong context, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết để tôi tìm kiếm chính xác hơn không?"

CẤU TRÚC TRẢ LỜI (cho câu hỏi về phí/lệ phí):
1. **NÓI RÕ PHÍ** trực tiếp ngay đầu câu
2. **CHI TIẾT** các loại phí (nếu có nhiều loại)
3. **GHI CHÚ** về miễn phí, giảm phí (nếu có)

Ví dụ tốt:
"Lệ phí: 50.000 đồng/hồ sơ

Lưu ý: Miễn phí đối với hộ nghèo, hộ cận nghèo có xác nhận của UBND cấp xã."

Ví dụ tốt (không thu phí):
"Không thu phí."

ĐỊNH DẠNG TRẢ LỜI:
- Nói rõ phí NGAY LẬP TỨC
- Nếu không thu phí, chỉ cần nói "Không thu phí"
- Ghi rõ đơn vị tính (đồng/hồ sơ, đồng/giấy...)
""",

    "timeline": """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ trả lời dựa trên CONTEXT được cung cấp
2. KHÔNG bịa đặt thông tin không có trong context
3. Nếu context không có thông tin, hãy nói rõ "Thông tin này không có trong tài liệu"
4. Trả lời CHÍNH XÁC, SÚC TÍCH, DỄ HIỂU
5. Sử dụng ngôn ngữ tự nhiên, thân thiện
6. **BẮT BUỘC: Trả lời HOÀN TOÀN bằng TIẾNG VIỆT, KHÔNG được dùng tiếng Anh**

YÊU CẦU HÀNH VI:
- Nếu KHÔNG TÌM THẤY thông tin trong context, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết để tôi tìm kiếm chính xác hơn không?"

CẤU TRÚC TRẢ LỜI (cho câu hỏi về thời gian/thời hạn):
1. **NÓI RÕ THỜI GIAN** trực tiếp ngay đầu câu
2. **CHI TIẾT** thời gian các bước (nếu có)
3. **GHI CHÚ** về trường hợp đặc biệt (nếu có)

Ví dụ tốt:
"Thời gian giải quyết: 3 ngày làm việc kể từ khi nhận đủ hồ sơ hợp lệ.

Lưu ý: Trong trường hợp phức tạp cần xác minh, thời gian có thể kéo dài thêm 2 ngày làm việc."

ĐỊNH DẠNG TRẢ LỜI:
- Nói rõ thời gian NGAY LẬP TỨC
- Ghi rõ đơn vị (ngày làm việc, ngày)
- Ghi rõ mốc thời gian bắt đầu tính (kể từ khi nhận hồ sơ...)
""",

    "legal": """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ trả lời dựa trên CONTEXT được cung cấp
2. KHÔNG bịa đặt thông tin không có trong context
3. Nếu context không có thông tin, hãy nói rõ "Thông tin này không có trong tài liệu"
4. Trả lời CHÍNH XÁC, SÚC TÍCH, DỄ HIỂU
5. Sử dụng ngôn ngữ tự nhiên, thân thiện
6. **BẮT BUỘC: Trả lời HOÀN TOÀN bằng TIẾNG VIỆT, KHÔNG được dùng tiếng Anh**

YÊU CẦU HÀNH VI:
- Nếu KHÔNG TÌM THẤY thông tin trong context, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết để tôi tìm kiếm chính xác hơn không?"

CẤU TRÚC TRẢ LỜI (cho câu hỏi về căn cứ pháp lý):
1. **LIỆT KÊ CĂN CỨ PHÁP LÝ** (tên văn bản, số/ký hiệu, điều khoản)
2. **NỘI DUNG** chính của quy định (nếu cần thiết)

Ví dụ tốt:
"Căn cứ pháp lý:

- Luật Hộ tịch năm 2014
- Nghị định 123/2015/NĐ-CP ngày 15/11/2015, Điều 15 về đăng ký kết hôn
- Thông tư 04/2020/TT-BTP hướng dẫn thực hiện"

ĐỊNH DẠNG TRẢ LỜI:
- Liệt kê văn bản pháp luật NGAY LẬP TỨC
- Ghi đầy đủ: tên văn bản, số/ký hiệu, điều khoản (nếu có)
- Sắp xếp theo thứ bậc (Luật > Nghị định > Thông tư...)
""",

    "location": """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ trả lời dựa trên CONTEXT được cung cấp
2. KHÔNG bịa đặt thông tin không có trong context
3. Nếu context không có thông tin, hãy nói rõ "Thông tin này không có trong tài liệu"
4. Trả lời CHÍNH XÁC, SÚC TÍCH, DỄ HIỂU
5. Sử dụng ngôn ngữ tự nhiên, thân thiện
6. **BẮT BUỘC: Trả lời HOÀN TOÀN bằng TIẾNG VIỆT, KHÔNG được dùng tiếng Anh**

YÊU CẦU HÀNH VI:
- Nếu KHÔNG TÌM THẤY thông tin trong context, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết để tôi tìm kiếm chính xác hơn không?"

CẤU TRÚC TRẢ LỜI (cho câu hỏi về địa điểm/cơ quan):
1. **NÓI RÕ ĐỊA ĐIỂM/CƠ QUAN** thực hiện
2. **ĐỊA CHỈ CỤ THỂ** (nếu có trong context)
3. **GHI CHÚ** về hình thức trực tuyến (nếu có)

Ví dụ tốt:
"Thực hiện tại: Bộ phận một cửa UBND cấp xã nơi cư trú.

Lưu ý: Một số thủ tục có thể thực hiện trực tuyến qua Cổng dịch vụ công quốc gia."

ĐỊNH DẠNG TRẢ LỜI:
- Nói rõ địa điểm NGAY LẬP TỨC
- Ghi rõ cấp cơ quan (cấp xã, cấp huyện, cấp tỉnh...)
- Nếu có địa chỉ cụ thể, ghi đầy đủ
""",

    "overview": """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ trả lời dựa trên CONTEXT được cung cấp
2. KHÔNG bịa đặt thông tin không có trong context
3. Nếu context không có thông tin, hãy nói rõ "Thông tin này không có trong tài liệu"
4. Trả lời CHÍNH XÁC, SÚC TÍCH, DỄ HIỂU
5. Sử dụng ngôn ngữ tự nhiên, thân thiện
6. **BẮT BUỘC: Trả lời HOÀN TOÀN bằng TIẾNG VIỆT, KHÔNG được dùng tiếng Anh**

YÊU CẦU HÀNH VI:
- Nếu KHÔNG TÌM THẤY thông tin trong context, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết (tên thủ tục, lĩnh vực, hoặc mã thủ tục) để tôi tìm kiếm chính xác hơn không?"

CẤU TRÚC TRẢ LỜI (cho câu hỏi tổng quan):
1. **GIỚI THIỆU** ngắn gọn về thủ tục
2. **THÔNG TIN CHÍNH** (đối tượng, hồ sơ, thời gian, phí...)
3. **GHI CHÚ** quan trọng (nếu có)

Ví dụ tốt:
"Đăng ký kết hôn là thủ tục hành chính thuộc lĩnh vực Hộ tịch, do UBND cấp xã thực hiện.

Thông tin chính:
- Đối tượng: Nam từ đủ 20 tuổi, nữ từ đủ 18 tuổi
- Hồ sơ: CMND/CCCD, giấy khám sức khỏe...
- Thời gian giải quyết: 1 ngày làm việc
- Phí: Không thu phí

Lưu ý: Có thể đăng ký trực tuyến hoặc trực tiếp tại UBND cấp xã."

ĐỊNH DẠNG TRẢ LỜI:
- Giới thiệu ngắn gọn về thủ tục
- Trình bày thông tin dưới dạng danh sách rõ ràng
- Kết thúc bằng ghi chú quan trọng (nếu có)
"""
}


@dataclass
class SourceCitation:
    """Source citation for answer"""
    chunk_id: str
    thu_tuc_name: str
    thu_tuc_code: str
    chunk_type: str
    relevance_score: float
    content_snippet: str  # First 200 chars for reference


@dataclass
class GeneratedAnswer:
    """Complete answer with metadata"""
    question: str
    answer: str  # Natural language answer
    structured_data: Dict  # JSON structured answer
    sources: List[SourceCitation]
    confidence: float
    intent: str
    timestamp: str
    metadata: Dict


class OllamaAnswerGenerator:
    """
    Answer Generator using Ollama LLM

    Features:
    1. Context-only answers (no hallucination)
    2. Hybrid output: JSON + Natural Language
    3. Source citation with chunk_id
    4. Confidence scoring
    """

    def __init__(
        self,
        model_name: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize answer generator

        Args:
            model_name: Ollama LLM model
            ollama_url: Ollama server URL
        """
        print(f"🔄 Initializing Answer Generator")
        print(f"   Model: {model_name}")
        print(f"   Server: {ollama_url}")

        self.model_name = model_name
        self.ollama_url = ollama_url
        self.generate_endpoint = f"{ollama_url}/api/generate"

        print(f"✅ Answer Generator initialized!")

    def _call_ollama(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1
    ) -> str:
        """
        Call Ollama LLM API

        Args:
            prompt: User prompt
            system: System prompt
            temperature: Sampling temperature (low for factual answers)

        Returns:
            Generated text
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40
            }
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=120  # Longer timeout for generation
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            return response.json()["response"].strip()
        except Exception as e:
            print(f"⚠️ Ollama API call failed: {e}")
            return ""

    def _extract_sources(self, retrieved_chunks: List[Dict]) -> List[SourceCitation]:
        """
        Extract source citations from retrieved chunks

        Args:
            retrieved_chunks: List of retrieved chunk dicts

        Returns:
            List of SourceCitation objects
        """
        sources = []

        for chunk in retrieved_chunks:
            # Extract metadata
            metadata = chunk.get("metadata", {})
            content = chunk.get("content", "")

            # Create citation (check top-level fields first, fallback to nested metadata)
            citation = SourceCitation(
                chunk_id=chunk.get("chunk_id", "N/A"),
                thu_tuc_name=chunk.get("tên_thủ_tục", metadata.get("tên_thủ_tục", "N/A")),
                thu_tuc_code=chunk.get("mã_thủ_tục", metadata.get("mã_thủ_tục", "N/A")),
                chunk_type=chunk.get("chunk_type", "N/A"),
                relevance_score=chunk.get("final_score", 0.0),
                content_snippet=content[:200] + "..." if len(content) > 200 else content
            )

            sources.append(citation)

        return sources

    def _generate_structured_answer(
        self,
        question: str,
        context: str,
        intent: str
    ) -> Dict:
        """
        Generate structured JSON answer based on intent

        Args:
            question: User question
            context: Retrieved context
            intent: Question intent

        Returns:
            Structured dictionary answer
        """
        system_prompt = """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NHIỆM VỤ:
- Trích xuất thông tin có cấu trúc từ context được cung cấp
- KHÔNG bịa đặt thông tin
- Chỉ trả lời dựa HOÀN TOÀN trên context
- Nếu context không chứa thông tin, trả về giá trị rỗng
- **BẮT BUỘC: Tất cả giá trị trong JSON phải bằng TIẾNG VIỆT**

QUAN TRỌNG:
- Chỉ trả về JSON, KHÔNG giải thích
- JSON phải valid và có thể parse được
- Tất cả text trong JSON phải bằng TIẾNG VIỆT
"""

        # Intent-specific JSON schema prompts
        intent_schemas = {
            "documents": """
Trích xuất danh sách giấy tờ cần nộp.
Trả về JSON:
{
  "ho_so_bao_gom": ["giấy tờ 1", "giấy tờ 2", ...],
  "so_ban": {"giấy tờ 1": "số bản", ...},
  "ghi_chu": "..."
}
""",
            "requirements": """
Trích xuất điều kiện và yêu cầu.
Trả về JSON:
{
  "doi_tuong": "mô tả đối tượng được làm thủ tục",
  "dieu_kien": ["điều kiện 1", "điều kiện 2", ...],
  "yeu_cau": ["yêu cầu 1", "yêu cầu 2", ...]
}
""",
            "process": """
Trích xuất quy trình thực hiện.
Trả về JSON:
{
  "cac_buoc": [
    {"buoc": 1, "mo_ta": "..."},
    {"buoc": 2, "mo_ta": "..."}
  ],
  "ghi_chu": "..."
}
""",
            "legal": """
Trích xuất căn cứ pháp lý.
Trả về JSON:
{
  "can_cu_phap_ly": ["văn bản 1", "văn bản 2", ...],
  "ghi_chu": "..."
}
""",
            "timeline": """
Trích xuất thông tin thời gian.
Trả về JSON:
{
  "thoi_han_giai_quyet": "...",
  "thoi_gian_tiep_nhan": "...",
  "ghi_chu": "..."
}
""",
            "fees": """
Trích xuất thông tin phí.
Trả về JSON:
{
  "le_phi": "...",
  "phi_khac": "...",
  "ghi_chu": "..."
}
""",
            "overview": """
Trích xuất thông tin tổng quan.
Trả về JSON:
{
  "ten_thu_tuc": "...",
  "ma_thu_tuc": "...",
  "linh_vuc": "...",
  "trich_yeu": "...",
  "co_quan_thuc_hien": "..."
}
"""
        }

        # Get schema for intent
        schema_prompt = intent_schemas.get(intent, intent_schemas["overview"])

        prompt = f"""Câu hỏi: {question}

Context từ cơ sở dữ liệu:
{context}

{schema_prompt}

Chỉ trả về JSON, không giải thích:"""

        try:
            response = self._call_ollama(prompt, system=system_prompt, temperature=0.1)

            # Extract JSON from response - try multiple strategies
            json_str = None

            # Strategy 1: Try to find JSON in markdown code blocks
            if "```json" in response:
                start_marker = response.find("```json") + 7
                end_marker = response.find("```", start_marker)
                if end_marker > start_marker:
                    json_str = response[start_marker:end_marker].strip()

            # Strategy 2: Find first complete JSON object
            if not json_str:
                start = response.find("{")
                if start != -1:
                    # Find matching closing brace
                    brace_count = 0
                    for i in range(start, len(response)):
                        if response[i] == "{":
                            brace_count += 1
                        elif response[i] == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = response[start:i+1]
                                break

            # Try to parse JSON
            if json_str:
                structured_data = json.loads(json_str)
                return structured_data
            else:
                print(f"⚠️ No valid JSON found in LLM response")

        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse JSON: {e}")
            print(f"   Response preview: {response[:200]}...")
        except Exception as e:
            print(f"⚠️ Failed to generate structured answer: {e}")

        # Return empty structure on failure
        return {}

    def _generate_natural_language_answer(
        self,
        question: str,
        context: str,
        intent: str,
        structured_data: Dict
    ) -> str:
        """
        Generate natural language answer

        Args:
            question: User question
            context: Retrieved context
            intent: Question intent
            structured_data: Previously generated structured data

        Returns:
            Natural language answer string
        """
        # Get intent-specific system prompt
        system_prompt = INTENT_SPECIFIC_PROMPTS.get(
            intent,
            INTENT_SPECIFIC_PROMPTS["overview"]  # Fallback to overview for unknown intents
        )

        prompt = f"""Câu hỏi: "{question}"

Context từ cơ sở dữ liệu:
{context}

Dữ liệu có cấu trúc đã trích xuất:
{json.dumps(structured_data, ensure_ascii=False, indent=2)}

Hãy trả lời câu hỏi bằng ngôn ngữ tự nhiên, dễ hiểu.
Trả lời:"""
        print("\n[DEBUG] Natural Language Answer Prompt:", prompt, "\n")
        answer = self._call_ollama(prompt, system=system_prompt, temperature=0.2)

        if not answer:
            answer = "Xin lỗi, tôi không thể tạo câu trả lời từ thông tin có sẵn."

        return answer

    def generate(
        self,
        question: str,
        intent: str,
        context: str,
        retrieved_chunks: List[Dict],
        confidence: float,
        metadata: Dict,
        enable_structured_output: Optional[bool] = None  # NEW: Override for intent-based config
    ) -> GeneratedAnswer:
        """
        Main generation method - creates complete answer with sources

        Args:
            question: User question
            intent: Question intent
            context: Retrieved context
            retrieved_chunks: List of retrieved chunks
            confidence: Retrieval confidence score
            metadata: Additional metadata
            enable_structured_output: Override for structured output (None = use settings default)

        Returns:
            GeneratedAnswer object with complete answer
        """
        print("\n" + "=" * 80)
        print("ANSWER GENERATION")
        print("=" * 80)
        print(f"\nQuestion: {question}")
        print(f"Intent: {intent}")
        print(f"Confidence: {confidence:.2f}")
        print()

        # Step 1: Extract sources
        print("[Step 1/3] Extracting source citations...")
        sources = self._extract_sources(retrieved_chunks)
        print(f"   ✓ {len(sources)} sources extracted")

        # Handle case when no context is available
        if not context or not context.strip():
            print("   ⚠️ No context available - generating fallback response")
            structured_data = {}
            natural_answer = "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể cung cấp thêm chi tiết (tên thủ tục, lĩnh vực, hoặc mã thủ tục) để tôi tìm kiếm chính xác hơn không?"
        else:
            # Use parameter override if provided, else use settings default
            if enable_structured_output is None:
                # No override - use settings default (TEMP: Disabled by default)
                enable_structured = False
                if settings and hasattr(settings, 'enable_structured_output'):
                    enable_structured = settings.enable_structured_output
            else:
                # Override provided by intent-based config
                enable_structured = enable_structured_output

            # Step 2: Generate structured answer (if enabled)
            if enable_structured:
                print("[Step 2/3] Generating structured answer (JSON)...")
                structured_data = self._generate_structured_answer(question, context, intent)
                print(f"   ✓ Structured data generated")
            else:
                print("[Step 2/3] Structured output disabled - skipping JSON generation")
                structured_data = {}

            # Step 3: Generate natural language answer
            print("[Step 3/3] Generating natural language answer...")
            natural_answer = self._generate_natural_language_answer(
                question, context, intent, structured_data
            )
            print(f"   ✓ Natural language answer generated ({len(natural_answer)} chars)")

        # Create final answer object
        answer = GeneratedAnswer(
            question=question,
            answer=natural_answer,
            structured_data=structured_data,
            sources=sources,
            confidence=confidence,
            intent=intent,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )

        print("\n" + "=" * 80)
        print("✅ ANSWER GENERATION COMPLETE")
        print("=" * 80)

        return answer

    def format_answer_for_display(self, answer: GeneratedAnswer) -> str:
        """
        Format answer for user-friendly display

        Args:
            answer: GeneratedAnswer object

        Returns:
            Formatted string for display
        """
        output = []

        # Header
        output.append("\n" + "=" * 80)
        output.append("📋 KẾT QUẢ TRẢ LỜI")
        output.append("=" * 80)

        # Question
        output.append(f"\n❓ Câu hỏi: {answer.question}")
        output.append(f"🎯 Intent: {answer.intent}")
        output.append(f"📊 Độ tin cậy: {answer.confidence:.0%}")

        # Natural language answer
        output.append("\n" + "-" * 80)
        output.append("💬 TRẢ LỜI:")
        output.append("-" * 80)
        output.append(answer.answer)

        # Structured data
        if answer.structured_data:
            output.append("\n" + "-" * 80)
            output.append("📊 DỮ LIỆU CÓ CẤU TRÚC (JSON):")
            output.append("-" * 80)
            output.append(json.dumps(answer.structured_data, ensure_ascii=False, indent=2))

        # Sources
        output.append("\n" + "-" * 80)
        output.append(f"📚 NGUỒN THAM KHẢO ({len(answer.sources)} nguồn):")
        output.append("-" * 80)

        for i, source in enumerate(answer.sources, 1):
            output.append(f"\n[{i}] {source.thu_tuc_name}")
            output.append(f"    Mã thủ tục: {source.thu_tuc_code}")
            output.append(f"    Chunk ID: {source.chunk_id}")
            output.append(f"    Loại: {source.chunk_type}")
            output.append(f"    Độ liên quan: {source.relevance_score:.4f}")
            output.append(f"    Nội dung: {source.content_snippet}")

        # Footer
        output.append("\n" + "=" * 80)
        output.append(f"⏰ Thời gian: {answer.timestamp}")
        output.append("=" * 80)

        return "\n".join(output)

    def export_answer_json(self, answer: GeneratedAnswer, filepath: str):
        """
        Export answer to JSON file

        Args:
            answer: GeneratedAnswer object
            filepath: Output file path
        """
        # Convert to dict
        answer_dict = asdict(answer)

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(answer_dict, f, ensure_ascii=False, indent=2)

        print(f"✅ Answer exported to: {filepath}")


def test_answer_generator():
    """Test answer generator with sample data"""
    print("=" * 80)
    print("TEST ANSWER GENERATOR")
    print("=" * 80)

    # Initialize generator
    generator = OllamaAnswerGenerator(model_name="qwen3:8b")

    # Mock retrieval result
    question = "Đăng ký kết hôn cần giấy tờ gì?"
    intent = "documents"
    confidence = 0.75

    context = """
================================================================================
[CHUNK 1] THỦ TỤC: Đăng ký kết hôn
Mã: 1.013124
Lĩnh vực: Hộ tịch
Chunk type: child_documents
================================================================================

[OVERVIEW]
Thủ tục đăng ký kết hôn theo quy định của pháp luật Việt Nam.

[DETAILED INFO]
Hồ sơ bao gồm:
- Giấy tờ tùy thân (CMND/CCCD) của cả hai bên
- Giấy xác nhận tình trạng hôn nhân (nếu cần)
- Giấy khám sức khỏe tiền hôn nhân
- Đơn đăng ký kết hôn (theo mẫu)
Số lượng hồ sơ: 02 bộ
"""

    retrieved_chunks = [
        {
            "chunk_id": "chunk_001_child_001",
            "thu_tuc_id": "1.013124",
            "chunk_type": "child_documents",
            "content": context,
            "final_score": 0.85,
            "metadata": {
                "tên_thủ_tục": "Đăng ký kết hôn",
                "mã_thủ_tục": "1.013124",
                "lĩnh_vực": "Hộ tịch"
            }
        }
    ]

    metadata = {
        "num_parent_chunks": 2,
        "num_child_chunks": 3,
        "query_variations": ["Đăng ký kết hôn cần giấy tờ gì?"]
    }

    # Generate answer
    answer = generator.generate(
        question=question,
        intent=intent,
        context=context,
        retrieved_chunks=retrieved_chunks,
        confidence=confidence,
        metadata=metadata
    )

    # Display answer
    print(generator.format_answer_for_display(answer))

    # Export to JSON
    generator.export_answer_json(answer, "test_answer.json")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_answer_generator()
