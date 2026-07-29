from django.test import SimpleTestCase

from main import routing, sltp_consumers


class WebSocketRoutingTests(SimpleTestCase):
    def test_sl_tp_route_uses_current_live_price_consumer(self):
        callback = routing.websocket_urlpatterns[0].callback

        self.assertIs(callback.consumer_class, sltp_consumers.SLTPWatcherLiveConsumer)
