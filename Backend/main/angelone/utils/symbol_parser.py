"""
Robust Symbol Parser
====================
Parses multiple symbol formats used by Angel One and other brokers.

Supported Formats:
1. Angel One format: NIFTY05MAY2622700CE, BANKNIFTY08MAY2448000PE
2. Dash-separated: NIFTY-250508-22700-CE, BANKNIFTY-250508-48000-PE
3. TradingView format: NIFTY_250508_22700_CE
4. Simple format: NIFTY22700CE (assumes current/nearest expiry)
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from enum import Enum

from .logging_utils import TradingLogger

logger = TradingLogger("symbol_parser")


class SymbolFormat(Enum):
    """Supported symbol formats"""
    ANGEL_ONE = "angel_one"      # NIFTY05MAY2622700CE
    DASH_SEPARATED = "dash"      # NIFTY-250508-22700-CE
    UNDERSCORE = "underscore"    # NIFTY_250508_22700_CE
    SIMPLE = "simple"            # NIFTY22700CE
    UNKNOWN = "unknown"


@dataclass
class ParsedSymbol:
    """Parsed symbol data structure"""
    underlying: str              # NIFTY, BANKNIFTY, etc.
    expiry_date: Optional[datetime]  # Parsed expiry date
    expiry_str: Optional[str]    # Original expiry string
    strike: Optional[float]      # Strike price
    option_type: Optional[str]   # CE or PE
    is_option: bool              # True if option, False if futures/equity
    is_futures: bool             # True if futures
    original_symbol: str         # Original input symbol
    format_detected: SymbolFormat
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "underlying": self.underlying,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "expiry_str": self.expiry_str,
            "strike": self.strike,
            "option_type": self.option_type,
            "is_option": self.is_option,
            "is_futures": self.is_futures,
            "original_symbol": self.original_symbol,
            "format_detected": self.format_detected.value
        }


class SymbolParser:
    """
    Thread-safe symbol parser supporting multiple formats.
    
    Usage:
        parser = SymbolParser()
        result = parser.parse("NIFTY05MAY2622700CE")
        print(result.underlying)  # NIFTY
        print(result.strike)      # 22700.0
        print(result.option_type) # CE
    """
    
    # Month mappings
    MONTH_MAP = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    MONTH_NUM_TO_STR = {v: k for k, v in MONTH_MAP.items()}
    
    # Known underlying symbols
    KNOWN_UNDERLYINGS = {
        'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 
        'BANKEX', 'NIFTYIT', 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK',
        'ICICIBANK', 'SBIN', 'TATAMOTORS', 'TATASTEEL', 'HINDUNILVR'
    }
    
    # Regex patterns for different formats
    PATTERNS = {
        # Angel One: NIFTY05MAY2622700CE or BANKNIFTY08MAY2448000PE
        'angel_one': re.compile(
            r'^([A-Z]+?)(\d{2})([A-Z]{3})(\d{2})(\d+)(CE|PE)$',
            re.IGNORECASE
        ),
        # Angel One futures: NIFTY28MAY25FUT
        'angel_one_fut': re.compile(
            r'^([A-Z]+?)(\d{2})([A-Z]{3})(\d{2})FUT$',
            re.IGNORECASE
        ),
        # Dash separated: NIFTY-250508-22700-CE
        'dash': re.compile(
            r'^([A-Z]+)-(\d{6})-(\d+(?:\.\d+)?)-?(CE|PE)?$',
            re.IGNORECASE
        ),
        # Underscore: NIFTY_250508_22700_CE
        'underscore': re.compile(
            r'^([A-Z]+)_(\d{6})_(\d+(?:\.\d+)?)_?(CE|PE)?$',
            re.IGNORECASE
        ),
        # Simple with strike: NIFTY22700CE
        'simple': re.compile(
            r'^([A-Z]+?)(\d+)(CE|PE)$',
            re.IGNORECASE
        ),
        # Equity symbol: RELIANCE, TCS
        'equity': re.compile(
            r'^([A-Z]+)$',
            re.IGNORECASE
        )
    }
    
    def __init__(self):
        self._cache: Dict[str, ParsedSymbol] = {}
    
    def parse(self, symbol: str) -> ParsedSymbol:
        """
        Parse a symbol string into its components.
        
        Args:
            symbol: The symbol string to parse
            
        Returns:
            ParsedSymbol with extracted components
        """
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        
        symbol = symbol.strip().upper()
        
        # Check cache
        if symbol in self._cache:
            return self._cache[symbol]
        
        result = self._parse_symbol(symbol)
        
        # Cache result
        self._cache[symbol] = result
        
        logger.debug(
            "Symbol parsed",
            symbol=symbol,
            underlying=result.underlying,
            strike=result.strike,
            option_type=result.option_type,
            format=result.format_detected.value
        )
        
        return result
    
    def _parse_symbol(self, symbol: str) -> ParsedSymbol:
        """Internal parsing logic"""
        
        # Try Angel One format first (most common)
        match = self.PATTERNS['angel_one'].match(symbol)
        if match:
            return self._parse_angel_one(match, symbol)
        
        # Try Angel One futures
        match = self.PATTERNS['angel_one_fut'].match(symbol)
        if match:
            return self._parse_angel_one_futures(match, symbol)
        
        # Try dash-separated
        match = self.PATTERNS['dash'].match(symbol)
        if match:
            return self._parse_dash_format(match, symbol)
        
        # Try underscore format
        match = self.PATTERNS['underscore'].match(symbol)
        if match:
            return self._parse_underscore_format(match, symbol)
        
        # Try simple format
        match = self.PATTERNS['simple'].match(symbol)
        if match:
            return self._parse_simple_format(match, symbol)
        
        # Try equity
        match = self.PATTERNS['equity'].match(symbol)
        if match:
            return self._parse_equity(match, symbol)
        
        # Unknown format - return basic parsed result
        logger.warning("Unknown symbol format", symbol=symbol)
        return ParsedSymbol(
            underlying=symbol,
            expiry_date=None,
            expiry_str=None,
            strike=None,
            option_type=None,
            is_option=False,
            is_futures=False,
            original_symbol=symbol,
            format_detected=SymbolFormat.UNKNOWN
        )
    
    def _parse_angel_one(self, match: re.Match, symbol: str) -> ParsedSymbol:
        """Parse Angel One format: NIFTY05MAY2622700CE"""
        underlying = match.group(1)
        day = int(match.group(2))
        month_str = match.group(3).upper()
        year = int(match.group(4))
        strike = float(match.group(5))
        option_type = match.group(6).upper()
        
        # Convert 2-digit year to 4-digit
        full_year = 2000 + year if year < 100 else year
        
        # Parse expiry date
        month = self.MONTH_MAP.get(month_str, 1)
        try:
            expiry_date = datetime(full_year, month, day)
        except ValueError:
            expiry_date = None
        
        expiry_str = f"{day:02d}{month_str}{year:02d}"
        
        return ParsedSymbol(
            underlying=underlying,
            expiry_date=expiry_date,
            expiry_str=expiry_str,
            strike=strike,
            option_type=option_type,
            is_option=True,
            is_futures=False,
            original_symbol=symbol,
            format_detected=SymbolFormat.ANGEL_ONE
        )
    
    def _parse_angel_one_futures(self, match: re.Match, symbol: str) -> ParsedSymbol:
        """Parse Angel One futures: NIFTY28MAY25FUT"""
        underlying = match.group(1)
        day = int(match.group(2))
        month_str = match.group(3).upper()
        year = int(match.group(4))
        
        full_year = 2000 + year if year < 100 else year
        month = self.MONTH_MAP.get(month_str, 1)
        
        try:
            expiry_date = datetime(full_year, month, day)
        except ValueError:
            expiry_date = None
        
        return ParsedSymbol(
            underlying=underlying,
            expiry_date=expiry_date,
            expiry_str=f"{day:02d}{month_str}{year:02d}",
            strike=None,
            option_type=None,
            is_option=False,
            is_futures=True,
            original_symbol=symbol,
            format_detected=SymbolFormat.ANGEL_ONE
        )
    
    def _parse_dash_format(self, match: re.Match, symbol: str) -> ParsedSymbol:
        """Parse dash format: NIFTY-250508-22700-CE"""
        underlying = match.group(1)
        expiry_str = match.group(2)  # YYMMDD
        strike = float(match.group(3))
        option_type = match.group(4).upper() if match.group(4) else None
        
        # Parse YYMMDD
        try:
            expiry_date = datetime.strptime(expiry_str, "%y%m%d")
        except ValueError:
            expiry_date = None
        
        return ParsedSymbol(
            underlying=underlying,
            expiry_date=expiry_date,
            expiry_str=expiry_str,
            strike=strike,
            option_type=option_type,
            is_option=option_type is not None,
            is_futures=option_type is None,
            original_symbol=symbol,
            format_detected=SymbolFormat.DASH_SEPARATED
        )
    
    def _parse_underscore_format(self, match: re.Match, symbol: str) -> ParsedSymbol:
        """Parse underscore format: NIFTY_250508_22700_CE"""
        underlying = match.group(1)
        expiry_str = match.group(2)
        strike = float(match.group(3))
        option_type = match.group(4).upper() if match.group(4) else None
        
        try:
            expiry_date = datetime.strptime(expiry_str, "%y%m%d")
        except ValueError:
            expiry_date = None
        
        return ParsedSymbol(
            underlying=underlying,
            expiry_date=expiry_date,
            expiry_str=expiry_str,
            strike=strike,
            option_type=option_type,
            is_option=option_type is not None,
            is_futures=option_type is None,
            original_symbol=symbol,
            format_detected=SymbolFormat.UNDERSCORE
        )
    
    def _parse_simple_format(self, match: re.Match, symbol: str) -> ParsedSymbol:
        """Parse simple format: NIFTY22700CE (no expiry)"""
        underlying = match.group(1)
        strike = float(match.group(2))
        option_type = match.group(3).upper()
        
        return ParsedSymbol(
            underlying=underlying,
            expiry_date=None,  # Will need to be resolved by ExpiryHandler
            expiry_str=None,
            strike=strike,
            option_type=option_type,
            is_option=True,
            is_futures=False,
            original_symbol=symbol,
            format_detected=SymbolFormat.SIMPLE
        )
    
    def _parse_equity(self, match: re.Match, symbol: str) -> ParsedSymbol:
        """Parse equity symbol: RELIANCE"""
        return ParsedSymbol(
            underlying=match.group(1),
            expiry_date=None,
            expiry_str=None,
            strike=None,
            option_type=None,
            is_option=False,
            is_futures=False,
            original_symbol=symbol,
            format_detected=SymbolFormat.UNKNOWN
        )
    
    def build_angel_one_symbol(
        self,
        underlying: str,
        expiry_date: datetime,
        strike: float,
        option_type: str
    ) -> str:
        """
        Build Angel One format symbol from components.
        
        Args:
            underlying: NIFTY, BANKNIFTY, etc.
            expiry_date: Expiry datetime
            strike: Strike price
            option_type: CE or PE
            
        Returns:
            Symbol in Angel One format (e.g., NIFTY05MAY2622700CE)
        """
        day = expiry_date.day
        month = self.MONTH_NUM_TO_STR[expiry_date.month]
        year = expiry_date.year % 100
        
        # Format strike (remove decimal if whole number)
        strike_str = str(int(strike)) if strike == int(strike) else str(strike)
        
        return f"{underlying}{day:02d}{month}{year:02d}{strike_str}{option_type.upper()}"
    
    def clear_cache(self):
        """Clear the symbol cache"""
        self._cache.clear()


# Singleton instance
_parser_instance: Optional[SymbolParser] = None


def get_symbol_parser() -> SymbolParser:
    """Get singleton symbol parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = SymbolParser()
    return _parser_instance
