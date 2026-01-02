/**
 * API service layer for backend communication
 */

import axios, { type AxiosInstance } from 'axios';
import { API_BASE_URL, ENDPOINTS } from '../utils/constants';
import type {
  ChatQueryResponse,
  ChatHistoryResponse,
  HealthResponse,
  ErrorResponse,
} from './types';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 120000, // 2 minutes - RAG pipeline can take time
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // Server responded with error status
          const errorData = error.response.data as ErrorResponse;
          throw new Error(errorData.message || 'Đã có lỗi xảy ra từ máy chủ');
        } else if (error.request) {
          // Request was made but no response
          throw new Error('Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối.');
        } else {
          // Something else happened
          throw new Error(error.message || 'Đã có lỗi xảy ra');
        }
      }
    );
  }

  async sendQuery(
    query: string,
    sessionId: string | null,
    includeStructured = true
  ): Promise<ChatQueryResponse> {
    const response = await this.client.post<ChatQueryResponse>(ENDPOINTS.CHAT_QUERY, {
      query,
      session_id: sessionId,
      include_sources: true,
      include_structured: includeStructured,
    });
    return response.data;
  }

  async getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const response = await this.client.get<ChatHistoryResponse>(
      `${ENDPOINTS.CHAT_HISTORY}/${sessionId}`
    );
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`${ENDPOINTS.DELETE_SESSION}/${sessionId}`);
  }

  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>(ENDPOINTS.HEALTH);
    return response.data;
  }
}

export const apiService = new ApiService();
