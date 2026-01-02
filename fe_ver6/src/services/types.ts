/**
 * TypeScript interfaces matching backend API responses
 */

export interface SourceCitation {
  chunk_id: string;
  thu_tuc_name: string;
  thu_tuc_code: string;
  chunk_type: string;
  relevance_score: number;
  content_snippet: string;
}

export interface StructuredData {
  metadata?: {
    mã_thủ_tục?: string;
    tên_thủ_tục?: string;
    cấp_thực_hiện?: string;
    loại_thủ_tục?: string;
    lĩnh_vực?: string;
  };
  content?: {
    trình_tự_thực_hiện?: string;
    đối_tượng_thực_hiện?: string;
    cơ_quan_thực_hiện?: string;
    kết_quả_thực_hiện?: string;
    thời_gian_giải_quyết?: string;
    phí_lệ_phí?: string;
    địa_điểm_thực_hiện?: string;
  };
  tables?: {
    hinh_thuc_nop?: Array<{
      [key: string]: string;
    }>;
    thanh_phan_ho_so?: Array<{
      [key: string]: string;
    }>;
    can_cu_phap_ly?: Array<{
      [key: string]: string;
    }>;
  };
}

export interface ChatQueryResponse {
  session_id: string;
  message_id: string;
  query: string;
  answer: string;
  structured_data: StructuredData | null;
  sources: SourceCitation[];
  confidence: number;
  intent: string;
  timestamp: string;
}

export interface ChatMessage {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  structured_data?: StructuredData | null;
  sources?: SourceCitation[];
  timestamp: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessage[];
  created_at: string;
  last_updated: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  qdrant_status: string;
  ollama_status: string;
  version: string;
  timestamp: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  timestamp: string;
}

// Frontend-specific types
export interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  structuredData?: StructuredData | null;
  sources?: SourceCitation[];
  timestamp: Date;
}

export interface Procedure {
  id: string;
  code: string;
  name: string;
  category?: string;
  level?: string;
}
