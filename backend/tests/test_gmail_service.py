"""Testes unitários do serviço de e-mail Gmail e da proteção do fluxo OAuth."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from googleapiclient.errors import HttpError

from api.routes import gmail_auth
from config import Settings
from services.email.gmail_service import (
    GMAIL_SEND_SCOPE,
    GmailAuthenticationError,
    GmailConfigurationError,
    GmailDeliveryError,
    GmailService,
)


def make_settings(**overrides: str) -> Settings:
    values = {
        "GOOGLE_CLIENT_ID": "client-id.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "client-secret",
        "GOOGLE_REFRESH_TOKEN": "refresh-token",
        "GMAIL_SENDER_EMAIL": "alerts@example.com",
        "GMAIL_ADMIN_SECRET": "admin-secret-for-tests",
        "GMAIL_STATE_MAX_AGE_SECONDS": 600,
    }
    values.update(overrides)
    return Settings(**values)


class GmailServiceTestCase(unittest.TestCase):
    def test_requires_all_oauth_values_before_sending(self) -> None:
        service = GmailService(make_settings(GOOGLE_CLIENT_SECRET=""))
        with self.assertRaisesRegex(GmailConfigurationError, "GOOGLE_CLIENT_SECRET"):
            service.assert_configured()

    def test_builds_multipart_email_for_multiple_recipients(self) -> None:
        service = GmailService(make_settings())
        message = service._build_message(
            recipients=["first@example.com", "second@example.com"],
            subject="Alerta de mercado",
            body="O preço atingiu a regra configurada.",
            html="<strong>O preço atingiu a regra configurada.</strong>",
            reply_to="support@example.com",
            attachments=(),
        )

        self.assertEqual(message["To"], "first@example.com, second@example.com")
        self.assertEqual(message["Reply-To"], "support@example.com")
        self.assertEqual(message.get_content_type(), "multipart/alternative")
        self.assertIn("text/html", message.as_string())

    def test_rejects_invalid_recipient_and_header_injection(self) -> None:
        service = GmailService(make_settings())
        with self.assertRaises(GmailDeliveryError):
            service._normalize_recipients(["invalid-address"])
        with self.assertRaises(GmailDeliveryError):
            service._build_message(
                recipients=["first@example.com"],
                subject="Assunto\nBcc: attacker@example.com",
                body="Conteúdo válido",
                html=None,
                reply_to=None,
                attachments=(),
            )

    @patch("services.email.gmail_service.build")
    @patch("services.email.gmail_service.Credentials")
    def test_sends_using_refresh_token_and_gmail_scope(
        self, credentials_class: MagicMock, build_client: MagicMock
    ) -> None:
        credentials = credentials_class.return_value
        client = build_client.return_value
        client.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "gmail-message-1",
            "threadId": "gmail-thread-1",
        }

        result = GmailService(make_settings()).send_email(
            to=["first@example.com", "second@example.com"],
            subject="Teste",
            body="Mensagem de teste",
        )

        self.assertEqual(result.message_id, "gmail-message-1")
        self.assertEqual(result.recipient_count, 2)
        self.assertEqual(credentials_class.call_args.kwargs["scopes"], [GMAIL_SEND_SCOPE])
        credentials.refresh.assert_called_once()

    def test_maps_gmail_authentication_error_without_exposing_token(self) -> None:
        response = MagicMock(status=401)
        error = HttpError(response, b"unauthorized")
        mapped = GmailService._map_http_error(error)
        self.assertIsInstance(mapped, GmailAuthenticationError)
        self.assertNotIn("refresh-token", str(mapped))


class GmailOAuthStateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.original_settings = gmail_auth.settings
        gmail_auth.settings = make_settings()

    def tearDown(self) -> None:
        gmail_auth.settings = self.original_settings

    def test_state_is_signed_and_has_short_expiration(self) -> None:
        state = gmail_auth.create_signed_state(now=1_000, nonce_factory=lambda: "nonce-for-test")
        gmail_auth.validate_signed_state(state, now=1_599)
        with self.assertRaises(HTTPException) as expired:
            gmail_auth.validate_signed_state(state, now=1_601)
        self.assertEqual(expired.exception.status_code, 400)

    def test_state_rejects_tampering(self) -> None:
        state = gmail_auth.create_signed_state(now=1_000, nonce_factory=lambda: "nonce-for-test")
        tampered_state = f"{state[:-1]}x"
        with self.assertRaises(HTTPException) as invalid:
            gmail_auth.validate_signed_state(tampered_state, now=1_001)
        self.assertEqual(invalid.exception.status_code, 400)

    def test_admin_guard_requires_correct_header_secret(self) -> None:
        with self.assertRaises(HTTPException) as missing:
            gmail_auth.require_gmail_admin(None)
        self.assertEqual(missing.exception.status_code, 403)

        with self.assertRaises(HTTPException) as wrong:
            gmail_auth.require_gmail_admin("wrong-secret")
        self.assertEqual(wrong.exception.status_code, 403)

        gmail_auth.require_gmail_admin("admin-secret-for-tests")
