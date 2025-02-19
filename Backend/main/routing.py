from django.urls import re_path

from main.consumers import UpstoxChainConsumer, StockTradingConsumer,UpstoxMarketDataConsumer#,OptionChainConsumer # type: ignore


# websocket_urlpatterns = [
#     # re_path(r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_token>[\w-]+)/$', StockTradingConsumer.as_asgi()),
#         re_path(
               
websocket_urlpatterns = [
    # re_path(r'ws/stock-live-price/$', StockTradingConsumer.as_asgi()),  # No dynamic parameters here
    re_path(r'ws/option-chain/$', UpstoxChainConsumer.as_asgi()),
    re_path(r'ws/stock-live-price/$', UpstoxMarketDataConsumer.as_asgi()),
    
]
