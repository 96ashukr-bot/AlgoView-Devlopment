import Swal from 'sweetalert2';
import {
    clearAuthTokens,
    getAccessToken,
    getAuthenticatedApiBaseUrl,
    getAuthenticatedWsBaseUrl,
} from "../Services/authStorage";

export const BASE_URL = "/api";

const browserWsOrigin =
    typeof window !== "undefined"
        ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`
        : "";

export const getWsBaseUrlForApi = (apiBaseUrl = BASE_URL) => {
    const normalizedApiBaseUrl = String(apiBaseUrl || BASE_URL).replace(/\/$/, "");
    if (/^https?:\/\//i.test(normalizedApiBaseUrl)) {
        return normalizedApiBaseUrl.replace(/^http/i, "ws").replace(/\/api$/, "");
    }
    return browserWsOrigin;
};

export const REMOTE_API_BASE_URL = (process.env.REACT_APP_API_BASE_URL || BASE_URL).replace(/\/$/, "");
export const REMOTE_WS_BASE_URL = (process.env.REACT_APP_WS_BASE_URL || getWsBaseUrlForApi(REMOTE_API_BASE_URL)).replace(/\/$/, "");

const configuredApiBaseUrl = process.env.REACT_APP_API_BASE_URL;
const configuredWsBaseUrl = process.env.REACT_APP_WS_BASE_URL;
const normalizeStoredApiBaseUrl = (value) => {
    if (!value || typeof window === "undefined") {
        return value;
    }
    if (!/^https?:\/\//i.test(value)) {
        return value;
    }
    try {
        const parsed = new URL(value);
        if (parsed.origin !== window.location.origin) {
            window.localStorage.removeItem("preferred_api_base_url");
            window.localStorage.removeItem("preferred_ws_base_url");
            return null;
        }
    } catch (_error) {
        window.localStorage.removeItem("preferred_api_base_url");
        window.localStorage.removeItem("preferred_ws_base_url");
        return null;
    }
    return value;
};

const storedApiBaseUrl =
    typeof window !== "undefined" ? normalizeStoredApiBaseUrl(window.localStorage.getItem("preferred_api_base_url")) : null;
const storedWsBaseUrl =
    typeof window !== "undefined" ? window.localStorage.getItem("preferred_ws_base_url") : null;
const authenticatedApiBaseUrl = typeof window !== "undefined" ? getAuthenticatedApiBaseUrl() : null;
const authenticatedWsBaseUrl = typeof window !== "undefined" ? getAuthenticatedWsBaseUrl() : null;

const defaultApiBaseUrl = process.env.REACT_APP_API_BASE_URL || BASE_URL;

const defaultWsBaseUrl = process.env.REACT_APP_WS_BASE_URL || getWsBaseUrlForApi(defaultApiBaseUrl);

const resolvedApiBaseUrl = configuredApiBaseUrl || authenticatedApiBaseUrl || storedApiBaseUrl || defaultApiBaseUrl;

const resolvedWsBaseUrl = configuredWsBaseUrl || authenticatedWsBaseUrl || storedWsBaseUrl || defaultWsBaseUrl;

export let baseUrl = resolvedApiBaseUrl.replace(/\/$/, "");
let wsBaseUrl = resolvedWsBaseUrl.replace(/\/$/, "");

export const setPreferredBackend = ({ apiBaseUrl, wsBaseUrl: nextWsBaseUrl, force = false }) => {
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

export const getLocalApiBaseUrl = () => BASE_URL;
export const getLocalWsBaseUrl = () => getWsBaseUrlForApi(BASE_URL);

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
