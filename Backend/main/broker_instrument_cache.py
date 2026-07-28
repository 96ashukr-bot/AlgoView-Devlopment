import csv
import gzip
import json
import logging
import os
import re
import tempfile
import threading
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import requests
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger("main")


_index_lock = threading.RLock()
_refresh_lock = threading.Lock()
_refreshing = set()
_zerodha_indexes: Dict[str, Tuple[Tuple[str, int, int], Dict[str, dict]]] = {}
_dhan_index: Optional[Tuple[Tuple[str, int, int], Dict[Tuple[str, str], dict], Dict[str, dict]]] = None


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


def _file_signature(path: Path) -> Tuple[str, int, int]:
    stat = path.stat()
    return str(path.resolve()), stat.st_mtime_ns, stat.st_size


def _normalize_instrument_symbol(value) -> str:
    return re.sub(r"[^\w]", "", str(value or "").strip()).upper()


def _begin_refresh(key: str) -> bool:
    with _refresh_lock:
        if key in _refreshing:
            return False
        _refreshing.add(key)
        return True


def _end_refresh(key: str) -> None:
    with _refresh_lock:
        _refreshing.discard(key)


def _run_refresh(key: str, target, *args) -> None:
    if not _begin_refresh(key):
        return

    def runner():
        try:
            target(*args)
        except Exception as exc:
            logger.warning("Background %s instrument refresh failed: %s", key, exc)
        finally:
            _end_refresh(key)

    threading.Thread(target=runner, daemon=True, name=f"instrument-refresh-{key}").start()


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
    # A unique same-directory temporary file makes os.replace atomic while
    # avoiding collisions between Gunicorn/Celery processes refreshing at once.
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp_file:
            tmp_file.write(payload)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            tmp_path = Path(tmp_file.name)
        tmp_path.chmod(0o664)
        os.replace(tmp_path, path)
        path.chmod(0o664)
        return path
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


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


def ensure_aliceblue_contract_file(exchange: str) -> Path:
    normalized_exchange = str(exchange or "NFO").strip().upper()
    if not normalized_exchange or not (len(normalized_exchange) == 3 or normalized_exchange == "INDICES"):
        raise ValueError("Invalid Alice Blue exchange")

    path = _main_dir() / f"aliceblue_{normalized_exchange}.csv"
    if _is_file_fresh(path) and _file_has_content(path):
        return path

    try:
        payload = _download(
            f"https://v2api.aliceblueonline.com/restpy/static/contract_master/{normalized_exchange}.csv",
            timeout=60,
        )
        if not payload.strip():
            raise ValueError(f"Alice Blue {normalized_exchange} contract source returned empty payload")
        logger.info("Refreshing Alice Blue %s contract master at %s", normalized_exchange, path)
        return _write_bytes_atomic(path, payload)
    except Exception as exc:
        fallback_path = _newest_valid_file(f"aliceblue_{normalized_exchange}.csv")
        if fallback_path:
            logger.warning("Using cached Alice Blue %s contract master at %s after refresh failed: %s", normalized_exchange, fallback_path, exc)
            return fallback_path
        return _stale_or_raise(path, exc, label=f"Alice Blue {normalized_exchange}")


def sync_aliceblue_contract_file_for_sdk(exchange: str) -> Path:
    """Keep pya3's expected EXCHANGE.csv file in the working directory."""
    normalized_exchange = str(exchange or "NFO").strip().upper()
    source_path = ensure_aliceblue_contract_file(normalized_exchange)
    sdk_path = Path.cwd() / f"{normalized_exchange}.csv"
    try:
        if (
            not sdk_path.exists()
            or sdk_path.stat().st_mtime < source_path.stat().st_mtime
            or sdk_path.stat().st_size != source_path.stat().st_size
        ):
            _write_bytes_atomic(sdk_path, source_path.read_bytes())
    except OSError as exc:
        logger.warning("Unable to sync Alice Blue contract master to %s: %s", sdk_path, exc)
    return source_path


def save_zerodha_instruments(exchange: str, instruments) -> Path:
    normalized_exchange = str(exchange or "NFO").strip().upper()
    path = _main_dir() / f"zerodha_{normalized_exchange}_instruments.json"
    payload = json.dumps(list(instruments or []), default=str).encode("utf-8")
    if not payload or payload == b"[]":
        raise ValueError(f"Zerodha {normalized_exchange} instrument source returned no instruments")
    logger.info("Refreshing Zerodha %s instrument cache at %s", normalized_exchange, path)
    return _write_bytes_atomic(path, payload)


