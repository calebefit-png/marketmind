"""Controle de acesso para operações administrativas de notificações."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from config import settings


async def require_notification_admin(
    x_admin_notification_secret: Annotated[str | None, Header()] = None,
    x_gmail_admin_secret: Annotated[str | None, Header()] = None,
) -> None:
    """Exige o segredo genérico; aceita o legado somente durante a transição segura."""
    configured = settings.ADMIN_NOTIFICATION_SECRET.strip()
    supplied = x_admin_notification_secret

    # Compatibilidade transitória: quando o novo segredo ainda não existe,
    # o endpoint pode usar exclusivamente o cabeçalho legado já configurado.
    if not configured:
        configured = settings.GMAIL_ADMIN_SECRET.strip()
        supplied = x_gmail_admin_secret

    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Controle administrativo de notificações não configurado.",
        )
    if not supplied or not secrets.compare_digest(supplied, configured):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credencial administrativa inválida.",
        )
