/**
 * Header component
 */

import './Header.css';

interface HeaderProps {
  organizationName?: string;
  logoUrl?: string;
}

export const Header = ({
  organizationName = 'BỘ QUỐC PHÒNG',
  logoUrl = '/logo.png',
}: HeaderProps) => {
  return (
    <header className="header">
      <div className="header-container">
        <div className="header-logo">
          <img
            src={logoUrl}
            alt="Logo"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        </div>
        <div className="header-content">
          <h1 className="header-title">{organizationName}</h1>
          <p className="header-subtitle">Hệ thống tra cứu thủ tục hành chính</p>
        </div>
      </div>
    </header>
  );
};
