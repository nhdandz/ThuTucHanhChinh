/**
 * User message component
 */

import { formatRelativeTime } from '../../utils/formatters';
import type { Message } from '../../services/types';
import './Message.css';

interface UserMessageProps {
  message: Message;
}

export const UserMessage = ({ message }: UserMessageProps) => {
  return (
    <div className="message message--user">
      <div className="message__content">
        <p className="message__text">{message.content}</p>
        <span className="message__timestamp">
          {formatRelativeTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
};
