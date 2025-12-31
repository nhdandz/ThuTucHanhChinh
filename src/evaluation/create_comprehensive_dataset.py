#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create Comprehensive Test Dataset
Expands from 4 to 50+ test cases covering all intents and difficulty levels
"""

import sys
from test_dataset import TestDatasetManager

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def create_comprehensive_dataset():
    """Create comprehensive test dataset with 50+ cases"""
    print("=" * 80)
    print("CREATING COMPREHENSIVE TEST DATASET (50+ CASES)")
    print("=" * 80)
    print()

    manager = TestDatasetManager()

    # ========================================================================
    # CATEGORY 1: DOCUMENTS (10 cases)
    # ========================================================================

    # EASY (4 cases)
    manager.add_test_case(
        test_id="DOC_EASY_001",
        category="documents",
        difficulty="easy",
        question="Đăng ký kết hôn cần giấy tờ gì?",
        natural_language_answer="""
Để đăng ký kết hôn, bạn cần chuẩn bị các giấy tờ sau:
1. Giấy tờ tùy thân (CMND/CCCD/Hộ chiếu) của cả hai bên - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính
3. Giấy khám sức khỏe tiền hôn nhân - 01 bản chính
4. Đơn đăng ký kết hôn - 01 bản
        """.strip(),
        key_facts=[
            "Giấy tờ tùy thân - 02 bản sao",
            "Giấy xác nhận tình trạng hôn nhân - 01 bản chính",
            "Giấy khám sức khỏe tiền hôn nhân - 01 bản chính",
            "Đơn đăng ký kết hôn - 01 bản"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Giấy tờ tùy thân",
                "Giấy xác nhận tình trạng hôn nhân",
                "Giấy khám sức khỏe tiền hôn nhân",
                "Đơn đăng ký kết hôn"
            ],
            "so_ban": {
                "Giấy tờ tùy thân": "02",
                "Giấy xác nhận tình trạng hôn nhân": "01",
                "Giấy khám sức khỏe tiền hôn nhân": "01",
                "Đơn đăng ký kết hôn": "01"
            }
        },
        required_aspects=["Danh sách giấy tờ"],
        source_procedure="Đăng ký kết hôn"
    )

    manager.add_test_case(
        test_id="DOC_EASY_002",
        category="documents",
        difficulty="easy",
        question="Cấp CCCD cần những giấy tờ nào?",
        natural_language_answer="""
Hồ sơ cấp CCCD gồm:
1. Giấy khai sinh - 01 bản sao
2. Sổ hộ khẩu hoặc giấy xác nhận cư trú - 01 bản sao
3. Ảnh 4x6 - 02 ảnh
        """.strip(),
        key_facts=[
            "Giấy khai sinh - 01 bản sao",
            "Sổ hộ khẩu - 01 bản sao",
            "Ảnh 4x6 - 02 ảnh"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Giấy khai sinh",
                "Sổ hộ khẩu",
                "Ảnh 4x6"
            ],
            "so_ban": {
                "Giấy khai sinh": "01",
                "Sổ hộ khẩu": "01",
                "Ảnh 4x6": "02"
            }
        },
        required_aspects=["Danh sách giấy tờ"],
        source_procedure="Cấp CCCD"
    )

    manager.add_test_case(
        test_id="DOC_EASY_003",
        category="documents",
        difficulty="easy",
        question="Đăng ký khai sinh cần hồ sơ gì?",
        natural_language_answer="""
Hồ sơ đăng ký khai sinh:
1. Giấy chứng sinh - 01 bản chính
2. Giấy tờ tùy thân của cha mẹ - 02 bản sao
3. Giấy chứng nhận kết hôn (nếu có) - 01 bản sao
        """.strip(),
        key_facts=[
            "Giấy chứng sinh - 01 bản chính",
            "Giấy tờ tùy thân của cha mẹ - 02 bản sao",
            "Giấy chứng nhận kết hôn - 01 bản sao"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Giấy chứng sinh",
                "Giấy tờ tùy thân của cha mẹ",
                "Giấy chứng nhận kết hôn"
            ],
            "so_ban": {
                "Giấy chứng sinh": "01 bản chính",
                "Giấy tờ tùy thân": "02 bản sao",
                "Giấy chứng nhận kết hôn": "01 bản sao"
            }
        },
        required_aspects=["Danh sách giấy tờ"],
        source_procedure="Đăng ký khai sinh"
    )

    manager.add_test_case(
        test_id="DOC_EASY_004",
        category="documents",
        difficulty="easy",
        question="Xin giấy phép xây dựng cần giấy tờ gì?",
        natural_language_answer="""
Hồ sơ xin giấy phép xây dựng:
1. Đơn xin cấp giấy phép - 01 bản
2. Bản vẽ thiết kế - 04 bản
3. Giấy chứng nhận quyền sử dụng đất - 01 bản sao
4. Giấy tờ tùy thân - 01 bản sao
        """.strip(),
        key_facts=[
            "Đơn xin cấp giấy phép - 01 bản",
            "Bản vẽ thiết kế - 04 bản",
            "Giấy chứng nhận quyền sử dụng đất - 01 bản sao",
            "Giấy tờ tùy thân - 01 bản sao"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Đơn xin cấp giấy phép",
                "Bản vẽ thiết kế",
                "Giấy chứng nhận quyền sử dụng đất",
                "Giấy tờ tùy thân"
            ],
            "so_ban": {
                "Đơn xin cấp giấy phép": "01",
                "Bản vẽ thiết kế": "04",
                "Giấy chứng nhận quyền sử dụng đất": "01",
                "Giấy tờ tùy thân": "01"
            }
        },
        required_aspects=["Danh sách giấy tờ"],
        source_procedure="Cấp giấy phép xây dựng"
    )

    # MEDIUM (3 cases)
    manager.add_test_case(
        test_id="DOC_MED_001",
        category="documents",
        difficulty="medium",
        question="Đăng ký kinh doanh cần hồ sơ gì và nộp mấy bộ?",
        natural_language_answer="""
Hồ sơ đăng ký kinh doanh:
1. Giấy đề nghị đăng ký doanh nghiệp - 01 bản
2. Điều lệ công ty - 01 bản
3. Danh sách thành viên - 01 bản
4. Bản sao CMND/CCCD của người đại diện - 01 bản
5. Giấy chứng nhận địa chỉ trụ sở - 01 bản

Số lượng hồ sơ: 01 bộ (nộp trực tuyến hoặc trực tiếp)
        """.strip(),
        key_facts=[
            "Giấy đề nghị đăng ký doanh nghiệp",
            "Điều lệ công ty",
            "Danh sách thành viên",
            "Bản sao CMND/CCCD",
            "Giấy chứng nhận địa chỉ trụ sở",
            "01 bộ hồ sơ"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Giấy đề nghị đăng ký doanh nghiệp",
                "Điều lệ công ty",
                "Danh sách thành viên",
                "Bản sao CMND/CCCD",
                "Giấy chứng nhận địa chỉ"
            ],
            "so_ban": {
                "Tổng số bộ hồ sơ": "01"
            }
        },
        required_aspects=["Danh sách giấy tờ", "Số lượng hồ sơ"],
        source_procedure="Đăng ký kinh doanh"
    )

    manager.add_test_case(
        test_id="DOC_MED_002",
        category="documents",
        difficulty="medium",
        question="Cấp hộ chiếu lần đầu cần giấy tờ gì và số lượng ảnh?",
        natural_language_answer="""
Hồ sơ cấp hộ chiếu lần đầu:
1. Tờ khai xin cấp hộ chiếu - 01 bản
2. CMND/CCCD - 01 bản sao
3. Giấy khai sinh - 01 bản sao
4. Sổ hộ khẩu - 01 bản sao
5. Ảnh 4x6 nền trắng - 04 ảnh

Lưu ý: Ảnh chụp không quá 06 tháng
        """.strip(),
        key_facts=[
            "Tờ khai xin cấp hộ chiếu",
            "CMND/CCCD - 01 bản sao",
            "Giấy khai sinh - 01 bản sao",
            "Sổ hộ khẩu - 01 bản sao",
            "Ảnh 4x6 nền trắng - 04 ảnh"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Tờ khai xin cấp hộ chiếu",
                "CMND/CCCD",
                "Giấy khai sinh",
                "Sổ hộ khẩu",
                "Ảnh 4x6"
            ],
            "so_ban": {
                "Tờ khai": "01",
                "CMND/CCCD": "01",
                "Giấy khai sinh": "01",
                "Sổ hộ khẩu": "01",
                "Ảnh 4x6": "04"
            }
        },
        required_aspects=["Danh sách giấy tờ", "Số lượng ảnh"],
        source_procedure="Cấp hộ chiếu"
    )

    manager.add_test_case(
        test_id="DOC_MED_003",
        category="documents",
        difficulty="medium",
        question="Đăng ký thường trú cần những giấy tờ gì và hồ sơ bản gốc hay bản sao?",
        natural_language_answer="""
Hồ sơ đăng ký thường trú:
1. Tờ khai đăng ký thường trú - 01 bản gốc
2. Sổ hộ khẩu cũ (nơi đi) - 01 bản gốc
3. Giấy chứng nhận nhà ở hoặc hợp đồng thuê - 01 bản sao
4. CMND/CCCD - 01 bản sao
5. Giấy xác nhận công tác (nếu có) - 01 bản chính

Lưu ý: Sổ hộ khẩu cũ phải nộp bản gốc để xóa
        """.strip(),
        key_facts=[
            "Tờ khai đăng ký thường trú - 01 bản gốc",
            "Sổ hộ khẩu cũ - 01 bản gốc",
            "Giấy chứng nhận nhà ở - 01 bản sao",
            "CMND/CCCD - 01 bản sao"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Tờ khai đăng ký thường trú (gốc)",
                "Sổ hộ khẩu cũ (gốc)",
                "Giấy chứng nhận nhà ở (sao)",
                "CMND/CCCD (sao)"
            ],
            "so_ban": {
                "Tờ khai": "01 gốc",
                "Sổ hộ khẩu cũ": "01 gốc",
                "Giấy chứng nhận nhà ở": "01 sao",
                "CMND/CCCD": "01 sao"
            }
        },
        required_aspects=["Danh sách giấy tờ", "Bản gốc hay bản sao"],
        source_procedure="Đăng ký thường trú"
    )

    # HARD (3 cases)
    manager.add_test_case(
        test_id="DOC_HARD_001",
        category="documents",
        difficulty="hard",
        question="Đăng ký kết hôn với người nước ngoài cần giấy tờ gì và có khác gì so với đăng ký thông thường?",
        natural_language_answer="""
Hồ sơ đăng ký kết hôn với người nước ngoài:

PHÍA VIỆT NAM:
1. Giấy tờ tùy thân (CMND/CCCD) - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính
3. Giấy khám sức khỏe - 01 bản chính

PHÍA NƯỚC NGOÀI:
1. Hộ chiếu còn hiệu lực - 02 bản sao có chứng thực
2. Giấy xác nhận tình trạng hôn nhân do cơ quan có thẩm quyền nước ngoài cấp - 01 bản chính có hợp pháp hóa lãnh sự
3. Giấy khám sức khỏe - 01 bản chính
4. Giấy phép cư trú tại Việt Nam (nếu đang ở VN) - 01 bản sao

KHÁC BIỆT:
- Giấy tờ nước ngoài phải dịch thuật và hợp pháp hóa lãnh sự
- Cần giấy xác nhận tình trạng hôn nhân do nước ngoài cấp
- Thời gian xử lý dài hơn (7-15 ngày)
        """.strip(),
        key_facts=[
            "Hộ chiếu người nước ngoài - 02 bản sao có chứng thực",
            "Giấy xác nhận hôn nhân nước ngoài - 01 bản chính có hợp pháp hóa lãnh sự",
            "Giấy tờ phải dịch thuật",
            "Cần hợp pháp hóa lãnh sự",
            "Thời gian xử lý 7-15 ngày"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "CMND/CCCD (phía VN)",
                "Hộ chiếu (phía nước ngoài)",
                "Giấy xác nhận hôn nhân (cả 2 phía)",
                "Giấy khám sức khỏe (cả 2 phía)"
            ],
            "so_ban": {
                "CMND/CCCD": "02",
                "Hộ chiếu": "02 (có chứng thực)",
                "Giấy xác nhận hôn nhân VN": "01",
                "Giấy xác nhận hôn nhân nước ngoài": "01 (có hợp pháp hóa)"
            },
            "yeu_cau_dac_biet": [
                "Dịch thuật giấy tờ nước ngoài",
                "Hợp pháp hóa lãnh sự",
                "Chứng thực bản sao"
            ]
        },
        required_aspects=["Danh sách giấy tờ", "Yêu cầu đặc biệt", "So sánh với đăng ký thông thường"],
        source_procedure="Đăng ký kết hôn với người nước ngoài"
    )

    manager.add_test_case(
        test_id="DOC_HARD_002",
        category="documents",
        difficulty="hard",
        question="Đăng ký doanh nghiệp 100% vốn nước ngoài cần hồ sơ gì và có yêu cầu đặc biệt nào?",
        natural_language_answer="""