def load_zerodha_instruments(exchange: str):
    normalized_exchange = str(exchange or "NFO").strip().upper()
    path = _main_dir() / f"zerodha_{normalized_exchange}_instruments.json"
    if not _file_has_content(path):
        return []
    with path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def _build_zerodha_index(path: Path) -> Dict[str, dict]:
    with path.open("r", encoding="utf-8") as file_obj:
        instruments = json.load(file_obj)
    return {
        str(item.get("tradingsymbol") or "").strip().upper(): item
        for item in instruments
        if isinstance(item, dict) and str(item.get("tradingsymbol") or "").strip()
    }


def load_zerodha_instrument_index(exchange: str) -> Dict[str, dict]:
    """Return the process-local immutable Zerodha symbol index."""
    normalized_exchange = str(exchange or "NFO").strip().upper()
    path = _main_dir() / f"zerodha_{normalized_exchange}_instruments.json"
    if not _file_has_content(path):
        return {}
    signature = _file_signature(path)
    with _index_lock:
        cached = _zerodha_indexes.get(normalized_exchange)
        if cached and cached[0] == signature:
            return cached[1]

    new_index = _build_zerodha_index(path)
    with _index_lock:
        _zerodha_indexes[normalized_exchange] = (signature, new_index)
    logger.info("Zerodha %s instrument index loaded", normalized_exchange, extra={"instrument_count": len(new_index)})
    return new_index


def refresh_zerodha_instrument_index(exchange: str, kite) -> Dict[str, dict]:
    normalized_exchange = str(exchange or "NFO").strip().upper()
    instruments = kite.instruments(normalized_exchange)
    path = save_zerodha_instruments(normalized_exchange, instruments)
    new_index = _build_zerodha_index(path)
    with _index_lock:
        _zerodha_indexes[normalized_exchange] = (_file_signature(path), new_index)
    return new_index


def _independent_zerodha_client(kite):
    """Clone a real Kite client so background I/O never shares order state."""
    api_key = getattr(kite, "api_key", None)
    access_token = getattr(kite, "access_token", None)
    if not api_key or not access_token:
        # Test doubles and non-standard clients remain usable.
        return kite
    from kiteconnect import KiteConnect

    refresh_client = KiteConnect(api_key=api_key, proxies=getattr(kite, "proxies", None))
    refresh_client.set_access_token(access_token)
    return refresh_client


def get_zerodha_instrument(exchange: str, symbol: str, kite=None) -> Optional[dict]:
    """Resolve in O(1), refreshing stale/missing snapshots outside live orders."""
    normalized_exchange = str(exchange or "NFO").strip().upper()
    symbol_key = str(symbol or "").strip().upper()
    index = load_zerodha_instrument_index(normalized_exchange)
    match = index.get(symbol_key)
    path = _main_dir() / f"zerodha_{normalized_exchange}_instruments.json"

    if match:
        if kite is not None and not _is_file_fresh(path):
            _run_refresh(
                f"zerodha-{normalized_exchange}",
                refresh_zerodha_instrument_index,
                normalized_exchange,
                _independent_zerodha_client(kite),
            )
        return match

    if kite is None:
        return None
    # Newly listed symbols trigger refresh outside the execution thread. The
    # broker remains the final authority, so a valid-looking symbol can still be
    # submitted immediately while this snapshot catches up.
    _run_refresh(
        f"zerodha-{normalized_exchange}",
        refresh_zerodha_instrument_index,
        normalized_exchange,
        _independent_zerodha_client(kite),
    )
    return None


