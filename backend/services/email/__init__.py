"""Serviços de entrega de e-mail do MarketMind."""

from services.email.gmail_service import GmailService, get_gmail_service

__all__ = ["GmailService", "get_gmail_service"]
