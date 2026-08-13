"""Configuração central da aplicação via variáveis de ambiente."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "MarketMind AI"
    # Serviços Render recebem a variável RENDER; mantendo APP_ENV explícito como prioridade.
    APP_ENV: str = os.getenv("APP_ENV", "production" if os.getenv("RENDER") else "development")
    APP_DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    APP_VERSION: str = "0.2.0"

    # Database: blank by default; production must provide DATABASE_URL.
    DATABASE_URL: str = ""
    DATABASE_URL_SYNC: str = ""

    # Redis is optional for the current in-process broadcaster.
    REDIS_URL: str = ""

    # External APIs
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"
    BINANCE_REST_URL: str = "https://api.binance.com/api/v3"
    BCB_SGS_URL: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

    # Gmail API / OAuth 2.0. Nunca use senha Gmail, SMTP ou Service Account.
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REFRESH_TOKEN: str = ""
    GMAIL_SENDER_EMAIL: str = ""
    # Segredo exclusivo da operação administrativa e da assinatura de state OAuth.
    GMAIL_ADMIN_SECRET: str = ""
    # Opcional, porém recomendado no Render para evitar depender do Host do proxy.
    GMAIL_OAUTH_REDIRECT_URI: str = ""
    GMAIL_STATE_MAX_AGE_SECONDS: int = 600

    # Entrega de alertas. Credenciais e destinatários ficam somente no ambiente do servidor.
    # Usado por todos os controles administrativos de alertas, inclusive Telegram.
    ADMIN_NOTIFICATION_SECRET: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    ALERT_EMAIL_RECIPIENTS: str = ""
    # Gmail permanece opcional; Telegram é o único canal ativo por padrão.
    ALERT_DEFAULT_CHANNELS: str = "telegram"
    ALERT_DEFAULT_COOLDOWN_SECONDS: int = 1800
    ALERT_WORKER_TECHNICAL_INTERVAL_SECONDS: int = 300
    ALERT_WORKER_MACRO_INTERVAL_SECONDS: int = 900
    TELEGRAM_MIN_SEND_INTERVAL_SECONDS: float = 1.0
    ALERT_PRICE_WINDOW_SECONDS: int = 900
    ALERT_PRICE_MOVE_THRESHOLD_PCT: float = 2.5
    ALERT_RSI_OVERBOUGHT: float = 70.0
    ALERT_RSI_OVERSOLD: float = 30.0
    ALERT_VOLUME_SPIKE_MULTIPLIER: float = 2.0
    ALERT_SELIC_CHANGE_THRESHOLD: float = 0.01
    ALERT_PROBABILITY_CHANGE_THRESHOLD: float = 0.15

    # Comma-separated exact origins.
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def alert_channels_list(self) -> list[str]:
        return [channel.strip().lower() for channel in self.ALERT_DEFAULT_CHANNELS.split(",") if channel.strip()]

    @property
    def alert_email_recipients_list(self) -> list[str]:
        return [recipient.strip() for recipient in self.ALERT_EMAIL_RECIPIENTS.split(",") if recipient.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
