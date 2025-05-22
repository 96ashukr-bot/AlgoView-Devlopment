import React, { createContext, useState, useEffect } from 'react';

export const LogoContext = createContext();

export const LogoProvider = ({ children }) => {
  const [logo, setLogo] = useState(localStorage.getItem('companyLogo') || '');

  return (
    <LogoContext.Provider value={{ logo, setLogo }}>
      {children}
    </LogoContext.Provider>
  );
};
