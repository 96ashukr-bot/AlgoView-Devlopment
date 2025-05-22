import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { handleAuthCallback } from '../../../../Services/Authentication';

const CallbackPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const currentUrl = window.location.href;

    const state = queryParams.get('state') || (
      currentUrl.includes('algoview.in/callback') ? 'zerodha' : 'default_state'
    );

    const code = state === 'fyers'
      ? queryParams.get('auth_code') || queryParams.get('code') || 'default_code_fyers'
      : queryParams.get('request_token') ||
        queryParams.get('RequestToken') ||
        queryParams.get('code') ||
        'default_code_others';

    console.log('Current URL:', currentUrl);
    console.log('Extracted Code:', code);
    console.log('Extracted State:', state);

    if (code) {
      const processAuthCallback = async () => {
        try {
          const data = await handleAuthCallback(state, code);
          console.log('Callback API response:', data);

          if (data.message === 'success' && data.access_token) {
            console.log('Received Access Token:', data.access_token);
            localStorage.setItem('access_token', data.access_token);
            navigate('/dashboard/algoviewtech/user');
          } else {
            console.error('API call failed:', data.message);
          }
        } catch (error) {
          console.error('Error with API call:', error.message);
        }
      };

      processAuthCallback();
    }
  }, [navigate]);

  return null;
};

export default CallbackPage;