def _build_dhan_index(path: Path):
    by_contract: Dict[Tuple[str, str], dict] = {}
    by_security_id: Dict[str, dict] = {}
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file_obj:
        for row in csv.DictReader(file_obj):
            security_id = str(row.get("SEM_SMST_SECURITY_ID") or "").strip()
            symbol = _normalize_instrument_symbol(row.get("SEM_TRADING_SYMBOL"))
            expiry_raw = str(row.get("SEM_EXPIRY_DATE") or "").strip()
            expiry = expiry_raw[:10] if re.match(r"^20\d{2}-\d{2}-\d{2}", expiry_raw) else ""
            if not security_id:
                continue
            record = {
                "security_id": security_id,
                "trading_symbol": row.get("SEM_TRADING_SYMBOL"),
                "expiry_date": expiry,
                "lot_size": row.get("SEM_LOT_UNITS"),
                "exchange": row.get("SEM_EXM_EXCH_ID"),
                "segment": row.get("SEM_SEGMENT"),
            }
            by_security_id[security_id] = record
            if symbol and expiry:
                by_contract[(symbol, expiry)] = record
    return by_contract, by_security_id


def load_dhan_instrument_index(*, refresh_source: bool = False):
    """Load Dhan security-id and lot-size maps once per file version."""
    global _dhan_index
    path = Path(ensure_dhan_instruments_file()) if refresh_source else _main_dir() / "dhantoken.csv"
    if not _file_has_content(path, required_headers=("SEM_SMST_SECURITY_ID", "SEM_TRADING_SYMBOL")):
        if not refresh_source:
            path = Path(ensure_dhan_instruments_file())
        else:
            return {}, {}
    signature = _file_signature(path)
    with _index_lock:
        if _dhan_index and _dhan_index[0] == signature:
            return _dhan_index[1], _dhan_index[2]

    by_contract, by_security_id = _build_dhan_index(path)
    with _index_lock:
        _dhan_index = (signature, by_contract, by_security_id)
    logger.info(
        "Dhan instrument index loaded contracts=%s security_ids=%s",
        len(by_contract),
        len(by_security_id),
    )
    return by_contract, by_security_id


def refresh_dhan_instrument_index():
    return load_dhan_instrument_index(refresh_source=True)


def get_dhan_instrument(symbol: str, expiry_date: str) -> Optional[dict]:
    path = _main_dir() / "dhantoken.csv"
    by_contract, _by_security_id = load_dhan_instrument_index(refresh_source=not _file_has_content(path))
    if _file_has_content(path) and not _is_file_fresh(path):
        _run_refresh("dhan", refresh_dhan_instrument_index)
    return by_contract.get((_normalize_instrument_symbol(symbol), str(expiry_date or "")[:10]))


def get_dhan_lot_size(security_id, *, symbol: str = None, expiry_date: str = None) -> Optional[float]:
    by_contract, by_security_id = load_dhan_instrument_index()
    record = by_security_id.get(str(int(security_id))) if security_id not in (None, "") else None
    if symbol and expiry_date:
        contract_record = by_contract.get((_normalize_instrument_symbol(symbol), str(expiry_date)[:10]))
        # Prevent an unrelated security-id collision from supplying a lot size.
        if not contract_record or contract_record.get("security_id") != str(int(security_id)):
            return None
        record = contract_record
    if not record:
        return None
    try:
        return float(record.get("lot_size"))
    except (TypeError, ValueError):
        return None


def prewarm_broker_instrument_indexes() -> None:
    """Load durable snapshots without making network calls during startup."""
    started = timezone.now()
    try:
        load_dhan_instrument_index(refresh_source=False)
    except Exception as exc:
        logger.warning("Dhan instrument prewarm skipped: %s", exc)
    for exchange in ("NFO", "NSE", "BFO", "BSE"):
        try:
            load_zerodha_instrument_index(exchange)
        except Exception as exc:
            logger.warning("Zerodha %s instrument prewarm skipped: %s", exchange, exc)
    logger.info("Broker instrument prewarm completed in %.3fs", (timezone.now() - started).total_seconds())


def _resolve_fyers_source(exchange: str = None, segment: str = None):
    exchange_value = str(exchange or "").strip().upper()
    segment_value = str(segment or "").strip().upper()

    if exchange_value in {"MCX", "MCX_COM"} or "COMMODITY" in segment_value or "MCX" in segment_value or segment_value == "COM":
        return ("MCX_COM", "https://public.fyers.in/sym_details/MCX_COM.csv", "fyers_mcx_com.csv")
    if exchange_value in {"BFO", "BSE_FO", "BSE_FNO"} or (
        "BSE" in segment_value and ("FNO" in segment_value or "FO" in segment_value)
    ):
        return ("BSE_FO", "https://public.fyers.in/sym_details/BSE_FO.csv", "fyers_bse_fo.csv")
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
