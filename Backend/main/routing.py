from django.urls import re_path

from main.consumers import StockTradingConsumer # type: ignore


# websocket_urlpatterns = [
#     # re_path(r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_token>[\w-]+)/$', StockTradingConsumer.as_asgi()),
#         re_path(
   
#         r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_tokens>[a-zA-Z0-9,]+)/$',
#         StockTradingConsumer.as_asgi(),
#         )
    
# ]

websocket_urlpatterns = [
    re_path(
        r'ws/option-chain/(?P<exchange_type>\d+)/(?P<symbol_tokens>[a-zA-Z0-9,]+)/$',
        StockTradingConsumer.as_asgi(),
    ),
]