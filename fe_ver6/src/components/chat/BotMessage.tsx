/**
 * Bot message component
 */

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatRelativeTime } from '../../utils/formatters';
import { removeThinkTags } from '../../utils/textFormatters';
import { ChevronDownIcon } from '../common/Icons';
import { StructuredProcedure } from '../procedures/StructuredProcedure';
import type { Message } from '../../services/types';
import './Message.css';

interface BotMessageProps {
  message: Message;
}

export const BotMessage = ({ message }: BotMessageProps) => {
  const [showSources, setShowSources] = useState(false);

  // Remove <think> tags from content
  const cleanedContent = removeThinkTags(message.content);

  return (
    <div className="message message--bot">
      <div className="message__content">
        <div className="message__answer markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {cleanedContent}
          </ReactMarkdown>
        </div>

        {message.structuredData && (
          <div className="message__structured">
            <StructuredProcedure data={message.structuredData} />
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="message__sources">
            <button
              className="message__sources-toggle"
              onClick={() => setShowSources(!showSources)}
              aria-expanded={showSources}
            >
              <span>Tài liệu tham khảo ({message.sources.length})</span>
              <ChevronDownIcon
                className={`message__sources-icon ${
                  showSources ? 'message__sources-icon--open' : ''
                }`}
              />
            </button>
            {showSources && (
              <ul className="message__sources-list">
                {message.sources.map((source, idx) => (
                  <li key={idx} className="message__sources-item">
                    <strong>{source.thu_tuc_name}</strong>
                    <span className="message__sources-code">
                      (Mã: {source.thu_tuc_code})
                    </span>
                    {source.content_snippet && (
                      <p className="message__sources-snippet">
                        {source.content_snippet}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <span className="message__timestamp">
          {formatRelativeTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
};
