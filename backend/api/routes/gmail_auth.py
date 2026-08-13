"""Fluxo administrativo de autorização OAuth 2.0 da Gmail API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from collections.abc import Callable
from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel, EmailStr, Field

from config import settings
from services.email.gmail_service import GMAIL_SEND_SCOPE, GmailError, get_gmail_service

router = APIRouter(tags=["gmail"], include_in_schema=False)

GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailTestRequest(BaseModel):
    to: EmailStr
    subject: str = Field(min_length=1, max_length=180)
    body: str = Field(min_length=1, max_length=20_000)
    html: str | None = Field(default=None, max_length=100_000)


def require_gmail_admin(
    x_gmail_admin_secret: Annotated[str | None, Header()] = None,
) -> None:
    """Impede que endpoints de autorização ou teste sejam acionados publicamente."""
    configured_secret = settings.GMAIL_ADMIN_SECRET
    if not configured_secret or not x_gmail_admin_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso administrativo necessário.")
    if not hmac.compare_digest(configured_secret, x_gmail_admin_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso administrativo necessário.")


def _oauth_redirect_uri(request: Request) -> str:
    return settings.GMAIL_OAUTH_REDIRECT_URI or str(request.url_for("gmail_oauth_callback"))


def _create_flow(redirect_uri: str) -> Flow:
    get_gmail_service().assert_configured(require_refresh_token=False)
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": GOOGLE_AUTH_URI,
                "token_uri": GOOGLE_TOKEN_URI,
            }
        },
        scopes=[GMAIL_SEND_SCOPE],
    )
    flow.redirect_uri = redirect_uri
    return flow


def _urlsafe_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _urlsafe_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _state_secret() -> bytes:
    if not settings.GMAIL_ADMIN_SECRET:
        raise HTTPException(status_code=503, detail="GMAIL_ADMIN_SECRET ainda não foi configurado.")
    return settings.GMAIL_ADMIN_SECRET.encode("utf-8")


def create_signed_state(now: int | None = None, nonce_factory: Callable[[], str] = lambda: secrets.token_urlsafe(24)) -> str:
    """Cria state com expiração curta, autenticado por HMAC e sem segredos de OAuth."""
    payload = {
        "purpose": "gmail_oauth",
        "issued_at": now if now is not None else int(time.time()),
        "nonce": nonce_factory(),
    }
    encoded = _urlsafe_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _urlsafe_encode(hmac.new(_state_secret(), encoded.encode("ascii"), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def validate_signed_state(state_value: str, now: int | None = None) -> None:
    """Valida integridade, propósito e expiração do state recebido do Google."""
    try:
        encoded, received_signature = state_value.split(".", maxsplit=1)
        expected_signature = _urlsafe_encode(
            hmac.new(_state_secret(), encoded.encode("ascii"), hashlib.sha256).digest()
        )
        payload = json.loads(_urlsafe_decode(encoded))
        issued_at = int(payload["issued_at"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="State OAuth inválido.") from exc

    if not hmac.compare_digest(expected_signature, received_signature):
        raise HTTPException(status_code=400, detail="State OAuth inválido.")
    current_time = now if now is not None else int(time.time())
    if payload.get("purpose") != "gmail_oauth" or not payload.get("nonce"):
        raise HTTPException(status_code=400, detail="State OAuth inválido.")
    if issued_at > current_time + 60 or current_time - issued_at > settings.GMAIL_STATE_MAX_AGE_SECONDS:
        raise HTTPException(status_code=400, detail="State OAuth expirado. Inicie a autorização novamente.")


@router.get("/gmail", dependencies=[Depends(require_gmail_admin)])
async def start_gmail_authorization(request: Request) -> RedirectResponse:
    """Inicia OAuth, exigindo o segredo administrativo apenas antes do redirecionamento ao Google."""
    redirect_uri = _oauth_redirect_uri(request)
    flow = _create_flow(redirect_uri)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=create_signed_state(),
    )
    return RedirectResponse(authorization_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/gmail/callback", name="gmail_oauth_callback")
async def gmail_authorization_callback(request: Request, code: str, state: str) -> HTMLResponse:
    """Troca code por refresh token e o revela uma única vez pela conexão HTTPS do administrador."""
    validate_signed_state(state)
    flow = _create_flow(_oauth_redirect_uri(request))
    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Não foi possível concluir a autorização Gmail.") from exc

    refresh_token = flow.credentials.refresh_token
    if not refresh_token:
        raise HTTPException(
            status_code=422,
            detail=(
                "O Google não retornou um refresh token. Revogue o acesso do app na Conta Google e "
                "repita a autorização com prompt de consentimento."
            ),
        )

    safe_token = escape(refresh_token)
    return HTMLResponse(
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>Gmail autorizado</title>"
        "</head><body><h1>Gmail autorizado</h1>"
        "<p>Copie o valor abaixo imediatamente para a variável <code>GOOGLE_REFRESH_TOKEN</code> "
        "no Render. Ele não foi gravado em arquivo, banco ou log.</p>"
        f"<pre>{safe_token}</pre>"
        "<p>Depois de salvar a variável e redeployar, use o endpoint administrativo de teste. "
        "Feche esta página e não compartilhe este valor.</p></body></html>",
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
    )


@router.post("/gmail/test", dependencies=[Depends(require_gmail_admin)])
async def send_gmail_test(payload: GmailTestRequest) -> dict[str, str | int | None]:
    """Testa o envio sem expor credenciais, corpo ou destinatário na resposta."""
    try:
        result = get_gmail_service().send_email(
            to=str(payload.to),
            subject=payload.subject,
            body=payload.body,
            html=payload.html,
        )
    except GmailError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "status": "sent",
        "message_id": result.message_id,
        "thread_id": result.thread_id,
        "recipient_count": result.recipient_count,
    }
