/**
 * Chat input component
 */

import { useState, useRef, type KeyboardEvent } from 'react';
import { SendIcon } from '../common/Icons';
import { MAX_MESSAGE_LENGTH } from '../../utils/constants';
import './ChatInput.css';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput = ({ onSend, disabled = false }: ChatInputProps) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled) {
      onSend(trimmedMessage);
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= MAX_MESSAGE_LENGTH) {
      setMessage(value);
      // Auto-resize textarea
      e.target.style.height = 'auto';
      e.target.style.height = e.target.scrollHeight + 'px';
    }
  };

  return (
    <div className="chat-input">
      <textarea
        ref={textareaRef}
        className="chat-input__textarea"
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Nhập câu hỏi của bạn... (Enter để gửi, Shift+Enter để xuống dòng)"
        disabled={disabled}
        rows={1}
        aria-label="Nhập câu hỏi"
      />
      <button
        className="chat-input__button"
        onClick={handleSend}
        disabled={!message.trim() || disabled}
        aria-label="Gửi tin nhắn"
      >
        <SendIcon />
      </button>
      <div className="chat-input__counter">
        {message.length}/{MAX_MESSAGE_LENGTH}
      </div>
    </div>
  );
};
