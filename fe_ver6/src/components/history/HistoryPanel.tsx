/**
 * History panel component
 */

import { useChat } from '../../context/ChatContext';
import { HistoryIcon, TrashIcon } from '../common/Icons';
import { truncateText } from '../../utils/formatters';
import './HistoryPanel.css';

export const HistoryPanel = () => {
  const { messages, clearSession } = useChat();

  // Get only user messages for history
  const userMessages = messages.filter((msg) => msg.type === 'user');

  return (
    <div className="history-panel">
      <div className="history-panel__header">
        <div className="history-panel__title">
          <HistoryIcon />
          <h3>Lịch sử hội thoại</h3>
        </div>
        {userMessages.length > 0 && (
          <button
            className="history-panel__clear"
            onClick={clearSession}
            aria-label="Xóa lịch sử"
            title="Xóa lịch sử"
          >
            <TrashIcon />
          </button>
        )}
      </div>

      <div className="history-panel__content">
        {userMessages.length === 0 ? (
          <p className="history-panel__empty">Chưa có câu hỏi nào</p>
        ) : (
          <ul className="history-panel__list">
            {userMessages.map((msg) => (
              <li key={msg.id} className="history-panel__item">
                <div className="history-panel__item-content">
                  <p className="history-panel__item-text">
                    {truncateText(msg.content, 80)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