Hồ sơ đăng ký doanh nghiệp 100% vốn nước ngoài:

1. Giấy đề nghị đăng ký doanh nghiệp - 01 bản
2. Điều lệ công ty - 02 bản
3. Danh sách thành viên/cổ đông sáng lập - 01 bản
4. Bản sao hợp lệ giấy tờ pháp lý của nhà đầu tư nước ngoài:
   - Cá nhân: Hộ chiếu - 01 bản sao có chứng thực
   - Tổ chức: Giấy chứng nhận đăng ký doanh nghiệp - 01 bản sao có hợp pháp hóa lãnh sự
5. Quyết định đầu tư hoặc Giấy chứng nhận đầu tư - 01 bản sao
6. Giấy chứng nhận địa chỉ trụ sở - 01 bản sao

YÊU CẦU ĐẶC BIỆT:
- Giấy tờ nước ngoài phải dịch sang tiếng Việt
- Hợp pháp hóa lãnh sự hoặc chứng nhận Apostille
- Vốn điều lệ tối thiểu theo ngành nghề
- Ngành nghề phải thuộc danh mục được phép đầu tư
- Cần Giấy chứng nhận đầu tư trước khi đăng ký kinh doanh
        """.strip(),
        key_facts=[
            "Giấy đề nghị đăng ký doanh nghiệp",
            "Điều lệ công ty - 02 bản",
            "Giấy tờ nhà đầu tư nước ngoài có hợp pháp hóa lãnh sự",
            "Quyết định đầu tư",
            "Giấy tờ phải dịch sang tiếng Việt",
            "Cần Giấy chứng nhận đầu tư trước"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Giấy đề nghị đăng ký doanh nghiệp",
                "Điều lệ công ty",
                "Danh sách thành viên",
                "Giấy tờ nhà đầu tư nước ngoài",
                "Quyết định đầu tư",
                "Giấy chứng nhận địa chỉ"
            ],
            "yeu_cau_dac_biet": [
                "Dịch thuật sang tiếng Việt",
                "Hợp pháp hóa lãnh sự/Apostille",
                "Vốn điều lệ tối thiểu",
                "Ngành nghề được phép",
                "Có Giấy chứng nhận đầu tư trước"
            ]
        },
        required_aspects=["Danh sách giấy tờ", "Yêu cầu đặc biệt", "Điều kiện tiên quyết"],
        source_procedure="Đăng ký doanh nghiệp FDI"
    )

    manager.add_test_case(
        test_id="DOC_HARD_003",
        category="documents",
        difficulty="hard",
        question="Cấp bằng lái xe ô tô B2 cần hồ sơ gì, có giấy tờ nào cần bản chính không?",
        natural_language_answer="""
Hồ sơ cấp bằng lái xe B2:

1. Đơn đề nghị cấp giấy phép lái xe - 01 bản (BẢN CHÍNH - viết tay hoặc đánh máy)
2. Giấy khám sức khỏe lái xe - 01 bản (BẢN CHÍNH - do cơ sở y tế có thẩm quyền cấp)
3. CMND/CCCD - 02 bản sao
4. Giấy chứng nhận tốt nghiệp khóa đào tạo lái xe B2 - 01 bản sao
5. Ảnh 3x4 nền trắng - 06 ảnh (chụp không quá 06 tháng)
6. Giấy xác nhận cư trú (nếu CCCD không còn hiệu lực) - 01 bản sao

GIẤY TỜ BẢN CHÍNH:
- Đơn đề nghị (phải là bản chính viết tay hoặc đánh máy)
- Giấy khám sức khỏe (phải là bản chính do bệnh viện cấp)

Các giấy tờ khác: nộp bản sao có chứng thực hoặc mang theo bản gốc để đối chiếu
        """.strip(),
        key_facts=[
            "Đơn đề nghị - 01 bản chính",
            "Giấy khám sức khỏe - 01 bản chính",
            "CMND/CCCD - 02 bản sao",
            "Giấy chứng nhận tốt nghiệp - 01 bản sao",
            "Ảnh 3x4 - 06 ảnh"
        ],
        structured_data={
            "ho_so_bao_gom": [
                "Đơn đề nghị (chính)",
                "Giấy khám sức khỏe (chính)",
                "CMND/CCCD (sao)",
                "Giấy chứng nhận tốt nghiệp (sao)",
                "Ảnh 3x4"
            ],
            "so_ban": {
                "Đơn đề nghị": "01 chính",
                "Giấy khám sức khỏe": "01 chính",
                "CMND/CCCD": "02 sao",
                "Giấy chứng nhận tốt nghiệp": "01 sao",
                "Ảnh 3x4": "06"
            },
            "ban_chinh": [
                "Đơn đề nghị cấp giấy phép lái xe",
                "Giấy khám sức khỏe lái xe"
            ]
        },
        required_aspects=["Danh sách giấy tờ", "Giấy tờ bản chính", "Số lượng"],
        source_procedure="Cấp bằng lái xe B2"
    )

    # ========================================================================
    # CATEGORY 2: TIMELINE (8 cases)
    # ========================================================================

    # EASY (3 cases)
    manager.add_test_case(
        test_id="TIME_EASY_001",
        category="timeline",
        difficulty="easy",
        question="Đăng ký kết hôn mất bao lâu?",
        natural_language_answer="""
Thời gian giải quyết: Trong ngày làm việc
Trường hợp đặc biệt: Không quá 03 ngày làm việc
        """.strip(),
        key_facts=[
            "Trong ngày làm việc",
            "Trường hợp đặc biệt không quá 03 ngày"
        ],
        structured_data={
            "thoi_han_giai_quyet": "Trong ngày làm việc",
            "thoi_han_dac_biet": "Không quá 03 ngày làm việc"
        },
        required_aspects=["Thời hạn giải quyết"],
        source_procedure="Đăng ký kết hôn"
    )

    manager.add_test_case(
        test_id="TIME_EASY_002",
        category="timeline",
        difficulty="easy",
        question="Cấp CCCD mất bao lâu?",
        natural_language_answer="""
Thời gian giải quyết:
- Trường hợp thường: 15 ngày làm việc
- Trường hợp cấp gấp: 05 ngày làm việc (phụ thu phí)
        """.strip(),
        key_facts=[
            "15 ngày làm việc (thường)",
            "05 ngày làm việc (cấp gấp)"
        ],
        structured_data={
            "thoi_han_giai_quyet": "15 ngày làm việc",
            "thoi_han_cap_gap": "05 ngày làm việc"
        },
        required_aspects=["Thời hạn giải quyết"],
        source_procedure="Cấp CCCD"
    )

    manager.add_test_case(
        test_id="TIME_EASY_003",
        category="timeline",
        difficulty="easy",
        question="Đăng ký khai sinh mất bao lâu?",
        natural_language_answer="""
Thời gian giải quyết: Trong ngày làm việc
Lưu ý: Tính từ khi hồ sơ hợp lệ
        """.strip(),
        key_facts=[
            "Trong ngày làm việc",
            "Tính từ khi hồ sơ hợp lệ"
        ],
        structured_data={
            "thoi_han_giai_quyet": "Trong ngày làm việc"
        },
        required_aspects=["Thời hạn giải quyết"],
        source_procedure="Đăng ký khai sinh"
    )

    # MEDIUM (3 cases)
    manager.add_test_case(
        test_id="TIME_MED_001",
        category="timeline",
        difficulty="medium",
        question="Đăng ký kinh doanh mất bao lâu và khi nào nhận được giấy phép?",
        natural_language_answer="""
Thời gian giải quyết: Không quá 03 ngày làm việc kể từ khi nhận đủ hồ sơ hợp lệ

Thời điểm nhận Giấy chứng nhận:
- Tại trụ sở: Sau 03 ngày làm việc
- Qua bưu điện: 05-07 ngày làm việc

Lưu ý: Có thể tra cứu online sau 02 ngày
        """.strip(),
        key_facts=[
            "Không quá 03 ngày làm việc",
            "Nhận tại trụ sở sau 03 ngày",
            "Qua bưu điện 05-07 ngày",
            "Tra cứu online sau 02 ngày"
        ],
        structured_data={
            "thoi_han_giai_quyet": "Không quá 03 ngày làm việc",
            "thoi_diem_nhan": {
                "tai_tru_so": "Sau 03 ngày làm việc",
                "qua_buu_dien": "05-07 ngày làm việc"
            },
            "tra_cuu_online": "Sau 02 ngày"
        },
        required_aspects=["Thời hạn giải quyết", "Thời điểm nhận giấy"],
        source_procedure="Đăng ký kinh doanh"
    )

    manager.add_test_case(
        test_id="TIME_MED_002",
        category="timeline",
        difficulty="medium",
        question="Cấp hộ chiếu mất bao lâu và có cấp gấp không?",
        natural_language_answer="""
Thời gian cấp hộ chiếu:
- Trường hợp thường: 07 ngày làm việc
- Trường hợp cấp gấp: 02 ngày làm việc (phí tăng 50%)
- Trường hợp đặc biệt cấp: Trong ngày (phí tăng 100%)

Điều kiện cấp gấp:
- Xuất cảnh khẩn cấp (chữa bệnh, tang lễ)
- Công tác đột xuất
- Có văn bản chứng minh lý do
        """.strip(),
        key_facts=[
            "07 ngày làm việc (thường)",
            "02 ngày làm việc (cấp gấp)",
            "Trong ngày (đặc biệt cấp)",
            "Phí tăng 50-100% nếu cấp gấp"
        ],
        structured_data={
            "thoi_han_giai_quyet": "07 ngày làm việc",
            "cap_gap": {
                "thoi_han": "02 ngày làm việc",
                "phi_tang": "50%"
            },
            "dac_biet_cap": {
                "thoi_han": "Trong ngày",
                "phi_tang": "100%"
            }
        },
        required_aspects=["Thời hạn giải quyết", "Cấp gấp", "Phí"],
        source_procedure="Cấp hộ chiếu"
    )

    manager.add_test_case(
        test_id="TIME_MED_003",
        category="timeline",
        difficulty="medium",
        question="Xin giấy phép xây dựng mất bao lâu và thời gian hiệu lực?",
        natural_language_answer="""
Thời gian xử lý hồ sơ:
- Nhà ở riêng lẻ: 20 ngày làm việc
- Công trình khác: 30 ngày làm việc

Thời gian hiệu lực giấy phép:
- Nhà ở riêng lẻ: 24 tháng
- Công trình khác: 36 tháng

Lưu ý: Nếu quá thời hạn chưa thi công, phải xin gia hạn
        """.strip(),
        key_facts=[
            "Nhà ở: 20 ngày làm việc",
            "Công trình khác: 30 ngày làm việc",
            "Hiệu lực nhà ở: 24 tháng",
            "Hiệu lực công trình khác: 36 tháng"
        ],
        structured_data={
            "thoi_han_giai_quyet": {
                "nha_o": "20 ngày làm việc",
                "cong_trinh_khac": "30 ngày làm việc"
            },
            "hieu_luc": {
                "nha_o": "24 tháng",
                "cong_trinh_khac": "36 tháng"
            }
        },
        required_aspects=["Thời hạn xử lý", "Thời gian hiệu lực"],
        source_procedure="Cấp giấy phép xây dựng"
    )

    # HARD (2 cases)
    manager.add_test_case(
        test_id="TIME_HARD_001",
        category="timeline",
        difficulty="hard",
        question="Thủ tục đăng ký đất đai mất bao lâu, tính từ lúc nào và có những mốc thời gian nào?",
        natural_language_answer="""
QUY TRÌNH VÀ THỜI GIAN:

1. Tiếp nhận hồ sơ: Ngày 0
   - Kiểm tra tính hợp lệ
   - Cấp giấy biên nhận

2. Thẩm định hồ sơ: Ngày 1-10
   - Kiểm tra pháp lý
   - Khảo sát thực địa (nếu cần)
   - Thông báo bổ sung (nếu thiếu)

3. Trình phê duyệt: Ngày 11-20
   - Lãnh đạo phê duyệt
   - Soạn thảo giấy chứng nhận

4. Cấp giấy: Ngày 21-30
   - In giấy chứng nhận
   - Thông báo đến nhận

TỔNG THỜI GIAN: 30 ngày làm việc (tính từ khi nhận đủ hồ sơ hợp lệ)

