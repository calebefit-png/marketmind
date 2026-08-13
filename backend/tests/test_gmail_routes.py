"""Cobertura de integração das rotas Gmail sem chamada externa ao Google."""

from __future__ import annotations

import os
import unittest

# Evita que uma variável DATABASE_URL herdada pelo ambiente afete a importação do app.
os.environ["DATABASE_URL"] = ""
os.environ["DATABASE_URL_SYNC"] = ""

from fastapi.testclient import TestClient

from main import app


class GmailRoutesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_gmail_routes_are_registered_and_admin_guard_blocks_unauthenticated_calls(self) -> None:
        paths = {route.path for route in app.routes}
        self.assertIn("/auth/gmail", paths)
        self.assertIn("/auth/gmail/callback", paths)
        self.assertIn("/auth/gmail/test", paths)

        response = self.client.get("/auth/gmail", follow_redirects=False)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Acesso administrativo necessário.")
