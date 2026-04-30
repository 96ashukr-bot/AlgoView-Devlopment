"""
Position Manager
================
Basic framework for tracking open positions.

Features:
- Track open positions per client
- Avoid duplicate buys
- Support exit logic
- Extensible design
"""

import threading
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from ..utils.logging_utils import TradingLogger

logger = TradingLogger("position_manager")


class PositionSide(Enum):
    """Position side"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class PositionStatus(Enum):
    """Position status"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


@dataclass
class Position:
    """Position data structure"""
    position_id: str
    client_id: str
    symbol: str
    underlying: str
    strike: Optional[float]
    option_type: Optional[str]
    exchange: str
    side: PositionSide
    quantity: int
    avg_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    entry_order_id: Optional[str] = None
    exit_order_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_price(self, price: float):
        """Update current price and PnL"""
        self.current_price = price
        multiplier = 1 if self.side == PositionSide.LONG else -1
        self.unrealized_pnl = (price - self.avg_price) * self.quantity * multiplier
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_id": self.position_id,
            "client_id": self.client_id,
            "symbol": self.symbol,
            "underlying": self.underlying,
            "strike": self.strike,
            "option_type": self.option_type,
            "side": self.side.value,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "status": self.status.value,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat() if self.exit_time else None
        }


class PositionManager:
    """
    Thread-safe position manager for tracking open positions.
    
    Usage:
        manager = PositionManager.get_instance()
        
        # Add position
        position = manager.add_position(
            client_id="C123",
            symbol="NIFTY05MAY2622700CE",
            side=PositionSide.LONG,
            quantity=50,
            price=150.0
        )
        
        # Check if position exists
        has_position = manager.has_open_position("C123", "NIFTY", 22700, "CE")
        
        # Get positions
        positions = manager.get_client_positions("C123")
    """
    
    _instance: Optional['PositionManager'] = None
    _instance_lock = threading.Lock()
    
    def __init__(self):
        self._lock = threading.RLock()
        # Positions indexed by client_id
        self._positions: Dict[str, Dict[str, Position]] = defaultdict(dict)
        # Quick lookup: (client_id, underlying, strike, option_type) -> position_id
        self._position_index: Dict[tuple, str] = {}
        self._position_counter = 0
    
    @classmethod
    def get_instance(cls) -> 'PositionManager':
        """Get singleton instance"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = PositionManager()
        return cls._instance
    
    def _generate_position_id(self) -> str:
        """Generate unique position ID"""
        with self._lock:
            self._position_counter += 1
            return f"POS{datetime.now().strftime('%Y%m%d')}{self._position_counter:06d}"
    
    def add_position(
        self,
        client_id: str,
        symbol: str,
        underlying: str,
        side: PositionSide,
        quantity: int,
        price: float,
        strike: Optional[float] = None,
        option_type: Optional[str] = None,
        exchange: str = "NFO",
        order_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Position:
        """
        Add or update a position.
        
        Args:
            client_id: Client identifier
            symbol: Full symbol
            underlying: Underlying symbol
            side: LONG or SHORT
            quantity: Position quantity
            price: Entry price
            strike: Strike price (for options)
            option_type: CE or PE
            exchange: Exchange
            order_id: Entry order ID
            metadata: Additional metadata
            
        Returns:
            Position object
        """
        with self._lock:
            # Check for existing position
            index_key = (client_id, underlying, strike, option_type)
            existing_id = self._position_index.get(index_key)
            
            if existing_id and existing_id in self._positions[client_id]:
                # Update existing position
                existing = self._positions[client_id][existing_id]
                
                if existing.side == side:
                    # Add to position
                    total_qty = existing.quantity + quantity
                    total_value = (existing.avg_price * existing.quantity) + (price * quantity)
                    existing.avg_price = total_value / total_qty
                    existing.quantity = total_qty
                    
                    logger.info(
                        "Position increased",
                        client_id=client_id,
                        position_id=existing_id,
                        new_quantity=total_qty
                    )
                    return existing
                else:
                    # Reduce/close position
                    return self._reduce_position(existing, quantity, price, order_id)
            
            # Create new position
            position = Position(
                position_id=self._generate_position_id(),
                client_id=client_id,
                symbol=symbol,
                underlying=underlying,
                strike=strike,
                option_type=option_type,
                exchange=exchange,
                side=side,
                quantity=quantity,
                avg_price=price,
                current_price=price,
                entry_order_id=order_id,
                metadata=metadata or {}
            )
            
            self._positions[client_id][position.position_id] = position
            self._position_index[index_key] = position.position_id
            
            logger.info(
                "Position opened",
                client_id=client_id,
                position_id=position.position_id,
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                price=price
            )
            
            return position
    
    def _reduce_position(
        self,
        position: Position,
        quantity: int,
        price: float,
        order_id: Optional[str]
    ) -> Position:
        """Reduce or close a position"""
        if quantity >= position.quantity:
            # Close position
            position.realized_pnl = (price - position.avg_price) * position.quantity
            if position.side == PositionSide.SHORT:
                position.realized_pnl *= -1
            
            position.quantity = 0
            position.status = PositionStatus.CLOSED
            position.exit_time = datetime.now()
            position.exit_order_id = order_id
            
            # Remove from index
            index_key = (position.client_id, position.underlying, position.strike, position.option_type)
            self._position_index.pop(index_key, None)
            
            logger.info(
                "Position closed",
                client_id=position.client_id,
                position_id=position.position_id,
                realized_pnl=position.realized_pnl
            )
        else:
            # Partial close
            closed_qty = quantity
            remaining_qty = position.quantity - quantity
            
            partial_pnl = (price - position.avg_price) * closed_qty
            if position.side == PositionSide.SHORT:
                partial_pnl *= -1
            
            position.realized_pnl += partial_pnl
            position.quantity = remaining_qty
            position.status = PositionStatus.PARTIAL
            
            logger.info(
                "Position reduced",
                client_id=position.client_id,
                position_id=position.position_id,
                remaining_quantity=remaining_qty
            )
        
        return position
    
    def close_position(
        self,
        client_id: str,
        position_id: str,
        price: float,
        order_id: Optional[str] = None
    ) -> Optional[Position]:
        """Close a position completely"""
        with self._lock:
            if client_id not in self._positions:
                return None
            
            position = self._positions[client_id].get(position_id)
            if not position:
                return None
            
            return self._reduce_position(position, position.quantity, price, order_id)
    
    def has_open_position(
        self,
        client_id: str,
        underlying: str,
        strike: Optional[float] = None,
        option_type: Optional[str] = None
    ) -> bool:
        """
        Check if client has an open position.
        
        Args:
            client_id: Client ID
            underlying: Underlying symbol
            strike: Strike price (optional)
            option_type: CE or PE (optional)
            
        Returns:
            True if open position exists
        """
        with self._lock:
            index_key = (client_id, underlying, strike, option_type)
            position_id = self._position_index.get(index_key)
            
            if not position_id:
                return False
            
            position = self._positions.get(client_id, {}).get(position_id)
            return position is not None and position.status == PositionStatus.OPEN
    
    def get_position(
        self,
        client_id: str,
        underlying: str,
        strike: Optional[float] = None,
        option_type: Optional[str] = None
    ) -> Optional[Position]:
        """Get specific position"""
        with self._lock:
            index_key = (client_id, underlying, strike, option_type)
            position_id = self._position_index.get(index_key)
            
            if not position_id:
                return None
            
            return self._positions.get(client_id, {}).get(position_id)
    
    def get_client_positions(
        self,
        client_id: str,
        status: Optional[PositionStatus] = None
    ) -> List[Position]:
        """Get all positions for a client"""
        with self._lock:
            positions = list(self._positions.get(client_id, {}).values())
            
            if status:
                positions = [p for p in positions if p.status == status]
            
            return positions
    
    def get_open_positions(self, client_id: str) -> List[Position]:
        """Get open positions for client"""
        return self.get_client_positions(client_id, PositionStatus.OPEN)
    
    def update_prices(self, client_id: str, prices: Dict[str, float]):
        """
        Update position prices.
        
        Args:
            client_id: Client ID
            prices: Dict of symbol -> price
        """
        with self._lock:
            for position in self._positions.get(client_id, {}).values():
                if position.symbol in prices:
                    position.update_price(prices[position.symbol])
    
    def get_total_pnl(self, client_id: str) -> Dict[str, float]:
        """Get total PnL for client"""
        with self._lock:
            positions = self._positions.get(client_id, {}).values()
            
            unrealized = sum(p.unrealized_pnl for p in positions if p.status == PositionStatus.OPEN)
            realized = sum(p.realized_pnl for p in positions)
            
            return {
                "unrealized_pnl": unrealized,
                "realized_pnl": realized,
                "total_pnl": unrealized + realized
            }
    
    def can_place_order(
        self,
        client_id: str,
        underlying: str,
        strike: Optional[float],
        option_type: Optional[str],
        side: str,
        check_duplicate_buy: bool = True
    ) -> tuple:
        """
        Check if order can be placed (avoid duplicate buys).
        
        Returns:
            (can_place, reason)
        """
        if not check_duplicate_buy:
            return True, ""
        
        with self._lock:
            has_position = self.has_open_position(
                client_id, underlying, strike, option_type
            )
            
            if has_position and side.upper() == "BUY":
                position = self.get_position(client_id, underlying, strike, option_type)
                if position and position.side == PositionSide.LONG:
                    return False, f"Already have long position: {position.position_id}"
            
            return True, ""
    
    def clear_client_positions(self, client_id: str):
        """Clear all positions for a client (use with caution)"""
        with self._lock:
            if client_id in self._positions:
                # Remove from index
                for position in self._positions[client_id].values():
                    index_key = (client_id, position.underlying, position.strike, position.option_type)
                    self._position_index.pop(index_key, None)
                
                del self._positions[client_id]
                
                logger.warning(
                    "Client positions cleared",
                    client_id=client_id
                )
