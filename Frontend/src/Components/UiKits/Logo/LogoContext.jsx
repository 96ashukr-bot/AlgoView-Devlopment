import React, { createContext, useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { baseUrl } from '../../../ConfigUrl/config';
import { getAccessToken } from '../../../Services/authStorage';

export const LogoContext = createContext();

const resolveAssetUrl = (assetPath) => {
  if (!assetPath) return '';
  if (/^https?:\/\//i.test(assetPath) || assetPath.startsWith('data:') || assetPath.startsWith('blob:')) {
    return assetPath;
  }

  const normalizedPath = assetPath.startsWith('/') ? assetPath : `/${assetPath}`;
  const apiBase = String(baseUrl || '').replace(/\/$/, '');
  const mediaBase = apiBase.replace(/\/api$/, '');
  return `${mediaBase}${normalizedPath}`;
};

const updateFavicon = (faviconUrl) => {
  const existingFavicons = document.querySelectorAll("link[rel~='icon']");
  existingFavicons.forEach((link) => link.parentNode.removeChild(link));

  const newLink = document.createElement('link');
  newLink.rel = 'icon';
  newLink.href = faviconUrl || '/favicon.png';
  document.head.appendChild(newLink);
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
      const logoUrl = resolveAssetUrl(response.data?.data?.company_logo);
      if (logoUrl) {
        localStorage.setItem('companyLogo', logoUrl);
        setLogo(logoUrl);
      }
      const faviconUrl = resolveAssetUrl(response.data?.data?.company_favicon);
      if (faviconUrl) {
        localStorage.setItem('companyFavicon', faviconUrl);
        updateFavicon(faviconUrl);
      }
    } catch (error) {
      console.error('Error refreshing company branding:', error.response?.data?.message || error.message);
    }
  }, []);

  useEffect(() => {
    updateFavicon(localStorage.getItem('companyFavicon'));
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
