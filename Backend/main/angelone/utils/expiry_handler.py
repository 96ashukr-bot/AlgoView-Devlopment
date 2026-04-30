"""
Expiry Handler Module
=====================
Handles expiry selection logic for options and futures.

Features:
- Automatic nearest expiry selection (weekly priority)
- Explicit expiry override support
- Expiry validation against contract master
- Weekly/Monthly expiry detection
"""

import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .logging_utils import TradingLogger

logger = TradingLogger("expiry_handler")


class ExpiryType(Enum):
    """Types of expiry"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class ExpiryInfo:
    """Expiry information structure"""
    date: datetime
    expiry_type: ExpiryType
    days_to_expiry: int
    is_current_week: bool
    is_current_month: bool
    formatted_str: str  # Angel One format: 05MAY26
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "expiry_type": self.expiry_type.value,
            "days_to_expiry": self.days_to_expiry,
            "is_current_week": self.is_current_week,
            "is_current_month": self.is_current_month,
            "formatted_str": self.formatted_str
        }


class ExpiryHandler:
    """
    Thread-safe expiry handler for options and futures.
    
    Usage:
        handler = ExpiryHandler()
        handler.set_available_expiries("NIFTY", [datetime(2025, 5, 8), ...])
        nearest = handler.get_nearest_expiry("NIFTY")
    """
    
    MONTH_MAP = {
        1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
        7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
    }
    
    # Weekly expiry days (Thursday for NIFTY/BANKNIFTY, etc.)
    WEEKLY_EXPIRY_DAYS = {
        'NIFTY': 3,      # Thursday (0=Monday)
        'BANKNIFTY': 2,  # Wednesday
        'FINNIFTY': 1,   # Tuesday
        'MIDCPNIFTY': 0, # Monday
        'SENSEX': 4,     # Friday
    }
    
    def __init__(self):
        self._lock = threading.RLock()
        self._expiry_cache: Dict[str, List[datetime]] = {}
        self._last_update: Dict[str, datetime] = {}
    
    def set_available_expiries(self, underlying: str, expiries: List[datetime]):
        """
        Set available expiries for an underlying from contract master.
        
        Args:
            underlying: Symbol like NIFTY, BANKNIFTY
            expiries: List of expiry dates
        """
        with self._lock:
            # Sort and deduplicate
            unique_expiries = sorted(set(expiries))
            self._expiry_cache[underlying.upper()] = unique_expiries
            self._last_update[underlying.upper()] = datetime.now()
            
            logger.debug(
                "Expiries updated",
                underlying=underlying,
                count=len(unique_expiries)
            )
    
    def get_available_expiries(self, underlying: str) -> List[datetime]:
        """Get all available expiries for an underlying"""
        with self._lock:
            return self._expiry_cache.get(underlying.upper(), [])
    
    def get_nearest_expiry(
        self,
        underlying: str,
        prefer_weekly: bool = True,
        min_days: int = 0
    ) -> Optional[ExpiryInfo]:
        """
        Get the nearest expiry for an underlying.
        
        Args:
            underlying: Symbol like NIFTY, BANKNIFTY
            prefer_weekly: If True, prefer weekly expiry over monthly
            min_days: Minimum days to expiry (0 = include today)
            
        Returns:
            ExpiryInfo or None if no expiry found
        """
        with self._lock:
            expiries = self._expiry_cache.get(underlying.upper(), [])
            
            if not expiries:
                # Generate estimated expiries if not available
                expiries = self._generate_estimated_expiries(underlying)
            
            now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            min_date = now + timedelta(days=min_days)
            
            # Filter future expiries
            future_expiries = [e for e in expiries if e >= min_date]
            
            if not future_expiries:
                logger.warning(
                    "No future expiries found",
                    underlying=underlying
                )
                return None
            
            # Sort by date
            future_expiries.sort()
            
            if prefer_weekly:
                # Try to find weekly expiry first
                for exp in future_expiries:
                    if self._is_weekly_expiry(underlying, exp):
                        return self._create_expiry_info(exp, underlying)
            
            # Return nearest expiry
            return self._create_expiry_info(future_expiries[0], underlying)
    
    def get_expiry_by_date(
        self,
        underlying: str,
        target_date: datetime
    ) -> Optional[ExpiryInfo]:
        """
        Get expiry info for a specific date.
        
        Args:
            underlying: Symbol
            target_date: Target expiry date
            
        Returns:
            ExpiryInfo or None
        """
        with self._lock:
            expiries = self._expiry_cache.get(underlying.upper(), [])
            
            # Normalize target date
            target = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Find exact match
            for exp in expiries:
                if exp.date() == target.date():
                    return self._create_expiry_info(exp, underlying)
            
            # Find closest match within 1 day
            for exp in expiries:
                if abs((exp - target).days) <= 1:
                    return self._create_expiry_info(exp, underlying)
            
            return None
    
    def get_monthly_expiry(
        self,
        underlying: str,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Optional[ExpiryInfo]:
        """
        Get monthly expiry for an underlying.
        
        Args:
            underlying: Symbol
            month: Target month (1-12), defaults to current
            year: Target year, defaults to current
            
        Returns:
            ExpiryInfo or None
        """
        now = datetime.now()
        month = month or now.month
        year = year or now.year
        
        with self._lock:
            expiries = self._expiry_cache.get(underlying.upper(), [])
            
            # Filter expiries for target month
            monthly_expiries = [
                e for e in expiries
                if e.month == month and e.year == year
            ]
            
            if not monthly_expiries:
                return None
            
            # Monthly expiry is typically the last Thursday of the month
            # Return the last expiry of the month
            monthly_expiries.sort()
            return self._create_expiry_info(monthly_expiries[-1], underlying)
    
    def resolve_expiry(
        self,
        underlying: str,
        expiry_override: Optional[datetime] = None,
        expiry_str: Optional[str] = None,
        prefer_weekly: bool = True
    ) -> Optional[ExpiryInfo]:
        """
        Resolve expiry with override support.
        
        Priority:
        1. Explicit expiry_override datetime
        2. Parsed expiry_str
        3. Nearest expiry (auto-select)
        
        Args:
            underlying: Symbol
            expiry_override: Explicit expiry datetime
            expiry_str: Expiry string to parse (DDMMMYY format)
            prefer_weekly: Prefer weekly for auto-select
            
        Returns:
            ExpiryInfo or None
        """
        # Priority 1: Explicit override
        if expiry_override:
            info = self.get_expiry_by_date(underlying, expiry_override)
            if info:
                logger.info(
                    "Using explicit expiry override",
                    underlying=underlying,
                    expiry=info.formatted_str
                )
                return info
        
        # Priority 2: Parse expiry string
        if expiry_str:
            parsed_date = self._parse_expiry_string(expiry_str)
            if parsed_date:
                info = self.get_expiry_by_date(underlying, parsed_date)
                if info:
                    logger.info(
                        "Using parsed expiry",
                        underlying=underlying,
                        expiry=info.formatted_str
                    )
                    return info
        
        # Priority 3: Auto-select nearest
        info = self.get_nearest_expiry(underlying, prefer_weekly)
        if info:
            logger.info(
                "Auto-selected nearest expiry",
                underlying=underlying,
                expiry=info.formatted_str,
                days_to_expiry=info.days_to_expiry
            )
        return info
    
    def _create_expiry_info(self, expiry: datetime, underlying: str) -> ExpiryInfo:
        """Create ExpiryInfo from datetime"""
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_to_expiry = (expiry - now).days
        
        # Determine expiry type
        expiry_type = ExpiryType.WEEKLY
        if self._is_monthly_expiry(expiry):
            expiry_type = ExpiryType.MONTHLY
        
        # Check if current week/month
        is_current_week = (expiry - now).days <= 7
        is_current_month = expiry.month == now.month and expiry.year == now.year
        
        # Format string
        formatted = f"{expiry.day:02d}{self.MONTH_MAP[expiry.month]}{expiry.year % 100:02d}"
        
        return ExpiryInfo(
            date=expiry,
            expiry_type=expiry_type,
            days_to_expiry=days_to_expiry,
            is_current_week=is_current_week,
            is_current_month=is_current_month,
            formatted_str=formatted
        )
    
    def _is_weekly_expiry(self, underlying: str, expiry: datetime) -> bool:
        """Check if expiry is a weekly expiry"""
        expected_day = self.WEEKLY_EXPIRY_DAYS.get(underlying.upper(), 3)
        return expiry.weekday() == expected_day
    
    def _is_monthly_expiry(self, expiry: datetime) -> bool:
        """Check if expiry is the last of its kind in the month"""
        next_week = expiry + timedelta(days=7)
        return next_week.month != expiry.month
    
    def _parse_expiry_string(self, expiry_str: str) -> Optional[datetime]:
        """Parse expiry string in various formats"""
        import re
        
        # Try DDMMMYY format (05MAY26)
        match = re.match(r'^(\d{2})([A-Z]{3})(\d{2})$', expiry_str.upper())
        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            year = int(match.group(3)) + 2000
            
            month_map = {v: k for k, v in self.MONTH_MAP.items()}
            month = month_map.get(month_str)
            
            if month:
                try:
                    return datetime(year, month, day)
                except ValueError:
                    pass
        
        # Try YYMMDD format (250508)
        if len(expiry_str) == 6 and expiry_str.isdigit():
            try:
                return datetime.strptime(expiry_str, "%y%m%d")
            except ValueError:
                pass
        
        return None
    
    def _generate_estimated_expiries(self, underlying: str) -> List[datetime]:
        """Generate estimated expiries when contract master not available"""
        expiries = []
        now = datetime.now()
        expiry_day = self.WEEKLY_EXPIRY_DAYS.get(underlying.upper(), 3)
        
        # Generate next 8 weeks of expiries
        current = now
        for _ in range(8):
            # Find next expiry day
            days_ahead = expiry_day - current.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_expiry = current + timedelta(days=days_ahead)
            next_expiry = next_expiry.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if next_expiry > now:
                expiries.append(next_expiry)
            
            current = next_expiry + timedelta(days=1)
        
        logger.debug(
            "Generated estimated expiries",
            underlying=underlying,
            count=len(expiries)
        )
        
        return expiries
    
    def clear_cache(self, underlying: Optional[str] = None):
        """Clear expiry cache"""
        with self._lock:
            if underlying:
                self._expiry_cache.pop(underlying.upper(), None)
                self._last_update.pop(underlying.upper(), None)
            else:
                self._expiry_cache.clear()
                self._last_update.clear()


# Singleton instance
_handler_instance: Optional[ExpiryHandler] = None
_handler_lock = threading.Lock()


def get_expiry_handler() -> ExpiryHandler:
    """Get singleton expiry handler instance"""
    global _handler_instance
    if _handler_instance is None:
        with _handler_lock:
            if _handler_instance is None:
                _handler_instance = ExpiryHandler()
    return _handler_instance
