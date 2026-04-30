"""
Legacy Angel One compatibility facade.

This module intentionally re-exports the upgraded modular implementation so
older imports continue to work while the codebase uses only one execution path.
"""

from main.angleapi_upgraded import (
    SymbolExpiryDateListView,
    angel_one_login,
    angel_one_logout,
    angel_one_refresh_token,
    exit_existing_buy_position_angleone,
    get_access_token,
    get_ltp,
    get_symbol_token,
    get_token_details,
    place_Angle_order,
    place_angel_one_order,
)

__all__ = [
    "SymbolExpiryDateListView",
    "angel_one_login",
    "angel_one_logout",
    "angel_one_refresh_token",
    "exit_existing_buy_position_angleone",
    "get_access_token",
    "get_ltp",
    "get_symbol_token",
    "get_token_details",
    "place_Angle_order",
    "place_angel_one_order",
]
