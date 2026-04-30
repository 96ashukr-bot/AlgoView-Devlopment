const ACCESS_TOKEN_KEY = "authToken";
const REFRESH_TOKEN_KEY = "refreshToken";
const LOGIN_FLAG_KEY = "login";
const AUTHENTICATED_FLAG_KEY = "authenticated";
const AUTH_API_BASE_URL_KEY = "authApiBaseUrl";
const AUTH_WS_BASE_URL_KEY = "authWsBaseUrl";
const BROKER_API_BASE_URL_KEY = "brokerApiBaseUrl";
const BROKER_WS_BASE_URL_KEY = "brokerWsBaseUrl";

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);

export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const getAccessTokenIssuedAt = () => {
  const accessToken = getAccessToken();
  if (!accessToken) {
    return null;
  }

  try {
    const [, payload] = accessToken.split(".");
    if (!payload) {
      return null;
    }

    const decodedPayload = JSON.parse(window.atob(payload));
    if (!decodedPayload?.iat) {
      return null;
    }

    return new Date(decodedPayload.iat * 1000).toISOString();
  } catch (_error) {
    return null;
  }
};

export const setAuthTokens = ({ accessToken, refreshToken }) => {
  if (accessToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  }

  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }

  localStorage.setItem(LOGIN_FLAG_KEY, JSON.stringify(true));
  localStorage.setItem(AUTHENTICATED_FLAG_KEY, JSON.stringify(true));
};

export const getAuthenticatedApiBaseUrl = () => localStorage.getItem(AUTH_API_BASE_URL_KEY);

export const getAuthenticatedWsBaseUrl = () => localStorage.getItem(AUTH_WS_BASE_URL_KEY);

export const getBrokerApiBaseUrl = () => localStorage.getItem(BROKER_API_BASE_URL_KEY);

export const getBrokerWsBaseUrl = () => localStorage.getItem(BROKER_WS_BASE_URL_KEY);

export const setAuthenticatedBackend = ({ apiBaseUrl, wsBaseUrl }) => {
  if (apiBaseUrl) {
    localStorage.setItem(AUTH_API_BASE_URL_KEY, apiBaseUrl);
  }
  if (wsBaseUrl) {
    localStorage.setItem(AUTH_WS_BASE_URL_KEY, wsBaseUrl);
  }
};

export const setBrokerBackend = ({ apiBaseUrl, wsBaseUrl }) => {
  if (apiBaseUrl) {
    localStorage.setItem(BROKER_API_BASE_URL_KEY, apiBaseUrl);
  }
  if (wsBaseUrl) {
    localStorage.setItem(BROKER_WS_BASE_URL_KEY, wsBaseUrl);
  }
};

export const clearAuthTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(LOGIN_FLAG_KEY);
  localStorage.removeItem(AUTHENTICATED_FLAG_KEY);
  localStorage.removeItem(AUTH_API_BASE_URL_KEY);
  localStorage.removeItem(AUTH_WS_BASE_URL_KEY);
  localStorage.removeItem(BROKER_API_BASE_URL_KEY);
  localStorage.removeItem(BROKER_WS_BASE_URL_KEY);
};

export const hasRefreshToken = () => Boolean(getRefreshToken());
