"""
Contract Master Manager
=======================
Thread-safe contract master caching with background refresh.

Features:
- Startup loading with background refresh
- Thread-safe access
- Fallback mechanisms
- Optimized lookups with indexing
"""

import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from ..utils.logging_utils import TradingLogger
from ..constants import (
    ANGEL_ONE_CONTRACT_URL,
    CONTRACT_MASTER_CACHE_TTL,
    ALLOW_STRIKE_FALLBACK,
    Exchange
)

logger = TradingLogger("contract_manager")


@dataclass
class Contract:
    """Contract/Instrument data structure"""
    token: str
    symbol: str
    name: str
    expiry: Optional[datetime]
    strike: Optional[float]
    lot_size: int
    instrument_type: str
    exchange: str
    tick_size: float
    option_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "symbol": self.symbol,
            "name": self.name,
            "expiry": self.expiry.isoformat() if self.expiry else None,
            "strike": self.strike,
            "lot_size": self.lot_size,
            "instrument_type": self.instrument_type,
            "exchange": self.exchange,
            "tick_size": self.tick_size,
            "option_type": self.option_type
        }


class ContractIndex:
    """Indexed contract lookup for fast searches"""
    
    def __init__(self):
        self._lock = threading.RLock()
        # Primary index: token -> Contract
        self.by_token: Dict[str, Contract] = {}
        # Secondary indexes
        self.by_symbol: Dict[str, List[Contract]] = defaultdict(list)
        self.by_underlying: Dict[str, List[Contract]] = defaultdict(list)
        self.by_expiry: Dict[str, List[Contract]] = defaultdict(list)
        # Composite index: (underlying, strike, expiry, option_type) -> Contract
        self.options_index: Dict[Tuple, Contract] = {}
    
    def add(self, contract: Contract):
        with self._lock:
            self.by_token[contract.token] = contract
            self.by_symbol[contract.symbol].append(contract)
            
            # Extract underlying from symbol
            underlying = self._extract_underlying(contract.symbol)
            if underlying:
                self.by_underlying[underlying].append(contract)
            
            # Index by expiry
            if contract.expiry:
                expiry_key = contract.expiry.strftime("%Y%m%d")
                self.by_expiry[expiry_key].append(contract)
            
            # Options composite index
            if contract.option_type and contract.strike and contract.expiry:
                key = (
                    underlying,
                    contract.strike,
                    contract.expiry.strftime("%Y%m%d"),
                    contract.option_type
                )
                self.options_index[key] = contract
    
    def _extract_underlying(self, symbol: str) -> Optional[str]:
        """Extract underlying from symbol"""
        known = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX']
        symbol_upper = symbol.upper()
        for u in known:
            if symbol_upper.startswith(u):
                return u
        return None
    
    def clear(self):
        with self._lock:
            self.by_token.clear()
            self.by_symbol.clear()
            self.by_underlying.clear()
            self.by_expiry.clear()
            self.options_index.clear()


