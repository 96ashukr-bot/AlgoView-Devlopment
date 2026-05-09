from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        from main.services.egress_guard import enforce_broker_proxy_for_requests

        enforce_broker_proxy_for_requests()
