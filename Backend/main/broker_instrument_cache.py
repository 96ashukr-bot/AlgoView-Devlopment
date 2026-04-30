import csv
import gzip
import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

import requests
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger("main")


FYERS_HEADERS = [
    "FyToken",
    "Symbol Details",
    "Exchange Instrument Type",
    "Minimum Lot Size",
    "Tick Size",
    "ISIN",
    "Trading Session",
    "Last Update Date",
    "Expiry Date",
    "Symbol Ticker",
    "Exchange",
    "Segment",
    "Scrip Code",
    "Underlying Symbol",
    "Underlying Scrip Code",
    "Strike Price",
    "Option Type",
    "Underlying FyToken",
    "Reserved 1",
    "Reserved 2",
    "Reserved 3",
]


def _main_dir() -> Path:
    return Path(settings.BASE_DIR) / "main"


def _is_file_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    modified = timezone.datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.get_current_timezone())
    return modified.date() == timezone.localdate()


def _file_has_content(path: Path, *, required_headers: Optional[Iterable[str]] = None) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    required = [str(header).strip() for header in (required_headers or []) if str(header).strip()]
    if not required:
        return True
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as file_obj:
            first_line = file_obj.readline()
    except OSError:
        return False
    return all(header in first_line for header in required)


def _stale_or_raise(path: Path, exc: Exception, *, label: str, required_headers: Optional[Iterable[str]] = None) -> Path:
    if _file_has_content(path, required_headers=required_headers):
        logger.warning("Using stale %s instrument master at %s after refresh failed: %s", label, path, exc)
        return path
    raise exc


