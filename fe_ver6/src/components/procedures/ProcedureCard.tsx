/**
 * Procedure card component
 */

import './ProcedureCard.css';

interface ProcedureCardProps {
  code: string;
  name: string;
  category?: string;
  onClick: () => void;
}

export const ProcedureCard = ({ code, name, category, onClick }: ProcedureCardProps) => {
  return (
    <button className="procedure-card" onClick={onClick}>
      <div className="procedure-card__code">{code}</div>
      <div className="procedure-card__name">{name}</div>
      {category && (
        <div className="procedure-card__category">
          <span className="procedure-card__badge">{category}</span>
        </div>
      )}
    </button>
  );
};
