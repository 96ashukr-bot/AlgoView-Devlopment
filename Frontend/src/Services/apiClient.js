import axios from "axios";
import { baseUrl } from "../ConfigUrl/config";
import {
  clearAuthTokens,
  getAccessToken,
  getAuthenticatedApiBaseUrl,
  getRefreshToken,
  setAuthenticatedBackend,
  setAuthTokens,
} from "./authStorage";

const PUBLIC_ENDPOINTS = [
  "/login/",
  "/signup/",
  "/verify-otp/",
  "/resend-otp/",
  "/password-reset-request/",
  "/password-reset-confirm/",
  "/token/refresh/",
];

const apiClient = axios.create({
  baseURL: baseUrl,
});

let refreshPromise = null;

const authDebug = (event, details = {}) => {
  if (typeof window === "undefined" || process.env.NODE_ENV === "production") {
    return;
  }
  console.info("[auth-debug]", event, details);
};

const isPublicEndpoint = (url = "") => PUBLIC_ENDPOINTS.some((endpoint) => url.endsWith(endpoint));

const redirectToLogin = () => {
  if (typeof window === "undefined") {
    return;
  }

  const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (!currentPath.includes("/login")) {
    window.location.replace("/login");
  }
};

const getTargetBaseUrl = (requestUrl = "") => {
  if (typeof requestUrl === "string" && /^https?:\/\//i.test(requestUrl)) {
    try {
      return new URL(requestUrl).origin;
    } catch (_error) {
      return getAuthenticatedApiBaseUrl() || baseUrl;
    }
  }
  return getAuthenticatedApiBaseUrl() || baseUrl;
};

const requestTokenRefresh = async (targetBaseUrl = null) => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error("No refresh token found.");
  }

  const refreshBaseUrl = (targetBaseUrl || getAuthenticatedApiBaseUrl() || baseUrl).replace(/\/$/, "");
  authDebug("refresh:start", {
    backend: refreshBaseUrl,
    hasAccessToken: Boolean(getAccessToken()),
    hasRefreshToken: Boolean(refreshToken),
  });

  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${refreshBaseUrl}/token/refresh/`, { refresh: refreshToken }, { skipAuthRefresh: true })
      .then((response) => {
        const nextAccessToken = response?.data?.access;
        const nextRefreshToken = response?.data?.refresh || refreshToken;
        if (!nextAccessToken) {
          throw new Error("Token refresh did not return a new access token.");
        }

        setAuthTokens({ accessToken: nextAccessToken, refreshToken: nextRefreshToken });
        setAuthenticatedBackend({ apiBaseUrl: refreshBaseUrl });
        authDebug("refresh:success", {
          backend: refreshBaseUrl,
          rotatedRefreshToken: Boolean(response?.data?.refresh),
        });
        return nextAccessToken;
      })
      .catch((error) => {
        authDebug("refresh:failure", {
          backend: refreshBaseUrl,
          status: error?.response?.status || null,
        });
        clearAuthTokens();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
};

apiClient.interceptors.request.use(
  (config) => {
    const nextConfig = { ...config };
    const accessToken = getAccessToken();

    if (!nextConfig.skipAuthRefresh && accessToken && !isPublicEndpoint(nextConfig.url || "")) {
      nextConfig.headers = nextConfig.headers || {};
      nextConfig.headers.Authorization = `Bearer ${accessToken}`;
      authDebug("request:auth-header", {
        url: nextConfig.url || "",
        hasAccessToken: true,
        backend: getTargetBaseUrl(nextConfig.url || ""),
      });
    }

    return nextConfig;
  },
  (error) => Promise.reject(error),
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config || {};
    const responseStatus = error.response?.status;
    const responseCode = error.response?.data?.code;
    const shouldRefresh =
      responseStatus === 401 &&
      !originalRequest._retry &&
      !originalRequest.skipAuthRefresh &&
      !isPublicEndpoint(originalRequest.url || "") &&
      (Boolean(getRefreshToken()) || responseCode === "token_not_valid");

    if (!shouldRefresh) {
      if (responseStatus === 401 && !originalRequest.skipAuthRefresh && !isPublicEndpoint(originalRequest.url || "")) {
        clearAuthTokens();
        redirectToLogin();
      }
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const nextAccessToken = await requestTokenRefresh(getTargetBaseUrl(originalRequest.url || ""));
      originalRequest.headers = originalRequest.headers || {};
      originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`;
      authDebug("request:retry-after-refresh", {
        url: originalRequest.url || "",
        backend: getTargetBaseUrl(originalRequest.url || ""),
      });
      return apiClient(originalRequest);
    } catch (refreshError) {
      clearAuthTokens();
      redirectToLogin();
      return Promise.reject(refreshError);
    }
  },
);

export { requestTokenRefresh };
export default apiClient;
