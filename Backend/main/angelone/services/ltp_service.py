"""
LTP Service
===========
Optimized LTP fetching with caching.

Features:
- Thread-safe LTP cache
- Batch LTP requests
- Automatic cache invalidation
- Rate limiting
"""

import threading
import time
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import OrderedDict

from ..utils.logging_utils import TradingLogger
from ..constants import (
    LTP_CACHE_TTL,
    RATE_LIMIT_SECONDS,
    LTP_MAX_RETRIES,
    LTP_RETRY_DELAY_SECONDS,
    DEFAULT_TICK_SIZE,
)

logger = TradingLogger("ltp_service")


@dataclass
class LTPData:
    """LTP data structure"""
    token: str
    symbol: str
    ltp: float
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    timestamp: float = 0.0
    
    def is_stale(self, ttl: float = LTP_CACHE_TTL) -> bool:
        """Check if data is stale"""
        return (time.time() - self.timestamp) > ttl


class LTPCache:
    """Thread-safe LTP cache with TTL"""
    
    def __init__(self, max_size: int = 5000, ttl: float = LTP_CACHE_TTL):
        self._cache: OrderedDict[str, LTPData] = OrderedDict()
        self._lock = threading.RLock()
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, token: str) -> Optional[LTPData]:
        """Get LTP data if not stale"""
        with self._lock:
            data = self._cache.get(token)
            if data and not data.is_stale(self.ttl):
                self._cache.move_to_end(token)
                return data
            return None
    
    def put(self, token: str, data: LTPData):
        """Store LTP data"""
        with self._lock:
            self._cache[token] = data
            self._cache.move_to_end(token)
            
            # Evict oldest if over capacity
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
    
    def put_batch(self, data_list: List[LTPData]):
        """Store multiple LTP data"""
        with self._lock:
            for data in data_list:
                self._cache[data.token] = data
            
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
    
    def invalidate(self, token: str):
        """Invalidate specific token"""
        with self._lock:
            self._cache.pop(token, None)
    
    def clear(self):
        """Clear all cache"""
        with self._lock:
            self._cache.clear()


