"""
main.py
Entrypoint da API MarketMind AI (FastAPI).
Registra rotas HTTP, endpoint WebSocket de streaming e lifecycle do BinanceStreamService.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.routes.market import router as market_router
from api.routes.prediction import router as prediction_router
from config import settings
from database import init_db
from schemas.candle import HealthResponse
from services.binance_stream import binance_stream_service
from services.ws_manager import connection_manager, on_binance_tick

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("marketmind.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando MarketMind AI (%s)", settings.APP_ENV)
    await init_db()

    binance_stream_service.subscribe(on_binance_tick)
    binance_stream_service.start()

    yield

    await binance_stream_service.stop()
    logger.info("MarketMind AI encerrado")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_router, prefix=settings.API_V1_PREFIX)
app.include_router(prediction_router, prefix=settings.API_V1_PREFIX)
# Alias sem prefixo de versão para compatibilidade direta com o spec original
app.include_router(market_router)
app.include_router(prediction_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.APP_NAME, env=settings.APP_ENV)


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket) -> None:
    """
    Canal WebSocket para streaming em tempo real de ticks de preço.
    Cada mensagem enviada tem o formato: {"type": "price_tick", "data": {...}}.
    """
    await connection_manager.connect(websocket)
    try:
        while True:
            # mantém a conexão viva; o cliente pode enviar pings, ignoramos o conteúdo
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
