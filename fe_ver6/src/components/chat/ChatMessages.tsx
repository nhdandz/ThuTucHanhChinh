/**
 * Chat messages container component
 */

import { useEffect, useRef } from 'react';
import { UserMessage } from './UserMessage';
import { BotMessage } from './BotMessage';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { Message } from '../../services/types';
import './ChatMessages.css';

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

export const ChatMessages = ({ messages, isLoading }: ChatMessagesProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-messages" role="log" aria-live="polite">
      {messages.length === 0 && !isLoading && (
        <div className="chat-messages__empty">
          <h3>Chào mừng bạn đến với Hệ thống tra cứu thủ tục hành chính</h3>
          <p>
            Hãy đặt câu hỏi về các thủ tục hành chính hoặc sử dụng tìm kiếm để tra cứu
            thủ tục theo mã hoặc tên.
          </p>
        </div>
      )}

      {messages.map((message) =>
        message.type === 'user' ? (
          <UserMessage key={message.id} message={message} />
        ) : (
          <BotMessage key={message.id} message={message} />
        )
      )}

      {isLoading && (
        <div className="chat-messages__loading">
          <LoadingSpinner size="small" message="Đang xử lý câu hỏi..." />
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};
