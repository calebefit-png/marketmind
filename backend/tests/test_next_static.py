"""Testes da resolução de payloads RSC exportados pelo Next.js."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from services.next_static import rsc_payload_path


class NextStaticPayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.static_dir = Path(self.temp_dir.name)
        (self.static_dir / "acoes").mkdir()
        (self.static_dir / "acoes" / "index.txt").write_text("payload", encoding="utf-8")
        (self.static_dir / "index.txt").write_text("home", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_resolves_category_payload_with_or_without_trailing_slash(self) -> None:
        expected = self.static_dir / "acoes" / "index.txt"
        self.assertEqual(rsc_payload_path(self.static_dir, "/acoes/"), expected)
        self.assertEqual(rsc_payload_path(self.static_dir, "/acoes"), expected)

    def test_resolves_home_payload(self) -> None:
        self.assertEqual(rsc_payload_path(self.static_dir, "/"), self.static_dir / "index.txt")

    def test_rejects_missing_or_outside_paths(self) -> None:
        self.assertIsNone(rsc_payload_path(self.static_dir, "/inexistente/"))
        self.assertIsNone(rsc_payload_path(self.static_dir, "/../../etc/"))


class NextStaticMiddlewareTests(unittest.TestCase):
    def test_rsc_request_for_actions_receives_exported_component_payload(self) -> None:
        with TestClient(app) as client:
            response = client.get("/acoes/?_rsc=validation", headers={"RSC": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"].split(";", 1)[0], "text/x-component")
        self.assertIn("Ações", response.text)
