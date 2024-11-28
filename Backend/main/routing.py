from django.urls import re_path

from main.consumers import StockTradingConsumer # type: ignore


websocket_urlpatterns = [
    re_path(r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_token>[\w-]+)/$', StockTradingConsumer.as_asgi()),
]