class ContractMasterManager:
    """
    Thread-safe contract master manager with background refresh.
    
    Usage:
        manager = ContractMasterManager.get_instance()
        manager.start_background_refresh()
        
        contract = manager.get_contract_by_token("12345")
        contract = manager.find_option_contract("NIFTY", 22700, expiry, "CE")
    """
    
    _instance: Optional['ContractMasterManager'] = None
    _instance_lock = threading.Lock()
    
    def __init__(self):
        self._lock = threading.RLock()
        self._index = ContractIndex()
        self._raw_data: List[Dict] = []
        self._last_refresh: Optional[datetime] = None
        self._refresh_in_progress = False
        self._initialized = False
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        self._fallback_data: List[Dict] = []
    
    @classmethod
    def get_instance(cls) -> 'ContractMasterManager':
        """Get singleton instance"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = ContractMasterManager()
        return cls._instance
    
    def initialize(self, blocking: bool = False) -> bool:
        """
        Initialize contract master.
        
        Args:
            blocking: If True, wait for initial load
            
        Returns:
            True if initialized successfully
        """
        if self._initialized and self._is_cache_valid():
            return True
        
        if blocking:
            return self._refresh_contracts()
        else:
            thread = threading.Thread(
                target=self._refresh_contracts,
                daemon=True,
                name="ContractMasterInit"
            )
            thread.start()
            return True
    
    def start_background_refresh(self, interval_seconds: int = None):
        """Start background refresh thread"""
        if self._refresh_thread and self._refresh_thread.is_alive():
            return
        
        interval = interval_seconds or CONTRACT_MASTER_CACHE_TTL
        self._stop_refresh.clear()
        
        self._refresh_thread = threading.Thread(
            target=self._background_refresh_loop,
            args=(interval,),
            daemon=True,
            name="ContractMasterRefresh"
        )
        self._refresh_thread.start()
        
        logger.info(
            "Background refresh started",
            interval_seconds=interval
        )
    
    def stop_background_refresh(self):
        """Stop background refresh"""
        self._stop_refresh.set()
        if self._refresh_thread:
            self._refresh_thread.join(timeout=5)
    
    def _background_refresh_loop(self, interval: int):
        """Background refresh loop"""
        # Initial load
        self._refresh_contracts()
        
        while not self._stop_refresh.is_set():
            self._stop_refresh.wait(timeout=interval)
            if not self._stop_refresh.is_set():
                self._refresh_contracts()
    
    def _refresh_contracts(self) -> bool:
        """Refresh contract master from API"""
        if self._refresh_in_progress:
            return False
        
        self._refresh_in_progress = True
        start_time = time.time()
        
        try:
            logger.info("Refreshing contract master")
            
            response = requests.get(
                ANGEL_ONE_CONTRACT_URL,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                raise ValueError("Empty contract master response")
            
            # Build new index
            new_index = ContractIndex()
            
            for item in data:
                contract = self._parse_contract(item)
                if contract:
                    new_index.add(contract)
            
            # Atomic swap
            with self._lock:
                self._index = new_index
                self._raw_data = data
                self._last_refresh = datetime.now()
                self._initialized = True
                self._fallback_data = data
            
            elapsed = time.time() - start_time
            logger.info(
                "Contract master refreshed",
                contracts_count=len(new_index.by_token),
                elapsed_seconds=round(elapsed, 2)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Contract master refresh failed",
                error=str(e)
            )
            
            # Use fallback if available
            if self._fallback_data and not self._initialized:
                self._load_fallback()
            
            return False
            
        finally:
            self._refresh_in_progress = False
    
    def _load_fallback(self):
        """Load from fallback data"""
        try:
            new_index = ContractIndex()
            for item in self._fallback_data:
                contract = self._parse_contract(item)
                if contract:
                    new_index.add(contract)
            
            with self._lock:
                self._index = new_index
                self._initialized = True
            
            logger.warning("Loaded from fallback data")
        except Exception as e:
            logger.error("Fallback load failed", error=str(e))
    
    def _parse_contract(self, item: Dict) -> Optional[Contract]:
        """Parse contract from API response"""
        try:
            # Parse expiry
            expiry = None
            expiry_str = item.get('expiry', '')
            if expiry_str:
                try:
                    expiry = datetime.strptime(expiry_str, "%d%b%Y")
                except:
                    try:
                        expiry = datetime.strptime(expiry_str, "%Y-%m-%d")
                    except:
                        pass
            
            # Parse strike
            strike = None
            strike_val = item.get('strike')
            if strike_val:
                try:
                    strike = self._normalize_raw_strike(strike_val)
                except Exception:
                    pass
            
            # Determine option type
            option_type = None
            symbol = item.get('symbol', '')
            if symbol.endswith('CE'):
                option_type = 'CE'
            elif symbol.endswith('PE'):
                option_type = 'PE'
            
            return Contract(
                token=str(item.get('token', '')),
                symbol=symbol,
                name=item.get('name', ''),
                expiry=expiry,
                strike=strike,
                lot_size=int(item.get('lotsize', 1)),
                instrument_type=item.get('instrumenttype', ''),
                exchange=item.get('exch_seg', 'NFO'),
                tick_size=float(item.get('tick_size', 0.05)),
                option_type=option_type
            )
        except Exception as e:
            return None

    @staticmethod
    def _normalize_raw_strike(strike: Optional[float]) -> Optional[float]:
        """Normalize contract-master strike values without assuming a fixed scale."""
        if strike in (None, ""):
            return None

        value = float(strike)
        while abs(value) >= 100000:
            value /= 100
        return round(value, 2)
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self._last_refresh:
            return False
        age = (datetime.now() - self._last_refresh).total_seconds()
        return age < CONTRACT_MASTER_CACHE_TTL
    
    def get_contract_by_token(self, token: str) -> Optional[Contract]:
        """Get contract by token"""
        with self._lock:
            return self._index.by_token.get(str(token))
    
    def get_contracts_by_symbol(self, symbol: str) -> List[Contract]:
        """Get contracts by symbol"""
        with self._lock:
            return self._index.by_symbol.get(symbol.upper(), [])
    
    def get_contracts_by_underlying(self, underlying: str) -> List[Contract]:
        """Get all contracts for an underlying"""
        with self._lock:
            return self._index.by_underlying.get(underlying.upper(), [])

    @staticmethod
    def _normalize_strike(strike: Optional[float]) -> Optional[float]:
        if strike is None:
            return None
        return ContractMasterManager._normalize_raw_strike(strike)
    
    def find_option_contract(
        self,
        underlying: str,
        strike: float,
        expiry: datetime,
        option_type: str,
        exchange: str = "NFO"
    ) -> Optional[Contract]:
        """
        Find specific option contract.
        
        Args:
            underlying: NIFTY, BANKNIFTY, etc.
            strike: Strike price
            expiry: Expiry date
            option_type: CE or PE
            exchange: Exchange (default NFO)
            
        Returns:
            Contract or None
        """
        with self._lock:
            # Try composite index first
            normalized_strike = self._normalize_strike(strike)
            key = (
                underlying.upper(),
                normalized_strike,
                expiry.strftime("%Y%m%d"),
                option_type.upper()
            )
            
            contract = self._index.options_index.get(key)
            if contract:
                return contract
            
            # Fallback to search
            contracts = self._index.by_underlying.get(underlying.upper(), [])
            
            for c in contracts:
                if (self._normalize_strike(c.strike) == normalized_strike and
                    c.option_type == option_type.upper() and
                    c.expiry and c.expiry.date() == expiry.date() and
                    c.exchange == exchange):
                    return c
            
            return None

    def resolve_option_contract(
        self,
        underlying: str,
        strike: float,
        option_type: str,
        exchange: str = "NFO",
        expiry: Optional[datetime] = None,
        prefer_weekly: bool = True,
        allow_strike_fallback: bool = ALLOW_STRIKE_FALLBACK,
    ) -> Tuple[Optional[Contract], Dict[str, Any]]:
        """
        Resolve an option contract using strict matching first.

        Matching strategy:
        1. Exact symbol family + option type.
        2. Exact strike.
        3. Nearest expiry first, with weekly contracts preferred.
        4. Optional nearest-strike fallback only when explicitly enabled.
        """
        if not self._initialized:
            self.initialize(blocking=True)

        normalized_strike = self._normalize_strike(strike)
        contracts = [
            c for c in self.get_contracts_by_underlying(underlying)
            if c.exchange == exchange
            and c.option_type == option_type.upper()
            and c.strike is not None
            and c.expiry is not None
        ]

        if not contracts:
            return None, {"match_type": "none", "reason": "no_contracts_for_underlying"}

        now = datetime.now().date()
        eligible = [c for c in contracts if c.expiry.date() >= now]
        if expiry:
            eligible = [c for c in eligible if c.expiry.date() == expiry.date()]

        if not eligible and expiry:
            eligible = [c for c in contracts if c.expiry.date() >= now]

        if not eligible:
            return None, {"match_type": "none", "reason": "no_future_contracts"}

        def weekly_priority(contract: Contract) -> Tuple[int, datetime]:
            expiry_contracts = [
                c for c in eligible
                if c.expiry.date() == contract.expiry.date()
            ]
            same_month = [c for c in eligible if c.expiry.year == contract.expiry.year and c.expiry.month == contract.expiry.month]
            is_monthly = bool(same_month) and contract.expiry.date() == max(c.expiry.date() for c in same_month)
            weekly_rank = 1 if (prefer_weekly and is_monthly) else 0
            return (weekly_rank, contract.expiry)

        eligible.sort(key=weekly_priority)

        expiries_in_priority = []
        seen_expiries = set()
        for contract in eligible:
            expiry_key = contract.expiry.date()
            if expiry_key not in seen_expiries:
                seen_expiries.add(expiry_key)
                expiries_in_priority.append(contract.expiry)

        for candidate_expiry in expiries_in_priority:
            exact_matches = [
                contract for contract in eligible
                if contract.expiry.date() == candidate_expiry.date()
                and self._normalize_strike(contract.strike) == normalized_strike
            ]
            if exact_matches:
                contract = exact_matches[0]
                return contract, {
                    "match_type": "exact",
                    "fallback_used": False,
                    "expiry": contract.expiry.isoformat(),
                }

        if not allow_strike_fallback:
            nearest = min(
                eligible,
                key=lambda c: (
                    abs((c.strike or 0) - normalized_strike),
                    c.expiry,
                )
            )
            return None, {
                "match_type": "exact_not_found",
                "fallback_used": False,
                "requested_strike": normalized_strike,
                "nearest_available_strike": nearest.strike,
                "nearest_available_expiry": nearest.expiry.isoformat() if nearest.expiry else None,
            }

        fallback = min(
            eligible,
            key=lambda c: (
                abs((c.strike or 0) - normalized_strike),
                c.expiry,
            )
        )
        return fallback, {
            "match_type": "nearest_strike_fallback",
            "fallback_used": True,
            "requested_strike": normalized_strike,
            "resolved_strike": fallback.strike,
            "expiry": fallback.expiry.isoformat() if fallback.expiry else None,
        }
    
    def get_expiries_for_underlying(self, underlying: str) -> List[datetime]:
        """Get all expiries for an underlying"""
        with self._lock:
            contracts = self._index.by_underlying.get(underlying.upper(), [])
            expiries = set()
            for c in contracts:
                if c.expiry:
                    expiries.add(c.expiry)
            return sorted(expiries)
    
    def search_contracts(
        self,
        underlying: Optional[str] = None,
        expiry: Optional[datetime] = None,
        option_type: Optional[str] = None,
        min_strike: Optional[float] = None,
        max_strike: Optional[float] = None,
        exchange: str = "NFO"
    ) -> List[Contract]:
        """Search contracts with filters"""
        with self._lock:
            if underlying:
                contracts = self._index.by_underlying.get(underlying.upper(), [])
            else:
                contracts = list(self._index.by_token.values())
            
            results = []
            for c in contracts:
                if exchange and c.exchange != exchange:
                    continue
                if expiry and c.expiry and c.expiry.date() != expiry.date():
                    continue
                if option_type and c.option_type != option_type.upper():
                    continue
                if min_strike and c.strike and c.strike < min_strike:
                    continue
                if max_strike and c.strike and c.strike > max_strike:
                    continue
                results.append(c)
            
            return results
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    @property
    def last_refresh(self) -> Optional[datetime]:
        return self._last_refresh
    
    @property
    def contract_count(self) -> int:
        with self._lock:
            return len(self._index.by_token)
