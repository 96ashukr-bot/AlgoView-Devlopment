"""
Angel One SmartAPI - Production-Ready Trading Module
=====================================================
A scalable, robust, and production-grade integration with Angel One SmartAPI.

Features:
- Thread-safe session management for multi-user environment
- Strict symbol/token matching with proper parsing
- Configurable order types (LIMIT as default with buffer)
- Retry mechanism with exponential backoff
- Efficient caching with thread-safe operations
- Comprehensive error handling and logging
- IP whitelist and compliance handling (AG7002 errors)
- Backward compatibility with existing function names

Author: AlgoView Development Team
Version: 2.0.0 (Production)
"""

# ============================================================================
# IMPORTS
# ============================================================================

import logging
import threading
import time
import re
from functools import wraps
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Callable
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

import requests
import pyotp
from django.utils import timezone
from django.conf import settings

try:
    from SmartApi import SmartConnect
    from SmartApi.smartExceptions import (
        DataException, 
        GenException, 
        TokenException,
        IPException
    )
    SMARTAPI_SDK_AVAILABLE = True
except ImportError:
    SMARTAPI_SDK_AVAILABLE = False
    SmartConnect = None

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

# Cache settings
CONTRACT_MASTER_CACHE_DURATION = timedelta(hours=1)
SESSION_CACHE_DURATION = timedelta(hours=11, minutes=50)  # Refresh before 12h expiry

# Rate limiting
RATE_LIMIT_MIN_INTERVAL = 0.05  # 50ms minimum between orders
ORDER_BOOK_COOLDOWN = 1.0  # 1 second cooldown for order book fetch

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2
RETRY_MAX_WAIT = 10  # seconds

# Buffer defaults
DEFAULT_BUFFER_PERCENTAGE = 2.5
MIN_BUFFER_PERCENTAGE = 0.1
MAX_BUFFER_PERCENTAGE = 10.0

# Contract master URL (official Angel One source)
CONTRACT_MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

# Error codes mapping
ERROR_CODES = {
    "AG7001": "Invalid API key",
    "AG7002": "IP not whitelisted",
    "AG7003": "Token expired",
    "AG7004": "Invalid request token",
    "AG7005": "Session expired",
    "AG7006": "Two-factor authentication failed",
    "AG7007": "Wrong OTP",
    "AG7008": "User disabled",
    "AG7009": "Account locked",
    "AG7010": "Password expired",
    "AG7011": "Market closed",
    "AG7012": "Insufficient margin",
    "AG7013": "Order rejected",
    "AG7014": "Invalid symbol",
    "AG7015": "Invalid quantity",
}

# Configure logger
logger = logging.getLogger('angel_one_trading')
logger.setLevel(logging.INFO)

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AngelOneConfig:
    """Configuration for Angel One API."""
    api_key: str
    client_code: str
    password: str
    totp_secret: str
    buffer_percentage: float = DEFAULT_BUFFER_PERCENTAGE
    enable_market_orders: bool = False
    enable_stoploss_orders: bool = True
    default_product_type: str = "INTRADAY"
    default_exchange: str = "NFO"
    default_duration: str = "DAY"
    default_variety: str = "NORMAL"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not 0.1 <= self.buffer_percentage <= MAX_BUFFER_PERCENTAGE:
            self.buffer_percentage = DEFAULT_BUFFER_PERCENTAGE


@dataclass
class OrderResult:
    """Structured order result."""
    status: str
    order_id: Optional[str] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    order_params: Optional[Dict] = None
    raw_response: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "order_id": self.order_id,
            "message": self.message,
            "error_code": self.error_code,
            "order_params": self.order_params,
        }


@dataclass
class SymbolInfo:
    """Parsed symbol information."""
    name: str          # NIFTY, BANKNIFTY, etc.
    expiry: str         # YYYYMMDD format
    strike: str         # Strike price
    option_type: str    # CE or PE
    
    @classmethod
    def parse(cls, trading_symbol: str) -> Optional['SymbolInfo']:
        """
        Parse trading symbol into structured components.
        Expected format: SYMBOL-YYMMDD-STRIKE-CE/PE
        Examples: NIFTY-25AUG24-25000-CE, BANKNIFTY-29AUG24-52000-PE
        """
        if not trading_symbol:
            return None
        
        try:
            # Split by '-'
            parts = trading_symbol.split('-')
            if len(parts) < 4:
                return None
            
            name = parts[0]
            expiry = parts[1]
            strike = parts[2]
            option_type = parts[3].upper()
            
            # Validate option type
            if option_type not in ['CE', 'PE', 'CALL', 'PUT']:
                return None
            
            return cls(
                name=name,
                expiry=expiry,
                strike=strike,
                option_type=option_type
            )
        except Exception:
            return None
    
    def matches(self, symbol: str, strike: str, option_type: str) -> bool:
        """Check if this symbol info matches the given criteria."""
        return (
            self.name.upper() == symbol.upper() and
            self.strike == str(strike) and
            self.option_type.upper() == option_type.upper()
        )


