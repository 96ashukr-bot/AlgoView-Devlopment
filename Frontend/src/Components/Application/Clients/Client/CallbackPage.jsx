import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { handleAuthCallback } from '../../../../Services/Authentication';

const CallbackPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const state = queryParams.get('state') || 'default_state';

    const callbackPayload = {
      code: state === 'fyers'
        ? queryParams.get('auth_code') || queryParams.get('code')
        : queryParams.get('request_token') ||
          queryParams.get('RequestToken') ||
          queryParams.get('auth_token') ||
          queryParams.get('access_token') ||
          queryParams.get('jwtToken') ||
          queryParams.get('code'),
      auth_token: queryParams.get('auth_token') || queryParams.get('access_token') || queryParams.get('jwtToken'),
      refresh_token: queryParams.get('refresh_token') || queryParams.get('refreshToken'),
      feed_token: queryParams.get('feed_token') || queryParams.get('feedToken'),
    };

    const hasBrokerCallbackPayload = Boolean(
      callbackPayload.code ||
      callbackPayload.auth_token ||
      callbackPayload.refresh_token ||
      callbackPayload.feed_token
    );

    if (hasBrokerCallbackPayload) {
      const processAuthCallback = async () => {
        try {
          const data = await handleAuthCallback(state, callbackPayload);
          const callbackSucceeded =
            data?.status === 'success' ||
            data?.message === 'success' ||
            data?.message === 'Callback successful' ||
            data?.message === 'Tokens registered';

          if (callbackSucceeded) {
            window.dispatchEvent(new CustomEvent('broker-runtime-updated', { detail: data?.data || data }));
            navigate('/dashboard/algoviewtech/user');
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
