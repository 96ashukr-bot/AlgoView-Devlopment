"""
Angel One Constants and Configuration
=====================================
Centralized configuration for the trading module.
"""

from enum import Enum
from typing import Final

# =========================
# SMARTAPI RESOURCES
# =========================
# Contract master still comes from Angel One's published instrument file.
ANGEL_ONE_CONTRACT_URL: Final[str] = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

# =========================
# FEATURE FLAGS
# =========================
# Toggle execution behavior without changing downstream service code.
ALLOW_MARKET_ORDERS: Final[bool] = True
USE_LIMIT_WITH_BUFFER: Final[bool] = True
FORCE_LTP_FETCH: Final[bool] = True
ENFORCE_LOT_SIZE: Final[bool] = True
ENFORCE_MARKET_HOURS: Final[bool] = True

# =========================
# BUFFER CONFIGURATION
# =========================
DEFAULT_BUFFER_PERCENTAGE: Final[float] = 2.5
MIN_BUFFER_PERCENTAGE: Final[float] = 0.1
MAX_BUFFER_PERCENTAGE: Final[float] = 10.0
DEFAULT_TICK_SIZE: Final[float] = 0.05
ALLOW_STRIKE_FALLBACK: Final[bool] = False

# =========================
# RATE LIMITING
# =========================
RATE_LIMIT_SECONDS: Final[float] = 0.1
MAX_ORDERS_PER_SECOND: Final[int] = 10
MAX_ORDERS_PER_MINUTE_PER_CLIENT: Final[int] = 30
DEFAULT_MAX_DAILY_TRADES_PER_CLIENT: Final[int] = 20
DEFAULT_MAX_QUANTITY_PER_TRADE: Final[int] = 5000
DEFAULT_MAX_ORDER_VALUE_PER_TRADE: Final[float] = 10000000.0

# =========================
# ORDER SAFETY
# =========================
# Controls retries and order placement behavior during transient failures.
MAX_ORDER_RETRIES: Final[int] = 2
ORDER_RETRY_DELAY: Final[float] = 0.3

# =========================
# CACHE CONFIGURATION
# =========================
CONTRACT_MASTER_CACHE_TTL: Final[int] = 3600  # 1 hour
LTP_CACHE_TTL: Final[int] = 1  # 1 second
SESSION_EXPIRY_HOURS: Final[int] = 12
REFRESH_TOKEN_EXPIRY_DAYS: Final[int] = 1
LTP_MAX_RETRIES: Final[int] = 2
LTP_RETRY_DELAY_SECONDS: Final[float] = 0.2

# =========================
# LTP SAFETY
# =========================
# Guardrails for rejecting invalid or outlier live prices.
MIN_VALID_LTP: Final[float] = 0.05
MAX_VALID_LTP: Final[float] = 1000000.0

# =========================
# SLIPPAGE CONTROL
# =========================
# Maximum acceptable execution slippage relative to the validated reference price.
MAX_SLIPPAGE_PERCENT: Final[float] = 5.0

# =========================
# IDEMPOTENCY CONFIGURATION
# =========================
DUPLICATE_ORDER_WINDOW_SECONDS: Final[int] = 5
IDEMPOTENCY_CACHE_SIZE: Final[int] = 10000

# =========================
# OAUTH / CALLBACK SECURITY
# =========================
OAUTH_STATE_TTL_SECONDS: Final[int] = 600

# =========================
# QUEUE CONFIGURATION
# =========================
ORDER_QUEUE_NAME: Final[str] = "angelone_orders"
ORDER_QUEUE_PRIORITY_HIGH: Final[int] = 9
ORDER_QUEUE_PRIORITY_NORMAL: Final[int] = 5
ORDER_QUEUE_PRIORITY_LOW: Final[int] = 1

# =========================
# TRADING HOURS (IST)
# =========================
MARKET_OPEN_HOUR: Final[int] = 9
MARKET_OPEN_MINUTE: Final[int] = 15
MARKET_CLOSE_HOUR: Final[int] = 15
MARKET_CLOSE_MINUTE: Final[int] = 30

# =========================
# TIMEZONE CONFIGURATION
# =========================
# Enable Indian Standard Time for all trading validations.
USE_IST: Final[bool] = True
# Shared timezone setting for trading hours validation, session expiry checks, and logging timestamps.
TIMEZONE: Final[str] = "Asia/Kolkata"


class Exchange(str, Enum):
    """Supported exchanges"""
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"
    BFO = "BFO"
    MCX = "MCX"
    CDS = "CDS"


class ProductType(str, Enum):
    """Product types for orders"""
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"
    CARRYFORWARD = "CARRYFORWARD"
    MARGIN = "MARGIN"
    BO = "BO"


class OrderType(str, Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOPLOSS_LIMIT = "STOPLOSS_LIMIT"
    STOPLOSS_MARKET = "STOPLOSS_MARKET"


class TransactionType(str, Enum):
    """Transaction types"""
    BUY = "BUY"
    SELL = "SELL"


class OptionType(str, Enum):
    """Option types"""
    CE = "CE"
    PE = "PE"


class Variety(str, Enum):
    """Order variety"""
    NORMAL = "NORMAL"
    STOPLOSS = "STOPLOSS"
    AMO = "AMO"
    ROBO = "ROBO"


class Duration(str, Enum):
    """Order duration/validity"""
    DAY = "DAY"
    IOC = "IOC"


class OrderStatus(str, Enum):
    """Order status values"""
    PENDING = "pending"
    OPEN = "open"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    MODIFIED = "modified"
