/**
 * Application constants
 */

// Use empty string to use Vite proxy (configured in vite.config.ts)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const ENDPOINTS = {
  CHAT_QUERY: '/api/chat/query',
  CHAT_HISTORY: '/api/chat/history',
  DELETE_SESSION: '/api/chat/session',
  HEALTH: '/api/health',
} as const;

export const POPULAR_PROCEDURES = [
  {
    id: '1',
    code: '1.013124',
    name: 'Thủ tục thẩm định kế hoạch ứng phó sự cố tràn dầu',
    category: 'Ứng phó sự cố',
  },
  {
    id: '2',
    code: '1.002345',
    name: 'Thủ tục đăng ký phương tiện quân sự',
    category: 'Đăng ký',
  },
  {
    id: '3',
    code: '1.003456',
    name: 'Thủ tục cấp giấy phép hoạt động',
    category: 'Cấp phép',
  },
  {
    id: '4',
    code: '1.004567',
    name: 'Thủ tục xét duyệt hồ sơ nghĩa vụ quân sự',
    category: 'Nghĩa vụ quân sự',
  },
  {
    id: '5',
    code: '1.005678',
    name: 'Thủ tục cấp chứng nhận đủ điều kiện',
    category: 'Chứng nhận',
  },
] as const;

export const SESSION_STORAGE_KEY = 'chat_session_id';

export const DEBOUNCE_DELAY = 300; // milliseconds

export const MAX_MESSAGE_LENGTH = 1000;
