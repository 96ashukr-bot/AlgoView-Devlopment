"""
Idempotency Manager
===================
Prevents duplicate orders from repeated webhook signals.

Features:
- Hash-based order deduplication
- Configurable time window
- Thread-safe in-memory cache
- Optional Redis backend support
"""

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from enum import Enum

from .logging_utils import TradingLogger

logger = TradingLogger("idempotency")


class DuplicateStatus(Enum):
    """Status of duplicate check"""
    NEW = "new"
    DUPLICATE = "duplicate"
    EXPIRED = "expired"


@dataclass
class OrderRecord:
    """Record of an executed order for deduplication"""
    idempotency_key: str
    client_id: str
    symbol: str
    strike: Optional[float]
    side: str
    quantity: int
    timestamp: float
    order_id: Optional[str] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "idempotency_key": self.idempotency_key,
            "client_id": self.client_id,
            "symbol": self.symbol,
            "strike": self.strike,
            "side": self.side,
            "quantity": self.quantity,
            "timestamp": self.timestamp,
            "order_id": self.order_id,
            "status": self.status
        }


class LRUCache(OrderedDict):
    """Thread-safe LRU cache with max size"""
    
    def __init__(self, maxsize: int = 10000):
        super().__init__()
        self.maxsize = maxsize
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self:
                return None
            self.move_to_end(key)
            return self[key]
    
    def put(self, key: str, value: Any):
        with self._lock:
            if key in self:
                self.move_to_end(key)
            self[key] = value
            if len(self) > self.maxsize:
                self.popitem(last=False)
    
    def remove(self, key: str) -> bool:
        with self._lock:
            if key in self:
                del self[key]
                return True
            return False
    
    def clear_expired(self, max_age_seconds: float):
        """Remove entries older than max_age_seconds"""
        with self._lock:
            current_time = time.time()
            keys_to_remove = []
            
            for key, record in self.items():
                if hasattr(record, 'timestamp'):
                    if current_time - record.timestamp > max_age_seconds:
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self[key]
            
            return len(keys_to_remove)



