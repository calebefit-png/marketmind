"""Entrypoint da API MarketMind AI (FastAPI)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes.gmail_auth import router as gmail_auth_router
from api.routes.alert_status import router as alert_status_router
from api.routes.market import router as market_router
from api.routes.notifications import router as notifications_router
from api.routes.prediction import router as prediction_router
from config import settings
from database import check_database, dispose_db, init_db
from schemas.candle import HealthResponse
from services.binance_stream import binance_stream_service
from services.notifications.telegram_service import get_telegram_service
from services.security_headers import apply_security_headers
from services.ws_manager import connection_manager, on_binance_tick

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("marketmind.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando %s (%s)", settings.APP_NAME, settings.APP_ENV)
    database_ready = await init_db()
    if not database_ready:
        logger.warning("Banco indisponível ou não configurado durante o startup")
    logger.info("Telegram configured: %s", get_telegram_service().is_configured())

    binance_stream_service.subscribe(on_binance_tick)
    binance_stream_service.start()

    try:
        yield
    finally:
        await binance_stream_service.stop()
        await dispose_db()
        logger.info("%s encerrado", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

cors_origins = settings.cors_origins_list
if "*" in cors_origins:
    logger.warning("CORS_ORIGINS=* não é permitido para produção; usando lista vazia")
    cors_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Adiciona proteção de transporte e conteúdo sem interferir no portal estático."""
    response = await call_next(request)
    return apply_security_headers(response, production=settings.APP_ENV == "production")

app.include_router(market_router, prefix=settings.API_V1_PREFIX)
app.include_router(prediction_router, prefix=settings.API_V1_PREFIX)
# Alias sem prefixo de versão para compatibilidade direta com o spec original.
app.include_router(market_router)
app.include_router(prediction_router)
app.include_router(gmail_auth_router, prefix="/auth")
app.include_router(notifications_router)
app.include_router(alert_status_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    database_ok, database_state = await check_database()
    return HealthResponse(
        status="ok" if database_ok else "degraded",
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        version=settings.APP_VERSION,
        database=database_state,
    )


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket) -> None:
    """Canal WebSocket para ticks de preço no formato `{type, data}`."""
    await connection_manager.connect(websocket)
    try:
        initial_tick = binance_stream_service.last_tick
        if initial_tick is None:
            try:
                initial_tick = await binance_stream_service.fetch_rest_tick()
            except Exception as exc:
                logger.warning("Não foi possível enviar tick inicial ao cliente WS: %s", type(exc).__name__)
        if initial_tick is not None:
            await websocket.send_json({"type": "price_tick", "data": initial_tick})

        while True:
            # Mantém a conexão viva; o cliente pode enviar pings/texto, ignoramos o conteúdo.
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


# O painel Next.js é exportado estaticamente para este diretório no release.
# O mount é registrado por último para preservar todas as rotas HTTP e WebSocket.
frontend_dir = Path(__file__).resolve().parent / "static"
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    logger.warning("Frontend estático não encontrado em %s; servindo apenas a API", frontend_dir)
