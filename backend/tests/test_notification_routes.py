"""Testes leves de registro e proteção das rotas administrativas de alertas."""

from __future__ import annotations

import unittest

from fastapi.routing import APIRoute

from main import app


class NotificationRoutesTestCase(unittest.TestCase):
    def test_notification_routes_are_registered_outside_public_schema(self) -> None:
        routes = {route.path: route for route in app.routes if isinstance(route, APIRoute)}
        self.assertIn("/notifications/test/telegram", routes)
        self.assertIn("/notifications/preferences/{scope_key}", routes)
        self.assertFalse(routes["/notifications/test/telegram"].include_in_schema)
