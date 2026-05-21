import React, { createContext, useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { baseUrl } from '../../../ConfigUrl/config';
import { getAccessToken } from '../../../Services/authStorage';

export const LogoContext = createContext();

const resolveLogoUrl = (logoPath) => {
  if (!logoPath) return '';
  if (/^https?:\/\//i.test(logoPath) || logoPath.startsWith('data:')) {
    return logoPath;
  }

  const normalizedPath = logoPath.startsWith('/') ? logoPath : `/${logoPath}`;
  const apiBase = String(baseUrl || '').replace(/\/$/, '');
  const mediaBase = apiBase.replace(/\/api$/, '');
  return `${mediaBase}${normalizedPath}`;
};

export const LogoProvider = ({ children }) => {
  const [logo, setLogo] = useState(localStorage.getItem('companyLogo') || '');

  const refreshLogo = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;

    try {
      const response = await axios.get(`${baseUrl}/get-company-profile/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const logoUrl = resolveLogoUrl(response.data?.data?.company_logo);
      if (logoUrl) {
        localStorage.setItem('companyLogo', logoUrl);
        setLogo(logoUrl);
      }
    } catch (error) {
      console.error('Error refreshing company logo:', error.response?.data?.message || error.message);
    }
  }, []);

  useEffect(() => {
    refreshLogo();
    window.addEventListener('focus', refreshLogo);
    return () => window.removeEventListener('focus', refreshLogo);
  }, [refreshLogo]);

  return (
    <LogoContext.Provider value={{ logo, setLogo, refreshLogo }}>
      {children}
    </LogoContext.Provider>
  );
};
