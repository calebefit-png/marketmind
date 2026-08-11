"""
config.py
Configuração central da aplicação via pydantic-settings.
Lê variáveis de ambiente do arquivo .env e expõe um singleton `settings`.
"""

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
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://marketmind:marketmind_secret@localhost:5432/marketmind"
    DATABASE_URL_SYNC: str = "postgresql://marketmind:marketmind_secret@localhost:5432/marketmind"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # External APIs
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"
    BINANCE_REST_URL: str = "https://api.binance.com/api/v3"
    BCB_SGS_URL: str = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