class LTPService:
    """
    Optimized LTP service with caching and batching.
    
    Usage:
        service = LTPService()
        
        # Get single LTP
        ltp = service.get_ltp(smart_connect, "NFO", "12345")
        
        # Get batch LTP
        ltps = service.get_batch_ltp(smart_connect, "NFO", ["12345", "12346"])
    """
    
    _instance: Optional['LTPService'] = None
    _instance_lock = threading.Lock()
    
    def __init__(self, cache_ttl: float = LTP_CACHE_TTL):
        self._cache = LTPCache(ttl=cache_ttl)
        self._lock = threading.RLock()
        self._last_request_time = 0.0
        self._rate_limit = RATE_LIMIT_SECONDS
    
    @classmethod
    def get_instance(cls) -> 'LTPService':
        """Get singleton instance"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = LTPService()
        return cls._instance
    
    def _rate_limit_wait(self):
        """Apply rate limiting"""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._rate_limit:
                time.sleep(self._rate_limit - elapsed)
            self._last_request_time = time.time()
    
    def get_ltp(
        self,
        smart_connect,
        exchange: str,
        token: str,
        symbol: str = "",
        max_retries: int = LTP_MAX_RETRIES,
    ) -> Optional[float]:
        """
        Get LTP for a single instrument.
        
        Args:
            smart_connect: SmartConnect instance
            exchange: Exchange (NFO, NSE, etc.)
            token: Instrument token
            symbol: Symbol name (for logging)
            
        Returns:
            LTP value or None
        """
        # Check cache first
        cached = self._cache.get(token)
        if cached:
            logger.debug(
                "LTP cache hit",
                token=token,
                ltp=cached.ltp
            )
            return cached.ltp
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                self._rate_limit_wait()
                data = smart_connect.ltpData(exchange, symbol, token)

                if data.get("status") and data.get("data"):
                    ltp = float(data["data"].get("ltp", 0) or 0)
                    if ltp > 0:
                        ltp_data = LTPData(
                            token=token,
                            symbol=symbol,
                            ltp=ltp,
                            open=float(data["data"].get("open", 0) or 0),
                            high=float(data["data"].get("high", 0) or 0),
                            low=float(data["data"].get("low", 0) or 0),
                            close=float(data["data"].get("close", 0) or 0),
                            timestamp=time.time()
                        )
                        self._cache.put(token, ltp_data)

                        logger.debug(
                            "LTP fetched",
                            token=token,
                            symbol=symbol,
                            ltp=ltp,
                            attempt=attempt,
                        )
                        return ltp

                    last_error = "LTP missing in broker response"
                else:
                    last_error = data.get("message") if isinstance(data, dict) else "Invalid LTP response"

                logger.warning(
                    "LTP fetch attempt failed",
                    token=token,
                    symbol=symbol,
                    attempt=attempt,
                    error=last_error,
                )
            except Exception as e:
                last_error = str(e)
                logger.error(
                    "LTP fetch error",
                    token=token,
                    symbol=symbol,
                    attempt=attempt,
                    error=last_error,
                )

            if attempt < max_retries:
                time.sleep(LTP_RETRY_DELAY_SECONDS)

        logger.error(
            "LTP fetch exhausted retries",
            token=token,
            symbol=symbol,
            error=last_error or "Unknown LTP error",
        )
        return None
    
    def get_batch_ltp(
        self,
        smart_connect,
        exchange: str,
        tokens: List[str],
        symbols: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """
        Get LTP for multiple instruments.
        
        Args:
            smart_connect: SmartConnect instance
            exchange: Exchange
            tokens: List of tokens
            symbols: Optional token -> symbol mapping
            
        Returns:
            Dict of token -> LTP
        """
        results = {}
        tokens_to_fetch = []
        
        # Check cache first
        for token in tokens:
            cached = self._cache.get(token)
            if cached:
                results[token] = cached.ltp
            else:
                tokens_to_fetch.append(token)
        
        if not tokens_to_fetch:
            return results
        
        # Fetch remaining from API
        try:
            self._rate_limit_wait()
            
            # Build request
            exchange_tokens = {
                exchange: [
                    {
                        "symboltoken": token,
                        "tradingsymbol": symbols.get(token, "") if symbols else ""
                    }
                    for token in tokens_to_fetch
                ]
            }
            
            data = smart_connect.getMarketData(
                mode="LTP",
                exchangeTokens=exchange_tokens
            )
            
            if data.get("status") and data.get("data"):
                fetched = data["data"].get("fetched", [])
                
                for item in fetched:
                    token = str(item.get("symbolToken", ""))
                    ltp = float(item.get("ltp", 0))
                    
                    results[token] = ltp
                    
                    # Cache
                    ltp_data = LTPData(
                        token=token,
                        symbol=item.get("tradingSymbol", ""),
                        ltp=ltp,
                        timestamp=time.time()
                    )
                    self._cache.put(token, ltp_data)
                
                logger.debug(
                    "Batch LTP fetched",
                    count=len(fetched)
                )
                
        except Exception as e:
            logger.error(
                "Batch LTP fetch error",
                error=str(e)
            )
        
        return results
    
    def calculate_limit_price(
        self,
        ltp: float,
        side: str,
        buffer_percentage: float = 2.5,
        tick_size: float = DEFAULT_TICK_SIZE,
    ) -> float:
        """
        Calculate limit price with buffer.
        
        Args:
            ltp: Last traded price
            side: BUY or SELL
            buffer_percentage: Buffer percentage
            
        Returns:
            Calculated limit price
        """
        buffer = ltp * (buffer_percentage / 100)

        if side.upper() == "BUY":
            price = ltp + buffer
            return self.round_to_tick(price, tick_size=tick_size, direction="UP")
        else:
            price = max(0, ltp - buffer)
            return self.round_to_tick(price, tick_size=tick_size, direction="DOWN")

    @staticmethod
    def round_to_tick(price: float, tick_size: float = DEFAULT_TICK_SIZE, direction: str = "NEAREST") -> float:
        """Round price to exchange tick size."""
        if tick_size <= 0:
            return round(price, 2)

        scaled = price / tick_size
        if direction == "UP":
            rounded = int(-(-scaled // 1))
        elif direction == "DOWN":
            rounded = int(scaled // 1)
        else:
            rounded = round(scaled)
        return round(rounded * tick_size, 2)
    
    def invalidate_cache(self, token: Optional[str] = None):
        """Invalidate cache"""
        if token:
            self._cache.invalidate(token)
        else:
            self._cache.clear()
