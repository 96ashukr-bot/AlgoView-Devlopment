import Swal from 'sweetalert2';
import {
    clearAuthTokens,
    getAccessToken,
    getAuthenticatedApiBaseUrl,
    getAuthenticatedWsBaseUrl,
} from "../Services/authStorage";

export const REMOTE_API_BASE_URL = (process.env.REACT_APP_API_BASE_URL || "https://sparksadmin.algoview.in").replace(/\/$/, "");
export const REMOTE_WS_BASE_URL = (process.env.REACT_APP_WS_BASE_URL || REMOTE_API_BASE_URL.replace(/^http/i, "ws")).replace(/\/$/, "");

const browserHost = typeof window !== "undefined" ? window.location.hostname : "localhost";
const useLocalBackend = process.env.REACT_APP_USE_LOCAL_BACKEND === "true";
const isLocalLikeHost =
    browserHost === "localhost" ||
    browserHost === "127.0.0.1" ||
    browserHost === "0.0.0.0" ||
    /^192\.168\./.test(browserHost) ||
    /^10\./.test(browserHost) ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(browserHost);

const configuredApiBaseUrl = process.env.REACT_APP_API_BASE_URL;
const configuredWsBaseUrl = process.env.REACT_APP_WS_BASE_URL;
const storedApiBaseUrl =
    typeof window !== "undefined" ? window.localStorage.getItem("preferred_api_base_url") : null;
const storedWsBaseUrl =
    typeof window !== "undefined" ? window.localStorage.getItem("preferred_ws_base_url") : null;
const authenticatedApiBaseUrl = typeof window !== "undefined" ? getAuthenticatedApiBaseUrl() : null;
const authenticatedWsBaseUrl = typeof window !== "undefined" ? getAuthenticatedWsBaseUrl() : null;

const defaultApiBaseUrl = (useLocalBackend || isLocalLikeHost)
    ? `http://${browserHost}:8000`
    : REMOTE_API_BASE_URL;

const defaultWsBaseUrl = (useLocalBackend || isLocalLikeHost)
    ? `ws://${browserHost}:8080`
    : REMOTE_WS_BASE_URL;

const resolvedApiBaseUrl = isLocalLikeHost
    ? (configuredApiBaseUrl || defaultApiBaseUrl)
    : (configuredApiBaseUrl || authenticatedApiBaseUrl || storedApiBaseUrl || defaultApiBaseUrl);

const resolvedWsBaseUrl = isLocalLikeHost
    ? (configuredWsBaseUrl || defaultWsBaseUrl)
    : (configuredWsBaseUrl || authenticatedWsBaseUrl || storedWsBaseUrl || defaultWsBaseUrl);

export let baseUrl = resolvedApiBaseUrl.replace(/\/$/, "");
let wsBaseUrl = resolvedWsBaseUrl.replace(/\/$/, "");

export const setPreferredBackend = ({ apiBaseUrl, wsBaseUrl: nextWsBaseUrl, force = false }) => {
    if (isLocalLikeHost) {
        const forcedLocalApiBaseUrl = (configuredApiBaseUrl || defaultApiBaseUrl).replace(/\/$/, "");
        const forcedLocalWsBaseUrl = (configuredWsBaseUrl || defaultWsBaseUrl).replace(/\/$/, "");
        if (typeof window !== "undefined") {
            window.localStorage.removeItem("preferred_api_base_url");
            window.localStorage.removeItem("preferred_ws_base_url");
        }
        baseUrl = forcedLocalApiBaseUrl;
        wsBaseUrl = forcedLocalWsBaseUrl;
        return;
    }
    if (typeof window !== "undefined") {
        if (apiBaseUrl) {
            window.localStorage.setItem("preferred_api_base_url", apiBaseUrl);
        }
        if (nextWsBaseUrl) {
            window.localStorage.setItem("preferred_ws_base_url", nextWsBaseUrl);
        }
    }
    if (apiBaseUrl) {
        baseUrl = apiBaseUrl.replace(/\/$/, "");
    }
    if (nextWsBaseUrl) {
        wsBaseUrl = nextWsBaseUrl.replace(/\/$/, "");
    }
};

export const clearPreferredBackend = () => {
    if (typeof window !== "undefined") {
        window.localStorage.removeItem("preferred_api_base_url");
        window.localStorage.removeItem("preferred_ws_base_url");
    }
    baseUrl = (configuredApiBaseUrl || defaultApiBaseUrl).replace(/\/$/, "");
    wsBaseUrl = (configuredWsBaseUrl || defaultWsBaseUrl).replace(/\/$/, "");
};

export const getLocalApiBaseUrl = () => `http://${browserHost}:8000`;
export const getLocalWsBaseUrl = () => `ws://${browserHost}:8080`;

export const getWebSocketUrl = (Exchange, token) => {
    return `${wsBaseUrl}/ws/stock-live-price/?exchange_type=${Exchange}&symbol_tokens=${token}`;
};

export const getOptionChainSocketUrl = (symbol, expiry_date) => {
    return `${wsBaseUrl}/ws/option-chain/?name=${symbol}&expiry_date=${expiry_date}`;
}

export const getStockSymbolLivePriceSocketUrl = () =>{
    return `${wsBaseUrl}/ws/stock-symbol-live-price/?name=BANKNIFTY,NIFTY,FINNIFTY,MIDCPNIFTY,SENSEX`
}

export const getAuthToken = () => {
    return getAccessToken();
};

export const showAlert = (icon, title, text, confirmAction) => {
    Swal.fire({
        icon,
        title,
        text,
        confirmButtonText: 'OK',
    }).then((result) => {
        if (result.isConfirmed && confirmAction) {
            confirmAction();
        }
    });
};

export const handleAuthError = () => {
    showAlert('warning', 'Session Expired', 'Your session has expired. Please log in again.', () => {
        clearAuthTokens();
        window.location.replace('/login');
    });
};

export const handleNoTokenError = () => {
    showAlert('error', 'Authentication Error', 'No authentication token found. Please log in again.', () => {
        window.location.replace('/login');
    });
};
