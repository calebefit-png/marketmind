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

    # Comma-separated exact origins.
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