LƯU Ý:
- Nếu thiếu giấy tờ: tạm dừng, chờ bổ sung (không tính vào thời gian)
- Nếu cần khảo sát thực địa: có thể kéo dài thêm 05 ngày
- Trường hợp phức tạp: tối đa 50 ngày
        """.strip(),
        key_facts=[
            "Tổng 30 ngày làm việc",
            "Tính từ khi nhận đủ hồ sơ hợp lệ",
            "Tiếp nhận: Ngày 0",
            "Thẩm định: Ngày 1-10",
            "Phê duyệt: Ngày 11-20",
            "Cấp giấy: Ngày 21-30",
            "Trường hợp phức tạp: tối đa 50 ngày"
        ],
        structured_data={
            "thoi_han_giai_quyet": "30 ngày làm việc",
            "cac_moc_thoi_gian": [
                {"buoc": "Tiếp nhận", "ngay": "0"},
                {"buoc": "Thẩm định", "ngay": "1-10"},
                {"buoc": "Phê duyệt", "ngay": "11-20"},
                {"buoc": "Cấp giấy", "ngay": "21-30"}
            ],
            "truong_hop_dac_biet": {
                "phuc_tap": "Tối đa 50 ngày",
                "thieu_giay_to": "Tạm dừng chờ bổ sung"
            }
        },
        required_aspects=["Tổng thời gian", "Các mốc thời gian", "Điểm tính thời gian"],
        source_procedure="Đăng ký đất đai"
    )

    manager.add_test_case(
        test_id="TIME_HARD_002",
        category="timeline",
        difficulty="hard",
        question="Đăng ký bảo hộ nhãn hiệu mất bao lâu, qua những giai đoạn nào?",
        natural_language_answer="""
QUY TRÌNH VÀ THỜI GIAN ĐĂNG KÝ NHÃN HIỆU:

GIAI ĐOẠN 1: Thẩm định hình thức (1 tháng)
- Kiểm tra tính đầy đủ của hồ sơ
- Thông báo bổ sung nếu thiếu
- Cấp số đơn nếu hợp lệ

GIAI ĐOẠN 2: Công bố đơn (sau 2 tháng kể từ ngày nộp)
- Đăng công báo sáng chế
- Công khai thông tin đơn đăng ký

GIAI ĐOẠN 3: Thẩm định nội dung (6-9 tháng)
- Kiểm tra tính phân biệt
- Kiểm tra trùng lặp với nhãn hiệu khác
- Nghiên cứu pháp lý

GIAI ĐOẠN 4: Thông báo chấp nhận/từ chối (tháng 9-10)
- Thông báo kết quả thẩm định
- Yêu cầu sửa đổi (nếu có)

GIAI ĐOẠN 5: Cấp văn bằng (tháng 11-12)
- Nộp phí cấp bằng
- In và cấp Giấy chứng nhận

TỔNG THỜI GIAN: 9-12 tháng

CÓ THỂ KÉO DÀI NẾU:
- Có ý kiến phản đối: thêm 3-6 tháng
- Cần sửa đổi đơn: thêm 1-2 tháng
- Tranh chấp: thêm 6-12 tháng
        """.strip(),
        key_facts=[
            "Tổng 9-12 tháng",
            "Thẩm định hình thức: 1 tháng",
            "Công bố đơn: sau 2 tháng",
            "Thẩm định nội dung: 6-9 tháng",
            "Cấp văn bằng: tháng 11-12",
            "Có thể kéo dài nếu có phản đối"
        ],
        structured_data={
            "thoi_han_giai_quyet": "9-12 tháng",
            "cac_giai_doan": [
                {"giai_doan": "Thẩm định hình thức", "thoi_gian": "1 tháng"},
                {"giai_doan": "Công bố đơn", "thoi_gian": "Sau 2 tháng"},
                {"giai_doan": "Thẩm định nội dung", "thoi_gian": "6-9 tháng"},
                {"giai_doan": "Thông báo kết quả", "thoi_gian": "Tháng 9-10"},
                {"giai_doan": "Cấp văn bằng", "thoi_gian": "Tháng 11-12"}
            ],
            "truong_hop_keo_dai": {
                "co_phan_doi": "Thêm 3-6 tháng",
                "can_sua_doi": "Thêm 1-2 tháng",
                "tranh_chap": "Thêm 6-12 tháng"
            }
        },
        required_aspects=["Tổng thời gian", "Các giai đoạn", "Trường hợp kéo dài"],
        source_procedure="Đăng ký nhãn hiệu"
    )

    # ========================================================================
    # CATEGORY 3: REQUIREMENTS (8 cases)
    # ========================================================================

    # EASY (3 cases)
    manager.add_test_case(
        test_id="REQ_EASY_001",
        category="requirements",
        difficulty="easy",
        question="Đăng ký kết hôn cần đủ bao nhiêu tuổi?",
        natural_language_answer="""
Điều kiện tuổi đăng ký kết hôn:
- Nam: Từ đủ 20 tuổi trở lên
- Nữ: Từ đủ 18 tuổi trở lên
        """.strip(),
        key_facts=[
            "Nam từ đủ 20 tuổi",
            "Nữ từ đủ 18 tuổi"
        ],
        structured_data={
            "dieu_kien": {
                "tuoi_nam": "Từ đủ 20 tuổi",
                "tuoi_nu": "Từ đủ 18 tuổi"
            }
        },
        required_aspects=["Điều kiện tuổi"],
        source_procedure="Đăng ký kết hôn"
    )

    manager.add_test_case(
        test_id="REQ_EASY_002",
        category="requirements",
        difficulty="easy",
        question="Cấp CCCD cần đủ bao nhiêu tuổi?",
        natural_language_answer="""
Điều kiện tuổi cấp CCCD:
- Công dân Việt Nam từ đủ 14 tuổi trở lên
        """.strip(),
        key_facts=[
            "Từ đủ 14 tuổi trở lên"
        ],
        structured_data={
            "dieu_kien": {
                "tuoi": "Từ đủ 14 tuổi",
                "quoc_tich": "Công dân Việt Nam"
            }
        },
        required_aspects=["Điều kiện tuổi"],
        source_procedure="Cấp CCCD"
    )

    manager.add_test_case(
        test_id="REQ_EASY_003",
        category="requirements",
        difficulty="easy",
        question="Thi bằng lái xe B2 cần đủ tuổi nào?",
        natural_language_answer="""
Điều kiện tuổi thi bằng lái xe B2:
- Từ đủ 21 tuổi trở lên
- Không giới hạn độ tuổi tối đa (nếu đủ sức khỏe)
        """.strip(),
        key_facts=[
            "Từ đủ 21 tuổi trở lên",
            "Không giới hạn độ tuổi tối đa"
        ],
        structured_data={
            "dieu_kien": {
                "tuoi_toi_thieu": "Từ đủ 21 tuổi",
                "tuoi_toi_da": "Không giới hạn (nếu đủ sức khỏe)"
            }
        },
        required_aspects=["Điều kiện tuổi"],
        source_procedure="Cấp bằng lái xe B2"
    )

    # MEDIUM (3 cases)
    manager.add_test_case(
        test_id="REQ_MED_001",
        category="requirements",
        difficulty="medium",
        question="Đăng ký kinh doanh cần điều kiện gì?",
        natural_language_answer="""
Điều kiện đăng ký kinh doanh:

ĐỐI TƯỢNG:
- Công dân Việt Nam từ đủ 18 tuổi
- Có năng lực hành vi dân sự đầy đủ
- Tổ chức, cá nhân nước ngoài (nếu pháp luật cho phép)

YÊU CẦU:
- Tên doanh nghiệp chưa trùng với doanh nghiệp đã đăng ký
- Ngành nghề kinh doanh không thuộc danh mục cấm
- Có địa chỉ trụ sở chính tại Việt Nam
- Có vốn điều lệ phù hợp với quy định
        """.strip(),
        key_facts=[
            "Công dân từ 18 tuổi",
            "Có năng lực hành vi dân sự đầy đủ",
            "Tên doanh nghiệp chưa trùng",
            "Ngành nghề không cấm",
            "Có địa chỉ trụ sở tại VN"
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
        source_procedure="Đăng ký kinh doanh"
    )

    manager.add_test_case(
        test_id="REQ_MED_002",
        category="requirements",
        difficulty="medium",
        question="Xin giấy phép xây dựng nhà ở cần điều kiện gì?",
        natural_language_answer="""
Điều kiện xin giấy phép xây dựng nhà ở:

1. VỀ QUYỀN SỬ DỤNG ĐẤT:
   - Có giấy chứng nhận quyền sử dụng đất hợp pháp
   - Hoặc hợp đồng thuê đất dài hạn

2. VỀ QUY HOẠCH:
   - Đất ở đúng quy hoạch sử dụng đất
   - Không nằm trong khu vực cấm xây dựng

3. VỀ THIẾT KẾ:
   - Có bản vẽ thiết kế do kiến trúc sư có chứng chỉ hành nghề thiết kế
   - Thiết kế phù hợp với quy chuẩn xây dựng

4. VỀ CHỦ ĐẦU TƯ:
   - Là chủ sở hữu hoặc người được ủy quyền hợp pháp
        """.strip(),
        key_facts=[
            "Có giấy chứng nhận quyền sử dụng đất",
            "Đất đúng quy hoạch",
            "Có bản vẽ thiết kế hợp lệ",
            "Thiết kế phù hợp quy chuẩn",
            "Là chủ sở hữu hợp pháp"
        ],
        structured_data={
            "dieu_kien": [
                "Có giấy chứng nhận quyền sử dụng đất",
                "Đất đúng quy hoạch",
                "Không nằm trong khu vực cấm xây",
                "Có bản vẽ thiết kế hợp lệ",
                "Là chủ sở hữu hợp pháp"
            ]
        },
        required_aspects=["Điều kiện về đất", "Điều kiện về quy hoạch", "Điều kiện về thiết kế"],
        source_procedure="Cấp giấy phép xây dựng"
    )

    manager.add_test_case(
        test_id="REQ_MED_003",
        category="requirements",
        difficulty="medium",
        question="Đăng ký thường trú cần điều kiện gì?",
        natural_language_answer="""
Điều kiện đăng ký thường trú:

1. VỀ NGƯỜI ĐĂNG KÝ:
   - Là công dân Việt Nam
   - Có nơi cư trú ổn định

2. VỀ NƠI Ở:
   - Có chỗ ở hợp pháp (nhà riêng, thuê, ở nhờ)
   - Nếu thuê: hợp đồng thuê ≥6 tháng
   - Nếu ở nhờ: có giấy xác nhận của chủ nhà

3. VỀ PHÁP LÝ:
   - Không vi phạm quy định về cư trú
   - Không bị truy nã
        """.strip(),
        key_facts=[
            "Là công dân Việt Nam",
            "Có chỗ ở hợp pháp",
            "Hợp đồng thuê ≥6 tháng (nếu thuê)",
            "Không vi phạm quy định cư trú"
        ],
        structured_data={
            "dieu_kien": [
                "Công dân Việt Nam",
                "Có chỗ ở hợp pháp",
                "Hợp đồng thuê ≥6 tháng (nếu thuê)",
                "Không vi phạm quy định cư trú",
                "Không bị truy nã"
            ]
        },
        required_aspects=["Điều kiện về người", "Điều kiện về nơi ở"],
        source_procedure="Đăng ký thường trú"
    )

    # HARD (2 cases)
    manager.add_test_case(
        test_id="REQ_HARD_001",
        category="requirements",
        difficulty="hard",
        question="Mở công ty cổ phần cần điều kiện gì và khác gì so với công ty TNHH?",
        natural_language_answer="""
ĐIỀU KIỆN MỞ CÔNG TY CỔ PHẦN:

1. VỐN VÀ CỔ ĐÔNG:
   - Tối thiểu 03 cổ đông (tối đa không giới hạn)
   - Vốn điều lệ: Không quy định tối thiểu (trừ một số ngành đặc thù)
   - Vốn góp: Có thể bằng tiền, tài sản, quyền sử dụng đất, quyền sở hữu trí tuệ

2. TỔ CHỨC QUẢN LÝ:
   - Phải có Đại hội đồng cổ đông
   - Phải có Hội đồng quản trị (tối thiểu 03 thành viên)
   - Có Giám đốc/Tổng giám đốc

3. CỔ PHẦN VÀ CHỨNG KHOÁN:
   - Phải phát hành cổ phiếu
   - Có thể niêm yết trên sàn chứng khoán

SO SÁNH VỚI CÔNG TY TNHH:

CÔNG TY CỔ PHẦN:
- Tối thiểu 03 cổ đông
- Có thể chuyển nhượng cổ phần tự do
- Phát hành cổ phiếu
- Quản lý: ĐHĐCĐ + HĐQT + Giám đốc
- Phù hợp: Doanh nghiệp muốn huy động vốn lớn

