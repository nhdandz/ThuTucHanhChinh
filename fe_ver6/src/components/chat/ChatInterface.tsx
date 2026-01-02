/**
 * Main chat interface component
 */

import { useChat } from '../../context/ChatContext';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';
import { ErrorMessage } from '../common/ErrorMessage';
import './ChatInterface.css';

export const ChatInterface = () => {
  const { messages, isLoading, error, sendMessage, clearError } = useChat();

  return (
    <div className="chat-interface">
      {error && <ErrorMessage message={error} onClose={clearError} />}
      <ChatMessages messages={messages} isLoading={isLoading} />
      <div className="chat-interface__input">
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>
    </div>
  );
};