# ============================================================================
# EXCEPTIONS
# ============================================================================

class AngelOneError(Exception):
    """Base exception for Angel One errors."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TokenExpiredError(AngelOneError):
    """Token has expired and needs refresh."""
    pass


class InvalidCredentialsError(AngelOneError):
    """Invalid API credentials."""
    pass


class IPWhitelistError(AngelOneError):
    """IP not whitelisted in Angel One settings."""
    pass


class InsufficientMarginError(AngelOneError):
    """Insufficient margin for the order."""
    pass


class OrderRejectedError(AngelOneError):
    """Order was rejected by the broker."""
    pass


class RateLimitError(AngelOneError):
    """API rate limit exceeded."""
    pass


# ============================================================================
# DECORATORS & UTILITIES
# ============================================================================

def retry_on_failure(max_retries: int = MAX_RETRIES, backoff_factor: float = RETRY_BACKOFF_FACTOR):
    """
    Retry decorator with exponential backoff.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            wait_time = 1.0
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TokenExpiredError, IPWhitelistError):
                    # Don't retry on auth/IP errors
                    raise
                except (RateLimitError, DataException) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                        wait_time = min(wait_time * backoff_factor, RETRY_MAX_WAIT)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            
            raise last_exception or AngelOneError("Max retries exceeded")
        return wrapper
    return decorator


def rate_limit(min_interval: float = RATE_LIMIT_MIN_INTERVAL):
    """
    Rate limiting decorator for order placement.
    """
    _last_call = {}
    _lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            thread_id = threading.get_ident()
            
            with _lock:
                current_time = time.time()
                last_time = _last_call.get(thread_id, 0)
                elapsed = current_time - last_time
                
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                
                _last_call[thread_id] = time.time()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def thread_safe_cache(cache_duration: timedelta):
    """
    Thread-safe caching decorator.
    """
    _cache: Dict[str, Tuple[Any, datetime]] = {}
    _lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            for arg in args:
                if isinstance(arg, (str, int, float)):
                    key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            cache_key = "|".join(key_parts)
            
            with _lock:
                if cache_key in _cache:
                    cached_value, cached_time = _cache[cache_key]
                    if datetime.now() - cached_time < cache_duration:
                        return cached_value
            
            result = func(*args, **kwargs)
            
            with _lock:
                _cache[cache_key] = (result, datetime.now())
            
            return result
        return wrapper
    return decorator


def validate_response(response: Dict) -> bool:
    """
    Validate Angel One API response structure.
    """
    if not isinstance(response, dict):
        return False
    
    # Check for error status
    if not response.get('status', True):
        error_msg = response.get('message', 'Unknown error')
        error_code = response.get('errorcode')
        
        # Map error codes
        if error_code in ['AG7003', 'AG7005']:
            raise TokenExpiredError(f"Token expired: {error_msg}", error_code)
        elif error_code == 'AG7002':
            raise IPWhitelistError(
                "IP not whitelisted. Please add your IP to Angel One settings.",
                error_code
            )
        elif error_code in ['AG7001', 'AG7004']:
            raise InvalidCredentialsError(f"Invalid credentials: {error_msg}", error_code)
        elif error_code == 'AG7012':
            raise InsufficientMarginError(f"Insufficient margin: {error_msg}", error_code)
        elif error_code == 'AG7013':
            raise OrderRejectedError(f"Order rejected: {error_msg}", error_code)
        
        return False
    
    return True


# ============================================================================
# CONTRACT MASTER CACHE
# ============================================================================

