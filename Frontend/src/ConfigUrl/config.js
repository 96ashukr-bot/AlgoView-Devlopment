import Swal from 'sweetalert2';

// export const baseUrl = "http://127.0.0.1:8000";

// This is a produnction url : -->
export const baseUrl = "https://sparksadmin.algoview.in";

// This is a Staging env baseUrl : -->
// export const baseUrl = "http://13.232.196.124";

export const getWebSocketUrl = (Exchange, token) => {
    // return `ws://127.0.0.1:8080/ws/stock-live-price/?exchange_type=${Exchange}&symbol_tokens=${token}`;
    // return `ws://13.232.196.124/ws/stock-live-price/?exchange_type=${Exchange}&symbol_tokens=${token}`;
    return `wss://sparksadmin.algoview.in/ws/stock-live-price/?exchange_type=${Exchange}&symbol_tokens=${token}`;
};

export const getOptionChainSocketUrl = (symbol, expiry_date) => {
    // return `ws://127.0.0.1:8080/ws/option-chain/?name=${symbol}&expiry_date=${expiry_date}`;
    // return `ws://13.232.196.124/ws/option-chain/?name=${symbol}&expiry_date=${expiry_date}`;
    return `wss://sparksadmin.algoview.in/ws/option-chain/?name=${symbol}&expiry_date=${expiry_date}`;
}

export const getStockSymbolLivePriceSocketUrl = () =>{
    return `wss://sparksadmin.algoview.in/ws/stock-symbol-live-price/?name=BANKNIFTY,NIFTY,FINNIFTY,MIDCPNIFTY,SENSEX`
}

export const getAuthToken = () => {
    const token = localStorage.getItem('authToken');
    console.log('Retrieved token:', token);
    return token;
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
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        window.location.replace('/login');
    });
};

export const handleNoTokenError = () => {
    showAlert('error', 'Authentication Error', 'No authentication token found. Please log in again.', () => {
        window.location.replace('/login');
    });
};