CÔNG TY TNHH:
- Tối thiểu 01 thành viên (tối đa 50)
- Chuyển nhượng vốn phải thông qua thành viên khác
- Không phát hành cổ phiếu
- Quản lý: Hội đồng thành viên/Chủ tịch + Giám đốc
- Phù hợp: Doanh nghiệp gia đình, vừa và nhỏ
        """.strip(),
        key_facts=[
            "Tối thiểu 03 cổ đông",
            "Phải có ĐHĐCĐ và HĐQT",
            "Phát hành cổ phiếu",
            "Có thể niêm yết",
            "TNHH: tối thiểu 01 thành viên, tối đa 50",
            "TNHH: không phát hành cổ phiếu"
        ],
        structured_data={
            "cong_ty_co_phan": {
                "co_dong_toi_thieu": "03",
                "von_dieu_le": "Không quy định tối thiểu",
                "to_chuc_quan_ly": ["ĐHĐCĐ", "HĐQT", "Giám đốc"],
                "phat_hanh_co_phieu": "Có"
            },
            "cong_ty_tnhh": {
                "thanh_vien_toi_thieu": "01",
                "thanh_vien_toi_da": "50",
                "to_chuc_quan_ly": ["Hội đồng thành viên/Chủ tịch", "Giám đốc"],
                "phat_hanh_co_phieu": "Không"
            },
            "khac_biet_chinh": [
                "Số lượng thành viên/cổ đông",
                "Phát hành cổ phiếu",
                "Cấu trúc quản lý",
                "Khả năng chuyển nhượng vốn"
            ]
        },
        required_aspects=["Điều kiện công ty cổ phần", "So sánh với TNHH"],
        source_procedure="Đăng ký công ty cổ phần"
    )

    manager.add_test_case(
        test_id="REQ_HARD_002",
        category="requirements",
        difficulty="hard",
        question="Thành lập quỹ đầu tư chứng khoán cần điều kiện gì và quy trình như thế nào?",
        natural_language_answer="""
ĐIỀU KIỆN THÀNH LẬP QUỸ ĐẦU TƯ CHỨNG KHOÁN:

1. VỐN ĐIỀU LỆ:
   - Tối thiểu: 50 tỷ đồng
   - Phải góp đủ trong vòng 90 ngày kể từ ngày cấp giấy phép

2. CƠ CẤU TỔ CHỨC:
   - Công ty quản lý quỹ (phải có giấy phép kinh doanh chứng khoán)
   - Ngân hàng giám sát (phải được Ngân hàng Nhà nước chấp thuận)
   - Ban đại diện quỹ (tối thiểu 03 thành viên)

3. ĐIỀU KIỆN CỦA CÔNG TY QUẢN LÝ QUỸ:
   - Vốn điều lệ tối thiểu: 50 tỷ đồng
   - Có giấy phép kinh doanh quản lý quỹ
   - Có đội ngũ chuyên gia đầu tư (tối thiểu 03 người có chứng chỉ hành nghề)
   - Hệ thống quản lý rủi ro đạt chuẩn

4. ĐIỀU KIỆN KHÁC:
   - Phương án hoạt động khả thi
   - Điều lệ quỹ phù hợp quy định
   - Không vi phạm pháp luật chứng khoán trong 03 năm gần nhất

QUY TRÌNH:
1. Chuẩn bị hồ sơ đầy đủ
2. Nộp hồ sơ lên Ủy ban Chứng khoán Nhà nước
3. Thẩm định (60 ngày)
4. Cấp giấy phép hoặc từ chối (có văn bản)
5. Góp vốn điều lệ (trong vòng 90 ngày)
6. Công bố thông tin và bắt đầu hoạt động
        """.strip(),
        key_facts=[
            "Vốn điều lệ tối thiểu: 50 tỷ đồng",
            "Phải có công ty quản lý quỹ",
            "Phải có ngân hàng giám sát",
            "Ban đại diện quỹ: tối thiểu 03 thành viên",
            "Công ty quản lý: vốn tối thiểu 50 tỷ",
            "Thời gian thẩm định: 60 ngày"
        ],
        structured_data={
            "dieu_kien": {
                "von_dieu_le": "Tối thiểu 50 tỷ đồng",
                "cong_ty_quan_ly": {
                    "von_toi_thieu": "50 tỷ đồng",
                    "giay_phep": "Có",
                    "chuyen_gia": "Tối thiểu 03 người"
                },
                "ngan_hang_giam_sat": "Phải được NHNN chấp thuận",
                "ban_dai_dien": "Tối thiểu 03 thành viên"
            },
            "quy_trinh": [
                "Chuẩn bị hồ sơ",
                "Nộp hồ sơ lên UBCKNN",
                "Thẩm định (60 ngày)",
                "Cấp giấy phép",
                "Góp vốn (90 ngày)",
                "Công bố và hoạt động"
            ]
        },
        required_aspects=["Điều kiện về vốn", "Điều kiện về tổ chức", "Quy trình thành lập"],
        source_procedure="Thành lập quỹ đầu tư chứng khoán"
    )

    # ========================================================================
    # CATEGORY 4: PROCESS (8 cases)
    # ========================================================================

    # EASY (3 cases)
    manager.add_test_case(
        test_id="PROC_EASY_001",
        category="process",
        difficulty="easy",
        question="Quy trình đăng ký kết hôn như thế nào?",
        natural_language_answer="""
Quy trình đăng ký kết hôn:

Bước 1: Chuẩn bị hồ sơ
- Thu thập các giấy tờ cần thiết

Bước 2: Nộp hồ sơ
- Nộp tại UBND cấp xã nơi một trong hai bên thường trú

Bước 3: Tiếp nhận và kiểm tra
- Cán bộ kiểm tra hồ sơ
- Hẹn ngày đăng ký

Bước 4: Đăng ký kết hôn
- Hai bên đến ký xác nhận

Bước 5: Nhận giấy chứng nhận
- Nhận trong ngày hoặc theo hẹn
        """.strip(),
        key_facts=[
            "Chuẩn bị hồ sơ",
            "Nộp tại UBND cấp xã",
            "Kiểm tra và hẹn ngày",
            "Hai bên ký xác nhận",
            "Nhận giấy chứng nhận"
        ],
        structured_data={
            "cac_buoc": [
                {"buoc": 1, "mo_ta": "Chuẩn bị hồ sơ"},
                {"buoc": 2, "mo_ta": "Nộp hồ sơ tại UBND cấp xã"},
                {"buoc": 3, "mo_ta": "Tiếp nhận và kiểm tra"},
                {"buoc": 4, "mo_ta": "Đăng ký kết hôn - hai bên ký xác nhận"},
                {"buoc": 5, "mo_ta": "Nhận giấy chứng nhận"}
            ]
        },
        required_aspects=["Các bước thực hiện"],
        source_procedure="Đăng ký kết hôn"
    )

    manager.add_test_case(
        test_id="PROC_EASY_002",
        category="process",
        difficulty="easy",
        question="Làm CCCD gồm những bước nào?",
        natural_language_answer="""
Quy trình làm CCCD:

Bước 1: Chuẩn bị hồ sơ
- Giấy khai sinh, sổ hộ khẩu, ảnh 4x6

Bước 2: Nộp hồ sơ
- Nộp tại phòng Cảnh sát quản lý hành chính

Bước 3: Thu thập sinh trắc học
- Chụp ảnh, lấy vân tay, lấy mống mắt

Bước 4: Chờ xử lý
- Hệ thống xử lý và in thẻ

Bước 5: Nhận CCCD
- Nhận sau 15 ngày làm việc
        """.strip(),
        key_facts=[
            "Chuẩn bị hồ sơ",
            "Nộp tại phòng Cảnh sát",
            "Thu thập sinh trắc học",
            "Chờ 15 ngày",
            "Nhận CCCD"
        ],
        structured_data={
            "cac_buoc": [
                {"buoc": 1, "mo_ta": "Chuẩn bị hồ sơ"},
                {"buoc": 2, "mo_ta": "Nộp hồ sơ tại phòng Cảnh sát"},
                {"buoc": 3, "mo_ta": "Thu thập sinh trắc học"},
                {"buoc": 4, "mo_ta": "Chờ xử lý (15 ngày)"},
                {"buoc": 5, "mo_ta": "Nhận CCCD"}
            ]
        },
        required_aspects=["Các bước thực hiện"],
        source_procedure="Cấp CCCD"
    )

    manager.add_test_case(
        test_id="PROC_EASY_003",
        category="process",
        difficulty="easy",
        question="Quy trình đăng ký khai sinh gồm mấy bước?",
        natural_language_answer="""
Quy trình đăng ký khai sinh:

Bước 1: Chuẩn bị hồ sơ
- Giấy chứng sinh, giấy tờ của cha mẹ

Bước 2: Nộp hồ sơ
- Nộp tại UBND cấp xã nơi trẻ sinh ra hoặc nơi cha/mẹ thường trú

Bước 3: Kiểm tra hồ sơ
- Cán bộ tư pháp kiểm tra

Bước 4: Nhận giấy khai sinh
- Nhận trong ngày làm việc
        """.strip(),
        key_facts=[
            "Chuẩn bị hồ sơ",
            "Nộp tại UBND cấp xã",
            "Kiểm tra hồ sơ",
            "Nhận trong ngày"
        ],
        structured_data={
            "cac_buoc": [
                {"buoc": 1, "mo_ta": "Chuẩn bị hồ sơ"},
                {"buoc": 2, "mo_ta": "Nộp hồ sơ tại UBND cấp xã"},
                {"buoc": 3, "mo_ta": "Kiểm tra hồ sơ"},
                {"buoc": 4, "mo_ta": "Nhận giấy khai sinh trong ngày"}
            ]
        },
        required_aspects=["Các bước thực hiện"],
        source_procedure="Đăng ký khai sinh"
    )

    # MEDIUM (3 cases)
    manager.add_test_case(
        test_id="PROC_MED_001",
        category="process",
        difficulty="medium",
        question="Quy trình đăng ký kinh doanh online như thế nào?",
        natural_language_answer="""
Quy trình đăng ký kinh doanh online:

Bước 1: Truy cập hệ thống
- Vào trang dangkykinhdoanh.gov.vn
- Đăng ký tài khoản (nếu chưa có)

Bước 2: Đăng ký thông tin doanh nghiệp
- Điền thông tin: tên, địa chỉ, vốn, ngành nghề
- Tải lên Điều lệ công ty (PDF)

Bước 3: Nộp hồ sơ điện tử
- Kiểm tra thông tin
- Ký số (nếu có) hoặc nộp không ký số
- Thanh toán lệ phí online (qua VNPAY/MoMo)

Bước 4: Chờ xử lý
- Phòng Đăng ký kinh doanh thẩm định
- Thời gian: 03 ngày làm việc

Bước 5: Nhận kết quả
- Tải Giấy chứng nhận về (PDF có chữ ký điện tử)
- Hoặc nhận bản giấy tại trụ sở
        """.strip(),
        key_facts=[
            "Truy cập dangkykinhdoanh.gov.vn",
            "Điền thông tin và tải Điều lệ",
            "Thanh toán lệ phí online",
            "Chờ 03 ngày xử lý",
            "Tải giấy chứng nhận PDF"
        ],
        structured_data={
            "cac_buoc": [
                {"buoc": 1, "mo_ta": "Truy cập dangkykinhdoanh.gov.vn"},
                {"buoc": 2, "mo_ta": "Đăng ký thông tin doanh nghiệp"},
                {"buoc": 3, "mo_ta": "Nộp hồ sơ và thanh toán online"},
                {"buoc": 4, "mo_ta": "Chờ xử lý (03 ngày)"},
                {"buoc": 5, "mo_ta": "Tải giấy chứng nhận PDF"}
            ]
        },
        required_aspects=["Các bước thực hiện", "Nộp online", "Thanh toán"],
        source_procedure="Đăng ký kinh doanh online"
    )

    manager.add_test_case(
        test_id="PROC_MED_002",
        category="process",
        difficulty="medium",
        question="Quy trình xin giấy phép xây dựng gồm những bước nào và ai thẩm định?",
        natural_language_answer="""
Quy trình xin giấy phép xây dựng:

Bước 1: Chuẩn bị hồ sơ
- Đơn xin cấp phép
- Bản vẽ thiết kế (do kiến trúc sư có chứng chỉ thiết kế)
- Giấy tờ quyền sử dụng đất

Bước 2: Nộp hồ sơ
- Nộp tại Phòng Quản lý đô thị (UBND quận/huyện)
- Nhận biên nhận hồ sơ

Bước 3: Thẩm định
- Phòng Quản lý đô thị thẩm định:
  + Kiểm tra quyền sử dụng đất
  + Kiểm tra bản vẽ thiết kế
  + Kiểm tra quy hoạch
- Khảo sát thực địa (nếu cần)

Bước 4: Phê duyệt
- Lãnh đạo UBND quận/huyện phê duyệt
- Ký cấp giấy phép