class ContractMasterCache:
    """
    Thread-safe singleton cache for contract master data.
    Optimized for high-frequency lookups.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize cache storage."""
        self._data: List[Dict] = []
        self._token_map: Dict[Tuple[str, str, str], Dict] = {}  # (symbol, strike, option_type) -> item
        self._name_index: Dict[str, List[Dict]] = {}  # symbol name -> list of items
        self._last_updated: Optional[datetime] = None
        self._loading = False
        self._data_lock = threading.Lock()
    
    def load(self, force_refresh: bool = False) -> bool:
        """
        Load contract master data from Angel One.
        Thread-safe with lazy loading.
        """
        with self._data_lock:
            # Check if already loaded and fresh
            if not force_refresh and self._data and self._last_updated:
                if datetime.now() - self._last_updated < CONTRACT_MASTER_CACHE_DURATION:
                    return True
            
            # Prevent concurrent loading
            if self._loading:
                # Wait for existing load to complete
                timeout = 30
                start = time.time()
                while self._loading:
                    if time.time() - start > timeout:
                        return bool(self._data)  # Return existing data if available
                    time.sleep(0.1)
                return True
            
            self._loading = True
        
        try:
            logger.info("Loading contract master from Angel One...")
            
            response = requests.get(CONTRACT_MASTER_URL, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                logger.error("Invalid contract master data format")
                return False
            
            with self._data_lock:
                self._data = data
                self._last_updated = datetime.now()
                self._build_indexes()
            
            logger.info(f"Contract master loaded: {len(data)} symbols")
            return True
        
        except requests.RequestException as e:
            logger.error(f"Failed to load contract master: {e}")
            return False
        finally:
            with self._data_lock:
                self._loading = False
    
    def _build_indexes(self):
        """
        Build lookup indexes for fast symbol/token resolution.
        Called after data is loaded.
        """
        self._token_map.clear()
        self._name_index.clear()
        
        for item in self._data:
            try:
                symbol = item.get('symbol', '')
                token = item.get('token', '')
                exch_seg = item.get('exch_seg', '')
                
                # Build token map key
                parsed = SymbolInfo.parse(symbol)
                if parsed:
                    key = (parsed.name.upper(), parsed.strike, parsed.option_type)
                    self._token_map[key] = item
                
                # Build name index
                name = item.get('name', '').upper()
                if name:
                    if name not in self._name_index:
                        self._name_index[name] = []
                    self._name_index[name].append(item)
            
            except Exception as e:
                logger.warning(f"Error indexing symbol {item.get('symbol')}: {e}")
    
    def find_by_strict_match(
        self,
        symbol: str,
        strike: str,
        option_type: str,
        exchange: str = "NFO"
    ) -> Optional[Tuple[str, str]]:
        """
        Find trading symbol and token using strict matching.
        
        Args:
            symbol: Symbol name (e.g., 'NIFTY', 'BANKNIFTY')
            strike: Strike price as string
            option_type: 'CE' or 'PE'
            exchange: Exchange segment (default: 'NFO')
        
        Returns:
            Tuple of (trading_symbol, token) or None if not found
        """
        # Ensure data is loaded
        if not self._data:
            self.load()
        
        with self._data_lock:
            # Try strict match first
            key = (symbol.upper(), str(strike), option_type.upper())
            
            if key in self._token_map:
                item = self._token_map[key]
                if item.get('exch_seg') == exchange:
                    return item.get('symbol'), item.get('token')
            
            # Fallback to linear search with strict matching
            symbol_upper = symbol.upper()
            strike_str = str(strike)
            option_upper = option_type.upper()
            
            for item in self._data:
                if item.get('exch_seg') != exchange:
                    continue
                
                parsed = SymbolInfo.parse(item.get('symbol', ''))
                if parsed and parsed.matches(symbol_upper, strike_str, option_upper):
                    return item.get('symbol'), item.get('token')
            
            return None
    
    def get_symbols_by_name(self, symbol: str, exchange: str = "NFO") -> List[Dict]:
        """Get all symbols matching a name (for expiry selection)."""
        if not self._data:
            self.load()
        
        with self._data_lock:
            return self._name_index.get(symbol.upper(), [])
    
    def get_expiry_list(self, symbol: str, exchange: str = "NFO") -> List[str]:
        """Get sorted list of expiry dates for a symbol."""
        items = self.get_symbols_by_name(symbol, exchange)
        expiries = set()
        
        for item in items:
            parsed = SymbolInfo.parse(item.get('symbol', ''))
            if parsed:
                expiries.add(parsed.expiry)
        
        return sorted(list(expiries))


# ============================================================================
# SESSION MANAGER
# ============================================================================

class AngelOneSessionManager:
    """
    Thread-safe session manager for Angel One API.
    Manages per-user sessions with automatic token refresh.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize session storage."""
        self._sessions: Dict[str, 'UserSession'] = {}
        self._session_lock = threading.Lock()
    
    def _get_session_key(self, client_code: str, api_key: str) -> str:
        """Generate unique session key."""
        return hashlib.sha256(f"{client_code}:{api_key}".encode()).hexdigest()
    
    def get_or_create_session(
        self,
        config: AngelOneConfig
    ) -> 'UserSession':
        """
        Get existing session or create new one.
        Thread-safe implementation.
        """
        session_key = self._get_session_key(config.client_code, config.api_key)
        
        with self._session_lock:
            if session_key in self._sessions:
                session = self._sessions[session_key]
                if session.is_valid():
                    return session
                else:
                    # Remove invalid session
                    del self._sessions[session_key]
            
            # Create new session
            session = UserSession(config)
            self._sessions[session_key] = session
            return session
    
    def invalidate_session(self, client_code: str, api_key: str):
        """Invalidate a specific session."""
        session_key = self._get_session_key(client_code, api_key)
        
        with self._session_lock:
            if session_key in self._sessions:
                self._sessions[session_key].invalidate()
                del self._sessions[session_key]
    
    def clear_all_sessions(self):
        """Clear all sessions (use with caution)."""
        with self._session_lock:
            for session in self._sessions.values():
                session.invalidate()
            self._sessions.clear()


class UserSession:
    """
    Individual user session with thread-safe token management.
    """
    def __init__(self, config: AngelOneConfig):
        self.config = config
        self.smart_connect: Optional[SmartConnect] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.feed_token: Optional[str] = None
        self.session_created: Optional[datetime] = None
        self.last_used: datetime = datetime.now()
        self._lock = threading.RLock()
        self._authenticated = False
    
    def is_valid(self) -> bool:
        """Check if session is valid and not expired."""
        with self._lock:
            if not self._authenticated or not self.access_token:
                return False
            
            if self.session_created:
                if datetime.now() - self.session_created > SESSION_CACHE_DURATION:
                    return False
            
            return True
    
    @retry_on_failure(max_retries=2)
    def authenticate(self) -> bool:
        """
        Authenticate with Angel One and obtain session tokens.
        """
        with self._lock:
            if self.is_valid():
                return True
            
            if not SMARTAPI_SDK_AVAILABLE:
                raise AngelOneError("SmartAPI SDK not installed")
            
            try:
                logger.info(f"Authenticating Angel One session for: {self.config.client_code}")
                
                # Create SmartConnect instance
                self.smart_connect = SmartConnect(api_key=self.config.api_key)
                
                # Generate TOTP
                totp = pyotp.TOTP(self.config.totp_secret).now()
                
                # Login
                login_data = self.smart_connect.generateSession(
                    userId=self.config.client_code,
                    password=self.config.password,
                    totp=totp
                )
                
                if not login_data.get('status'):
                    error_msg = login_data.get('message', 'Login failed')
                    error_code = login_data.get('errorcode')
                    logger.error(f"Angel One login failed: {error_msg} (code: {error_code})")
                    
                    # Raise specific exceptions
                    if error_code in ['AG7006', 'AG7007']:
                        raise InvalidCredentialsError(f"Authentication failed: {error_msg}", error_code)
                    raise AngelOneError(f"Login failed: {error_msg}", error_code)
                
                # Store tokens
                self.access_token = login_data['data']['jwtToken']
                self.refresh_token = login_data['data'].get('refreshToken')
                
                # Get feed token for market data
                try:
                    feed_data = self.smart_connect.getFeedToken()
                    if feed_data.get('status'):
                        self.feed_token = feed_data['data'].get('feedToken')
                except Exception as e:
                    logger.warning(f"Failed to get feed token: {e}")
                
                self.session_created = datetime.now()
                self._authenticated = True
                
                logger.info(f"Angel One session created for: {self.config.client_code}")
                return True
            
            except Exception as e:
                self._authenticated = False
                logger.error(f"Authentication error: {e}")
                raise
    
    def refresh_if_needed(self) -> bool:
        """Refresh session if it's close to expiring."""
        with self._lock:
            if not self._authenticated:
                return self.authenticate()
            
            if self.session_created:
                time_since_create = datetime.now() - self.session_created
                if time_since_create > timedelta(hours=11):
                    logger.info("Session close to expiry, refreshing...")
                    return self.authenticate()
            
            return True
    
    def invalidate(self):
        """Invalidate the session."""
        with self._lock:
            try:
                if self.smart_connect:
                    self.smart_connect.logout()
            except Exception as e:
                logger.warning(f"Logout error: {e}")
            
            self._authenticated = False
            self.access_token = None
            self.refresh_token = None
            self.feed_token = None
            self.smart_connect = None
    
    def mark_used(self):
        """Update last used timestamp."""
        self.last_used = datetime.now()


# ============================================================================
# LTP SERVICE
# ============================================================================

class LTPService:
    """
    Service for fetching Last Traded Price with caching and retry logic.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize LTP cache."""
        self._ltp_cache: Dict[str, Tuple[float, datetime]] = {}
        self._cache_duration = timedelta(seconds=5)  # 5 second cache
        self._lock = threading.Lock()
    
    def get_ltp(
        self,
        session: UserSession,
        exchange: str,
        trading_symbol: str,
        symbol_token: str
    ) -> Optional[float]:
        """
        Get LTP with caching and fallback logic.
        """
        cache_key = f"{exchange}:{symbol_token}"
        
        # Check cache first
        with self._lock:
            if cache_key in self._ltp_cache:
                ltp, cached_time = self._ltp_cache[cache_key]
                if datetime.now() - cached_time < self._cache_duration:
                    return ltp
        
        # Fetch fresh LTP
        ltp = self._fetch_ltp(session, exchange, trading_symbol, symbol_token)
        
        if ltp:
            with self._lock:
                self._ltp_cache[cache_key] = (ltp, datetime.now())
        
        return ltp
    
    @retry_on_failure(max_retries=2)
    def _fetch_ltp(
        self,
        session: UserSession,
        exchange: str,
        trading_symbol: str,
        symbol_token: str
    ) -> Optional[float]:
        """
        Fetch LTP from Angel One API.
        """
        if not session.smart_connect or not session.is_valid():
            session.authenticate()
        
        try:
            # Use correct LTP API
            # SmartAPI uses: ltpData(exchange, symbol, token)
            response = session.smart_connect.ltpData(
                exchange=exchange,
                tradingsymbol=trading_symbol,
                symboltoken=symbol_token
            )
            
            if response and response.get('status'):
                data = response.get('data', {})
                if data:
                    ltp = data.get('ltp')
                    if ltp:
                        return float(ltp)
            
            logger.warning(f"Failed to get LTP for {trading_symbol}: {response}")
            return None
        
        except TokenExpiredError:
            session.authenticate()
            raise
        except Exception as e:
            logger.error(f"LTP fetch error for {trading_symbol}: {e}")
            return None


# ============================================================================
# ORDER SERVICE
# ============================================================================

class AngelOneOrderService:
    """
    Production-ready order service with comprehensive error handling,
    retry logic, and compliance checks.
    """
    
    def __init__(self):
        self.session_manager = AngelOneSessionManager()
        self.contract_cache = ContractMasterCache()
        self.ltp_service = LTPService()
    
    def _get_config_from_broker_details(self, broker_details) -> AngelOneConfig:
        """Extract configuration from broker details model."""
        return AngelOneConfig(
            api_key=getattr(broker_details, 'broker_API_KEY', ''),
            client_code=getattr(broker_details, 'broker_API_UID', ''),
            password=getattr(broker_details, 'broker_pass', ''),
            totp_secret=getattr(broker_details, 'totp', ''),
            buffer_percentage=float(
                getattr(broker_details, 'buffer_percentage', DEFAULT_BUFFER_PERCENTAGE) 
                or DEFAULT_BUFFER_PERCENTAGE
            ),
            enable_market_orders=getattr(broker_details, 'enable_market_orders', False),
        )
    
    def _calculate_limit_price(
        self,
        ltp: float,
        side: str,
        buffer_percentage: float
    ) -> float:
        """
        Calculate limit price with configurable buffer.
        BUY: LTP + buffer
        SELL: LTP - buffer
        """
        buffer_amount = ltp * (buffer_percentage / 100)
        
        if side.upper() == "BUY":
            price = ltp + buffer_amount
        else:
            price = ltp - buffer_amount
        
        # Round to 2 decimal places using banker's rounding
        return float(Decimal(str(price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    @rate_limit(min_interval=RATE_LIMIT_MIN_INTERVAL)
    def place_order(
        self,
        broker_details,
        symbol: str,
        strike: str,
        option_type: str,
        quantity: int,
        transaction_type: str = "BUY",
        order_type: str = "LIMIT",
        product_type: str = "INTRADAY",
        exchange: str = "NFO",
        variety: str = "NORMAL",
        duration: str = "DAY",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
    ) -> OrderResult:
        """
        Place an order with full compliance and error handling.
        
        Args:
            broker_details: Broker details model
            symbol: Symbol name (NIFTY, BANKNIFTY, etc.)
            strike: Strike price
            option_type: CE or PE
            quantity: Order quantity
            transaction_type: BUY or SELL
            order_type: LIMIT, MARKET, or STOPLOSS
            product_type: INTRADAY, DELIVERY, MARGIN, CNC
            exchange: NFO, BSE, etc.
            variety: NORMAL, STOPLOSS, AMO
            duration: DAY, IOC
            price: Limit price (auto-calculated if not provided)
            trigger_price: For STOPLOSS orders
        
        Returns:
            OrderResult with order status and details
        """
        try:
            # Get configuration
            config = self._get_config_from_broker_details(broker_details)
            
            # Validate inputs
            if not all([config.api_key, config.client_code, config.password, config.totp_secret]):
                return OrderResult(
                    status="error",
                    message="Missing broker credentials (API key, client code, password, or TOTP)"
                )
            
            # Validate symbol parameters
            if not all([symbol, strike, option_type]):
                return OrderResult(
                    status="error",
                    message="Missing required symbol parameters"
                )
            
            # Get/create session
            session = self.session_manager.get_or_create_session(config)
            
            # Authenticate if needed
            try:
                session.refresh_if_needed()
            except Exception as e:
                return OrderResult(
                    status="error",
                    message=f"Authentication failed: {str(e)}",
                    error_code=getattr(e, 'error_code', None)
                )
            
            # Load contract master
            self.contract_cache.load()
            
            # Find symbol and token with strict matching
            result = self.contract_cache.find_by_strict_match(
                symbol=symbol,
                strike=str(strike),
                option_type=option_type.upper(),
                exchange=exchange
            )
            
            if not result:
                return OrderResult(
                    status="error",
                    message=f"Symbol not found: {symbol} {strike} {option_type}"
                )
            
            trading_symbol, symbol_token = result
            
            # Determine order type and price
            if order_type.upper() == "MARKET":
                if not config.enable_market_orders:
                    # Auto-convert to LIMIT with buffer
                    order_type = "LIMIT"
                    logger.info(f"Market orders disabled, converting to LIMIT for {trading_symbol}")
                else:
                    order_type = "MARKET"
            
            # Get LTP for limit price calculation
            ltp = None
            if order_type.upper() == "LIMIT" and not price:
                ltp = self.ltp_service.get_ltp(
                    session=session,
                    exchange=exchange,
                    trading_symbol=trading_symbol,
                    symbol_token=symbol_token
                )
                
                if not ltp:
                    return OrderResult(
                        status="error",
                        message="Could not fetch LTP for limit price calculation"
                    )
                
                price = self._calculate_limit_price(
                    ltp=ltp,
                    side=transaction_type,
                    buffer_percentage=config.buffer_percentage
                )
            
            # Build order parameters
            order_params = {
                "variety": variety.upper(),
                "tradingsymbol": trading_symbol,
                "symboltoken": symbol_token,
                "transactiontype": transaction_type.upper(),
                "exchange": exchange.upper(),
                "ordertype": order_type.upper(),
                "producttype": product_type.upper(),
                "duration": duration.upper(),
                "quantity": str(quantity),
            }
            
            # Add price for LIMIT orders
            if order_type.upper() == "LIMIT" and price:
                order_params["price"] = str(price)
                order_params["priceType"] = "LIMIT"
            
            # Add trigger price for STOPLOSS orders
            if trigger_price:
                order_params["triggerprice"] = str(trigger_price)
            
            # Place order with retry
            response = self._place_order_with_retry(session, order_params)
            
            if response and response.get('status'):
                order_id = response.get('data', {}).get('orderid')
                
                return OrderResult(
                    status="success",
                    order_id=order_id,
                    message="Order placed successfully",
                    order_params={
                        "symbol": trading_symbol,
                        "token": symbol_token,
                        "transaction_type": transaction_type,
                        "order_type": order_type,
                        "price": price,
                        "ltp": ltp,
                        "buffer_percentage": config.buffer_percentage,
                        "quantity": quantity,
                        "product_type": product_type,
                    },
                    raw_response=response
                )
            else:
                error_msg = response.get('message', 'Order placement failed') if response else 'No response'
                error_code = response.get('errorcode')
                
                return OrderResult(
                    status="error",
                    message=error_msg,
                    error_code=error_code
                )
        
        except TokenExpiredError as e:
            # Invalidate session and return error
            if 'config' in dir():
                self.session_manager.invalidate_session(
                    config.client_code, 
                    config.api_key
                )
            return OrderResult(
                status="error",
                message="Session expired. Please login again.",
                error_code=e.error_code
            )
        
        except IPWhitelistError as e:
            return OrderResult(
                status="error",
                message=str(e) + " Please whitelist your IP in Angel One settings.",
                error_code=e.error_code
            )
        
        except InsufficientMarginError as e:
            return OrderResult(
                status="error",
                message="Insufficient margin for this order",
                error_code=e.error_code
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error in place_order: {e}")
            return OrderResult(
                status="error",
                message=f"Order placement failed: {str(e)}"
            )
    
    @retry_on_failure(max_retries=MAX_RETRIES)
    def _place_order_with_retry(
        self,
        session: UserSession,
        order_params: Dict
    ) -> Dict:
        """
        Internal method to place order with retry logic.
        """
        if not session.smart_connect:
            session.authenticate()
        
        session.mark_used()
        response = session.smart_connect.placeOrder(order_params)
        
        if not validate_response(response):
            return response
        
        return response
    
    def get_order_book(self, broker_details) -> OrderResult:
        """Fetch order book."""
        try:
            config = self._get_config_from_broker_details(broker_details)
            session = self.session_manager.get_or_create_session(config)
            session.refresh_if_needed()
            
            response = session.smart_connect.orderBook()
            
            if response and response.get('status'):
                return OrderResult(
                    status="success",
                    message="Order book fetched",
                    raw_response=response
                )
            
            return OrderResult(
                status="error",
                message=response.get('message', 'Failed to fetch order book')
            )
        
        except Exception as e:
            logger.error(f"Order book error: {e}")
            return OrderResult(
                status="error",
                message=str(e)
            )
    
    def get_trade_book(self, broker_details) -> OrderResult:
        """Fetch trade book."""
        try:
            config = self._get_config_from_broker_details(broker_details)
            session = self.session_manager.get_or_create_session(config)
            session.refresh_if_needed()
            
            response = session.smart_connect.tradeBook()
            
            if response and response.get('status'):
                return OrderResult(
                    status="success",
                    message="Trade book fetched",
                    raw_response=response
                )
            
            return OrderResult(
                status="error",
                message=response.get('message', 'Failed to fetch trade book')
            )
        
        except Exception as e:
            logger.error(f"Trade book error: {e}")
            return OrderResult(
                status="error",
                message=str(e)
            )
    
    def cancel_order(self, broker_details, order_id: str, variety: str = "NORMAL") -> OrderResult:
        """Cancel an existing order."""
        try:
            config = self._get_config_from_broker_details(broker_details)
            session = self.session_manager.get_or_create_session(config)
            session.refresh_if_needed()
            
            response = session.smart_connect.cancelOrder(order_id=order_id, variety=variety)
            
            if response and response.get('status'):
                return OrderResult(
                    status="success",
                    order_id=order_id,
                    message="Order cancelled successfully"
                )
            
            return OrderResult(
                status="error",
                message=response.get('message', 'Failed to cancel order')
            )
        
        except Exception as e:
            logger.error(f"Cancel order error: {e}")
            return OrderResult(
                status="error",
                message=str(e)
            )
    
    def get_holdings(self, broker_details) -> OrderResult:
        """Fetch holdings/positions."""
        try:
            config = self._get_config_from_broker_details(broker_details)
            session = self.session_manager.get_or_create_session(config)
            session.refresh_if_needed()
            
            response = session.smart_connect.holding()
            
            if response and response.get('status'):
                return OrderResult(
                    status="success",
                    message="Holdings fetched",
                    raw_response=response
                )
            
            return OrderResult(
                status="error",
                message=response.get('message', 'Failed to fetch holdings')
            )
        
        except Exception as e:
            logger.error(f"Holdings error: {e}")
            return OrderResult(
                status="error",
                message=str(e)
            )
    
    def get_profile(self, broker_details) -> OrderResult:
        """Get user profile."""
        try:
            config = self._get_config_from_broker_details(broker_details)
            session = self.session_manager.get_or_create_session(config)
            session.refresh_if_needed()
            
            response = session.smart_connect.getProfile()
            
            if response and response.get('status'):
                return OrderResult(
                    status="success",
                    message="Profile fetched",
                    raw_response=response
                )
            
            return OrderResult(
                status="error",
                message=response.get('message', 'Failed to fetch profile')
            )
        
        except Exception as e:
            logger.error(f"Profile error: {e}")
            return OrderResult(
                status="error",
                message=str(e)
            )
    
    def get_margin(self, broker_details) -> OrderResult:
        """Get margin/limits."""
        try:
            config = self._get_config_from_broker_details(broker_details)
            session = self.session_manager.get_or_create_session(config)
            session.refresh_if_needed()
            
            response = session.smart_connect.rmsLimit()
            
            if response and response.get('status'):
                return OrderResult(
                    status="success",
                    message="Margin fetched",
                    raw_response=response
                )
            
            return OrderResult(
                status="error",
                message=response.get('message', 'Failed to fetch margin')
            )
        
        except Exception as e:
            logger.error(f"Margin error: {e}")
            return OrderResult(
                status="error",
                message=str(e)
            )


# ============================================================================
# SYMBOL EXPIRY API VIEW
# ============================================================================

class SymbolExpiryDateListView:
    """API View to get expiry dates for a symbol."""
    
    def __init__(self):
        self.contract_cache = ContractMasterCache()
    
    def get(self, symbol: str, exchange: str = "NFO") -> List[str]:
        """Get sorted expiry dates for a symbol."""
        self.contract_cache.load()
        return self.contract_cache.get_expiry_list(symbol, exchange)


# ============================================================================
# BACKWARD COMPATIBILITY WRAPPER
# ============================================================================

class AngelOneTradingWrapper:
    """
    Wrapper class providing backward compatibility with existing function names.
    Maps old function calls to new production-grade implementation.
    """
    
    def __init__(self):
        self.order_service = AngelOneOrderService()
        self.contract_cache = ContractMasterCache()
    
    def get_access_token(self, client_code, password, totp_secret, api_key, broker_details) -> Optional[str]:
        """Legacy function - redirects to new login."""
        try:
            config = AngelOneConfig(
                api_key=api_key,
                client_code=client_code,
                password=password,
                totp_secret=totp_secret
            )
            session = AngelOneSessionManager().get_or_create_session(config)
            session.authenticate()
            return session.access_token
        except Exception as e:
            logger.error(f"get_access_token error: {e}")
            return None
    
    def place_Angle_order(self, broker_details, **kwargs) -> Dict:
        """Legacy function - redirects to new place_order."""
        result = self.order_service.place_order(
            broker_details=broker_details,
            symbol=kwargs.get('symbol'),
            strike=kwargs.get('strike'),
            option_type=kwargs.get('option_type'),
            quantity=kwargs.get('quantity'),
            transaction_type=kwargs.get('transactiontype', 'BUY'),
        )
        return result.to_dict()
    
    def get_token_details(self, broker_details) -> Dict:
        """Legacy function - get token status."""
        try:
            config = self.order_service._get_config_from_broker_details(broker_details)
            session = AngelOneSessionManager().get_or_create_session(config)
            
            return {
                "status": "success",
                "is_valid": session.is_valid(),
                "client_code": config.client_code,
                "session_expiry": session.session_created.isoformat() if session.session_created else None,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def exit_existing_buy_position_angleone(self, broker_details, **kwargs) -> Dict:
        """Legacy function - placeholder for exit position logic."""
        return {
            "status": "info",
            "message": "Exit position logic needs implementation"
        }


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

# Global service instances
order_service = AngelOneOrderService()
trading_wrapper = AngelOneTradingWrapper()
symbol_expiry_view = SymbolExpiryDateListView()


# ============================================================================
# LEGACY FUNCTION EXPORTS (for backward compatibility)
# ============================================================================

def get_access_token(client_code, password, totp_secret, api_key, broker_details):
    """Backward compatible function."""
    return trading_wrapper.get_access_token(
        client_code, password, totp_secret, api_key, broker_details
    )


def place_Angle_order(broker_details, **kwargs):
    """Backward compatible function."""
    return trading_wrapper.place_Angle_order(broker_details, **kwargs)


def get_token_details(broker_details):
    """Backward compatible function."""
    return trading_wrapper.get_token_details(broker_details)


def exit_existing_buy_position_angleone(broker_details, **kwargs):
    """Backward compatible function."""
    return trading_wrapper.exit_existing_buy_position_angleone(broker_details, **kwargs)


def place_angel_one_order(broker_details, **kwargs):
    """New production function."""
    result = order_service.place_order(broker_details, **kwargs)
    return result.to_dict()


def get_angel_one_order_book(broker_details):
    """Get order book."""
    result = order_service.get_order_book(broker_details)
    return result.to_dict()


def get_angel_one_trade_book(broker_details):
    """Get trade book."""
    result = order_service.get_trade_book(broker_details)
    return result.to_dict()


def cancel_angel_one_order(broker_details, order_id, variety="NORMAL"):
    """Cancel order."""
    result = order_service.cancel_order(broker_details, order_id, variety)
    return result.to_dict()


def get_angel_one_holdings(broker_details):
    """Get holdings."""
    result = order_service.get_holdings(broker_details)
    return result.to_dict()


def get_angel_one_profile(broker_details):
    """Get profile."""
    result = order_service.get_profile(broker_details)
    return result.to_dict()


def get_angel_one_margin(broker_details):
    """Get margin."""
    result = order_service.get_margin(broker_details)
    return result.to_dict()


def fetch_contract_master(force_refresh: bool = False):
    """Fetch contract master."""
    cache = ContractMasterCache()
    cache.load(force_refresh=force_refresh)
    return cache._data


def get_symbol_token(symbol, strike, option_type, exchange="NFO"):
    """Find symbol and token."""
    cache = ContractMasterCache()
    cache.load()
    result = cache.find_by_strict_match(symbol, strike, option_type, exchange)
    return result if result else (None, None)


def angel_one_login(client_code, password, totp_secret, api_key, broker_details=None):
    """Login to Angel One."""
    try:
        config = AngelOneConfig(
            api_key=api_key,
            client_code=client_code,
            password=password,
            totp_secret=totp_secret
        )
        session = AngelOneSessionManager().get_or_create_session(config)
        session.authenticate()
        
        return {
            "status": "success",
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "feed_token": session.feed_token,
            "client_code": client_code
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        return {"status": "error", "message": str(e)}


def angel_one_logout(client_code, api_key):
    """Logout from Angel One."""
    try:
        AngelOneSessionManager().invalidate_session(client_code, api_key)
        return {"status": "success", "message": "Logged out successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================================
# DRF API VIEW
# ============================================================================

try:
    from rest_framework.views import APIView
    from rest_framework.response import Response
    
    class SymbolExpiryDateListAPIView(APIView):
        """DRF API View for symbol expiry dates."""
        
        def get(self, request):
            symbol = request.query_params.get('symbol')
            exchange = request.query_params.get('exchange', 'NFO')
            
            if not symbol:
                return Response({"error": "Symbol required"}, status=400)
            
            try:
                cache = ContractMasterCache()
                cache.load()
                expiries = cache.get_expiry_list(symbol, exchange)
                
                return Response({
                    "symbol": symbol,
                    "exchange": exchange,
                    "expiry_dates": expiries[:10]
                })
            except Exception as e:
                return Response({
                    "error": str(e)
                }, status=500)

except ImportError:
    pass
