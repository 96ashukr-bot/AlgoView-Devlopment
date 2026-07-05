from django.urls import re_path

from main.sltp_consumers import SLTPWatcherLiveConsumer

try:
    from main.consumers import UpstoxChainConsumer, UpstoxChainLiveSymbolConsumer, UpstoxMarketDataConsumer
except ModuleNotFoundError:
    UpstoxChainConsumer = UpstoxChainLiveSymbolConsumer = UpstoxMarketDataConsumer = None


# websocket_urlpatterns = [
#     # re_path(r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_token>[\w-]+)/$', StockTradingConsumer.as_asgi()),
#         re_path(
               
websocket_urlpatterns = [
    re_path(r'ws/sl-tp-watcher/$', SLTPWatcherLiveConsumer.as_asgi()),
]

if UpstoxChainConsumer:
    websocket_urlpatterns.extend([
        re_path(r'ws/option-chain/$', UpstoxChainConsumer.as_asgi()),
        re_path(r'ws/stock-live-price/$', UpstoxMarketDataConsumer.as_asgi()),
        re_path(r'ws/stock-symbol-live-price/$', UpstoxChainLiveSymbolConsumer.as_asgi()),
    ])