Bước 5: Nhận giấy phép
- Nhận sau 20 ngày (nhà ở) hoặc 30 ngày (công trình khác)
        """.strip(),
        key_facts=[
            "Chuẩn bị hồ sơ với bản vẽ thiết kế",
            "Nộp tại Phòng Quản lý đô thị",
            "Phòng Quản lý đô thị thẩm định",
            "Lãnh đạo UBND phê duyệt",
            "Nhận sau 20-30 ngày"
        ],
        structured_data={
            "cac_buoc": [
                {"buoc": 1, "mo_ta": "Chuẩn bị hồ sơ"},
                {"buoc": 2, "mo_ta": "Nộp tại Phòng Quản lý đô thị"},
                {"buoc": 3, "mo_ta": "Phòng Quản lý đô thị thẩm định"},
                {"buoc": 4, "mo_ta": "Lãnh đạo UBND phê duyệt"},
                {"buoc": 5, "mo_ta": "Nhận giấy phép"}
            ],
            "don_vi_tham_dinh": "Phòng Quản lý đô thị",
            "don_vi_phe_duyet": "UBND quận/huyện"
        },
        required_aspects=["Các bước thực hiện", "Đơn vị thẩm định", "Đơn vị phê duyệt"],
        source_procedure="Cấp giấy phép xây dựng"
    )

    manager.add_test_case(
        test_id="PROC_MED_003",
        category="process",
        difficulty="medium",
        question="Làm hộ chiếu qua mấy bước và nộp hồ sơ ở đâu?",
        natural_language_answer="""
Quy trình làm hộ chiếu:

Bước 1: Đăng ký online (khuyến khích)
- Truy cập dichvucong.bocongan.gov.vn
- Điền thông tin và đặt lịch hẹn

Bước 2: Chuẩn bị hồ sơ
- Tờ khai, CMND/CCCD, giấy khai sinh, ảnh 4x6

Bước 3: Nộp hồ sơ
- Tại Phòng Quản lý xuất nhập cảnh Công an tỉnh/TP
- Hoặc Công an quận/huyện (nếu được ủy quyền)
- Nộp theo lịch hẹn (nếu đăng ký online)

Bước 4: Thu thập dữ liệu sinh trắc
- Chụp ảnh, lấy vân tay
- Thanh toán lệ phí

Bước 5: Chờ xử lý
- Hệ thống xử lý và in hộ chiếu
- Thời gian: 07 ngày (hoặc 02 ngày nếu cấp gấp)

Bước 6: Nhận hộ chiếu
- Nhận tại nơi nộp hồ sơ
- Hoặc nhận qua bưu điện (nếu đăng ký)
        """.strip(),
        key_facts=[
            "Đăng ký online trước (khuyến khích)",
            "Nộp tại Phòng Quản lý xuất nhập cảnh",
            "Thu thập sinh trắc và thanh toán",
            "Chờ 07 ngày (02 ngày nếu cấp gấp)",
            "Nhận tại nơi nộp hoặc qua bưu điện"
        ],
        structured_data={
            "cac_buoc": [
                {"buoc": 1, "mo_ta": "Đăng ký online và đặt lịch"},
                {"buoc": 2, "mo_ta": "Chuẩn bị hồ sơ"},
                {"buoc": 3, "mo_ta": "Nộp tại Phòng Quản lý xuất nhập cảnh"},
                {"buoc": 4, "mo_ta": "Thu thập sinh trắc và thanh toán"},
                {"buoc": 5, "mo_ta": "Chờ xử lý (07 ngày)"},
                {"buoc": 6, "mo_ta": "Nhận hộ chiếu"}
            ],
            "noi_nop": [
                "Phòng Quản lý xuất nhập cảnh Công an tỉnh/TP",
                "Công an quận/huyện (nếu được ủy quyền)"
            ]
        },
        required_aspects=["Các bước thực hiện", "Nơi nộp hồ sơ"],
        source_procedure="Cấp hộ chiếu"
    )

    # HARD (2 cases)
    manager.add_test_case(
        test_id="PROC_HARD_001",
        category="process",
        difficulty="hard",
        question="Quy trình đấu thầu dự án công như thế nào, qua những giai đoạn nào?",
        natural_language_answer="""
QUY TRÌNH ĐẤU THẦU DỰ ÁN CÔNG:

GIAI ĐOẠN 1: Chuẩn bị đấu thầu (30-45 ngày)
- Lập kế hoạch đấu thầu
- Lập hồ sơ mời thầu (HSMT)
- Phê duyệt HSMT

GIAI ĐOẠN 2: Tổ chức đấu thầu (30-60 ngày)
Bước 1: Thông báo mời thầu
- Đăng trên mạng đấu thầu quốc gia (muasamcong.mpi.gov.vn)
- Thời gian đăng: tối thiểu 15 ngày trước đóng thầu

Bước 2: Phát hành HSMT
- Nhà thầu mua HSMT
- Giải đáp thắc mắc (nếu có)

Bước 3: Nhận và mở thầu
- Nhận hồ sơ dự thầu
- Mở thầu công khai
- Lập biên bản mở thầu

GIAI ĐOẠN 3: Đánh giá hồ sơ dự thầu (30-45 ngày)
Bước 1: Đánh giá sơ bộ
- Kiểm tra tính hợp lệ
- Loại nhà thầu không đủ điều kiện

Bước 2: Đánh giá chi tiết
- Đánh giá kỹ thuật (70 điểm)
- Đánh giá tài chính (30 điểm)
- Xếp hạng nhà thầu

Bước 3: Thương thảo hợp đồng
- Thương thảo với nhà thầu xếp hạng nhất
- Nếu không thành, thương thảo với nhà thầu xếp hạng hai

GIAI ĐOẠN 4: Phê duyệt và ký kết (15-30 ngày)
- Trình kết quả đấu thầu
- Phê duyệt kết quả
- Thông báo kết quả
- Ký hợp đồng

TỔNG THỜI GIAN: 105-180 ngày (3.5-6 tháng)

CÁC BÊN THAM GIA:
- Bên mời thầu: Chủ đầu tư
- Tổ chuyên gia: Đánh giá hồ sơ
- Nhà thầu: Dự thầu
- Cơ quan phê duyệt: Phê duyệt kết quả
        """.strip(),
        key_facts=[
            "Giai đoạn 1: Chuẩn bị (30-45 ngày)",
            "Giai đoạn 2: Tổ chức đấu thầu (30-60 ngày)",
            "Giai đoạn 3: Đánh giá (30-45 ngày)",
            "Giai đoạn 4: Phê duyệt và ký kết (15-30 ngày)",
            "Tổng thời gian: 105-180 ngày",
            "Đăng trên muasamcong.mpi.gov.vn"
        ],
        structured_data={
            "cac_giai_doan": [
                {
                    "giai_doan": "Chuẩn bị đấu thầu",
                    "thoi_gian": "30-45 ngày",
                    "cong_viec": ["Lập kế hoạch", "Lập HSMT", "Phê duyệt HSMT"]
                },
                {
                    "giai_doan": "Tổ chức đấu thầu",
                    "thoi_gian": "30-60 ngày",
                    "cong_viec": ["Thông báo mời thầu", "Phát hành HSMT", "Mở thầu"]
                },
                {
                    "giai_doan": "Đánh giá",
                    "thoi_gian": "30-45 ngày",
                    "cong_viec": ["Đánh giá sơ bộ", "Đánh giá chi tiết", "Thương thảo"]
                },
                {
                    "giai_doan": "Phê duyệt và ký kết",
                    "thoi_gian": "15-30 ngày",
                    "cong_viec": ["Phê duyệt", "Thông báo", "Ký hợp đồng"]
                }
            ],
            "tong_thoi_gian": "105-180 ngày"
        },
        required_aspects=["Các giai đoạn", "Thời gian từng giai đoạn", "Các bên tham gia"],
        source_procedure="Đấu thầu dự án công"
    )

    manager.add_test_case(
        test_id="PROC_HARD_002",
        category="process",
        difficulty="hard",
        question="Quy trình cấp phép đầu tư FDI như thế nào và phải làm việc với những cơ quan nào?",
        natural_language_answer="""
QUY TRÌNH CẤP GIẤY CHỨNG NHẬN ĐẦU TƯ FDI:

GIAI ĐOẠN 1: Chuẩn bị dự án (60-90 ngày)
Bước 1: Nghiên cứu pháp lý
- Kiểm tra ngành nghề được phép đầu tư
- Nghiên cứu ưu đãi đầu tư (nếu có)

Bước 2: Lựa chọn địa điểm
- Tìm địa điểm đầu tư
- Làm việc với UBND tỉnh/thành phố

Bước 3: Lập hồ sơ dự án
- Đề án đầu tư
- Giấy tờ pháp lý nhà đầu tư (hợp pháp hóa lãnh sự)
- Báo cáo nghiên cứu khả thi

GIAI ĐOẠN 2: Nộp hồ sơ và thẩm định (30-45 ngày)
Bước 1: Nộp hồ sơ
- Nộp tại Sở Kế hoạch và Đầu tư tỉnh/thành phố
- Hoặc Ban quản lý KCN/KCX (nếu đầu tư trong KCN)

Bước 2: Thẩm định liên ngành
- Sở Kế hoạch và Đầu tư: Chủ trì
- Sở Tài nguyên và Môi trường: Thẩm định đất đai, môi trường
- Sở Xây dựng: Thẩm định quy hoạch xây dựng
- Sở Tài chính: Thẩm định vốn đầu tư
- Các sở ngành khác (tùy ngành nghề)

Bước 3: Họp hội đồng thẩm định
- Tổng hợp ý kiến các sở ngành
- Đề xuất cấp hoặc không cấp

GIAI ĐOẠN 3: Phê duyệt (5-15 ngày)
- UBND tỉnh/thành phố phê duyệt
- Hoặc Thủ tướng Chính phủ (nếu dự án lớn ≥15,000 tỷ đồng)

GIAI ĐOẠN 4: Cấp giấy chứng nhận đầu tư (5-10 ngày)
- In Giấy chứng nhận đầu tư
- Thông báo nhà đầu tư đến nhận

GIAI ĐOẠN 5: Sau cấp phép (30-60 ngày)
- Thuê đất/Nhận quyền sử dụng đất
- Làm thủ tục môi trường (Đánh giá tác động môi trường)
- Đăng ký kinh doanh tại Sở Kế hoạch và Đầu tư

TỔNG THỜI GIAN: 130-220 ngày (4-7 tháng)

CÁC CƠ QUAN PHẢI LÀM VIỆC:
1. Sở Kế hoạch và Đầu tư (chủ đạo)
2. UBND tỉnh/thành phố
3. Sở Tài nguyên và Môi trường
4. Sở Xây dựng
5. Sở Tài chính
6. Ban quản lý KCN (nếu trong KCN)
7. Thủ tướng Chính phủ (nếu dự án lớn)
        """.strip(),
        key_facts=[
            "Giai đoạn 1: Chuẩn bị (60-90 ngày)",
            "Giai đoạn 2: Thẩm định (30-45 ngày)",
            "Giai đoạn 3: Phê duyệt (5-15 ngày)",
            "Giai đoạn 4: Cấp giấy (5-10 ngày)",
            "Giai đoạn 5: Sau cấp phép (30-60 ngày)",
            "Tổng: 130-220 ngày",
            "Nộp tại Sở Kế hoạch và Đầu tư",
            "Thẩm định liên ngành",
            "UBND tỉnh hoặc Thủ tướng phê duyệt"
        ],
        structured_data={
            "cac_giai_doan": [
                {
                    "giai_doan": "Chuẩn bị dự án",
                    "thoi_gian": "60-90 ngày",
                    "cong_viec": ["Nghiên cứu pháp lý", "Chọn địa điểm", "Lập hồ sơ"]
                },
                {
                    "giai_doan": "Nộp và thẩm định",
                    "thoi_gian": "30-45 ngày",
                    "cong_viec": ["Nộp hồ sơ", "Thẩm định liên ngành", "Họp hội đồng"]
                },
                {
                    "giai_doan": "Phê duyệt",
                    "thoi_gian": "5-15 ngày",
                    "nguoi_phe_duyet": "UBND tỉnh hoặc Thủ tướng"
                },
                {
                    "giai_doan": "Cấp giấy",
                    "thoi_gian": "5-10 ngày"
                },
                {
                    "giai_doan": "Sau cấp phép",
                    "thoi_gian": "30-60 ngày",
                    "cong_viec": ["Thuê đất", "Đánh giá môi trường", "Đăng ký kinh doanh"]
                }
            ],
            "cac_co_quan": [
                "Sở Kế hoạch và Đầu tư",
                "UBND tỉnh/thành phố",
                "Sở Tài nguyên và Môi trường",
                "Sở Xây dựng",
                "Sở Tài chính",
                "Ban quản lý KCN",
                "Thủ tướng Chính phủ (dự án lớn)"
            ]
        },
        required_aspects=["Các giai đoạn", "Thời gian", "Cơ quan liên quan"],
        source_procedure="Cấp giấy chứng nhận đầu tư FDI"
    )

    # ========================================================================
    # CATEGORY 5: LEGAL (6 cases)
    # ========================================================================

    # EASY (2 cases)
    manager.add_test_case(
        test_id="LEGAL_EASY_001",
        category="legal",
        difficulty="easy",
        question="Đăng ký kết hôn căn cứ vào văn bản nào?",
        natural_language_answer="""
