from django.test import TestCase
from django.urls import Resolver404, resolve


class BrokerCallbackRoutingTests(TestCase):
    def test_broker_callback_accepts_request_token(self):
        response = self.client.get("/api/broker/callback/", {"request_token": "test123"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["message"], "Broker callback received.")
        self.assertIn("request_token", payload["callback"]["present_params"])
        self.assertNotIn("test123", str(payload))

    def test_broker_callback_final_url_is_not_double_prefixed(self):
        match = resolve("/api/broker/callback/")
        self.assertEqual(match.url_name, "broker-callback")

        with self.assertRaises(Resolver404):
            resolve("/api/api/broker/callback/")

    def test_broker_callback_missing_params_returns_safe_json(self):
        response = self.client.get("/api/broker/callback/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["callback"]["present_params"], [])
        self.assertEqual(payload["callback"]["token_exchange"], "not_attempted")
