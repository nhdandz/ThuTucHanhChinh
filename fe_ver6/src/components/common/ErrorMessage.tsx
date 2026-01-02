/**
 * Error message component
 */

import './ErrorMessage.css';
import { CloseIcon } from './Icons';

interface ErrorMessageProps {
  message: string;
  onClose?: () => void;
}

export const ErrorMessage = ({ message, onClose }: ErrorMessageProps) => {
  return (
    <div className="error-message" role="alert">
      <div className="error-message__content">
        <span className="error-message__text">{message}</span>
        {onClose && (
          <button
            className="error-message__close"
            onClick={onClose}
            aria-label="Đóng thông báo lỗi"
          >
            <CloseIcon />
          </button>
        )}
      </div>
    </div>
  );
};
