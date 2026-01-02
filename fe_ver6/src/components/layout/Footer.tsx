/**
 * Footer component
 */

import './Footer.css';

export const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-container">
        <p className="footer-text">
          © {currentYear} Bộ Quốc phòng - Hệ thống tra cứu thủ tục hành chính
        </p>
        <p className="footer-text footer-text--secondary">
          Phiên bản 1.0.0
        </p>
      </div>
    </footer>
  );
};
