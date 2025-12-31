# 🚀 Hướng Dẫn Deployment - Chatbot 207 Thủ Tục Hành Chính

## 📋 Tổng Quan

Hệ thống bao gồm:
- **Backend**: FastAPI (Python) - Port 8000
- **Frontend**: Next.js (React) - Port 3000
- **Vector DB**: Qdrant (local storage)
- **LLM**: Ollama (qwen3:8b, bge-m3)

---

## ✅ Prerequisites

### 1. Ollama

Đảm bảo Ollama đang chạy với các models cần thiết:

```bash
# Kiểm tra Ollama đang chạy
ollama list

# Cần có 2 models:
# - bge-m3 (embedding model)
# - qwen3:8b (LLM model)

# Nếu chưa có, tải về:
ollama pull bge-m3
ollama pull qwen3:8b
```

### 2. Conda Environment

```bash
# Activate environment
conda activate thu_tuc_rag

# Kiểm tra Python version (cần >= 3.10)
python --version
```

### 3. Node.js & npm

```bash
# Kiểm tra Node.js (cần >= 18.0)
node --version

# Kiểm tra npm
npm --version
```

---

## 🔧 Setup & Installation

### Backend Setup

```bash
# 1. Navigate to project directory
cd /home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag

# 2. Activate conda environment
conda activate thu_tuc_rag

# 3. Install backend dependencies (đã install rồi)
# pip install -r requirements_backend.txt

# 4. Verify .env file exists
cat .env
```

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd /home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag/fe

# 2. Install dependencies (nếu chưa install)
npm install

# 3. Verify .env.local file exists
cat .env.local
```

---

## 🚀 Starting the Application

### Terminal 1: Start Backend (FastAPI)

```bash
# Activate conda environment
conda activate thu_tuc_rag

# Navigate to project root
cd /home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag

# Start backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
============================================================
Starting Thu Tuc RAG API v1.0.0
CORS Origins: ['http://localhost:3000']
Ollama URL: http://localhost:11434
Qdrant Path: /home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag/qdrant_storage
============================================================
Initializing RAG pipeline...
RAG pipeline initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Backend URLs:**
- API Root: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

### Terminal 2: Start Frontend (Next.js)

```bash
# Navigate to frontend directory
cd /home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag/fe

# Start development server
npm run dev
```

**Expected output:**
```
▲ Next.js 16.1.1
- Local:        http://localhost:3000
- Network:      http://0.0.0.0:3000

✓ Starting...
✓ Ready in 2.3s
```

**Frontend URL:**
- Application: http://localhost:3000

---

## 🧪 Testing the Application

### 1. Test Backend Health

```bash
# In a new terminal
curl http://localhost:8000/api/health | python3 -m json.tool
```

**Expected response:**
```json
{
  "status": "healthy",
  "qdrant_status": "connected",
  "ollama_status": "connected",
  "version": "1.0.0",
  "timestamp": "2025-12-29T..."
}
```

### 2. Test Backend API

```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Đăng ký kết hôn cần giấy tờ gì?"}' \
  | python3 -m json.tool
```

### 3. Test Frontend

1. Mở browser: http://localhost:3000
2. Nhập câu hỏi: "Đăng ký kết hôn cần giấy tờ gì?"
3. Đợi phản hồi (60-180 giây do Ollama local)
4. Kiểm tra:
   - ✅ Câu trả lời hiển thị
   - ✅ Source citations có thể mở/đóng
   - ✅ Structured data (JSON) có thể xem
   - ✅ Chat history được lưu khi refresh page

---

## 📂 File Structure

```
thu_tuc_rag/
├── backend/                      # FastAPI backend
│   ├── main.py                   # Entry point
│   ├── config.py                 # Configuration
│   ├── dependencies.py           # DI container
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py           # Chat endpoints
│   │   │   └── health.py         # Health check
│   │   └── models/
│   │       ├── request.py        # Request schemas
│   │       └── response.py       # Response schemas
│   ├── services/
│   │   ├── chat_service.py       # Core business logic
│   │   └── session_manager.py   # Session management
│   └── middleware/
│       └── error_handler.py      # Error handling
│
├── fe/                           # Next.js frontend
│   ├── app/
│   │   ├── page.tsx              # Main page
│   │   ├── layout.tsx            # Root layout
│   │   └── globals.css           # Global styles
│   ├── components/
│   │   ├── ui/                   # UI components
│   │   └── chat/                 # Chat components
│   ├── hooks/
│   │   ├── useChat.ts            # Chat state management
│   │   └── useLocalStorage.ts   # LocalStorage hook
│   └── lib/
│       ├── types.ts              # TypeScript interfaces
│       ├── api-client.ts         # API client
│       └── utils.ts              # Utilities
│
├── src/                          # RAG pipeline (existing)
├── data/                         # Data files (existing)
├── qdrant_storage/               # Vector database (existing)
│
├── .env                          # Backend environment variables
├── requirements_backend.txt      # Backend dependencies
└── README_DEPLOYMENT.md          # This file
```

---

## 🔍 Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill process using port 8000
lsof -ti :8000 | xargs kill -9

# Or use different port
uvicorn backend.main:app --port 8001
```

**Ollama connection error:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama if needed
systemctl restart ollama  # or restart Ollama app
```

**Qdrant connection error:**
```bash
# Check Qdrant storage path exists
ls -la /home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag/qdrant_storage

# Re-index if needed (if you have indexing script)
# python src/retrieval/index_to_qdrant.py
```

**Import errors:**
```bash
# Make sure you're in the right directory
cd /home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag

# Make sure conda environment is activated
conda activate thu_tuc_rag

# Reinstall dependencies if needed
pip install -r requirements_backend.txt
```

### Frontend Issues

**Module not found errors:**
```bash
cd /home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag/fe

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**CORS errors:**
```bash
# Verify backend CORS settings in .env
cat ../.env | grep CORS

# Should be: CORS_ORIGINS=["http://localhost:3000"]
```

**API connection errors:**
```bash
# Verify .env.local
cat .env.local

# Should be: NEXT_PUBLIC_API_URL=http://localhost:8000

# Restart frontend after changing .env.local
npm run dev
```

---

## ⚙️ Configuration

### Backend (.env)

```bash
# Ollama
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=bge-m3
LLM_MODEL=qwen3:8b

# Qdrant
QDRANT_PATH=/home/admin123/Downloads/NHDanDz/ThuTucHanhChinh/thu_tuc_rag/qdrant_storage

# Session
SESSION_TTL_SECONDS=3600

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Server
HOST=0.0.0.0
PORT=8000
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📊 Performance Expectations

### Response Times (Local Ollama)

- **Query Enhancement**: 2-5 seconds
- **Vector Retrieval**: 0.1-0.5 seconds
- **Answer Generation**: **50-180 seconds** ⚠️
- **Total**: ~60-190 seconds per query

**Note:** Ollama local inference is slow. For production, consider using cloud LLM (OpenAI GPT-4, Claude 3.5) for 10-50x speedup.

### Concurrent Users

- **Local Ollama**: 1-2 concurrent users
- **Session Storage**: 1000 sessions max (in-memory)

---

## 🔄 Stopping the Application

### Stop Backend

In the terminal running backend:
```bash
# Press Ctrl+C
^C
```

### Stop Frontend

In the terminal running frontend:
```bash
# Press Ctrl+C
^C
```

---

## 📝 Usage Examples

### Basic Query

```
User: "Đăng ký kết hôn cần giấy tờ gì?"