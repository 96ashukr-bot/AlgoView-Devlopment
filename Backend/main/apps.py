from django.apps import AppConfig
import sys


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        from main.services.egress_guard import enforce_broker_proxy_for_requests

        enforce_broker_proxy_for_requests()
        # Management/test commands should stay lightweight. Serving processes
        # preload durable snapshots once so the first live order does no parsing.
        if any(command in sys.argv for command in ("test", "check", "migrate", "makemigrations", "collectstatic")):
            return

        from main.angelone.managers.contract_manager import ContractMasterManager
        from main.broker_instrument_cache import prewarm_broker_instrument_indexes

        prewarm_broker_instrument_indexes()
        ContractMasterManager.get_instance().initialize(blocking=False)
