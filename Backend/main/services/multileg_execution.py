from __future__ import annotations

import csv
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import requests
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from zoneinfo import ZoneInfo

from main.angleapi_upgraded import get_angel_one_margin, get_ltp
from main.angelone.constants import MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE, MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE, TIMEZONE
from main.angelone.managers.contract_manager import ContractMasterManager
from main.angelone.services.auth_service import AuthService
from main.angelone.utils.logging_utils import TradingLogger
from main.Alice_Blue_Api import fetch_instrument_data, get_alice_session
from main.broker_instrument_cache import ensure_dhan_instruments_file, ensure_fivepaisa_scrip_master_file, ensure_fyers_instruments_file, load_upstox_instruments
from main.broker_order_utils import extract_ltp_from_quote_payload
from main.broker_registry import normalize_broker_name
from main.execution_engine import ContractInfo, ExecutionRequest, OrderConfig, get_execution_engine
from main.models import ClientBrokerdetails, ClientMultiLegStrategySetting, Strategies, StrategyExecution, StrategyExecutionLog, StrategyLeg, User
from main.permissions import can_access_client_record, is_admin_or_superadmin
from main.fivepaisa import MARKET_FEED_URL
from main.services.broker_transport import ProxyRoutingRequiredError
from main.services.option_ltp_fallback import cache_option_ltp, fetch_nse_option_chain_ltp
from main.services.proxy_utils import build_requests_proxy_config
from main.dhanapi import DHAN_LTP_URL
from main.zerodha import KITE_LTP_URL

try:
    from dhanhq import dhanhq
except Exception:  # pragma: no cover - optional at import time in some environments
    dhanhq = None

try:
    from kiteconnect import KiteConnect
except Exception:  # pragma: no cover - optional at import time in some environments
    KiteConnect = None

logger = TradingLogger("multileg_execution")


SUPPORTED_STRATEGIES = {
    "BULL_CALL_SPREAD",
    "BEAR_CALL_SPREAD",
    "BEAR_PUT_SPREAD",
    "SHORT_STRADDLE",
    "LONG_CALL_BUTTERFLY",
    "SHORT_CALL_BUTTERFLY",
    "LONG_CALL_CONDOR",
    "SHORT_CALL_CONDOR",
    "LONG_IRON_CONDOR",
    "SHORT_IRON_BUTTERFLY",
    "CUSTOM_BASKET",
}

ACTIVE_STRATEGY_STATUSES = {
    StrategyExecution.STATUS_PENDING,
    StrategyExecution.STATUS_EXECUTING,
    StrategyExecution.STATUS_ACTIVE,
    StrategyExecution.STATUS_EXITING,
}

ACTIVE_LEG_STATUSES = {
    StrategyLeg.STATUS_EXECUTING,
    StrategyLeg.STATUS_ACTIVE,
    StrategyLeg.STATUS_EXITING,
}