class IdempotencyManager:
    """
    Thread-safe idempotency manager for duplicate order protection.
    
    Usage:
        manager = IdempotencyManager(window_seconds=5)
        
        # Check before placing order
        is_dup, existing = manager.check_duplicate(
            client_id="C123",
            symbol="NIFTY",
            strike=22700,
            side="BUY",
            quantity=50
        )
        
        if is_dup:
            return {"error": "Duplicate order detected"}
        
        # Place order...
        
        # Record the execution
        manager.record_execution(key, order_id="ORD123")
    """
    
    def __init__(
        self,
        window_seconds: float = 5.0,
        cache_size: int = 10000,
        cleanup_interval: int = 60
    ):
        """
        Initialize idempotency manager.
        
        Args:
            window_seconds: Time window for duplicate detection (default 5s)
            cache_size: Maximum cache entries
            cleanup_interval: Seconds between cache cleanup
        """
        self.window_seconds = window_seconds
        self.cache_size = cache_size
        self.cleanup_interval = cleanup_interval
        
        self._cache = LRUCache(maxsize=cache_size)
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        
        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="IdempotencyCleanup"
        )
        self._cleanup_thread.start()
        
        logger.info(
            "IdempotencyManager initialized",
            window_seconds=window_seconds,
            cache_size=cache_size
        )
    
    def generate_key(
        self,
        client_id: str,
        symbol: str,
        strike: Optional[float],
        side: str,
        quantity: Optional[int] = None,
        option_type: Optional[str] = None
    ) -> str:
        """
        Generate idempotency key from order parameters.
        
        Args:
            client_id: Client identifier
            symbol: Trading symbol
            strike: Strike price (for options)
            side: BUY or SELL
            quantity: Order quantity (optional)
            option_type: CE or PE (optional)
            
        Returns:
            SHA256 hash key
        """
        # Build key components
        components = [
            str(client_id).upper(),
            str(symbol).upper(),
            str(strike) if strike else "",
            str(side).upper(),
            str(option_type).upper() if option_type else ""
        ]
        
        # Optionally include quantity for stricter deduplication
        if quantity:
            components.append(str(quantity))
        
        key_string = "|".join(components)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def check_duplicate(
        self,
        client_id: str,
        symbol: str,
        strike: Optional[float],
        side: str,
        quantity: int = 1,
        option_type: Optional[str] = None,
        custom_key: Optional[str] = None
    ) -> Tuple[bool, Optional[OrderRecord]]:
        """
        Check if an order is a duplicate.
        
        Args:
            client_id: Client identifier
            symbol: Trading symbol
            strike: Strike price
            side: BUY or SELL
            quantity: Order quantity
            option_type: CE or PE
            custom_key: Optional custom idempotency key
            
        Returns:
            Tuple of (is_duplicate, existing_record)
        """
        # Generate or use custom key
        key = custom_key or self.generate_key(
            client_id, symbol, strike, side, None, option_type
        )
        
        current_time = time.time()
        
        with self._lock:
            existing = self._cache.get(key)
            
            if existing:
                # Check if within time window
                age = current_time - existing.timestamp
                
                if age <= self.window_seconds:
                    logger.warning(
                        "Duplicate order detected",
                        client_id=client_id,
                        symbol=symbol,
                        strike=strike,
                        side=side,
                        age_seconds=round(age, 2),
                        existing_order_id=existing.order_id
                    )
                    return True, existing
                else:
                    # Expired, remove and allow new order
                    self._cache.remove(key)
            
            # Create new record
            record = OrderRecord(
                idempotency_key=key,
                client_id=client_id,
                symbol=symbol,
                strike=strike,
                side=side,
                quantity=quantity,
                timestamp=current_time
            )
            
            self._cache.put(key, record)
            
            logger.debug(
                "New order recorded",
                client_id=client_id,
                symbol=symbol,
                strike=strike,
                side=side,
                idempotency_key=key
            )
            
            return False, record
    
    def record_execution(
        self,
        idempotency_key: str,
        order_id: str,
        status: str = "complete"
    ) -> bool:
        """
        Record successful order execution.
        
        Args:
            idempotency_key: The idempotency key
            order_id: Broker order ID
            status: Order status
            
        Returns:
            True if record updated, False if not found
        """
        with self._lock:
            record = self._cache.get(idempotency_key)
            
            if record:
                record.order_id = order_id
                record.status = status
                self._cache.put(idempotency_key, record)
                
                logger.info(
                    "Order execution recorded",
                    idempotency_key=idempotency_key,
                    order_id=order_id,
                    status=status
                )
                return True
            
            return False
    
    def remove_record(self, idempotency_key: str) -> bool:
        """Remove a record (e.g., on order failure)"""
        return self._cache.remove(idempotency_key)
    
    def get_record(self, idempotency_key: str) -> Optional[OrderRecord]:
        """Get record by key"""
        return self._cache.get(idempotency_key)
    
    def get_recent_orders(
        self,
        client_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Get recent orders, optionally filtered by client"""
        with self._lock:
            records = []
            for record in self._cache.values():
                if client_id and record.client_id != client_id:
                    continue
                records.append(record)
                if len(records) >= limit:
                    break
            return records
    
    def _cleanup_loop(self):
        """Background cleanup of expired entries"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                
                # Clean entries older than 10x the window
                max_age = self.window_seconds * 10
                removed = self._cache.clear_expired(max_age)
                
                if removed > 0:
                    logger.debug(
                        "Idempotency cache cleanup",
                        removed_entries=removed
                    )
                    
            except Exception as e:
                logger.error(
                    "Cleanup error",
                    error=str(e)
                )
    
    def clear(self):
        """Clear all records"""
        with self._lock:
            self._cache.clear()


# Singleton instance
_manager_instance: Optional[IdempotencyManager] = None
_manager_lock = threading.Lock()


def get_idempotency_manager(
    window_seconds: float = 5.0
) -> IdempotencyManager:
    """Get singleton idempotency manager instance"""
    global _manager_instance
    if _manager_instance is None:
        with _manager_lock:
            if _manager_instance is None:
                _manager_instance = IdempotencyManager(
                    window_seconds=window_seconds
                )
    return _manager_instance