Căn cứ pháp lý:
- Luật Hôn nhân và Gia đình 2014
- Nghị định 126/2014/NĐ-CP hướng dẫn thi hành Luật Hôn nhân và Gia đình
        """.strip(),
        key_facts=[
            "Luật Hôn nhân và Gia đình 2014",
            "Nghị định 126/2014/NĐ-CP"
        ],
        structured_data={
            "can_cu_phap_ly": [
                "Luật Hôn nhân và Gia đình 2014",
                "Nghị định 126/2014/NĐ-CP"
            ]
        },
        required_aspects=["Căn cứ pháp lý"],
        source_procedure="Đăng ký kết hôn"
    )

    manager.add_test_case(
        test_id="LEGAL_EASY_002",
        category="legal",
        difficulty="easy",
        question="Cấp CCCD dựa trên luật nào?",
        natural_language_answer="""
Căn cứ pháp lý:
- Luật Căn cước công dân 2014
- Nghị định 137/2015/NĐ-CP quy định chi tiết thi hành Luật Căn cước công dân
        """.strip(),
        key_facts=[
            "Luật Căn cước công dân 2014",
            "Nghị định 137/2015/NĐ-CP"
        ],
        structured_data={
            "can_cu_phap_ly": [
                "Luật Căn cước công dân 2014",
                "Nghị định 137/2015/NĐ-CP"
            ]
        },
        required_aspects=["Căn cứ pháp lý"],
        source_procedure="Cấp CCCD"
    )

    # MEDIUM (2 cases)
    manager.add_test_case(
        test_id="LEGAL_MED_001",
        category="legal",
        difficulty="medium",
        question="Đăng ký kinh doanh căn cứ vào những văn bản pháp luật nào?",
        natural_language_answer="""
Căn cứ pháp lý:
- Luật Doanh nghiệp 2020
- Nghị định 01/2021/NĐ-CP quy định chi tiết thi hành một số điều của Luật Doanh nghiệp
- Thông tư 01/2021/TT-BKHĐT hướng dẫn về đăng ký doanh nghiệp
        """.strip(),
        key_facts=[
            "Luật Doanh nghiệp 2020",
            "Nghị định 01/2021/NĐ-CP",
            "Thông tư 01/2021/TT-BKHĐT"
        ],
        structured_data={
            "can_cu_phap_ly": [
                "Luật Doanh nghiệp 2020",
                "Nghị định 01/2021/NĐ-CP",
                "Thông tư 01/2021/TT-BKHĐT"
            ]
        },
        required_aspects=["Căn cứ pháp lý"],
        source_procedure="Đăng ký kinh doanh"
    )

    manager.add_test_case(
        test_id="LEGAL_MED_002",
        category="legal",
        difficulty="medium",
        question="Cấp giấy phép xây dựng dựa trên quy định nào?",
        natural_language_answer="""
Căn cứ pháp lý:
- Luật Xây dựng 2014 (sửa đổi 2020)
- Nghị định 15/2021/NĐ-CP quy định về quản lý dự án đầu tư xây dựng
- Thông tư 03/2021/TT-BXD hướng dẫn cấp giấy phép xây dựng
        """.strip(),
        key_facts=[
            "Luật Xây dựng 2014 (sửa đổi 2020)",
            "Nghị định 15/2021/NĐ-CP",
            "Thông tư 03/2021/TT-BXD"
        ],
        structured_data={
            "can_cu_phap_ly": [
                "Luật Xây dựng 2014 (sửa đổi 2020)",
                "Nghị định 15/2021/NĐ-CP",
                "Thông tư 03/2021/TT-BXD"
            ]
        },
        required_aspects=["Căn cứ pháp lý"],
        source_procedure="Cấp giấy phép xây dựng"
    )

    # HARD (2 cases)
    manager.add_test_case(
        test_id="LEGAL_HARD_001",
        category="legal",
        difficulty="hard",
        question="Đầu tư FDI phải tuân thủ những văn bản pháp luật nào và có văn bản quốc tế không?",
        natural_language_answer="""
CĂN CỨ PHÁP LÝ:

VĂN BẢN TRONG NƯỚC:
1. Luật Đầu tư 2020
2. Luật Doanh nghiệp 2020
3. Nghị định 31/2021/NĐ-CP quy định chi tiết Luật Đầu tư
4. Nghị định 01/2021/NĐ-CP quy định chi tiết Luật Doanh nghiệp
5. Thông tư 03/2021/TT-BKHĐT hướng dẫn thủ tục đầu tư

VĂN BẢN QUỐC TẾ (nếu có):
- Hiệp định thương mại tự do (FTA) mà Việt Nam ký kết:
  + CPTPP (Hiệp định Đối tác Toàn diện và Tiến bộ xuyên Thái Bình Dương)
  + EVFTA (Hiệp định Thương mại tự do Việt Nam - EU)
  + RCEP (Hiệp định Đối tác Kinh tế Toàn diện Khu vực)
- Hiệp định đầu tư song phương (BIT) với nước của nhà đầu tư

LƯU Ý:
- Nếu có xung đột, ưu tiên áp dụng điều ước quốc tế mà Việt Nam ký kết
- Nhà đầu tư thuộc nước thành viên FTA có thể hưởng ưu đãi đặc biệt
        """.strip(),
        key_facts=[
            "Luật Đầu tư 2020",
            "Luật Doanh nghiệp 2020",
            "Nghị định 31/2021/NĐ-CP",
            "CPTPP, EVFTA, RCEP",
            "Hiệp định đầu tư song phương",
            "Ưu tiên điều ước quốc tế nếu xung đột"
        ],
        structured_data={
            "can_cu_phap_ly": {
                "trong_nuoc": [
                    "Luật Đầu tư 2020",
                    "Luật Doanh nghiệp 2020",
                    "Nghị định 31/2021/NĐ-CP",
                    "Nghị định 01/2021/NĐ-CP",
                    "Thông tư 03/2021/TT-BKHĐT"
                ],
                "quoc_te": [
                    "CPTPP",
                    "EVFTA",
                    "RCEP",
                    "Hiệp định đầu tư song phương (BIT)"
                ]
            }
        },
        required_aspects=["Căn cứ pháp lý trong nước", "Văn bản quốc tế"],
        source_procedure="Đầu tư FDI"
    )

    manager.add_test_case(
        test_id="LEGAL_HARD_002",
        category="legal",
        difficulty="hard",
        question="Đấu thầu dự án công căn cứ vào những quy định nào và có quy định về chống tham nhũng không?",
        natural_language_answer="""
CĂN CỨ PHÁP LÝ ĐẤU THẦU:

VĂN BẢN VỀ ĐẤU THẦU:
1. Luật Đấu thầu 2013 (sửa đổi 2016)
2. Nghị định 63/2014/NĐ-CP quy định chi tiết Luật Đấu thầu
3. Thông tư 03/2015/TT-BKHĐT hướng dẫn lựa chọn nhà thầu

VĂN BẢN VỀ CHỐNG THAM NHŨNG:
1. Luật Phòng, chống tham nhũng 2018
2. Nghị định 59/2019/NĐ-CP quy định xử lý vi phạm về đấu thầu
3. Thông tư 08/2019/TT-TTCP hướng dẫn phát hiện và xử lý hành vi tham nhũng trong đấu thầu

QUY ĐỊNH ĐẶC BIỆT:
- Cán bộ tham gia đấu thầu phải cam kết không nhận hối lộ
- Nhà thầu phải cam kết không hối lộ
- Vi phạm: bị đưa vào danh sách đen, không được tham gia đấu thầu 1-3 năm
- Tham nhũng nghiêm trọng: truy cứu trách nhiệm hình sự theo Bộ luật Hình sự 2015

CƠ CHẾ GIÁM SÁT:
- Thanh tra Chính phủ
- Kiểm toán Nhà nước
- Cơ quan điều tra (nếu có dấu hiệu phạm tội)
        """.strip(),
        key_facts=[
            "Luật Đấu thầu 2013 (sửa đổi 2016)",
            "Luật Phòng, chống tham nhũng 2018",
            "Nghị định 63/2014/NĐ-CP",
            "Phải cam kết không tham nhũng",
            "Vi phạm: đưa vào danh sách đen 1-3 năm",
            "Giám sát bởi Thanh tra và Kiểm toán"
        ],
        structured_data={
            "can_cu_phap_ly": {
                "ve_dau_thau": [
                    "Luật Đấu thầu 2013 (sửa đổi 2016)",
                    "Nghị định 63/2014/NĐ-CP",
                    "Thông tư 03/2015/TT-BKHĐT"
                ],
                "ve_chong_tham_nhung": [
                    "Luật Phòng, chống tham nhũng 2018",
                    "Nghị định 59/2019/NĐ-CP",
                    "Thông tư 08/2019/TT-TTCP",
                    "Bộ luật Hình sự 2015"
                ]
            },
            "co_che_giam_sat": [
                "Thanh tra Chính phủ",
                "Kiểm toán Nhà nước",
                "Cơ quan điều tra"
            ]
        },
        required_aspects=["Căn cứ pháp lý đấu thầu", "Quy định chống tham nhũng", "Cơ chế giám sát"],
        source_procedure="Đấu thầu dự án công"
    )

    # ========================================================================
    # CATEGORY 6: FEES (8 cases)
    # ========================================================================

    # EASY (3 cases)
    manager.add_test_case(
        test_id="FEE_EASY_001",
        category="fees",
        difficulty="easy",
        question="Đăng ký kết hôn mất bao nhiêu tiền?",
        natural_language_answer="""
Lệ phí đăng ký kết hôn:
- Miễn phí (theo quy định tại Nghị định 167/2017/NĐ-CP)

Lưu ý: Không phải nộp lệ phí đăng ký kết hôn
        """.strip(),
        key_facts=[
            "Miễn phí",
            "Không phải nộp lệ phí"
        ],
        structured_data={
            "le_phi": "0 đồng (miễn phí)"
        },
        required_aspects=["Lệ phí"],
        source_procedure="Đăng ký kết hôn"
    )

    manager.add_test_case(
        test_id="FEE_EASY_002",
        category="fees",
        difficulty="easy",
        question="Đăng ký khai sinh tốn bao nhiêu tiền?",
        natural_language_answer="""
Lệ phí đăng ký khai sinh:
- Miễn phí (theo quy định tại Nghị định 167/2017/NĐ-CP)

Lưu ý: Đăng ký khai sinh trong 60 ngày kể từ ngày sinh không phải nộp phí
        """.strip(),
        key_facts=[
            "Miễn phí",
            "Đăng ký trong 60 ngày không phí"
        ],
        structured_data={
            "le_phi": "0 đồng (miễn phí nếu trong 60 ngày)"
        },
        required_aspects=["Lệ phí"],
        source_procedure="Đăng ký khai sinh"
    )

    manager.add_test_case(
        test_id="FEE_EASY_003",
        category="fees",
        difficulty="easy",
        question="Cấp CCCD lần đầu mất bao nhiêu tiền?",
        natural_language_answer="""
Lệ phí cấp CCCD lần đầu:
- Miễn phí (theo quy định tại Nghị định 167/2017/NĐ-CP)

Lưu ý: Cấp lần đầu cho công dân từ 14 tuổi không phải nộp phí
        """.strip(),
        key_facts=[
            "Miễn phí",
            "Cấp lần đầu không phí"
        ],
        structured_data={
            "le_phi": "0 đồng (miễn phí lần đầu)"
        },
        required_aspects=["Lệ phí"],
        source_procedure="Cấp CCCD"
    )

    # MEDIUM (3 cases)
    manager.add_test_case(
        test_id="FEE_MED_001",
        category="fees",
        difficulty="medium",
        question="Đăng ký kinh doanh mất bao nhiêu tiền và cách thanh toán?",
        natural_language_answer="""
Lệ phí đăng ký kinh doanh:
- Đăng ký lần đầu: 500,000 đồng
- Cấp bản sao Giấy chứng nhận: 50,000 đồng/bản

Cách thanh toán:
- Nộp trực tiếp: Nộp tiền mặt tại quầy thu ngân
- Nộp online: Chuyển khoản qua VNPAY, MoMo, hoặc thẻ ATM
- Nộp qua ngân hàng: Chuyển khoản vào tài khoản Kho bạc Nhà nước

Lưu ý: Thanh toán online được giảm 20% lệ phí (còn 400,000 đồng)
        """.strip(),
        key_facts=[
            "Lệ phí: 500,000 đồng",
            "Bản sao: 50,000 đồng",
            "Thanh toán online giảm 20%",
            "Có thể nộp qua VNPAY, MoMo"
        ],
        structured_data={
            "le_phi": {
                "dang_ky_lan_dau": "500,000 đồng",
                "ban_sao": "50,000 đồng/bản",
                "online_giam": "20% (còn 400,000 đồng)"
            },
            "cach_thanh_toan": [
                "Tiền mặt tại quầy",
                "Online qua VNPAY/MoMo",
                "Chuyển khoản ngân hàng"
            ]
        },
        required_aspects=["Lệ phí", "Cách thanh toán"],
        source_procedure="Đăng ký kinh doanh"
    )

    manager.add_test_case(
        test_id="FEE_MED_002",
        category="fees",
        difficulty="medium",
        question="Cấp hộ chiếu mất bao nhiêu tiền, cấp gấp thì sao?",
        natural_language_answer="""