class MultiLegExecutionError(Exception):
    def __init__(self, message: str, *, error_code: str = "MULTILEG_EXECUTION_ERROR", metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.metadata = metadata or {}


def _extract_response_data(response: Any) -> Dict[str, Any]:
    if not isinstance(response, dict):
        return {"status": "Failed", "message": str(response)}

    data = response.get("data")
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            return data[0]
        return {"status": "Failed", "message": str(data[0]) if data else "Empty response list"}
    if isinstance(data, str):
        return {
            "status": str(response.get("status") or "Failed"),
            "message": data,
            "raw_data": data,
        }

    return {
        "status": str(response.get("status") or "Failed"),
        "message": str(response.get("message") or "Unknown response shape"),
    }


def _extract_response_message(response: Any) -> str:
    data = _extract_response_data(response)
    for key in ("message", "error", "status_message", "statusMessage", "remarks", "detail"):
        value = data.get(key)
        if value not in (None, "", "None"):
            return str(value)

    if isinstance(response, dict):
        for key in ("message", "error", "detail", "remarks"):
            value = response.get(key)
            if value not in (None, "", "None"):
                return str(value)

    return "Broker did not return a detailed failure reason."


@dataclass(frozen=True)
class ResolvedContract:
    underlying: str
    expiry: datetime
    strike_price: float
    option_type: str
    symbol: str
    token: str
    lot_size: int
    tick_size: float
    exchange: str = "NFO"


@dataclass(frozen=True)
class StrategyLegPlan:
    leg_name: str
    transaction_type: str
    option_type: str
    strike_price: float
    quantity: int
    order_type: str
    product_type: str
    limit_price: Optional[float]
    contract: ResolvedContract
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyPlan:
    strategy_name: str
    client_id: int
    broker: str
    underlying: str
    expiry: datetime
    quantity_lots: int
    order_type: str
    product_type: str
    buffer_percentage: Optional[float]
    sell_leg_stop_loss_percentage: Optional[float]
    combined_trailing_start: Optional[float]
    combined_trailing_gap: Optional[float]
    entry_time: Optional[str]
    exit_time: Optional[str]
    allow_reentry: bool
    idempotency_key: str
    legs: List[StrategyLegPlan]
    raw_config: Dict[str, Any]

    @property
    def total_quantity(self) -> int:
        return sum(int(leg.quantity or 0) for leg in self.legs)


class MultiLegLockManager:
    LOCK_TIMEOUT_SECONDS = 120

    def acquire(self, key: str) -> bool:
        return bool(cache.add(f"multileg:lock:{key}", timezone.now().isoformat(), timeout=self.LOCK_TIMEOUT_SECONDS))

    def release(self, key: str) -> None:
        cache.delete(f"multileg:lock:{key}")


class MultiLegRateLimiter:
    MAX_ORDERS_PER_SECOND = 10
    WINDOW_SECONDS = 1

    def wait_for_slot(self, client_id: int, broker_name: str) -> None:
        key = f"multileg:rate:{client_id}:{broker_name.lower()}"
        current_ts = timezone.now().timestamp()
        snapshots = cache.get(key) or []
        snapshots = [ts for ts in snapshots if current_ts - float(ts) < self.WINDOW_SECONDS]
        if len(snapshots) >= self.MAX_ORDERS_PER_SECOND:
            raise MultiLegExecutionError(
                "Order rate limit exceeded for multi-leg execution.",
                error_code="MULTILEG_RATE_LIMIT_EXCEEDED",
                metadata={"client_id": client_id, "broker": broker_name},
            )
        snapshots.append(current_ts)
        cache.set(key, snapshots, timeout=self.WINDOW_SECONDS + 1)


class MultiLegContractResolver:
    UPSTOX_MARKET_QUOTE_LTP_URL = "https://api.upstox.com/v2/market-quote/ltp"

    def __init__(self):
        self._contract_manager = ContractMasterManager.get_instance()

    def _proxy_config_for_broker(self, broker_details: Optional[ClientBrokerdetails]) -> dict[str, str]:
        node = getattr(broker_details, "execution_node", None)
        if not node:
            raise MultiLegExecutionError(
                "No verified execution node/proxy is assigned. Broker preflight calls are blocked.",
                error_code="EXECUTION_ROUTE_REQUIRED",
            )
        if not node.is_active or not node.is_verified_with_broker:
            raise MultiLegExecutionError(
                "Assigned execution node/proxy is not active and broker verified.",
                error_code="EXECUTION_ROUTE_NOT_VERIFIED",
            )
        if getattr(node, "execution_type", None) == node.EXECUTION_TYPE_PROXY and not node.proxy_public_ip_verified:
            raise MultiLegExecutionError(
                "Assigned proxy public IP is not verified.",
                error_code="EXECUTION_PROXY_NOT_VERIFIED",
            )
        try:
            return build_requests_proxy_config(node)
        except (ValueError, ProxyRoutingRequiredError) as exc:
            raise MultiLegExecutionError(str(exc), error_code="EXECUTION_ROUTE_INVALID") from exc

    def resolve_expiry(self, underlying: str, expiry_value: Any, exchange: str = "NFO") -> datetime:
        self._contract_manager.initialize(blocking=True)
        normalized_underlying = str(underlying or "").strip().upper()
        if not normalized_underlying:
            raise MultiLegExecutionError("Underlying is required.", error_code="MISSING_UNDERLYING")

        if expiry_value in (None, "", "nearest"):
            expiries = self._contract_manager.get_expiries_for_underlying(normalized_underlying)
            if not expiries:
                raise MultiLegExecutionError(
                    "Unable to resolve nearest expiry for underlying.",
                    error_code="EXPIRY_RESOLUTION_FAILED",
                    metadata={"underlying": normalized_underlying},
                )
            return expiries[0]

        if isinstance(expiry_value, datetime):
            return expiry_value

        expiry_str = str(expiry_value).strip()
        for fmt in ("%Y-%m-%d", "%d%b%Y", "%d%b%y"):
            try:
                return datetime.strptime(expiry_str, fmt)
            except ValueError:
                continue

        raise MultiLegExecutionError(
            "Expiry format is invalid. Use YYYY-MM-DD or nearest.",
            error_code="INVALID_EXPIRY_FORMAT",
        )

    def resolve_option_contract(
        self,
        *,
        broker_name: str,
        underlying: str,
        strike_price: float,
        option_type: str,
        expiry: datetime,
        exchange: str = "NFO",
        broker_details: Optional[ClientBrokerdetails] = None,
    ) -> ResolvedContract:
        normalized_broker = str(broker_name or "").strip().lower()
        if normalized_broker in {"upstox"}:
            return self._resolve_upstox_option_contract(
                underlying=underlying,
                strike_price=strike_price,
                option_type=option_type,
                expiry=expiry,
                exchange=exchange,
            )
        if normalized_broker in {"dhan"}:
            return self._resolve_dhan_option_contract(
                underlying=underlying,
                strike_price=strike_price,
                option_type=option_type,
                expiry=expiry,
            )
        if normalized_broker in {"fyers"}:
            return self._resolve_fyers_option_contract(
                underlying=underlying,
                strike_price=strike_price,
                option_type=option_type,
                expiry=expiry,
                exchange=exchange,
            )
        if normalized_broker in {"5paisa", "5 paisa"}:
            return self._resolve_fivepaisa_option_contract(
                underlying=underlying,
                strike_price=strike_price,
                option_type=option_type,
                expiry=expiry,
            )
        if normalized_broker in {"zerodha"}:
            return self._resolve_zerodha_option_contract(
                underlying=underlying,
                strike_price=strike_price,
                option_type=option_type,
                expiry=expiry,
                exchange=exchange,
                broker_details=broker_details,
            )
        if normalized_broker in {"alice blue", "aliceblue"}:
            return self._resolve_alice_blue_option_contract(
                underlying=underlying,
                strike_price=strike_price,
                option_type=option_type,
                expiry=expiry,
                broker_details=broker_details,
            )
        if normalized_broker not in {"angel one", "angle one"}:
            raise MultiLegExecutionError(
                f"Multi-leg contract resolution is not implemented yet for broker: {broker_name}.",
                error_code="BROKER_NOT_IMPLEMENTED",
            )

        self._contract_manager.initialize(blocking=True)
        contract, contract_resolution = self._contract_manager.resolve_option_contract(
            underlying=str(underlying or "").strip().upper(),
            strike=float(strike_price),
            option_type=str(option_type or "").strip().upper(),
            exchange=exchange,
            expiry=expiry,
            prefer_weekly=True,
        )
        if not contract:
            raise MultiLegExecutionError(
                "Exact option contract could not be resolved.",
                error_code="CONTRACT_RESOLUTION_FAILED",
                metadata={
                    "underlying": underlying,
                    "strike_price": strike_price,
                    "option_type": option_type,
                    "expiry": expiry.isoformat() if expiry else None,
                    "resolution": contract_resolution,
                },
            )

        return ResolvedContract(
            underlying=str(underlying or "").strip().upper(),
            expiry=contract.expiry,
            strike_price=float(strike_price),
            option_type=str(option_type or "").strip().upper(),
            symbol=contract.symbol,
            token=str(contract.token),
            lot_size=int(contract.lot_size or 0),
            tick_size=float(contract.tick_size or 0.05),
            exchange=str(contract.exchange or exchange).upper(),
        )

    def fetch_ltp(self, broker_details: ClientBrokerdetails, contract: ResolvedContract) -> Optional[float]:
        broker_name = str(getattr(getattr(broker_details, "broker_name", None), "broker_name", "") or "").strip().lower()
        if broker_name == "upstox":
            return self._fetch_upstox_ltp(broker_details, contract)
        if broker_name == "dhan":
            return self._fetch_dhan_ltp(broker_details, contract)
        if broker_name == "fyers":
            return self._fetch_fyers_ltp(broker_details, contract)
        if broker_name in {"5paisa", "5 paisa"}:
            return self._fetch_fivepaisa_ltp(broker_details, contract)
        if broker_name == "zerodha":
            return self._fetch_zerodha_ltp(broker_details, contract)
        if broker_name in {"alice blue", "aliceblue"}:
            return self._fetch_alice_blue_ltp(broker_details, contract)

        ltp = get_ltp(
            symbol_token=contract.token,
            exchange=contract.exchange,
            tradingsymbol=contract.symbol,
            broker_details=broker_details,
        )
        try:
            return float(ltp) if ltp is not None else None
        except (TypeError, ValueError):
            return None

    def _resolve_dhan_option_contract(
        self,
        *,
        underlying: str,
        strike_price: float,
        option_type: str,
        expiry: datetime,
    ) -> ResolvedContract:
        csv_path = ensure_dhan_instruments_file()
        target_symbol = self._build_trade_symbol_for_broker("dhan", underlying, expiry, strike_price, option_type)
        target_expiry = expiry.strftime("%Y-%m-%d")
        matched_row = None

        with open(csv_path, newline="", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                trading_symbol = self._normalize_symbol(row.get("SEM_TRADING_SYMBOL"))
                option_value = str(row.get("SEM_OPTION_TYPE") or row.get("SEM_INSTRUMENT_NAME") or "").upper()
                strike_value = self._safe_float(row.get("SEM_STRIKE_PRICE") or row.get("SEM_EXM_EXERCISE_PRICE"))
                expiry_value = self._normalize_date_str(row.get("SEM_EXPIRY_DATE"))
                if trading_symbol == self._normalize_symbol(target_symbol):
                    matched_row = row
                    break
                if (
                    self._normalize_symbol(row.get("SEM_CUSTOM_SYMBOL")).startswith(self._normalize_symbol(underlying))
                    and option_type in option_value
                    and strike_value is not None
                    and abs(strike_value - float(strike_price)) < 0.01
                    and expiry_value == target_expiry
                ):
                    matched_row = row
                    break

        if not matched_row:
            raise MultiLegExecutionError(
                "Exact Dhan option contract could not be resolved.",
                error_code="CONTRACT_RESOLUTION_FAILED",
                metadata={"broker": "Dhan", "symbol": target_symbol},
            )

        return ResolvedContract(
            underlying=str(underlying or "").strip().upper(),
            expiry=expiry,
            strike_price=float(strike_price),
            option_type=str(option_type or "").strip().upper(),
            symbol=str(matched_row.get("SEM_TRADING_SYMBOL") or target_symbol).strip(),
            token=str(matched_row.get("SEM_SMST_SECURITY_ID") or "").strip(),
            lot_size=self._safe_int(matched_row.get("SEM_LOT_UNITS") or 0),
            tick_size=self._safe_float(matched_row.get("SEM_TICK_SIZE") or 0.05) or 0.05,
            exchange="NFO",
        )

    def _resolve_fyers_option_contract(
        self,
        *,
        underlying: str,
        strike_price: float,
        option_type: str,
        expiry: datetime,
        exchange: str,
    ) -> ResolvedContract:
        csv_path = ensure_fyers_instruments_file(exchange=exchange, segment="FNO")
        target_symbol = self._build_trade_symbol_for_broker("fyers", underlying, expiry, strike_price, option_type)
        matched_row = None

        with open(csv_path, newline="", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                if self._normalize_symbol(row.get("Symbol Details")) == self._normalize_symbol(target_symbol):
                    matched_row = row
                    break

        if not matched_row:
            raise MultiLegExecutionError(
                "Exact FYERS option contract could not be resolved.",
                error_code="CONTRACT_RESOLUTION_FAILED",
                metadata={"broker": "FYERS", "symbol": target_symbol},
            )

        return ResolvedContract(
            underlying=str(underlying or "").strip().upper(),
            expiry=expiry,
            strike_price=float(strike_price),
            option_type=str(option_type or "").strip().upper(),
            symbol=str(matched_row.get("Symbol Ticker") or "").strip(),
            token=str(matched_row.get("FyToken") or "").strip(),
            lot_size=self._safe_int(matched_row.get("Minimum Lot Size") or 0),
            tick_size=self._safe_float(matched_row.get("Tick Size") or 0.05) or 0.05,
            exchange="NFO",
        )

    def _resolve_fivepaisa_option_contract(
        self,
        *,
        underlying: str,
        strike_price: float,
        option_type: str,
        expiry: datetime,
    ) -> ResolvedContract:
        file_path = self._ensure_fivepaisa_scrip_master("nse_fo")
        target_symbol = self._build_trade_symbol_for_broker("5paisa", underlying, expiry, strike_price, option_type)
        matched_row = None

        with open(file_path, newline="", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                if self._normalize_symbol(row.get("Name")) == self._normalize_symbol(target_symbol):
                    matched_row = row
                    break

        if not matched_row:
            raise MultiLegExecutionError(
                "Exact 5Paisa option contract could not be resolved.",
                error_code="CONTRACT_RESOLUTION_FAILED",
                metadata={"broker": "5Paisa", "symbol": target_symbol},
            )

        return ResolvedContract(
            underlying=str(underlying or "").strip().upper(),
            expiry=expiry,
            strike_price=float(strike_price),
            option_type=str(option_type or "").strip().upper(),
            symbol=str(matched_row.get("Name") or target_symbol).strip(),
            token=str(matched_row.get("ScripCode") or "").strip(),
            lot_size=self._safe_int(
                matched_row.get("LotQty") or matched_row.get("LotSize") or matched_row.get("QtyLotSize") or 0
            ),
            tick_size=self._safe_float(matched_row.get("TickSize") or 0.05) or 0.05,
            exchange="NFO",
        )

    def _resolve_zerodha_option_contract(
        self,
        *,
        underlying: str,
        strike_price: float,
        option_type: str,
        expiry: datetime,
        exchange: str,
        broker_details: Optional[ClientBrokerdetails],
    ) -> ResolvedContract:
        if KiteConnect is None or not broker_details:
            raise MultiLegExecutionError("Zerodha client library or broker details unavailable.", error_code="BROKER_NOT_IMPLEMENTED")

        api_key = broker_details.broker_API_KEY
        access_token = self._get_broker_access_token(broker_details)
        proxy_config = self._proxy_config_for_broker(broker_details)
        kite = KiteConnect(api_key=api_key, proxies=proxy_config)
        if access_token:
            kite.set_access_token(access_token)

        target_symbol = self._build_trade_symbol_for_broker("zerodha", underlying, expiry, strike_price, option_type)
        instruments = kite.instruments(exchange or "NFO")
        matched_instrument = None
        for instrument in instruments:
            if self._normalize_symbol(instrument.get("tradingsymbol")) == self._normalize_symbol(target_symbol):
                matched_instrument = instrument
                break
        if not matched_instrument:
            raise MultiLegExecutionError(
                "Exact Zerodha option contract could not be resolved.",
                error_code="CONTRACT_RESOLUTION_FAILED",
                metadata={"broker": "Zerodha", "symbol": target_symbol},
            )

        return ResolvedContract(
            underlying=str(underlying or "").strip().upper(),
            expiry=matched_instrument.get("expiry") or expiry,
            strike_price=float(strike_price),
            option_type=str(option_type or "").strip().upper(),
            symbol=str(matched_instrument.get("tradingsymbol") or target_symbol).strip(),
            token=str(matched_instrument.get("instrument_token") or "").strip(),
            lot_size=self._safe_int(matched_instrument.get("lot_size") or 0),
            tick_size=self._safe_float(matched_instrument.get("tick_size") or 0.05) or 0.05,
            exchange=str(matched_instrument.get("exchange") or "NFO").upper(),
        )

    def _resolve_alice_blue_option_contract(
        self,
        *,
        underlying: str,
        strike_price: float,
        option_type: str,
        expiry: datetime,
        broker_details: Optional[ClientBrokerdetails],
    ) -> ResolvedContract:
        target_symbol = self._build_trade_symbol_for_broker("alice blue", underlying, expiry, strike_price, option_type)
        file_path = self._find_alice_contract_master_file("NFO")

        if not file_path and broker_details:
            alice = get_alice_session(broker_details.broker_API_UID, broker_details.broker_API_KEY, proxy_config=self._proxy_config_for_broker(broker_details))
            if alice:
                fetch_instrument_data(alice, "NFO")
                file_path = self._find_alice_contract_master_file("NFO")

        matched_row = None
        if file_path and file_path.exists():
            with file_path.open(newline="", encoding="utf-8") as file_obj:
                reader = csv.DictReader(file_obj)
                for row in reader:
                    candidates = [row.get("Trading Symbol"), row.get("Symbol"), row.get("symbol")]
                    if any(self._normalize_symbol(candidate) == self._normalize_symbol(target_symbol) for candidate in candidates):
                        matched_row = row
                        break

        if not matched_row:
            raise MultiLegExecutionError(
                "Exact Alice Blue option contract could not be resolved.",
                error_code="CONTRACT_RESOLUTION_FAILED",
                metadata={"broker": "Alice Blue", "symbol": target_symbol},
            )

        return ResolvedContract(
            underlying=str(underlying or "").strip().upper(),
            expiry=expiry,
            strike_price=float(strike_price),
            option_type=str(option_type or "").strip().upper(),
            symbol=str(matched_row.get("Trading Symbol") or matched_row.get("Symbol") or target_symbol).strip(),
            token=str(matched_row.get("Token") or matched_row.get("token") or "").strip(),
            lot_size=self._safe_int(matched_row.get("Lot Size") or matched_row.get("lot_size") or 0),
            tick_size=self._safe_float(matched_row.get("Tick Size") or matched_row.get("tick_size") or 0.05) or 0.05,
            exchange="NFO",
        )

    def _resolve_upstox_option_contract(
        self,
        *,
        underlying: str,
        strike_price: float,
        option_type: str,
        expiry: datetime,
        exchange: str,
    ) -> ResolvedContract:
        instruments = load_upstox_instruments(self._map_upstox_exchange(exchange))
        normalized_underlying = str(underlying or "").strip().upper()
        normalized_option_type = str(option_type or "").strip().upper()
        expiry_date = expiry.date() if hasattr(expiry, "date") else expiry
        target_strike = float(strike_price)

        matched_instrument = None
        for instrument in instruments:
            if not self._upstox_matches_underlying(instrument, normalized_underlying):
                continue
            if not self._upstox_matches_option_type(instrument, normalized_option_type):
                continue
            if not self._upstox_matches_expiry(instrument, expiry_date):
                continue
            if not self._upstox_matches_strike(instrument, target_strike):
                continue
            matched_instrument = instrument
            break

        if not matched_instrument:
            raise MultiLegExecutionError(
                "Exact Upstox option contract could not be resolved.",
                error_code="CONTRACT_RESOLUTION_FAILED",
                metadata={
                    "broker": "Upstox",
                    "underlying": normalized_underlying,
                    "strike_price": strike_price,
                    "option_type": normalized_option_type,
                    "expiry": expiry.isoformat() if expiry else None,
                },
            )

        lot_size = self._safe_int(
            matched_instrument.get("lot_size")
            or matched_instrument.get("minimum_lot")
            or matched_instrument.get("minimum_lot_size")
            or matched_instrument.get("qty_multiplier")
            or 0
        )
        tick_size = self._safe_float(matched_instrument.get("tick_size") or matched_instrument.get("minimum_tick_size") or 0.05) or 0.05
        contract_expiry = self._parse_instrument_expiry(matched_instrument) or expiry

        return ResolvedContract(
            underlying=normalized_underlying,
            expiry=contract_expiry,
            strike_price=target_strike,
            option_type=normalized_option_type,
            symbol=str(matched_instrument.get("trading_symbol") or matched_instrument.get("symbol") or "").strip(),
            token=str(matched_instrument.get("instrument_key") or matched_instrument.get("instrument_token") or "").strip(),
            lot_size=lot_size,
            tick_size=tick_size,
            exchange="NFO",
        )

    def _fetch_upstox_ltp(self, broker_details: ClientBrokerdetails, contract: ResolvedContract) -> Optional[float]:
        access_token = self._get_broker_access_token(broker_details)
        if not access_token or not contract.token:
            return None

        try:
            proxy_config = self._proxy_config_for_broker(broker_details)
            response = requests.get(
                self.UPSTOX_MARKET_QUOTE_LTP_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"instrument_key": contract.token},
                timeout=5,
                proxies=proxy_config,
            )
            payload = response.json() if response.content else {}
            if response.status_code != 200:
                return None
            ltp = extract_ltp_from_quote_payload(payload, preferred_keys=(contract.token, contract.symbol))
            if ltp is not None:
                return cache_option_ltp(
                    contract.symbol,
                    ltp,
                    expiry_date=contract.expiry,
                    underlying=contract.underlying,
                    source="upstox",
                ) or float(ltp)
            return None
        except Exception:
            return None

    def _fetch_dhan_ltp(self, broker_details: ClientBrokerdetails, contract: ResolvedContract) -> Optional[float]:
        if dhanhq is None:
            return None
        client_id = broker_details.broker_API_UID or broker_details.broker_Demate_User_Name
        access_token = self._get_broker_access_token(broker_details)
        if not client_id or not access_token or not contract.token:
            return None
        try:
            proxy_config = self._proxy_config_for_broker(broker_details)
            dhan_client = dhanhq(client_id, access_token)
            if hasattr(dhan_client, "session"):
                dhan_client.session.proxies.update(proxy_config)
            if not hasattr(dhan_client, "get_ltp_data"):
                pass
            exchange_code = getattr(dhan_client, "NSE_FNO", "NSE_FNO")
            security_id_key = str(int(float(contract.token)))
            rest_response = requests.post(
                DHAN_LTP_URL,
                headers={
                    "Content-Type": "application/json",
                    "access-token": access_token,
                    "client-id": str(client_id),
                },
                json={exchange_code: [int(float(contract.token))]},
                timeout=5,
                proxies=proxy_config,
            )
            rest_payload = rest_response.json() if rest_response.content else {}
            ltp = extract_ltp_from_quote_payload(rest_payload, preferred_keys=(exchange_code, security_id_key, int(float(contract.token))))
            if ltp is None and hasattr(dhan_client, "get_ltp_data"):
                response = dhan_client.get_ltp_data({exchange_code: [int(float(contract.token))]})
                ltp = extract_ltp_from_quote_payload(response, preferred_keys=(exchange_code, security_id_key, int(float(contract.token))))
            if ltp is None:
                ltp = fetch_nse_option_chain_ltp(
                    contract.symbol,
                    expiry_date=contract.expiry,
                    underlying=contract.underlying,
                    proxy_config=proxy_config,
                    user=getattr(broker_details.client, "email", None),
                )
            return float(ltp) if ltp is not None else None
        except Exception:
            return None

    def _fetch_fyers_ltp(self, broker_details: ClientBrokerdetails, contract: ResolvedContract) -> Optional[float]:
        access_token = self._get_broker_access_token(broker_details)
        api_key = broker_details.broker_API_KEY
        if not access_token or not api_key or not contract.symbol:
            return None
        try:
            proxy_config = self._proxy_config_for_broker(broker_details)
            response = requests.get(
                "https://api-t1.fyers.in/data/quotes",
                headers={"Authorization": f"{api_key}:{access_token}", "Content-Type": "application/json"},
                params={"symbols": contract.symbol},
                timeout=5,
                proxies=proxy_config,
            )
            payload = response.json() if response.content else {}
            ltp = extract_ltp_from_quote_payload(payload, preferred_keys=(contract.symbol,))
            return float(ltp) if ltp is not None else None
        except Exception:
            return None

    def _fetch_fivepaisa_ltp(self, broker_details: ClientBrokerdetails, contract: ResolvedContract) -> Optional[float]:
        access_token = self._get_broker_access_token(broker_details)
        api_key = broker_details.broker_API_KEY
        if not access_token or not api_key or not contract.token:
            return None
        try:
            proxy_config = self._proxy_config_for_broker(broker_details)
            payload = {
                "head": {"key": api_key},
                "body": {
                    "MarketFeedData": [{"Exch": "N", "ExchType": "D", "ScripCode": int(float(contract.token))}],
                },
            }
            response = requests.post(
                MARKET_FEED_URL,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
                json=payload,
                timeout=5,
                proxies=proxy_config,
            )
            data = response.json() if response.content else {}
            ltp = extract_ltp_from_quote_payload(data, preferred_keys=(contract.token, contract.symbol))
            return float(ltp) if ltp is not None else None
        except Exception:
            return None

    def _fetch_zerodha_ltp(self, broker_details: ClientBrokerdetails, contract: ResolvedContract) -> Optional[float]:
        if KiteConnect is None:
            return None
        access_token = self._get_broker_access_token(broker_details)
        api_key = broker_details.broker_API_KEY
        if not access_token or not api_key or not contract.symbol:
            return None
        try:
            proxy_config = self._proxy_config_for_broker(broker_details)
            kite = KiteConnect(api_key=api_key, proxies=proxy_config)
            kite.set_access_token(access_token)
            quote_key = f"{contract.exchange}:{contract.symbol}"
            response = kite.ltp(quote_key)
            ltp = extract_ltp_from_quote_payload(response, preferred_keys=(quote_key, contract.symbol))
            if ltp is None:
                rest_response = requests.get(
                    KITE_LTP_URL,
                    headers={
                        "X-Kite-Version": "3",
                        "Authorization": f"token {api_key}:{access_token}",
                    },
                    params={"i": quote_key},
                    timeout=5,
                    proxies=proxy_config,
                )
                rest_payload = rest_response.json() if rest_response.content else {}
                ltp = extract_ltp_from_quote_payload(rest_payload, preferred_keys=(quote_key, contract.symbol))
            if ltp is None:
                ltp = fetch_nse_option_chain_ltp(
                    contract.symbol,
                    expiry_date=contract.expiry,
                    underlying=contract.underlying,
                    proxy_config=proxy_config,
                    user=getattr(broker_details.client, "email", None),
                )
            return float(ltp) if ltp is not None else None
        except Exception:
            return None

    def _fetch_alice_blue_ltp(self, broker_details: ClientBrokerdetails, contract: ResolvedContract) -> Optional[float]:
        try:
            alice = get_alice_session(broker_details.broker_API_UID, broker_details.broker_API_KEY, proxy_config=self._proxy_config_for_broker(broker_details))
            if not alice:
                return None
            instrument = alice.get_instrument_by_symbol(contract.exchange, contract.symbol)
            if not instrument:
                return None
            ltp = alice.get_scrip_info(instrument).get("Ltp", 0)
            return float(ltp) if ltp is not None else None
        except Exception:
            return None

    @staticmethod
    def _map_upstox_exchange(exchange: str) -> str:
        normalized_exchange = str(exchange or "").strip().upper()
        if normalized_exchange in {"NFO", "NSE_FO", "NSE"}:
            return "NSE"
        if normalized_exchange in {"BSE", "BSE_EQ", "BSE_FO"}:
            return "BSE"
        if normalized_exchange in {"MCX", "MCX_FO"}:
            return "MCX"
        return "NSE"

    @staticmethod
    def _parse_instrument_expiry(instrument: Dict[str, Any]) -> Optional[datetime]:
        raw_value = instrument.get("expiry") or instrument.get("expiry_date")
        if not raw_value:
            return None
        if isinstance(raw_value, (int, float)):
            try:
                timestamp = float(raw_value)
                if timestamp > 10_000_000_000:
                    timestamp = timestamp / 1000.0
                return datetime.fromtimestamp(timestamp)
            except (TypeError, ValueError, OSError):
                return None
        raw_str = str(raw_value).strip()
        if raw_str.isdigit():
            try:
                timestamp = float(raw_str)
                if timestamp > 10_000_000_000:
                    timestamp = timestamp / 1000.0
                return datetime.fromtimestamp(timestamp)
            except (TypeError, ValueError, OSError):
                return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(raw_str, fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def _upstox_matches_expiry(cls, instrument: Dict[str, Any], expiry_date) -> bool:
        instrument_expiry = cls._parse_instrument_expiry(instrument)
        return bool(instrument_expiry and instrument_expiry.date() == expiry_date)

    @staticmethod
    def _upstox_matches_underlying(instrument: Dict[str, Any], underlying: str) -> bool:
        candidates = [
            instrument.get("underlying_symbol"),
            instrument.get("underlying"),
            instrument.get("name"),
            instrument.get("trading_symbol"),
            instrument.get("symbol"),
        ]
        normalized_candidates = [str(item or "").replace(" ", "").replace("-", "").upper() for item in candidates]
        return any(candidate.startswith(underlying) or underlying in candidate for candidate in normalized_candidates)

    @staticmethod
    def _upstox_matches_option_type(instrument: Dict[str, Any], option_type: str) -> bool:
        raw_values = [
            instrument.get("option_type"),
            instrument.get("instrument_type"),
            instrument.get("trading_symbol"),
            instrument.get("symbol"),
        ]
        normalized_values = [str(item or "").upper() for item in raw_values]
        if option_type == "CE":
            return any("CE" in value or "CALL" in value for value in normalized_values)
        if option_type == "PE":
            return any("PE" in value or "PUT" in value for value in normalized_values)
        return False

    @classmethod
    def _upstox_matches_strike(cls, instrument: Dict[str, Any], strike_price: float) -> bool:
        candidate_values = [
            instrument.get("strike_price"),
            instrument.get("strike"),
            instrument.get("weekly_strike_price"),
        ]
        for value in candidate_values:
            parsed = cls._safe_float(value)
            if parsed is not None and abs(parsed - strike_price) < 0.01:
                return True
        return False

    @staticmethod
    def _normalize_symbol(value: Any) -> str:
        return str(value or "").replace(" ", "").replace("-", "").upper()

    @staticmethod
    def _normalize_date_str(value: Any) -> Optional[str]:
        if not value:
            return None
        raw_value = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(raw_value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @staticmethod
    def _build_trade_symbol_for_broker(broker_name: str, underlying: str, expiry: datetime, strike_price: float, option_type: str) -> str:
        normalized_broker = str(broker_name or "").strip().lower()
        normalized_underlying = str(underlying or "").strip().upper()
        normalized_option_type = str(option_type or "").strip().upper()
        strike_component = f"{float(strike_price):.2f}" if normalized_broker in {"5paisa", "5 paisa"} else str(int(float(strike_price)))
        day = expiry.strftime("%d")
        month = expiry.strftime("%b").upper()
        year_short = expiry.strftime("%y")
        year_full = expiry.strftime("%Y")

        if normalized_broker == "fyers":
            return f"{normalized_underlying}{year_short}{month}{day}{strike_component}{normalized_option_type}"
        if normalized_broker == "dhan":
            return f"{normalized_underlying}{month}{year_full}{strike_component}{normalized_option_type}"
        if normalized_broker in {"5paisa", "5 paisa"}:
            return f"{normalized_underlying}{day}{month}{year_full}{normalized_option_type}{strike_component}"
        if normalized_broker == "zerodha":
            return f"{normalized_underlying}{year_short}{month}{strike_component}{normalized_option_type}"
        if normalized_broker in {"alice blue", "aliceblue"}:
            return f"{normalized_underlying}{day}{month}{year_short}{normalized_option_type[:1]}{strike_component}"
        if normalized_broker == "upstox":
            return f"{normalized_underlying}{strike_component}{normalized_option_type}{day}{month}{year_short}"
        return f"{normalized_underlying}{day}{month}{year_full}{strike_component}{normalized_option_type}"

    @staticmethod
    def _get_broker_access_token(broker_details: ClientBrokerdetails) -> Optional[str]:
        secure_token_getter = getattr(broker_details, "get_access_token_secure", None)
        secure_token = secure_token_getter() if callable(secure_token_getter) else None
        return secure_token or broker_details.access_token

    @staticmethod
    def _ensure_fivepaisa_scrip_master(segment: str) -> Path:
        try:
            return ensure_fivepaisa_scrip_master_file(segment)
        except Exception as exc:
            raise MultiLegExecutionError(
                "5Paisa scrip master download failed and no valid cached copy is available.",
                error_code="CONTRACT_RESOLUTION_FAILED",
                metadata={"details": str(exc)},
            ) from exc

    @staticmethod
    def _find_alice_contract_master_file(exchange: str) -> Optional[Path]:
        filename = f"{str(exchange or 'NFO').strip().upper()}.csv"
        candidates = [
            Path.cwd() / filename,
            Path(__file__).resolve().parents[2] / filename,
            Path(__file__).resolve().parent.parent / filename,
        ]
        for path in candidates:
            if path.exists() and path.stat().st_size > 0:
                return path
        return None

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


class StrategyPlanBuilder:
    def __init__(self):
        self._resolver = MultiLegContractResolver()

    def build(self, config: Dict[str, Any], *, client: User, broker_details: ClientBrokerdetails) -> StrategyPlan:
        strategy_name = str(config.get("strategy_name") or "").strip().upper()
        if strategy_name not in SUPPORTED_STRATEGIES:
            raise MultiLegExecutionError(
                f"Unsupported multi-leg strategy '{strategy_name}'.",
                error_code="UNSUPPORTED_STRATEGY",
            )

        broker_name = str(config.get("broker") or getattr(getattr(broker_details, "broker_name", None), "broker_name", "") or "").strip()
        underlying = str(config.get("underlying") or "").strip().upper()
        order_type = str(config.get("order_type") or "LIMIT").strip().upper()
        product_type = str(config.get("product_type") or "INTRADAY").strip().upper()
        quantity_lots = int(config.get("quantity_lots") or 0)
        if quantity_lots <= 0:
            raise MultiLegExecutionError("quantity_lots must be greater than zero.", error_code="INVALID_LOTS")

        expiry = self._resolver.resolve_expiry(underlying, config.get("expiry"))
        legs = self._build_legs(
            strategy_name=strategy_name,
            config=config,
            broker_name=broker_name,
            underlying=underlying,
            expiry=expiry,
            quantity_lots=quantity_lots,
            order_type=order_type,
            product_type=product_type,
            broker_details=broker_details,
        )

        idempotency_source = str(
            config.get("idempotency_key")
            or self._build_plan_fingerprint(
                strategy_name=strategy_name,
                client_id=client.id,
                broker_name=broker_name,
                underlying=underlying,
                expiry=expiry,
                quantity_lots=quantity_lots,
                config=config,
                legs=legs,
            )
        )
        idempotency_key = hashlib.sha256(idempotency_source.encode()).hexdigest()[:32]

        return StrategyPlan(
            strategy_name=strategy_name,
            client_id=client.id,
            broker=broker_name,
            underlying=underlying,
            expiry=expiry,
            quantity_lots=quantity_lots,
            order_type=order_type,
            product_type=product_type,
            buffer_percentage=self._to_float(config.get("buffer_percentage")),
            sell_leg_stop_loss_percentage=self._to_float(config.get("sell_leg_stop_loss_percentage")),
            combined_trailing_start=self._to_float(config.get("combined_trailing_start")),
            combined_trailing_gap=self._to_float(config.get("combined_trailing_gap")),
            entry_time=str(config.get("entry_time") or "").strip() or None,
            exit_time=str(config.get("exit_time") or "").strip() or None,
            allow_reentry=bool(config.get("allow_reentry", False)),
            idempotency_key=idempotency_key,
            legs=legs,
            raw_config=dict(config),
        )

    def _build_legs(
        self,
        *,
        strategy_name: str,
        config: Dict[str, Any],
        broker_name: str,
        underlying: str,
        expiry: datetime,
        quantity_lots: int,
        order_type: str,
        product_type: str,
        broker_details: ClientBrokerdetails,
    ) -> List[StrategyLegPlan]:
        spread_definitions = {
            "BULL_CALL_SPREAD": [
                ("BUY_LOWER_CALL", "BUY", "CE", "lower"),
                ("SELL_HIGHER_CALL", "SELL", "CE", "higher"),
            ],
            "BEAR_CALL_SPREAD": [
                ("SELL_LOWER_CALL", "SELL", "CE", "lower"),
                ("BUY_HIGHER_CALL", "BUY", "CE", "higher"),
            ],
            "BEAR_PUT_SPREAD": [
                ("SELL_LOWER_PUT", "SELL", "PE", "lower"),
                ("BUY_HIGHER_PUT", "BUY", "PE", "higher"),
            ],
        }

        if strategy_name in spread_definitions:
            lower_strike = self._required_float(config.get("lower_strike"), field_name="lower_strike")
            higher_strike = self._required_float(config.get("higher_strike"), field_name="higher_strike")
            if lower_strike >= higher_strike:
                raise MultiLegExecutionError(
                    "Spread strategies require lower_strike to be less than higher_strike.",
                    error_code="INVALID_STRIKE_CONFIGURATION",
                )

            raw_legs = []
            for leg_name, transaction_type, option_type, strike_key in spread_definitions[strategy_name]:
                raw_legs.append({
                    "leg_name": leg_name,
                    "transaction_type": transaction_type,
                    "option_type": option_type,
                    "strike": lower_strike if strike_key == "lower" else higher_strike,
                    "ratio": 1,
                })
            return self._build_custom_leg_plans(
                raw_legs=raw_legs,
                broker_name=broker_name,
                underlying=underlying,
                expiry=expiry,
                quantity_lots=quantity_lots,
                order_type=order_type,
                product_type=product_type,
                broker_details=broker_details,
            )

        if strategy_name == "SHORT_STRADDLE":
            template_legs = config.get("legs") or []
            if template_legs:
                return self._build_custom_leg_plans(
                    raw_legs=template_legs,
                    broker_name=broker_name,
                    underlying=underlying,
                    expiry=expiry,
                    quantity_lots=quantity_lots,
                    order_type=order_type,
                    product_type=product_type,
                    broker_details=broker_details,
                )
            atm_strike = self._required_float(config.get("lower_strike"), field_name="lower_strike")
            return self._build_custom_leg_plans(
                raw_legs=[
                    {"leg_name": "SELL_CALL", "transaction_type": "SELL", "option_type": "CE", "strike": atm_strike, "ratio": 1},
                    {"leg_name": "SELL_PUT", "transaction_type": "SELL", "option_type": "PE", "strike": atm_strike, "ratio": 1},
                ],
                broker_name=broker_name,
                underlying=underlying,
                expiry=expiry,
                quantity_lots=quantity_lots,
                order_type=order_type,
                product_type=product_type,
                broker_details=broker_details,
            )

        if strategy_name == "CUSTOM_BASKET":
            raw_legs = config.get("legs") or []
            if not isinstance(raw_legs, list) or not raw_legs:
                raise MultiLegExecutionError("Custom basket requires at least one leg.", error_code="MISSING_CUSTOM_LEGS")
            return self._build_custom_leg_plans(
                raw_legs=raw_legs,
                broker_name=broker_name,
                underlying=underlying,
                expiry=expiry,
                quantity_lots=quantity_lots,
                order_type=order_type,
                product_type=product_type,
                broker_details=broker_details,
            )

        template_legs = config.get("legs") or []
        if template_legs:
            return self._build_custom_leg_plans(
                raw_legs=template_legs,
                broker_name=broker_name,
                underlying=underlying,
                expiry=expiry,
                quantity_lots=quantity_lots,
                order_type=order_type,
                product_type=product_type,
                broker_details=broker_details,
            )

        raise MultiLegExecutionError(
            f"{strategy_name} requires configured legs before execution.",
            error_code="MISSING_CONFIGURED_LEGS",
        )

    def _build_custom_leg_plans(
        self,
        *,
        raw_legs: List[Dict[str, Any]],
        broker_name: str,
        underlying: str,
        expiry: datetime,
        quantity_lots: int,
        order_type: str,
        product_type: str,
        broker_details: ClientBrokerdetails,
    ) -> List[StrategyLegPlan]:
        planned_legs: List[StrategyLegPlan] = []
        base_lot_size = None
        for index, raw_leg in enumerate(raw_legs, start=1):
            strike_price = self._required_float(raw_leg.get("strike"), field_name=f"legs[{index}].strike")
            option_type = str(raw_leg.get("option_type") or "").strip().upper()
            transaction_type = str(raw_leg.get("transaction_type") or raw_leg.get("action") or "").strip().upper()
            ratio = int(raw_leg.get("ratio") or 1)
            if option_type not in {"CE", "PE"}:
                raise MultiLegExecutionError(
                    f"legs[{index}].option_type must be CE or PE.",
                    error_code="INVALID_CUSTOM_LEG",
                )
            if transaction_type not in {"BUY", "SELL"}:
                raise MultiLegExecutionError(
                    f"legs[{index}].transaction_type must be BUY or SELL.",
                    error_code="INVALID_CUSTOM_LEG",
                )
            if ratio <= 0:
                raise MultiLegExecutionError(
                    f"legs[{index}].ratio must be greater than zero.",
                    error_code="INVALID_CUSTOM_LEG",
                )
            contract = self._resolver.resolve_option_contract(
                broker_name=broker_name,
                underlying=underlying,
                strike_price=strike_price,
                option_type=option_type,
                expiry=expiry,
                broker_details=broker_details,
            )
            if base_lot_size is None:
                base_lot_size = contract.lot_size
            elif base_lot_size != contract.lot_size:
                raise MultiLegExecutionError("All strategy legs must share the same lot size.", error_code="LOT_SIZE_MISMATCH")
            planned_legs.append(
                StrategyLegPlan(
                    leg_name=str(raw_leg.get("leg_name") or f"LEG_{index}"),
                    transaction_type=transaction_type,
                    option_type=option_type,
                    strike_price=strike_price,
                    quantity=quantity_lots * contract.lot_size * ratio,
                    order_type=order_type,
                    product_type=product_type,
                    limit_price=None,
                    contract=contract,
                )
            )
        return planned_legs

    @staticmethod
    def _required_float(value: Any, *, field_name: str) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            raise MultiLegExecutionError(f"{field_name} is required and must be numeric.", error_code="INVALID_FIELD")
        return parsed

    @staticmethod
    def _build_plan_fingerprint(
        *,
        strategy_name: str,
        client_id: int,
        broker_name: str,
        underlying: str,
        expiry: datetime,
        quantity_lots: int,
        config: Dict[str, Any],
        legs: List[StrategyLegPlan],
    ) -> str:
        leg_fingerprint = "|".join(
            f"{leg.leg_name}:{leg.transaction_type}:{leg.option_type}:{leg.strike_price}:{leg.quantity}:{leg.contract.symbol}"
            for leg in legs
        )
        return "|".join(
            [
                strategy_name,
                str(client_id),
                normalize_broker_name(broker_name),
                underlying,
                expiry.strftime("%Y-%m-%d"),
                str(config.get("lower_strike") or ""),
                str(config.get("higher_strike") or ""),
                str(quantity_lots),
                leg_fingerprint,
            ]
        )

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class MultiLegRiskManager:
    DEFAULT_MAX_OPEN_STRATEGIES = 5
    DEFAULT_MAX_TOTAL_QUANTITY = 1800

    def __init__(self):
        self._auth_service = AuthService()

    def validate(self, plan: StrategyPlan, *, client: User, broker_details: ClientBrokerdetails) -> None:
        if not client.is_active or not client.client_status or not client.is_enable:
            raise MultiLegExecutionError("Client is inactive for trading.", error_code="CLIENT_INACTIVE")

        if client.end_date_client and client.end_date_client < timezone.localdate():
            raise MultiLegExecutionError("Client service has expired.", error_code="CLIENT_SERVICE_EXPIRED")

        current_time = datetime.now(ZoneInfo(TIMEZONE))
        market_open = current_time.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
        market_close = current_time.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
        if current_time < market_open or current_time >= market_close:
            raise MultiLegExecutionError("Multi-leg execution is allowed only during market hours.", error_code="MARKET_CLOSED")

        if plan.entry_time:
            entry_window = self._parse_time(plan.entry_time)
            if current_time.time() < entry_window:
                raise MultiLegExecutionError("Strategy entry time has not opened yet.", error_code="ENTRY_TIME_NOT_REACHED")

        if plan.exit_time:
            exit_window = self._parse_time(plan.exit_time)
            if current_time.time() >= exit_window:
                raise MultiLegExecutionError("Strategy exit time has already passed.", error_code="EXIT_TIME_PASSED")

        self._validate_broker_session(plan, broker_details)

        active_count = StrategyExecution.objects.filter(client=client, status__in=ACTIVE_STRATEGY_STATUSES).count()
        if active_count >= self.DEFAULT_MAX_OPEN_STRATEGIES:
            raise MultiLegExecutionError(
                "Maximum active multi-leg strategies reached for this client.",
                error_code="MAX_OPEN_STRATEGIES_REACHED",
            )

        if plan.total_quantity > self.DEFAULT_MAX_TOTAL_QUANTITY:
            raise MultiLegExecutionError(
                "Combined strategy quantity exceeds allowed limit.",
                error_code="MAX_STRATEGY_QUANTITY_EXCEEDED",
            )

        self._validate_no_reentry(plan, client)
        self._validate_margin(plan, broker_details)

    def _validate_no_reentry(self, plan: StrategyPlan, client: User) -> None:
        if plan.allow_reentry:
            return

        previous_execution = StrategyExecution.objects.filter(
            client=client,
            strategy_name=plan.strategy_name,
            underlying=plan.underlying,
            expiry=plan.expiry,
        ).exclude(status=StrategyExecution.STATUS_FAILED).first()
        if previous_execution:
            raise MultiLegExecutionError(
                "Re-entry is disabled for this multi-leg strategy configuration.",
                error_code="REENTRY_DISABLED",
                metadata={"strategy_execution_id": previous_execution.id},
            )

    def _validate_margin(self, plan: StrategyPlan, broker_details: ClientBrokerdetails) -> None:
        broker_name = str(plan.broker or "").strip().lower()
        if broker_name not in {"angel one", "angle one"}:
            return

        margin_response = get_angel_one_margin(broker_details)
        if margin_response.get("status") != "success":
            return

        payload = margin_response.get("data") or margin_response.get("margin") or margin_response
        candidate_values = []
        if isinstance(payload, dict):
            for key in ("availablecash", "availableCash", "available_margin", "net", "cash"):
                value = payload.get(key)
                if value not in (None, "", "None"):
                    candidate_values.append(value)
        available_margin = None
        for value in candidate_values:
            try:
                available_margin = float(value)
                break
            except (TypeError, ValueError):
                continue

        if available_margin is not None and available_margin <= 0:
            raise MultiLegExecutionError(
                "Broker margin is unavailable for strategy execution.",
                error_code="INSUFFICIENT_MARGIN",
            )

    @staticmethod
    def _parse_time(value: str):
        return datetime.strptime(value, "%H:%M").time()

    def _validate_broker_session(self, plan: StrategyPlan, broker_details: ClientBrokerdetails) -> None:
        broker_name = str(plan.broker or "").strip().lower()

        if broker_name in {"angel one", "angle one"}:
            session_result = self._auth_service.ensure_valid_session(
                client_id=broker_details.broker_Demate_User_Name or broker_details.broker_API_UID,
                api_key=broker_details.broker_API_KEY,
                broker_details=broker_details,
                proxy_config=build_requests_proxy_config(broker_details.execution_node),
            )
            if session_result.get("status") != "success":
                raise MultiLegExecutionError(
                    session_result.get("message", "Broker session is invalid."),
                    error_code="INVALID_BROKER_SESSION",
                )
            return

        required_fields = {
            "fyers": ("broker_API_KEY",),
            "dhan": (),
            "5paisa": ("broker_API_KEY",),
            "5 paisa": ("broker_API_KEY",),
            "zerodha": ("broker_API_KEY",),
            "upstox": (),
            "alice blue": ("broker_API_KEY", "broker_API_UID"),
            "aliceblue": ("broker_API_KEY", "broker_API_UID"),
        }.get(broker_name, ())

        missing = [field for field in required_fields if not getattr(broker_details, field, None)]
        if broker_name == "dhan" and not (broker_details.broker_API_UID or broker_details.broker_Demate_User_Name):
            missing.append("broker_API_UID")
        if missing:
            raise MultiLegExecutionError(
                f"Broker credentials are incomplete for {plan.broker}. Missing: {', '.join(missing)}.",
                error_code="MISSING_CREDENTIALS",
            )

        if broker_name not in {"alice blue", "aliceblue"}:
            access_token = self._get_broker_access_token(broker_details)
            if not access_token:
                raise MultiLegExecutionError(
                    f"Access token not found for this {plan.broker} client.",
                    error_code="MISSING_ACCESS_TOKEN",
                )

            expiry = getattr(broker_details, "access_token_expiry", None)
            if expiry and timezone.is_naive(expiry):
                expiry = timezone.make_aware(expiry)
            if expiry and expiry <= timezone.now():
                raise MultiLegExecutionError(
                    f"{plan.broker} access token has expired. Please login again.",
                    error_code="ACCESS_TOKEN_EXPIRED",
                )

    @staticmethod
    def _get_broker_access_token(broker_details: ClientBrokerdetails) -> Optional[str]:
        secure_token_getter = getattr(broker_details, "get_access_token_secure", None)
        secure_token = secure_token_getter() if callable(secure_token_getter) else None
        return secure_token or broker_details.access_token


class StrategyPositionTracker:
    def create_execution(self, *, client: User, plan: StrategyPlan) -> StrategyExecution:
        try:
            return StrategyExecution.objects.create(
                client=client,
                broker=plan.broker,
                strategy_name=plan.strategy_name,
                underlying=plan.underlying,
                expiry=plan.expiry,
                status=StrategyExecution.STATUS_EXECUTING,
                total_quantity=plan.total_quantity,
                idempotency_key=plan.idempotency_key,
                config_snapshot=plan.raw_config,
            )
        except IntegrityError as exc:
            existing = StrategyExecution.objects.filter(idempotency_key=plan.idempotency_key).first()
            raise MultiLegExecutionError(
                "Duplicate multi-leg execution request blocked by idempotency key.",
                error_code="DUPLICATE_IDEMPOTENCY_KEY",
                metadata={"strategy_execution_id": existing.id if existing else None},
            ) from exc

    def create_leg(self, *, execution: StrategyExecution, leg_plan: StrategyLegPlan) -> StrategyLeg:
        return StrategyLeg.objects.create(
            strategy_execution=execution,
            leg_name=leg_plan.leg_name,
            transaction_type=leg_plan.transaction_type,
            option_type=leg_plan.option_type,
            strike_price=Decimal(str(leg_plan.strike_price)),
            symbol=leg_plan.contract.symbol,
            token=leg_plan.contract.token,
            lot_size=leg_plan.contract.lot_size,
            quantity=leg_plan.quantity,
            order_type=leg_plan.order_type,
            limit_price=Decimal(str(leg_plan.limit_price)) if leg_plan.limit_price is not None else None,
            exchange=leg_plan.contract.exchange,
            status=StrategyLeg.STATUS_PLANNED,
        )

    def update_leg_after_entry(self, leg: StrategyLeg, response: Dict[str, Any]) -> StrategyLeg:
        data = _extract_response_data(response)
        leg.broker_order_id = str(data.get("order_id") or "") or None
        leg.entry_price = self._to_decimal(data.get("executed_price") or data.get("reference_price") or data.get("ltp"))
        leg.status = StrategyLeg.STATUS_ACTIVE
        leg.order_response = response
        leg.save(update_fields=["broker_order_id", "entry_price", "status", "order_response", "updated_at"])
        return leg

    def update_leg_after_exit(self, leg: StrategyLeg, response: Dict[str, Any]) -> StrategyLeg:
        data = _extract_response_data(response)
        leg.exit_price = self._to_decimal(data.get("executed_price") or data.get("reference_price") or data.get("ltp"))
        leg.status = StrategyLeg.STATUS_EXITED
        leg.order_response = {**(leg.order_response or {}), "exit": response}
        leg.save(update_fields=["exit_price", "status", "order_response", "updated_at"])
        return leg

    def mark_leg_failed(self, leg: StrategyLeg, response: Optional[Dict[str, Any]] = None, *, rolled_back: bool = False) -> StrategyLeg:
        leg.status = StrategyLeg.STATUS_ROLLED_BACK if rolled_back else StrategyLeg.STATUS_FAILED
        if response is not None:
            leg.order_response = {**(leg.order_response or {}), "failure": response}
        leg.save(update_fields=["status", "order_response", "updated_at"])
        return leg

    def update_strategy_status(
        self,
        execution: StrategyExecution,
        *,
        status: str,
        exit_reason: Optional[str] = None,
        entry_time: Optional[datetime] = None,
        exit_time: Optional[datetime] = None,
    ) -> StrategyExecution:
        execution.status = status
        if exit_reason is not None:
            execution.exit_reason = exit_reason
        if entry_time is not None:
            execution.entry_time = entry_time
        if exit_time is not None:
            execution.exit_time = exit_time
        execution.save(update_fields=["status", "exit_reason", "entry_time", "exit_time", "updated_at"])
        return execution

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        if value in (None, "", "None"):
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None


class LegExecutionManager:
    def __init__(self):
        self._execution_engine = get_execution_engine()
        self._rate_limiter = MultiLegRateLimiter()

    def execute_leg(
        self,
        *,
        client: User,
        broker_details: ClientBrokerdetails,
        plan: StrategyPlan,
        execution: StrategyExecution,
        leg_plan: StrategyLegPlan,
        action: Optional[str] = None,
        history_id_suffix: str = "entry",
    ) -> Dict[str, Any]:
        self._rate_limiter.wait_for_slot(client.id, plan.broker)
        transaction_type = str(action or leg_plan.transaction_type).upper()
        request = self._build_execution_request(
            client=client,
            broker_details=broker_details,
            plan=plan,
            execution=execution,
            leg_plan=leg_plan,
            transaction_type=transaction_type,
            history_id_suffix=history_id_suffix,
        )
        return self._execution_engine.execute_order(request)

    def _build_execution_request(
        self,
        *,
        client: User,
        broker_details: ClientBrokerdetails,
        plan: StrategyPlan,
        execution: StrategyExecution,
        leg_plan: StrategyLegPlan,
        transaction_type: str,
        history_id_suffix: str,
    ) -> ExecutionRequest:
        expiry = leg_plan.contract.expiry
        if timezone.is_naive(expiry):
            expiry = timezone.make_aware(expiry, timezone.get_current_timezone())
        pseudo_trade = SimpleNamespace(
            client=client,
            broker=plan.broker,
            quantity=leg_plan.quantity,
            trade_limit=plan.raw_config.get("max_open_strategies_per_client") or 10,
            max_order_value=plan.raw_config.get("max_order_value"),
            sl_type=None,
            stop_loss=None,
            target=None,
        )
        request_id = f"ml-{execution.id}-{leg_plan.leg_name.lower()}-{history_id_suffix}-{uuid.uuid4().hex[:8]}"
        order_action = str(history_id_suffix or "").split("-", 1)[0].lower() or "entry"
        order_params = {
            "multi_leg_strategy_execution_id": execution.id,
            "multi_leg_leg_name": leg_plan.leg_name,
            "multi_leg_order_action": order_action,
            "buffer_percentage": plan.buffer_percentage,
            "strategy_name": plan.strategy_name,
            "idempotency_key": f"ml:{execution.id}:{leg_plan.leg_name}:{order_action}:{transaction_type}",
            "request_id": request_id,
        }
        if leg_plan.limit_price is not None:
            order_params["price"] = leg_plan.limit_price

        return ExecutionRequest(
            LivePrice=None,
            group_service=plan.raw_config.get("group_service"),
            trade=pseudo_trade,
            user=client,
            transaction_type=transaction_type,
            symbol=plan.underlying,
            quantity=leg_plan.quantity,
            strategy=plan.strategy_name,
            ordertype=leg_plan.order_type,
            product_type=leg_plan.product_type,
            price=leg_plan.limit_price,
            Lots=plan.quantity_lots,
            trade_order_status="MULTI_LEG",
            Entry_type=None,
            Exit_type=None,
            Entry_price=None,
            Exit_price=None,
            EntryQty=leg_plan.quantity if transaction_type == "BUY" else None,
            ExitQty=leg_plan.quantity if transaction_type == "SELL" else None,
            webhook_signal={"source": "multi_leg_strategy"},
            Exchange=leg_plan.contract.exchange,
            Segment="OPTION",
            Index_Symbol=leg_plan.contract.symbol,
            triggerPrice=None,
            day=expiry.strftime("%d"),
            month=expiry.strftime("%b").upper(),
            year=expiry.strftime("%y"),
            fullyear=expiry.strftime("%Y"),
            strike=leg_plan.strike_price,
            option_type=leg_plan.option_type,
            order_params=order_params,
            history_id=f"{execution.id}-{leg_plan.leg_name}-{history_id_suffix}",
            contract_info=ContractInfo(
                symbol=plan.underlying,
                strike=leg_plan.strike_price,
                option_type=leg_plan.option_type,
                exchange=leg_plan.contract.exchange,
                expiry=expiry,
                tradingsymbol=leg_plan.contract.symbol,
                symboltoken=leg_plan.contract.token,
            ),
            order_config=OrderConfig(
                order_type=leg_plan.order_type,
                product_type=leg_plan.product_type,
                price=leg_plan.limit_price,
                trigger_price=None,
                lots=plan.quantity_lots,
            ),
        )


class ExecutionRollbackManager:
    def __init__(self, leg_execution_manager: LegExecutionManager, tracker: StrategyPositionTracker):
        self._leg_execution_manager = leg_execution_manager
        self._tracker = tracker

    def rollback_completed_legs(
        self,
        *,
        execution: StrategyExecution,
        plan: StrategyPlan,
        client: User,
        broker_details: ClientBrokerdetails,
        completed_legs: List[StrategyLeg],
    ) -> None:
        for leg in reversed(completed_legs):
            exit_side = "SELL" if leg.transaction_type == "BUY" else "BUY"
            leg_plan = StrategyLegPlan(
                leg_name=leg.leg_name,
                transaction_type=leg.transaction_type,
                option_type=leg.option_type,
                strike_price=float(leg.strike_price),
                quantity=leg.quantity,
                order_type=leg.order_type or plan.order_type,
                product_type=plan.product_type,
                limit_price=float(leg.limit_price) if leg.limit_price is not None else None,
                contract=ResolvedContract(
                    underlying=plan.underlying,
                    expiry=plan.expiry,
                    strike_price=float(leg.strike_price),
                    option_type=leg.option_type,
                    symbol=leg.symbol,
                    token=leg.token or "",
                    lot_size=leg.lot_size,
                    tick_size=0.05,
                    exchange=leg.exchange,
                ),
            )
            response = self._leg_execution_manager.execute_leg(
                client=client,
                broker_details=broker_details,
                plan=plan,
                execution=execution,
                leg_plan=leg_plan,
                action=exit_side,
                history_id_suffix="rollback",
            )
            response_data = _extract_response_data(response)
            if str(response_data.get("status", "")).lower() not in {"complete", "completed", "open"}:
                raise MultiLegExecutionError(
                    "Rollback failed; immediate manual intervention required to avoid naked exposure.",
                    error_code="ROLLBACK_FAILED",
                    metadata={"leg_name": leg.leg_name, "response": response},
                )
            self._tracker.mark_leg_failed(leg, response=response, rolled_back=True)


class PnLMonitor:
    def __init__(self):
        self._resolver = MultiLegContractResolver()

    def refresh(self, execution: StrategyExecution, *, broker_details: ClientBrokerdetails) -> Dict[str, Any]:
        combined_pnl = Decimal("0")
        max_seen = Decimal(str(execution.max_pnl_seen or 0))
        sell_leg_triggered = False
        trigger_reason = None
        leg_summaries = []

        for leg in execution.legs.filter(status__in=ACTIVE_LEG_STATUSES):
            ltp = self._resolver.fetch_ltp(
                broker_details,
                ResolvedContract(
                    underlying=execution.underlying,
                    expiry=execution.expiry if execution.expiry else timezone.now(),
                    strike_price=float(leg.strike_price),
                    option_type=leg.option_type,
                    symbol=leg.symbol,
                    token=leg.token or "",
                    lot_size=leg.lot_size,
                    tick_size=0.05,
                    exchange=leg.exchange,
                ),
            )
            leg_pnl = self._calculate_leg_pnl(leg, ltp)
            leg.pnl = leg_pnl
            leg.save(update_fields=["pnl", "updated_at"])
            combined_pnl += leg_pnl
            leg_summaries.append({"leg_name": leg.leg_name, "ltp": ltp, "pnl": float(leg_pnl)})

            sell_leg_stop_loss_percentage = self._to_float(execution.config_snapshot.get("sell_leg_stop_loss_percentage"))
            if leg.transaction_type == "SELL" and sell_leg_stop_loss_percentage and leg.entry_price and ltp:
                threshold = float(leg.entry_price) * (1 + sell_leg_stop_loss_percentage / 100.0)
                if float(ltp) >= threshold:
                    sell_leg_triggered = True
                    trigger_reason = f"Sell leg stop loss triggered on {leg.leg_name}"

        execution.combined_pnl = combined_pnl
        if combined_pnl > max_seen:
            max_seen = combined_pnl
        execution.max_pnl_seen = max_seen

        trailing_start = self._to_float(execution.config_snapshot.get("combined_trailing_start"))
        trailing_gap = self._to_float(execution.config_snapshot.get("combined_trailing_gap"))
        if trailing_start is not None and trailing_gap is not None and float(combined_pnl) >= trailing_start:
            trailing_level = max(float(max_seen) - trailing_gap, 0)
            execution.trailing_stop_level = Decimal(str(round(trailing_level, 2)))
            if float(combined_pnl) <= trailing_level:
                trigger_reason = trigger_reason or "Combined trailing P&L stop triggered"
        execution.save(update_fields=["combined_pnl", "max_pnl_seen", "trailing_stop_level", "updated_at"])

        if not trigger_reason and execution.config_snapshot.get("exit_time"):
            exit_time = datetime.strptime(execution.config_snapshot["exit_time"], "%H:%M").time()
            if datetime.now(ZoneInfo(TIMEZONE)).time() >= exit_time:
                trigger_reason = "Configured time exit triggered"

        return {
            "combined_pnl": float(combined_pnl),
            "legs": leg_summaries,
            "trigger_exit": bool(trigger_reason or sell_leg_triggered),
            "trigger_reason": trigger_reason,
        }

    @staticmethod
    def _calculate_leg_pnl(leg: StrategyLeg, ltp: Optional[float]) -> Decimal:
        if ltp is None or leg.entry_price is None or not leg.quantity:
            return Decimal("0")
        current = Decimal(str(ltp))
        entry = Decimal(str(leg.entry_price))
        qty = Decimal(str(leg.quantity))
        if leg.transaction_type == "BUY":
            return (current - entry) * qty
        return (entry - current) * qty

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class ExitManager:
    def __init__(self, leg_execution_manager: LegExecutionManager, tracker: StrategyPositionTracker):
        self._leg_execution_manager = leg_execution_manager
        self._tracker = tracker

    def exit_strategy(
        self,
        execution: StrategyExecution,
        *,
        broker_details: ClientBrokerdetails,
        reason: str,
    ) -> StrategyExecution:
        if execution.status in {StrategyExecution.STATUS_EXITED, StrategyExecution.STATUS_FAILED, StrategyExecution.STATUS_ROLLED_BACK}:
            return execution

        plan = StrategyPlan(
            strategy_name=execution.strategy_name,
            client_id=execution.client_id,
            broker=execution.broker,
            underlying=execution.underlying,
            expiry=execution.expiry or timezone.now(),
            quantity_lots=1,
            order_type=str(execution.config_snapshot.get("order_type") or "LIMIT").upper(),
            product_type=str(execution.config_snapshot.get("product_type") or "INTRADAY").upper(),
            buffer_percentage=self._to_float(execution.config_snapshot.get("buffer_percentage")),
            sell_leg_stop_loss_percentage=self._to_float(execution.config_snapshot.get("sell_leg_stop_loss_percentage")),
            combined_trailing_start=self._to_float(execution.config_snapshot.get("combined_trailing_start")),
            combined_trailing_gap=self._to_float(execution.config_snapshot.get("combined_trailing_gap")),
            entry_time=execution.config_snapshot.get("entry_time"),
            exit_time=execution.config_snapshot.get("exit_time"),
            allow_reentry=bool(execution.config_snapshot.get("allow_reentry", False)),
            idempotency_key=execution.idempotency_key or uuid.uuid4().hex,
            legs=[],
            raw_config=execution.config_snapshot or {},
        )

        self._tracker.update_strategy_status(execution, status=StrategyExecution.STATUS_EXITING, exit_reason=reason)
        for leg in execution.legs.filter(status__in=ACTIVE_LEG_STATUSES):
            leg_plan = StrategyLegPlan(
                leg_name=leg.leg_name,
                transaction_type=leg.transaction_type,
                option_type=leg.option_type,
                strike_price=float(leg.strike_price),
                quantity=leg.quantity,
                order_type=leg.order_type or plan.order_type,
                product_type=plan.product_type,
                limit_price=float(leg.limit_price) if leg.limit_price is not None else None,
                contract=ResolvedContract(
                    underlying=execution.underlying,
                    expiry=execution.expiry or timezone.now(),
                    strike_price=float(leg.strike_price),
                    option_type=leg.option_type,
                    symbol=leg.symbol,
                    token=leg.token or "",
                    lot_size=leg.lot_size,
                    tick_size=0.05,
                    exchange=leg.exchange,
                ),
            )
            exit_side = "SELL" if leg.transaction_type == "BUY" else "BUY"
            response = self._leg_execution_manager.execute_leg(
                client=execution.client,
                broker_details=broker_details,
                plan=plan,
                execution=execution,
                leg_plan=leg_plan,
                action=exit_side,
                history_id_suffix="exit",
            )
            response_data = _extract_response_data(response)
            if str(response_data.get("status", "")).lower() not in {"complete", "completed", "open"}:
                raise MultiLegExecutionError(
                    "Strategy exit failed for one or more legs.",
                    error_code="STRATEGY_EXIT_FAILED",
                    metadata={"leg_name": leg.leg_name, "response": response},
                )
            self._tracker.update_leg_after_exit(leg, response)

        self._tracker.update_strategy_status(
            execution,
            status=StrategyExecution.STATUS_EXITED,
            exit_reason=reason,
            exit_time=timezone.now(),
        )
        return execution

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class MultiLegExecutionEngine:
    def __init__(self):
        self._plan_builder = StrategyPlanBuilder()
        self._risk_manager = MultiLegRiskManager()
        self._tracker = StrategyPositionTracker()
        self._leg_execution_manager = LegExecutionManager()
        self._rollback_manager = ExecutionRollbackManager(self._leg_execution_manager, self._tracker)
        self._pnl_monitor = PnLMonitor()
        self._exit_manager = ExitManager(self._leg_execution_manager, self._tracker)
        self._auth_service = AuthService()
        self._lock_manager = MultiLegLockManager()

    def execute(self, *, config: Dict[str, Any], user: User) -> Dict[str, Any]:
        client = self._resolve_client(config, user)
        config = self._merge_assigned_strategy_defaults(client=client, config=config)
        broker_details = self._resolve_broker_details(client, config.get("broker"))
        self._assert_execution_route_ready(client=client, broker_details=broker_details)
        plan = self._plan_builder.build(config, client=client, broker_details=broker_details)
        self._assert_strategy_allowed_for_client(client=client, plan=plan)
        existing_execution = StrategyExecution.objects.filter(idempotency_key=plan.idempotency_key).select_related("client").prefetch_related("legs").first()
        if existing_execution:
            self._assert_access(existing_execution, user)
            return self._serialize_execution(existing_execution, refresh_pnl=False)
        lock_key = f"{client.id}:{plan.strategy_name}:{plan.underlying}:{plan.expiry.strftime('%Y%m%d')}"
        if not self._lock_manager.acquire(lock_key):
            raise MultiLegExecutionError(
                "A multi-leg execution is already in progress for this client and strategy.",
                error_code="EXECUTION_LOCKED",
            )

        try:
            self._risk_manager.validate(plan, client=client, broker_details=broker_details)
            execution = self._tracker.create_execution(client=client, plan=plan)
            self._log(
                execution,
                "EXECUTION_STARTED",
                "Multi-leg strategy execution started.",
                {
                    "strategy_name": plan.strategy_name,
                    "underlying": plan.underlying,
                    "expiry": plan.expiry.isoformat() if plan.expiry else None,
                    "order_type": plan.order_type,
                },
            )

            completed_legs: List[StrategyLeg] = []
            for leg_plan in plan.legs:
                leg = self._tracker.create_leg(execution=execution, leg_plan=leg_plan)
                self._log(
                    execution,
                    "LEG_PLANNED",
                    f"Leg {leg_plan.leg_name} planned.",
                    {"symbol": leg.symbol, "quantity": leg.quantity, "transaction_type": leg.transaction_type},
                )
                response = self._execute_leg_with_retry(
                    client=client,
                    broker_details=broker_details,
                    plan=plan,
                    execution=execution,
                    leg_plan=leg_plan,
                )
                response_data = _extract_response_data(response)
                if str(response_data.get("status", "")).lower() not in {"complete", "completed", "open"}:
                    failure_message = _extract_response_message(response)
                    self._tracker.mark_leg_failed(leg, response=response)
                    self._log(
                        execution,
                        "LEG_EXECUTION_FAILED",
                        f"Leg {leg_plan.leg_name} failed during execution.",
                        {"leg_name": leg_plan.leg_name, "broker_message": failure_message, "response": response},
                    )
                    raise MultiLegExecutionError(
                        f"Leg {leg_plan.leg_name} failed during execution: {failure_message}",
                        error_code="LEG_EXECUTION_FAILED",
                        metadata={"response": response, "leg_name": leg_plan.leg_name, "broker_message": failure_message},
                    )
                self._tracker.update_leg_after_entry(leg, response)
                completed_legs.append(leg)
                self._log(
                    execution,
                    "LEG_EXECUTED",
                    f"Leg {leg_plan.leg_name} executed successfully.",
                    {"order_id": leg.broker_order_id, "entry_price": str(leg.entry_price or "")},
                )

            self._tracker.update_strategy_status(
                execution,
                status=StrategyExecution.STATUS_ACTIVE,
                entry_time=timezone.now(),
            )
            self._log(execution, "EXECUTION_ACTIVE", "Multi-leg strategy is active.", {"legs": len(completed_legs)})

            return self._serialize_execution(execution, broker_details=broker_details, refresh_pnl=False)
        except Exception as exc:
            if 'execution' in locals():
                completed_legs = [leg for leg in locals().get("completed_legs", []) if leg.status == StrategyLeg.STATUS_ACTIVE]
                if completed_legs:
                    try:
                        self._rollback_manager.rollback_completed_legs(
                            execution=execution,
                            plan=plan,
                            client=client,
                            broker_details=broker_details,
                            completed_legs=completed_legs,
                        )
                        self._tracker.update_strategy_status(
                            execution,
                            status=StrategyExecution.STATUS_ROLLED_BACK,
                            exit_reason=str(exc),
                            exit_time=timezone.now(),
                        )
                        self._log(
                            execution,
                            "ROLLBACK_COMPLETED",
                            "Completed legs were rolled back after execution failure.",
                            {"completed_leg_ids": [leg.id for leg in completed_legs]},
                        )
                    except Exception as rollback_exc:
                        self._tracker.update_strategy_status(
                            execution,
                            status=StrategyExecution.STATUS_FAILED,
                            exit_reason=f"{exc}; rollback error: {rollback_exc}",
                        )
                        self._log(execution, "ROLLBACK_FAILED", "Rollback failed and manual intervention is required.", {"error": str(rollback_exc)})
                        raise
                else:
                    self._tracker.update_strategy_status(execution, status=StrategyExecution.STATUS_FAILED, exit_reason=str(exc))
                self._log(execution, "EXECUTION_FAILED", "Multi-leg execution failed.", {"error": str(exc)})
            if isinstance(exc, MultiLegExecutionError):
                raise
            raise MultiLegExecutionError(str(exc), error_code="MULTILEG_EXECUTION_ERROR")
        finally:
            self._lock_manager.release(lock_key)

    @staticmethod
    def _assert_execution_route_ready(*, client: User, broker_details: ClientBrokerdetails) -> None:
        node = getattr(broker_details, "execution_node", None) or getattr(client, "execution_node", None)
        if not node:
            raise MultiLegExecutionError(
                "No verified execution node/proxy is assigned. Direct broker execution is blocked.",
                error_code="EXECUTION_ROUTE_REQUIRED",
            )
        if node.assigned_client_id and node.assigned_client_id != client.id:
            raise MultiLegExecutionError(
                "Assigned execution node does not belong to this client.",
                error_code="EXECUTION_ROUTE_CLIENT_MISMATCH",
            )
        if not node.is_active or not node.is_verified_with_broker:
            raise MultiLegExecutionError(
                "Assigned execution node/proxy is not active and broker verified.",
                error_code="EXECUTION_ROUTE_NOT_VERIFIED",
            )
        if node.execution_type == node.EXECUTION_TYPE_PROXY and not node.proxy_public_ip_verified:
            raise MultiLegExecutionError(
                "Assigned proxy public IP is not verified.",
                error_code="EXECUTION_PROXY_NOT_VERIFIED",
            )
        if broker_details.execution_node_id != node.id:
            broker_details.execution_node = node
            broker_details.save(update_fields=["execution_node"])

    def list_active(self, *, user: User, client_id: Optional[int] = None) -> List[Dict[str, Any]]:
        queryset = StrategyExecution.objects.select_related("client").prefetch_related("legs").filter(status__in=ACTIVE_STRATEGY_STATUSES)
        if client_id:
            if not can_access_client_record(user, client_id):
                raise MultiLegExecutionError("You do not have access to this client's executions.", error_code="PERMISSION_DENIED")
            queryset = queryset.filter(client_id=client_id)
        elif not self._is_admin(user):
            queryset = queryset.filter(client=user)
        return [self._serialize_execution(execution, refresh_pnl=True) for execution in queryset.order_by("-id")]

    def get_execution(self, execution_id: int, *, user: User, refresh_pnl: bool = True) -> Dict[str, Any]:
        execution = StrategyExecution.objects.select_related("client").prefetch_related("legs", "logs").get(id=execution_id)
        self._assert_access(execution, user)
        return self._serialize_execution(execution, refresh_pnl=refresh_pnl)

    def get_logs(self, execution_id: int, *, user: User) -> List[Dict[str, Any]]:
        execution = StrategyExecution.objects.select_related("client").get(id=execution_id)
        self._assert_access(execution, user)
        return list(execution.logs.order_by("id").values("id", "event_type", "message", "metadata", "created_at"))

    def exit_execution(self, execution_id: int, *, user: User, reason: str = "Manual exit") -> Dict[str, Any]:
        execution = StrategyExecution.objects.select_related("client").prefetch_related("legs").get(id=execution_id)
        self._assert_access(execution, user)
        broker_details = self._resolve_broker_details(execution.client, execution.broker)
        execution = self._exit_manager.exit_strategy(execution, broker_details=broker_details, reason=reason)
        self._log(execution, "MANUAL_EXIT", "Strategy exited manually.", {"reason": reason})
        return self._serialize_execution(execution, broker_details=broker_details, refresh_pnl=False)

    def kill_switch(self, *, user: User, client_id: Optional[int] = None, reason: str = "Kill switch") -> Dict[str, Any]:
        if client_id:
            if not can_access_client_record(user, client_id):
                raise MultiLegExecutionError("You do not have access to this client.", error_code="PERMISSION_DENIED")
            client = User.objects.get(id=client_id)
        else:
            client = user

        executions = StrategyExecution.objects.select_related("client").prefetch_related("legs").filter(
            client=client,
            status__in=ACTIVE_STRATEGY_STATUSES,
        )
        exited = []
        for execution in executions:
            broker_details = self._resolve_broker_details(execution.client, execution.broker)
            self._exit_manager.exit_strategy(execution, broker_details=broker_details, reason=reason)
            self._log(execution, "KILL_SWITCH", "Strategy exited through kill switch.", {"reason": reason})
            exited.append(execution.id)
        return {"client_id": client.id, "exited_strategy_ids": exited}

    def monitor_active_strategies(self, *, user: Optional[User] = None, client_id: Optional[int] = None, strategy_execution_id: Optional[int] = None) -> List[Dict[str, Any]]:
        queryset = StrategyExecution.objects.select_related("client").prefetch_related("legs").filter(status=StrategyExecution.STATUS_ACTIVE)
        if strategy_execution_id:
            queryset = queryset.filter(id=strategy_execution_id)
        if client_id:
            if user and not can_access_client_record(user, client_id):
                raise MultiLegExecutionError("You do not have access to this client.", error_code="PERMISSION_DENIED")
            queryset = queryset.filter(client_id=client_id)
        if user and not self._is_admin(user) and not client_id:
            queryset = queryset.filter(client=user)

        results = []
        for execution in queryset:
            broker_details = self._resolve_broker_details(execution.client, execution.broker)
            pnl_snapshot = self._pnl_monitor.refresh(execution, broker_details=broker_details)
            if pnl_snapshot.get("trigger_exit"):
                self._exit_manager.exit_strategy(execution, broker_details=broker_details, reason=pnl_snapshot.get("trigger_reason") or "Monitor exit")
                self._log(execution, "AUTO_EXIT", "Strategy exited by monitor.", pnl_snapshot)
            results.append(self._serialize_execution(execution, broker_details=broker_details, refresh_pnl=False))
        return results

    def _execute_leg_with_retry(
        self,
        *,
        client: User,
        broker_details: ClientBrokerdetails,
        plan: StrategyPlan,
        execution: StrategyExecution,
        leg_plan: StrategyLegPlan,
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        last_response = None
        for attempt in range(1, max_attempts + 1):
            response = self._leg_execution_manager.execute_leg(
                client=client,
                broker_details=broker_details,
                plan=plan,
                execution=execution,
                leg_plan=leg_plan,
                history_id_suffix=f"entry-{attempt}",
            )
            last_response = response
            response_data = _extract_response_data(response)
            if str(response_data.get("status", "")).lower() in {"complete", "completed", "open"}:
                return response
            self._log(
                execution,
                "LEG_RETRY" if attempt < max_attempts else "LEG_FAILED",
                f"Leg {leg_plan.leg_name} attempt {attempt} failed.",
                {"response": response},
            )
        return last_response or {"data": {"status": "Failed", "message": "Unknown leg execution failure"}}

    def _serialize_execution(
        self,
        execution: StrategyExecution,
        *,
        broker_details: Optional[ClientBrokerdetails] = None,
        refresh_pnl: bool = False,
    ) -> Dict[str, Any]:
        if refresh_pnl and execution.status == StrategyExecution.STATUS_ACTIVE:
            broker_details = broker_details or self._resolve_broker_details(execution.client, execution.broker)
            self._pnl_monitor.refresh(execution, broker_details=broker_details)
            execution.refresh_from_db()

        return {
            "id": execution.id,
            "client_id": execution.client_id,
            "broker": execution.broker,
            "strategy_name": execution.strategy_name,
            "underlying": execution.underlying,
            "expiry": execution.expiry.isoformat() if execution.expiry else None,
            "status": execution.status,
            "entry_time": execution.entry_time.isoformat() if execution.entry_time else None,
            "exit_time": execution.exit_time.isoformat() if execution.exit_time else None,
            "total_quantity": execution.total_quantity,
            "combined_pnl": float(execution.combined_pnl or 0),
            "max_pnl_seen": float(execution.max_pnl_seen or 0),
            "trailing_stop_level": float(execution.trailing_stop_level or 0) if execution.trailing_stop_level is not None else None,
            "exit_reason": execution.exit_reason,
            "idempotency_key": execution.idempotency_key,
            "legs": [
                {
                    "id": leg.id,
                    "leg_name": leg.leg_name,
                    "transaction_type": leg.transaction_type,
                    "option_type": leg.option_type,
                    "strike_price": float(leg.strike_price),
                    "symbol": leg.symbol,
                    "token": leg.token,
                    "lot_size": leg.lot_size,
                    "quantity": leg.quantity,
                    "order_type": leg.order_type,
                    "limit_price": float(leg.limit_price) if leg.limit_price is not None else None,
                    "broker_order_id": leg.broker_order_id,
                    "entry_price": float(leg.entry_price) if leg.entry_price is not None else None,
                    "exit_price": float(leg.exit_price) if leg.exit_price is not None else None,
                    "status": leg.status,
                    "pnl": float(leg.pnl or 0),
                    "stop_loss": float(leg.stop_loss) if leg.stop_loss is not None else None,
                    "exchange": leg.exchange,
                }
                for leg in execution.legs.order_by("id")
            ],
        }

    def _resolve_client(self, config: Dict[str, Any], user: User) -> User:
        client_id = config.get("client_id")
        if client_id:
            client = User.objects.filter(
                Q(id=client_id) &
                (Q(type_of_user="is_client") | Q(is_client=True) | Q(is_client="True") | Q(is_client="true"))
            ).first()
            if not client:
                raise MultiLegExecutionError(
                    "Client not found.",
                    error_code="CLIENT_NOT_FOUND",
                    metadata={"client_id": client_id},
                )
            if not can_access_client_record(user, client):
                raise MultiLegExecutionError("You do not have permission to execute for this client.", error_code="PERMISSION_DENIED")
            return client
        return user

    def _resolve_broker_details(self, client: User, broker_name: Any) -> ClientBrokerdetails:
        broker_name_value = str(broker_name or "").strip()
        normalized_broker_name = normalize_broker_name(broker_name_value)
        broker_details = None
        for candidate in ClientBrokerdetails.objects.filter(client=client).select_related("broker_name"):
            candidate_name = getattr(getattr(candidate, "broker_name", None), "broker_name", "")
            if normalize_broker_name(candidate_name) == normalized_broker_name:
                broker_details = candidate
                break
        if not broker_details:
            raise MultiLegExecutionError(
                f"Broker details not found for {broker_name_value}.",
                error_code="BROKER_NOT_FOUND",
            )
        return broker_details

    def _get_client_broker_name(self, client: User) -> Optional[str]:
        broker_detail = ClientBrokerdetails.objects.filter(client=client).select_related("broker_name").first()
        if broker_detail and broker_detail.broker_name:
            return broker_detail.broker_name.broker_name
        return None

    def _sync_client_strategy_assignments(self, client: User) -> None:
        assigned_strategies = Strategies.objects.filter(
            Q(client_strategy=client) | Q(clients=client),
            execution_mode=Strategies.EXECUTION_MODE_MULTI_LEG,
            is_active=True,
        ).select_related("segment").distinct()

        retained_ids = set()
        for strategy in assigned_strategies:
            setting, _ = ClientMultiLegStrategySetting.objects.update_or_create(
                client=client,
                strategy=strategy,
                defaults={
                    "segment": strategy.segment,
                    "group_service": getattr(getattr(client, "Group_service", None), "group_name", None),
                    "broker": self._get_client_broker_name(client),
                },
            )
            retained_ids.add(setting.id)

        ClientMultiLegStrategySetting.objects.filter(client=client).exclude(id__in=retained_ids).delete()

    def _merge_assigned_strategy_defaults(self, *, client: User, config: Dict[str, Any]) -> Dict[str, Any]:
        strategy_name = str(config.get("strategy_name") or "").strip().upper()
        if not strategy_name:
            return dict(config)

        self._sync_client_strategy_assignments(client)
        setting = ClientMultiLegStrategySetting.objects.select_related("strategy", "segment").filter(
            client=client,
            strategy__execution_mode=Strategies.EXECUTION_MODE_MULTI_LEG,
            strategy__multi_leg_template=strategy_name,
            strategy__is_active=True,
        ).first()
        if not setting:
            return dict(config)

        merged = dict(config)
        if setting.broker and not merged.get("broker"):
            merged["broker"] = setting.broker
        if setting.product_type and not merged.get("product_type"):
            merged["product_type"] = setting.product_type
        if setting.order_type and not merged.get("order_type"):
            merged["order_type"] = setting.order_type
        if setting.buffer_percentage is not None and merged.get("buffer_percentage") in (None, ""):
            merged["buffer_percentage"] = float(setting.buffer_percentage)
        if setting.quantity and not merged.get("quantity_lots"):
            merged["quantity_lots"] = setting.quantity
        if setting.expiry_date and not merged.get("expiry"):
            merged["expiry"] = setting.expiry_date.strftime("%Y-%m-%d")
        if setting.group_service and not merged.get("group_service"):
            merged["group_service"] = setting.group_service
        if setting.underlying and not merged.get("underlying"):
            merged["underlying"] = setting.underlying
        if setting.segment and not merged.get("underlying"):
            merged["underlying"] = getattr(setting.segment, "short_name", None) or getattr(setting.segment, "name", None)
        if setting.legs and not merged.get("legs"):
            merged["legs"] = setting.legs
        if setting.start_time and not merged.get("entry_time"):
            merged["entry_time"] = setting.start_time.strftime("%H:%M")
        if setting.end_time and not merged.get("exit_time"):
            merged["exit_time"] = setting.end_time.strftime("%H:%M")
        return merged

    def _assert_strategy_allowed_for_client(self, *, client: User, plan: StrategyPlan) -> None:
        self._sync_client_strategy_assignments(client)
        is_allowed = ClientMultiLegStrategySetting.objects.filter(
            client=client,
            strategy__execution_mode=Strategies.EXECUTION_MODE_MULTI_LEG,
            strategy__multi_leg_template=plan.strategy_name,
            strategy__is_active=True,
        ).exists()
        if is_allowed:
            return

        raise MultiLegExecutionError(
            "This multi-leg strategy is locked for this client. Please contact admin to enable it.",
            error_code="MULTILEG_STRATEGY_LOCKED",
            metadata={
                "client_id": client.id,
                "strategy_name": plan.strategy_name,
            },
        )

    def _assert_access(self, execution: StrategyExecution, user: User) -> None:
        if not can_access_client_record(user, execution.client):
            raise MultiLegExecutionError("You do not have access to this strategy execution.", error_code="PERMISSION_DENIED")

    def _log(self, execution: StrategyExecution, event_type: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        StrategyExecutionLog.objects.create(
            strategy_execution=execution,
            event_type=event_type,
            message=message,
            metadata=self._sanitize_metadata(metadata or {}),
        )

    @staticmethod
    def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        redacted = {}
        for key, value in metadata.items():
            if any(secret_key in str(key).lower() for secret_key in ("token", "secret", "password", "api_key")):
                redacted[key] = "***redacted***"
            else:
                redacted[key] = value
        return redacted

    @staticmethod
    def _is_admin(user: User) -> bool:
        return is_admin_or_superadmin(user) or bool(getattr(user, "is_staff", False))


_multileg_execution_engine: Optional[MultiLegExecutionEngine] = None


def get_multileg_execution_engine() -> MultiLegExecutionEngine:
    global _multileg_execution_engine
    if _multileg_execution_engine is None:
        _multileg_execution_engine = MultiLegExecutionEngine()
    return _multileg_execution_engine
