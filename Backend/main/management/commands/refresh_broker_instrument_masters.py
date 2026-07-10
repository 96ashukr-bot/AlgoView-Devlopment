from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Pre-refresh broker instrument/contract masters and keep stale-cache fallback ready."

    def add_arguments(self, parser):
        parser.add_argument(
            "--broker",
            action="append",
            dest="brokers",
            help="Broker/provider to refresh. Can be passed multiple times. Defaults to all supported public masters.",
        )

    def handle(self, *args, **options):
        requested = {str(item).strip().lower() for item in (options.get("brokers") or []) if str(item).strip()}
        results = []

        def should_run(name):
            return not requested or name in requested

        def record(name, status, message):
            results.append((name, status, message))
            style = self.style.SUCCESS if status == "ok" else self.style.WARNING if status == "warn" else self.style.ERROR
            self.stdout.write(style(f"{name}: {message}"))

        if should_run("angelone") or should_run("angel one"):
            try:
                from main.angelone.managers.contract_manager import ContractMasterManager

                manager = ContractMasterManager.get_instance()
                refreshed = manager._refresh_contracts()
                if refreshed:
                    record("Angel One", "ok", f"contract master refreshed ({manager.contract_count} contracts)")
                elif manager.initialize(blocking=False) and manager.contract_count:
                    record("Angel One", "warn", f"refresh failed; using cached contract master ({manager.contract_count} contracts)")
                else:
                    record("Angel One", "error", "contract master unavailable")
            except Exception as exc:
                record("Angel One", "error", str(exc))

        if should_run("upstox"):
            try:
                from main.broker_instrument_cache import ensure_upstox_instruments_file

                for exchange in ("NSE", "BSE", "MCX"):
                    path = ensure_upstox_instruments_file(exchange)
                    record("Upstox", "ok", f"{exchange} instruments ready at {path}")
            except Exception as exc:
                record("Upstox", "error", str(exc))

        if should_run("dhan"):
            try:
                from main.broker_instrument_cache import ensure_dhan_instruments_file

                path = ensure_dhan_instruments_file()
                record("Dhan", "ok", f"instruments ready at {path}")
            except Exception as exc:
                record("Dhan", "error", str(exc))

        if should_run("fyers"):
            try:
                from main.broker_instrument_cache import ensure_fyers_instruments_file

                for exchange, segment in (("NSE", "CM"), ("NFO", "FO"), ("BSE", "CM"), ("BFO", "FO"), ("MCX", "COM")):
                    path = ensure_fyers_instruments_file(exchange=exchange, segment=segment)
                    record("FYERS", "ok", f"{exchange}/{segment} instruments ready at {path}")
            except Exception as exc:
                record("FYERS", "error", str(exc))

        if should_run("5paisa") or should_run("fivepaisa"):
            try:
                from main.broker_instrument_cache import ensure_fivepaisa_scrip_master_file

                for segment in ("nse_fo", "bse_fo"):
                    path = ensure_fivepaisa_scrip_master_file(segment)
                    record("5Paisa", "ok", f"{segment} scrip master ready at {path}")
            except Exception as exc:
                record("5Paisa", "error", str(exc))

        if should_run("groww"):
            try:
                from main.groww import _refresh_instrument_cache, GROWW_INSTRUMENT_CACHE

                _refresh_instrument_cache()
                record("Groww", "ok", f"instruments ready at {GROWW_INSTRUMENT_CACHE}")
            except Exception as exc:
                record("Groww", "error", str(exc))

        if should_run("zerodha"):
            try:
                from kiteconnect import KiteConnect
                from main.models import ClientBrokerdetails
                from main.broker_instrument_cache import save_zerodha_instruments
                from main.services.egress_guard import allow_direct_market_data_egress

                cached_any = False
                queryset = ClientBrokerdetails.objects.select_related("broker_name").filter(
                    broker_name__broker_name__iexact="Zerodha",
                    broker_API_KEY__isnull=False,
                )
                for details in queryset.order_by("-tokenCreatedAt", "-id")[:25]:
                    access_token = None
                    getter = getattr(details, "get_access_token_secure", None)
                    if callable(getter):
                        access_token = getter()
                    access_token = access_token or getattr(details, "access_token", None)
                    if not access_token or not details.broker_API_KEY:
                        continue
                    try:
                        kite = KiteConnect(api_key=details.broker_API_KEY)
                        kite.set_access_token(access_token)
                        with allow_direct_market_data_egress():
                            for exchange in ("NFO", "BFO", "NSE", "BSE"):
                                instruments = kite.instruments(exchange)
                                path = save_zerodha_instruments(exchange, instruments)
                                record("Zerodha", "ok", f"{exchange} instruments ready at {path}")
                        cached_any = True
                        break
                    except Exception as exc:
                        record("Zerodha", "warn", f"client {details.client_id} session could not refresh instruments: {exc}")
                if not cached_any:
                    record("Zerodha", "warn", "no valid Zerodha session was available for pre-market instrument refresh; existing cache will be used if present")
            except Exception as exc:
                record("Zerodha", "error", str(exc))

        if should_run("alice") or should_run("aliceblue") or should_run("alice blue"):
            try:
                from main.broker_instrument_cache import sync_aliceblue_contract_file_for_sdk

                for exchange in ("NFO", "NSE", "BFO", "BSE", "MCX", "INDICES"):
                    path = sync_aliceblue_contract_file_for_sdk(exchange)
                    record("Alice Blue", "ok", f"{exchange} contract master ready at {path}")
            except Exception as exc:
                record("Alice Blue", "error", str(exc))

        failures = [name for name, status, _message in results if status == "error"]
        if failures:
            raise SystemExit(1)
