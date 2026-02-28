import React from 'react';
import './Logo.css';

const Logo = ({ className = "" }) => {
  return (
    <div className={`logo-mark chrome-text ${className}`}>
      <div className="logo-orb"></div>
      BANCAFIEL
    </div>
  );
};

export default Logo;
