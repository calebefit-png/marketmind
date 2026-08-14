import unittest

from fastapi.testclient import TestClient

from main import app


class AlertStatusRoutesTestCase(unittest.TestCase):
    def test_public_alert_status_routes_are_registered(self):
        paths = {route.path for route in app.routes}
        self.assertIn("/alerts/status", paths)
        self.assertIn("/alerts/recent", paths)

    def test_alert_status_remains_safe_when_database_is_unavailable(self):
        with TestClient(app) as client:
            response = client.get("/alerts/status")
        self.assertIn(response.status_code, {200, 503})
        self.assertNotIn("TELEGRAM_BOT_TOKEN", response.text)
        self.assertNotIn("TELEGRAM_CHAT_ID", response.text)

    def test_recent_alerts_accepts_all_public_filter_fields(self):
        with TestClient(app) as client:
            response = client.get(
                "/alerts/recent",
                params={
                    "asset": "btcusdt",
                    "severity": "warning",
                    "channel": "telegram",
                    "status": "sent",
                    "date_from": "2026-08-01T00:00:00Z",
                    "date_to": "2026-08-14T23:59:59Z",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
