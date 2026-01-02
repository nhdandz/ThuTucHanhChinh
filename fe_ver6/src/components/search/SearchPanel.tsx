/**
 * Search panel component for procedure search
 */

import { useState } from 'react';
import { SearchIcon } from '../common/Icons';
import { useChat } from '../../context/ChatContext';
import { useDebounce } from '../../hooks/useDebounce';
import { DEBOUNCE_DELAY, POPULAR_PROCEDURES } from '../../utils/constants';
import './SearchPanel.css';

export const SearchPanel = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showResults, setShowResults] = useState(false);
  const debouncedSearchTerm = useDebounce(searchTerm, DEBOUNCE_DELAY);
  const { sendMessage } = useChat();

  // Simple client-side filtering using popular procedures
  // In a real app, this could fetch from an API or load a full procedures list
  const filteredProcedures = debouncedSearchTerm
    ? POPULAR_PROCEDURES.filter(
        (proc) =>
          proc.code.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
          proc.name.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
      )
    : [];

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setShowResults(true);
  };

  const handleProcedureSelect = (procedureName: string) => {
    sendMessage(`Cho tôi biết về thủ tục: ${procedureName}`);
    setSearchTerm('');
    setShowResults(false);
  };

  const handleBlur = () => {
    // Delay to allow click on results
    setTimeout(() => setShowResults(false), 200);
  };

  return (
    <div className="search-panel">
      <div className="search-panel__input-wrapper">
        <SearchIcon className="search-panel__icon" />
        <input
          type="text"
          className="search-panel__input"
          placeholder="Tìm kiếm thủ tục theo mã hoặc tên..."
          value={searchTerm}
          onChange={handleSearchChange}
          onFocus={() => setShowResults(true)}
          onBlur={handleBlur}
          aria-label="Tìm kiếm thủ tục"
        />
      </div>

      {showResults && filteredProcedures.length > 0 && (
        <div className="search-panel__results">
          <ul className="search-panel__results-list">
            {filteredProcedures.map((proc) => (
              <li key={proc.id} className="search-panel__result-item">
                <button
                  className="search-panel__result-button"
                  onClick={() => handleProcedureSelect(proc.name)}
                >
                  <span className="search-panel__result-code">{proc.code}</span>
                  <span className="search-panel__result-name">{proc.name}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {showResults && searchTerm && filteredProcedures.length === 0 && (
        <div className="search-panel__results">
          <p className="search-panel__no-results">
            Không tìm thấy thủ tục phù hợp. Vui lòng thử từ khóa khác.
          </p>
        </div>
      )}
    </div>
  );
};
