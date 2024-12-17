from django.urls import re_path

from main.consumers import StockChainConsumer, StockTradingConsumer#,OptionChainConsumer # type: ignore


# websocket_urlpatterns = [
#     # re_path(r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_token>[\w-]+)/$', StockTradingConsumer.as_asgi()),
#         re_path(
   
#         r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_tokens>[a-zA-Z0-9,]+)/$',
#         StockTradingConsumer.as_asgi(),
#         )
    
# ]

# websocket_urlpatterns = [
#     re_path(
#         r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_tokens>[a-zA-Z0-9,]+)/$',
#         StockTradingConsumer.as_asgi(),
#     ),
# ]

websocket_urlpatterns = [
    re_path(r'ws/stock-live-price/$', StockTradingConsumer.as_asgi()),  # No dynamic parameters here
    re_path(r'ws/option-chain/$', StockChainConsumer.as_asgi()),
]