def _newest_valid_file(pattern: str, *, required_headers: Optional[Iterable[str]] = None) -> Optional[Path]:
    candidates = [
        path
        for path in _main_dir().glob(pattern)
        if _file_has_content(path, required_headers=required_headers)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


def _write_bytes_atomic(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_bytes(payload)
    tmp_path.replace(path)
    return path


def _download(url: str, timeout: int = 20) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def ensure_dhan_instruments_file() -> Path:
    path = _main_dir() / "dhantoken.csv"
    if _is_file_fresh(path) and _file_has_content(path, required_headers=("SEM_SMST_SECURITY_ID", "SEM_TRADING_SYMBOL")):
        return path

    try:
        payload = _download("https://images.dhan.co/api-data/api-scrip-master.csv")
        if b"SEM_SMST_SECURITY_ID" not in payload or b"SEM_TRADING_SYMBOL" not in payload:
            raise ValueError("Dhan instrument source returned invalid headers")
        logger.info("Refreshing Dhan instrument master at %s", path)
        return _write_bytes_atomic(path, payload)
    except Exception as exc:
        return _stale_or_raise(
            path,
            exc,
            label="Dhan",
            required_headers=("SEM_SMST_SECURITY_ID", "SEM_TRADING_SYMBOL"),
        )


def ensure_upstox_instruments_file(exchange: str) -> Path:
    normalized_exchange = str(exchange or "NSE").strip().upper()
    path = _main_dir() / f"upstox_{normalized_exchange.lower()}_instruments.json"
    if _is_file_fresh(path) and _file_has_content(path):
        return path

    try:
        payload = _download(f"https://assets.upstox.com/market-quote/instruments/exchange/{normalized_exchange}.json.gz")
        with gzip.GzipFile(fileobj=BytesIO(payload)) as gz_file:
            decoded = gz_file.read()
        parsed = json.loads(decoded.decode("utf-8"))
        if not isinstance(parsed, list) or not parsed:
            raise ValueError(f"Upstox {normalized_exchange} instrument source returned no instruments")
        logger.info("Refreshing Upstox %s instrument master at %s", normalized_exchange, path)
        return _write_bytes_atomic(path, decoded)
    except Exception as exc:
        return _stale_or_raise(path, exc, label=f"Upstox {normalized_exchange}")


def load_upstox_instruments(exchange: str):
    path = ensure_upstox_instruments_file(exchange)
    with path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def _resolve_fyers_source(exchange: str = None, segment: str = None):
    exchange_value = str(exchange or "").strip().upper()
    segment_value = str(segment or "").strip().upper()

    if exchange_value in {"MCX", "MCX_COM"} or "COMMODITY" in segment_value or "MCX" in segment_value or segment_value == "COM":
        return ("MCX_COM", "https://public.fyers.in/sym_details/MCX_COM.csv", "fyers_mcx_com.csv")
    if exchange_value in {"NFO", "NSE_FO"} or "FNO" in segment_value or segment_value == "FO":
        return ("NSE_FO", "https://public.fyers.in/sym_details/NSE_FO.csv", "fyers_nse_fo.csv")
    if exchange_value in {"BSE", "BSE_EQ"}:
        return ("BSE_CM", "https://public.fyers.in/sym_details/BSE_CM.csv", "fyers_bse_cm.csv")
    return ("NSE_CM", "https://public.fyers.in/sym_details/NSE_CM.csv", "fyers_nse_cm.csv")


def ensure_fyers_instruments_file(exchange: str = None, segment: str = None) -> Path:
    _source_name, url, filename = _resolve_fyers_source(exchange=exchange, segment=segment)
    path = _main_dir() / filename
    if _is_file_fresh(path) and _file_has_content(path, required_headers=("FyToken", "Symbol Details")):
        return path

    try:
        raw_payload = _download(url)
        decoded_rows = raw_payload.decode("utf-8").splitlines()
        rows = list(csv.reader(decoded_rows))
        if len(rows) <= 1:
            raise ValueError(f"FYERS instrument source returned no rows for {url}")

        normalized_rows = [FYERS_HEADERS]
        normalized_rows.extend(rows[1:])

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(f"{path.suffix}.tmp")
        with tmp_path.open("w", newline="", encoding="utf-8") as file_obj:
            writer = csv.writer(file_obj)
            writer.writerows(normalized_rows)
        tmp_path.replace(path)
        logger.info("Refreshing FYERS instrument master at %s from %s", path, url)
        return path
    except Exception as exc:
        legacy_path = _main_dir() / "fyers_instrument_symbol.csv"
        if _file_has_content(legacy_path, required_headers=("FyToken", "Symbol Details")):
            logger.warning("Using legacy FYERS instrument master at %s after refresh failed: %s", legacy_path, exc)
            return legacy_path
        return _stale_or_raise(
            path,
            exc,
            label="FYERS",
            required_headers=("FyToken", "Symbol Details"),
        )


def ensure_fivepaisa_scrip_master_file(segment: str) -> Path:
    normalized_segment = str(segment or "nse_fo").strip().lower()
    today = timezone.localdate()
    path = _main_dir() / f"scrip_master_{normalized_segment}_{today.strftime('%Y_%m')}.csv"
    if _is_file_fresh(path) and _file_has_content(path, required_headers=("Exch", "ScripCode")):
        return path

    url = f"https://Openapi.5paisa.com/VendorsAPI/Service1.svc/ScripMaster/segment/{normalized_segment}"
    try:
        payload = _download(url, timeout=60)
        if b"Exch" not in payload or b"ScripCode" not in payload:
            raise ValueError("5Paisa scrip master source returned invalid headers")
        logger.info("Refreshing 5Paisa %s scrip master at %s", normalized_segment, path)
        return _write_bytes_atomic(path, payload)
    except Exception as exc:
        fallback_path = _newest_valid_file(
            f"scrip_master_{normalized_segment}_*.csv",
            required_headers=("Exch", "ScripCode"),
        )
        if fallback_path:
            logger.warning("Using cached 5Paisa %s scrip master at %s after refresh failed: %s", normalized_segment, fallback_path, exc)
            return fallback_path
        return _stale_or_raise(
            path,
            exc,
            label=f"5Paisa {normalized_segment}",
            required_headers=("Exch", "ScripCode"),
        )
