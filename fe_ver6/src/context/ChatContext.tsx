/**
 * ChatContext - Global state management for chat functionality
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import { apiService } from '../services/api';
import { getSessionId, saveSessionId, clearSessionId } from '../utils/sessionManager';
import type { Message } from '../services/types';

interface ChatContextType {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  sendMessage: (query: string) => Promise<void>;
  loadHistory: () => Promise<void>;
  clearSession: () => void;
  clearError: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Load session ID on mount
  useEffect(() => {
    const storedSessionId = getSessionId();
    if (storedSessionId) {
      setSessionId(storedSessionId);
      // Optionally load history here
    }
  }, []);

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim()) return;

    // Add user message immediately
    const userMessage: Message = {
      id: crypto.randomUUID(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const currentSessionId = getSessionId();
      const response = await apiService.sendQuery(query, currentSessionId);

      // Save session ID
      saveSessionId(response.session_id);
      setSessionId(response.session_id);

      // Add bot message
      const botMessage: Message = {
        id: response.message_id,
        type: 'bot',
        content: response.answer,
        structuredData: response.structured_data,
        sources: response.sources,
        timestamp: new Date(response.timestamp),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Đã có lỗi xảy ra';
      setError(errorMessage);
      console.error('Error sending message:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    const currentSessionId = getSessionId();
    if (!currentSessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const history = await apiService.getChatHistory(currentSessionId);

      // Convert API messages to frontend Message format
      const convertedMessages: Message[] = history.messages.map((msg) => ({
        id: msg.message_id,
        type: msg.role === 'user' ? 'user' : 'bot',
        content: msg.content,
        structuredData: msg.structured_data,
        sources: msg.sources,
        timestamp: new Date(msg.timestamp),
      }));

      setMessages(convertedMessages);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Không thể tải lịch sử';
      setError(errorMessage);
      console.error('Error loading history:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearSession = useCallback(() => {
    const currentSessionId = getSessionId();
    if (currentSessionId) {
      apiService.deleteSession(currentSessionId).catch(console.error);
    }
    clearSessionId();
    setSessionId(null);
    setMessages([]);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        isLoading,
        error,
        sessionId,
        sendMessage,
        loadHistory,
        clearSession,
        clearError,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within ChatProvider');
  }
  return context;
};