Lệ phí cấp hộ chiếu:

TRƯỜNG HỢP THƯỜNG (hiệu lực 10 năm):
- Lệ phí: 200,000 đồng
- Thời gian: 07 ngày làm việc

CẤP GẤP (02 ngày làm việc):
- Lệ phí: 300,000 đồng (tăng 50%)
- Thời gian: 02 ngày làm việc

ĐẶC BIỆT CẤP (trong ngày):
- Lệ phí: 400,000 đồng (tăng 100%)
- Thời gian: Trong ngày làm việc
- Điều kiện: Có lý do chính đáng (bệnh, tang)

Lưu ý: Hộ chiếu 5 năm (cho trẻ em): 100,000 đồng
        """.strip(),
        key_facts=[
            "Thường: 200,000 đồng (10 năm)",
            "Cấp gấp: 300,000 đồng (02 ngày)",
            "Đặc biệt: 400,000 đồng (trong ngày)",
            "Trẻ em (5 năm): 100,000 đồng"
        ],
        structured_data={
            "le_phi": {
                "thuong": {
                    "phi": "200,000 đồng",
                    "thoi_gian": "07 ngày",
                    "hieu_luc": "10 năm"
                },
                "cap_gap": {
                    "phi": "300,000 đồng",
                    "thoi_gian": "02 ngày"
                },
                "dac_biet": {
                    "phi": "400,000 đồng",
                    "thoi_gian": "Trong ngày"
                },
                "tre_em": {
                    "phi": "100,000 đồng",
                    "hieu_luc": "5 năm"
                }
            }
        },
        required_aspects=["Lệ phí thường", "Lệ phí cấp gấp"],
        source_procedure="Cấp hộ chiếu"
    )

    manager.add_test_case(
        test_id="FEE_MED_003",
        category="fees",
        difficulty="medium",
        question="Xin giấy phép xây dựng nhà ở mất bao nhiêu tiền?",
        natural_language_answer="""
Lệ phí cấp giấy phép xây dựng:

NHÀ Ở RIÊNG LẺ:
- Diện tích ≤ 150m²: 150,000 đồng
- Diện tích 150-300m²: 300,000 đồng
- Diện tích > 300m²: 500,000 đồng

CÔNG TRÌNH KHÁC:
- Theo giá trị công trình (0.05% giá trị)
- Tối thiểu: 500,000 đồng
- Tối đa: 10,000,000 đồng

PHÍ THẨM ĐỊNH THIẾT KẾ (nếu cần):
- 200,000 - 1,000,000 đồng tùy quy mô
        """.strip(),
        key_facts=[
            "Nhà ≤150m²: 150,000 đồng",
            "Nhà 150-300m²: 300,000 đồng",
            "Nhà >300m²: 500,000 đồng",
            "Phí thẩm định: 200,000-1,000,000 đồng"
        ],
        structured_data={
            "le_phi": {
                "nha_o_rieng_le": {
                    "≤150m²": "150,000 đồng",
                    "150-300m²": "300,000 đồng",
                    ">300m²": "500,000 đồng"
                },
                "cong_trinh_khac": "0.05% giá trị (tối thiểu 500,000, tối đa 10,000,000)",
                "tham_dinh_thiet_ke": "200,000 - 1,000,000 đồng"
            }
        },
        required_aspects=["Lệ phí theo diện tích", "Phí thẩm định"],
        source_procedure="Cấp giấy phép xây dựng"
    )

    # HARD (2 cases)
    manager.add_test_case(
        test_id="FEE_HARD_001",
        category="fees",
        difficulty="hard",
        question="Cấp bằng lái xe B2 mất tổng bao nhiêu tiền, kể cả học phí?",
        natural_language_answer="""
TỔNG CHI PHÍ HỌC VÀ THI BẰNG LÁI XE B2:

1. HỌC PHÍ TRUNG TÂM ĐÀO TẠO:
   - Học lý thuyết: 1,500,000 - 2,000,000 đồng
   - Học thực hành: 6,000,000 - 8,000,000 đồng
   - Tổng học phí: 7,500,000 - 10,000,000 đồng

2. PHÍ THI:
   - Lý thuyết: 100,000 đồng
   - Sa hình: 100,000 đồng
   - Thực hành đường trường: 150,000 đồng
   - Tổng phí thi: 350,000 đồng

3. PHÍ CẤP BẰNG:
   - Lệ phí cấp bằng: 135,000 đồng
   - Ảnh, khám sức khỏe: 150,000 đồng

4. PHÍ TÁI THI (nếu trượt):
   - Thi lại lý thuyết: 100,000 đồng/lần
   - Thi lại thực hành: 150,000 đồng/lần

TỔNG CHI PHÍ: 8,135,000 - 10,635,000 đồng (nếu thi đỗ ngay)

LƯU Ý:
- Giá có thể khác nhau tùy trung tâm đào tạo
- Các khoản phí thi và cấp bằng do Nhà nước quy định (cố định)
- Học phí do trung tâm tự định giá (cạnh tranh)
        """.strip(),
        key_facts=[
            "Học phí: 7,500,000 - 10,000,000 đồng",
            "Phí thi: 350,000 đồng",
            "Phí cấp bằng: 135,000 đồng",
            "Tổng: 8,135,000 - 10,635,000 đồng",
            "Thi lại: 100,000-150,000 đồng/lần"
        ],
        structured_data={
            "chi_phi": {
                "hoc_phi": "7,500,000 - 10,000,000 đồng",
                "phi_thi": {
                    "ly_thuyet": "100,000 đồng",
                    "sa_hinh": "100,000 đồng",
                    "thuc_hanh": "150,000 đồng",
                    "tong": "350,000 đồng"
                },
                "phi_cap_bang": "135,000 đồng",
                "khac": "150,000 đồng (ảnh, khám)",
                "tong_cong": "8,135,000 - 10,635,000 đồng"
            },
            "phi_tai_thi": {
                "ly_thuyet": "100,000 đồng/lần",
                "thuc_hanh": "150,000 đồng/lần"
            }
        },
        required_aspects=["Học phí", "Phí thi", "Phí cấp bằng", "Tổng chi phí"],
        source_procedure="Cấp bằng lái xe B2"
    )

    manager.add_test_case(
        test_id="FEE_HARD_002",
        category="fees",
        difficulty="hard",
        question="Đầu tư FDI phải trả những khoản phí gì và có miễn giảm không?",
        natural_language_answer="""
CÁC KHOẢN PHÍ ĐẦU TƯ FDI:

1. PHÍ CẤP GIẤY CHỨNG NHẬN ĐẦU TƯ:
   - Lệ phí: 1,000,000 đồng
   - Phí thẩm định hồ sơ: 3,000,000 - 10,000,000 đồng (tùy quy mô dự án)

2. PHÍ THUÊ ĐẤT/QUYỀN SỬ DỤNG ĐẤT:
   - Trong KCN: 30-100 USD/m²/năm (tùy khu vực)
   - Ngoài KCN: Theo quy định địa phương

3. PHÍ MÔI TRƯỜNG:
   - Đánh giá tác động môi trường (ĐTM): 20,000,000 - 100,000,000 đồng
   - Phí thẩm định ĐTM: 5,000,000 - 30,000,000 đồng

4. PHÍ ĐĂNG KÝ KINH DOANH:
   - Sau khi có GCN đầu tư: 500,000 đồng

MIỄN GIẢM PHÍ (ƯU ĐÃI ĐẦU TƯ):

1. MIỄN TIỀN THUÊ ĐẤT (tùy địa bàn):
   - Địa bàn ưu đãi đầu tư: Miễn 03-05 năm
   - Địa bàn khó khăn: Miễn 07-11 năm
   - Địa bàn đặc biệt khó khăn: Miễn 11-15 năm

2. GIẢM TIỀN THUÊ ĐẤT:
   - Sau thời gian miễn: Giảm 50% từ 05-10 năm tiếp theo

3. CÁC ƯU ĐÃI KHÁC:
   - Dự án công nghệ cao: Miễn phí thẩm định
   - Dự án lớn (>6,000 tỷ): Giảm 50% phí môi trường

TỔNG CHI PHÍ DỰ ÁN NHỎ: 30,000,000 - 50,000,000 đồng
TỔNG CHI PHÍ DỰ ÁN LỚN: 100,000,000 - 500,000,000 đồng (chưa tính thuê đất)

LƯU Ý:
- Phí thuê đất phụ thuộc vào vị trí, diện tích
- Ưu đãi phụ thuộc vào địa bàn và lĩnh vực đầu tư
- Dự án ưu tiên (công nghệ cao, môi trường, năng lượng sạch) có ưu đãi nhiều hơn
        """.strip(),
        key_facts=[
            "Phí cấp GCN đầu tư: 1,000,000 đồng",
            "Phí thẩm định: 3,000,000-10,000,000 đồng",
            "Thuê đất KCN: 30-100 USD/m²/năm",
            "Phí môi trường: 20,000,000-100,000,000 đồng",
            "Miễn thuê đất: 3-15 năm tùy địa bàn",
            "Giảm 50% sau miễn: 5-10 năm"
        ],
        structured_data={
            "cac_khoan_phi": {
                "cap_gcn_dau_tu": "1,000,000 đồng",
                "tham_dinh": "3,000,000 - 10,000,000 đồng",
                "thue_dat_kcn": "30-100 USD/m²/năm",
                "phi_moi_truong": "20,000,000 - 100,000,000 đồng",
                "dang_ky_kinh_doanh": "500,000 đồng"
            },
            "uu_dai": {
                "mien_thue_dat": {
                    "uu_dai": "03-05 năm",
                    "kho_khan": "07-11 năm",
                    "dac_biet_kho_khan": "11-15 năm"
                },
                "giam_thue_dat": "50% trong 05-10 năm sau miễn",
                "uu_dai_khac": [
                    "Công nghệ cao: miễn phí thẩm định",
                    "Dự án lớn: giảm 50% phí môi trường"
                ]
            }
        },
        required_aspects=["Các khoản phí", "Miễn giảm", "Ưu đãi đầu tư"],
        source_procedure="Đầu tư FDI"
    )

    # ========================================================================
    # CATEGORY 7: OVERVIEW (6 cases)
    # ========================================================================

    # EASY (2 cases)
    manager.add_test_case(
        test_id="OVER_EASY_001",
        category="overview",
        difficulty="easy",
        question="Thủ tục đăng ký kết hôn là gì?",
        natural_language_answer="""
Thủ tục đăng ký kết hôn là thủ tục hành chính để Nhà nước công nhận sự kết hôn giữa nam và nữ có đủ điều kiện kết hôn theo pháp luật.

Thông tin chính:
- Mã thủ tục: 1.013124
- Lĩnh vực: Hộ tịch
- Cơ quan thực hiện: UBND cấp xã
- Thời gian: Trong ngày làm việc
- Lệ phí: Miễn phí
        """.strip(),
        key_facts=[
            "Công nhận sự kết hôn hợp pháp",
            "Mã: 1.013124",
            "Lĩnh vực: Hộ tịch",
            "UBND cấp xã",
            "Trong ngày",
            "Miễn phí"
        ],
        structured_data={
            "ten_thu_tuc": "Đăng ký kết hôn",
            "ma_thu_tuc": "1.013124",
            "linh_vuc": "Hộ tịch",
            "co_quan": "UBND cấp xã",
            "thoi_gian": "Trong ngày làm việc",
            "le_phi": "Miễn phí"
        },
        required_aspects=["Tên thủ tục", "Lĩnh vực", "Cơ quan", "Thời gian", "Phí"],
        source_procedure="Đăng ký kết hôn"
    )

    manager.add_test_case(
        test_id="OVER_EASY_002",
        category="overview",
        difficulty="easy",
        question="Thủ tục cấp CCCD là gì?",
        natural_language_answer="""
Thủ tục cấp Căn cước công dân (CCCD) là thủ tục cấp giấy tờ định danh cá nhân cho công dân Việt Nam từ 14 tuổi trở lên.

