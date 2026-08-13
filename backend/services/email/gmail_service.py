"""Entrega de e-mail via Gmail API oficial usando OAuth 2.0 com refresh token."""

from __future__ import annotations

import base64
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, parseaddr
from functools import lru_cache
from typing import Any

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Settings, settings

logger = logging.getLogger("marketmind.gmail")

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailError(RuntimeError):
    """Erro base de entrega Gmail, seguro para expor como detalhe administrativo."""


class GmailConfigurationError(GmailError):
    """Configuração OAuth incompleta ou inconsistente."""


class GmailAuthenticationError(GmailError):
    """Refresh token ausente, revogado ou inválido."""


class GmailDeliveryError(GmailError):
    """Falha temporária ou permanente ao chamar a Gmail API."""


@dataclass(frozen=True)
class EmailAttachment:
    """Contrato para anexos futuros, mantendo o serviço extensível sem alterar a API."""

    filename: str
    content: bytes
    mime_type: str = "application/octet-stream"


@dataclass(frozen=True)
class EmailSendResult:
    """Resultado mínimo da Gmail API, sem reter conteúdo ou destinatários em logs."""

    message_id: str
    thread_id: str | None
    recipient_count: int


class GmailService:
    """Cliente lazy da Gmail API, autenticado por refresh token configurado no ambiente."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        self._settings = app_settings or settings

    def assert_configured(self, *, require_refresh_token: bool = True) -> None:
        required = {
            "GOOGLE_CLIENT_ID": self._settings.GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": self._settings.GOOGLE_CLIENT_SECRET,
            "GMAIL_SENDER_EMAIL": self._settings.GMAIL_SENDER_EMAIL,
        }
        if require_refresh_token:
            required["GOOGLE_REFRESH_TOKEN"] = self._settings.GOOGLE_REFRESH_TOKEN

        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise GmailConfigurationError(
                "Configuração Gmail incompleta: defina " + ", ".join(missing) + "."
            )

        self._normalize_address(self._settings.GMAIL_SENDER_EMAIL, field="GMAIL_SENDER_EMAIL")

    def send_email(
        self,
        to: str | Iterable[str],
        subject: str,
        body: str,
        html: str | None = None,
        reply_to: str | None = None,
        attachments: Sequence[EmailAttachment] | None = None,
    ) -> EmailSendResult:
        """Envia texto ou MIME multipart alternativo; anexo é suportado pelo contrato futuro."""
        self.assert_configured()
        recipients = self._normalize_recipients(to)
        message = self._build_message(
            recipients=recipients,
            subject=subject,
            body=body,
            html=html,
            reply_to=reply_to,
            attachments=attachments or (),
        )

        try:
            response = (
                self._build_client()
                .users()
                .messages()
                .send(
                    userId="me",
                    body={
                        "raw": base64.urlsafe_b64encode(message.as_bytes()).decode("ascii"),
                    },
                )
                .execute()
            )
        except HttpError as exc:
            raise self._map_http_error(exc) from exc
        except (OSError, ValueError) as exc:
            raise GmailDeliveryError("Não foi possível concluir o envio pela Gmail API.") from exc

        message_id = str(response.get("id", ""))
        if not message_id:
            raise GmailDeliveryError("A Gmail API não retornou o identificador da mensagem enviada.")

        logger.info("E-mail Gmail entregue para %d destinatário(s)", len(recipients))
        return EmailSendResult(
            message_id=message_id,
            thread_id=response.get("threadId"),
            recipient_count=len(recipients),
        )

    def _build_client(self) -> Any:
        credentials = Credentials(
            token=None,
            refresh_token=self._settings.GOOGLE_REFRESH_TOKEN,
            token_uri=GOOGLE_TOKEN_URI,
            client_id=self._settings.GOOGLE_CLIENT_ID,
            client_secret=self._settings.GOOGLE_CLIENT_SECRET,
            scopes=[GMAIL_SEND_SCOPE],
        )
        try:
            credentials.refresh(Request())
        except RefreshError as exc:
            raise GmailAuthenticationError(
                "Não foi possível renovar a autorização Gmail. Gere e configure um novo refresh token."
            ) from exc

        return build("gmail", "v1", credentials=credentials, cache_discovery=False)

    def _build_message(
        self,
        *,
        recipients: Sequence[str],
        subject: str,
        body: str,
        html: str | None,
        reply_to: str | None,
        attachments: Sequence[EmailAttachment],
    ) -> EmailMessage:
        if not isinstance(subject, str) or not subject.strip():
            raise GmailDeliveryError("O assunto do e-mail é obrigatório.")
        if not isinstance(body, str) or not body.strip():
            raise GmailDeliveryError("O corpo de texto do e-mail é obrigatório.")
        self._assert_safe_header(subject, field="subject")

        message = EmailMessage()
        message["To"] = ", ".join(recipients)
        message["From"] = formataddr(("MarketMind AI", self._settings.GMAIL_SENDER_EMAIL))
        message["Subject"] = subject.strip()
        if reply_to:
            message["Reply-To"] = self._normalize_address(reply_to, field="reply_to")

        message.set_content(body)
        if html:
            message.add_alternative(html, subtype="html")

        for attachment in attachments:
            if not attachment.filename or not isinstance(attachment.content, bytes):
                raise GmailDeliveryError("Anexo inválido.")
            maintype, _, subtype = attachment.mime_type.partition("/")
            message.add_attachment(
                attachment.content,
                maintype=maintype or "application",
                subtype=subtype or "octet-stream",
                filename=attachment.filename,
            )
        return message

    @staticmethod
    def _normalize_recipients(to: str | Iterable[str]) -> list[str]:
        if isinstance(to, str):
            candidates = [to]
        else:
            try:
                candidates = list(to)
            except TypeError as exc:
                raise GmailDeliveryError("Informe pelo menos um destinatário válido.") from exc
        if not candidates:
            raise GmailDeliveryError("Informe pelo menos um destinatário.")
        return [GmailService._normalize_address(value, field="to") for value in candidates]

    @staticmethod
    def _normalize_address(value: str, *, field: str) -> str:
        if not isinstance(value, str):
            raise GmailDeliveryError(f"O campo {field} deve conter um endereço de e-mail.")
        GmailService._assert_safe_header(value, field=field)
        _, address = parseaddr(value)
        if not address or "@" not in address or address != value.strip():
            raise GmailDeliveryError(f"O endereço informado em {field} é inválido.")
        return address

    @staticmethod
    def _assert_safe_header(value: str, *, field: str) -> None:
        if "\r" in value or "\n" in value:
            raise GmailDeliveryError(f"O campo {field} contém caracteres de cabeçalho inválidos.")

    @staticmethod
    def _map_http_error(exc: HttpError) -> GmailDeliveryError:
        status = getattr(exc.resp, "status", None)
        if status in {401, 403}:
            return GmailAuthenticationError(
                "A Gmail API recusou a autorização. Verifique o escopo gmail.send e reautorize a conta."
            )
        if status == 429:
            return GmailDeliveryError("A cota da Gmail API foi excedida; tente novamente mais tarde.")
        if status and 400 <= status < 500:
            return GmailDeliveryError("A Gmail API recusou a mensagem; revise os dados do envio.")
        return GmailDeliveryError("A Gmail API está indisponível no momento; tente novamente mais tarde.")


@lru_cache
def get_gmail_service() -> GmailService:
    """Retorna uma instância process-local; as credenciais só são renovadas no envio."""
    return GmailService()
