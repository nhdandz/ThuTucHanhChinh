# 🏛️ HỆ THỐNG HỎI ĐÁP THỦ TỤC HÀNH CHÍNH - RAG SYSTEM

Hệ thống RAG (Retrieval-Augmented Generation) cho 207 thủ tục hành chính, tối ưu hóa cho độ chính xác cao nhất.

## 📋 MỤC LỤC

- [Tổng Quan](#tổng-quan)
- [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
- [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
- [Kết Quả Đạt Được](#kết-quả-đạt-được)
- [Roadmap Triển Khai](#roadmap-triển-khai)
- [Chiến Lược Kỹ Thuật](#chiến-lược-kỹ-thuật)
- [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng)
- [Tài Liệu Tham Khảo](#tài-liệu-tham-khảo)

---

## 🎯 TỔNG QUAN

### Mục Tiêu
Xây dựng hệ thống hỏi đáp tự động về thủ tục hành chính với **độ chính xác > 95%**, giúp người dân tra cứu nhanh chóng và chính xác các thông tin về:
- Giấy tờ cần thiết
- Yêu cầu và điều kiện
- Quy trình thực hiện
- Căn cứ pháp lý
- Thời gian và chi phí

### Đặc Điểm Nổi Bật

✅ **Accuracy-First**: Tối ưu hóa độ chính xác thay vì tốc độ
✅ **Hierarchical Chunking**: 2-tier structure (Parent + Child chunks)
✅ **5-Stage Retrieval**: Pipeline retrieval nâng cao với multi-query fusion và re-ranking
✅ **Multi-Layer Validation**: 5 layers kiểm tra để đảm bảo chất lượng câu trả lời
✅ **BGE-M3 Embeddings**: Model embedding đa ngôn ngữ tối ưu cho tiếng Việt (1024-dim)
✅ **Hybrid Output**: Kết hợp JSON (structured) và Natural Language

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Embedding** | BGE-M3 (BAAI/bge-m3) | Vector embeddings 1024-dim |
| **Vector DB** | Qdrant / ChromaDB | Lưu trữ và tìm kiếm vector |
| **Reranker** | BAAI/bge-reranker-v2-m3 | Cross-encoder reranking |
| **LLM** | qwen3-8b (OpenAI API) | Generation & synthesis |
| **NLI** | xlm-roberta-large-xnli | Hallucination detection |
| **Chunking** | Tiktoken (cl100k_base) | Token counting |

### Kiến Trúc RAG Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                       USER QUERY                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: QUERY ENHANCEMENT                                       │
│  • Intent Detection (documents/requirements/process/legal)       │
│  • Query Expansion                                               │
│  • Multi-Query Generation (N=3)                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: HIERARCHICAL RETRIEVAL                                  │
│  • Step 1: Retrieve Parent chunks (K=5)                          │
│  • Step 2: Retrieve Child chunks for each parent (K=3)           │
│  • Total: 5 parent + 15 child = 20 chunks                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: MULTI-QUERY FUSION                                      │
│  • Reciprocal Rank Fusion (RRF)                                  │
│  • Combine results from 3 queries                                │
│  • Top-K=10 final chunks                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: CROSS-ENCODER RE-RANKING                                │
│  • BGE Reranker v2-m3                                            │
│  • Re-score 10 chunks                                            │
│  • Select top-5 most relevant                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: CONTEXT ASSEMBLY                                        │
│  • Context window management (~3500 tokens)                      │
│  • Chunk priority ordering                                       │
│  • Metadata enrichment                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ GENERATION & ANSWER SYNTHESIS                                    │
│  • qwen3-8b with structured prompt                                  │
│  • Hybrid output: JSON + Natural Language                        │
│  • Citation with chunk references                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ MULTI-LAYER VALIDATION                                           │
│  Layer 1: NLI Hallucination Detection                            │
│  Layer 2: Completeness Check                                     │
│  Layer 3: Cross-Reference Validation                             │
│  Layer 4: Self-Consistency (N=5 samples)                         │
│  Layer 5: Chain-of-Verification (CoVe)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                       FINAL ANSWER
```

---

## 📁 CẤU TRÚC DỰ ÁN

```
thu_tuc_rag/
│
├── README.md                          # File này
├── requirements.txt                   # Dependencies
│
├── data/
│   ├── raw/                          # 207 .doc files gốc
│   │   └── ChiTietTTHC_*.doc
│   │
│   ├── extracted/                    # 207 JSON files đã extract
│   │   ├── 1.013124.json
│   │   ├── 1.013125.json
│   │   └── ...
│   │
│   ├── chunks/                       # Chunks data
│   │   ├── all_chunks.json          # 1,084 chunks
│   │   └── chunking_stats.json      # Statistics
│   │
│   └── embeddings/                   # Vector embeddings (Phase 3)
│       └── chunks_with_embeddings.json
│
├── src/
│   ├── extraction/                   # Phase 1: Data Extraction
│   │   ├── extract_documents.py     # Extract from .doc files
│   │   └── data_validator.py        # Validate extracted data
│   │
│   ├── chunking/                     # Phase 2: Chunking
│   │   ├── hierarchical_chunker.py  # 2-tier chunking logic
│   │   └── test_chunker.py          # Testing
│   │
│   ├── retrieval/                    # Phase 3: Retrieval Pipeline
│   │   ├── embedding_generator.py   # BGE-M3 embeddings
│   │   ├── vector_store.py          # Qdrant setup
│   │   ├── query_processor.py       # Query enhancement
│   │   └── retrieval_pipeline.py    # 5-stage retrieval
│   │
│   ├── generation/                   # Phase 4: Generation
│   │   ├── answer_generator.py      # qwen3-8b integration
│   │   └── prompt_templates.py      # Prompt engineering
│   │
│   ├── validation/                   # Phase 5: Validation
│   │   ├── nli_validator.py         # Hallucination detection
│   │   ├── consistency_checker.py   # Self-consistency
│   │   └── cove_verifier.py         # Chain-of-Verification
│   │
│   └── evaluation/                   # Phase 6: Testing
│       ├── test_dataset.py          # 50-100 Q&A pairs
│       └── metrics.py               # Accuracy, precision, recall
│
├── config/
│   └── config.yaml                   # Configuration
│
└── notebooks/
    └── analysis.ipynb                # Data analysis
```

---

## ✅ KẾT QUẢ ĐẠT ĐƯỢC

### Phase 1: Data Extraction ✅ HOÀN THÀNH

**Kết quả:**
- ✅ Extract thành công **207/207 files** (100% success rate)
- ✅ 20 fields/thủ tục với cấu trúc đồng nhất
- ✅ 3 bảng dữ liệu: Thành phần hồ sơ, Căn cứ pháp lý, Hình thức nộp

**Files tạo ra:**
- `extract_documents.py` - Script extraction chính
- `data_validator.py` - Multi-layer validation
- 207 JSON files trong `data/extracted/`

**Cấu trúc JSON:**
```json
{
  "thu_tuc_id": "1.013124",
  "source_file": "ChiTietTTHC_1.013124.doc",
  "metadata": {
    "mã_thủ_tục": "...",
    "tên_thủ_tục": "...",
    "lĩnh_vực": "...",
    "cấp_thực_hiện": "...",
    "loại_thủ_tục": "..."
  },
  "content": {
    "đối_tượng_thực_hiện": "...",
    "yêu_cầu_điều_kiện_thực_hiện": "...",
    "trình_tự_thực_hiện": "...",
    "cách_thức_thực_hiện": "...",
    "cơ_quan_thực_hiện": "...",
    "kết_quả_thực_hiện": "..."
  },
  "tables": {
    "thanh_phan_ho_so": [...],
    "can_cu_phap_ly": [...],
    "hinh_thuc_nop": [...]
  }
}
```

---

### Phase 2: Hierarchical Chunking ✅ HOÀN THÀNH

**Kết quả:**
- ✅ **1,084 chunks** tổng cộng
- ✅ **207 Parent chunks** (overview/routing)
- ✅ **877 Child chunks** (detailed info)

**Phân bố Child Chunks:**
```
┌────────────────────┬────────┬──────────┬──────────┐
│ Chunk Type         │ Count  │ Avg Tkns │ Max Tkns │
├────────────────────┼────────┼──────────┼──────────┤
│ Parent Overview    │   207  │    353   │    601   │
│ Child Documents    │   236  │    640   │   2114   │
│ Child Requirements │   300  │    484   │    769   │
│ Child Process      │   118  │    698   │    896   │
│ Child Legal        │   223  │    350   │    930   │
└────────────────────┴────────┴──────────┴──────────┘
```

**Chiến lược Chunking:**

**TIER 1: Parent Chunks (Overview)**
- Mục đích: Quick answer + Routing to children
- Nội dung: Tóm tắt thủ tục, đối tượng, cơ quan, thời gian, chi phí
- Size: ~350 tokens
- Luôn được retrieve trước

**TIER 2: Child Chunks (Detailed)**

| Type | Content | Max Tokens | Overlap |
|------|---------|------------|---------|
| **Child A - Documents** | Danh sách giấy tờ + Cách nộp | 1024 | 100 |
| **Child B - Requirements** | Đối tượng + Điều kiện | 768 | 200 |
| **Child C - Process** | Trình tự + Quy trình | 896 | 150 |
| **Child D - Legal** | Căn cứ pháp lý | 512 | 50 |

**Đặc điểm:**
- Mỗi child chunk có **Parent Context** ở đầu
- Preserve structure (numbered lists, tables)
- Overlap để tránh mất ngữ cảnh

**Files tạo ra:**
- `hierarchical_chunker.py` - Core chunking logic
- `test_chunker.py` - Testing script
- `all_chunks.json` - 1,084 chunks
- `chunking_stats.json` - Statistics

---

### Phase 3: Retrieval Pipeline 🔄 ĐANG TRIỂN KHAI

**Mục tiêu:**
- [ ] Setup BGE-M3 embedding model
- [ ] Generate embeddings cho 1,084 chunks
- [ ] Setup Qdrant vector database
- [ ] Implement query processor
- [ ] Implement 5-stage retrieval pipeline
- [ ] Test với sample queries

**5-Stage Retrieval Strategy:**

**Stage 1: Query Enhancement**
```python
Input: "Thủ tục cấp giấy phép xây dựng cần giấy tờ gì?"

Processing:
1. Intent Detection → "documents" (tìm giấy tờ)
2. Query Expansion → Add synonyms, related terms
3. Multi-Query Generation:
   - Q1: "Thành phần hồ sơ cấp giấy phép xây dựng"
   - Q2: "Giấy tờ cần thiết xây dựng"
   - Q3: "Documents required for construction permit"
```

**Stage 2: Hierarchical Retrieval**
```
Step 1: Retrieve Parent chunks (K=5)
  → Get top-5 most relevant procedures

Step 2: For each parent, retrieve Child chunks (K=3)
  → Based on intent, retrieve from specific child type
  → 5 parents × 3 children = 15 child chunks

Total: 5 parent + 15 child = 20 chunks
```

**Stage 3: Multi-Query Fusion (RRF)**
```python
# Reciprocal Rank Fusion
for each chunk in results:
    RRF_score = Σ(1 / (k + rank_i))  # k=60

Sort by RRF_score → Top-10 chunks
```

**Stage 4: Cross-Encoder Re-Ranking**
```python
# BGE Reranker v2-m3
scores = reranker.compute_score([
    [query, chunk_1],
    [query, chunk_2],
    ...
])

Sort by scores → Top-5 chunks
```

**Stage 5: Context Assembly**
```python
# Build context với priority
Context window: ~3500 tokens

Priority order:
1. Parent chunks của thủ tục matching
2. Child chunks theo intent type
3. Related chunks nếu còn chỗ

Format: [PARENT CONTEXT] + [MAIN CONTENT] + [METADATA]
```

---

### Phase 4: Generation & Answer Synthesis 📋 KẾ HOẠCH

**LLM:** qwen3-8b (ollama da tai)

**Prompt Engineering:**
```
System: Bạn là trợ lý thủ tục hành chính. Trả lời chính xác dựa trên context.

Context: [5 chunks đã rerank]

User Query: {query}

Instructions:
1. Trả lời chính xác dựa 100% vào context
2. Format: JSON + Natural Language
3. Cite sources với chunk_id
4. Nếu không có thông tin → nói rõ "Không có thông tin"
5. KHÔNG tự bịa thêm

Output Format:
{
  "answer": "...",
  "thu_tuc": {
    "ma": "...",
    "ten": "..."
  },
  "documents": [...],
  "sources": ["chunk_id_1", "chunk_id_2"]
}
```

**Output Format - Hybrid:**

**JSON (Structured):**
```json
{
  "answer": "Để cấp giấy phép xây dựng, bạn cần nộp 5 loại giấy tờ...",
  "thu_tuc": {
    "ma": "1.013124",
    "ten": "Thủ tục cấp giấy phép xây dựng"
  },
  "documents": [
    {
      "name": "Đơn đề nghị cấp phép",
      "quantity": "Bản chính: 1",
      "note": ""
    },
    ...
  ],
  "thoi_han": "30 ngày làm việc",
  "phi_le_phi": "Phí: 0 đồng",
  "sources": ["1.013124_child_documents_0", "1.013124_parent_overview"]
}
```

**Natural Language:**
```
Để làm thủ tục cấp giấy phép xây dựng (Mã: 1.013124), bạn cần nộp các giấy tờ sau:

1. Đơn đề nghị cấp phép (Bản chính: 1)
2. Bản vẽ thiết kế kỹ thuật (Bản chính: 1)
...

Thời gian giải quyết: 30 ngày làm việc
Phí, lệ phí: Phí 0 đồng

Nộp hồ sơ tại: [địa chỉ]

[Sources: Chunk 1.013124_child_documents_0, 1.013124_parent_overview]
```

---

### Phase 5: Optimization & Validation 📋 KẾ HOẠCH

**Multi-Layer Validation Framework:**

**Layer 1: NLI Hallucination Detection**
```python
Model: xlm-roberta-large-xnli

For each sentence in answer:
    NLI_score = model(premise=context, hypothesis=sentence)

    If NLI_score["contradiction"] > 0.5:
        → Flag as hallucination
        → Request regeneration or remove sentence
```

**Layer 2: Completeness Check**
```python
# Check if answer addresses all parts of query
query_aspects = extract_aspects(query)
answer_aspects = extract_aspects(answer)

completeness = len(answer_aspects ∩ query_aspects) / len(query_aspects)

If completeness < 0.8:
    → Request more information retrieval
```

**Layer 3: Cross-Reference Validation**
```python
# Verify facts across multiple chunks
For each fact in answer:
    supporting_chunks = count_supporting_evidence(fact, chunks)

    If supporting_chunks < 2:
        → Flag as low confidence
        → Add uncertainty marker
```

**Layer 4: Self-Consistency (Majority Voting)**
```python
# Generate N=5 answers independently
answers = []
for i in range(5):
    answer_i = generate_answer(query, context, temperature=0.7)
    answers.append(answer_i)

# Extract key facts from each
facts_matrix = extract_facts(answers)  # 5 × M matrix

# Majority voting
final_facts = []
for fact in facts_matrix:
    if count(fact) >= 3:  # 60% agreement
        final_facts.append(fact)

final_answer = synthesize(final_facts)
```

**Layer 5: Chain-of-Verification (CoVe)**
```python
# Step 1: Generate initial answer
baseline_answer = generate_answer(query, context)

# Step 2: LLM plans verification questions
verification_questions = llm_generate_questions(baseline_answer)
# Example: "Có chính xác là cần 5 giấy tờ không?"
#          "Thời hạn 30 ngày có đúng không?"

# Step 3: Answer verification questions
verifications = []
for q in verification_questions:
    v = generate_answer(q, context)
    verifications.append(v)

# Step 4: Generate final verified answer
final_answer = generate_answer_with_verifications(
    query, context, baseline_answer, verifications
)
```

---

### Phase 6: Evaluation & Testing 📋 KẾ HOẠCH

**Test Dataset:**
- 50-100 cặp (Question, Ground Truth Answer)
- Cover tất cả loại query:
  - Documents queries (30%)
  - Requirements queries (25%)
  - Process queries (25%)
  - Legal queries (10%)
  - Mixed queries (10%)

**Evaluation Metrics:**

| Metric | Target | Method |
|--------|--------|--------|
| **Accuracy** | > 95% | Exact + Semantic match |
| **Precision** | > 90% | Correct facts / Total facts |
| **Recall** | > 90% | Retrieved facts / Total facts |
| **F1-Score** | > 90% | Harmonic mean |
| **Hallucination Rate** | < 5% | NLI detection |
| **Latency** | 3-5s | End-to-end |

**Test Categories:**

```python
# 1. Factual Accuracy
"Thủ tục X cần bao nhiêu giấy tờ?"
→ Check exact number match

# 2. Completeness
"Quy trình làm thủ tục Y như thế nào?"
→ Check all steps present

# 3. Consistency
"Thời gian giải quyết thủ tục Z?"
→ Check no conflicting info

# 4. Citation Quality
→ Check all facts have source chunks

# 5. Edge Cases
"Thủ tục không tồn tại"
→ Should return "Không tìm thấy"
```

---

## 🗺️ ROADMAP TRIỂN KHAI

### Timeline Overview

```
┌─────────────┬──────────────────────────────────────┬──────────┐
│ Phase       │ Tasks                                │ Status   │
├─────────────┼──────────────────────────────────────┼──────────┤
│ Phase 1     │ Data Extraction                      │ ✅ DONE  │
│             │ - Extract 207 .doc files             │          │
│             │ - Validate data                      │          │
├─────────────┼──────────────────────────────────────┼──────────┤
│ Phase 2     │ Chunking & Indexing                  │ ✅ DONE  │
│             │ - Hierarchical chunker               │          │
│             │ - Generate 1,084 chunks              │          │
├─────────────┼──────────────────────────────────────┼──────────┤
│ Phase 3     │ Retrieval Pipeline                   │ 🔄 IN PROGRESS│
│             │ - BGE-M3 embeddings                  │          │
│             │ - Qdrant vector DB                   │          │
│             │ - 5-stage retrieval                  │          │
├─────────────┼──────────────────────────────────────┼──────────┤
│ Phase 4     │ Generation & Synthesis               │ 📋 PLANNED│
│             │ - qwen3-8b integration                  │          │
│             │ - Prompt engineering                 │          │
│             │ - Hybrid output format               │          │
├─────────────┼──────────────────────────────────────┼──────────┤
│ Phase 5     │ Optimization & Validation            │ 📋 PLANNED│
│             │ - NLI hallucination detection        │          │
│             │ - Self-consistency                   │          │
│             │ - Chain-of-Verification              │          │
├─────────────┼──────────────────────────────────────┼──────────┤
│ Phase 6     │ Evaluation & Testing                 │ 📋 PLANNED│
│             │ - Create test dataset                │          │
│             │ - Measure metrics                    │          │
│             │ - Optimize performance               │          │
└─────────────┴──────────────────────────────────────┴──────────┘
```

---

## 🎓 CHIẾN LƯỢC KỸ THUẬT

### 1. Hierarchical Chunking Strategy

**Tại sao 2-tier?**
- **Tier 1 (Parent)**: Fast routing, quick overview
  - User có thể được answer ngay từ parent
  - Hoặc parent giúp identify đúng thủ tục

- **Tier 2 (Child)**: Detailed information
  - Chỉ retrieve children khi cần details
  - Tránh information overload

**Ưu điểm:**
✅ Reduce noise: Không retrieve tất cả details ngay từ đầu
✅ Better precision: Parent làm filter đầu tiên
✅ Scalable: Dễ mở rộng khi thêm thủ tục
✅ Context-aware: Child chunks có parent context

### 2. Multi-Query Fusion (RRF)

**Tại sao cần 3 queries?**
- User query có thể diễn đạt nhiều cách
- Một query có thể miss relevant chunks
- 3 queries cover nhiều góc độ hơn

**Reciprocal Rank Fusion:**
```
RRF(d) = Σ(1 / (k + rank_i(d)))

k = 60 (constant)
rank_i(d) = vị trí của document d trong query i
```

**Ưu điểm:**
✅ Không cần normalize scores từ các models khác nhau
✅ Robust với outliers
✅ Proven effectiveness (used by search engines)

### 3. Cross-Encoder Re-Ranking

**Tại sao cần reranking?**
- Bi-encoder (BGE-M3) fast nhưng less accurate
- Cross-encoder slow nhưng very accurate
- Strategy: Bi-encoder retrieve nhiều (K=10), Cross-encoder refine (K=5)

**BGE Reranker v2-m3:**
- Multilingual (support Vietnamese)
- Fine-tuned for relevance scoring
- Input: (query, document) pair → score

### 4. Self-Consistency Voting

**Concept:**
Generate N=5 câu trả lời độc lập → Majority voting

**Tại sao effective?**
- Reduce randomness của LLM
- Facts xuất hiện ở nhiều answers → high confidence
- Facts chỉ ở 1-2 answers → low confidence, có thể bỏ

**Implementation:**
```python
answers = [generate(query, temp=0.7) for _ in range(5)]
facts = extract_facts(answers)  # Extract key facts
consensus = [f for f in facts if count(f) >= 3]  # 60% threshold
```

### 5. Chain-of-Verification (CoVe)

**4-Step Process:**
1. **Generate baseline answer**
2. **LLM self-generates verification questions**
   - "Có đúng là cần 5 giấy tờ?"
   - "Thời hạn có phải 30 ngày?"
3. **Answer verification questions independently**
4. **Revise answer based on verifications**

**Ưu điểm:**
✅ LLM tự detect và fix hallucinations
✅ Không cần external fact-checking DB
✅ Proven to reduce hallucination rate by 20-40%

---

## 🚀 HƯỚNG DẪN SỬ DỤNG

### Installation

```bash
# Clone repository
cd thu_tuc_rag

# Install dependencies
pip install -r requirements.txt

# Tùy chọn: Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Phase 1: Data Extraction

```bash
cd src/extraction
python extract_documents.py

# Output:
# - data/extracted/*.json (207 files)
```

### Phase 2: Chunking

```bash
cd src/chunking

# Test với vài files
python test_chunker.py

# Chunk tất cả
python hierarchical_chunker.py

# Output:
# - data/chunks/all_chunks.json
# - data/chunks/chunking_stats.json
```

### Phase 3: Generate Embeddings (In Progress)

```bash
cd src/retrieval
python embedding_generator.py

# Output:
# - data/embeddings/chunks_with_embeddings.json
```

### Phase 4: Setup Vector Database (Upcoming)

```bash
cd src/retrieval
python vector_store.py

# Khởi động Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Phase 5: Run Query (Upcoming)

```bash
python main.py --query "Thủ tục cấp giấy phép xây dựng cần giấy tờ gì?"

# Output: JSON + Natural Language answer
```

---

## 📊 DỮ LIỆU THỐNG KÊ

### Extracted Data (Phase 1)

- **Tổng số thủ tục**: 207
- **Thành công**: 207/207 (100%)
- **Trường dữ liệu**: 20 fields/thủ tục
- **Bảng**: 3 tables/thủ tục

**Field Length Statistics:**
```
Yêu cầu điều kiện: avg 834 chars, max 9,285 chars
Thành phần hồ sơ: avg 709 chars, max 7,130 chars
Trình tự thực hiện: 130/207 files missing (63%)
```

### Chunks Data (Phase 2)

**Overview:**
- **Total chunks**: 1,084
- **Parent chunks**: 207
- **Child chunks**: 877
- **Avg tokens/chunk**: 489
- **Procedures với Process chunks**: 118/207 (57%)

**Distribution:**
```
Parent Overview:    207 chunks (353 tokens avg)
Child Documents:    236 chunks (640 tokens avg)
Child Requirements: 300 chunks (484 tokens avg)
Child Process:      118 chunks (698 tokens avg)
Child Legal:        223 chunks (350 tokens avg)
```

---

## 🔧 CONFIGURATION

### config/config.yaml

```yaml
# Embedding
embedding:
  model: "BAAI/bge-m3"
  dimension: 1024
  batch_size: 32

# Vector Database
vector_db:
  type: "qdrant"
  host: "localhost"
  port: 6333
  collection: "thu_tuc_chunks"

# Retrieval
retrieval:
  parent_top_k: 5
  child_top_k: 3
  rerank_top_k: 5
  multi_query_count: 3
  rrf_k: 60

# Generation
generation:
  model: "qwen3-8b"
  temperature: 0.1
  max_tokens: 1000

# Validation
validation:
  nli_threshold: 0.5
  consistency_samples: 5
  consistency_threshold: 0.6
  cove_enabled: true
```

---

## 📈 EXPECTED PERFORMANCE

### Target Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Accuracy** | > 95% | Administrative procedures require high precision |
| **Precision** | > 90% | Minimize false information |
| **Recall** | > 90% | Don't miss important information |
| **Hallucination Rate** | < 5% | Critical for legal documents |
| **Latency** | 3-5s | Acceptable for accuracy-first approach |

### Performance Optimizations

**Speed-Accuracy Tradeoffs:**
- ✅ Accept 3-5s latency for >95% accuracy
- ✅ Multi-query fusion → Better recall
- ✅ Cross-encoder reranking → Better precision
- ✅ Self-consistency → Lower hallucination

**Potential Bottlenecks:**
- Embedding generation: ~30s for 1,084 chunks (one-time)
- Vector search: <100ms (Qdrant optimized)
- Cross-encoder reranking: ~500ms for 10 chunks
- LLM generation: ~2s (qwen3-8b)
- Validation (CoVe): +1-2s

**Total latency**: ~3-5s ✅

---

## 🧪 TESTING STRATEGY

### Test Dataset Structure

```python
{
  "id": "test_001",
  "category": "documents",  # documents/requirements/process/legal/mixed
  "query": "Thủ tục cấp giấy phép xây dựng cần giấy tờ gì?",
  "thu_tuc_id": "1.013124",
  "ground_truth": {
    "answer": "Cần 5 loại giấy tờ...",
    "documents": [...],
    "sources": ["1.013124_child_documents_0"]
  }
}
```

### Test Categories Distribution

```
Documents queries:     30 tests (30%)
Requirements queries:  25 tests (25%)
Process queries:       25 tests (25%)
Legal queries:         10 tests (10%)
Mixed queries:         10 tests (10%)
─────────────────────────────────────
Total:                100 tests
```

### Evaluation Process

```python
for test in test_dataset:
    # Generate answer
    answer = rag_system.query(test["query"])

    # Evaluate
    accuracy = check_accuracy(answer, test["ground_truth"])
    precision = check_precision(answer, test["ground_truth"])
    recall = check_recall(answer, test["ground_truth"])
    hallucination = check_hallucination(answer, retrieved_chunks)

    # Record metrics
    metrics.append({
        "test_id": test["id"],
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "hallucination": hallucination
    })

# Aggregate
overall_accuracy = mean(metrics["accuracy"])
print(f"Overall Accuracy: {overall_accuracy:.2%}")
```