Thông tin chính:
- Mã thủ tục: 1.002565
- Lĩnh vực: Công an - Căn cước công dân
- Cơ quan thực hiện: Phòng Cảnh sát quản lý hành chính
- Thời gian: 15 ngày làm việc (hoặc 05 ngày nếu cấp gấp)
- Lệ phí: Miễn phí (lần đầu)
        """.strip(),
        key_facts=[
            "Cấp giấy tờ định danh",
            "Từ 14 tuổi trở lên",
            "Mã: 1.002565",
            "Công an",
            "15 ngày (hoặc 05 ngày cấp gấp)",
            "Miễn phí lần đầu"
        ],
        structured_data={
            "ten_thu_tuc": "Cấp Căn cước công dân",
            "ma_thu_tuc": "1.002565",
            "linh_vuc": "Công an - Căn cước công dân",
            "co_quan": "Phòng Cảnh sát quản lý hành chính",
            "thoi_gian": "15 ngày (hoặc 05 ngày cấp gấp)",
            "le_phi": "Miễn phí (lần đầu)"
        },
        required_aspects=["Tên thủ tục", "Lĩnh vực", "Cơ quan", "Thời gian", "Phí"],
        source_procedure="Cấp CCCD"
    )

    # MEDIUM (2 cases)
    manager.add_test_case(
        test_id="OVER_MED_001",
        category="overview",
        difficulty="medium",
        question="Thủ tục đăng ký kinh doanh là gì và dành cho ai?",
        natural_language_answer="""
Thủ tục đăng ký kinh doanh là thủ tục để cá nhân hoặc tổ chức thành lập doanh nghiệp mới, được Nhà nước cấp Giấy chứng nhận đăng ký doanh nghiệp để hoạt động kinh doanh hợp pháp.

ĐỐI TƯỢNG:
- Công dân Việt Nam từ 18 tuổi
- Tổ chức, cá nhân nước ngoài (theo quy định)

THÔNG TIN CHÍNH:
- Mã thủ tục: 1.013145
- Lĩnh vực: Đầu tư - Đăng ký kinh doanh
- Cơ quan: Sở Kế hoạch và Đầu tư
- Thời gian: 03 ngày làm việc
- Lệ phí: 500,000 đồng (online giảm 20%)

MỤC ĐÍCH:
- Thành lập doanh nghiệp hợp pháp
- Được hoạt động kinh doanh
- Được bảo vệ quyền lợi theo pháp luật
        """.strip(),
        key_facts=[
            "Thành lập doanh nghiệp mới",
            "Từ 18 tuổi",
            "Mã: 1.013145",
            "Sở Kế hoạch và Đầu tư",
            "03 ngày",
            "500,000 đồng"
        ],
        structured_data={
            "ten_thu_tuc": "Đăng ký kinh doanh lần đầu",
            "ma_thu_tuc": "1.013145",
            "linh_vuc": "Đầu tư - Đăng ký kinh doanh",
            "doi_tuong": "Công dân từ 18 tuổi, tổ chức",
            "co_quan": "Sở Kế hoạch và Đầu tư",
            "thoi_gian": "03 ngày làm việc",
            "le_phi": "500,000 đồng (online: 400,000)"
        },
        required_aspects=["Tên thủ tục", "Đối tượng", "Cơ quan", "Mục đích"],
        source_procedure="Đăng ký kinh doanh"
    )

    manager.add_test_case(
        test_id="OVER_MED_002",
        category="overview",
        difficulty="medium",
        question="Thủ tục xin giấy phép xây dựng là gì và khi nào cần xin?",
        natural_language_answer="""
Thủ tục xin giấy phép xây dựng là thủ tục xin phép từ cơ quan Nhà nước có thẩm quyền trước khi tiến hành xây dựng công trình.

KHI NÀO CẦN XIN:
- Xây dựng nhà ở riêng lẻ (trừ nhà tạm)
- Xây dựng công trình công cộng
- Sửa chữa, cải tạo công trình (thay đổi kết cấu)

KHÔNG CẦN XIN (TRƯỜNG HỢP ĐẶC BIỆT):
- Nhà tạm dưới 25m²
- Sửa chữa nhỏ không thay đổi kết cấu
- Xây dựng trong khu công nghiệp đã có quy hoạch chi tiết

THÔNG TIN:
- Lĩnh vực: Xây dựng
- Cơ quan: Phòng Quản lý đô thị (UBND quận/huyện)
- Thời gian: 20-30 ngày
- Lệ phí: 150,000 - 500,000 đồng (nhà ở)

MỤC ĐÍCH:
- Đảm bảo công trình đúng quy hoạch
- Đảm bảo an toàn kết cấu
- Bảo vệ cảnh quan đô thị
        """.strip(),
        key_facts=[
            "Xin phép trước khi xây dựng",
            "Nhà ở, công trình công cộng cần phép",
            "Nhà tạm <25m² không cần",
            "Phòng Quản lý đô thị",
            "20-30 ngày",
            "150,000-500,000 đồng"
        ],
        structured_data={
            "ten_thu_tuc": "Cấp giấy phép xây dựng",
            "linh_vuc": "Xây dựng",
            "khi_nao_can": [
                "Xây nhà ở riêng lẻ",
                "Công trình công cộng",
                "Sửa chữa thay đổi kết cấu"
            ],
            "khong_can": [
                "Nhà tạm <25m²",
                "Sửa chữa nhỏ",
                "Trong KCN có quy hoạch"
            ],
            "co_quan": "Phòng Quản lý đô thị",
            "thoi_gian": "20-30 ngày",
            "le_phi": "150,000 - 500,000 đồng"
        },
        required_aspects=["Tên thủ tục", "Khi nào cần", "Cơ quan", "Mục đích"],
        source_procedure="Cấp giấy phép xây dựng"
    )

    # HARD (2 cases)
    manager.add_test_case(
        test_id="OVER_HARD_001",
        category="overview",
        difficulty="hard",
        question="Thủ tục đầu tư FDI là gì, gồm những bước lớn nào và mất bao lâu?",
        natural_language_answer="""
Thủ tục đầu tư FDI (Foreign Direct Investment - Đầu tư trực tiếp nước ngoài) là quy trình để nhà đầu tư nước ngoài được cấp Giấy chứng nhận đầu tư và thành lập doanh nghiệp tại Việt Nam.

ĐỐI TƯỢNG:
- Cá nhân, tổ chức nước ngoài
- Doanh nghiệp có vốn nước ngoài
- Người Việt Nam định cư ở nước ngoài

CÁC BƯỚC LỚN:
1. Chuẩn bị dự án (60-90 ngày):
   - Nghiên cứu pháp lý, thị trường
   - Tìm địa điểm đầu tư
   - Lập hồ sơ dự án

2. Xin Giấy chứng nhận đầu tư (40-60 ngày):
   - Nộp hồ sơ tại Sở Kế hoạch và Đầu tư
   - Thẩm định liên ngành
   - Phê duyệt và cấp GCN

3. Triển khai dự án (30-60 ngày):
   - Thuê đất/Nhận quyền sử dụng đất
   - Đánh giá tác động môi trường
   - Đăng ký kinh doanh

TỔNG THỜI GIAN: 130-220 ngày (4-7 tháng)

CHI PHÍ:
- Phí hành chính: 30,000,000 - 50,000,000 đồng
- Thuê đất: 30-100 USD/m²/năm (trong KCN)
- Có ưu đãi: Miễn/giảm thuê đất 3-15 năm

LĨNH VỰC:
- Tất cả lĩnh vực (trừ danh mục cấm/hạn chế)
- Ưu tiên: Công nghệ cao, năng lượng sạch, R&D
        """.strip(),
        key_facts=[
            "Đầu tư trực tiếp nước ngoài",
            "Cá nhân, tổ chức nước ngoài",
            "Chuẩn bị: 60-90 ngày",
            "Xin GCN: 40-60 ngày",
            "Triển khai: 30-60 ngày",
            "Tổng: 4-7 tháng",
            "Chi phí: 30-50 triệu đồng",
            "Có ưu đãi đầu tư"
        ],
        structured_data={
            "ten_thu_tuc": "Cấp Giấy chứng nhận đầu tư FDI",
            "linh_vuc": "Đầu tư nước ngoài",
            "doi_tuong": "Cá nhân, tổ chức nước ngoài",
            "cac_buoc_lon": [
                {"buoc": "Chuẩn bị dự án", "thoi_gian": "60-90 ngày"},
                {"buoc": "Xin GCN đầu tư", "thoi_gian": "40-60 ngày"},
                {"buoc": "Triển khai dự án", "thoi_gian": "30-60 ngày"}
            ],
            "tong_thoi_gian": "130-220 ngày (4-7 tháng)",
            "chi_phi": "30,000,000 - 50,000,000 đồng (chưa tính thuê đất)",
            "uu_dai": "Miễn/giảm thuê đất 3-15 năm"
        },
        required_aspects=["Tên thủ tục", "Đối tượng", "Các bước lớn", "Tổng thời gian", "Chi phí"],
        source_procedure="Đầu tư FDI"
    )

    manager.add_test_case(
        test_id="OVER_HARD_002",
        category="overview",
        difficulty="hard",
        question="Thủ tục đấu thầu dự án công là gì, áp dụng khi nào và có mấy hình thức?",
        natural_language_answer="""
Thủ tục đấu thầu dự án công là quy trình lựa chọn nhà thầu để thực hiện dự án sử dụng vốn nhà nước, đảm bảo công khai, minh bạch, cạnh tranh và hiệu quả kinh tế.

KHI NÀO ÁP DỤNG:
- Dự án xây dựng công trình công cộng (đường, cầu, trường, bệnh viện)
- Mua sắm tài sản, thiết bị công (dùng vốn nhà nước)
- Thuê tư vấn cho dự án công
- Giá trị ≥ 500 triệu đồng (phải đấu thầu)

HÌNH THỨC ĐẤU THẦU:
1. Đấu thầu rộng rãi:
   - Công khai mời tất cả nhà thầu
   - Áp dụng: Dự án lớn, quan trọng

2. Đấu thầu hạn chế:
   - Mời danh sách nhà thầu có đủ năng lực
   - Áp dụng: Dự án chuyên môn cao

3. Chỉ định thầu:
   - Chỉ định trực tiếp 01 nhà thầu
   - Áp dụng: Trường hợp đặc biệt (khẩn cấp, độc quyền)

4. Mua sắm trực tiếp:
   - Giá trị < 500 triệu: không đấu thầu
   - Chào giá, so sánh 3 nhà cung cấp

QUY TRÌNH CHUNG:
- Chuẩn bị: 30-45 ngày
- Tổ chức đấu thầu: 30-60 ngày
- Đánh giá: 30-45 ngày
- Phê duyệt: 15-30 ngày
- Tổng: 105-180 ngày (3.5-6 tháng)

NGUYÊN TẮC:
- Công khai, minh bạch
- Cạnh tranh
- Công bằng
- Hiệu quả kinh tế
- Chống tham nhũng

CƠ QUAN QUẢN LÝ:
- Chủ đầu tư: Tổ chức đấu thầu
- Bộ Kế hoạch và Đầu tư: Quản lý nhà nước
- Thanh tra, Kiểm toán: Giám sát
        """.strip(),
        key_facts=[
            "Lựa chọn nhà thầu cho dự án công",
            "Dự án ≥500 triệu phải đấu thầu",
            "4 hình thức: Rộng rãi, Hạn chế, Chỉ định, Mua sắm trực tiếp",
            "Tổng thời gian: 3.5-6 tháng",
            "Nguyên tắc: Công khai, cạnh tranh, minh bạch",
            "Chống tham nhũng"
        ],
        structured_data={
            "ten_thu_tuc": "Đấu thầu dự án công",
            "linh_vuc": "Đấu thầu - Mua sắm công",
            "khi_nao_ap_dung": [
                "Dự án xây dựng công trình công",
                "Mua sắm tài sản, thiết bị công",
                "Thuê tư vấn dự án công",
                "Giá trị ≥ 500 triệu đồng"
            ],
            "hinh_thuc": [
                "Đấu thầu rộng rãi (dự án lớn)",
                "Đấu thầu hạn chế (chuyên môn cao)",
                "Chỉ định thầu (trường hợp đặc biệt)",
                "Mua sắm trực tiếp (<500 triệu)"
            ],
            "thoi_gian": "105-180 ngày (3.5-6 tháng)",
            "nguyen_tac": [
                "Công khai, minh bạch",
                "Cạnh tranh",
                "Công bằng",
                "Hiệu quả kinh tế",
                "Chống tham nhũng"
            ]
        },
        required_aspects=["Tên thủ tục", "Khi nào áp dụng", "Hình thức", "Nguyên tắc", "Thời gian"],
        source_procedure="Đấu thầu dự án công"
    )

    # ========================================================================
    # FINAL EXPORT
    # ========================================================================

    print(f"\n✅ Created {len(manager.test_cases)} test cases")
    print(f"\n📊 Final statistics:")

    stats = manager.get_statistics()
    print(f"\nBy category:")
    for category, count in stats["by_category"].items():
        print(f"   {category}: {count} cases")

    print(f"\nBy difficulty:")
    for difficulty, count in stats["by_difficulty"].items():
        print(f"   {difficulty}: {count} cases")

    print(f"\nTotal: {stats['total_cases']} test cases")

    return manager


if __name__ == "__main__":
    manager = create_comprehensive_dataset()
    manager.export_dataset("comprehensive_test_dataset.json")
