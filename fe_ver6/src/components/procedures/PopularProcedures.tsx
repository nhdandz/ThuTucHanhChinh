/**
 * Popular procedures component
 */

import { useChat } from '../../context/ChatContext';
import { POPULAR_PROCEDURES } from '../../utils/constants';
import { ProcedureCard } from './ProcedureCard';
import './PopularProcedures.css';

export const PopularProcedures = () => {
  const { sendMessage } = useChat();

  const handleProcedureClick = (procedureName: string) => {
    sendMessage(`Cho tôi biết về thủ tục: ${procedureName}`);
  };

  return (
    <div className="popular-procedures">
      <div className="popular-procedures__header">
        <h3>Thủ tục phổ biến</h3>
        <p className="popular-procedures__subtitle">
          Click để xem chi tiết
        </p>
      </div>

      <div className="popular-procedures__list">
        {POPULAR_PROCEDURES.map((procedure) => (
          <ProcedureCard
            key={procedure.id}
            code={procedure.code}
            name={procedure.name}
            category={procedure.category}
            onClick={() => handleProcedureClick(procedure.name)}
          />
        ))}
      </div>
    </div>
  );
};
